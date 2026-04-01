# src/ui/main_window.py
"""
Main Window - Application entry point
Style: Modern Glassmorphism with Colored Icons
"""

import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame,
    QComboBox, QStatusBar, QMessageBox, QGraphicsDropShadowEffect,
    QApplication, QScrollArea
)
from PySide6.QtCore import Qt, QSize, QTimer, QEvent, Signal, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap
import os

# Import Core
from src.core.adb.adb_manager import ADBManager, DeviceStatus
from src.core.update_manager import UpdateChecker
from src.core.log_manager import LogManager

# Import Theme
from src.ui.theme_manager import ThemeManager

# Import Widgets
from src.ui.widgets.dashboard import DashboardWidget
# from .widgets.app_manager import AppManagerWidget # Wrapped in AppsAndAPKPage
from src.ui.widgets.file_manager import FileManagerWidget
# Redundant imports removed after page refactoring

from src.ui.widgets.settings import SettingsWidget
from src.ui.widgets.notification_center import NotificationCenter
from src.ui.widgets.badge_button import NotifBadgeButton
from src.ui.dialogs.update_dialog import UpdateNotificationDialog, UpdateProgressDialog
from src.core.plugin_manager import PluginManager

from src.ui.pages import (
    AboutPage, AppsAndAPKPage, XiaomiToolsPage, 
    ScreenAndDebugPage, DeveloperPage
)
from src.core.resource_utils import get_resource_path


