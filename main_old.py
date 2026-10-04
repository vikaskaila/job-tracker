"""
Personal Job Tracker - Desktop Application
A single executable app that fetches jobs from LinkedIn and Indeed,
tracks applications, and monitors Gmail for responses.

Author: Datta's Job Tracker
"""

import sys
import os
import sqlite3
import json
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

# Third-party imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QPushButton,
    QLabel, QTabWidget, QDialog, QTextEdit, QSpinBox, QMessageBox,
    QFileDialog, QMenu, QHeaderView, QAbstractItemView, QStatusBar,
    QSystemTrayIcon
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QEvent
from PyQt6.QtGui import QColor, QFont, QIcon, QAction, QCursor
from PyQt6.QtWidgets import QApplication
import schedule

# Import custom modules
try:
    from scheduler import SchedulerThread
    from gmail_manager import GmailManager, EmailMatcher
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Custom modules not found, some features may be disabled")

# Job scraping import
try:
    from jobspy import scrape_jobs
except ImportError:
    print("ERROR: jobspy not installed. Run: pip install jobspy")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

class Database:
    """SQLite database manager for job tracking"""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                posted_date TEXT,
                description_snippet TEXT,
                apply_link TEXT NOT NULL UNIQUE,
                applied_date TEXT,
                status TEXT DEFAULT 'New',
                last_email_matched TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def insert_job(self, job_id: str, title: str, company: str, 
                   location: str, posted_date: str, description: str,
                   apply_link: str) -> bool:
        """Insert a new job into database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Handle None values
            title = title or "Unknown Title"
            company = company or "Unknown Company"
            location = location or "Location Not Specified"
            description = description or ""
            
            # Safely slice description if it's not None
            description_snippet = (description[:500] if description else "")
            
            cursor.execute('''
                INSERT OR IGNORE INTO jobs 
                (id, title, company, location, posted_date, description_snippet, apply_link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (job_id, title, company, location, posted_date, description_snippet, apply_link))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error inserting job: {e} | Data: title={title}, company={company}, location={location}")
            return False
    
    def get_all_jobs(self, status_filter: str = None) -> List[Dict]:
        """Get all jobs or filtered by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status_filter and status_filter != "All":
            cursor.execute('SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC', (status_filter,))
        else:
            cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_job_status(self, job_id: str, status: str, notes: str = None):
        """Update job status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if status == "Applied" and notes is None:
                cursor.execute('''
                    UPDATE jobs SET status = ?, applied_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, job_id))
            else:
                cursor.execute('''
                    UPDATE jobs SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, notes or "", job_id))
            
            conn.commit()
            conn.close()
            logger.info(f"Job {job_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """Get a specific job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
            conn.commit()
            conn.close()
            logger.info(f"Job {job_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            return False
    
    def search_jobs(self, query: str, status_filter: str = None) -> List[Dict]:
        """Search jobs by title, company, or location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        
        if status_filter and status_filter != "All":
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE (title LIKE ? OR company LIKE ? OR location LIKE ?)
                AND status = ?
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern, search_pattern, status_filter))
        else:
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE title LIKE ? OR company LIKE ? OR location LIKE ?
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        """Get job statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "New"')
        new = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Applied"')
        applied = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Interview"')
        interview = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Rejected"')
        rejected = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Offer"')
        offer = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'new': new,
            'applied': applied,
            'interview': interview,
            'rejected': rejected,
            'offer': offer
        }

# ============================================================================
# JOB SCRAPER THREAD
# ============================================================================

