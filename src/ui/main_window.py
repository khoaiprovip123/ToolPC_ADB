# src/ui/main_window.py
"""
Main Window - Application entry point
Style: Modern Glassmorphism with Colored Icons
"""

import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QPushButton, QLabel, QFrame,
    QComboBox, QStatusBar, QMessageBox, QGraphicsDropShadowEffect,
    QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer, QEvent, Signal, QThread
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap

# Import Core
from src.core.adb.adb_manager import ADBManager, DeviceStatus
from src.core.update_manager import UpdateChecker

# Import Theme
from src.ui.theme_manager import ThemeManager

# Import Widgets
from src.ui.widgets.dashboard import DashboardWidget
from src.ui.widgets.app_manager import AppManagerWidget
from src.ui.widgets.file_manager import FileManagerWidget
# from src.ui.widgets.screen_mirror import ScreenMirrorWidget # Removed
from src.ui.widgets.unified_tools import (
    XiaomiSuiteWidget, GeneralToolsWidget
)
from src.ui.widgets.settings import SettingsWidget
from src.ui.widgets.notification_center import NotificationCenter
from src.ui.dialogs.update_dialog import UpdateNotificationDialog, UpdateProgressDialog
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
        
        # Use custom logo image instead of emoji
        logo_lbl = QLabel(logo_frame)
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setGeometry(0, 0, 44, 44)
        
        # Load logo image
        import os
        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'logo.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(scaled_pixmap)
        else:
            # Fallback to emoji if image not found
            logo_lbl.setText("🤖")
            logo_lbl.setStyleSheet("color: white; font-size: 26px; background: transparent;")
        
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
        self.add_nav_button("Tệp Tin", "files", 2, layout)
        layout.addSpacing(20)
        
        # Công cụ
        self.add_group_label("CÔNG CỤ", layout)
        self.add_nav_button("Bộ Xiaomi", "xiaomi", 3, layout)
        self.add_nav_button("Công Cụ Khác", "tools", 4, layout)
        layout.addSpacing(20)
        
        # Hệ thống
        self.add_group_label("HỆ THỐNG", layout)
        self.add_nav_button("Cài Đặt", "settings", 5, layout)
        
        layout.addStretch()
        
        # Version
        from src.version import __version__
        self.version_label = QLabel(f"v{__version__} • HyperOS Style")
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
        icon_val = ThemeManager.get_icon(icon_key, "●")
        
        btn = QPushButton(text)
        
        # Check for image icon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icons', icon_val)
        
        has_icon = False
        if icon_val.endswith('.png') and os.path.exists(icon_path):
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
        
        # iOS Button Style
        hover_bg = theme['COLOR_GLASS_HOVER']
        active_bg = ThemeManager.COLOR_ACCENT + "25" # Stronger active background
        active_color = ThemeManager.COLOR_ACCENT
        
        # Padding adjustment for QIcon vs Text
        padding_left = "16px" if has_icon else "16px" 
        
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: {padding_left};
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
        
        return btn


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
        
        # Set window icon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1450, 850)
        
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
        ctrl_btn = QPushButton()
        ctrl_btn.setFixedSize(44, 44)
        ctrl_btn.setCursor(Qt.PointingHandCursor)
        ctrl_btn.setToolTip("Trung tâm Điều khiển")
        ctrl_btn.clicked.connect(lambda checked: self.toggle_notification_center(0))
        ctrl_btn.setStyleSheet(refresh_btn.styleSheet())

        # Load control center icon
        import os
        ctrl_icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icons', 'control_center.png')
        if os.path.exists(ctrl_icon_path):
            ctrl_btn.setIcon(QIcon(ctrl_icon_path))
            ctrl_btn.setIconSize(QSize(24, 24))
        else:
            ctrl_btn.setText("🎛️")

        # Notification Button
        notif_btn = QPushButton()
        notif_btn.setFixedSize(44, 44)
        notif_btn.setCursor(Qt.PointingHandCursor)
        notif_btn.setToolTip("Thông báo")
        notif_btn.clicked.connect(lambda checked: self.toggle_notification_center(1))
        notif_btn.setStyleSheet(refresh_btn.styleSheet())

        # Load notification icon
        notif_icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icons', 'notification.png')
        if os.path.exists(notif_icon_path):
            notif_btn.setIcon(QIcon(notif_icon_path))
            notif_btn.setIconSize(QSize(24, 24))
        else:
            notif_btn.setText("🔔")

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

        # 2. File Manager
        self.file_manager = FileManagerWidget(self.adb)
        self.pages.addWidget(self.file_manager)

        # 3. Xiaomi Suite
        self.xiaomi_suite = XiaomiSuiteWidget(self.adb)
        self.pages.addWidget(self.xiaomi_suite)

        # 4. General Tools
        self.general_tools = GeneralToolsWidget(self.adb)
        self.pages.addWidget(self.general_tools)

        # 5. Settings
        self.settings_widget = SettingsWidget(self.adb)
        self.pages.addWidget(self.settings_widget)

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
                except:
                    self.count_ready.emit(-1)

        self._check_worker = CheckWorker(self.adb)
        
        def on_check_finished(real_count):
            if real_count == -1: return
            ui_count = self.device_selector.count()
            is_placeholder = (ui_count == 1 and self.device_selector.itemData(0) is None)
            ui_real_count = 0 if is_placeholder else ui_count
            if real_count != ui_real_count:
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
                
                if hasattr(self, 'app_manager'): self.app_manager.reset()
                if hasattr(self, 'file_manager'): self.file_manager.reset()
                if hasattr(self, 'xiaomi_suite'): self.xiaomi_suite.reset()
                if hasattr(self, 'general_tools'): self.general_tools.reset()
                
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
        # Stop timers
        if hasattr(self, 'device_timer'):
            self.device_timer.stop()
            
        # Stop workers if running
        if hasattr(self, '_refresh_worker') and self._refresh_worker.isRunning():
            self._refresh_worker.terminate()
            self._refresh_worker.wait()
            
        if hasattr(self, '_check_worker') and self._check_worker.isRunning():
            self._check_worker.terminate()
            self._check_worker.wait()

        if hasattr(self, 'dashboard'):
            self.dashboard.stop_updates()
        if hasattr(self, 'notif_center'):
            self.notif_center.stop_mirroring()
        event.accept()

    def resizeEvent(self, event):
        """Ensure Notification Center stays on the right edge"""
        if hasattr(self, 'notif_center'):
            # Height: Match window height
            self.notif_center.setFixedHeight(self.height())
            
            # Position: Right aligned
            # x = width - notif_width
            # y = 0
            new_x = self.width() - self.notif_center.width()
            self.notif_center.move(new_x, 0)
        
        super().resizeEvent(event)

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
    
    def check_for_updates_startup(self):
        """Check for updates silently on startup"""
        try:
            include_prerelease = self.settings.value("include_prerelease", False, type=bool)
            self.update_checker = UpdateChecker(include_prerelease)
            self.update_checker.update_found.connect(self.on_startup_update_found)
            # No handler for no_update - silent on startup
            self.update_checker.error_occurred.connect(lambda err: None)  # Silent error on startup
            self.update_checker.start()
            
            # Update last check time
            from PySide6.QtCore import QDateTime
            current_time = QDateTime.currentDateTime().toString(Qt.ISODate)
            self.settings.setValue("last_update_check", current_time)
        except:
            pass  # Silent fail on startup
    
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
        except:
            pass  # Fail silently on startup
    
    def start_update_download(self, update_info: dict):
        """Start downloading update"""
        try:
            progress_dialog = UpdateProgressDialog(update_info, self)
            progress_dialog.start_download()
            progress_dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể tải cập nhật:\n{str(e)}")