class Sidebar(QFrame):
    """Navigation Sidebar - iPadOS Style"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280) # iOS sidebar is wide
        self.full_width = 280
        self.collapsed_width = 80
        self.is_collapsed = False
        
        self.group_labels = []
        self.nav_buttons = []
        self.title_label = None
        
        self.apply_theme()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 20, 16, 20)
        self.main_layout.setSpacing(10)
        
        # App Logo/Title
        self.title_container = QFrame()
        self.title_container.setStyleSheet("background: transparent; border: none;")
        self.title_layout = QHBoxLayout(self.title_container)
        self.title_layout.setContentsMargins(12, 0, 0, 0)
        self.title_layout.setSpacing(14)
        
        # Logo with Android Green Gradient
        logo_frame = QFrame()
        logo_frame.setFixedSize(44, 44)
        logo_frame.setStyleSheet(ThemeManager.get_sidebar_logo_style())
        
        # Use custom logo image instead of emoji
        logo_lbl = QLabel(logo_frame)
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setGeometry(0, 0, 44, 44)
        
        # Load logo image
        logo_path = get_resource_path('resources', 'logo.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(scaled_pixmap)
        else:
            # Fallback to emoji if image not found
            logo_lbl.setText("🤖")
            logo_lbl.setStyleSheet("color: white; font-size: 26px; background: transparent;")
        
        self.title_layout.addWidget(logo_frame)
        
        theme = ThemeManager.get_theme()
        self.title_label = QLabel("ADB Commander")
        self.title_label.setStyleSheet(ThemeManager.get_sidebar_title_style())
        self.title_layout.addWidget(self.title_label)
        self.title_spacer = self.title_layout.addStretch()
        self.main_layout.addWidget(self.title_container)
        
        self.main_layout.addSpacing(20)
        
        # === SCROLLABLE NAVIGATION AREA ===
        self.nav_area = QScrollArea()
        self.nav_area.setWidgetResizable(True)
        self.nav_area.setFrameShape(QFrame.NoFrame)
        self.nav_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 4px; background: transparent; }
            QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.2); border-radius: 2px; }
        """)
        
        self.nav_content = QWidget()
        self.nav_content.setStyleSheet("background: transparent;")
        self.nav_layout = QVBoxLayout(self.nav_content)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(5) # Compact spacing
        
        # Navigation Buttons (FLATTENED 8-ITEM STRUCTURE)
        self.buttons = []
        
        # 1. Main
        self.add_nav_button("Tổng Quan", "dashboard", 0, active=True)
        self.nav_layout.addSpacing(10)
        
        # 2. Quản lý
        self.add_group_label("QUẢN LÝ")
        self.add_nav_button("Ứng Dụng & APK", "apps", 1)
        self.add_nav_button("Quản Lý Tệp Tin", "files", 2)
        self.nav_layout.addSpacing(10)
        
        # 3. Công cụ
        self.add_group_label("CÔNG CỤ")
        self.add_nav_button("Công Cụ Xiaomi", "xiaomi", 3)
        self.add_nav_button("Màn Hình & Debug", "debug", 4)
        self.add_nav_button("Dành Cho Dev", "developer", 5)
        
        self.nav_layout.addSpacing(10)
        
        # 4. Hệ thống
        self.add_group_label("HỆ THỐNG")
        self.add_nav_button("Cài Đặt", "settings", 6)
        self.add_nav_button("Giới Thiệu", "about", 7)
        
        self.nav_layout.addStretch()
        
        self.nav_area.setWidget(self.nav_content)
        self.main_layout.addWidget(self.nav_area)
        
        # Version - Moved back to Main Layout (Bottom)
        from src.version import __version__
        self.version_label = QLabel(f"v{__version__} • HyperOS Style")
        self.version_label.setStyleSheet(f"color: {theme['COLOR_TEXT_SECONDARY']}; padding: 12px; font-size: 12px; font-weight: 500; border: none; background: transparent;")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.version_label)
        
        # Bottom Toggle Button - Moved back to Main Layout (Bottom)
        self.collapse_btn = QPushButton("  ☰   Thu gọn")
        self.collapse_btn.setFixedHeight(50)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setStyleSheet(ThemeManager.get_nav_button_style("16px", alignment="left"))
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        self.main_layout.addWidget(self.collapse_btn)
        
        # NOTE: No stretch here, content will define its height. 
        # But if window is tall, we need one stretch to keep footer at bottom.
        # self.main_layout.addStretch() 
        # Actually, let's NOT add stretch to the main sidebar layout if we want it to hug.
        # But for QMainWindow compatibility, we usually want it.
        

    
    def apply_theme(self):
        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {theme['COLOR_BG_MAIN']}E6;
                border-radius: {ThemeManager.RADIUS_CARD};
                border: 0.5px solid {theme['COLOR_BORDER']};
            }}
        """)
        
        # Add elevation shadow for floating look
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
    
    def add_group_label(self, text):
        theme = ThemeManager.get_theme()
        label = QLabel(text)
        label.setStyleSheet(ThemeManager.get_sidebar_group_label_style())
        self.nav_layout.addWidget(label)
        self.group_labels.append(label)
    
    def add_nav_button(self, text, icon_key, index, active=False):
        theme = ThemeManager.get_theme()
        icon_val = ThemeManager.get_icon(icon_key, "●")
        
        btn = QPushButton(text)
        
        # Check for image icon
        icon_path = get_resource_path('resources', 'icons', icon_val)
        
        has_icon = False
        if icon_val.endswith(('.png', '.svg')) and os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(26, 26))
            has_icon = True
        else:
            # Fallback to emoji text
            btn.setText(f"  {icon_val}   {text}")
            
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(50)
        
        padding_left = "16px" if has_icon else "16px"
        btn.setStyleSheet(ThemeManager.get_nav_button_style(padding_left))
        
        if active:
            btn.setChecked(True)
        
        btn.setProperty("page_index", index)
        btn.setProperty("full_text", text)
        btn.setProperty("has_icon", has_icon)
        btn.setProperty("icon_key", icon_key)
        
        self.buttons.append(btn)
        self.nav_buttons.append(btn)
        self.nav_layout.addWidget(btn)
        
        return btn

    def toggle_collapse(self):
        """Toggle between expanded and collapsed states with animation"""
        self.is_collapsed = not self.is_collapsed
        
        # Target width
        target_width = self.collapsed_width if self.is_collapsed else self.full_width
        
        # Start animation
        self.anim = QPropertyAnimation(self, b"minimumWidth")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(target_width)
        self.anim.setEasingCurve(QEasingCurve.InOutQuart)
        
        self.anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.anim_max.setDuration(300)
        self.anim_max.setStartValue(self.width())
        self.anim_max.setEndValue(target_width)
        self.anim_max.setEasingCurve(QEasingCurve.InOutQuart)
        
        self.anim.start()
        self.anim_max.start()
        
        # Update visibility of text elements
        self.title_label.setVisible(not self.is_collapsed)
        for label in self.group_labels:
            label.setVisible(not self.is_collapsed)
        
        if self.is_collapsed:
            self.main_layout.setContentsMargins(0, 30, 0, 30)
            self.title_layout.setContentsMargins(0, 0, 0, 0)
            self.title_layout.setSpacing(0)
            self.title_layout.setAlignment(Qt.AlignCenter)
            self.main_layout.setAlignment(self.title_container, Qt.AlignCenter)
            if hasattr(self, 'title_spacer'):
                self.title_layout.setStretchFactor(self.title_spacer, 0)
            
            self.collapse_btn.setText("☰")
            self.collapse_btn.setStyleSheet(ThemeManager.get_nav_button_style("0px", alignment="center"))
            self.collapse_btn.setFixedWidth(80)
        else:
            self.main_layout.setContentsMargins(16, 30, 16, 30)
            self.title_layout.setContentsMargins(12, 0, 0, 0)
            self.title_layout.setSpacing(14)
            self.title_layout.setAlignment(Qt.AlignLeft)
            self.main_layout.setAlignment(self.title_container, Qt.AlignLeft)
            if hasattr(self, 'title_spacer'):
                self.title_layout.setStretchFactor(self.title_spacer, 1)
            
            self.collapse_btn.setText("  ☰   Thu gọn")
            self.collapse_btn.setStyleSheet(ThemeManager.get_nav_button_style("16px", alignment="left"))
            self.collapse_btn.setFixedWidth(248) # Matching full width minus margins
            
        self.version_label.setVisible(not self.is_collapsed)
        
        # Update button text/padding
        for btn in self.nav_buttons:
            has_icon = btn.property("has_icon")
            icon_key = btn.property("icon_key")
            icon_val = ThemeManager.get_icon(icon_key, "●")
            
            if self.is_collapsed:
                if has_icon:
                    btn.setText("") # Show image icon only
                else:
                    btn.setText(icon_val) # Show emoji only
                
                btn.setToolTip(btn.property("full_text"))
                # Perfect Centering: alignment='center', padding=0
                btn.setStyleSheet(ThemeManager.get_nav_button_style("0px", alignment="center"))
            else:
                full_text = btn.property("full_text")
                if has_icon:
                    btn.setText(full_text)
                else:
                    btn.setText(f"  {icon_val}   {full_text}")
                
                btn.setToolTip("")
                # Use default padding for expanded mode
                btn.setStyleSheet(ThemeManager.get_nav_button_style("16px", "12px", alignment="left"))


class DeviceSelector(QComboBox):
    """Device selection dropdown with modern styling"""
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        self.apply_theme()
    
    def apply_theme(self):
        theme = ThemeManager.get_theme()
        self.setStyleSheet(ThemeManager.get_input_style())


class MainWindow(QMainWindow):
    """Main Application Window with Modern Theme"""
    
    def __init__(self, adb_manager=None):
        super().__init__()
        
        self.adb = adb_manager if adb_manager else ADBManager()
        
        self.setWindowTitle("Xiaomi ADB Commander")
        
        # Set window icon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Balanced Resolution: 1400x800 (as requested by user)
        # Using setMinimumSize to ensure usability while allowing expansion
        self.resize(1400, 800)
        self.setMinimumSize(1100, 600)
        
        # Restore Maximize Button/Resizability
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        # Initialize Settings & Theme
        from PySide6.QtCore import QSettings
        self.settings = QSettings("VanKhoai", "XiaomiADBCommander")
        
        # Load and apply saved theme
        saved_theme = self.settings.value("theme", "light")
        ThemeManager.set_theme(saved_theme)
        self.apply_theme()
        
        # Initialize Plugins
        self.plugin_manager = PluginManager()
        self.plugin_manager.set_context(self)
        self.plugin_manager.discover_plugins()
        
        self.setup_ui()
        self.setup_timers()
        self.refresh_devices()
        
        # Check for updates after startup (delayed)
        auto_check = self.settings.value("auto_check_updates", True, type=bool)
        if auto_check:
            # Delay 3 seconds to let UI load first
            QTimer.singleShot(3000, self.check_for_updates_startup)

        # Apply Window Acrylic Effect (Glass)
        try:
            from src.core.utils.window_effect import WindowEffect
            self.window_effect = WindowEffect()
            # Set translucent background for Qt
            self.setAttribute(Qt.WA_TranslucentBackground)
            # Apply Acrylic: use 0x01FFFFFF (very slight white tint) or adapt to theme
            # Wait for show event to ensure hwnd is valid, but usually safe here if widget created
            # Better to do it in showEvent or after a simplified timer
            QTimer.singleShot(100, self.apply_window_effect)
        except Exception as e:
            print(f"Effect Error: {e}")

    def apply_window_effect(self):
        """Apply Acrylic Blur based on theme"""
        if hasattr(self, 'window_effect'):
            # Detect Dark Mode for tint
            is_dark = ThemeManager.is_dark()
            # Low alpha (0x20-0x60) for crystal clear glass effect
            # Light Mode: 0x30FCE5B3 (Sea Blue tint - Lower alpha for more glassiness)
            # Dark Mode: 0x40000000 (Black tint)
            tint = 0x40000000 if is_dark else 0x30FCE5B3
            self.window_effect.apply_acrylic(self.winId(), tint)

    def apply_theme(self):
        """Apply main theme"""
        self.setStyleSheet(ThemeManager.get_main_window_style())

    def setup_ui(self):
        """Setup main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Install Global Event Filter for robust Auto-Hide (catches clicks on other widgets)
        QApplication.instance().installEventFilter(self)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20) # Floating Margins
        main_layout.setSpacing(20)

        # Sidebar
        self.sidebar = Sidebar()
        for btn in self.sidebar.buttons:
            btn.clicked.connect(self.on_nav_clicked)
        main_layout.addWidget(self.sidebar)

        # Content Area (Right Side)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0) # Content area margins handled by main_layout spacing
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
        self.status_bar.setStyleSheet(ThemeManager.get_statusbar_style())
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✓ Sẵn sàng")

        # Initialize Notification Center
        # Parent to centralWidget to ensure correct Z-order and geometry as an overlay
        self.notif_center = NotificationCenter(self.centralWidget(), self.adb)
        
        # Connect LogManager to Notification Center
        from src.core.log_manager import LogManager
        log_manager = LogManager.get_instance()
        log_manager.log_signal.connect(self.on_log_received)

    def create_header(self):
        theme = ThemeManager.get_theme()
        header = QFrame()
        header.setObjectName("MainHeader")
        header.setStyleSheet(ThemeManager.get_header_frame_style())

        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 6)
        header.setGraphicsEffect(shadow)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        # Page Title
        self.page_title = QLabel("Tổng Quan")
        self.page_title.setStyleSheet(ThemeManager.get_header_title_style())
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
        layout.addSpacing(10)

        # Refresh Button with icon
        refresh_btn = QPushButton("↻")
        refresh_btn.setToolTip("Làm mới danh sách thiết bị")
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.clicked.connect(self.refresh_devices)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(ThemeManager.get_icon_button_style())

        # Control Center Button
        ctrl_btn = QPushButton()
        ctrl_btn.setFixedSize(36, 36)
        ctrl_btn.setCursor(Qt.PointingHandCursor)
        ctrl_btn.setToolTip("Trung tâm Điều khiển")
        ctrl_btn.clicked.connect(lambda checked: self.toggle_notification_center(0))
        ctrl_btn.setStyleSheet(ThemeManager.get_icon_button_style())

        # Load control center icon
        import os
        ctrl_icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icons', 'control_center.png')
        if os.path.exists(ctrl_icon_path):
            ctrl_btn.setIcon(QIcon(ctrl_icon_path))
            ctrl_btn.setIconSize(QSize(18, 18))
        else:
            ctrl_btn.setText("🎛️")

        # Notification Button (B1: đổi sang NotifBadgeButton có badge)
        notif_icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icons', 'notification.png')
        self.notif_btn = NotifBadgeButton(notif_icon_path, tooltip="Thông báo")
        self.notif_btn.clicked.connect(lambda checked: self.toggle_notification_center(1))

        layout.addWidget(refresh_btn)
        layout.addSpacing(8)
        layout.addWidget(ctrl_btn)
        layout.addSpacing(8)
        layout.addWidget(self.notif_btn)

        return header

    def add_pages(self):
        """Initialize and add pages"""
        # 0. Dashboard
        self.dashboard = DashboardWidget(self.adb)
        self.pages.addWidget(self.dashboard)

        # 1. Apps & APKs (Replaces standalone App Manager)
        self.apps_and_apk = AppsAndAPKPage(self.adb)
        self.pages.addWidget(self.apps_and_apk)

        # 2. File Manager
        self.file_manager = FileManagerWidget(self.adb)
        self.pages.addWidget(self.file_manager)

        # 3. Xiaomi Tools (Replaces Xiaomi Suite Hub)
        self.xiaomi_tools = XiaomiToolsPage(self.adb)
        self.pages.addWidget(self.xiaomi_tools)

        # 4. Screen & Debug
        self.screen_debug = ScreenAndDebugPage(self.adb)
        self.pages.addWidget(self.screen_debug)

        # 5. Developer (Replaces General Tools)
        self.developer = DeveloperPage(self.adb)
        self.pages.addWidget(self.developer)

        # 5. Settings
        self.settings_widget = SettingsWidget(self.adb)
        self.pages.addWidget(self.settings_widget)

        # 6. About
        self.about_page = AboutPage(self.adb)
        self.pages.addWidget(self.about_page)

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

        text = btn.property("full_text")
        self.page_title.setText(text)
        self.status_bar.showMessage(f"✓ {text}")
        
        # Animation: Fade In New Page
        current_page = self.pages.currentWidget()
        if current_page:
            ThemeManager.AnimationHelper.fade_in(current_page, duration=250)

    def refresh_devices(self):
        """Refresh connected devices list in background"""
        if hasattr(self, '_refresh_worker') and self._refresh_worker.isRunning():
            return

        class RefreshWorker(QThread):
            result_ready = Signal(list, str)
            def __init__(self, adb):
                super().__init__()
                self.adb = adb
            def run(self):
                try:
                    adb_devices = self.adb.get_devices()
                    mode = "ADB"
                    detected = []
                    if adb_devices:
                        for serial, status in adb_devices:
                            icon = "🟢" if status == DeviceStatus.ONLINE else "🔴"
                            detected.append((f"{icon} {serial}", serial))
                    else:
                        fastboot_devices = self.adb.get_fastboot_devices()
                        if fastboot_devices:
                            mode = "Fastboot"
                            for serial in fastboot_devices:
                                detected.append((f"⚡ {serial} (Fastboot)", serial))
                    self.result_ready.emit(detected, mode)
                except Exception as e:
                    self.result_ready.emit([], str(e))

        self._refresh_worker = RefreshWorker(self.adb)
        self._refresh_worker.result_ready.connect(self.on_refresh_finished)
        self._refresh_worker.start()

    def on_refresh_finished(self, detected_devices, mode_or_error):
        if not isinstance(detected_devices, list): # Error occurred
            self.status_bar.showMessage(f"⚠ Lỗi: {mode_or_error}")
            return

        current_serial = self.device_selector.currentData()
        self.device_selector.clear()

        if detected_devices:
            for text, serial in detected_devices:
                self.device_selector.addItem(text, serial)
            
            if current_serial:
                index = self.device_selector.findData(current_serial)
                if index >= 0:
                    self.device_selector.setCurrentIndex(index)
            elif self.device_selector.count() > 0:
                self.device_selector.setCurrentIndex(0)
            
            # Check for unauthorized
            is_unauth = any("🔴" in t for t, s in detected_devices)
            if is_unauth:
                self.status_bar.showMessage(f"⚠ Có thiết bị chưa được ủy quyền! Vui lòng chấp nhận trên điện thoại.")
            else:
                self.status_bar.showMessage(f"✓ Tìm thấy {len(detected_devices)} thiết bị ({mode_or_error})")
        else:
            self.device_selector.addItem("⚪ Không có thiết bị", None)
            self.conn_indicator.setStyleSheet("font-size: 12px; color: #EF4444; background: transparent;")
            self.status_bar.showMessage("⚠ Không có thiết bị kết nối")
            if hasattr(self, 'dashboard'):
                self.dashboard.stop_updates()
    
    def check_device_status(self):
        """Periodic device check (Background to prevent UI stutter)"""
        if hasattr(self, '_check_worker') and self._check_worker.isRunning():
            return

        class CheckWorker(QThread):
            count_ready = Signal(int)
            def __init__(self, adb):
                super().__init__()
                self.adb = adb
            def run(self):
                try:
                    adb_devices = self.adb.get_devices()
                    fastboot_devices = []
                    if not adb_devices:
                        fastboot_devices = self.adb.get_fastboot_devices()
                    self.count_ready.emit(len(adb_devices) + len(fastboot_devices))
                except Exception as _e:
                    self.count_ready.emit(-1)

        self._check_worker = CheckWorker(self.adb)
        
        def on_check_finished(real_count):
            if real_count == -1: return
            
            # Smart comparison: Get current serials from UI
            ui_serials = set()
            for i in range(self.device_selector.count()):
                data = self.device_selector.itemData(i)
                if data: ui_serials.add(data)
                
            # We can't know the REAL serials from check_worker easily without changing it to return list
            # But we can assume if real_count != ui_count, we refresh
            # To avoid loop: Only refresh if count differs OR if valid items mismatch
            
            # Simple fix: Throttle refresh. If we just refreshed < 2s ago, don't refresh.
            # But better: CheckWorker should return list.
            
            # However, since I cannot easily change CheckWorker signature without risk, 
            # I will check against ui_count AND ensure we don't loop.
            
            ui_count = self.device_selector.count()
            # If selector has "No devices" placeholder, count is 0 for comparison
            is_placeholder = (ui_count == 1 and self.device_selector.itemData(0) is None)
            ui_real_count = 0 if is_placeholder else ui_count
            
            if real_count != ui_real_count:
                print(f"Device Check: Count mismatch (Real: {real_count} vs UI: {ui_real_count}). Refreshing...")
                self.refresh_devices()

        self._check_worker.count_ready.connect(on_check_finished)
        self._check_worker.start()
 
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
                
                # Reset widgets on device change
                if hasattr(self, 'apps_and_apk'):
                    self.apps_and_apk.reset()
                if hasattr(self, 'file_manager'):
                    self.file_manager.reset()
                if hasattr(self, 'xiaomi_tools'):
                    self.xiaomi_tools.reset()
                if hasattr(self, 'screen_debug'):
                    self.screen_debug.reset()
                if hasattr(self, 'developer'):
                    self.developer.reset()
                
                if hasattr(self, 'dashboard'):
                    self.dashboard.start_updates()
                
                try:
                    brand = self.adb.shell("getprop ro.product.brand")
                    if brand and "Xiaomi" in brand:
                        self.status_bar.showMessage(f"✓ Thiết bị Xiaomi: {serial}")
                except Exception as _e:

                    pass  # TODO: consider LogManager.log
        else:
            if hasattr(self, 'dashboard'):
                self.dashboard.stop_updates()
    
    def closeEvent(self, event):
        """Handle app close"""
        # Stop timers
        if hasattr(self, 'device_timer'):
            self.device_timer.stop()
            
        # Stop workers if running — use requestInterruption for graceful shutdown
        if hasattr(self, '_refresh_worker') and self._refresh_worker.isRunning():
            self._refresh_worker.requestInterruption()
            self._refresh_worker.wait(3000)  # Wait up to 3s for graceful exit
            
        if hasattr(self, '_check_worker') and self._check_worker.isRunning():
            self._check_worker.requestInterruption()
            self._check_worker.wait(3000)  # Wait up to 3s for graceful exit

        if hasattr(self, 'dashboard'):
            self.dashboard.stop_updates()
        if hasattr(self, 'notif_center'):
            self.notif_center.stop_mirroring()
        event.accept()

    def resizeEvent(self, event):
        """Ensure Notification Center stays on the right edge"""
        super().resizeEvent(event)
        if hasattr(self, 'notif_center') and self.notif_center.isVisible():
            # Adjust Y position to account for header/toolbar
            parent_rect = self.centralWidget().rect()
            self.notif_center.setFixedHeight(parent_rect.height())
            self.notif_center.setGeometry(
                parent_rect.width() - self.notif_center.width(),
                0,
                self.notif_center.width(),
                parent_rect.height()
            )

    def on_log_received(self, title: str, message: str, level: str):
        """Handle log signal from LogManager and forward to notification center"""
        level_map = {
            'error': 'error', 'warning': 'warning',
            'info': 'info', 'success': 'success'
        }
        notif_type = level_map.get(level.lower(), 'info')

        if hasattr(self, 'notif_center'):
            # Pass everything separately to keep cards clean
            self.notif_center.add_notification(notif_type, message, title)

        # B1: Tăng badge nếu notification panel đang đóng
        if hasattr(self, 'notif_btn') and hasattr(self, 'notif_center'):
            if not self.notif_center.isVisible():
                self.notif_btn.increment(level.lower())

    def eventFilter(self, obj, event):
        """Handle global events for Auto-Hide logic"""
        if event.type() == QEvent.MouseButtonPress:
            if hasattr(self, 'notif_center') and self.notif_center.isVisible():
                # Global Event Filter (via QApplication) logic
                # Check if the object receiving the click is part of the Notification Center
                
                # 1. Get widget under mouse
                widget_under_mouse = QApplication.widgetAt(event.globalPos()) if hasattr(event, 'globalPos') else QApplication.widgetAt(event.globalPosition().toPoint())
                
                # 2. Check hierarchy
                is_inside = False
                if widget_under_mouse:
                    # Check if widget is notif_center or a child of it
                    if widget_under_mouse == self.notif_center or self.notif_center.isAncestorOf(widget_under_mouse):
                        is_inside = True
                
                # 3. Check Toggle Buttons (Prevent immediate reopen)
                # We need to see if the click target is one of our toggle buttons
                is_toggle_btn = False
                if widget_under_mouse:
                    # Heuristic: Check tooltip or parent
                    # Simplified: If we click outside, we hide.
                    # The toggle button click event will process AFTER this filter? 
                    # If this filter returns False, event propagates.
                    # If Toggle Button receives click, it toggles (Shows/Hides).
                    # If Update: Open -> Click Toggle -> (Filter: Hides) -> (Button: Toggles -> Shows again?)
                    # Fix: If clicking toggle button, DO NOTHING in filter.
                    
                    # Identify toggle buttons by property or object
                    # We can iterate sidebar buttons or check tooltip "Thông báo" / "Trung tâm Điều khiển"
                    if isinstance(widget_under_mouse, QPushButton):
                        tip = widget_under_mouse.toolTip()
                        if tip in ["Thông báo", "Trung tâm Điều khiển"]:
                            is_toggle_btn = True
                        # Also check icon parents if QIcon? (No, widget is button)
                
                if not is_inside and not is_toggle_btn:
                    # Clicked outside!
                    self.notif_center.toggle()
                    # Do not consume event, let it trigger the background click
        
        return super().eventFilter(obj, event)

    def update_menu_visibility(self, menu_name, is_visible):
        """Update sidebar menu button visibility"""
        if menu_name == 'advanced' and hasattr(self.sidebar, 'advanced_btn'):
            self.sidebar.advanced_btn.setVisible(is_visible)

    def toggle_notification_center(self, tab_index=None):
        if hasattr(self, 'notif_center'):
            self.notif_center.toggle(tab_index)
            # B1: Reset badge khi user mở notification panel (tab 1)
            if tab_index == 1 and hasattr(self, 'notif_btn'):
                self.notif_btn.reset()
    
    def check_for_updates_startup(self):
        """Check for updates silently on startup"""
        try:
            include_prerelease = self.settings.value("include_prerelease", False, type=bool)
            self.update_checker = UpdateChecker(include_prerelease)
            self.update_checker.update_found.connect(self.on_startup_update_found)
            # No handler for no_update - silent on startup
            self.update_checker.error_occurred.connect(
                lambda err: LogManager.log("Update", f"Kiểm tra cập nhật lỗi: {err}", "warning")
            )
            self.update_checker.start()
            
            # Update last check time
            from PySide6.QtCore import QDateTime
            current_time = QDateTime.currentDateTime().toString(Qt.ISODate)
            self.settings.setValue("last_update_check", current_time)
        except Exception as _e:
            LogManager.log("Update", f"Lỗi khởi tạo update checker: {_e}", "warning")
    
    def on_startup_update_found(self, update_info: dict):
        """Handle update found on startup"""
        try:
            # Check if this version should be skipped
            skip_version = self.settings.value("skip_version", "")
            if skip_version == update_info['version']:
                return  # Silently skip
            
            # Show update dialog
            dialog = UpdateNotificationDialog(update_info, self)
            result = dialog.exec()
            
            if dialog.user_choice == 'update':
                # Start download
                self.start_update_download(update_info)
            elif dialog.user_choice == 'skip':
                # Save skip version
                self.settings.setValue("skip_version", update_info['version'])
        except Exception as _e:
            LogManager.log("Update", f"Lỗi hiển thị update dialog: {_e}", "warning")
    
    def start_update_download(self, update_info: dict):
        """Start downloading update"""
        try:
            progress_dialog = UpdateProgressDialog(update_info, self)
            progress_dialog.start_download()
            progress_dialog.exec()
        except Exception as e:
            LogManager.log("Lỗi", f"Không thể tải cập nhật:\n{str(e)}", "warning")
