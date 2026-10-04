"""
Email Watcher Service - monitors emails via IMAP for job status updates
"""

import logging
import time
import difflib
from PyQt6.QtCore import QThread, pyqtSignal
from imap_tools import MailBox, AND

logger = logging.getLogger(__name__)


class EmailWatcherThread(QThread):
    """Background thread for monitoring emails via IMAP"""
    email_processed = pyqtSignal(str, str)  # (status, message)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, db, email: str, app_password: str, interval_minutes: int = 30):
        super().__init__()
        self.db = db
        self.email = email
        self.app_password = app_password
        self.interval_minutes = interval_minutes
        self.is_running = True
        self.daemon = True
    
    def run(self):
        """Monitor emails periodically"""
        while self.is_running:
            try:
                self.check_emails()
            except Exception as e:
                logger.error(f"Email watcher error: {e}")
                self.error_occurred.emit(f"Email check failed: {str(e)}")
            
            # Sleep for the configured interval
            time.sleep(self.interval_minutes * 60)
    
    def check_emails(self):
        """Check unread emails and update job status"""
        try:
            keywords = {
                'interview': ['interview', 'interviewtermin', 'gespräch', 'termin', 'vorstellungsgespräch', 'gesprächstermin'],
                'rejected': ['unfortunately', 'not proceeding', 'nicht in Betracht', 'ablehnung', 'absage', 'leider nicht', 'we decided', 'regret'],
                'offer': ['offer', 'position', 'angebot', 'stelle', 'job offer', 'welcome', 'willkommen', 'können wir dir anbieten']
            }
            
            with MailBox('imap.gmail.com').login(self.email, self.app_password, 'INBOX') as mailbox:
                for msg in mailbox.fetch(AND(seen=False)):
                    subject_lower = msg.subject.lower()
                    body_lower = msg.text.lower()
                    
                    # Detect status from email content
                    detected_status = None
                    for status, kws in keywords.items():
                        if any(kw in subject_lower or kw in body_lower for kw in kws):
                            detected_status = status.capitalize()
                            break
                    
                    if detected_status:
                        # Try to match email to a job using fuzzy matching
                        jobs = self.db.get_all_jobs()
                        best_match = None
                        best_score = 0
                        
                        for job in jobs:
                            # Match company name
                            company_match = difflib.SequenceMatcher(
                                None, 
                                job['company'].lower(), 
                                subject_lower + " " + body_lower[:200]
                            ).ratio()
                            
                            # Match job title
                            title_match = difflib.SequenceMatcher(
                                None, 
                                job['title'].lower(), 
                                subject_lower[:100]
                            ).ratio()
                            
                            combined_score = (company_match * 0.6 + title_match * 0.4)
                            
                            if combined_score > best_score and combined_score > 0.5:
                                best_match = job
                                best_score = combined_score
                        
                        if best_match:
                            # Update job status
                            email_snippet = msg.subject[:100]
                            self.db.update_job_status(
                                best_match['id'], 
                                detected_status, 
                                f"Email: {email_snippet}"
                            )
                            self.email_processed.emit(detected_status, f"{best_match['company']} - {best_match['title']}")
                            logger.info(f"Updated job to {detected_status}: {best_match['company']}")
                    
                    # Mark email as read
                    mailbox.flag([msg.uid], ['\\Seen'], True)
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            raise
    
    def stop(self):
        """Stop the thread"""
        self.is_running = False