class JobScraperThread(QThread):
    """Background thread for scraping jobs"""
    
    jobs_fetched = pyqtSignal(int)  # Signal with number of new jobs
    error_occurred = pyqtSignal(str)  # Signal with error message
    scraping_started = pyqtSignal()
    scraping_finished = pyqtSignal()
    
    def __init__(self, db: Database, config: Dict):
        super().__init__()
        self.db = db
        self.config = config
        self.is_running = True
    
    def run(self):
        """Execute job scraping"""
        try:
            self.scraping_started.emit()
            logger.info("Starting job scrape...")
            
            # Get configuration
            search_terms = self.config.get('search_terms', ['Python Developer'])
            location = self.config.get('location', 'North Rhine-Westphalia, Germany')
            results_per_scrape = self.config.get('results_wanted', 50)
            
            new_jobs_count = 0
            
            for search_term in search_terms:
                try:
                    logger.info(f"Scraping for: {search_term}")
                    
                    # Scrape from LinkedIn and Indeed
                    jobs = scrape_jobs(
                        site_name=["linkedin", "indeed"],
                        search_term=search_term,
                        location=location,
                        results_wanted=results_per_scrape,
                        hours_old=24*7  # Past week
                    )
                    
                    if jobs is not None and len(jobs) > 0:
                        for job in jobs.itertuples():
                            job_id = f"{job.company}_{hash(job.job_url)}"
                            
                            if self.db.insert_job(
                                job_id=job_id,
                                title=job.title,
                                company=job.company,
                                location=job.location,
                                posted_date=str(job.date_posted) if hasattr(job, 'date_posted') else None,
                                description=job.description if hasattr(job, 'description') else "",
                                apply_link=job.job_url
                            ):
                                new_jobs_count += 1
                        
                        logger.info(f"Added {new_jobs_count} new jobs from {search_term}")
                    
                except Exception as e:
                    error_msg = f"Error scraping for '{search_term}': {str(e)}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
            
            self.jobs_fetched.emit(new_jobs_count)
            
        except Exception as e:
            error_msg = f"Fatal scraping error: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        
        finally:
            self.scraping_finished.emit()
    
    def stop(self):
        """Stop the thread"""
        self.is_running = False

# ============================================================================
# SETTINGS DIALOG
# ============================================================================

