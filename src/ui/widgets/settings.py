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
from src.workers.callable_worker import CallableWorker
from src.core.log_manager import LogManager

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
        header_frame.setStyleSheet("background: transparent; border: none;")
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title = QLabel("Cài Đặt & Cấu Hình")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {ThemeManager.COLOR_ACCENT}; margin-bottom: 5px;")
        header_layout.addWidget(title)
        
        # Tab Pills Container (Pills/Segmented Control)
        tabs_container = QFrame()
        tabs_container.setObjectName("PillsContainer")
        tabs_container.setStyleSheet(f"""
            #PillsContainer {{
                background: rgba(45, 45, 45, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 4px;
            }}
        """)
        tabs_layout = QHBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(4, 4, 4, 4)
        tabs_layout.setSpacing(4)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        tabs = [
            ("Chung", 0),
            ("Cấu hình ADB", 1),
            ("Cloud Sync", 2),
            ("Cập Nhật", 3)
        ]
        
        for text, index in tabs:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName("PillTab")
            # Modern Pills Style with glassmorphism
            btn.setStyleSheet(f"""
                #PillTab {{
                    background-color: transparent;
                    border: none;
                    border-radius: 16px;
                    font-weight: 500;
                    color: #B4B4B4;
                    padding: 10px 24px;
                    font-size: 14px;
                }}
                #PillTab:checked {{
                    background-color: {ThemeManager.COLOR_ACCENT};
                    color: white;
                    font-weight: 600;
                    border-radius: 16px;
                }}
                #PillTab:hover:!checked {{
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #FFFFFF;
                }}
                #PillTab:focus {{
                    outline: none;
                }}
            """)
            
            self.btn_group.addButton(btn, index)
            tabs_layout.addWidget(btn)
            
            if index == 0:
                btn.setChecked(True)
                
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


        
        # Connect Group
        self.btn_group.idClicked.connect(self.stack.setCurrentIndex)



    def create_card_frame(self, title):
        card = QFrame()
        card.setObjectName("SettingsCard")
        card.setStyleSheet(f"""
            #SettingsCard {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_CARD']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: {ThemeManager.RADIUS_CARD};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        if title:
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {ThemeManager.COLOR_ACCENT}; margin-bottom: 5px;")
            layout.addWidget(lbl_title)
            
        return card, layout

    def create_general_page(self):
        page = QWidget()
        content_layout = QVBoxLayout(page)
        
        # General Settings
        card, card_layout = self.create_card_frame("Chung")
        
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        
        self.theme_combo = QComboBox()
        for name, key in ThemeManager.get_available_themes():
            self.theme_combo.addItem(name, key)
        index = self.theme_combo.findData(ThemeManager._current_theme)
        if index >= 0: self.theme_combo.setCurrentIndex(index)
        self.theme_combo.setStyleSheet(ThemeManager.get_input_style())
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        
        lbl_theme = QLabel("Giao diện:")
        lbl_theme.setStyleSheet(f"color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-weight: 600;")
        form_layout.addRow(lbl_theme, self.theme_combo)
        
        # A2: Language selector — kết nối save setting
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Tiếng Việt", "vi")
        self.lang_combo.addItem("Tiếng Anh", "en")
        saved_lang = self.settings.value("language", "vi")
        lang_idx = self.lang_combo.findData(saved_lang)
        if lang_idx >= 0:
            self.lang_combo.setCurrentIndex(lang_idx)
        self.lang_combo.setStyleSheet(ThemeManager.get_input_style())
        self.lang_combo.currentIndexChanged.connect(self.on_lang_changed)  # A2: kết nối
        
        lbl_lang = QLabel("Ngôn ngữ:")
        lbl_lang.setStyleSheet(f"color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-weight: 600;")
        form_layout.addRow(lbl_lang, self.lang_combo)
        
        card_layout.addLayout(form_layout)
        content_layout.addWidget(card)
        
        content_layout.addStretch()
        return page

    def _save_setting(self, key, value, feedback_msg=None):
        """Helper to save setting with feedback"""
        self.settings.setValue(key, value)
        if feedback_msg:
            self.show_toast(feedback_msg)
            
    def show_toast(self, message):
        """Show a simple toast"""
        from PySide6.QtWidgets import QToolTip
        from PySide6.QtGui import QCursor
        QToolTip.showText(QCursor.pos(), f"✅ {message}", self)

    def on_theme_changed(self, index):
        """Handle theme change with auto-save"""
        theme_key = self.theme_combo.itemData(index)
        if theme_key:
            ThemeManager.set_theme(theme_key)
            if self.window():
                try:
                    self.window().apply_theme()
                    self.setStyleSheet("") # Force refresh
                    self._save_setting("theme", theme_key, f"Đã đổi giao diện: {self.theme_combo.currentText()}")
                except Exception as e:
                    LogManager.log("Settings", f"Lỗi khi đổi theme: {e}", "error")

    def on_lang_changed(self, index):
        """A2: Lưu cài đặt ngôn ngữ và thông báo cần khởi động lại"""
        lang_key = self.lang_combo.itemData(index)
        if lang_key:
            self.settings.setValue("language", lang_key)
            lang_name = self.lang_combo.currentText()
            self.show_toast(f"Đã chọn {lang_name} — Khởi động lại ứng dụng để áp dụng")
            LogManager.log("Settings", f"🌐 Ngôn ngữ được đổi sang: {lang_name}", "info")


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
        
        # Auto-save ADB Path on editing finished
        self.adb_path_input.editingFinished.connect(self.save_adb_path_auto)
        
        # Connect Browse button to update input AND save
        # (Already connected to browse_adb, need to update browse_adb to save too)
        
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
        
        # Auto-save Cloud Path
        self.cloud_path_input.editingFinished.connect(self.save_cloud_path_auto)
        
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
        self.auto_check_checkbox = QCheckBox("Tự động kiểm tra khi khởi động")
        auto_check = self.settings.value("auto_check_updates", True, type=bool)
        self.auto_check_checkbox.setChecked(auto_check)
        self.auto_check_checkbox.stateChanged.connect(self.save_update_settings_auto) 
        self.auto_check_checkbox.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px;")
        update_layout.addWidget(self.auto_check_checkbox)
        
        self.prerelease_checkbox = QCheckBox("Bao gồm phiên bản beta (pre-release)")
        include_prerelease = self.settings.value("include_prerelease", False, type=bool)
        self.prerelease_checkbox.setChecked(include_prerelease)
        self.prerelease_checkbox.stateChanged.connect(self.save_update_settings_auto)
        self.prerelease_checkbox.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px;")
        update_layout.addWidget(self.prerelease_checkbox)
        
        # Removed Save Button
        
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
            LogManager.log(
                "Cập Nhật",
                f"Phiên bản {update_info['version']} có sẵn (bạn đã chọn bỏ qua).\nBạn có thể kiểm tra lại để cập nhật.",
                "info"
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
            LogManager.log("Thông báo", f"Đã bỏ qua phiên bản {update_info['version']}.", "success")
    
    def on_no_update(self):
        """Handle no update available"""
        if hasattr(self, 'last_check_label'):
            current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm")
            self.last_check_label.setText(f"Lần kiểm tra cuối: {current_time}")
        
        LogManager.log(
            "Cập Nhật",
            f"Bạn đang sử dụng phiên bản mới nhất ({__version__})! 🎉",
            "success"
        )
    
    def on_update_error(self, error_msg: str):
        """Handle update check error"""
        if hasattr(self, 'last_check_label'):
            current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm")
            self.last_check_label.setText(f"Lần kiểm tra cuối: {current_time} (Lỗi)")
        
        LogManager.log(
            "Lỗi Kiểm Tra Cập Nhật",
            f"Không thể kiểm tra cập nhật:\n{error_msg}\nVui lòng kiểm tra kết nối internet.",
            "error"
        )
    
    def start_update_download(self, update_info: dict):
        """Start downloading update"""
        progress_dialog = UpdateProgressDialog(update_info, self)
        progress_dialog.start_download()
        progress_dialog.exec()
    

    
    def save_update_settings_auto(self, state=None):
        """Auto save update settings"""
        auto_check = self.auto_check_checkbox.isChecked()
        include_prerelease = self.prerelease_checkbox.isChecked()
        
        self.settings.setValue("auto_check_updates", auto_check)
        self.settings.setValue("include_prerelease", include_prerelease)
        
        self.show_toast("Đã lưu cài đặt cập nhật")


        
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
            self.save_adb_path_auto() # Auto save after browse
            
    def browse_cloud_folder(self):
        """Browse for Cloud Sync folder"""
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục đồng bộ Cloud")
        if path:
            self.cloud_path_input.setText(path)
            self.save_cloud_path_auto()

    def save_adb_path_auto(self):
        """Auto save ADB path"""
        path = self.adb_path_input.text().strip()
        if os.path.exists(path):
            self.adb.adb_path = path
            self._save_setting("adb_path", path, "Đã lưu đường dẫn ADB")
        else:
            # Only warn if not empty (user might be clearing it)
            if path:
                LogManager.log("Lỗi", "Đường dẫn ADB không hợp lệ", "warning")

    def save_cloud_path_auto(self):
        """Auto save Cloud path"""
        path = self.cloud_path_input.text().strip()
        self._save_setting("cloud_sync_path", path, "Đã lưu đường dẫn Cloud")

    def fix_connection(self):
        """A1: Chạy ADB Fix Connection trên background thread (không đơ UI)"""
        # Disable button trong lúc chạy
        btn = self.sender()
        if isinstance(btn, QPushButton):
            btn.setEnabled(False)
            btn.setText("⏳ Đang sửa lỗi...")

        LogManager.log("Settings", "🛠️ Đang sửa lỗi kết nối ADB...", "info")

        self._fix_worker = CallableWorker(self.adb.fix_connection)

        def on_done(result):
            LogManager.log("Settings", f"✓ Kết quả sửa kết nối: {result}", "success")
            if isinstance(btn, QPushButton):
                btn.setEnabled(True)
                btn.setText("🔧 Sửa lỗi kết nối ADB")

        def on_error(err):
            LogManager.log("Settings", f"❌ Lỗi khi sửa kết nối: {err}", "error")
            if isinstance(btn, QPushButton):
                btn.setEnabled(True)
                btn.setText("🔧 Sửa lỗi kết nối ADB")

        self._fix_worker.finished.connect(on_done)
        self._fix_worker.error.connect(on_error)
        self._fix_worker.start()



