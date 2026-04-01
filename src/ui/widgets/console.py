# src/ui/widgets/console.py
"""
Console Widget - Direct ADB Command Interface
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QFrame, QMessageBox, QSplitter, QProgressBar, QApplication
)
from PySide6.QtCore import Qt, QEvent
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
        self.history_index = -1
        self.auto_scroll = True
        
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
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: {ThemeManager.RADIUS_CARD};
                border: 0.5px solid {ThemeManager.get_theme()['COLOR_BORDER']};
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
                color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']};
                outline: none;
                font-family: {ThemeManager.FONT_FAMILY};
            }}
            QTreeWidget::item {{
                height: 36px;
                padding-left: 10px;
                border-radius: 10px;
                margin-bottom: 4px;
                border: none;
            }}
            QTreeWidget::item:hover {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}80;
            }}
            QTreeWidget::item:selected {{
                background: {ThemeManager.COLOR_ACCENT_GRADIENT};
                color: white;
                font-weight: 700;
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
        
        # --- Console Toolbar ---
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 0, 5, 0)
        
        console_lbl = QLabel("🖥️ ADB Console")
        console_lbl.setStyleSheet(f"font-weight: bold; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-size: 12px; border: none; background: transparent;")
        toolbar_layout.addWidget(console_lbl)
        toolbar_layout.addStretch()
        
        # Clear Button
        self.btn_clear = QPushButton("🗑️ Clear")
        self.btn_clear.setToolTip("Xóa sạch log")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet(ThemeManager.get_ghost_button_style())
        self.btn_clear.clicked.connect(self.clear_log)
        toolbar_layout.addWidget(self.btn_clear)
        
        # Copy Button
        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.setToolTip("Sao chép toàn bộ log")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet(ThemeManager.get_ghost_button_style())
        self.btn_copy.clicked.connect(self.copy_log)
        toolbar_layout.addWidget(self.btn_copy)
        
        # Auto-scroll Toggle
        self.btn_scroll = QPushButton("⚓ Scroll: ON")
        self.btn_scroll.setToolTip("Bật/Tắt tự động cuộn")
        self.btn_scroll.setCheckable(True)
        self.btn_scroll.setChecked(True)
        self.btn_scroll.setCursor(Qt.PointingHandCursor)
        self.btn_scroll.setStyleSheet(ThemeManager.get_ghost_button_style())
        self.btn_scroll.clicked.connect(self.toggle_autoscroll)
        toolbar_layout.addWidget(self.btn_scroll)
        
        content_layout.addLayout(toolbar_layout)

        # Log Output Area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        terminal_bg = "#0D1117" if ThemeManager.is_dark() else "#111827" # Deep Night Blue
        self.output_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {terminal_bg};
                color: #E6EDF3;
                border-radius: {ThemeManager.RADIUS_CARD};
                border: 0.5px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                padding: 15px;
                font-family: {ThemeManager.FONT_FAMILY_MONO};
                font-size: 13px;
                selection-background-color: {ThemeManager.COLOR_ACCENT}40;
            }}
        """)
        content_layout.addWidget(self.output_area)
        
        # Input Area
        input_container = QFrame()
        input_container.setObjectName("input_console")
        input_container.setStyleSheet(f"""
            #input_console {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 25px; 
                border: 0.5px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Nhập lệnh ADB (VD: shell pm list packages)...")
        self.input_field.setStyleSheet("background: transparent; border: none; padding: 5px;")
        self.input_field.returnPressed.connect(self.execute_command)
        self.input_field.installEventFilter(self) # For History Navigation
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Gửi")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.send_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(self.send_btn)
        
        content_layout.addWidget(input_container)
        
        # Mini Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(ThemeManager.get_progress_bar_style("mini"))
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.hide()
        content_layout.addWidget(self.progress_bar)
        
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
        
        self.set_loading(True)
        try:
             res = self.adb.execute(cmd_list)
             self.append_log(res)
        except Exception as e:
             self.append_log(f"Error: {str(e)}", "red")
        finally:
             self.set_loading(False)
             
    def execute_command(self):
        """Execute command from input field (Legacy/Manual)"""
        cmd = self.input_field.text().strip()
        if not cmd: return
            
        # Add to history if not duplicate and not empty
        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.history_index = -1
        
        self.append_log(f"\n$ {cmd}", "#00FF00")
        
        # Basic Safety Filter
        if any(x in cmd for x in ["rm -rf", "mkfs"]):
             self.append_log("❌ Lệnh này bị chặn bởi bộ lọc an toàn.", "red")
             self.input_field.clear()
             return

        self.set_loading(True)
        try:
            # Still use string input for manual typing (ADBManager handles it)
            result = self.adb.execute(cmd)
            self.append_log(result)
        except Exception as e:
            self.append_log(f"Error: {str(e)}", "red")
        finally:
            self.set_loading(False)
            
        self.input_field.clear()

    def set_loading(self, loading):
        """Toggle loading state UI"""
        self.progress_bar.setVisible(loading)
        self.send_btn.setEnabled(not loading)
        if loading:
            self.send_btn.setText("...")
        else:
            self.send_btn.setText("Gửi")

    def eventFilter(self, source, event):
        """Handle Arrow Keys for History Navigation"""
        if source == self.input_field and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                if self.history:
                    if self.history_index == -1:
                        self.history_index = len(self.history) - 1
                    elif self.history_index > 0:
                        self.history_index -= 1
                    self.input_field.setText(self.history[self.history_index])
                return True
            elif event.key() == Qt.Key_Down:
                if self.history:
                    if self.history_index != -1 and self.history_index < len(self.history) - 1:
                        self.history_index += 1
                        self.input_field.setText(self.history[self.history_index])
                    else:
                        self.history_index = -1
                        self.input_field.clear()
                return True
        return super().eventFilter(source, event)

    def clear_log(self):
        self.output_area.clear()
        self.append_log("✨ Console cleared.")

    def copy_log(self):
        QApplication.clipboard().setText(self.output_area.toPlainText())
        # Notification could be added here if available

    def toggle_autoscroll(self):
        self.auto_scroll = self.btn_scroll.isChecked()
        self.btn_scroll.setText(f"⚓ Scroll: {'ON' if self.auto_scroll else 'OFF'}")

    def append_log(self, text, color=None):
        # Safety limit
        if self.output_area.document().blockCount() > 2000:
            self.output_area.document().setMaximumBlockCount(2000)
            
        if color:
             self.output_area.append(f'<span style="color:{color};">{text}</span>')
        else:
             self.output_area.append(text)
             
        if self.auto_scroll:
            self.output_area.moveCursor(self.output_area.textCursor().MoveOperation.End)
