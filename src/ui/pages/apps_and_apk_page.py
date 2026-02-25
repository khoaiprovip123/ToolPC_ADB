# src/ui/pages/apps_and_apk_page.py
"""
Apps Page - Applications management
Merged App Manager & APK Analyzer (Simplified to just Apps)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)
from src.ui.widgets.app_manager import AppManagerWidget


class AppsAndAPKPage(QWidget):
    """
    Apps management page (Single View)
    Renamed conceptually to AppsPage but kept class name for compatibility
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Direct AppManagerWidget (No Tabs)
        self.app_manager = AppManagerWidget(self.adb)
        layout.addWidget(self.app_manager)
        
    def reset(self):
        """Reset widget"""
        if hasattr(self.app_manager, 'reset'):
            self.app_manager.reset()
