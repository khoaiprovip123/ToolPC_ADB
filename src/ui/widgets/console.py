# src/ui/widgets/console.py
"""
Console Widget - Direct ADB Command Interface
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QFrame, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from src.ui.theme_manager import ThemeManager

class ConsoleWidget(QWidget):
    """
    ADB Console Widget
    Provides direct command execution and log viewing
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.history = []
        self.history_index = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QHBoxLayout(self) # Changed to HBox for Sidebar
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # ==================== LEFT SIDEBAR (Quick Commands) ====================
        sidebar_container = QFrame()
        sidebar_container.setObjectName("sidebar_console")
        sidebar_container.setFixedWidth(300)
        sidebar_container.setStyleSheet(f"""
            #sidebar_console {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-right: 1px solid {ThemeManager.COLOR_BORDER};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Sidebar Header
        lbl_quick = QLabel("⚡ Lệnh Nhanh (Awesome ADB)")
        lbl_quick.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; border: none; background: transparent;")
        sidebar_layout.addWidget(lbl_quick)
        
        # Command Categories
        self.cmd_tree = QTreeWidget()
        self.cmd_tree.setHeaderHidden(True)
        self.cmd_tree.setIndentation(15)
        self.cmd_tree.setFocusPolicy(Qt.NoFocus)
        self.cmd_tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                font-size: 13px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px;
                border-radius: 6px;
                margin-bottom: 2px;
                border: none;
            }}
            QTreeWidget::item:hover {{
                background-color: {ThemeManager.COLOR_GLASS_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {ThemeManager.COLOR_ACCENT}20;
                color: {ThemeManager.COLOR_ACCENT};
                border: 1px solid {ThemeManager.COLOR_ACCENT}50;
            }}
        """)
        self.cmd_tree.itemDoubleClicked.connect(self.on_quick_command_clicked)
        sidebar_layout.addWidget(self.cmd_tree)
        
        # Description Box
        self.desc_box = QLabel("Chọn lệnh để xem hướng dẫn")
        self.desc_box.setWordWrap(True)
        self.desc_box.setStyleSheet(f"""
            background-color: rgba(0,0,0,0.05);
            border-radius: 8px;
            padding: 10px;
            color: {ThemeManager.COLOR_TEXT_SECONDARY};
            font-size: 12px;
            border: none;
        """)
        sidebar_layout.addWidget(self.desc_box)
        
        # Populate Commands
        self.populate_commands()
        self.cmd_tree.currentItemChanged.connect(self.on_command_selected)
 
        main_layout.addWidget(sidebar_container)
        
        # ==================== RIGHT CONTENT (Console) ====================
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        
        # Log Output Area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeManager.COLOR_GLASS_CARD};
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                border-radius: {ThemeManager.RADIUS_CARD};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                padding: 10px;
                font-family: Consolas, monospace;
            }}
        """)
        content_layout.addWidget(self.output_area)
        
        # Input Area
        input_container = QFrame()
        input_container.setObjectName("input_console")
        input_container.setStyleSheet(f"""
            #input_console {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 12px;
                border: 1px solid {ThemeManager.COLOR_BORDER};
            }}
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Nhập lệnh ADB (VD: shell pm list packages)...")
        self.input_field.setStyleSheet("background: transparent; border: none; padding: 5px;")
        self.input_field.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("Gửi")
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        send_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(send_btn)
        
        content_layout.addWidget(input_container)
        
        # Tips Label
        tips_lbl = QLabel("💡 Click đúp vào lệnh bên trái để chạy an toàn.")
        tips_lbl.setStyleSheet("color: #888; font-size: 11px; margin-left: 5px; border: none; background: transparent;")
        content_layout.addWidget(tips_lbl)
        
        main_layout.addLayout(content_layout)

    def populate_commands(self):
        """Populate the sidebar with categories and commands"""
        
        # Data Structure: Category -> [(Name, Command List, Description, Warning)]
        
        commands = {
            "📱 Hiển Thị (Display)": [
                ("Xem Độ phân giải", ["shell", "wm", "size"], 
                 "Hiển thị độ phân giải màn hình hiện tại.", None),
                ("Xem Mật độ điểm ảnh (DPI)", ["shell", "wm", "density"], 
                 "Hiển thị mật độ điểm ảnh (DPI/PPI) hiện tại.", None),
            ],
            "🔋 Pin & Nguồn (Power)": [
                ("Thông tin Pin chi tiết", ["shell", "dumpsys", "battery"], 
                 "Xem trạng thái sạc, mức pin, nhiệt độ và sức khỏe pin.", None),
                ("Giả lập rút sạc", ["shell", "dumpsys", "battery", "unplug"], 
                 "Giả lập tình trạng thiết bị đang không sạc.", None),
                ("Reset trạng thái Pin", ["shell", "dumpsys", "battery", "reset"], 
                 "Khôi phục trạng thái báo cáo pin về thực tế.", None),
            ],
            "📦 Ứng Dụng (Package)": [
                ("Liệt kê App bên thứ 3", ["shell", "pm", "list", "packages", "-3"], 
                 "Danh sách các ứng dụng do người dùng cài đặt (không phải hệ thống).", None),
                ("Liệt kê App đã tắt", ["shell", "pm", "list", "packages", "-d"], 
                 "Danh sách các ứng dụng đang bị vô hiệu hóa.", None),
            ],
            "⚙️ Hệ Thống (System)": [
                ("Thông tin Android", ["shell", "getprop", "ro.build.version.release"], 
                 "Xem phiên bản Android hiện tại.", None),
                ("Thông tin Model", ["shell", "getprop", "ro.product.model"], 
                 "Xem tên mã model của thiết bị.", None),
                ("Khởi động lại (Reboot)", ["reboot"], 
                 "Khởi động lại thiết bị ngay lập tức.", "⚠️ Thiết bị sẽ tắt và khởi động lại."),
                ("Vào Fastboot", ["reboot", "bootloader"], 
                 "Khởi động lại vào chế độ Fastboot.", "⚠️ Dành cho việc flash ROM/Firmware."),
            ]
        }
        
        for category, cmds in commands.items():
            cat_item = QTreeWidgetItem(self.cmd_tree)
            cat_item.setText(0, category)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            cat_item.setExpanded(True)
            
            for name, cmd, desc, warn in cmds:
                item = QTreeWidgetItem(cat_item)
                item.setText(0, name)
                item.setData(0, Qt.UserRole, {
                    "cmd": cmd,
                    "desc": desc,
                    "warn": warn
                })

    def on_command_selected(self, current, previous):
        if not current: return
        data = current.data(0, Qt.UserRole)
        if data:
            desc = data["desc"]
            warn = data.get("warn")
            
            text = f"<b>Mô tả:</b><br>{desc}"
            if warn:
                text += f"<br><br><span style='color:red; font-weight:bold;'>{warn}</span>"
            
            self.desc_box.setText(text)
        else:
             self.desc_box.setText("Chọn lệnh để xem hướng dẫn")

    def on_quick_command_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data: return # Header clicked
        
        cmd_list = data["cmd"]
        warn = data.get("warn")
        
        # Safety Check / Warning
        if warn:
            reply = QMessageBox.warning(
                self, "Cảnh báo an toàn", 
                f"{warn}\n\nBạn có chắc chắn muốn thực hiện lệnh này không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.run_command_safe(cmd_list)

    def run_command_safe(self, cmd_list):
        """Execute a predefined safe list command"""
        cmd_disp = " ".join(cmd_list)
        self.append_log(f"\n$ {cmd_disp}", "#00FF00")
        
        try:
             res = self.adb.execute(cmd_list)
             self.append_log(res)
        except Exception as e:
             self.append_log(f"Error: {str(e)}", "red")
             
    def execute_command(self):
        """Execute command from input field (Legacy/Manual)"""
        cmd = self.input_field.text().strip()
        if not cmd: return
            
        self.history.append(cmd)
        self.history_index = len(self.history)
        
        self.append_log(f"\n$ {cmd}", "#00FF00")
        
        # Basic Safety Filter
        if any(x in cmd for x in ["rm -rf", "mkfs"]):
             self.append_log("❌ Lệnh này bị chặn bởi bộ lọc an toàn.", "red")
             return

        try:
            # Still use string input for manual typing (ADBManager handles it)
            result = self.adb.execute(cmd)
            self.append_log(result)
        except Exception as e:
            self.append_log(f"Error: {str(e)}", "red")
            
        self.input_field.clear()

    def append_log(self, text, color=None):
        # Safety limit
        if self.output_area.document().blockCount() > 2000:
            self.output_area.document().setMaximumBlockCount(2000)
            
        if color:
             self.output_area.append(f'<span style="color:{color};">{text}</span>')
        else:
             self.output_area.append(text)
        self.output_area.moveCursor(self.output_area.textCursor().MoveOperation.End)
