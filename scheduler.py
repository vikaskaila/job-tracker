"""
Background scheduler for periodic job scraping
"""

import threading
import time
import logging
from typing import Callable, Optional
import schedule

logger = logging.getLogger(__name__)

class SchedulerThread(threading.Thread):
    """Background thread that runs scheduled tasks"""
    
    def __init__(self):
        super().__init__(daemon=True)
        self.jobs_schedule = schedule.Scheduler()
        self.running = False
    
    def schedule_job(self, job_func: Callable, interval_hours: int, 
                     job_name: str = "Job"):
        """Schedule a job to run every N hours"""
        self.jobs_schedule.every(interval_hours).hours.do(
            self._run_job,
            job_func,
            job_name
        )
        logger.info(f"Scheduled {job_name} to run every {interval_hours} hours")
    
    def schedule_email_check(self, job_func: Callable, interval_minutes: int,
                             job_name: str = "Email Check"):
        """Schedule email check to run every N minutes"""
        self.jobs_schedule.every(interval_minutes).minutes.do(
            self._run_job,
            job_func,
            job_name
        )
        logger.info(f"Scheduled {job_name} to run every {interval_minutes} minutes")
    
    def _run_job(self, job_func: Callable, job_name: str):
        """Internal method to run a scheduled job with error handling"""
        try:
            logger.info(f"Running scheduled task: {job_name}")
            job_func()
            logger.info(f"Completed: {job_name}")
        except Exception as e:
            logger.error(f"Error in scheduled task {job_name}: {e}")
    
    def run(self):
        """Main loop for scheduler thread"""
        self.running = True
        logger.info("Scheduler thread started")
        
        while self.running:
            self.jobs_schedule.run_pending()
            time.sleep(1)  # Check every second
        
        logger.info("Scheduler thread stopped")
    
    def stop(self):
        """Stop the scheduler thread"""
        self.running = False
    
    def clear(self):
        """Clear all scheduled jobs"""
        self.jobs_schedule.clear()
