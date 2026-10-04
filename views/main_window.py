"""
Main Window - JobTrackerApp QMainWindow and UI components
This file contains the main application window class with all UI logic.
"""

# Import all necessary PyQt6 and system modules
import sys
import os
import json
import threading
import time
import webbrowser
import csv
from datetime import datetime
from typing import Optional, List, Dict
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog, QTextEdit, QSpinBox,
    QMessageBox, QFileDialog, QMenu, QHeaderView, QAbstractItemView, QStatusBar,
    QSystemTrayIcon, QMenuBar, QCheckBox, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QEvent
from PyQt6.QtGui import QColor, QFont, QIcon, QAction, QCursor

# Import from models
from models.database import Database
from models.config import load_config, save_config, get_default_config, CONFIG_FILE

# Import from services
from services.email_watcher import EmailWatcherThread
from services.ai_provider import (
    detect_language, translate_text, fetch_job_description_from_url,
    extract_cover_letter_from_docx, read_latex_template, fix_latex_with_ai,
    compile_latex_to_pdf, create_simple_latex_fallback, generate_pdf_with_reportlab,
    latex_to_html, tailor_latex_resume
)

# Import from views
from views.themes import THEMES
from views.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)

# Data directory (import from models to keep it centralized)
from models.database import DATA_DIR, GENERATED_DIR, DB_FILE


