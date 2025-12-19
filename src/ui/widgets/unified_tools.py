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
from src.ui.widgets.xiaomi_optimizer import XiaomiOptimizerWidget # Kept for reference but not used in lists if unified
from src.ui.widgets.ota_downloader import OTADownloaderWidget, HyperOSAppsWidget
from src.ui.widgets.cloud_sync import CloudSyncWidget
from src.ui.widgets.plugin_manager_ui import PluginManagerWidget
from src.ui.widgets.battery_health import BatteryHealthWidget
from src.ui.widgets.cleaner import CleanerWidget
from src.ui.widgets.fastboot_toolbox import FastbootToolboxWidget
from src.ui.widgets.apk_analyzer import APKAnalyzerWidget
from src.core.optimization_manager import OptimizationManager
from src.ui.widgets.global_optimizer import GeneralTweaksWidget

class BaseTabbedWidget(QWidget):
    """Base class for tabbed tool containers"""
    def __init__(self, adb_manager, title):
        super().__init__()
        self.adb = adb_manager
        self.title = title
        self.widgets = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(self.title)
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                background: rgba(255, 255, 255, 0.5);
            }}
            QTabBar::tab {{
                background: rgba(255, 255, 255, 0.3);
                border: none;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QTabBar::tab:selected {{
                background: rgba(255, 255, 255, 0.8);
                font-weight: bold;
                border-bottom: 2px solid {ThemeManager.COLOR_ACCENT};
            }}
        """)
        layout.addWidget(self.tabs)
        
    def add_tool(self, widget_class, title, icon=""):
        # Instantiate widget
        widget = widget_class(self.adb)
        self.widgets.append(widget)
        self.add_tab(widget, title, icon) # Reuse add_tab logic

    def add_tab(self, widget, title, icon=""):
        """Add an instantiated widget, wrapped in ScrollArea"""
        from PySide6.QtWidgets import QScrollArea
        
        # Wrap in ScrollArea to prevent clipping on small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True) # Important!
        scroll.setWidget(widget)
        
        # Transparent style for scroll area so it blends in
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(0,0,0,0.05);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.2);
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        
        self.widgets.append(widget) # Keep validation ref
        self.tabs.addTab(scroll, f"{icon} {title}")
        
    def reset(self):
        for widget in self.widgets:
            if hasattr(widget, 'reset'):
                widget.reset()

class DevToolsWidget(BaseTabbedWidget):
    """Combines all developer tools"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager, "🛠️ Công cụ Lập trình (Dev Tools)")
        
        self.add_tool(ConsoleWidget, "Console", "💻")
        self.add_tool(LogcatViewerWidget, "Logcat", "📜")
        self.add_tool(WirelessDebugWidget, "Wireless Debug", "📡")
        self.add_tool(DNSConfigWidget, "DNS Config", "🌐")
        self.add_tool(ScriptEngineWidget, "Script Engine", "⚡")
        self.add_tool(APKAnalyzerWidget, "APK Analyzer", "📦")


class XiaomiSuiteWidget(BaseTabbedWidget):
    """Combines Xiaomi specific tools"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager, "🚀 Bộ công cụ Xiaomi")
        
        # Initialize Manager
        self.opt_manager = OptimizationManager(adb_manager)
        
        # 1. General Tweaks (Card UI)
        self.add_tab(GeneralTweaksWidget(adb_manager, self.opt_manager), "Tối Ưu Chung", "🚀")
        
        # 2. Xiaomi Ext
        self.add_tool(XiaomiOptimizerWidget, "Tiện Ích Xiaomi", "✨")
        
        # 3. Fastboot & Repair
        self.add_tool(FastbootToolboxWidget, "Fastboot Repair", "🔌")

        # 4. OTA
        self.add_tool(OTADownloaderWidget, "OTA Downloader", "☁️")
        
        # 5. Apps
        self.add_tool(HyperOSAppsWidget, "HyperOS Apps", "📱")

class SystemUtilsWidget(BaseTabbedWidget):
    """Combines system utilities"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager, "⚙️ Tiện ích Hệ thống")
        
        self.add_tool(CleanerWidget, "Dọn Rác (Cleaner)", "🗑️")
        self.add_tool(BatteryHealthWidget, "Battery Health", "🔋")
        self.add_tool(CloudSyncWidget, "Cloud Sync", "☁️")
        self.add_tool(PluginManagerWidget, "Plugins", "🧩")
