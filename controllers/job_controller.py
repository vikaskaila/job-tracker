"""
Job Controller - handles job management operations
"""

import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class JobController:
    """Controller for job-related operations"""
    
    def __init__(self, db):
        """Initialize with database"""
        self.db = db
    
    def get_all_jobs(self, status_filter: Optional[str] = None) -> List[Dict]:
        """Get all jobs, optionally filtered by status"""
        return self.db.get_all_jobs(status_filter)
    
    def search_jobs(self, query: str, status_filter: Optional[str] = None) -> List[Dict]:
        """Search jobs by title, company, or location"""
        return self.db.search_jobs(query, status_filter)
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get a single job by ID"""
        return self.db.get_job_by_id(job_id)
    
    def update_status(self, job_id: str, status: str, notes: Optional[str] = None) -> bool:
        """Update job status"""
        return self.db.update_job_status(job_id, status, notes)
    
    def set_priority(self, job_id: str, priority: int) -> bool:
        """Set job priority (1-5)"""
        return self.db.update_job_priority(job_id, priority)
    
    def toggle_favorite(self, job_id: str) -> bool:
        """Toggle favorite status"""
        return self.db.toggle_favorite(job_id)
    
    def delete(self, job_id: str) -> bool:
        """Delete a job"""
        return self.db.delete_job(job_id)
    
    def get_stats(self) -> Dict:
        """Get job statistics"""
        return self.db.get_stats()
