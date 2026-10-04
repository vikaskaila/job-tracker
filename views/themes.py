"""
Themes - application theme stylesheets
"""

THEMES = {
    'Light': """
        QMainWindow { background-color: white; color: black; }
        QTableWidget { background-color: white; color: black; gridline-color: #ddd; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #5DADE2; color: white; }
        QHeaderView::section { background-color: #f0f0f0; color: black; padding: 5px; border: 1px solid #ddd; }
        QPushButton { background-color: #007bff; color: white; border: none; padding: 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #0056b3; }
        QLineEdit { border: 1px solid #ccc; padding: 5px; }
        QComboBox { border: 1px solid #ccc; padding: 5px; }
        QStatusBar { background-color: #f0f0f0; color: black; }
    """,
    'Dark': """
        QMainWindow { background-color: #2d2d2d; color: #e0e0e0; }
        QTableWidget { background-color: #1e1e1e; color: #e0e0e0; gridline-color: #444; alternate-background-color: #2a2a2a; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #007acc; color: white; }
        QHeaderView::section { background-color: #333; color: #e0e0e0; padding: 5px; border: 1px solid #555; }
        QPushButton { background-color: #007acc; color: white; border: none; padding: 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #005a9e; }
        QLineEdit { background-color: #3d3d3d; color: #e0e0e0; border: 1px solid #555; padding: 5px; }
        QComboBox { background-color: #3d3d3d; color: #e0e0e0; border: 1px solid #555; padding: 5px; }
        QLabel { color: #e0e0e0; }
        QStatusBar { background-color: #333; color: #e0e0e0; }
        QMenuBar { background-color: #2d2d2d; color: #e0e0e0; }
        QMenu { background-color: #2d2d2d; color: #e0e0e0; }
        QMenu::item:selected { background-color: #007acc; }
    """,
    'Pastel': """
        QMainWindow { background-color: #f0f8ff; color: #333; }
        QTableWidget { background-color: #fef5e7; color: #333; gridline-color: #e8d5c4; alternate-background-color: #f9f5f0; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #a8dadc; color: white; }
        QHeaderView::section { background-color: #f4a261; color: white; padding: 5px; border: 1px solid #e8d5c4; }
        QPushButton { background-color: #a8dadc; color: white; border: none; padding: 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #8bc5d0; }
        QLineEdit { background-color: #fffbf0; color: #333; border: 1px solid #e8d5c4; padding: 5px; }
        QComboBox { background-color: #fffbf0; color: #333; border: 1px solid #e8d5c4; padding: 5px; }
        QLabel { color: #333; }
        QStatusBar { background-color: #f9f5f0; color: #333; }
    """
}
