# src/ui/main_window.py
"""
Main Window - Application entry point
Style: Modern Glassmorphism with Colored Icons
"""

import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame,
    QComboBox, QStatusBar, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QColor, QFont

# Import Core
from src.core.adb.adb_manager import ADBManager, DeviceStatus

# Import Theme
from src.ui.theme_manager import ThemeManager

# Import Widgets
from src.ui.widgets.dashboard import DashboardWidget
from src.ui.widgets.app_manager import AppManagerWidget
from src.ui.widgets.file_manager import FileManagerWidget
# from src.ui.widgets.screen_mirror import ScreenMirrorWidget # Removed
from src.ui.widgets.unified_tools import DevToolsWidget, XiaomiSuiteWidget, SystemUtilsWidget
from src.ui.widgets.fastboot_toolbox import FastbootToolboxWidget
from src.ui.widgets.settings import SettingsWidget
from src.ui.widgets.notification_center import NotificationCenter
from src.core.plugin_manager import PluginManager


class Sidebar(QFrame):
    """Navigation Sidebar - iPadOS Style"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280) # iOS sidebar is wide
        self.apply_theme()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 30, 16, 30)
        layout.setSpacing(8)
        
        # App Logo/Title
        title_container = QFrame()
        title_container.setStyleSheet("background: transparent; border: none;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(12, 0, 0, 0)
        title_layout.setSpacing(14)
        
        # Logo with Android Green Gradient
        logo_frame = QFrame()
        logo_frame.setFixedSize(44, 44)
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #3DDC84, stop:1 #32B36C);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.2);
            }}
        """)
        # Using Android Robot Emoji
        logo_lbl = QLabel("🤖", logo_frame)
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet("color: white; font-size: 26px; background: transparent;")
        logo_lbl.setGeometry(0, 0, 44, 44)
        title_layout.addWidget(logo_frame)
        
        theme = ThemeManager.get_theme()
        title_text = QLabel("ADB Commander")
        title_text.setStyleSheet(f"""
            font-size: 19px;
            font-weight: 700;
            color: {theme['COLOR_TEXT_PRIMARY']};
            background: transparent;
            font-family: {ThemeManager.FONT_FAMILY};
            letter-spacing: -0.5px;
        """)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        layout.addWidget(title_container)
        
        layout.addSpacing(30)
        
        # Navigation Buttons
        self.buttons = []
        
        # Main
        self.add_nav_button("Tổng Quan", "dashboard", 0, layout, active=True)
        layout.addSpacing(20)
        
        # Quản lý
        self.add_group_label("QUẢN LÝ", layout)
        self.add_nav_button("Ứng Dụng", "apps", 1, layout)
        self.add_nav_button("Tệp Tin", "files", 3, layout)
        layout.addSpacing(20)
        
        # Công cụ
        self.add_group_label("TIỆN ÍCH", layout)
        self.add_nav_button("Bộ Xiaomi", "xiaomi", 2, layout)
        # Fastboot & Tools
        # self.add_nav_button("Fastboot", "fastboot", 4, layout) # Consolidated into Tools
        self.add_nav_button("Công cụ", "tools", 4, layout)
        self.add_nav_button("Dev Tools", "devtools", 5, layout)
        layout.addSpacing(20)
        
        # Hệ thống
        self.add_group_label("HỆ THỐNG", layout)
        self.add_nav_button("Cài Đặt", "settings", 6, layout)
        
        layout.addStretch()
        
        # Version
        self.version_label = QLabel("v2.4.0 • HyperOS Style")
        self.version_label.setStyleSheet(f"""
            color: {theme['COLOR_TEXT_SECONDARY']}; 
            padding: 12px; 
            background: transparent; 
            border: none; 
            font-size: 12px;
            font-weight: 500;
        """)
        self.version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.version_label)
    
    def apply_theme(self):
        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border-right: 1px solid {theme['COLOR_BORDER']};
            }}
        """)
    
    def add_group_label(self, text, layout):
        theme = ThemeManager.get_theme()
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {theme['COLOR_TEXT_SECONDARY']};
            font-size: 11px;
            font-weight: 600;
            padding-left: 14px;
            margin-bottom: 6px;
            background: transparent;
            font-family: {ThemeManager.FONT_FAMILY};
            text-transform: uppercase;
            opacity: 0.8;
        """)
        layout.addWidget(label)
    
    def add_nav_button(self, text, icon_key, index, layout, active=False):
        theme = ThemeManager.get_theme()
        icon_str = ThemeManager.get_icon(icon_key, "●")
        
        btn = QPushButton(f"  {icon_str}   {text}")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(50)
        
        # iOS Button Style
        hover_bg = theme['COLOR_GLASS_HOVER']
        active_bg = ThemeManager.COLOR_ACCENT + "25" # Stronger active background
        active_color = ThemeManager.COLOR_ACCENT
        
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 16px;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 500;
                color: {theme['COLOR_TEXT_PRIMARY']};
                background: transparent;
                font-family: {ThemeManager.FONT_FAMILY};
                margin-left: 8px;
                margin-right: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:checked {{
                background-color: rgba(126, 217, 87, 0.5); /* Lime Green 50% Opacity */
                color: {theme['COLOR_TEXT_PRIMARY']}; /* Keep text readable on light green */
                font-weight: 700;
                border: 1px solid rgba(126, 217, 87, 0.8);
                border-left: 4px solid #7ed957; /* Solid accent on left */
                padding-left: 12px;
            }}
        """)
        
        if active:
            btn.setChecked(True)
        
        btn.setProperty("page_index", index)
        self.buttons.append(btn)
        layout.addWidget(btn)


class DeviceSelector(QComboBox):
    """Device selection dropdown with modern styling"""
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        self.apply_theme()
    
    def apply_theme(self):
        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {theme['COLOR_GLASS_CARD']};
                border: 2px solid {theme['COLOR_BORDER']};
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-family: {ThemeManager.FONT_FAMILY};
            }}
            QComboBox:hover {{
                border: 2px solid {ThemeManager.COLOR_ACCENT};
                background-color: {theme['COLOR_GLASS_HOVER']};
            }}
            QComboBox:focus {{
                border: 2px solid {ThemeManager.COLOR_ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 12px;
            }}
        """)


