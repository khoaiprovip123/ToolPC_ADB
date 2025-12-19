# src/ui/widgets/cloud_sync.py
"""
Cloud Sync & Backup Widget
Style: Glassmorphism
"""

import os
import shutil
import zipfile
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFileDialog, QMessageBox, QGroupBox, QListWidget
)
from PySide6.QtCore import Qt, QStandardPaths
from src.ui.theme_manager import ThemeManager

class CloudSyncWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.config_path = "config.yaml"  # Pivot to dynamic path if needed
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("☁️ Sao lưu & Đồng bộ")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(header)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
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
            }}
            QTabBar::tab:selected {{
                background: rgba(255, 255, 255, 0.8);
                font-weight: bold;
            }}
        """)
        
        # Tab 1: Local Backup
        local_tab = QWidget()
        local_layout = QVBoxLayout(local_tab)
        local_layout.setContentsMargins(20, 20, 20, 20)
        
        # Backup Section
        backup_group = QGroupBox("Sao lưu Cài đặt Tool (PC)")
        backup_group.setStyleSheet(ThemeManager.get_card_style())
        backup_layout = QVBoxLayout(backup_group)
        
        backup_desc = QLabel("Tạo bản sao lưu cấu hình (Settings) và lịch sử của phần mềm trên máy tính.")
        backup_layout.addWidget(backup_desc)
        
        btn_backup = QPushButton("💾 Sao lưu Setting")
        btn_backup.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_backup.clicked.connect(self.create_backup)
        backup_layout.addWidget(btn_backup)
        
        local_layout.addWidget(backup_group)
        
        # Restore Section
        restore_group = QGroupBox("Khôi phục")
        restore_group.setStyleSheet(ThemeManager.get_card_style())
        restore_layout = QVBoxLayout(restore_group)
        
        restore_desc = QLabel("Khôi phục dữ liệu từ file sao lưu (.zip).")
        restore_layout.addWidget(restore_desc)
        
        btn_restore = QPushButton("📂 Khôi phục (Restore)")
        btn_restore.setStyleSheet(ThemeManager.get_button_style("outline"))
        btn_restore.clicked.connect(self.restore_backup)
        restore_layout.addWidget(btn_restore)
        
        local_layout.addWidget(restore_group)
        local_layout.addStretch()
        
        tabs.addTab(local_tab, "Local Backup")
        
        # Tab 2: Cloud
        cloud_tab = QWidget()
        cloud_layout = QVBoxLayout(cloud_tab)
        cloud_layout.setContentsMargins(20, 20, 20, 20)
        
        cloud_desc = QLabel("Đồng bộ dữ liệu lên đám mây (Tính năng đang phát triển)")
        cloud_desc.setAlignment(Qt.AlignCenter)
        cloud_layout.addWidget(cloud_desc)
        
        cloud_btns = QHBoxLayout()
        btn_gdrive = QPushButton("Google Drive")
        btn_gdrive.setEnabled(False)
        cloud_btns.addWidget(btn_gdrive)
        
        btn_dropbox = QPushButton("Dropbox")
        btn_dropbox.setEnabled(False)
        cloud_btns.addWidget(btn_dropbox)
        
        cloud_layout.addLayout(cloud_btns)
        cloud_layout.addStretch()
        
        tabs.addTab(cloud_tab, "Cloud Sync")
        
        layout.addWidget(tabs)
        
    def create_backup(self):
        # Explicit info to prevent confusion with Phone Backup
        confirm = QMessageBox.question(
            self, "Xác nhận Sao lưu",
            "🛠️ Đây là tính năng sao lưu CẤU HÌNH CỦA TOOL trên máy tính (Settings, History...).\n\n"
            "📱 Nếu bạn muốn sao lưu ỨNG DỤNG ĐIỆN THOẠI, vui lòng vào tab 'Ứng Dụng' -> chọn app -> nhấn 'Sao lưu'.\n\n"
            "Bạn có muốn tiếp tục sao lưu cấu hình Tool không?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        default_name = f"adb_commander_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu file backup (PC Settings)", default_name, "Zip Files (*.zip)")
        
        if file_path:
            try:
                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if os.path.exists(self.config_path):
                        zipf.write(self.config_path, "config.yaml")
                        # Add other files like 'history.json' if check existence
                        
                QMessageBox.information(self, "Thành công", f"Đã sao lưu Cấu hình Tool tại:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo backup: {e}")
                
    def restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file backup (PC Settings)", "", "Zip Files (*.zip)")
        
        if file_path:
            confirm = QMessageBox.question(
                self, "Xác nhận khôi phục",
                "Việc khôi phục sẽ ghi đè cài đặt TOOL hiện tại của bạn.\nBạn có chắc chắn muốn tiếp tục?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                try:
                    with zipfile.ZipFile(file_path, 'r') as zipf:
                        # Validate structure
                        if "config.yaml" not in zipf.namelist():
                            raise Exception("File backup không hợp lệ (thiếu config.yaml)")
                            
                        # Extract
                        zipf.extract("config.yaml", ".")
                        
                    QMessageBox.information(self, "Thành công", "Khôi phục thành công! Vui lòng khởi động lại ứng dụng để áp dụng thay đổi.")
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể khôi phục: {e}")
                    
    def reset(self):
        pass
