# src/ui/widgets/unified_tools.py
"""
Unified Tools Widgets
Group related widgets into tabbed containers to clean up the UI.
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QFrame, QStackedWidget, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt
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
        from PySide6.QtWidgets import QScrollArea
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

class XiaomiSuiteWidget(QWidget):
    """
    Unified Xiaomi Suite with Modern Hub Navigation
    """
    layout_type = QVBoxLayout

    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.widgets = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        # Navigation Bar (Back Button + Title)
        self.nav_bar = QFrame()
        self.nav_bar.setFixedHeight(60)
        self.nav_bar.setVisible(False) # Hidden on Hub
        self.nav_bar.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-bottom: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                margin-bottom: 15px;
            }}
        """)
        
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(0, 0, 0, 10)
        
        btn_back = QPushButton(" ←  Quay lại Hub")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.switch_to_page(0))
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: {ThemeManager.COLOR_GLASS_CARD};
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: bold;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
            QPushButton:hover {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']};
            }}
        """)
        nav_layout.addWidget(btn_back)
        nav_layout.addStretch()
        
        layout.addWidget(self.nav_bar)

        # Content Stack
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # 0. HUB
        self.hub = XiaomiHubWidget(self.adb)
        self.hub.switch_page.connect(self.switch_to_page)
        self.stack.addWidget(self.hub)
        
        # Tools
        self.opt_manager = OptimizationManager(self.adb)
        
        # Mapping for Hub tiles (indices):
        # 1: Debloater, 2: QuickTools, 3: Advanced, 4: OTA
        
        # Page 1: Debloater
        self.debloater = XiaomiDebloaterWidget(self.adb)
        self.add_to_stack(self.debloater)
        
        # Page 2: Quick Tools
        self.quick_tools = XiaomiQuickToolsWidget(self.adb)
        self.add_to_stack(self.quick_tools)
        
        # Page 3: Advanced Tools
        self.advanced = XiaomiAdvancedWidget(self.adb)
        self.add_to_stack(self.advanced)
        
        # Page 4: OTA Downloader
        self.ota = OTADownloaderWidget(self.adb)
        self.add_to_stack(self.ota)
        
        # Mapping continued:
        # 5: General Tweaks (Tối Ưu), 6: Fastboot, 7: App Store
        
        # Page 5: General Tweaks
        self.tweaks = GeneralTweaksWidget(self.adb, self.opt_manager)
        self.add_to_stack(self.tweaks)
        
        # Page 6: Fastboot
        self.fastboot = FastbootToolboxWidget(self.adb)
        self.add_to_stack(self.fastboot)
        
        # Page 7: App Store
        self.app_store = HyperOSAppsWidget(self.adb)
        self.add_to_stack(self.app_store)

    def add_to_stack(self, widget):
        self.stack.addWidget(widget)
        self.widgets.append(widget)

    def switch_to_page(self, index):
        self.stack.setCurrentIndex(index)
        self.nav_bar.setVisible(index != 0)
        
    def reset(self):
        for widget in self.widgets:
            if hasattr(widget, 'reset'):
                widget.reset()
        self.switch_to_page(0)

class GeneralToolsWidget(BaseTabbedWidget):
    """Unified General Tools & Dev Suite - Flat Hierarchy"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        
        # System Utils
        self.add_tool(CleanerWidget, "Dọn Rác", "🧹")
        self.add_tool(BatteryHealthWidget, "Sức Khỏe Pin", "🔋")
        self.add_tool(PermissionToolsWidget, "Cấp Quyền", "🔐")
        
        # Dev Tools
        self.add_tool(ConsoleWidget, "Console", "💻")
        self.add_tool(LogcatViewerWidget, "Logcat", "📜")
        self.add_tool(WirelessDebugWidget, "Wireless", "📡")
        
        # Others
        # self.add_tool(CloudSyncWidget, "Cloud Sync", "☁️")
        # self.add_tool(PluginManagerWidget, "Plugins", "🧩")
        self.add_tool(AdvancedCommandsWidget, "Lệnh Nâng Cao", "⚡")
