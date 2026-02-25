# src/ui/pages/screen_and_debug_page.py
"""
Screen & Debug Page - Combined Screen Mirror, Console, and Logcat
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize
from src.ui.theme_manager import ThemeManager

# Import sub-widgets
from src.ui.widgets.console import ConsoleWidget
from src.ui.widgets.logcat_viewer import LogcatViewerWidget


class ScreenAndDebugPage(QWidget):
    """
    Combined Screen Mirroring and Debugging tools with Vertical Sidebar
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.widgets = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup page UI with modern vertical sidebar"""
        # Main Layout: Horizontal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        
        # 1. Secondary Sidebar
        self.sidebar_container = QFrame()
        self.sidebar_container.setFixedWidth(240)
        self.sidebar_container.setStyleSheet(self.get_sidebar_style())
        
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(10)
        
        title_lbl = QLabel("MÀN HÌNH & DEBUG")
        title_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_ACCENT}; font-size: 11px; font-weight: 800; letter-spacing: 1px; padding-left: 10px; margin-bottom: 5px;")
        sidebar_layout.addWidget(title_lbl)
        
        self.nav_list = QListWidget()
        self.nav_list.setFocusPolicy(Qt.NoFocus)
        self.nav_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.nav_list.setStyleSheet(self.get_nav_list_style())
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)
        
        main_layout.addWidget(self.sidebar_container)
        
        # 2. Content Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: transparent; border: none;")
        main_layout.addWidget(self.stack, stretch=1)
        
        # Define Tools
        tools = [
            (ConsoleWidget, "ADB Console", "💻"),
            (LogcatViewerWidget, "Logcat Viewer", "📜"),
        ]
        
        # Populate
        for widget_class, title, icon in tools:
            widget = widget_class(self.adb)
            self.widgets.append(widget)
            self.stack.addWidget(widget)
            
            item = QListWidgetItem(f"{icon}  {title}")
            item.setSizeHint(QSize(0, 48))
            self.nav_list.addItem(item)
            
        self.nav_list.setCurrentRow(0)
        
    def get_sidebar_style(self):
        theme = ThemeManager.get_theme()
        return f"""
            QFrame {{
                background-color: {theme['COLOR_BG_SECONDARY']};
                border-right: 1px solid {theme['COLOR_BORDER']};
            }}
        """
        
    def get_nav_list_style(self):
        theme = ThemeManager.get_theme()
        return f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                border-radius: 12px;
                padding: 12px 15px;
                margin-bottom: 4px;
                color: {theme['COLOR_TEXT_SECONDARY']};
                font-family: {ThemeManager.FONT_FAMILY};
                font-size: 14px;
                font-weight: 500;
                border: 1px solid transparent;
            }}
            QListWidget::item:hover {{
                background: {theme['COLOR_GLASS_HOVER']};
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QListWidget::item:selected {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                color: {ThemeManager.COLOR_ACCENT};
                font-weight: 700;
                border: 1px solid {theme['COLOR_BORDER_LIGHT']};
            }}
        """

    def on_nav_changed(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index)
    
    def reset(self):
        """Reset all child widgets"""
        for widget in self.widgets:
            if hasattr(widget, 'reset'):
                widget.reset()
