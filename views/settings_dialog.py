"""
Settings Dialog - application configuration UI
"""

import os
import json
import logging
import threading
from typing import Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QSpinBox,
    QPushButton, QCheckBox, QFileDialog, QMessageBox
)
from imap_tools import MailBox

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings dialog for app configuration"""
    
    def __init__(self, parent=None, config_path: str = None):
        super().__init__(parent)
        self.config_path = config_path
        self.config = self.load_config()
        self.init_ui()
        self.setWindowTitle("Job Tracker Settings")
        self.setGeometry(100, 100, 700, 600)
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return {
            'search_terms': ['Python Developer', 'Software Engineer'],
            'location': 'Germany',
            'country': 'Germany',
            'results_wanted': 50,
            'scrape_interval_hours': 2,
            'email_check_interval_minutes': 30,
            'gmail_email': '',
            'gmail_enabled': False,
            'theme': 'Dark',
            'groq_api_key': '',
            'base_resume_path': '',
            'base_cover_letter_path': '',
        }
    
    def init_ui(self):
        """Initialize UI elements"""
        layout = QVBoxLayout()
        
        # Search terms
        layout.addWidget(QLabel("Search Terms (one per line):"))
        self.search_terms_input = QTextEdit()
        self.search_terms_input.setPlainText("\n".join(self.config.get('search_terms', [])))
        layout.addWidget(self.search_terms_input)
        
        # Location
        layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setText(self.config.get('location', 'Germany'))
        layout.addWidget(self.location_input)
        
        # Results
        layout.addWidget(QLabel("Results per Scrape:"))
        self.results_input = QSpinBox()
        self.results_input.setValue(self.config.get('results_wanted', 50))
        self.results_input.setRange(10, 500)
        layout.addWidget(self.results_input)
        
        # Scrape interval
        layout.addWidget(QLabel("Scrape Interval (hours):"))
        self.scrape_interval = QSpinBox()
        self.scrape_interval.setValue(self.config.get('scrape_interval_hours', 2))
        self.scrape_interval.setRange(1, 24)
        layout.addWidget(self.scrape_interval)
        
        # ===== GMAIL SETTINGS =====
        layout.addWidget(QLabel("\n📧 Gmail Settings (IMAP + App Password):"))
        
        layout.addWidget(QLabel("Gmail Email:"))
        self.gmail_email = QLineEdit()
        self.gmail_email.setPlaceholderText("your.email@gmail.com")
        self.gmail_email.setText(self.config.get('gmail_email', ''))
        layout.addWidget(self.gmail_email)
        
        layout.addWidget(QLabel("App Password (16 chars):"))
        self.gmail_password = QLineEdit()
        self.gmail_password.setPlaceholderText("xxxx xxxx xxxx xxxx")
        self.gmail_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.gmail_password)
        
        # Email check interval
        layout.addWidget(QLabel("Email Check Interval (minutes):"))
        self.email_interval = QSpinBox()
        self.email_interval.setValue(self.config.get('email_check_interval_minutes', 30))
        self.email_interval.setRange(5, 120)
        layout.addWidget(self.email_interval)
        
        # Test Gmail connection button
        self.test_gmail_btn = QPushButton("Save & Test Connection")
        self.test_gmail_btn.clicked.connect(self.test_gmail_connection)
        layout.addWidget(self.test_gmail_btn)
        
        # Gmail enabled checkbox
        self.gmail_enabled_check = QCheckBox("Enable Gmail Monitoring")
        self.gmail_enabled_check.setChecked(self.config.get('gmail_enabled', False))
        layout.addWidget(self.gmail_enabled_check)
        
        # ===== RESUME & COVER LETTER GENERATION =====
        layout.addWidget(QLabel("\n📄 Resume & Cover Letter Generation:"))
        
        layout.addWidget(QLabel("Groq API Key (get free at groq.com):"))
        self.groq_key = QLineEdit()
        self.groq_key.setPlaceholderText("gsk_...")
        self.groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.groq_key.setText(self.config.get('groq_api_key', ''))
        layout.addWidget(self.groq_key)
        
        # Base Resume selector
        resume_layout = QHBoxLayout()
        layout.addWidget(QLabel("Base Resume (PDF):"))
        self.resume_label = QLineEdit()
        self.resume_label.setText(self.config.get('base_resume_path', '') or "No file selected")
        self.resume_label.setReadOnly(True)
        resume_layout.addWidget(self.resume_label)
        select_resume_btn = QPushButton("Select...")
        select_resume_btn.clicked.connect(self.select_base_resume)
        resume_layout.addWidget(select_resume_btn)
        layout.addLayout(resume_layout)
        
        # Base Cover Letter selector
        cover_layout = QHBoxLayout()
        layout.addWidget(QLabel("Base Cover Letter (PDF or TXT):"))
        self.cover_label = QLineEdit()
        self.cover_label.setText(self.config.get('base_cover_letter_path', '') or "No file selected")
        self.cover_label.setReadOnly(True)
        cover_layout.addWidget(self.cover_label)
        select_cover_btn = QPushButton("Select...")
        select_cover_btn.clicked.connect(self.select_base_cover)
        cover_layout.addWidget(select_cover_btn)
        layout.addLayout(cover_layout)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
    
    def test_gmail_connection(self):
        """Test IMAP connection to Gmail"""
        email = self.gmail_email.text().strip()
        password = self.gmail_password.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Missing Info", "Please enter Gmail email and app password")
            return
        
        # Disable button and show loading state
        self.test_gmail_btn.setText("Testing connection...")
        self.test_gmail_btn.setEnabled(False)
        
        # Run test in background thread to avoid blocking UI
        def test_connection():
            try:
                logger.info(f"Testing Gmail IMAP connection for {email}")
                # Set timeout to 10 seconds
                mailbox = MailBox('imap.gmail.com', timeout=10)
                mailbox.login(email, password, 'INBOX')
                # Just check if we can log in, don't fetch all emails
                mailbox.logout()
                
                # Success
                self.test_gmail_btn.setText("Save & Test Connection")
                self.test_gmail_btn.setEnabled(True)
                QMessageBox.information(self, "Success", "✅ Gmail connection successful!\n\nYour email monitoring is ready to use.")
                logger.info(f"Gmail connection test successful for {email}")
                
            except TimeoutError:
                self.test_gmail_btn.setText("Save & Test Connection")
                self.test_gmail_btn.setEnabled(True)
                QMessageBox.critical(
                    self, "Connection Failed",
                    "⏱️ Connection timeout (10 seconds)\n\n"
                    "Make sure:\n"
                    "1. Your internet connection is working\n"
                    "2. IMAP is enabled in Gmail settings\n"
                    "3. App password is correct (16 chars, no spaces)")
                logger.error(f"Gmail connection test timeout for {email}")
                
            except Exception as e:
                error_str = str(e)
                self.test_gmail_btn.setText("Save & Test Connection")
                self.test_gmail_btn.setEnabled(True)
                
                if "401" in error_str or "authentication" in error_str.lower():
                    msg = "❌ Authentication failed\n\nMake sure:\n1. Email address is correct\n2. App password is correct (no spaces)\n3. IMAP is enabled in Gmail settings"
                else:
                    msg = f"❌ Connection failed\n\nError: {error_str}\n\nMake sure:\n1. IMAP is enabled in Gmail settings\n2. App password is correct (16 chars, no spaces)"
                
                QMessageBox.critical(self, "Connection Failed", msg)
                logger.error(f"Gmail connection test failed: {e}")
        
        # Start test in background thread
        test_thread = threading.Thread(target=test_connection, daemon=True)
        test_thread.start()
    
    def select_base_resume(self):
        """Select base resume LaTeX file (TXT format)"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Base Resume (LaTeX TXT)", "", "Text Files (*.txt);;LaTeX Files (*.tex)")
        if file_path:
            self.resume_label.setText(file_path)
            self.config['base_resume_path'] = file_path
            logger.info(f"Base resume selected: {file_path}")
    
    def select_base_cover(self):
        """Select base cover letter DOCX"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Base Cover Letter (DOCX)", "", "Word Documents (*.docx);;Text Files (*.txt)")
        if file_path:
            self.cover_label.setText(file_path)
            self.config['base_cover_letter_path'] = file_path
            logger.info(f"Base cover letter selected: {file_path}")
    
    def save_settings(self):
        """Save settings to file"""
        self.config['search_terms'] = [t.strip() for t in self.search_terms_input.toPlainText().split('\n') if t.strip()]
        self.config['location'] = self.location_input.text()
        self.config['results_wanted'] = self.results_input.value()
        self.config['scrape_interval_hours'] = self.scrape_interval.value()
        self.config['email_check_interval_minutes'] = self.email_interval.value()
        self.config['gmail_email'] = self.gmail_email.text().strip()
        self.config['gmail_enabled'] = self.gmail_enabled_check.isChecked()
        self.config['groq_api_key'] = self.groq_key.text().strip()
        # base_resume_path and base_cover_letter_path already set in select methods
        
        try:
            if self.config_path:
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            logger.info("Settings saved successfully")
            QMessageBox.information(self, "Success", "Settings saved! Please restart the app for all changes to take effect.")
            self.accept()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
