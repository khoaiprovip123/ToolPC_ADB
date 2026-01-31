# src/ui/widgets/unified_tools.py
"""
Unified Tools Widgets
Group related widgets into tabbed containers to clean up the UI.
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QFrame, QStackedWidget, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QAbstractItemView, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QColor
from src.ui.theme_manager import ThemeManager

# Import widgets to wrap
from src.ui.widgets.console import ConsoleWidget
from src.ui.widgets.logcat_viewer import LogcatViewerWidget
from src.ui.widgets.wireless_debug import WirelessDebugWidget
from src.ui.widgets.dns_config import DNSConfigWidget
from src.ui.widgets.script_engine import ScriptEngineWidget
from src.ui.widgets.xiaomi_optimizer import (
    XiaomiOptimizerWidget, XiaomiDebloaterWidget, 
    XiaomiQuickToolsWidget, XiaomiAdvancedWidget,
    XiaomiHubWidget
)
from src.ui.widgets.system_tweaks import SystemTweaksWidget
from src.ui.widgets.ota_downloader import OTADownloaderWidget, HyperOSAppsWidget
from src.ui.widgets.cloud_sync import CloudSyncWidget
from src.ui.widgets.plugin_manager_ui import PluginManagerWidget
from src.ui.widgets.permission_tools import PermissionToolsWidget
from src.ui.widgets.battery_health import BatteryHealthWidget
from src.ui.widgets.cleaner import CleanerWidget
from src.ui.widgets.fastboot_toolbox import FastbootToolboxWidget
from src.core.optimization_manager import OptimizationManager
from src.ui.widgets.global_optimizer import GeneralTweaksWidget
from src.ui.widgets.app_manager import AppManagerWidget
from src.ui.widgets.file_manager import FileManagerWidget
from src.ui.widgets.advanced_commands import AdvancedCommandsWidget

class BaseTabbedWidget(QWidget):
    """Base class for tabbed tool containers - Space Optimized"""
    def __init__(self, adb_manager, title=""):
        super().__init__()
        self.adb = adb_manager
        self.title = title
        self.widgets = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20) # Standard margins
        layout.setSpacing(0)
        
        # Tabs - Header-less for space
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                border-radius: 12px;
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
            }}
            QTabBar::tab {{
                background: transparent;
                border: none;
                padding: 12px 24px;
                margin-right: 2px;
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                font-family: {ThemeManager.FONT_FAMILY};
                font-size: 14px;
                font-weight: 500;
            }}
            QTabBar::tab:hover {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']};
                border-radius: 8px;
            }}
            QTabBar::tab:selected {{
                color: {ThemeManager.COLOR_ACCENT};
                font-weight: 700;
                border-bottom: 3px solid {ThemeManager.COLOR_ACCENT};
            }}
        """)
        layout.addWidget(self.tabs)
        
    def add_tool(self, widget_class, title, icon=""):
        widget = widget_class(self.adb)
        self.widgets.append(widget)
        self.add_tab(widget, title, icon)

    def add_tab(self, widget, title, icon=""):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)
        self.tabs.addTab(scroll, f"{icon} {title}")
        
    def reset(self):
        for widget in self.widgets:
            if hasattr(widget, 'reset'):
                widget.reset()

class XiaomiSuiteWidget(XiaomiOptimizerWidget):
    """
    Unified Xiaomi Suite (Restored Original Logic)
    Wrapper for XiaomiOptimizerWidget to maintain compatibility with MainWindow.
    """
    def __init__(self, adb_manager):
        # Initialize the original widget which contains all logic (Workers, Device Check, Tabs)
        super().__init__(adb_manager)

    def reset(self):
        """Reload/Refresh state when device changes"""
        # Call setup_ui or checks if needed, but primarily XiaomiOptimizerWidget 
        # handles checks in __init__. We can re-trigger check_device.
        if hasattr(self, 'check_device') and hasattr(self, 'status_label'):
            self.check_device(self.status_label)
        # Also refresh tabs if they have reset methods?
        # Iterate over tabs? self.tabs is QTabWidget.
        # This is good enough for now to prevent crash.

