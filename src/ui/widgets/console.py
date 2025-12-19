# src/ui/widgets/console.py
"""
Console Widget - Direct ADB Command Interface
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt
from src.ui.theme_manager import ThemeManager

class ConsoleWidget(QWidget):
    """
    Console Widget
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout"""
        # Root layout for the widget
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Content Widget
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: transparent;")
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        scroll.setWidget(content_widget)
        root_layout.addWidget(scroll)
        
        # Header
        header = QLabel("💻 ADB Console")
        header.setStyleSheet(f"""
            font-size: 20px;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
            font-weight: bold;
            padding: 10px;
        """)
        main_layout.addWidget(header)
        
        # Output Area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(400) # Guarantee some height
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(0, 0, 0, 0.85);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                padding: 10px;
                color: #00FF00;
                font-family: Consolas, monospace;
                font-size: 13px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        main_layout.addWidget(self.output)
        
        # Input Area
        input_layout = QHBoxLayout()
        
        label_prompt = QLabel("adb >")
        label_prompt.setStyleSheet(f"font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        input_layout.addWidget(label_prompt)
        
        self.input_cmd = QLineEdit()
        self.input_cmd.setPlaceholderText("Nhập lệnh ADB (ví dụ: shell pm list packages) hoặc fastboot...")
        self.input_cmd.returnPressed.connect(self.run_command)
        self.input_cmd.setStyleSheet(ThemeManager.get_input_style())
        input_layout.addWidget(self.input_cmd)
        
        btn_run = QPushButton("Chạy")
        btn_run.clicked.connect(self.run_command)
        btn_run.setStyleSheet(ThemeManager.get_button_style("primary"))
        input_layout.addWidget(btn_run)
        
        btn_clear = QPushButton("Xóa")
        btn_clear.clicked.connect(self.output.clear)
        btn_clear.setStyleSheet(ThemeManager.get_button_style("outline"))
        input_layout.addWidget(btn_clear)
        
        main_layout.addLayout(input_layout)
        
        # Quick Commands
        quick_group = QGroupBox("Lệnh nhanh")
        quick_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                margin-top: 10px;
                padding-top: 15px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        quick_layout = QVBoxLayout(quick_group)
        
        # Row 1: Action Buttons
        row1 = QHBoxLayout()
        commands = [
            ("📱 Devices", "devices"),
            ("🔋 Battery", "shell dumpsys battery"),
            ("🌐 IP Address", "shell ip addr show wlan0"),
            ("🔁 Reboot", "reboot"),
            ("📸 Screenshot", "shell screencap -p /sdcard/s.png"),
        ]
        
        for name, cmd in commands:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked=False, c=cmd: self.run_custom_command(c))
            btn.setStyleSheet(ThemeManager.get_button_style("outline"))
            row1.addWidget(btn)
        
        quick_layout.addLayout(row1)
        
        # Row 1.5: Fastboot Commands
        row_fb = QHBoxLayout()
        fb_commands = [
            ("⚡ FB Devices", "fastboot devices"),
            ("🔄 FB Reboot", "fastboot reboot"),
            ("🔙 Bootloader", "fastboot reboot bootloader"),
            ("ℹ️ FB Info", "fastboot getvar all"),
            ("🔒 Unlock Status", "fastboot oem device-info"),
        ]
        
        for name, cmd in fb_commands:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked=False, c=cmd: self.run_custom_command(c))
            btn.setStyleSheet(ThemeManager.get_button_style("outline"))
            row_fb.addWidget(btn)
            
        quick_layout.addLayout(row_fb)
        
        # Row 2: Helper Keywords
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Gợi ý:"))
        
        suggestions = [
            "shell pm list packages",
            "shell dumpsys package",
            "fastboot devices",
            "fastboot reboot",
            "logcat -d",
            "install -r",
        ]
        
        for sug in suggestions:
            btn = QPushButton(sug)
            btn.setToolTip("Nhấn để điền vào ô nhập")
            btn.clicked.connect(lambda checked=False, s=sug: self.input_cmd.setText(s))
            btn.setStyleSheet(f"""
                QPushButton {{
                    border: 1px solid {ThemeManager.COLOR_ACCENT}40;
                    border-radius: 10px;
                    padding: 4px 8px;
                    background-color: rgba(255, 255, 255, 0.5);
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.COLOR_ACCENT}20;
                }}
            """)
            row2.addWidget(btn)
            
        quick_layout.addLayout(row2)
            
        main_layout.addWidget(quick_group)
        
    def run_command(self):
        cmd = self.input_cmd.text().strip()
        if not cmd:
            return
            
        self.run_custom_command(cmd)
        self.input_cmd.clear()
        
    def run_custom_command(self, cmd):
        """
        Execute command with intelligent prefix handling
        """
        cmd = cmd.strip()
        if not cmd: return

        # Determine how to display command in log
        display_cmd = cmd
        if not cmd.startswith("adb") and not cmd.startswith("fastboot"):
             display_cmd = f"adb {display_cmd}"
             
        self.output.append(f"\n$ {display_cmd}")
        
        try:
            # 1. HANDLE FASTBOOT
            if cmd.startswith("fastboot"):
                # Strip 'fastboot ' prefix
                args = cmd[8:].strip()
                if not args:
                    result = "Error: Missing arguments for fastboot"
                else:
                    result = self.adb.fastboot_command(args)
                    
            # 2. HANDLE ADB EXPLICIT
            elif cmd.startswith("adb "):
                args = cmd[4:].strip()
                if not args:
                    result = "Error: Missing arguments for adb"
                elif args.startswith("shell "):
                    result = self.adb.shell(args[6:])
                else:
                    result = self.adb.execute(args)
            
            # 3. IMPLICIT ADB (Default)
            else:
                if cmd == "devices":
                    result = self.adb.execute("devices")
                elif cmd.startswith("shell "):
                    result = self.adb.shell(cmd[6:])
                else:
                    result = self.adb.execute(cmd)
                
            self.output.append(result)
            self.output.moveCursor(self.output.textCursor().MoveOperation.End)
            
        except Exception as e:
            self.output.append(f"Lỗi: {e}")
            
    def reset(self):
        pass