class JobTrackerApp(QMainWindow):
    """Main application window - displays and manages job listings"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize data
        self.data_dir = DATA_DIR
        self.config_file = CONFIG_FILE
        self.load_config()
        self.db = Database(DB_FILE)
        
        # Show data location on first run
        if not os.path.exists(os.path.join(DATA_DIR, ".initialized")):
            open(os.path.join(DATA_DIR, ".initialized"), 'a').close()
        
        self.setWindowTitle("Job Tracker v2.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize UI
        self.init_ui()
        self.apply_theme(self.config.get('theme', 'Dark'))
        
        # Scheduler and threads
        self.scheduler_thread = None
        self.scraper_thread = None
        self.email_watcher_thread = None
        
        # Status tracking
        self.last_scrape_time = None
        self.last_scrape_count = 0
        
        # Initialize scraper
        self.start_scheduler()
        
        # Load existing jobs from database on startup
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
        self.update_status_bar()
    
    def load_config(self):
        """Load configuration"""
        self.config = load_config(self.config_file)
    
    def save_config(self):
        """Save configuration to file"""
        save_config(self.config, self.config_file)
        logger.info("Configuration saved")
    
    def init_ui(self):
        """Initialize user interface"""
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Search and filter layout
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, company, or location...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        search_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "New", "Applied", "Interview", "Rejected", "Offer", "Ghosted"])
        self.status_filter.currentTextChanged.connect(self.on_status_filter_changed)
        search_layout.addWidget(self.status_filter)
        
        main_layout.addLayout(search_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Work Type:"))
        self.work_type_filter = QComboBox()
        self.work_type_filter.addItems(["All", "Remote", "Onsite", "Hybrid"])
        self.work_type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.work_type_filter)
        
        self.priority_filter = QCheckBox("High Priority (4-5 only)")
        self.priority_filter.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.priority_filter)
        
        self.favorites_filter = QCheckBox("Favorites Only")
        self.favorites_filter.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.favorites_filter)
        
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels(["Title", "Company", "Location", "Posted", "Status", "Apply Link", "Company Website", "Work Type", "Priority", "Favorite", "Resume", "Cover"])
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(self.open_apply_link)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh Jobs Now")
        refresh_btn.clicked.connect(self.refresh_jobs)
        button_layout.addWidget(refresh_btn)
        
        mark_applied_btn = QPushButton("✓ Mark as Applied")
        mark_applied_btn.clicked.connect(self.mark_selected_applied)
        button_layout.addWidget(mark_applied_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_selected_rows)
        button_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("📊 Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(export_btn)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()
        
        # Tray icon
        self.setup_tray_icon()
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Themes menu
        themes_menu = menubar.addMenu("Themes")
        for theme_name in THEMES:
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, t=theme_name: self.set_theme(t))
            themes_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        quickstart_action = QAction("Quick start Guide", self)
        quickstart_action.triggered.connect(self.show_quickstart)
        help_menu.addAction(quickstart_action)
        
        gmail_action = QAction("Gmail Setup Guide", self)
        gmail_action.triggered.connect(self.show_gmail_guide)
        help_menu.addAction(gmail_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def set_theme(self, theme_name: str):
        """Set application theme"""
        if theme_name in THEMES:
            self.apply_theme(theme_name)
            self.config['theme'] = theme_name
            self.save_config()
    
    def apply_theme(self, theme_name: str):
        """Apply theme stylesheet"""
        if theme_name in THEMES:
            self.setStyleSheet(THEMES[theme_name])
    
    def setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Tray icon activation handler"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
    
    def update_status_bar(self):
        """Update status bar with statistics"""
        stats = self.db.get_stats()
        self.status_bar.showMessage(
            f"Total: {stats['total']} | New: {stats['new']} | Applied: {stats['applied']} | " 
            f"Interview: {stats['interview']} | Rejected: {stats['rejected']} | Offer: {stats['offer']}"
        )
    
    def refresh_table(self, search_query: str = "", status_filter: str = "All"):
        """Refresh job table"""
        if search_query:
            jobs = self.db.search_jobs(search_query, status_filter if status_filter != "All" else None)
        else:
            jobs = self.db.get_all_jobs(status_filter if status_filter != "All" else None)
        
        self.table.setRowCount(0)
        
        for row_idx, job in enumerate(jobs):
            self.table.insertRow(row_idx)
            
            # Title
            title_item = QTableWidgetItem(job['title'])
            self.table.setItem(row_idx, 0, title_item)
            
            # Company
            company_item = QTableWidgetItem(job['company'])
            self.table.setItem(row_idx, 1, company_item)
            
            # Location
            location_item = QTableWidgetItem(job['location'] or "N/A")
            self.table.setItem(row_idx, 2, location_item)
            
            # Posted date
            posted_item = QTableWidgetItem(job['posted_date'] or "N/A")
            self.table.setItem(row_idx, 3, posted_item)
            
            # Status with color coding
            status_item = QTableWidgetItem(job['status'])
            status_colors = {
                'New': QColor('#3498db'),  # Blue
                'Applied': QColor('#2ecc71'),  # Green
                'Interview': QColor('#f39c12'),  # Orange
                'Rejected': QColor('#e74c3c'),  # Red
                'Offer': QColor('#27ae60'),  # Dark Green
                'Ghosted': QColor('#95a5a6')  # Gray
            }
            if job['status'] in status_colors:
                status_item.setBackground(status_colors[job['status']])
                status_item.setForeground(QColor('white'))
            self.table.setItem(row_idx, 4, status_item)
            
            # Apply link
            link_item = QTableWidgetItem("Open Link")
            link_item.setForeground(QColor('#007bff'))
            link_item.setData(Qt.ItemDataRole.UserRole, job['apply_link'])
            link_item.setFont(QFont(link_item.font().family(), -1, -1, True))  # Underline
            self.table.setItem(row_idx, 5, link_item)
            
            # Company website
            company_website_item = QTableWidgetItem("Visit Website" if job.get('company_website') else "N/A")
            if job.get('company_website'):
                company_website_item.setForeground(QColor('#27ae60'))  # Green for clickable  
                company_website_item.setData(Qt.ItemDataRole.UserRole, job['company_website'])
                company_website_item.setFont(QFont(company_website_item.font().family(), -1, -1, True))
            self.table.setItem(row_idx, 6, company_website_item)
            
            # Work Type
            work_type_item = QTableWidgetItem(job.get('work_type') or "N/A")
            self.table.setItem(row_idx, 7, work_type_item)
            
            # Priority (1-5, default 3)
            priority = job.get('priority') or 3
            priority_item = QTableWidgetItem("⭐" * priority)
            priority_item.setData(Qt.ItemDataRole.UserRole, priority)
            self.table.setItem(row_idx, 8, priority_item)
            
            # Favorite (★ if favorited)
            is_favorite = job.get('is_favorite', 0)
            favorite_item = QTableWidgetItem("★" if is_favorite else "☆")
            favorite_item.setData(Qt.ItemDataRole.UserRole, is_favorite)
            favorite_item.setForeground(QColor('#f39c12') if is_favorite else QColor('#95a5a6'))
            self.table.setItem(row_idx, 9, favorite_item)
            
            # Resume generated (✓ if exists)
            resume_path = job.get('generated_resume_path')
            resume_item = QTableWidgetItem("✓" if resume_path else "✗")
            if resume_path:
                resume_item.setForeground(QColor('#2ecc71'))  # Green
                resume_item.setData(Qt.ItemDataRole.UserRole, resume_path)
            else:
                resume_item.setForeground(QColor('#95a5a6'))  # Gray
            self.table.setItem(row_idx, 10, resume_item)
            
            # Cover letter generated (✓ if exists)
            cover_path = job.get('generated_cover_path')
            cover_item = QTableWidgetItem("✓" if cover_path else "✗")
            if cover_path:
                cover_item.setForeground(QColor('#2ecc71'))  # Green
                cover_item.setData(Qt.ItemDataRole.UserRole, cover_path)
            else:
                cover_item.setForeground(QColor('#95a5a6'))  # Gray
            self.table.setItem(row_idx, 11, cover_item)
            
            # Store job_id for later reference
            self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, job['id'])
    
    def apply_filters(self):
        """Apply active filters to the table"""
        work_type_filter = self.work_type_filter.currentText()
        priority_filter = self.priority_filter.isChecked()
        favorites_filter = self.favorites_filter.isChecked()
        
        for row in range(self.table.rowCount()):
            show_row = True
            
            if work_type_filter != "All":
                work_type = self.table.item(row, 7).text() if self.table.item(row, 7) else ""
                if work_type != work_type_filter:
                    show_row = False
            
            if show_row and priority_filter:
                priority = self.table.item(row, 8).data(Qt.ItemDataRole.UserRole) if self.table.item(row, 8) else 3
                if priority < 4:
                    show_row = False
            
            if show_row and favorites_filter:
                is_favorite = self.table.item(row, 9).data(Qt.ItemDataRole.UserRole) if self.table.item(row, 9) else 0
                if not is_favorite:
                    show_row = False
            
            self.table.setRowHidden(row, not show_row)
        
        self.update_status_bar()
    
    def open_apply_link(self, row: int, col: int):
        """Open apply link, company website, or generated documents when double-clicked"""
        if col in [5, 6]:  # URLs
            url = self.table.item(row, col).data(Qt.ItemDataRole.UserRole)
            if url:
                webbrowser.open(url)
                logger.info(f"Opened {'Apply Link' if col == 5 else 'Company Website'}: {url}")
        elif col in [10, 11]:  # Generated documents
            file_path = self.table.item(row, col).data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                try:
                    if col == 10 and file_path.endswith('.tex'):
                        pdf_path = file_path.replace('.tex', '.pdf')
                        html_path = file_path.replace('.tex', '.html')
                        
                        if os.path.exists(pdf_path):
                            os.startfile(pdf_path)
                            logger.info(f"Opened LaTeX resume (PDF): {pdf_path}")
                        elif os.path.exists(html_path):
                            webbrowser.open("file://" + html_path)
                            logger.info(f"Opened resume (HTML): {html_path}")
                    else:
                        if file_path.endswith('.html'):
                            webbrowser.open("file://" + file_path)
                        else:
                            os.startfile(file_path)
                        logger.info(f"Opened {'Resume' if col == 10 else 'Cover Letter'}: {file_path}")
                except Exception as e:
                    logger.error(f"Error opening file {file_path}: {e}")
    
    def show_context_menu(self, position):
        """Show right-click context menu"""
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        
        menu = QMenu()
        
        open_link_action = QAction("Open Apply Link", self)
        open_link_action.triggered.connect(lambda: self.open_apply_link(row, 5))
        menu.addAction(open_link_action)
        
        company_website = self.table.item(row, 6).data(Qt.ItemDataRole.UserRole)
        if company_website:
            open_website_action = QAction("Open Company Website", self)
            open_website_action.triggered.connect(lambda: self.open_apply_link(row, 6))
            menu.addAction(open_website_action)
        
        menu.addSeparator()
        
        is_favorite = self.table.item(row, 9).data(Qt.ItemDataRole.UserRole)
        favorite_text = "Remove from Favorites" if is_favorite else "Add to Favorites"
        favorite_action = QAction(favorite_text, self)
        job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        favorite_action.triggered.connect(lambda: self.toggle_favorite(row, job_id))
        menu.addAction(favorite_action)
        
        menu.addSeparator()
        
        priority_menu = menu.addMenu("Set Priority")
        for i in range(1, 6):
            priority_action = QAction("⭐" * i, self)
            priority_action.triggered.connect(lambda checked, p=i, jid=job_id: self.set_job_priority(row, jid, p))
            priority_menu.addAction(priority_action)
        
        menu.addSeparator()
        
        for status in ["Applied", "Interview", "Rejected", "Offer", "Ghosted"]:
            action = QAction(f"Mark as {status}", self)
            action.triggered.connect(lambda checked, s=status: self.mark_row_status(row, s))
            menu.addAction(action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete Job", self)
        delete_action.triggered.connect(lambda: self.delete_job(row))
        menu.addAction(delete_action)
        
        menu.exec(self.table.mapToGlobal(position))
    
    def mark_row_status(self, row: int, status: str):
        """Mark job status"""
        job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if job_id:
            self.db.update_job_status(job_id, status)
            self.refresh_table(self.search_input.text(), self.status_filter.currentText())
            self.update_status_bar()
    
    def mark_selected_applied(self):
        """Mark selected job as applied"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.mark_row_status(current_row, "Applied")
    
    def delete_job(self, row: int):
        """Delete a job"""
        job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if job_id:
            reply = QMessageBox.question(self, "Confirm Delete", "Delete this job?")
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_job(job_id)
                self.refresh_table(self.search_input.text(), self.status_filter.currentText())
                self.update_status_bar()
    
    def delete_selected_rows(self):
        """Delete all selected rows with double confirmation"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select at least one job to delete")
            return
        
        job_count = len(selected_rows)
        
        reply1 = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete {job_count} job(s)?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply1 != QMessageBox.StandardButton.Yes:
            return
        
        reply2 = QMessageBox.warning(
            self,
            "Final Warning - No Recovery",
            f"⚠️ WARNING: You are about to permanently delete {job_count} job(s).\n\n"
            "This data CANNOT be recovered once deleted.\n\n"
            "Are you absolutely sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply2 != QMessageBox.StandardButton.Yes:
            return
        
        deleted_count = 0
        for model_index in selected_rows:
            row = model_index.row()
            job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if job_id:
                try:
                    self.db.delete_job(job_id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting job {job_id}: {e}")
        
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
        self.update_status_bar()
        
        QMessageBox.information(self, "Delete Complete", f"✓ Successfully deleted {deleted_count} job(s)")
    
    def toggle_favorite(self, row: int, job_id: int):
        """Toggle favorite status for a job"""
        if job_id:
            self.db.toggle_favorite(job_id)
            self.refresh_table(self.search_input.text(), self.status_filter.currentText())
            self.update_status_bar()
    
    def set_job_priority(self, row: int, job_id: int, priority: int):
        """Set job priority (1-5)"""
        if job_id:
            self.db.update_job_priority(job_id, priority)
            self.refresh_table(self.search_input.text(), self.status_filter.currentText())
            self.update_status_bar()
    
    def on_search_changed(self):
        """Handle search input change"""
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
    
    def on_status_filter_changed(self):
        """Handle status filter change"""
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
    
    def refresh_jobs(self):
        """Trigger job scraping"""
        QMessageBox.information(self, "Jobs", "Full scraping will be implemented via controllers in Step 5")
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
        self.update_status_bar()
    
    def export_to_csv(self):
        """Export jobs to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Jobs", "", "CSV Files (*.csv)")
        if file_path:
            try:
                jobs = self.db.get_all_jobs()
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if jobs:
                        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
                        writer.writeheader()
                        writer.writerows(jobs)
                QMessageBox.information(self, "Success", f"Exported {len(jobs)} jobs to CSV")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.config_file)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_config()
            self.update_status_bar()
    
    def start_scheduler(self):
        """Start background scheduler (stub for now)"""
        logger.info("Scheduler initialization (will be completed in controllers)")
    
    def show_quickstart(self):
        """Show quickstart guide"""
        QMessageBox.information(self, "Quickstart Guide", """
Job Tracker v2.0 - Quick Start

1. CONFIGURE SEARCH TERMS
   - Open Settings (⚙️ button)
   - Add job titles you're searching for

2. TRACK APPLICATIONS
   - Right-click job → Mark as Applied
   - Double-click to open links

3. EXPORT DATA
   - Click "📊 Export to CSV"
        """)
    
    def show_gmail_guide(self):
        """Show Gmail setup guide"""
        QMessageBox.information(self, "Gmail Setup", "See Settings for Gmail configuration")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.information(self, "About", "Job Tracker v2.0\n© 2026")
    
    def closeEvent(self, event):
        """Handle window close"""
        try:
            self.save_config()
            event.accept()
        except Exception as e:
            logger.error(f"Error during app close: {e}")
            event.accept()
