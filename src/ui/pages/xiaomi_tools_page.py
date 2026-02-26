# src/ui/pages/xiaomi_tools_page.py
"""
Xiaomi Tools Page - Flattened version of Xiaomi Suite
Replaces the old Hub -> Detail flow with horizontal tabs
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QFrame, QScrollArea, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize
from src.ui.theme_manager import ThemeManager

# Import sub-widgets
from src.ui.widgets.xiaomi_optimizer import (
    XiaomiDebloaterWidget, XiaomiAIOOptimizerWidget, XiaomiNotificationFixWidget
)
from src.ui.widgets.ota_downloader import OTADownloaderWidget, HyperOSAppsWidget
from src.ui.widgets.fastboot_toolbox import FastbootToolboxWidget
from src.ui.widgets.cleaner import CleanerWidget
from src.ui.widgets.battery_health import BatteryHealthWidget


class XiaomiToolsPage(QWidget):
    """
    Consolidated Xiaomi Tools page with Vertical Sidebar (Secondary Nav)
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.widgets = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup page UI with modern vertical sidebar"""
        # Main Layout: Horizontal (Sidebar | Content)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2) # Minimal spacing
        
        # 1. Secondary Sidebar
        self.sidebar_container = QFrame()
        self.sidebar_container.setFixedWidth(240) # Standard width for sub-nav
        self.sidebar_container.setStyleSheet(self.get_sidebar_style())
        
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(10)
        
        # Title for Section (Optional, but looks nice)
        title_lbl = QLabel("CÔNG CỤ XIAOMI")
        title_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_ACCENT}; font-size: 11px; font-weight: 800; letter-spacing: 1px; padding-left: 10px; margin-bottom: 5px;")
        sidebar_layout.addWidget(title_lbl)
        
        # Navigation List
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
            (XiaomiDebloaterWidget, "Gỡ Ứng Dụng", "🗑️"),
            (XiaomiAIOOptimizerWidget, "Tối Ưu & Tinh Chỉnh (AIO)", "✨"),
            (XiaomiNotificationFixWidget, "Fix Thông Báo 🔔", "🔔"),
            (OTADownloaderWidget, "Tải ROM & OTA", "☁️"),
            (HyperOSAppsWidget, "Kho App HyperOS", "🛍️"),
            (FastbootToolboxWidget, "Công Cụ Fastboot", "🛠️"),
            (CleanerWidget, "Dọn Rác", "🧹"),
            (BatteryHealthWidget, "Pin & Sức Khỏe", "🔋"),
        ]
        
        # Populate
        for widget_class, title, icon in tools:
            widget = widget_class(self.adb)
            self.widgets.append(widget)
            self.stack.addWidget(widget)
            
            # Add to nav
            item = QListWidgetItem(f"{icon}  {title}")
            item.setSizeHint(QSize(0, 48))
            self.nav_list.addItem(item)
            
        # Select first
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
        # Trigger refresh on current tab or all?
        # For performance, maybe just current. But simpler to iterate.
        for widget in self.widgets:
            if hasattr(widget, 'reset'):
                widget.reset()
            elif hasattr(widget, 'refresh_state'):
                widget.refresh_state()
            elif hasattr(widget, 'check_device') and hasattr(widget, 'status_label'):
                widget.check_device(widget.status_label)