class MainWindow(QMainWindow):
    """Main Application Window with Modern Theme"""
    
    def __init__(self, adb_manager=None):
        super().__init__()
        
        self.adb = adb_manager if adb_manager else ADBManager()
        
        self.setWindowTitle("Xiaomi ADB Commander")
        self.resize(1300, 850)
        
        self.apply_theme()
        
        # Initialize Plugins
        self.plugin_manager = PluginManager()
        self.plugin_manager.set_context(self)
        self.plugin_manager.discover_plugins()
        
        self.setup_ui()
        self.setup_timers()
        self.refresh_devices()
    
    def apply_theme(self):
        """Apply main theme"""
        self.setStyleSheet(ThemeManager.get_main_window_style())
    
    def setup_ui(self):
        """Setup main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        for btn in self.sidebar.buttons:
            btn.clicked.connect(self.on_nav_clicked)
        main_layout.addWidget(self.sidebar)
        
        # Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(28, 28, 28, 28)
        content_layout.setSpacing(20)
        
        # Header
        header = self.create_header()
        content_layout.addWidget(header)
        
        # Pages Stack
        self.pages = QStackedWidget()
        self.add_pages()
        content_layout.addWidget(self.pages)
        
        main_layout.addWidget(content_area)
        
        # Status Bar
        theme = ThemeManager.get_theme()
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {theme['COLOR_GLASS_WHITE']};
                color: {theme['COLOR_TEXT_SECONDARY']};
                border-top: 1px solid {theme['COLOR_BORDER']};
                font-family: {ThemeManager.FONT_FAMILY};
                padding: 8px 16px;
                font-size: 12px;
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✓ Sẵn sàng")

        # Initialize Notification Center
        # Parent to centralWidget to ensure correct Z-order and geometry as an overlay
        self.notif_center = NotificationCenter(self.centralWidget(), self.adb)

    def create_header(self):
        theme = ThemeManager.get_theme()
        header = QFrame()
        header.setObjectName("MainHeader")
        header.setStyleSheet(f"""
            #MainHeader {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border-radius: 16px;
                border: 1px solid {theme['COLOR_BORDER_LIGHT']};
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        header.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 18, 24, 18)
        
        # Page Title
        self.page_title = QLabel("Tổng Quan")
        self.page_title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 700;
            color: {theme['COLOR_TEXT_PRIMARY']};
            background: transparent;
            font-family: {ThemeManager.FONT_FAMILY};
        """)
        layout.addWidget(self.page_title)
        
        layout.addStretch()
        
        # Connection indicator
        self.conn_indicator = QLabel("●")
        self.conn_indicator.setStyleSheet("font-size: 12px; color: #10B981; background: transparent;")
        layout.addWidget(self.conn_indicator)
        layout.addSpacing(8)
        
        # Device Selector
        self.device_selector = DeviceSelector()
        self.device_selector.currentIndexChanged.connect(self.on_device_changed)
        layout.addWidget(self.device_selector)
        layout.addSpacing(12)
        
        # Refresh Button with icon
        refresh_btn = QPushButton("↻")
        refresh_btn.setToolTip("Làm mới danh sách thiết bị")
        refresh_btn.setFixedSize(44, 44)
        refresh_btn.clicked.connect(self.refresh_devices)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['COLOR_GLASS_CARD']};
                border-radius: 12px;
                border: 2px solid {theme['COLOR_BORDER']};
                font-size: 20px;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.COLOR_ACCENT}15;
                border: 2px solid {ThemeManager.COLOR_ACCENT};
                color: {ThemeManager.COLOR_ACCENT};
            }}
        """)
        
        # Control Center Button
        ctrl_btn = QPushButton("🎛️")
        ctrl_btn.setFixedSize(44, 44)
        ctrl_btn.setCursor(Qt.PointingHandCursor)
        ctrl_btn.setToolTip("Trung tâm Điều khiển")
        ctrl_btn.clicked.connect(lambda checked: self.toggle_notification_center(0))
        ctrl_btn.setStyleSheet(refresh_btn.styleSheet())
        
        # Notification Button
        notif_btn = QPushButton("🔔")
        notif_btn.setFixedSize(44, 44)
        notif_btn.setCursor(Qt.PointingHandCursor)
        notif_btn.setToolTip("Thông báo")
        notif_btn.clicked.connect(lambda checked: self.toggle_notification_center(1))
        notif_btn.setStyleSheet(refresh_btn.styleSheet())
        
        layout.addWidget(refresh_btn)
        layout.addSpacing(10)
        layout.addWidget(ctrl_btn)
        layout.addSpacing(10)
        layout.addWidget(notif_btn)
        
        return header
    
    def add_pages(self):
        """Initialize and add pages"""
        # 0. Dashboard
        self.dashboard = DashboardWidget(self.adb)
        self.pages.addWidget(self.dashboard)
        
        # 1. App Manager
        self.app_manager = AppManagerWidget(self.adb)
        self.pages.addWidget(self.app_manager)
        
        # 2. Xiaomi Suite
        self.xiaomi_suite = XiaomiSuiteWidget(self.adb)
        self.pages.addWidget(self.xiaomi_suite)
        
        # 3. File Manager
        self.file_manager = FileManagerWidget(self.adb)
        self.pages.addWidget(self.file_manager)
        
        # 4. Fastboot - Consolidated into SystemUtilsWidget
        # self.fastboot_tool = FastbootToolboxWidget(self.adb)
        # self.pages.addWidget(self.fastboot_tool)
        
        # 5. Unified Tools
        self.system_utils = SystemUtilsWidget(self.adb)
        self.pages.addWidget(self.system_utils)
        
        # 6. Dev Tools
        self.dev_tools = DevToolsWidget(self.adb)
        self.pages.addWidget(self.dev_tools)
        
        # 7. Settings
        self.settings = SettingsWidget(self.adb)
        self.pages.addWidget(self.settings)
    
    def setup_timers(self):
        """Setup background timers"""
        self.device_timer = QTimer()
        self.device_timer.timeout.connect(self.check_device_status)
        self.device_timer.start(5000)
    
    def on_nav_clicked(self):
        """Handle navigation"""
        btn = self.sender()
        index = btn.property("page_index")
        self.pages.setCurrentIndex(index)
        
        text = btn.text().strip().split("    ")[-1].strip()
        self.page_title.setText(text)
        self.status_bar.showMessage(f"✓ {text}")
    
    def refresh_devices(self):
        """Refresh connected devices list"""
        try:
            # 1. Try ADB
            adb_devices = self.adb.get_devices()
            current_serial = self.device_selector.currentData()
            
            self.device_selector.clear()
            
            detected_devices = []
            mode = "ADB"

            if adb_devices:
                for serial, status in adb_devices:
                    icon = "🟢" if status == DeviceStatus.ONLINE else "🔴"
                    detected_devices.append((f"{icon} {serial}", serial))
                self.conn_indicator.setStyleSheet("font-size: 12px; color: #10B981; background: transparent;")
            
            else:
                # 2. Try Fastboot Fallback
                fastboot_devices = self.adb.get_fastboot_devices()
                if fastboot_devices:
                    mode = "Fastboot"
                    for serial in fastboot_devices:
                        detected_devices.append((f"⚡ {serial} (Fastboot)", serial))
                    self.conn_indicator.setStyleSheet("font-size: 12px; color: #3B82F6; background: transparent;")
            
            # Populate Selector
            if detected_devices:
                for text, serial in detected_devices:
                    self.device_selector.addItem(text, serial)
                
                # Restore selection
                if current_serial:
                    index = self.device_selector.findData(current_serial)
                    if index >= 0:
                        self.device_selector.setCurrentIndex(index)
                elif self.device_selector.count() > 0:
                    self.device_selector.setCurrentIndex(0)
                
                self.status_bar.showMessage(f"✓ Tìm thấy {len(detected_devices)} thiết bị ({mode})")
            
            else:
                # No devices found
                self.device_selector.addItem("⚪ Không có thiết bị", None)
                self.conn_indicator.setStyleSheet("font-size: 12px; color: #EF4444; background: transparent;")
                self.status_bar.showMessage("⚠ Không có thiết bị kết nối")
                if hasattr(self, 'dashboard'):
                    self.dashboard.stop_updates()
            
        except Exception as e:
            self.status_bar.showMessage(f"⚠ Lỗi: {str(e)}")
    
    def check_device_status(self):
        """Periodic device check"""
        try:
            adb_devices = self.adb.get_devices()
            fastboot_devices = []
            if not adb_devices:
                fastboot_devices = self.adb.get_fastboot_devices()
                
            real_count = len(adb_devices) + len(fastboot_devices)
            
            # UI State
            ui_count = self.device_selector.count()
            
            # Check if UI has "No device" placeholder (count=1, data=None)
            is_placeholder = (ui_count == 1 and self.device_selector.itemData(0) is None)
            ui_real_count = 0 if is_placeholder else ui_count
            
            if real_count != ui_real_count:
                self.refresh_devices()
        except:
            pass
 
    def on_device_changed(self, index):
        """Handle device selection change"""
        serial = self.device_selector.itemData(index)
        
        if serial:
            self.adb.select_device(serial)
            
            # Check mode from text
            is_fastboot = "Fastboot" in self.device_selector.itemText(index)
            
            if is_fastboot:
                self.status_bar.showMessage(f"✓ Thiết bị Fastboot: {serial}")
                if hasattr(self, 'dashboard'):
                    self.dashboard.start_updates()
                # Do not initialize App/File managers in Fastboot mode
            else:
                self.status_bar.showMessage(f"✓ Đã chọn thiết bị: {serial}")
                
                if hasattr(self, 'app_manager'): self.app_manager.reset()
                if hasattr(self, 'file_manager'): self.file_manager.reset()
                if hasattr(self, 'screen_mirror'): self.screen_mirror.reset()
                if hasattr(self, 'dev_tools'): self.dev_tools.reset() 
                if hasattr(self, 'xiaomi_suite'): self.xiaomi_suite.reset()
                if hasattr(self, 'system_utils'): self.system_utils.reset()
                
                if hasattr(self, 'dashboard'):
                    self.dashboard.start_updates()
                
                try:
                    brand = self.adb.shell("getprop ro.product.brand")
                    if brand and "Xiaomi" in brand:
                        self.status_bar.showMessage(f"✓ Thiết bị Xiaomi: {serial}")
                except:
                    pass
        else:
            if hasattr(self, 'dashboard'):
                self.dashboard.stop_updates()
    
    def closeEvent(self, event):
        """Handle app close"""
        if hasattr(self, 'dashboard'):
            self.dashboard.stop_updates()
        if hasattr(self, 'screen_mirror'):
            self.screen_mirror.stop_mirroring()
        event.accept()

    def toggle_notification_center(self, tab_index=None):
        if hasattr(self, 'notif_center'):
            self.notif_center.toggle(tab_index)
