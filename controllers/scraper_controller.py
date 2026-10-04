"""
Scraper Controller - handles job scraping operations
"""

import logging
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal
from jobspy import scrape_jobs
import pandas as pd
import uuid

logger = logging.getLogger(__name__)


class JobScraperThread(QThread):
    """Background thread for scraping jobs"""
    jobs_fetched = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    scraping_finished = pyqtSignal()
    
    def __init__(self, db, search_terms: List[str], location: str, max_results: int = 50):
        super().__init__()
        self.db = db
        self.search_terms = search_terms
        self.location = location
        self.max_results = max_results
        self.is_running = True
    
    def run(self):
        """Run the scraper"""
        jobs_added = 0
        
        try:
            logger.info(f"Starting job scraping: {', '.join(self.search_terms)} in {self.location}")
            
            for search_term in self.search_terms:
                if not self.is_running:
                    break
                
                try:
                    logger.info(f"Scraping for: {search_term} in {self.location}")
                    
                    # Scrape jobs using jobspy
                    jobs = scrape_jobs(
                        site_name=['indeed', 'linkedin', 'glassdoor'],
                        search_term=search_term,
                        location=self.location,
                        results_wanted=self.max_results,
                        hours_old=24,
                        is_remote=False
                    )
                    
                    # Process each job
                    if jobs is not None and len(jobs) > 0:
                        for idx, row in jobs.iterrows():
                            if not self.is_running:
                                break
                            
                            try:
                                # Generate unique ID
                                job_id = str(uuid.uuid4())
                                
                                # Extract job details
                                title = str(row.get('job_title', 'Unknown'))
                                company = str(row.get('company', 'Unknown'))
                                location = str(row.get('location', 'Unknown'))
                                posted_date = str(row.get('date_posted', ''))
                                description = str(row.get('job_description', ''))
                                apply_link = str(row.get('job_url', ''))
                                company_website = str(row.get('company_url', '')) if row.get('company_url') else None
                                work_type = str(row.get('work_type', '')) if row.get('work_type') else None
                                
                                # Insert into database
                                if self.db.insert_job(
                                    job_id=job_id,
                                    title=title,
                                    company=company,
                                    location=location,
                                    posted_date=posted_date,
                                    description=description,
                                    apply_link=apply_link,
                                    company_website=company_website,
                                    work_type=work_type
                                ):
                                    jobs_added += 1
                                    logger.info(f"Added job: {title} @ {company}")
                            
                            except Exception as e:
                                logger.error(f"Error processing job: {e}")
                                continue
                        
                        logger.info(f"Scraped {len(jobs)} jobs for '{search_term}'")
                    
                except Exception as e:
                    logger.error(f"Error scraping for '{search_term}': {e}")
                    self.error_occurred.emit(f"Error scraping '{search_term}': {str(e)}")
                    continue
            
            logger.info(f"Scraping complete: {jobs_added} new jobs added")
            self.jobs_fetched.emit(jobs_added)
        
        except Exception as e:
            logger.error(f"Fatal scraping error: {e}")
            self.error_occurred.emit(f"Fatal error: {str(e)}")
        
        finally:
            self.scraping_finished.emit()
    
    def stop(self):
        """Stop the scraper"""
        self.is_running = False


class ScraperController:
    """Controller for scraping operations"""
    
    def __init__(self, db):
        """Initialize with database"""
        self.db = db
        self.scraper_thread = None
    
    def start_scraping(self, search_terms: List[str], location: str, max_results: int = 50) -> JobScraperThread:
        """Start a scraping job"""
        self.scraper_thread = JobScraperThread(self.db, search_terms, location, max_results)
        return self.scraper_thread
    
    def stop_scraping(self):
        """Stop the current scraping job"""
        if self.scraper_thread:
            self.scraper_thread.stop()
