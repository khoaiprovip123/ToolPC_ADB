from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QMessageBox, QGroupBox, QGridLayout, QTabWidget,
    QLineEdit, QFileDialog, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager
import os

class FastbootToolboxWidget(QWidget):
    """
    Fastboot Toolbox Widget
    Includes Flash, Wipe, Lock/Unlock, and Reboot controls.
    """
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 1. Tabs (Moved to top)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 8px;
                background: white; 
                margin-top: -1px; 
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #333;
                padding: 10px 20px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
                border-bottom: 2px solid #007bff;
            }
        """)
        
        # Tab 1: Menu Chính (Basic)
        self.tab_basic = QWidget()
        self.setup_basic_tab()
        self.tabs.addTab(self.tab_basic, "Menu Chính")
        
        # Tab 2: Flash & Wipe
        self.tab_flash = QWidget()
        self.setup_flash_tab()
        self.tabs.addTab(self.tab_flash, "Flash & Wipe")
        
        layout.addWidget(self.tabs)
        
        # Log Output (Small)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)
        self.log_output.setPlaceholderText("Kết quả lệnh Fastboot sẽ hiện ở đây...")
        self.log_output.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 8px;
                font-family: Consolas;
            }}
        """)
        layout.addWidget(self.log_output)

    def setup_basic_tab(self):
        layout = QVBoxLayout(self.tab_basic)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Group 1: Reboot
        reboot_group = QGroupBox("Fastboot Reboot Menu") 
        reboot_group.setStyleSheet(f"""
            QGroupBox {{ 
                font-weight: bold; 
                color: {ThemeManager.COLOR_TEXT_PRIMARY}; 
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']}; 
                border-radius: 12px; 
                padding-top: 20px; 
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
            }}
        """)
        reboot_layout = QGridLayout(reboot_group)
        reboot_layout.setSpacing(15)
        
        btn_system = QPushButton("📱 Reboot System")
        btn_recovery = QPushButton("🛠️ Reboot Recovery")
        btn_bootloader = QPushButton("🔧 Reboot Bootloader")
        btn_edl = QPushButton("🔌 Reboot EDL (9008)")
        
        # Blue Style for Reboot Buttons (Matches Screenshot)
        blue_style = """
            QPushButton {
                background-color: #007bff; /* Bright Blue */
                color: white;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """
        
        for btn in [btn_system, btn_recovery, btn_bootloader, btn_edl]:
            btn.setMinimumHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(blue_style)
            
        btn_system.clicked.connect(lambda: self.fastboot_action("reboot", "Khởi động lại vào hệ điều hành?"))
        btn_recovery.clicked.connect(lambda: self.fastboot_action("reboot recovery", "Khởi động vào chế độ Recovery?"))
        btn_bootloader.clicked.connect(lambda: self.fastboot_action("reboot-bootloader", "Khởi động lại Bootloader?"))
        btn_edl.clicked.connect(lambda: self.fastboot_action("oem edl", "Chuyển sang chế độ EDL (Emergency Download)?\nChỉ hoạt động trên một số thiết bị!"))
        
        reboot_layout.addWidget(btn_system, 0, 0)
        reboot_layout.addWidget(btn_recovery, 0, 1)
        reboot_layout.addWidget(btn_bootloader, 1, 0)
        reboot_layout.addWidget(btn_edl, 1, 1)
        
        layout.addWidget(reboot_group)
        
        # Group 2: Quick Fix
        fix_group = QGroupBox("Sửa lỗi nhanh")
        fix_group.setStyleSheet(reboot_group.styleSheet())
        fix_layout = QVBoxLayout(fix_group)
        
        self.btn_frp = QPushButton("🔓 Mở Khóa Tài Khoản Google (FRP)")
        self.btn_frp.setMinimumHeight(50)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        # Red/Salmon Style (Matches Screenshot)
        self.btn_frp.setStyleSheet("""
            QPushButton {
                background-color: #ff5e62; /* Salmon/Red */
                color: white; 
                font-weight: bold; 
                border-radius: 10px; 
                font-size: 14px; 
                border: none;
            }
            QPushButton:hover { 
                background-color: #ff4044; 
            }
        """)
        self.btn_frp.clicked.connect(self.run_frp_unlock)
        fix_layout.addWidget(self.btn_frp)
        
        layout.addWidget(fix_group)
        layout.addStretch()

    def setup_flash_tab(self):
        layout = QVBoxLayout(self.tab_flash)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Style for cards
        group_style = f"""
            QGroupBox {{ 
                font-weight: bold; 
                color: {ThemeManager.COLOR_TEXT_PRIMARY}; 
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']}; 
                border-radius: 12px; 
                padding-top: 20px; 
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
            }}
        """
        
        # 1. Flash Section
        flash_group = QGroupBox("Flash Images (.img)")
        flash_group.setStyleSheet(group_style)
        flash_layout = QVBoxLayout(flash_group)
        flash_layout.setSpacing(15)
        
        def create_flash_row(label, command_key):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-weight: 500; font-size: 13px; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
            lbl.setFixedWidth(130)
            
            path_edit = QLineEdit()
            path_edit.setPlaceholderText("Chọn file .img từ máy tính...")
            path_edit.setStyleSheet(f"""
                QLineEdit {{
                    padding: 8px;
                    border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                    border-radius: 6px;
                    background: white;
                }}
            """)
            
            btn_browse = QPushButton("📁")
            btn_browse.setFixedSize(40, 36)
            btn_browse.setCursor(Qt.PointingHandCursor)
            btn_browse.setStyleSheet(ThemeManager.get_button_style("secondary"))
            btn_browse.clicked.connect(lambda: self.browse_file(path_edit))
            
            btn_flash = QPushButton("Flash Ngay")
            btn_flash.setCursor(Qt.PointingHandCursor)
            # Blue Style
            btn_flash.setStyleSheet("""
                QPushButton {
                    background-color: #007bff; color: white; border-radius: 6px; padding: 8px 15px; font-weight: bold; border: none;
                }
                QPushButton:hover { background-color: #0056b3; }
            """)
            btn_flash.clicked.connect(lambda: self.run_flash(command_key, path_edit.text()))
            
            row.addWidget(lbl)
            row.addWidget(path_edit)
            row.addWidget(btn_browse)
            row.addWidget(btn_flash)
            return row
            
        flash_layout.addLayout(create_flash_row("Recovery (TWRP/OrangeFox):", "recovery"))
        flash_layout.addLayout(create_flash_row("Boot Image (Root):", "boot"))
        
        layout.addWidget(flash_group)
        
        # 2. Wipe Section
        wipe_group = QGroupBox("Công cụ Xóa (Wipe Controls)")
        wipe_group.setStyleSheet(group_style)
        wipe_layout = QHBoxLayout(wipe_group)
        wipe_layout.setSpacing(15)
        
        # Erase Cache
        btn_cache = QPushButton("🗑️ Xóa Cache (Fix treo logo)")
        btn_cache.setMinimumHeight(45)
        btn_cache.setCursor(Qt.PointingHandCursor)
        # Orange/Warning Style
        btn_cache.setStyleSheet("""
            QPushButton {
                background-color: #ff9800; color: white; border-radius: 8px; font-weight: bold; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #e68900; }
        """)
        btn_cache.clicked.connect(lambda: self.fastboot_action("erase cache", "Bạn có chắc muốn xóa phân vùng Cache?"))
        
        # Erase Userdata (Factory Reset)
        btn_userdata = QPushButton("⚠️ Factory Reset (Mất dữ liệu)")
        btn_userdata.setMinimumHeight(45)
        btn_userdata.setCursor(Qt.PointingHandCursor)
        # Red/Danger Style
        btn_userdata.setStyleSheet("""
            QPushButton {
                 background-color: #dc3545; color: white; border-radius: 8px; font-weight: bold; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #bd2130; }
        """)
        btn_userdata.clicked.connect(lambda: self.fastboot_action("erase userdata", "CẢNH BÁO: Hành động này sẽ xóa toàn bộ dữ liệu người dùng!\nBạn có chắc chắn muốn tiếp tục?"))

        wipe_layout.addWidget(btn_cache)
        wipe_layout.addWidget(btn_userdata)
        
        layout.addWidget(wipe_group)
        layout.addStretch()

    def setup_advanced_tab(self):
        # Stub method or remove content if completely unused
        pass

    # --- Logic ---
    # check_device removed (Handling moved to MainWindow global check)
    # open_device_manager removed (Button removed)

    def browse_file(self, line_edit, filter="Image Files (*.img);;All Files (*)"):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file", "", filter)
        if path:
            line_edit.setText(path)

    def run_command(self, cmd_str):
        self.log_output.appendPlainText(f"\n> fastboot {cmd_str}")
        result = self.adb.fastboot_command(cmd_str)
        self.log_output.appendPlainText(result)
        
    def fastboot_action(self, cmd, confirm):
        if QMessageBox.question(self, "Xác nhận", confirm) == QMessageBox.Yes:
            self.run_command(cmd)

    def run_flash(self, partition, file_path):
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file hợp lệ!")
            return
        
        if QMessageBox.question(self, "Flash", f"Bạn có chắc muốn flash vào phân vùng '{partition}'?\nFile: {os.path.basename(file_path)}") == QMessageBox.Yes:
            self.run_command(f"flash {partition} \"{file_path}\"")

    def run_frp_unlock(self):
        if QMessageBox.question(self, "FRP Unlock", "Thực hiện xóa FRP (Google Account)?\nLệnh: erase frp & erase config") == QMessageBox.Yes:
            self.log_output.appendPlainText("\n> Chạy FRP Unlock...")
            res = self.adb.fastboot_unlock_frp()
            self.log_output.appendPlainText(res)

    def run_write_cid(self):
        cid = self.cid_input.text().strip()
        if not cid: return
        self.fastboot_action(f"oem writecid {cid}", f"Bạn có chắc muốn đổi CID thành '{cid}'?")

    def run_flash_token(self):
        path = self.token_path.text().strip()
        if not path: return
        self.run_command(f"flash unlocktoken \"{path}\"")