class GeneralToolsWidget(QWidget):
    """
    Unified General Tools & Dev Suite - Modern Sidebar Layout
    Replaces Tabs with a premium vertical navigation rail.
    """
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.widgets = []
        self.setup_ui()
        
    def setup_ui(self):
        # Main Layout: Horizontal (Sidebar | Content)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 1. Sidebar Container
        sidebar_container = QFrame()
        sidebar_container.setObjectName("sidebar_panel")
        sidebar_container.setFixedWidth(260)
        sidebar_container.setStyleSheet(f"""
            #sidebar_panel {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
                border-radius: 16px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
        """)
        
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)
        
        # Title/Brand Area
        lbl_title = QLabel("Công Cụ Khác")
        lbl_title.setStyleSheet(f"""
            QLabel {{
                color: {ThemeManager.COLOR_ACCENT};
                font-size: 20px;
                font-weight: 800;
                padding-left: 10px;
                margin-bottom: 10px;
                background: transparent;
                border: none;
            }}
        """)
        sidebar_layout.addWidget(lbl_title)

        # Navigation List
        self.nav_list = QListWidget()
        self.nav_list.setFocusPolicy(Qt.NoFocus)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nav_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.nav_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                border-radius: 10px;
                padding: 12px 15px;
                margin-bottom: 5px;
                color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']};
                font-size: 14px;
                font-weight: 600;
                border: none;
            }}
            QListWidget::item:hover {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']};
                color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeManager.COLOR_ACCENT};
                color: white;
                font-weight: 700;
            }}
        """)
        
        # Connect signal
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)
        
        layout.addWidget(sidebar_container)
        
        # 2. Content Area
        content_container = QFrame()
        content_container.setObjectName("content_panel")
        content_container.setStyleSheet(f"""
            #content_panel {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 16px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0,0,0,0) # Content widgets handle their own margins
        
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        
        layout.addWidget(content_container, stretch=1)
        
        # Populate Tools
        self.add_tool(CleanerWidget, "Dọn Rác", "🧹")
        self.add_tool(BatteryHealthWidget, "Sức Khỏe Pin", "🔋")
        self.add_tool(PermissionToolsWidget, "Cấp Quyền", "🔐")
        self.add_tool(ConsoleWidget, "Console", "💻")
        self.add_tool(LogcatViewerWidget, "Logcat", "📜")
        self.add_tool(WirelessDebugWidget, "Wireless", "📡")
        self.add_tool(AdvancedCommandsWidget, "Lệnh Nâng Cao", "⚡")
        
        # Select first item
        self.nav_list.setCurrentRow(0)

    def add_tool(self, widget_class, title, icon_text=""):
        # Create Widget
        widget = widget_class(self.adb)
        
        # NOTE: Removed wrapping QScrollArea to prevent double-scrollbars.
        # Widgets that need scrolling (Cleaner, Console, etc.) handle it internally.
        # For those that don't (like WirelessDebug), if they overflow, they should include their own ScrollArea.
        # Checking WirelessDebug: It does NOT have a scroll area, so we might need to Wrap it if shrinking window.
        # However, for now, let's trust the widgets or Wrap specific ones if reported.
        # Safest bet: Check if it's one of the known "Full Height" widgets (Console, Logcat).
        # If not, wrap in ScrollArea? 
        # Actually simplest fix for user issue (Logcat/Cleaner "not scrolling") is removing the wrapper because they ALREADY scroll.
        
        if widget_class in [WirelessDebugWidget, BatteryHealthWidget, PermissionToolsWidget, AdvancedCommandsWidget]:
             # These might need scrolling if content is tall
             from PySide6.QtWidgets import QScrollArea
             scroll = QScrollArea()
             scroll.setWidgetResizable(True)
             scroll.setWidget(widget)
             scroll.setStyleSheet("""
                QScrollArea { border: none; background: transparent; }
                QScrollArea > QWidget > QWidget { background: transparent; }
             """)
             self.stack.addWidget(scroll)
        else:
             # Console, Logcat, Cleaner (has internal scroll)
             self.stack.addWidget(widget)
        
        self.widgets.append(widget)
        
        # Add Nav Item
        item = QListWidgetItem(f"{icon_text}  {title}")
        item.setSizeHint(QSize(0, 50)) # Height 50px
        self.nav_list.addItem(item)
        
    def on_nav_changed(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index)
            
    def reset(self):
        for widget in self.widgets:
            if hasattr(widget, 'reset'):
                widget.reset()