class SettingsDialog(QDialog):
    """Settings dialog for app configuration"""
    
    def __init__(self, parent=None, config_path: str = "config.json"):
        super().__init__(parent)
        self.config_path = config_path
        self.config = self.load_config()
        self.init_ui()
        self.setWindowTitle("Job Tracker Settings")
        self.setGeometry(100, 100, 600, 500)
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        return {
            'search_terms': ['Python Developer', 'Software Engineer'],
            'location': 'North Rhine-Westphalia, Germany',
            'country': 'Germany',
            'results_wanted': 50,
            'scrape_interval_hours': 2,
            'email_check_interval_minutes': 30,
            'gmail_connected': False
        }
    
    def init_ui(self):
        """Initialize UI elements"""
        layout = QVBoxLayout()
        
        # Search terms
        layout.addWidget(QLabel("Search Terms (one per line):"))
        self.search_terms_input = QTextEdit()
        self.search_terms_input.setText('\n'.join(self.config.get('search_terms', [])))
        layout.addWidget(self.search_terms_input)
        
        # Location
        layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setText(self.config.get('location', ''))
        layout.addWidget(self.location_input)
        
        # Country
        layout.addWidget(QLabel("Country:"))
        self.country_input = QLineEdit()
        self.country_input.setText(self.config.get('country', ''))
        layout.addWidget(self.country_input)
        
        # Results per scrape
        layout.addWidget(QLabel("Results per Scrape:"))
        self.results_input = QSpinBox()
        self.results_input.setRange(10, 500)
        self.results_input.setValue(self.config.get('results_wanted', 50))
        layout.addWidget(self.results_input)
        
        # Scrape interval
        layout.addWidget(QLabel("Scrape Interval (hours):"))
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 24)
        self.interval_input.setValue(self.config.get('scrape_interval_hours', 2))
        layout.addWidget(self.interval_input)
        
        # Email check interval
        layout.addWidget(QLabel("Email Check Interval (minutes):"))
        self.email_interval_input = QSpinBox()
        self.email_interval_input.setRange(5, 1440)
        self.email_interval_input.setValue(self.config.get('email_check_interval_minutes', 30))
        layout.addWidget(self.email_interval_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_settings(self):
        """Save settings to configuration file"""
        self.config['search_terms'] = [s.strip() for s in self.search_terms_input.toPlainText().split('\n') if s.strip()]
        self.config['location'] = self.location_input.text()
        self.config['country'] = self.country_input.text()
        self.config['results_wanted'] = self.results_input.value()
        self.config['scrape_interval_hours'] = self.interval_input.value()
        self.config['email_check_interval_minutes'] = self.email_interval_input.value()
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Settings saved successfully")
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.accept()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class JobTrackerApp(QMainWindow):
    """Main application window with integrated scheduler and Gmail monitoring"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Datta's Job Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize database
        self.db = Database("jobs.db")
        
        # Load configuration
        self.config_path = "config.json"
        self.config = self.load_config()
        
        # Job scraper thread
        self.scraper_thread = None
        self.last_scrape_time = 0
        self.min_scrape_interval = 30 * 60  # 30 minutes minimum
        
        # Scheduler thread
        self.scheduler_thread = None
        
        # Gmail manager and email watcher
        self.gmail_manager = None
        self.email_watcher_thread = None
        
        # Initialize UI
        self.init_ui()
        
        # Load initial data
        self.refresh_table()
        
        # Start background scheduler
        self.start_scheduler()
        
        logger.info("Application started successfully")
    
    def load_config(self) -> Dict:
        """Load configuration"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'search_terms': ['Python Developer', 'Software Engineer'],
            'location': 'North Rhine-Westphalia, Germany',
            'country': 'Germany',
            'results_wanted': 50,
            'scrape_interval_hours': 2,
            'email_check_interval_minutes': 30,
            'gmail_connected': False
        }
    
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search box
        toolbar_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, company, or location...")
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_input)
        
        # Status filter
        toolbar_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "New", "Applied", "Interview", "Rejected", "Ghosted", "Offer"])
        self.status_filter.currentTextChanged.connect(self.on_status_filter_changed)
        toolbar_layout.addWidget(self.status_filter)
        
        main_layout.addLayout(toolbar_layout)
        
        # Buttons toolbar
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh Jobs Now")
        refresh_btn.clicked.connect(self.on_refresh_clicked)
        button_layout.addWidget(refresh_btn)
        
        mark_applied_btn = QPushButton("Mark Selected as Applied")
        mark_applied_btn.clicked.connect(self.mark_selected_applied)
        button_layout.addWidget(mark_applied_btn)
        
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(export_btn)
        
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)
        
        gmail_btn = QPushButton("Connect Gmail")
        gmail_btn.clicked.connect(self.connect_gmail)
        button_layout.addWidget(gmail_btn)
        
        main_layout.addLayout(button_layout)
        
        # Jobs table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Title", "Company", "Location", "Posted", "Status", "Apply Link"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.on_cell_double_clicked)
        
        # Configure columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Company
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Location
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Posted
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Apply Link
        
        main_layout.addWidget(self.table)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.update_status_bar()
    
    def start_scheduler(self):
        """Start background scheduler thread"""
        try:
            self.scheduler_thread = SchedulerThread()
            
            # Schedule job scraping every N hours
            scrape_interval = self.config.get('scrape_interval_hours', 2)
            self.scheduler_thread.schedule_job(
                self.scheduled_scrape,
                scrape_interval,
                "Job Scraping"
            )
            
            # Schedule email checking every N minutes (if Gmail connected)
            if self.config.get('gmail_connected', False):
                email_interval = self.config.get('email_check_interval_minutes', 30)
                self.scheduler_thread.schedule_email_check(
                    self.scheduled_email_check,
                    email_interval,
                    "Email Check"
                )
            
            self.scheduler_thread.start()
            logger.info("Scheduler thread started")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    def scheduled_scrape(self):
        """Scheduled job scraping (called by scheduler)"""
        current_time = time.time()
        
        # Check rate limiting
        if current_time - self.last_scrape_time < self.min_scrape_interval:
            logger.info("Rate limit active, skipping scheduled scrape")
            return
        
        self.last_scrape_time = current_time
        
        # Trigger scraping
        try:
            self.scraper_thread = JobScraperThread(self.db, self.config)
            self.scraper_thread.jobs_fetched.connect(self.on_scrape_complete)
            self.scraper_thread.error_occurred.connect(self.on_scrape_error)
            self.scraper_thread.start()
            
            logger.info("Scheduled scrape started")
        except Exception as e:
            logger.error(f"Error in scheduled scrape: {e}")
    
    def scheduled_email_check(self):
        """Scheduled email checking (called by scheduler)"""
        try:
            if not self.gmail_manager or not self.gmail_manager.authenticated:
                logger.warning("Gmail not authenticated for scheduled email check")
                return
            
            self.check_emails()
        except Exception as e:
            logger.error(f"Error in scheduled email check: {e}")
    
    def connect_gmail(self):
        """Connect to Gmail API"""
        try:
            self.gmail_manager = GmailManager()
            if self.gmail_manager.authenticate():
                self.config['gmail_connected'] = True
                self.save_config()
                QMessageBox.information(self, "Success", "Gmail connected successfully!")
                logger.info("Gmail connected")
                
                # Restart scheduler with email monitoring
                if self.scheduler_thread:
                    self.scheduler_thread.stop()
                    self.scheduler_thread.wait()
                self.start_scheduler()
            else:
                QMessageBox.critical(self, "Error", "Failed to authenticate with Gmail")
        except Exception as e:
            logger.error(f"Gmail connection error: {e}")
            QMessageBox.critical(self, "Error", f"Gmail connection failed: {e}")
    
    def check_emails(self):
        """Check emails and update job statuses"""
        try:
            if not self.gmail_manager or not self.gmail_manager.authenticated:
                return
            
            # Fetch unread emails from last 24 hours
            emails = self.gmail_manager.get_unread_emails(hours=24)
            
            if not emails:
                logger.info("No new emails to process")
                return
            
            matcher = EmailMatcher()
            jobs = self.db.get_all_jobs()
            updates_made = 0
            
            for email in emails:
                for job in jobs:
                    confidence, status = matcher.match_email_to_job(
                        email,
                        job['title'],
                        job['company']
                    )
                    
                    # Update if confidence is high (> 60%)
                    if confidence > 0.6 and status:
                        old_status = job['status']
                        
                        # Only update to higher priority statuses
                        status_priority = {
                            'New': 0, 'Applied': 1, 'Interview': 2,
                            'Rejected': 3, 'Offer': 4
                        }
                        
                        old_priority = status_priority.get(old_status, 0)
                        new_priority = status_priority.get(status, 0)
                        
                        if new_priority >= old_priority:
                            notes = f"Auto-updated from email: {email.get('subject', 'Unknown')}\n" + \
                                   (job.get('notes', '') or '')
                            self.db.update_job_status(job['id'], status, notes[:1000])
                            updates_made += 1
                            logger.info(f"Updated job {job['id']} to {status}")
                            
                            # Mark email as read
                            self.gmail_manager.mark_as_read(email['id'])
            
            if updates_made > 0:
                self.refresh_table()
                logger.info(f"Email check completed, {updates_made} jobs updated")
        
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
    
    def refresh_table(self, search_query: str = "", status_filter: str = "All"):
        """Refresh job table"""
        self.table.setRowCount(0)
        
        # Get jobs based on filters
        if search_query:
            jobs = self.db.search_jobs(search_query, status_filter)
        elif status_filter != "All":
            jobs = self.db.get_all_jobs(status_filter)
        else:
            jobs = self.db.get_all_jobs()
        
        # Populate table
        for row, job in enumerate(jobs):
            self.table.insertRow(row)
            
            # Store job_id in first column for reference
            title_item = QTableWidgetItem(job['title'][:100])  # Truncate long titles
            title_item.setData(Qt.ItemDataRole.UserRole, job['id'])  # Store job ID
            self.table.setItem(row, 0, title_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(job['company']))
            self.table.setItem(row, 2, QTableWidgetItem(job['location'] or "N/A"))
            self.table.setItem(row, 3, QTableWidgetItem(job['posted_date'] or "N/A"))
            
            # Status with color coding
            status_item = QTableWidgetItem(job['status'])
            status_colors = {
                'New': QColor(100, 149, 237),  # Cornflower blue
                'Applied': QColor(144, 238, 144),  # Light green
                'Interview': QColor(255, 215, 0),  # Gold
                'Rejected': QColor(255, 99, 71),  # Tomato
                'Ghosted': QColor(169, 169, 169),  # Dark gray
                'Offer': QColor(50, 205, 50)  # Lime green
            }
            status_item.setBackground(status_colors.get(job['status'], QColor(200, 200, 200)))
            self.table.setItem(row, 4, status_item)
            
            # Apply link (clickable)
            link_item = QTableWidgetItem("Click to Open")
            link_item.setForeground(QColor(0, 0, 255))  # Blue
            link_item.setData(Qt.ItemDataRole.UserRole, job['apply_link'])
            font = QFont()
            font.setUnderline(True)
            link_item.setFont(font)
            self.table.setItem(row, 5, link_item)
        
        self.update_status_bar()
    
    def on_search_changed(self):
        """Handle search input change"""
        search_query = self.search_input.text()
        status_filter = self.status_filter.currentText()
        self.refresh_table(search_query, status_filter)
    
    def on_status_filter_changed(self):
        """Handle status filter change"""
        search_query = self.search_input.text()
        status_filter = self.status_filter.currentText()
        self.refresh_table(search_query, status_filter)
    
    def on_cell_double_clicked(self, index):
        """Open job URL when apply link is double-clicked"""
        if index.column() == 5:  # Apply Link column
            item = self.table.item(index.row(), index.column())
            url = item.data(Qt.ItemDataRole.UserRole)
            if url:
                webbrowser.open(url)
                logger.info(f"Opened URL: {url}")
    
    def show_context_menu(self, position):
        """Show context menu for table rows"""
        menu = QMenu()
        
        mark_applied = QAction("Mark as Applied")
        mark_rejected = QAction("Mark as Rejected")
        mark_interview = QAction("Mark as Interview")
        add_note = QAction("Add/Edit Note")
        delete = QAction("Delete Job")
        
        mark_applied.triggered.connect(lambda: self.mark_row_status("Applied"))
        mark_rejected.triggered.connect(lambda: self.mark_row_status("Rejected"))
        mark_interview.triggered.connect(lambda: self.mark_row_status("Interview"))
        add_note.triggered.connect(self.add_note_to_job)
        delete.triggered.connect(self.delete_selected_jobs)
        
        menu.addAction(mark_applied)
        menu.addAction(mark_interview)
        menu.addAction(mark_rejected)
        menu.addSeparator()
        menu.addAction(add_note)
        menu.addAction(delete)
        
        menu.exec(self.table.mapToGlobal(position))
    
    def mark_row_status(self, status: str):
        """Mark selected row with status"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Warning", "Please select a job to mark as " + status)
            return
        
        for row in rows:
            job_id = self.table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
            self.db.update_job_status(job_id, status)
        
        self.refresh_table()
    
    def mark_selected_applied(self):
        """Mark selected jobs as applied"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Warning", "Please select jobs to mark as applied")
            return
        
        for row in rows:
            job_id = self.table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
            self.db.update_job_status(job_id, "Applied")
        
        self.refresh_table()
    
    def add_note_to_job(self):
        """Add or edit note for a job"""
        rows = self.table.selectionModel().selectedRows()
        if len(rows) != 1:
            QMessageBox.warning(self, "Warning", "Please select exactly one job")
            return
        
        job_id = self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        job = self.db.get_job_by_id(job_id)
        
        # Simple dialog for note
        dialog = QDialog(self)
        dialog.setWindowTitle("Add/Edit Note")
        dialog.setGeometry(150, 150, 400, 300)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Job: {job['title']} at {job['company']}"))
        
        note_input = QTextEdit()
        note_input.setText(job['notes'] or "")
        layout.addWidget(note_input)
        
        save_btn = QPushButton("Save Note")
        save_btn.clicked.connect(lambda: self.save_job_note(job_id, note_input.toPlainText(), dialog))
        layout.addWidget(save_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_job_note(self, job_id: str, note: str, dialog):
        """Save note to job"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE jobs SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (note, job_id))
            conn.commit()
            conn.close()
            self.refresh_table()
            dialog.accept()
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")
    
    def delete_selected_jobs(self):
        """Delete selected jobs"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Warning", "Please select jobs to delete")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(rows)} job(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for row in rows:
                job_id = self.table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
                self.db.delete_job(job_id)
            
            self.refresh_table()
    
    def export_to_csv(self):
        """Export jobs to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Jobs", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            jobs = self.db.get_all_jobs()
            
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Company', 'Location', 'Posted Date', 'Status', 'Applied Date', 'Notes', 'Apply Link'])
                
                for job in jobs:
                    writer.writerow([
                        job['title'],
                        job['company'],
                        job['location'],
                        job['posted_date'],
                        job['status'],
                        job['applied_date'],
                        job['notes'],
                        job['apply_link']
                    ])
            
            QMessageBox.information(self, "Success", f"Jobs exported to {file_path}")
            logger.info(f"Jobs exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")
    
    def on_refresh_clicked(self):
        """Handle refresh button click"""
        current_time = time.time()
        
        # Rate limiting: max 1 scrape every 30 minutes
        if current_time - self.last_scrape_time < self.min_scrape_interval:
            remaining = int(self.min_scrape_interval - (current_time - self.last_scrape_time))
            QMessageBox.warning(
                self, "Rate Limit",
                f"Please wait {remaining} seconds before scraping again.\n"
                "(Maximum 1 scrape every 30 minutes to avoid blocking)"
            )
            return
        
        if self.scraper_thread and self.scraper_thread.isRunning():
            QMessageBox.warning(self, "Warning", "A scrape is already in progress")
            return
        
        self.last_scrape_time = current_time
        
        # Start scraper thread
        self.scraper_thread = JobScraperThread(self.db, self.config)
        self.scraper_thread.jobs_fetched.connect(self.on_scrape_complete)
        self.scraper_thread.error_occurred.connect(self.on_scrape_error)
        self.scraper_thread.start()
        
        self.statusBar.showMessage("Scraping jobs...")
    
    def on_scrape_complete(self, new_jobs_count: int):
        """Handle scrape completion"""
        self.refresh_table()
        self.statusBar.showMessage(f"Scrape complete! Found {new_jobs_count} new jobs.")
        QMessageBox.information(self, "Success", f"Scraping complete!\nAdded {new_jobs_count} new jobs.")
    
    def on_scrape_error(self, error_msg: str):
        """Handle scrape error"""
        logger.error(error_msg)
        self.statusBar.showMessage("Scrape error. Check logs for details.")
        QMessageBox.critical(self, "Scraping Error", error_msg)
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.config_path)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload configuration
            self.config = dialog.config
            self.save_config()
    
    def save_config(self):
        """Save current config to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def update_status_bar(self):
        """Update status bar with statistics"""
        stats = self.db.get_stats()
        status_text = (
            f"Total: {stats['total']} | New: {stats['new']} | "
            f"Applied: {stats['applied']} | Interview: {stats['interview']} | "
            f"Rejected: {stats['rejected']} | Offer: {stats['offer']}"
        )
        self.statusBar.showMessage(status_text)
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.scraper_thread.stop()
            self.scraper_thread.wait()
        
        if self.scheduler_thread:
            self.scheduler_thread.stop()
            self.scheduler_thread.wait()
        
        logger.info("Application closed")
        event.accept()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Apply dark stylesheet (optional)
    try:
        from qdarkstyle import load_stylesheet
        app.setStyle('Fusion')
        app.setStyleSheet(load_stylesheet(qt_api='pyqt6'))
    except ImportError:
        # Fallback if qdarkstyle not available
        pass
    
    window = JobTrackerApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
