"""
Personal Job Tracker - Desktop Application (Version 2.0)
Main entry point - launches the application

Features: JobSpy scraping, IMAP email monitoring, PyQt6 GUI, SQLite DB, theme switching
Author: Datta's Job Tracker
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Import the Application class
from PyQt6.QtWidgets import QApplication
from views.main_window import JobTrackerApp


def main():
    """Main entry point - create and launch application"""
    app = QApplication(sys.argv)
    window = JobTrackerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
