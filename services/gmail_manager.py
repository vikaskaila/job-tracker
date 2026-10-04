"""
Gmail integration for email monitoring and job status updates
"""

import os
import logging
import json
from typing import Optional, List, Dict, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import base64
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailManager:
    """Manages Gmail API connection and email monitoring"""
    
    def __init__(self, credentials_file: str = "credentials.json", 
                 token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2"""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(
                    self.token_file, SCOPES
                )
            
            # If no valid credentials, start OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save token for future use
                with open(self.token_file, 'w') as f:
                    f.write(creds.to_json())
            
            # Build service
            from googleapiclient.discovery import build
            self.service = build('gmail', 'v1', credentials=creds)
            self.authenticated = True
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    def get_unread_emails(self, hours: int = 24) -> List[Dict]:
        """Get unread emails from past N hours"""
        if not self.authenticated or not self.service:
            logger.error("Not authenticated with Gmail")
            return []
        
        try:
            # Calculate time threshold
            since_time = datetime.now() - timedelta(hours=hours)
            since_str = since_time.strftime('%Y/%m/%d')
            
            # Query for unread emails
            results = self.service.users().messages().list(
                userId='me',
                q=f'is:unread after:{since_str}',
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("No new unread emails")
                return []
            
            logger.info(f"Found {len(messages)} unread emails")
            
            # Get full message details
            emails = []
            for msg in messages:
                email_detail = self._get_message_details(msg['id'])
                if email_detail:
                    emails.append(email_detail)
            
            return emails
        
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _get_message_details(self, msg_id: str) -> Optional[Dict]:
        """Get full details of a specific message"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract header information
            email_info = {
                'id': msg_id,
                'subject': self._get_header(headers, 'Subject'),
                'from': self._get_header(headers, 'From'),
                'date': self._get_header(headers, 'Date'),
                'body': self._get_body(message),
                'snippet': message.get('snippet', '')
            }
            
            return email_info
        
        except Exception as e:
            logger.error(f"Error getting message details: {e}")
            return None
    
    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Extract header value"""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return ""
    
    def _get_body(self, message: Dict) -> str:
        """Extract message body"""
        try:
            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                data = message['payload']['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error extracting body: {e}")
        
        return message.get('snippet', '')
    
    def mark_as_read(self, msg_id: str) -> bool:
        """Mark an email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False

class EmailMatcher:
    """Fuzzy matches emails with database jobs"""
    
    # Keywords that indicate job status
    STATUS_KEYWORDS = {
        'interview': ['interview', 'interview scheduled', 'interview call', 'phone screen'],
        'rejection': ['unfortunately', 'we regret', 'not selected', 'not moving forward', 
                      'declined', 'rejected', 'not the right fit', 'do not'],
        'offer': ['congratulations', 'offer', 'excited to offer', 'we would like to offer',
                  'job offer', 'offer of employment'],
        'confirmation': ['confirmed', 'received', 'thank you for applying', 'application received']
    }
    
    SOURCE_KEYWORDS = {
        'linkedin': ['linkedin', 'linkedin.com'],
        'indeed': ['indeed', 'indeed.com'],
    }
    
    def __init__(self):
        try:
            from fuzzywuzzy import fuzz
            self.fuzz = fuzz
            self.has_fuzzy = True
        except ImportError:
            logger.warning("fuzzywuzzy not available, using simple string matching")
            self.has_fuzzy = False
    
    def extract_job_info_from_email(self, email: Dict) -> Dict:
        """Extract job information from email"""
        subject = email.get('subject', '').lower()
        body = email.get('body', '').lower()
        from_address = email.get('from', '').lower()
        
        info = {
            'status_keywords': [],
            'company_hints': [],
            'position_hints': [],
            'source': self._detect_source(subject, body, from_address),
            'matched_status': None
        }
        
        # Extract status indicators
        for status, keywords in self.STATUS_KEYWORDS.items():
            for keyword in keywords:
                if keyword in subject or keyword in body:
                    info['status_keywords'].append(status)
        
        # Determine most likely status
        if 'offer' in info['status_keywords']:
            info['matched_status'] = 'Offer'
        elif 'interview' in info['status_keywords']:
            info['matched_status'] = 'Interview'
        elif 'rejection' in info['status_keywords']:
            info['matched_status'] = 'Rejected'
        
        return info
    
    def _detect_source(self, subject: str, body: str, from_addr: str) -> str:
        """Detect job source (LinkedIn, Indeed, etc.)"""
        combined = f"{subject} {body} {from_addr}"
        
        if 'linkedin' in combined:
            return 'LinkedIn'
        elif 'indeed' in combined:
            return 'Indeed'
        else:
            return 'Unknown'
    
    def match_email_to_job(self, email: Dict, job_title: str, 
                          company_name: str) -> Tuple[float, str]:
        """
        Match an email to a job with fuzzy matching
        Returns: (confidence_score, matched_status)
        """
        subject = email.get('subject', '')
        body = email.get('body', '')
        
        email_info = self.extract_job_info_from_email(email)
        
        # Calculate similarity scores
        subject_score = 0
        company_score = 0
        
        if self.has_fuzzy:
            subject_score = self.fuzz.token_set_ratio(subject, job_title) / 100
            company_score = self.fuzz.token_set_ratio(subject, company_name) / 100
        else:
            # Simple substring matching fallback
            subject_lower = subject.lower()
            title_lower = job_title.lower()
            company_lower = company_name.lower()
            
            if title_lower in subject_lower:
                subject_score = 0.9
            elif any(word in subject_lower for word in title_lower.split()):
                subject_score = 0.5
            
            if company_lower in subject_lower:
                company_score = 0.9
            elif any(word in subject_lower for word in company_lower.split()):
                company_score = 0.5
        
        # Combined confidence (weights: subject 60%, company 40%)
        confidence = (subject_score * 0.6) + (company_score * 0.4)
        
        return (confidence, email_info['matched_status'])
