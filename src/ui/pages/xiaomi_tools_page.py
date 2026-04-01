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
    XiaomiDebloaterWidget, XiaomiAIOOptimizerWidget, XiaomiNotificationFixWidget,
    XiaomiExpertTweaksWidget
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
        
        # Navigation List (Unified Scroll)
        self.nav_list = QListWidget()
        self.nav_list.setFocusPolicy(Qt.NoFocus)
        self.nav_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.nav_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.nav_list.setStyleSheet(self.get_nav_list_style())
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)
        
        main_layout.addWidget(self.sidebar_container)
        
        # 2. Content Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: transparent; border: none;")
        main_layout.addWidget(self.stack, stretch=1)
        
        # Define Tools with group separators
        tools = [
            (None, "⚡ HIỆU NĂNG", None),           # Group header
            (XiaomiDebloaterWidget, "Gỡ Ứng Dụng", "🗑️"),
            (XiaomiAIOOptimizerWidget, "Tối Ưu Hệ Thống", "✨"),
            (XiaomiExpertTweaksWidget, "Tối Ưu Chuyên Sâu", "💀"),
            (None, "📢 ỨNG DỤNG", None),            # Group header
            (XiaomiNotificationFixWidget, "Fix Thông Báo", "🔔"),
            (None, "🌐 ROM & HỆ THỐNG", None),      # Group header
            (OTADownloaderWidget, "Tải ROM & OTA", "☁️"),
            (HyperOSAppsWidget, "Kho App HyperOS", "🛍️"),
            (FastbootToolboxWidget, "Công Cụ Fastboot", "🛠️"),
            (CleanerWidget, "Dọn Rác", "🧹"),
            (BatteryHealthWidget, "Pin & Sức Khỏe", "🔋"),
        ]
        
        # Populate — include group headers (widget_class is None)
        for widget_class, title, icon in tools:
            if widget_class is None:
                # Add group separator as a non-selectable item
                item = QListWidgetItem(title)
                item.setFlags(Qt.NoItemFlags) # Non-selectable, non-enabled
                item.setSizeHint(QSize(0, 40))
                item.setData(Qt.UserRole, "header") # Custom role for styling if needed
                self.nav_list.addItem(item)
                continue
            
            widget = widget_class(self.adb)
            if hasattr(widget, 'set_parent_page'):
                widget.set_parent_page(self)
            
            self.widgets.append(widget)
            self.stack.addWidget(widget)
            
            # Add to nav
            item = QListWidgetItem(f"   {icon}  {title}")
            item.setSizeHint(QSize(0, 48))
            item.setData(Qt.UserRole, "item")
            self.nav_list.addItem(item)
            
        # Select first
        self.nav_list.setCurrentRow(0)
        
    def switch_to_tool(self, tool_title_fragment):
        """Switch to a tool by searching for a fragment of its title"""
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            if tool_title_fragment.lower() in item.text().lower():
                self.nav_list.setCurrentRow(i)
                return True
        return False
        
    def get_sidebar_style(self):
        theme = ThemeManager.get_theme()
        # GLASS ISLANDS: Translucent background with margin
        return f"""
            QFrame {{
                background-color: rgba(20, 20, 20, 0.15); /* Neutral Glass */
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 28px;
                margin: 12px;
                margin-right: 2px;
            }}
        """
        
    def get_nav_list_style(self):
        theme = ThemeManager.get_theme()
        return f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
                padding-top: 10px;
            }}
            QListWidget::item {{
                height: 48px;
                background: transparent;
                border-radius: 14px;
                margin-bottom: 6px;
                margin-left: 8px;
                margin-right: 8px;
                color: {theme['COLOR_TEXT_SECONDARY']};
                font-family: {ThemeManager.FONT_FAMILY};
                font-size: 14px;
                font-weight: 600;
            }}
            QListWidget::item:hover {{
                background: rgba(255, 255, 255, 0.08);
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QListWidget::item:selected {{
                background: {ThemeManager.GRADIENT_HYPER_BLUE};
                color: white;
                font-weight: 800;
            }}
            /* Specific style for headers via flags (they won't be selectable) */
            QListWidget::item:disabled {{
                color: {ThemeManager.COLOR_ACCENT};
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1.2px;
                padding-top: 15px;
                margin-bottom: 0px;
                background: transparent;
            }}
        """

    def on_nav_changed(self, index):
        if index >= 0:
            item = self.nav_list.item(index)
            # Only switch stack if it's an "item", not a "header"
            if item and item.data(Qt.UserRole) == "item":
                # Find the actual widget index (ignoring headers)
                widget_idx = 0
                for i in range(index):
                    if self.nav_list.item(i).data(Qt.UserRole) == "item":
                        widget_idx += 1
                self.stack.setCurrentIndex(widget_idx)
    
    def reset(self):
        """Reset only the active widget for performance; others reset lazily when navigated to"""
        current = self.stack.currentWidget()
        if current:
            if hasattr(current, 'reset'):
                current.reset()
            elif hasattr(current, 'refresh_state'):
                current.refresh_state()
        # Mark all other widgets dirty so they refresh on next visit
        for widget in self.widgets:
            if widget is not current and hasattr(widget, '_needs_refresh'):
                widget._needs_refresh = True
