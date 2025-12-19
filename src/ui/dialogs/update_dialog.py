# src/ui/dialogs/update_dialog.py
"""
Update Dialogs - UI for update notifications and progress
"""

import os
import subprocess
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from src.ui.theme_manager import ThemeManager
from src.core.downloader import FileDownloader
from src.core.update_manager import UpdateManager


class UpdateNotificationDialog(QDialog):
    """
    Dialog to notify user about available update
    """
    
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.user_choice = None  # 'update', 'skip', 'later'
        
        self.setWindowTitle("Cập Nhật Mới Có Sẵn")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Icon + Title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("🎉")
        icon_label.setStyleSheet("font-size: 48px;")
        header_layout.addWidget(icon_label)
        
        title_layout = QVBoxLayout()
        title = QLabel("Cập Nhật Mới Có Sẵn!")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {ThemeManager.COLOR_ACCENT};
        """)
        title_layout.addWidget(title)
        
        version_label = QLabel(f"Phiên bản {self.update_info['version']}")
        version_label.setStyleSheet(f"""
            font-size: 16px;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
        """)
        title_layout.addWidget(version_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {ThemeManager.COLOR_BORDER};")
        layout.addWidget(separator)
        
        # Changelog
        changelog_label = QLabel("📝 Thay đổi:")
        changelog_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
        """)
        layout.addWidget(changelog_label)
        
        changelog_text = QTextEdit()
        changelog_text.setPlainText(self.update_info.get('changelog', 'Không có thông tin thay đổi.'))
        changelog_text.setReadOnly(True)
        changelog_text.setMaximumHeight(150)
        changelog_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid {ThemeManager.COLOR_BORDER};
                border-radius: 8px;
                padding: 10px;
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                font-size: 13px;
            }}
        """)
        layout.addWidget(changelog_text)
        
        # File size info
        if self.update_info.get('download_url'):
            update_manager = UpdateManager()
            size_str = update_manager.format_file_size(self.update_info.get('file_size', 0))
            size_label = QLabel(f"📦 Kích thước: {size_str}")
            size_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
            layout.addWidget(size_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        skip_btn = QPushButton("Bỏ qua phiên bản này")
        skip_btn.setStyleSheet(ThemeManager.get_button_style("outline"))
        skip_btn.clicked.connect(self.skip_version)
        button_layout.addWidget(skip_btn)
        
        later_btn = QPushButton("Nhắc tôi sau")
        later_btn.setStyleSheet(ThemeManager.get_button_style("outline"))
        later_btn.clicked.connect(self.remind_later)
        button_layout.addWidget(later_btn)
        
        button_layout.addStretch()
        
        update_btn = QPushButton("🚀 Cập nhật ngay")
        update_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        update_btn.clicked.connect(self.start_update)
        update_btn.setDefault(True)
        button_layout.addWidget(update_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeManager.COLOR_BACKGROUND};
            }}
        """)
    
    def start_update(self):
        """User chose to update"""
        self.user_choice = 'update'
        self.accept()
    
    def skip_version(self):
        """User chose to skip this version"""
        self.user_choice = 'skip'
        self.reject()
    
    def remind_later(self):
        """User chose to be reminded later"""
        self.user_choice = 'later'
        self.reject()


class UpdateProgressDialog(QDialog):
    """
    Dialog to show download progress
    """
    
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.downloader = None
        self.download_path = None
        
        self.setWindowTitle("Đang Tải Cập Nhật")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel(f"Đang tải {self.update_info['version']}")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ThemeManager.COLOR_BORDER};
                border-radius: 8px;
                text-align: center;
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                height: 25px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ThemeManager.COLOR_ACCENT},
                    stop:1 {ThemeManager.COLOR_SUCCESS}
                );
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Đang chuẩn bị...")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        layout.addWidget(self.status_label)
        
        # Speed label
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.speed_label)
        
        layout.addStretch()
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setStyleSheet(ThemeManager.get_button_style("outline"))
        self.cancel_btn.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeManager.COLOR_BACKGROUND};
            }}
        """)
    
    def start_download(self):
        """Start downloading update"""
        download_url = self.update_info.get('download_url')
        if not download_url:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy link tải xuống!")
            self.reject()
            return
        
        # Download to temp folder
        import tempfile
        temp_dir = tempfile.gettempdir()
        file_name = self.update_info.get('file_name', 'XiaomiADBCommander_Setup.exe')
        self.download_path = os.path.join(temp_dir, file_name)
        
        # Create downloader
        self.downloader = FileDownloader(download_url, self.download_path)
        
        # Connect signals
        self.downloader.progress.connect(self.update_progress)
        self.downloader.speed_update.connect(self.update_speed)
        self.downloader.finished.connect(self.download_finished)
        self.downloader.error.connect(self.download_error)
        
        # Start download
        self.downloader.start()
        self.status_label.setText("Đang tải xuống...")
    
    def update_progress(self, downloaded: int, total: int, percentage: int):
        """Update progress bar"""
        self.progress_bar.setValue(percentage)
        
        update_manager = UpdateManager()
        downloaded_str = update_manager.format_file_size(downloaded)
        total_str = update_manager.format_file_size(total)
        
        self.status_label.setText(f"Đã tải: {downloaded_str} / {total_str}")
    
    def update_speed(self, speed: float):
        """Update download speed"""
        speed_str = FileDownloader.format_speed(speed)
        self.speed_label.setText(f"Tốc độ: {speed_str}")
    
    def download_finished(self, file_path: str):
        """Download completed"""
        self.status_label.setText("✅ Tải xuống hoàn tất!")
        self.cancel_btn.setText("Đóng")
        
        # Ask user to install
        QTimer.singleShot(500, lambda: self.prompt_install(file_path))
    
    def download_error(self, error_msg: str):
        """Download failed"""
        QMessageBox.critical(self, "Lỗi Tải Xuống", error_msg)
        self.reject()
    
    def cancel_download(self):
        """Cancel download"""
        if self.downloader and self.downloader.isRunning():
            reply = QMessageBox.question(
                self,
                "Xác nhận",
                "Bạn có chắc muốn hủy tải xuống?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.downloader.cancel()
                self.downloader.wait()
                self.reject()
        else:
            self.reject()
    
    def prompt_install(self, file_path: str):
        """Prompt user to install update"""
        reply = QMessageBox.question(
            self,
            "Cài Đặt Cập Nhật",
            f"Tải xuống hoàn tất!\n\nBạn có muốn cài đặt ngay bây giờ?\n\n"
            f"Ứng dụng sẽ tự động đóng và installer sẽ chạy.\n"
            f"File: {os.path.basename(file_path)}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.install_update(file_path)
        else:
            # Just inform user where file is
            QMessageBox.information(
                self,
                "Thông báo",
                f"File cài đặt đã được lưu tại:\n{file_path}\n\n"
                f"Bạn có thể chạy file này sau để cập nhật."
            )
            self.accept()
    
    def install_update(self, file_path: str):
        """Run installer and exit application"""
        try:
            # Run installer
            subprocess.Popen([file_path])
            
            # Exit application
            self.accept()
            
            # Signal to main window to quit
            if self.parent():
                QTimer.singleShot(100, lambda: self.parent().close())
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Lỗi",
                f"Không thể chạy installer:\n{str(e)}\n\n"
                f"Vui lòng chạy thủ công:\n{file_path}"
            )
