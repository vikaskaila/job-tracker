"""
Database model - SQLite database manager for job tracking
"""

import sqlite3
import logging
import os
import platform
from typing import Optional, List, Dict

# Configure logger
logger = logging.getLogger(__name__)

# Data directory setup
if platform.system() == "Windows":
    BASE_DIR = os.getenv("APPDATA") or os.path.expanduser(r"~\AppData\Roaming")
else:
    BASE_DIR = os.path.expanduser("~")

DATA_DIR = os.path.join(BASE_DIR, "JobTracker")
os.makedirs(DATA_DIR, exist_ok=True)

DB_FILE = os.path.join(DATA_DIR, "jobs.db")


class Database:
    """SQLite database manager for job tracking"""
    
    def __init__(self, db_path: str = DB_FILE):
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
                company_website TEXT,
                location TEXT,
                posted_date TEXT,
                description_snippet TEXT,
                apply_link TEXT NOT NULL UNIQUE,
                applied_date TEXT,
                status TEXT DEFAULT 'New',
                last_email_matched TEXT,
                notes TEXT,
                work_type TEXT,
                priority INTEGER DEFAULT 3,
                is_favorite INTEGER DEFAULT 0,
                generated_resume_path TEXT,
                generated_cover_path TEXT,
                match_score_resume REAL,
                match_score_cover REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)')
        
        # Migrations: Add new columns if they don't exist
        new_columns = [
            ('company_website', 'TEXT'),
            ('work_type', 'TEXT'),
            ('priority', 'INTEGER DEFAULT 3'),
            ('is_favorite', 'INTEGER DEFAULT 0'),
            ('generated_resume_path', 'TEXT'),
            ('generated_cover_path', 'TEXT'),
            ('match_score_resume', 'REAL'),
            ('match_score_cover', 'REAL'),
        ]
        
        for col_name, col_type in new_columns:
            try:
                cursor.execute(f'ALTER TABLE jobs ADD COLUMN {col_name} {col_type}')
                logger.info(f"Added {col_name} column to jobs table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    pass  # Column already exists
                else:
                    raise
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def insert_job(self, job_id: str, title: str, company: str, 
                   location: str, posted_date: str, description: str,
                   apply_link: str, company_website: str = None, work_type: str = None) -> bool:
        """Insert a new job into database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            title = title or "Unknown Title"
            company = company or "Unknown Company"
            location = location or "Location Not Specified"
            description = description or ""
            company_website = company_website or None
            work_type = work_type or None
            description_snippet = (description[:500] if description else "")
            
            cursor.execute('''
                INSERT OR IGNORE INTO jobs 
                (id, title, company, company_website, location, posted_date, description_snippet, apply_link, work_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_id, title, company, company_website, location, posted_date, description_snippet, apply_link, work_type))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error inserting job: {e}")
            return False
    
    def update_job_description(self, job_url: str, description: str) -> bool:
        """Update a job's description by URL (for LinkedIn enrichment)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if not description:
                return False
            
            description_snippet = description[:]
            
            cursor.execute('''
                UPDATE jobs
                SET description_snippet = ?
                WHERE apply_link = ?
            ''', (description_snippet, job_url))
            
            conn.commit()
            conn.close()
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Updated description for job URL: {job_url[:60]}...")
            return updated
        except Exception as e:
            logger.error(f"Error updating job description: {e}")
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
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """Get a specific job"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting job by ID: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: str, notes: str = None):
        """Update job status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
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
    
    def update_job_priority(self, job_id: str, priority: int):
        """Update job priority (1-5)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE jobs SET priority = ? WHERE id = ?', (priority, job_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating priority: {e}")
            return False
    
    def toggle_favorite(self, job_id: str):
        """Toggle favorite status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE jobs SET is_favorite = 1 - is_favorite WHERE id = ?', (job_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return False
    
    def save_generated_documents(self, job_id: str, resume_path: str = None, cover_path: str = None, 
                                  resume_score: float = None, cover_score: float = None):
        """Save paths and scores for generated documents"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs SET 
                    generated_resume_path = ?,
                    generated_cover_path = ?,
                    match_score_resume = ?,
                    match_score_cover = ?
                WHERE id = ?
            ''', (resume_path, cover_path, resume_score, cover_score, job_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving generated documents: {e}")
            return False
    
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
