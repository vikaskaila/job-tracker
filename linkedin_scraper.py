"""
LinkedIn Job Description Scraper using Playwright
Purpose: Enrich LinkedIn job postings with full job descriptions
Uses anti-detection measures to avoid LinkedIn blocks
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Scrapes LinkedIn job descriptions using Playwright with anti-detection measures"""
    
    def __init__(self, headless: bool = True, rate_limit_seconds: float = 2.5):
        """
        Initialize the LinkedIn scraper
        
        Args:
            headless: Run browser in headless mode (no UI)
            rate_limit_seconds: Seconds to wait between requests (2-3 sec recommended)
        """
        self.headless = headless
        self.rate_limit_seconds = rate_limit_seconds
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def _launch_browser(self):
        """Launch Playwright browser with stealth plugin"""
        try:
            playwright = await async_playwright().start()
            
            # Launch chromium browser
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-resources',
                ]
            )
            
            # Create context with anti-detection measures
            context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                }
            )
            self.page = await context.new_page()
            
            # Try to apply stealth plugin if available
            try:
                from playwright_stealth import stealth_sync
                # The stealth plugin might not have an async version, so we'll work without it
                logger.debug("playwright-stealth available but using basic anti-detection measures")
            except (ImportError, AttributeError):
                logger.debug("playwright-stealth not available, using basic anti-detection measures")
            
            # Set viewport and timeout
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            self.page.set_default_timeout(15000)  # 15 second timeout
            
            logger.info("Browser launched successfully with anti-detection measures")
            
        except Exception as e:
            logger.error(f"Error launching browser: {str(e)}")
            raise
    
    async def _close_browser(self):
        """Close the browser"""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    async def _extract_description_from_page(self) -> Optional[str]:
        """
        Extract job description from LinkedIn job page
        
        Returns:
            Job description text or None if not found
        """
        try:
            # Wait for description to load
            await self.page.wait_for_selector(
                '[data-test-id="description-details"] article, .description, .show-more-less-html__markup',
                timeout=5000
            )
            
            # Try multiple selectors for LinkedIn description (they change frequently)
            selectors = [
                '[data-test-id="description-details"] article',  # New LinkedIn format
                '.description',                                  # Common class
                '.show-more-less-html__markup',                 # Expandable description
                '.base-card__full-details',                     # Card format
            ]
            
            description_text = None
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Get text content from first matching element
                        text = await elements[0].inner_text()
                        if text and len(text.strip()) > 20:  # Ensure meaningful content
                            description_text = text.strip()
                            logger.debug(f"Found description with selector: {selector}")
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            
            if not description_text:
                # Try getting all text as fallback
                all_text = await self.page.inner_text('body')
                if 'about the job' in all_text.lower():
                    # Extract section after "about the job"
                    parts = all_text.lower().split('about the job')
                    if len(parts) > 1:
                        description_text = parts[1].split('\n')[0:50]  # First 50 lines after "about the job"
                        description_text = '\n'.join(description_text)
            
            return description_text if description_text else None
            
        except Exception as e:
            logger.warning(f"Error extracting description: {str(e)}")
            return None
    
    async def scrape_job_descriptions(self, job_urls: List[str]) -> Dict[str, str]:
        """
        Scrape job descriptions from a list of LinkedIn job URLs
        
        Args:
            job_urls: List of LinkedIn job URLs to scrape
        
        Returns:
            Dictionary mapping job URL to description text
        """
        results = {}
        
        if not job_urls:
            logger.warning("No job URLs provided")
            return results
        
        try:
            await self._launch_browser()
            
            for idx, job_url in enumerate(job_urls):
                if not job_url or 'linkedin' not in job_url.lower():
                    logger.warning(f"Skipping invalid LinkedIn URL: {job_url}")
                    continue
                
                try:
                    logger.info(f"Scraping ({idx+1}/{len(job_urls)}): {job_url[:80]}...")
                    
                    # Navigate to job page
                    await self.page.goto(job_url, wait_until='networkidle', timeout=15000)
                    
                    # Wait a bit for content to load
                    await self.page.wait_for_timeout(1000)
                    
                    # Extract description
                    description = await self._extract_description_from_page()
                    
                    if description:
                        results[job_url] = description
                        logger.info(f"✓ Successfully scraped ({len(results)}/{len(job_urls)})")
                    else:
                        logger.warning(f"✗ Could not extract description from {job_url}")
                        results[job_url] = None
                    
                    # Rate limiting - wait between requests
                    if idx < len(job_urls) - 1:  # Don't wait after last job
                        await self.page.wait_for_timeout(int(self.rate_limit_seconds * 1000))
                    
                except Exception as e:
                    logger.error(f"Error scraping {job_url}: {str(e)}")
                    results[job_url] = None
                    continue
            
        except Exception as e:
            logger.error(f"Fatal scraping error: {str(e)}")
        
        finally:
            await self._close_browser()
        
        logger.info(f"Scraping complete: {len([v for v in results.values() if v])} descriptions found")
        return results


def scrape_linkedin_jobs(job_urls: List[str], headless: bool = True, rate_limit_seconds: float = 2.5) -> Dict[str, Optional[str]]:
    """
    Synchronous wrapper for scraping LinkedIn job descriptions
    
    Args:
        job_urls: List of LinkedIn job URLs to scrape
        headless: Run browser in headless mode
        rate_limit_seconds: Seconds between requests
    
    Returns:
        Dictionary mapping job URL to description text (or None if failed)
    
    Example:
        urls = ["https://www.linkedin.com/jobs/view/...", ...]
        descriptions = scrape_linkedin_jobs(urls)
        for url, desc in descriptions.items():
            if desc:
                print(f"URL: {url}")
                print(f"Description: {desc[:200]}...")
    """
    try:
        scraper = LinkedInScraper(headless=headless, rate_limit_seconds=rate_limit_seconds)
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(scraper.scrape_job_descriptions(job_urls))
        loop.close()
        
        return results
    
    except Exception as e:
        logger.error(f"Error in scrape_linkedin_jobs: {str(e)}")
        # Return empty descriptions for all URLs on error
        return {url: None for url in job_urls}


if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    test_urls = [
        "https://www.linkedin.com/jobs/view/3856389101/",
    ]
    
    print("Testing LinkedIn scraper...")
    results = scrape_linkedin_jobs(test_urls, headless=True)
    
    for url, desc in results.items():
        print(f"\nURL: {url}")
        if desc:
            print(f"Description found ({len(desc)} chars):")
            print(desc[:300] + "..." if len(desc) > 300 else desc)
        else:
            print("No description found")
