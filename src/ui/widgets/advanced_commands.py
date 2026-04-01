# src/ui/widgets/advanced_commands.py
"""
Advanced Commands Widget - ADB Advanced Features
Contains: Input Automation, Broadcast, Settings, Security, OTA Sideload, Monkey Testing
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTabWidget,
    QPushButton, QLineEdit, QSpinBox, QComboBox, QTextEdit, QCheckBox,
    QGroupBox, QFormLayout, QGridLayout, QFileDialog, QMessageBox,
    QScrollArea, QListWidget, QProgressBar, QApplication, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
from src.ui.theme_manager import ThemeManager
from src.ui.dialogs.confirmation_dialog import ConfirmationDialog


class CommandWorker(QThread):
    """Background worker for ADB commands"""
    output = Signal(str)
    finished_signal = Signal(bool, str)
    
    def __init__(self, adb, command_type, params=None):
        super().__init__()
        self.adb = adb
        self.command_type = command_type
        self.params = params or {}
        
    def run(self):
        try:
            result = ""
            success = True
            
            if self.command_type == "tap":
                x, y = self.params.get("x", 0), self.params.get("y", 0)
                result = self.adb.shell(f"input tap {x} {y}")
                result = f"✓ Tap at ({x}, {y})" if not result else result
                
            elif self.command_type == "swipe":
                x1, y1 = self.params.get("x1", 0), self.params.get("y1", 0)
                x2, y2 = self.params.get("x2", 0), self.params.get("y2", 0)
                duration = self.params.get("duration", 300)
                result = self.adb.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
                result = f"✓ Swipe ({x1},{y1}) → ({x2},{y2})" if not result else result
                
            elif self.command_type == "text":
                text = self.params.get("text", "")
                # Escape spaces for shell
                text = text.replace(" ", "%s")
                result = self.adb.shell(f"input text '{text}'")
                result = f"✓ Text input: {self.params.get('text', '')}" if not result else result
                
            elif self.command_type == "keyevent":
                keycode = self.params.get("keycode", 0)
                result = self.adb.shell(f"input keyevent {keycode}")
                result = f"✓ Key event: {keycode}" if not result else result
                
            elif self.command_type == "broadcast":
                action = self.params.get("action", "")
                result = self.adb.shell(f"am broadcast -a {action}")
                
            elif self.command_type == "get_setting":
                namespace = self.params.get("namespace", "global")
                key = self.params.get("key", "")
                result = self.adb.shell(f"settings get {namespace} {key}")
                
            elif self.command_type == "put_setting":
                namespace = self.params.get("namespace", "global")
                key = self.params.get("key", "")
                value = self.params.get("value", "")
                result = self.adb.shell(f"settings put {namespace} {key} {value}")
                result = f"✓ Set {namespace}/{key} = {value}" if not result else result
                
            elif self.command_type == "immersive":
                mode = self.params.get("mode", "")
                result = self.adb.shell(f"settings put global policy_control {mode}")
                result = f"✓ Immersive mode: {mode}" if not result else result
                
            elif self.command_type == "selinux":
                enable = self.params.get("enable", True)
                val = "1" if enable else "0"
                result = self.adb.shell(f"setenforce {val}")
                result = f"✓ SELinux {'enabled' if enable else 'disabled'}" if not result else result
                
            elif self.command_type == "monkey":
                package = self.params.get("package", "")
                events = self.params.get("events", 500)
                verbose = "-v" if self.params.get("verbose", False) else ""
                result = self.adb.shell(f"monkey -p {package} {verbose} {events}")
                
            self.finished_signal.emit(success, result)
            
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class AdvancedCommandsWidget(QWidget):
    """Advanced ADB Commands Widget with tabbed interface"""
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.worker = None
        self.current_btn = None
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header = QLabel("⚡ Lệnh Nâng Cao")
        header.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
            font-family: {ThemeManager.FONT_FAMILY};
        """)
        main_layout.addWidget(header)
        
        # Warning banner
        warning = QLabel("⚠️ Một số lệnh yêu cầu quyền Root hoặc có thể ảnh hưởng đến hệ thống. Sử dụng cẩn thận!")
        warning.setStyleSheet(f"""
            background-color: #FEF3C7;
            color: #92400E;
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
        """)
        warning.setWordWrap(True)
        main_layout.addWidget(warning)
        
        # Tab Widget
        self.tabs = QTabWidget()
        theme = ThemeManager.get_theme()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {theme['COLOR_BORDER']};
                border-radius: 12px;
                background: {theme['COLOR_GLASS_WHITE']};
            }}
            QTabBar::tab {{
                background: {theme['COLOR_BG_SECONDARY']};
                border: none;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QTabBar::tab:selected {{
                background: {theme['COLOR_GLASS_CARD']};
                font-weight: bold;
                border-bottom: 2px solid {ThemeManager.COLOR_ACCENT};
            }}
        """)
        
        # Add tabs (Input removed - already in Dev Tools > Script Engine)
        # Wrap each tab in scroll area for proper scrolling
        self.tabs.addTab(self._wrap_in_scroll(self.create_broadcast_tab()), "📡 Broadcast")
        self.tabs.addTab(self._wrap_in_scroll(self.create_settings_tab()), "⚙️ Settings")
        self.tabs.addTab(self._wrap_in_scroll(self.create_security_tab()), "🔐 Security")
        self.tabs.addTab(self._wrap_in_scroll(self.create_sideload_tab()), "📦 Sideload")
        self.tabs.addTab(self._wrap_in_scroll(self.create_monkey_tab()), "🐒 Monkey")
        
        # Add tooltips for each tab
        self.tabs.setTabToolTip(0, "Gửi broadcast intent đến hệ thống (Boot, Screen, Battery...)")
        self.tabs.setTabToolTip(1, "Đọc/Ghi system settings và chế độ Immersive Mode")
        self.tabs.setTabToolTip(2, "Bật/Tắt SELinux, dm_verity (yêu cầu Root)")
        self.tabs.setTabToolTip(3, "Flash OTA update qua ADB Sideload (cần Recovery mode)")
        self.tabs.setTabToolTip(4, "Stress test ứng dụng với Monkey Testing")
        
        main_layout.addWidget(self.tabs)
        
        # Setup output console at the bottom
        self.setup_output_console(main_layout)
    
    def _wrap_in_scroll(self, widget):
        """Wrap a widget in QScrollArea for scrolling support"""
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: rgba(0,0,0,0.05);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.2);
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        return scroll
        
    def setup_output_console(self, main_layout):
        """Setup output console at the bottom"""
        # Output Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 0, 5, 0)
        
        out_lbl = QLabel("📜 Output Log")
        out_lbl.setStyleSheet(f"font-weight: bold; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-size: 11px; text-transform: uppercase;")
        toolbar.addWidget(out_lbl)
        toolbar.addStretch()
        
        btn_clear = QPushButton("🗑️")
        btn_clear.setToolTip("Xóa log")
        btn_clear.setFixedSize(24, 24)
        btn_clear.setStyleSheet(ThemeManager.get_ghost_button_style())
        btn_clear.clicked.connect(lambda: self.output_console.clear())
        toolbar.addWidget(btn_clear)
        
        btn_copy = QPushButton("📋")
        btn_copy.setToolTip("Sao chép log")
        btn_copy.setFixedSize(24, 24)
        btn_copy.setStyleSheet(ThemeManager.get_ghost_button_style())
        btn_copy.clicked.connect(self.copy_log)
        toolbar.addWidget(btn_copy)
        
        main_layout.addLayout(toolbar)

        # Output console
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setMaximumHeight(150)
        terminal_bg = "#0D1117" if ThemeManager.is_dark() else "#111827"
        self.output_console.setStyleSheet(f"""
            background-color: {terminal_bg};
            color: #E6EDF3;
            font-family: {ThemeManager.FONT_FAMILY_MONO};
            font-size: 12px;
            border-radius: 12px;
            border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            padding: 12px;
        """)
        self.output_console.setPlaceholderText("Output sẽ hiển thị ở đây...")
        main_layout.addWidget(self.output_console)
    def create_input_tab(self):
        """Input Automation tab - tap, swipe, text, keys"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Tap Group
        tap_group = QGroupBox("📍 Tap")
        tap_group.setStyleSheet(ThemeManager.get_group_box_style())
        tap_layout = QHBoxLayout(tap_group)
        
        self.tap_x = QSpinBox()
        self.tap_x.setRange(0, 9999)
        self.tap_x.setPrefix("X: ")
        self.tap_y = QSpinBox()
        self.tap_y.setRange(0, 9999)
        self.tap_y.setPrefix("Y: ")
        btn_tap = QPushButton("Tap")
        btn_tap.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_tap.clicked.connect(self.do_tap)
        
        tap_layout.addWidget(self.tap_x)
        tap_layout.addWidget(self.tap_y)
        tap_layout.addWidget(btn_tap)
        layout.addWidget(tap_group)
        
        # Swipe Group
        swipe_group = QGroupBox("👆 Swipe")
        swipe_group.setStyleSheet(ThemeManager.get_group_box_style())
        swipe_layout = QGridLayout(swipe_group)
        
        self.swipe_x1 = QSpinBox()
        self.swipe_x1.setRange(0, 9999)
        self.swipe_x1.setPrefix("X1: ")
        self.swipe_y1 = QSpinBox()
        self.swipe_y1.setRange(0, 9999)
        self.swipe_y1.setPrefix("Y1: ")
        self.swipe_x2 = QSpinBox()
        self.swipe_x2.setRange(0, 9999)
        self.swipe_x2.setPrefix("X2: ")
        self.swipe_y2 = QSpinBox()
        self.swipe_y2.setRange(0, 9999)
        self.swipe_y2.setPrefix("Y2: ")
        self.swipe_duration = QSpinBox()
        self.swipe_duration.setRange(50, 5000)
        self.swipe_duration.setValue(300)
        self.swipe_duration.setSuffix(" ms")
        
        btn_swipe = QPushButton("Swipe")
        btn_swipe.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_swipe.clicked.connect(self.do_swipe)
        
        swipe_layout.addWidget(self.swipe_x1, 0, 0)
        swipe_layout.addWidget(self.swipe_y1, 0, 1)
        swipe_layout.addWidget(self.swipe_x2, 0, 2)
        swipe_layout.addWidget(self.swipe_y2, 0, 3)
        swipe_layout.addWidget(self.swipe_duration, 1, 0, 1, 2)
        swipe_layout.addWidget(btn_swipe, 1, 2, 1, 2)
        layout.addWidget(swipe_group)
        
        # Text Input Group
        text_group = QGroupBox("⌨️ Text Input")
        text_group.setStyleSheet(ThemeManager.get_group_box_style())
        text_layout = QHBoxLayout(text_group)
        
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Nhập text...")
        self.input_text.setStyleSheet(ThemeManager.get_input_style())
        btn_text = QPushButton("Gửi")
        btn_text.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_text.clicked.connect(self.do_text_input)
        
        text_layout.addWidget(self.input_text)
        text_layout.addWidget(btn_text)
        layout.addWidget(text_group)
        
        # Key Events Group
        keys_group = QGroupBox("🔘 Key Events")
        keys_group.setStyleSheet(ThemeManager.get_group_box_style())
        keys_layout = QGridLayout(keys_group)
        
        key_buttons = [
            ("Home", 3), ("Back", 4), ("Menu", 82), ("Power", 26),
            ("Vol+", 24), ("Vol-", 25), ("Play/Pause", 85), ("Mute", 164)
        ]
        
        for i, (name, keycode) in enumerate(key_buttons):
            btn = QPushButton(name)
            btn.setStyleSheet(ThemeManager.get_button_style("normal"))
            btn.clicked.connect(lambda checked, kc=keycode: self.do_keyevent(kc))
            keys_layout.addWidget(btn, i // 4, i % 4)
        
        layout.addWidget(keys_group)
        layout.addStretch()
        
        return widget
        
    def create_broadcast_tab(self):
        """Broadcast & Intent tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Helper text
        helper = QLabel("💡 Ví dụ: Gửi 'Boot Completed' để kích hoạt các app khởi động cùng hệ thống")
        helper.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
        helper.setWordWrap(True)
        layout.addWidget(helper)
        
        # Predefined Broadcasts
        predef_group = QFrame()
        predef_group.setObjectName("BroadcastScanPanel")
        predef_group.setStyleSheet(f"""
            #BroadcastScanPanel {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 12px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
        """)
        predef_layout = QVBoxLayout(predef_group)
        predef_layout.setContentsMargins(15, 15, 15, 15)
        
        predef_header = QLabel("📢 Broadcast Có Sẵn")
        predef_header.setStyleSheet(f"font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 14px; border: none; background: transparent;")
        predef_layout.addWidget(predef_header)
        
        self.broadcast_combo = QComboBox()
        self.broadcast_combo.setStyleSheet(ThemeManager.get_input_style())
        broadcasts = [
            ("Khởi động xong / Boot Completed", "android.intent.action.BOOT_COMPLETED"),
            ("Bật màn hình / Screen On", "android.intent.action.SCREEN_ON"),
            ("Tắt màn hình / Screen Off", "android.intent.action.SCREEN_OFF"),
            ("Pin yếu / Battery Low", "android.intent.action.BATTERY_LOW"),
            ("Pin OK / Battery OK", "android.intent.action.BATTERY_OKAY"),
            ("Cắm sạc / Power Connected", "android.intent.action.ACTION_POWER_CONNECTED"),
            ("Rút sạc / Power Disconnected", "android.intent.action.ACTION_POWER_DISCONNECTED"),
            ("Thay đổi kết nối / Connectivity Change", "android.net.conn.CONNECTIVITY_CHANGE"),
            ("Wifi thay đổi / Wifi State Changed", "android.net.wifi.WIFI_STATE_CHANGED"),
        ]
        for name, action in broadcasts:
            self.broadcast_combo.addItem(name, action)
            
        btn_send_broadcast = QPushButton("📡 Gửi Broadcast")
        btn_send_broadcast.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_send_broadcast.clicked.connect(self.do_broadcast)
        
        predef_layout.addWidget(self.broadcast_combo)
        predef_layout.addWidget(btn_send_broadcast)
        layout.addWidget(predef_group)
        
        # Custom Broadcast
        custom_group = QFrame()
        custom_group.setObjectName("CustomBroadcastPanel")
        custom_group.setStyleSheet(f"""
            #CustomBroadcastPanel {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 12px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
        """)
        custom_layout = QVBoxLayout(custom_group)
        custom_layout.setContentsMargins(15, 15, 15, 15)
        
        custom_header = QLabel("✏️ Custom Broadcast")
        custom_header.setStyleSheet(f"font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 14px; border: none; background: transparent;")
        custom_layout.addWidget(custom_header)
        
        self.custom_action = QLineEdit()
        self.custom_action.setPlaceholderText("android.intent.action.CUSTOM")
        self.custom_action.setStyleSheet(ThemeManager.get_input_style())
        
        btn_custom = QPushButton("Gửi Custom Broadcast")
        btn_custom.setStyleSheet(ThemeManager.get_button_style("normal"))
        btn_custom.clicked.connect(self.do_custom_broadcast)
        
        custom_layout.addWidget(self.custom_action)
        custom_layout.addWidget(btn_custom)
        layout.addWidget(custom_group)
        
        layout.addStretch()
        return widget
        
    def create_settings_tab(self):
        """System Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Helper text
        helper = QLabel("💡 Ví dụ: Đọc global/adb_enabled để kiểm tra ADB | Ghi global/animator_duration_scale = 0 để tắt animation")
        helper.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
        helper.setWordWrap(True)
        layout.addWidget(helper)
        
        # Get Setting
        get_group = QGroupBox("📖 Đọc Setting")
        get_group.setStyleSheet(ThemeManager.get_group_box_style())
        get_layout = QFormLayout(get_group)
        
        self.get_namespace = QComboBox()
        self.get_namespace.addItems(["global", "secure", "system"])
        self.get_namespace.setStyleSheet(ThemeManager.get_input_style())
        
        self.get_key = QLineEdit()
        self.get_key.setPlaceholderText("adb_enabled")
        self.get_key.setStyleSheet(ThemeManager.get_input_style())
        
        btn_get = QPushButton("Đọc")
        btn_get.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_get.clicked.connect(self.do_get_setting)
        
        get_layout.addRow("Namespace:", self.get_namespace)
        get_layout.addRow("Key:", self.get_key)
        get_layout.addRow("", btn_get)
        layout.addWidget(get_group)
        
        # Put Setting
        put_group = QGroupBox("✏️ Ghi Setting")
        put_group.setStyleSheet(ThemeManager.get_group_box_style())
        put_layout = QFormLayout(put_group)
        
        self.put_namespace = QComboBox()
        self.put_namespace.addItems(["global", "secure", "system"])
        self.put_namespace.setStyleSheet(ThemeManager.get_input_style())
        
        self.put_key = QLineEdit()
        self.put_key.setStyleSheet(ThemeManager.get_input_style())
        self.put_value = QLineEdit()
        self.put_value.setStyleSheet(ThemeManager.get_input_style())
        
        btn_put = QPushButton("Ghi")
        btn_put.setStyleSheet(ThemeManager.get_button_style("warning"))
        btn_put.clicked.connect(self.do_put_setting)
        
        put_layout.addRow("Namespace:", self.put_namespace)
        put_layout.addRow("Key:", self.put_key)
        put_layout.addRow("Value:", self.put_value)
        put_layout.addRow("", btn_put)
        layout.addWidget(put_group)
        
        # Immersive Mode / Chế độ toàn màn hình
        immersive_group = QGroupBox("🖥️ Chế độ toàn màn hình / Immersive Mode")
        immersive_group.setStyleSheet(ThemeManager.get_group_box_style())
        immersive_layout = QGridLayout(immersive_group)
        
        modes = [
            ("Ẩn cả hai / Hide All", "immersive.full=*"),
            ("Ẩn thanh trạng thái / Hide Status", "immersive.status=*"),
            ("Ẩn thanh điều hướng / Hide Nav", "immersive.navigation=*"),
            ("Khôi phục / Reset", "null"),
        ]
        
        for i, (name, mode) in enumerate(modes):
            btn = QPushButton(name)
            btn.setStyleSheet(ThemeManager.get_button_style("normal"))
            btn.clicked.connect(lambda checked, m=mode: self.do_immersive(m))
            immersive_layout.addWidget(btn, 0, i)
            
        layout.addWidget(immersive_group)
        layout.addStretch()
        
        return widget
        
    def create_security_tab(self):
        """Security commands tab (Root required)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Root Warning
        root_warning = QLabel("🔴 Các lệnh trong tab này yêu cầu quyền ROOT!")
        root_warning.setStyleSheet("""
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
        """)
        layout.addWidget(root_warning)
        
        # Helper text
        helper = QLabel("💡 SELinux: Tắt để cài Magisk modules | dm_verity: Tắt để sửa file hệ thống")
        helper.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
        helper.setWordWrap(True)
        layout.addWidget(helper)
        
        # SELinux
        selinux_group = QGroupBox("🛡️ SELinux")
        selinux_group.setStyleSheet(ThemeManager.get_group_box_style())
        selinux_layout = QHBoxLayout(selinux_group)
        
        btn_selinux_on = QPushButton("Bật / Enable (Enforcing)")
        btn_selinux_on.setStyleSheet(ThemeManager.get_button_style("success"))
        btn_selinux_on.clicked.connect(lambda: self.do_selinux(True))
        
        btn_selinux_off = QPushButton("Tắt / Disable (Permissive)")
        btn_selinux_off.setStyleSheet(ThemeManager.get_button_style("danger"))
        btn_selinux_off.clicked.connect(lambda: self.do_selinux(False))
        
        selinux_layout.addWidget(btn_selinux_on)
        selinux_layout.addWidget(btn_selinux_off)
        layout.addWidget(selinux_group)
        
        # dm_verity
        verity_group = QGroupBox("🔒 dm_verity")
        verity_group.setStyleSheet(ThemeManager.get_group_box_style())
        verity_layout = QHBoxLayout(verity_group)
        
        btn_verity_on = QPushButton("Bật / Enable Verity")
        btn_verity_on.setStyleSheet(ThemeManager.get_button_style("success"))
        btn_verity_on.clicked.connect(lambda: self.do_verity(True))
        
        btn_verity_off = QPushButton("Tắt / Disable Verity")
        btn_verity_off.setStyleSheet(ThemeManager.get_button_style("danger"))
        btn_verity_off.clicked.connect(lambda: self.do_verity(False))
        
        verity_layout.addWidget(btn_verity_on)
        verity_layout.addWidget(btn_verity_off)
        layout.addWidget(verity_group)
        
        layout.addStretch()
        return widget
        
    def create_sideload_tab(self):
        """OTA Sideload tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Instructions
        instructions = QLabel("""
📦 <b>OTA Sideload</b><br><br>
1. Thiết bị cần ở chế độ Recovery<br>
2. Trong Recovery, chọn "Apply update from ADB" hoặc tương tự<br>
3. Chọn file update.zip từ máy tính<br>
4. Nhấn "Sideload" để bắt đầu
        """)
        instructions.setStyleSheet(f"""
            background-color: {ThemeManager.COLOR_GLASS_WHITE};
            padding: 15px;
            border-radius: 10px;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File picker
        file_group = QGroupBox("📁 Chọn File Update")
        file_group.setStyleSheet(ThemeManager.get_group_box_style())
        file_layout = QHBoxLayout(file_group)
        
        self.sideload_path = QLineEdit()
        self.sideload_path.setReadOnly(True)
        self.sideload_path.setPlaceholderText("Chọn file update.zip...")
        self.sideload_path.setStyleSheet(ThemeManager.get_input_style())
        
        btn_browse = QPushButton("Duyệt...")
        btn_browse.setStyleSheet(ThemeManager.get_button_style("normal"))
        btn_browse.clicked.connect(self.browse_sideload_file)
        
        file_layout.addWidget(self.sideload_path)
        file_layout.addWidget(btn_browse)
        layout.addWidget(file_group)
        
        # Sideload button
        btn_sideload = QPushButton("🚀 Sideload")
        btn_sideload.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_sideload.setFixedHeight(50)
        btn_sideload.clicked.connect(self.do_sideload)
        layout.addWidget(btn_sideload)
        
        layout.addStretch()
        return widget
        
    def create_monkey_tab(self):
        """Monkey stress testing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Description
        desc = QLabel("🐒 Monkey Testing tạo các sự kiện ngẫu nhiên để stress test ứng dụng.")
        desc.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Helper text
        helper = QLabel("💡 Ví dụ: Package = com.facebook.katana, Events = 1000 → Gửi 1000 sự kiện random đến Facebook")
        helper.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
        helper.setWordWrap(True)
        layout.addWidget(helper)
        
        # Config group
        config_group = QGroupBox("⚙️ Cấu hình")
        config_group.setStyleSheet(ThemeManager.get_group_box_style())
        config_layout = QFormLayout(config_group)
        
        self.monkey_package = QLineEdit()
        self.monkey_package.setPlaceholderText("com.example.app")
        self.monkey_package.setStyleSheet(ThemeManager.get_input_style())
        
        self.monkey_events = QSpinBox()
        self.monkey_events.setRange(100, 100000)
        self.monkey_events.setValue(500)
        self.monkey_events.setSuffix(" events")
        
        self.monkey_verbose = QCheckBox("Verbose output")
        
        config_layout.addRow("Package:", self.monkey_package)
        config_layout.addRow("Số sự kiện:", self.monkey_events)
        config_layout.addRow("", self.monkey_verbose)
        layout.addWidget(config_group)
        
        # Run button
        btn_monkey = QPushButton("🐒 Chạy Monkey Test")
        btn_monkey.setStyleSheet(ThemeManager.get_button_style("warning"))
        btn_monkey.setFixedHeight(50)
        btn_monkey.clicked.connect(self.do_monkey)
        layout.addWidget(btn_monkey)
        
        layout.addStretch()
        return widget
        
    # ═══════════════════════════════════════
    # ACTION HANDLERS
    # ═══════════════════════════════════════
    
    def log(self, message):
        """Add message to output console"""
        self.output_console.append(message)
        self.output_console.moveCursor(self.output_console.textCursor().MoveOperation.End)
        
    def copy_log(self):
        """Copy output to clipboard"""
        QApplication.clipboard().setText(self.output_console.toPlainText())

    def set_loading(self, loading, btn=None):
        """Toggle loading state UI"""
        self.tabs.setEnabled(not loading)
        if btn:
            btn.setEnabled(not loading)
            if loading:
                self._old_text = btn.text()
                btn.setText("⏳ Đang chạy...")
            else:
                btn.setText(self._old_text)
                
    def run_command(self, cmd_type, params, btn=None):
        """Run command in background thread"""
        if self.worker and self.worker.isRunning():
            return
            
        self.current_btn = btn
        self.set_loading(True, btn)
            
        self.worker = CommandWorker(self.adb, cmd_type, params)
        self.worker.finished_signal.connect(self.on_command_finished)
        self.worker.start()
        self.log(f"\n$ {cmd_type} {params if params else ''}")
        
    def on_command_finished(self, success, result):
        """Handle command completion"""
        self.set_loading(False, self.current_btn)
        if success:
            self.log(f'<span style="color:#00FF00;">✓ {result}</span>')
        else:
            self.log(f'<span style="color:red;">✗ Lỗi: {result}</span>')
            
    def do_tap(self):
        self.run_command("tap", {"x": self.tap_x.value(), "y": self.tap_y.value()}, self.sender())
        
    def do_swipe(self):
        self.run_command("swipe", {
            "x1": self.swipe_x1.value(), "y1": self.swipe_y1.value(),
            "x2": self.swipe_x2.value(), "y2": self.swipe_y2.value(),
            "duration": self.swipe_duration.value()
        }, self.sender())
        
    def do_text_input(self):
        self.run_command("text", {"text": self.input_text.text()}, self.sender())
        
    def do_keyevent(self, keycode):
        self.run_command("keyevent", {"keycode": keycode}, self.sender())
        
    def do_broadcast(self):
        action = self.broadcast_combo.currentData()
        self.run_command("broadcast", {"action": action}, self.sender())
        
    def do_custom_broadcast(self):
        action = self.custom_action.text()
        if action:
            self.run_command("broadcast", {"action": action}, self.sender())
            
    def do_get_setting(self):
        self.run_command("get_setting", {
            "namespace": self.get_namespace.currentText(),
            "key": self.get_key.text()
        }, self.sender())
        
    def do_put_setting(self):
        dlg = ConfirmationDialog(
            self,
            title="Cảnh báo",
            message="Thay đổi cài đặt hệ thống?",
            details="Việc thay đổi System Settings (Global/Secure) có thể gây ra sự cố nếu nhập sai giá trị.\n\nBạn có muốn tiếp tục?",
            confirm_text="Tiến hành",
            cancel_text="Hủy",
            warning_mode=True
        )
        if dlg.exec() == QDialog.Accepted:
            self.run_command("put_setting", {
                "namespace": self.put_namespace.currentText(),
                "key": self.put_key.text(),
                "value": self.put_value.text()
            }, self.sender())
            
    def do_immersive(self, mode):
        self.run_command("immersive", {"mode": mode}, self.sender())
        
    def do_selinux(self, enable):
        dlg = ConfirmationDialog(
            self,
            title="Cảnh báo",
            message=f"{'Bật' if enable else 'Tắt'} SELinux?",
            details="Thao tác này yêu cầu quyền ROOT và có thể ảnh hưởng đến tính bảo mật/ổn định của hệ thống.\n\nTiếp tục?",
            confirm_text="Xác nhận",
            cancel_text="Hủy",
            warning_mode=True
        )
        if dlg.exec() == QDialog.Accepted:
            self.run_command("selinux", {"enable": enable}, self.sender())
            
    def do_verity(self, enable):
        dlg = ConfirmationDialog(
            self,
            title="Cảnh báo",
            message=f"{'Bật' if enable else 'Tắt'} dm_verity?",
            details="Thao tác này yêu cầu quyền ROOT. Thiết bị sẽ cần khởi động lại để áp dụng.\n\nTiếp tục?",
            confirm_text="Xác nhận",
            cancel_text="Hủy",
            warning_mode=True
        )
        if dlg.exec() == QDialog.Accepted:
            btn = self.sender()
            self.set_loading(True, btn)
            try:
                cmd = "enable-verity" if enable else "disable-verity"
                result = self.adb.run_adb([cmd])
                self.log(f'<span style="color:#00FF00;">✓ {result if result else cmd + " executed"}</span>')
            finally:
                self.set_loading(False, btn)
            
    def browse_sideload_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file update", "", "ZIP Files (*.zip)"
        )
        if path:
            self.sideload_path.setText(path)
            
    def do_sideload(self):
        path = self.sideload_path.text()
        if not path:
            QMessageBox.critical(self, "Lỗi", "Vui lòng chọn file update.zip trước khi sideload.")
            return
            
        dlg = ConfirmationDialog(
            self,
            title="Sideload",
            message="Bắt đầu quá trình Sideload?",
            details="Đảm bảo thiết bị đang ở chế độ Recovery và đã chọn 'Apply update from ADB'.\n\nHành động này không thể hoàn tác giữa chừng.\nTiếp tục?",
            confirm_text="Sideload ngay",
            cancel_text="Hủy",
            warning_mode=True
        )
        if dlg.exec() == QDialog.Accepted:
            btn = self.sender()
            self.set_loading(True, btn)
            try:
                self.log(f"\n$ adb sideload {path}")
                result = self.adb.run_adb(["sideload", path])
                self.log(f'<span style="color:#00FF00;">{result if result else "✓ Sideload started"}</span>')
            finally:
                self.set_loading(False, btn)
            
    def do_monkey(self):
        package = self.monkey_package.text()
        if not package:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Package Name để chạy Monkey Test.")
            return
            
        self.run_command("monkey", {
            "package": package,
            "events": self.monkey_events.value(),
            "verbose": self.monkey_verbose.isChecked()
        }, self.sender())
        
    def reset(self):
        """Reset widget state"""
        self.output_console.clear()
