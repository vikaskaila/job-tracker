"""
Utilities for system tray, notifications, and UI enhancements
"""

import sys
import logging
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

logger = logging.getLogger(__name__)

class TrayIcon(QSystemTrayIcon):
    """System tray icon with menu"""
    
    show_window_signal = pyqtSignal()
    refresh_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_icon()
        self.setup_menu()
        self.show()
    
    def setup_icon(self):
        """Setup tray icon"""
        # Create a simple icon (in production, use actual icon file)
        # For now, use default application icon
        self.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
    
    def setup_menu(self):
        """Setup context menu"""
        self.menu = QMenu()
        
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window)
        self.menu.addAction(show_action)
        
        self.menu.addSeparator()
        
        refresh_action = QAction("Refresh Jobs Now", self)
        refresh_action.triggered.connect(self.refresh_jobs)
        self.menu.addAction(refresh_action)
        
        self.menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(exit_action)
        
        self.setContextMenu(self.menu)
        
        # Also handle left-click to show/hide window
        self.activated.connect(self.on_tray_activated)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        from PyQt6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """Show main window"""
        if self.parent_window:
            self.parent_window.showNormal()
            self.parent_window.activateWindow()
    
    def refresh_jobs(self):
        """Trigger job refresh"""
        self.refresh_signal.emit()
        if self.parent_window and hasattr(self.parent_window, 'on_refresh_clicked'):
            self.parent_window.on_refresh_clicked()
    
    def exit_app(self):
        """Exit application"""
        self.exit_signal.emit()
        QApplication.quit()


class NotificationManager:
    """Manages desktop notifications"""
    
    @staticmethod
    def show_notification(title: str, message: str, duration: int = 5000):
        """Show system notification (Windows only, needs wintoast)"""
        try:
            from winotify import Notification, audio
            
            notification = Notification(
                app_id="Job Tracker",
                title=title,
                msg=message,
                duration=duration
            )
            notification.show()
            logger.info(f"Notification shown: {title}")
        except ImportError:
            logger.warning("winotify not available, notification skipped")
        except Exception as e:
            logger.error(f"Error showing notification: {e}")


class DarkStylesheet:
    """Provides dark mode stylesheet"""
    
    @staticmethod
    def get_dark_stylesheet() -> str:
        """Return dark stylesheet for PyQt6"""
        return """
        QMainWindow, QDialog {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QTableWidget {
            background-color: #252526;
            alternate-background-color: #2d2d30;
            color: #ffffff;
            gridline-color: #3e3e42;
        }
        
        QTableWidget::item {
            padding: 4px;
            border: none;
        }
        
        QTableWidget::item:selected {
            background-color: #007acc;
        }
        
        QHeaderView::section {
            background-color: #3e3e42;
            color: #ffffff;
            padding: 4px;
            border: none;
        }
        
        QPushButton {
            background-color: #007acc;
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #005a9e;
        }
        
        QPushButton:pressed {
            background-color: #003d82;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
            border-radius: 3px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid #007acc;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox::down-arrow {
            image: none;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        QStatusBar {
            background-color: #3e3e42;
            color: #ffffff;
            border-top: 1px solid #555555;
        }
        
        QDialog {
            background-color: #1e1e1e;
        }
        
        QMenuBar {
            background-color: #3e3e42;
            color: #ffffff;
            border-bottom: 1px solid #555555;
        }
        
        QMenuBar::item:selected {
            background-color: #007acc;
        }
        
        QMenu {
            background-color: #3e3e42;
            color: #ffffff;
        }
        
        QMenu::item:selected {
            background-color: #007acc;
        }
        """
