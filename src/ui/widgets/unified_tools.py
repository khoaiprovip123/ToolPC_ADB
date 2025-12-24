# src/ui/widgets/unified_tools.py
"""
Unified Tools Widgets
Group related widgets into tabbed containers to clean up the UI.
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel
)
from src.ui.theme_manager import ThemeManager

# Import widgets to wrap
from src.ui.widgets.console import ConsoleWidget
from src.ui.widgets.logcat_viewer import LogcatViewerWidget
from src.ui.widgets.wireless_debug import WirelessDebugWidget
from src.ui.widgets.dns_config import DNSConfigWidget
from src.ui.widgets.script_engine import ScriptEngineWidget
from src.ui.widgets.xiaomi_optimizer import (
    XiaomiOptimizerWidget, XiaomiDebloaterWidget, 
    XiaomiQuickToolsWidget, XiaomiAdvancedWidget
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
        layout.setContentsMargins(5, 5, 5, 5) # Compact margins
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

class XiaomiSuiteWidget(BaseTabbedWidget):
    """Unified Xiaomi Suite - Flat Hierarchy"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        
        self.opt_manager = OptimizationManager(adb_manager)
        
        self.add_tab(GeneralTweaksWidget(adb_manager, self.opt_manager), "Tối Ưu", "🚀")
        self.add_tool(XiaomiDebloaterWidget, "Gỡ App", "🗑️")
        self.add_tool(XiaomiQuickToolsWidget, "Tiện Ích", "✨")
        self.add_tool(XiaomiAdvancedWidget, "Nâng Cao", "⚙️")
        self.add_tool(FastbootToolboxWidget, "Fastboot", "🔌")
        self.add_tool(OTADownloaderWidget, "OTA Download", "☁️")
        self.add_tool(HyperOSAppsWidget, "Kho Apps", "📱")

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
