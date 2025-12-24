# src/ui/widgets/settings.py
"""
Settings Widget - Application configuration
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QLineEdit, QFormLayout, QFileDialog,
    QMessageBox, QScrollArea, QListWidget, QStackedWidget, QListWidgetItem,
    QButtonGroup, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, QSize, QSettings, QDateTime
from src.ui.theme_manager import ThemeManager
from src.version import __version__, __app_name__
from src.core.update_manager import UpdateChecker
from src.ui.dialogs.update_dialog import UpdateNotificationDialog, UpdateProgressDialog

class SettingsWidget(QWidget):
    """
    Application Settings Widget
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.settings = QSettings("VanKhoai", "XiaomiADBCommander")
        self.update_checker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. Header & Tabs
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.6);
            }}
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title = QLabel("Cài Đặt & Cấu Hình")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        header_layout.addWidget(title)
        
        # Tab Buttons Container
        tabs_container = QFrame()
        tabs_container.setStyleSheet("background-color: rgba(0,0,0,0.05); border-radius: 10px; padding: 4px;")
        tabs_layout = QHBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(4, 4, 4, 4)
        tabs_layout.setSpacing(8)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        tabs = [
            ("Chung", 0),
            ("Cấu hình ADB", 1),
            ("Cloud Sync", 2),
            ("Cập Nhật", 3),
            ("Giới thiệu", 4)
        ]
        
        for text, index in tabs:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            # Apply Segmented Button Style directly here or via class
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                    color: {ThemeManager.COLOR_TEXT_SECONDARY};
                    padding: 8px 20px;
                    font-size: 14px;
                }}
                QPushButton:checked {{
                    background-color: {ThemeManager.COLOR_ACCENT_TRANSPARENT};
                    color: {ThemeManager.COLOR_ACCENT};
                    font-weight: 800;
                }}
                QPushButton:hover {{
                    background-color: rgba(0,0,0,0.05);
                }}
            """)
            
            self.btn_group.addButton(btn, index)
            tabs_layout.addWidget(btn)
            
            if index == 0:
                btn.setChecked(True)
                
        tabs_layout.addStretch()
        header_layout.addWidget(tabs_container)
        
        main_layout.addWidget(header_frame)

        # 2. Content Stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # General Page
        general_page = self.create_general_page()
        self.stack.addWidget(general_page)

        # ADB Page
        adb_page = self.create_adb_page()
        self.stack.addWidget(adb_page)

        # Cloud Sync Page
        cloud_page = self.create_cloud_page()
        self.stack.addWidget(cloud_page)

        # Update Page
        update_page = self.create_update_page()
        self.stack.addWidget(update_page)

        # About Page
        about_page = self.create_about_page()
        self.stack.addWidget(about_page)
        
        # Connect Group
        self.btn_group.idClicked.connect(self.stack.setCurrentIndex)

    def create_general_page(self):
        """Create the general settings page"""
        page = QWidget()
        content_layout = QVBoxLayout(page)
        
        # General Settings
        general_group = QGroupBox("Chung")
        general_group.setStyleSheet(self.get_group_style())
        general_layout = QFormLayout(general_group)
        
        self.theme_combo = QComboBox()
        # Load themes dynamically
        themes = ThemeManager.get_available_themes()
        for name, key in themes:
            self.theme_combo.addItem(name, key)
            
        # Set current selection
        current = ThemeManager._current_theme
        index = self.theme_combo.findData(current)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        self.theme_combo.setStyleSheet(ThemeManager.get_input_style())
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        general_layout.addRow("Giao diện:", self.theme_combo)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Tiếng Việt", "Tiếng Anh"])
        self.lang_combo.setStyleSheet(ThemeManager.get_input_style())
        general_layout.addRow("Ngôn ngữ:", self.lang_combo)
        
        content_layout.addWidget(general_group)
        
        # Menu Visibility Settings
        menu_group = QGroupBox("Hiển thị Menu / Menu Visibility")
        menu_group.setStyleSheet(self.get_group_style())
        menu_layout = QVBoxLayout(menu_group)
        
        menu_desc = QLabel("Bật/tắt các menu trong thanh điều hướng bên trái:")
        menu_desc.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px;")
        menu_layout.addWidget(menu_desc)
        
        # Advanced Commands Toggle
        self.advanced_menu_checkbox = QCheckBox("⚡ Hiện menu 'Nâng Cao' / Show 'Advanced' menu")
        show_advanced = self.settings.value("show_advanced_menu", True, type=bool)
        self.advanced_menu_checkbox.setChecked(show_advanced)
        self.advanced_menu_checkbox.stateChanged.connect(self.on_menu_changed_preview) # Optional: just track change if needed, or do nothing
        self.advanced_menu_checkbox.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px; padding: 5px;")
        menu_layout.addWidget(self.advanced_menu_checkbox)
        
        content_layout.addWidget(menu_group)
        content_layout.addStretch()
        
        # Global Save Button
        save_btn = QPushButton("💾 Lưu Cài Đặt / Save Settings")
        save_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        save_btn.setFixedHeight(45)
        save_btn.clicked.connect(self.save_general_settings)
        content_layout.addWidget(save_btn)

        return page
    
    def on_menu_changed_preview(self, state):
        # Optional: Enable Save button if it was disabled
        pass

    def save_general_settings(self):
        """Save and apply all general settings"""
        # 1. Advanced Menu Visibility
        show_advanced = self.advanced_menu_checkbox.isChecked()
        self.settings.setValue("show_advanced_menu", show_advanced)
        
        # Notify main window to update sidebar
        if self.window() and hasattr(self.window(), 'update_menu_visibility'):
            self.window().update_menu_visibility('advanced', show_advanced)
            
        # 2. Language (Placeholder for now)
        # lang = self.lang_combo.currentText()
        # self.settings.setValue("language", lang)
        
        QMessageBox.information(self, "Đã Lưu", "Cài đặt đã được lưu và áp dụng thành công! ✅")

    def create_adb_page(self):
        """Create the ADB configuration page"""
        page = QWidget()
        content_layout = QVBoxLayout(page)

        # ADB Settings
        adb_group = QGroupBox("Cấu hình ADB")
        adb_group.setStyleSheet(self.get_group_style())
        adb_layout = QVBoxLayout(adb_group)
        
        adb_path_layout = QHBoxLayout()
        self.adb_path_input = QLineEdit()
        self.adb_path_input.setText(self.adb.adb_path)
        self.adb_path_input.setPlaceholderText("Đường dẫn đến tập tin thực thi adb")
        self.adb_path_input.setStyleSheet(ThemeManager.get_input_style())
        adb_path_layout.addWidget(self.adb_path_input)
        
        browse_btn = QPushButton("Duyệt")
        browse_btn.clicked.connect(self.browse_adb)
        browse_btn.setStyleSheet(ThemeManager.get_button_style("outline"))
        adb_path_layout.addWidget(browse_btn)
        
        adb_layout.addLayout(adb_path_layout)
        
        save_adb_btn = QPushButton("Lưu đường dẫn ADB")
        save_adb_btn.clicked.connect(self.save_adb_path)
        save_adb_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        adb_layout.addWidget(save_adb_btn)
        
        # Fix Connection Button
        fix_btn = QPushButton("🛠️ Sửa lỗi kết nối USB (Fix Connection)")
        fix_btn.clicked.connect(self.fix_connection)
        fix_btn.setStyleSheet(ThemeManager.get_button_style("warning"))
        adb_layout.addWidget(fix_btn)
        
        content_layout.addWidget(adb_group)
        content_layout.addStretch()

        return page

    def create_cloud_page(self):
        """Create Cloud Sync Configuration Page"""
        page = QWidget()
        content_layout = QVBoxLayout(page)
        
        group = QGroupBox("Cấu hình Đồng bộ Đám mây")
        group.setStyleSheet(self.get_group_style())
        layout = QVBoxLayout(group)
        
        desc = QLabel(
            "Chọn thư mục đồng bộ trên máy tính (ví dụ: thư mục Google Drive, OneDrive, Dropbox).\n"
            "Khi bạn chọn 'Backup', file sẽ được tự động lưu vào thư mục này để đồng bộ lên mây."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        path_layout = QHBoxLayout()
        self.cloud_path_input = QLineEdit()
        # You might want to load this from QSettings
        self.cloud_path_input.setPlaceholderText("Đường dẫn thư mục Cloud (Ví dụ: C:\\Users\\Name\\OneDrive)")
        self.cloud_path_input.setStyleSheet(ThemeManager.get_input_style())
        path_layout.addWidget(self.cloud_path_input)
        
        browse_btn = QPushButton("Chọn Thư mục")
        browse_btn.clicked.connect(self.browse_cloud_folder)
        browse_btn.setStyleSheet(ThemeManager.get_button_style("outline"))
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        save_btn = QPushButton("Lưu Cấu hình Cloud")
        # save_btn.clicked.connect(self.save_cloud_config) # Implement save later
        save_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        layout.addWidget(save_btn)
        
        content_layout.addWidget(group)
        content_layout.addStretch()
        return page

    def create_update_page(self):
        """Create the Update page"""
        page = QWidget()
        content_layout = QVBoxLayout(page)
        
        # Update Settings Group
        update_group = QGroupBox("Kiểm Tra Cập Nhật")
        update_group.setStyleSheet(self.get_group_style())
        update_layout = QVBoxLayout(update_group)
        
        # Current version info
        version_label = QLabel(f"Phiên bản hiện tại: <b>{__version__}</b>")
        version_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 14px;")
        update_layout.addWidget(version_label)
        
        # Check now button
        check_btn = QPushButton("🔍 Kiểm tra cập nhật ngay")
        check_btn.clicked.connect(self.manual_check_update)
        check_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        update_layout.addWidget(check_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {ThemeManager.COLOR_BORDER}; margin: 10px 0;")
        update_layout.addWidget(separator)
        
        # Auto-check settings
        # Auto-check settings
        self.auto_check_checkbox = QCheckBox("Tự động kiểm tra khi khởi động")
        auto_check = self.settings.value("auto_check_updates", True, type=bool)
        self.auto_check_checkbox.setChecked(auto_check)
        # self.auto_check_checkbox.stateChanged.connect(self.toggle_auto_check) # Removed immediate save
        self.auto_check_checkbox.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px;")
        update_layout.addWidget(self.auto_check_checkbox)
        
        self.prerelease_checkbox = QCheckBox("Bao gồm phiên bản beta (pre-release)")
        include_prerelease = self.settings.value("include_prerelease", True, type=bool)
        self.prerelease_checkbox.setChecked(include_prerelease)
        # self.prerelease_checkbox.stateChanged.connect(self.toggle_prerelease) # Removed immediate save
        self.prerelease_checkbox.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px;")
        update_layout.addWidget(self.prerelease_checkbox)
        
        # Save Button for Update Settings
        save_update_btn = QPushButton("💾 Lưu Cài Đặt Cập Nhật")
        save_update_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        save_update_btn.clicked.connect(self.save_update_settings)
        update_layout.addWidget(save_update_btn)
        
        # Last check info
        last_check = self.settings.value("last_update_check", None)
        if last_check:
            last_check_dt = QDateTime.fromString(last_check, Qt.ISODate)
            last_check_str = last_check_dt.toString("dd/MM/yyyy HH:mm")
        else:
            last_check_str = "Chưa kiểm tra"
        
        self.last_check_label = QLabel(f"Lần kiểm tra cuối: {last_check_str}")
        self.last_check_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; margin-top: 10px;")
        update_layout.addWidget(self.last_check_label)
        
        content_layout.addWidget(update_group)
        
        # Info box
        info_group = QGroupBox("ℹ️ Thông Tin")
        info_group.setStyleSheet(self.get_group_style())
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(
            "Hệ thống tự động kiểm tra phiên bản mới từ GitHub Releases.\n"
            "Khi có bản cập nhật, bạn sẽ nhận được thông báo và có thể "
            "tải xuống trực tiếp từ ứng dụng."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px;")
        info_layout.addWidget(info_text)
        
        content_layout.addWidget(info_group)
        content_layout.addStretch()
        
        return page
    
    def manual_check_update(self):
        """Manually check for updates"""
        # Show loading state
        if hasattr(self, 'last_check_label'):
            self.last_check_label.setText("Đang kiểm tra...")
        
        # Check in background
        include_prerelease = self.settings.value("include_prerelease", False, type=bool)
        self.update_checker = UpdateChecker(include_prerelease)
        self.update_checker.update_found.connect(self.on_update_found)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error_occurred.connect(self.on_update_error)
        self.update_checker.start()
        
        # Update last check time
        current_time = QDateTime.currentDateTime().toString(Qt.ISODate)
        self.settings.setValue("last_update_check", current_time)
    
    def on_update_found(self, update_info: dict):
        """Handle update found"""
        # Update UI
        if hasattr(self, 'last_check_label'):
            current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm")
            self.last_check_label.setText(f"Lần kiểm tra cuối: {current_time}")
        
        # Check if this version should be skipped
        skip_version = self.settings.value("skip_version", "")
        if skip_version == update_info['version']:
            QMessageBox.information(
                self,
                "Cập Nhật",
                f"Phiên bản {update_info['version']} có sẵn (bạn đã chọn bỏ qua).\n\n"
                f"Bạn có thể kiểm tra lại để cập nhật."
            )
            return
        
        # Show update dialog
        dialog = UpdateNotificationDialog(update_info, self)
        result = dialog.exec()
        
        if dialog.user_choice == 'update':
            # Start download
            self.start_update_download(update_info)
        elif dialog.user_choice == 'skip':
            # Save skip version
            self.settings.setValue("skip_version", update_info['version'])
            QMessageBox.information(self, "Thông báo", f"Đã bỏ qua phiên bản {update_info['version']}.")
    
    def on_no_update(self):
        """Handle no update available"""
        if hasattr(self, 'last_check_label'):
            current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm")
            self.last_check_label.setText(f"Lần kiểm tra cuối: {current_time}")
        
        QMessageBox.information(
            self,
            "Cập Nhật",
            f"Bạn đang sử dụng phiên bản mới nhất ({__version__})! 🎉"
        )
    
    def on_update_error(self, error_msg: str):
        """Handle update check error"""
        if hasattr(self, 'last_check_label'):
            current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm")
            self.last_check_label.setText(f"Lần kiểm tra cuối: {current_time} (Lỗi)")
        
        QMessageBox.warning(
            self,
            "Lỗi Kiểm Tra Cập Nhật",
            f"Không thể kiểm tra cập nhật:\n{error_msg}\n\n"
            f"Vui lòng kiểm tra kết nối internet và thử lại."
        )
    
    def start_update_download(self, update_info: dict):
        """Start downloading update"""
        progress_dialog = UpdateProgressDialog(update_info, self)
        progress_dialog.start_download()
        progress_dialog.exec()
    
    def manual_check_update(self):
        """Manually check for updates"""
        # ... existing implementation ...
    
    def save_update_settings(self):
        """Save and apply update settings"""
        auto_check = self.auto_check_checkbox.isChecked()
        include_prerelease = self.prerelease_checkbox.isChecked()
        
        self.settings.setValue("auto_check_updates", auto_check)
        self.settings.setValue("include_prerelease", include_prerelease)
        
        QMessageBox.information(self, "Đã Lưu", "Cài đặt cập nhật đã được lưu thành công! ✅")

    def toggle_auto_check(self, state):
        """Toggle auto-check updates setting - DEPRECATED (Kept for compatibility if needed or removed)"""
        # Now handled by save_update_settings
        pass
    
    def toggle_prerelease(self, state):
        """Toggle include pre-release setting - DEPRECATED"""
        # Now handled by save_update_settings
        pass

    def create_about_page(self):
        """Create the detailed about page"""
        page = QWidget()
        content_layout = QVBoxLayout(page)
        
        # Scroll Area for long content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_container = QWidget()
        content_layout_inner = QVBoxLayout(content_container)
        
        # About Header
        about_group = QGroupBox("Giới thiệu")
        about_group.setStyleSheet(self.get_group_style())
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel(
            "<h2>📱 Xiaomi ADB Commander</h2>"
            f"<p><b>Phiên bản:</b> {__version__} (Latest)</p>"
            "<p><b>Tác giả:</b> Van Khoai</p>"
            "<p>Công cụ quản lý thiết bị Android toàn diện, tối ưu hóa đặc biệt cho Xiaomi/MIUI/HyperOS.</p>"
        )
        about_text.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        about_layout.addWidget(about_text)
        content_layout_inner.addWidget(about_group)
        
        # New Features / Changelog Preview (Dynamic from Release Notes)
        changelog_group = QGroupBox(f"Cập nhật mới (v{__version__})")
        changelog_group.setStyleSheet(self.get_group_style())
        changelog_layout = QVBoxLayout(changelog_group)
        
        # Release Notes v2.5.2 mapped content
        changelog_html = """
        <h3 style="margin-bottom: 5px;">🔧 Fixes & Optimizations (v2.5.2)</h3>
        <ul style="margin-top: 0px; margin-bottom: 10px; margin-left: -20px; color: #333;">
            <li>✅ <b>Dashboard Fix:</b> Resolved "Checking..." freeze and missing data display.</li>
            <li>✅ <b>ART Tuning:</b> Fixed crash and added real-time progress for app optimization.</li>
            <li>✅ <b>Log System:</b> Added file logging (app_log.txt) for better debugging.</li>
            <li>✅ <b>Stability:</b> Fixed random crashes during long-running tasks.</li>
        </ul>
        """
        if ThemeManager.get_theme() == "dark":
             changelog_html = changelog_html.replace("#333", "#eee")
             
        changelog_label = QLabel(changelog_html)
        changelog_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        changelog_layout.addWidget(changelog_label)
        content_layout_inner.addWidget(changelog_group)
        
        # Features List
        features_group = QGroupBox("Tính năng Chính")
        features_group.setStyleSheet(self.get_group_style())
        features_layout = QVBoxLayout(features_group)
        
        features_html = """
        <ul style="margin-top: 0px; margin-bottom: 0px; margin-left: -20px; color: #333;">
            <li><b>Dashboard:</b> Xem thông tin chi tiết thiết bị, tình trạng pin, bộ nhớ.</li>
            <li><b>Quản lý Ứng dụng:</b> Cài đặt, gỡ bỏ, vô hiệu hóa ứng dụng hệ thống (Debloat).</li>
            <li><b>File Manager:</b> Quản lý tệp tin, kéo thả, upload/download nhanh chóng.</li>
            <li><b>Screen Mirror:</b> Phản chiếu màn hình điện thoại lên máy tính (Scrcpy tích hợp).</li>
            <li><b>Xiaomi Tools:</b> Bỏ qua tài khoản Mi, tắt quảng cáo hệ thống (MSA), tối ưu MIUI.</li>
            <li><b>Fastboot & Recovery:</b> Các công cụ nạp ROM, xóa dữ liệu, reboot nâng cao.</li>
        </ul>
        """
        if ThemeManager.get_theme() == "dark":
             features_html = features_html.replace("#333", "#eee")
             
        features_label = QLabel(features_html)
        features_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        features_layout.addWidget(features_label)
        content_layout_inner.addWidget(features_group)
        
        # Roadmap / Dev Status
        dev_group = QGroupBox("Lộ trình Phát triển (Roadmap)")
        dev_group.setStyleSheet(self.get_group_style())
        dev_layout = QVBoxLayout(dev_group)
        
        dev_html = """
        <p><b>Đang phát triển (Upcoming):</b></p>
        <ul style="margin-top: 0px; margin-left: -20px;">
            <li>☁️ <b>Cloud Sync Global:</b> Đồng bộ trực tiếp Google Drive API (Không cần qua thư mục máy tính).</li>
            <li>🐧 <b>Linux/Mac Support:</b> Hỗ trợ đa nền tảng tốt hơn.</li>
            <li>⚡ <b>Flash ROM Auto:</b> Tự động tải và flash ROM Stock cho Xiaomi.</li>
            <li>🔋 <b>Battery Cycle Reset:</b> (Cần Root) Reset số lần sạc pin.</li>
        </ul>
        <p><i>Mọi ý kiến đóng góp xin vui lòng liên hệ tác giả.</i></p>
        """
        dev_label = QLabel(dev_html)
        dev_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        dev_layout.addWidget(dev_label)
        content_layout_inner.addWidget(dev_group)
        
        content_layout_inner.addStretch()
        
        scroll.setWidget(content_container)
        content_layout.addWidget(scroll)

        return page
        
    def get_group_style(self):
        return f"""
            QGroupBox {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                margin-top: 10px;
                padding: 15px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """
        
    def browse_adb(self):
        """Browse for ADB executable"""
        path, _ = QFileDialog.getOpenFileName(self, "Chọn tập tin thực thi ADB", "", "Executables (*.exe);;All Files (*)")
        if path:
            self.adb_path_input.setText(path)
            
    def browse_cloud_folder(self):
        """Browse for Cloud Sync folder"""
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục đồng bộ Cloud")
        if path:
            self.cloud_path_input.setText(path)
            
    def save_adb_path(self):
        """Save ADB path"""
        path = self.adb_path_input.text().strip()
        if os.path.exists(path):
            self.adb.adb_path = path
            QMessageBox.information(self, "Thành công", "Đã cập nhật đường dẫn ADB")
        else:
            QMessageBox.warning(self, "Lỗi", "Đường dẫn không hợp lệ")

    def fix_connection(self):
        """Run ADB Fix Connection"""
        QMessageBox.information(self, "Thông báo", "Đang tiến hành sửa lỗi kết nối...\nVui lòng đợi trong giây lát.")
        
        # Run in background to avoid freezing UI? For now run directly as it's short
        result = self.adb.fix_connection()
        
        QMessageBox.information(self, "Kết quả", result)

    def change_theme(self, index):
        """Handle theme change"""
        theme_key = self.theme_combo.itemData(index)
        if theme_key:
            ThemeManager.set_theme(theme_key)
            
            # Try to update parent window
            if self.window():
                try:
                    self.window().apply_theme()
                    # Also refresh self to apply new styles to inputs/buttons
                    self.setStyleSheet("")  # Reset to force refresh
                    
                    # Notify user with themed message box
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("Đổi Giao Diện")
                    msg_box.setText(f"Đã chuyển sang giao diện: {self.theme_combo.currentText()}.")
                    msg_box.setInformativeText("Một số thành phần có thể cần khởi động lại ứng dụng để hiển thị đúng hoàn toàn.")
                    msg_box.setIcon(QMessageBox.Information)
                    
                    # Apply theme styling to message box
                    theme = ThemeManager.get_theme()
                    msg_box.setStyleSheet(f"""
                        QMessageBox {{
                            background-color: {theme['COLOR_GLASS_WHITE']};
                            color: {theme['COLOR_TEXT_PRIMARY']};
                        }}
                        QMessageBox QLabel {{
                            color: {theme['COLOR_TEXT_PRIMARY']};
                            background: transparent;
                        }}
                        QPushButton {{
                            background: {ThemeManager.COLOR_ACCENT};
                            color: white;
                            border: none;
                            padding: 8px 20px;
                            border-radius: 6px;
                            font-weight: bold;
                            min-width: 80px;
                        }}
                        QPushButton:hover {{
                            opacity: 0.9;
                        }}
                    """)
                    msg_box.exec()
                except Exception as e:
                    print(f"Error applying theme: {e}")
