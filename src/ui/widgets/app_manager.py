import sys
import os
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, 
    QMessageBox, QFrame, QButtonGroup, QScrollArea, QCheckBox, QDialog,
    QApplication, QGraphicsDropShadowEffect, QProgressBar, QProgressDialog,
    QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPoint
from PySide6.QtGui import QIcon, QColor, QFont, QPainter, QPainterPath

from src.ui.theme_manager import ThemeManager
from src.ui.performance_utils import widget_cache, BatchProcessor, debounce
from src.core.adb.adb_manager import DeviceStatus
from src.data.app_data import AppInfo
from src.workers.app_worker import (
    InstallerThread, BackupThread, AppScanner, SmartAppActionThread
)
from src.core.log_manager import LogManager
from src.ui.dialogs.confirmation_dialog import ConfirmationDialog

# OneDrive APK Repository
ONEDRIVE_APK_FOLDER = "https://4wl8ft-my.sharepoint.com/:f:/g/personal/vankhoai_4wl8ft_onmicrosoft_com/IgDXdoT3HHxqTLwC2ClHOMPsATiYFsuCYtWBDTH1zBQaYG0?e=mjZW4R"


# ===========================
# CUSTOM FRAMELESS DIALOG (Soft UI)
# ===========================
class SoftDialog(QDialog):
    """
    Base class for soft, rounded, frameless dialogs
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(450, 250)
        
        # Main Container with Shadow
        self.container = QFrame(self)
        self.container.setObjectName("SoftDialogContainer")
        self.container.setStyleSheet(f"""
            #SoftDialogContainer {{
                background-color: {ThemeManager.get_theme()['COLOR_DIALOG_BG']};
                border-radius: 24px;
                border: 0.5px solid {ThemeManager.COLOR_BORDER};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.container.setGraphicsEffect(shadow)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.addWidget(self.container)
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(25, 25, 25, 25)
        self.content_layout.setSpacing(15)

    def set_content(self, layout):
        self.content_layout.addLayout(layout)

# ===========================
# SPECIFIC DIALOGS
# ===========================
import webbrowser

class InstallApkDialog(SoftDialog):
    def __init__(self, adb_manager, parent=None):
        super().__init__(parent)
        self.adb = adb_manager
        
        layout = QVBoxLayout()
        title = QLabel("Cài đặt APK")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(title)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Đường dẫn file (.apk)...")
        self.path_edit.setStyleSheet(ThemeManager.get_input_style() + "border-radius: 12px;")
        layout.addWidget(self.path_edit)
        
        btns = QHBoxLayout()
        btns.addStretch()
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setStyleSheet(ThemeManager.get_button_style("outline"))
        btn_cancel.clicked.connect(self.reject)
        
        btn_install = QPushButton("Cài đặt")
        btn_install.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_install.clicked.connect(self.accept)
        
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_install)
        layout.addLayout(btns)
        
        self.set_content(layout)

# Local AppConfirmDialog removed in favor of src.ui.dialogs.confirmation_dialog.ConfirmationDialog

class BackupOptionsDialog(SoftDialog):
    def __init__(self, count, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        title = QLabel("Tùy chọn Sao lưu")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(title)
        
        self.chk_apk = QCheckBox("File bộ cài (.apk)")
        self.chk_apk.setChecked(True)
        self.chk_apk.setStyleSheet(ThemeManager.get_checkbox_style())
        
        self.chk_data = QCheckBox("Dữ liệu ứng dụng (Data)")
        self.chk_data.setStyleSheet(ThemeManager.get_checkbox_style())
        
        layout.addWidget(self.chk_apk)
        layout.addWidget(self.chk_data)
        
        btns = QHBoxLayout()
        btns.addStretch()
        btn_ok = QPushButton("Bắt đầu")
        btn_ok.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_ok)
        
        layout.addLayout(btns)
        self.set_content(layout)

# ===========================
# ROW & WIDGET
# ===========================
class ModernAppRow(QFrame):
    action_triggered = Signal(str, object) 
    toggled = Signal(bool, object) # Signal when checkbox changes

    def __init__(self, app: AppInfo, parent=None):
        super().__init__(parent)
        self.app = app
        self.setFixedHeight(85)
        self.setObjectName("ModernAppRow")
        self.setStyleSheet(f"""
            #ModernAppRow {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 20px;
                border: 0.5px solid {ThemeManager.COLOR_BORDER_LIGHT};
            }}
            #ModernAppRow:hover {{
                background-color: {ThemeManager.COLOR_BG_SECONDARY}40;
                border: 0.5px solid {ThemeManager.COLOR_ACCENT}40;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 12, 20, 12) # Increased left margin to 30
        layout.setSpacing(12)
        
        # 0. Selection Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(32, 32) # Increased from 24 to 32 to prevent clipping
        self.checkbox.setCursor(Qt.PointingHandCursor)
        self.checkbox.setStyleSheet(ThemeManager.get_checkbox_style() + "QCheckBox { padding: 0px; }")
        self.checkbox.toggled.connect(lambda checked: self.toggled.emit(checked, self.app))
        layout.addWidget(self.checkbox)
        
        # 1. Icon
        icon_lbl = QLabel(self.app.name[0].upper() if self.app.name else "?")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(48, 48)
        color_idx = abs(hash(self.app.package)) % 6
        colors = ["#3498DB", "#E67E22", "#E74C3C", "#2ECC71", "#9B59B6", "#F1C40F"]
        icon_lbl.setStyleSheet(f"""
            background-color: {colors[color_idx]};
            color: white;
            border-radius: 16px; /* Softer */
            font-size: 20px;
            font-weight: bold;
            border: none;
        """)
        layout.addWidget(icon_lbl)
        
        # 2. Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignVCenter)
        
        disp_name = self.app.name if self.app.name and self.app.name.strip() else self.app.package
        name_lbl = QLabel(disp_name)
        name_lbl.setStyleSheet(f"font-weight: 700; font-size: 15px; color: {ThemeManager.COLOR_TEXT_PRIMARY}; background: transparent; border: none;")
        
        pkg_lbl = QLabel(self.app.package)
        pkg_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; font-family: Consolas; background: transparent; border: none;")
        
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(pkg_lbl)
        layout.addLayout(info_layout, 1)
        
        # 3. Badges
        type_text = "HỆ THỐNG" if self.app.is_system else "NGƯỜI DÙNG"
        type_bg = "#f39c12" if self.app.is_system else "#3498db"
        
        badge_type = QLabel(type_text)
        badge_type.setFixedSize(65, 26)
        badge_type.setAlignment(Qt.AlignCenter)
        badge_type.setStyleSheet(f"""
            background-color: {type_bg}20; color: {type_bg}; border-radius: 10px; font-size: 10px; font-weight: bold; border: none;
        """)
        layout.addWidget(badge_type)
        
        # Status
        if self.app.is_enabled:
            status_text = "ĐANG CHẠY"
            status_color = "#2ecc71"
        else:
            status_text = "ĐÃ TẮT"
            status_color = "#e74c3c"
            name_lbl.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {ThemeManager.COLOR_TEXT_SECONDARY}; text-decoration: line-through; background: transparent; border: none;")
            
        badge_status = QLabel(status_text)
        badge_status.setFixedSize(75, 26)
        badge_status.setAlignment(Qt.AlignCenter)
        badge_status.setStyleSheet(f"""
            background-color: {status_color}20; color: {status_color}; border-radius: 10px; font-size: 10px; font-weight: bold; border: none;
        """)
        layout.addWidget(badge_status)
        
        # 4. Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        if not self.app.is_enabled:
            # Disabled/Removed apps: Show Restore button
            btn_enable = self.create_action_btn("Khôi phục", "#2ecc71")
            btn_enable.clicked.connect(lambda: (print(f"DEBUG: Enable button clicked for {self.app.package}"), self.action_triggered.emit("enable", self.app)))
            actions_layout.addWidget(btn_enable)
        else:
            # Enabled apps: Show single action button
            if self.app.is_system:
                # System apps: "Xóa" (Remove) - will try disable then uninstall via cascade
                btn_remove = self.create_action_btn("Xóa", "#e74c3c")
                btn_remove.clicked.connect(lambda: (print(f"DEBUG: Remove button clicked for {self.app.package}"), self.action_triggered.emit("disable", self.app)))
                actions_layout.addWidget(btn_remove)
            else:
                # User apps: "Gỡ" (Uninstall) - will uninstall directly
                btn_uninstall = self.create_action_btn("Gỡ", "#e74c3c")
                btn_uninstall.clicked.connect(lambda: (print(f"DEBUG: Uninstall button clicked for {self.app.package}"), self.action_triggered.emit("disable", self.app)))  # Use disable mode for cascade
                actions_layout.addWidget(btn_uninstall)
                
        layout.addLayout(actions_layout)

    def create_action_btn(self, text, color):
        btn = QPushButton(text)
        btn.setFixedSize(80, 34)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 10px; /* Softer */
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        return btn

    def set_checked(self, checked):
        """External control of the checkbox"""
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)


class AppManagerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.apps_all: List[AppInfo] = []
        
        # Optimized: Tăng debounce delay từ 300ms lên 500ms
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_apps)
        
        # Optimized: Batch processor cho rendering
        self.batch_processor = BatchProcessor(batch_size=30)
        
        # Selection management
        self.selected_packages = set()
        
        self.setup_ui()
        QTimer.singleShot(500, self.refresh_data)

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(20)
        main.setContentsMargins(30, 30, 30, 30)
        
        # Header
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm ứng dụng...")
        self.search_input.setFixedHeight(50)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid {ThemeManager.COLOR_BORDER};
                border-radius: 25px; 
                padding-left: 20px;
                font-size: 14px;
                font-family: {ThemeManager.FONT_FAMILY};
            }}
            QLineEdit:focus {{ 
                border: 1px solid {ThemeManager.COLOR_ACCENT}; 
                background-color: {ThemeManager.COLOR_BG_MAIN};
            }}
        """)
        self.search_input.textChanged.connect(lambda: self.search_timer.start(500))  # Increased from 300ms to 500ms
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(50, 50)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid {ThemeManager.COLOR_BORDER};
                border-radius: 25px; /* Circle */
                font-size: 20px;
            }}
            QPushButton:hover {{ background: {ThemeManager.COLOR_GLASS_HOVER}; }}
        """)
        btn_refresh.clicked.connect(self.refresh_data)
        
        self.btn_install_apk = QPushButton("📦 Cài đặt APK")
        self.btn_install_apk.setFixedHeight(50)
        self.btn_install_apk.setCursor(Qt.PointingHandCursor)
        self.btn_install_apk.setStyleSheet(f"""
            QPushButton {{
                background: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid {ThemeManager.COLOR_BORDER};
                border-radius: 25px;
                padding: 0 20px;
                font-size: 14px;
                font-weight: 600;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{ background: {ThemeManager.COLOR_GLASS_HOVER}; }}
        """)
        self.btn_install_apk.clicked.connect(self.on_install_apk_clicked)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_install_apk)
        search_layout.addWidget(btn_refresh)
        main.addLayout(search_layout)
        
        # Tabs
        self.tab_group = QButtonGroup(self)
        pill_layout = QHBoxLayout()
        pill_layout.setSpacing(12)
        
        tabs = [(1, "Tất cả"), (2, "Hệ thống"), (3, "Người dùng"), (4, "Đã tắt")]
        for id, text in tabs:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                    border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                    border-radius: 20px;
                    padding: 0 24px;
                    color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']};
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']};
                    border: 1px solid {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']};
                    color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']};
                }}
                QPushButton:checked {{
                    background: {ThemeManager.COLOR_ACCENT_GRADIENT};
                    color: white;
                    border: none;
                    font-weight: 700;
                }}
            """)
            self.tab_group.addButton(btn, id)
            pill_layout.addWidget(btn)
            
        self.tab_group.button(1).setChecked(True)
        self.tab_group.idClicked.connect(self.filter_apps)
        
        pill_layout.addStretch()
        self.lbl_stats = QLabel("0 apps")
        self.lbl_stats.setStyleSheet(f"color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-weight: 600;")
        pill_layout.addWidget(self.lbl_stats)
        main.addLayout(pill_layout)
        
        # Batch Action Bar
        self.batch_bar = QFrame()
        self.batch_bar.setFixedHeight(50)
        self.batch_bar.setStyleSheet(f"""
            QFrame {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 12px;
            }}
        """)
        batch_layout = QHBoxLayout(self.batch_bar)
        batch_layout.setContentsMargins(30, 0, 20, 0) # Sync with rows
        
        self.chk_all = QCheckBox("Chọn tất cả")
        self.chk_all.setStyleSheet(ThemeManager.get_checkbox_style())
        self.chk_all.clicked.connect(self.toggle_all)
        batch_layout.addWidget(self.chk_all)
        
        batch_layout.addStretch()
        
        self.btn_batch_uninstall = QPushButton("🗑️ Gỡ hàng loạt (0)")
        self.btn_batch_uninstall.setFixedSize(140, 34)
        self.btn_batch_uninstall.setCursor(Qt.PointingHandCursor)
        self.btn_batch_uninstall.setEnabled(False)
        self.btn_batch_uninstall.setStyleSheet(f"""
            QPushButton {{
                background: {ThemeManager.COLOR_ACCENT_GRADIENT};
                color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 11px;
            }}
            QPushButton:disabled {{ background: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; opacity: 0.5; }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        self.btn_batch_uninstall.clicked.connect(self.handle_batch_uninstall)
        batch_layout.addWidget(self.btn_batch_uninstall)
        
        main.addWidget(self.batch_bar)
        
        # List
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(12)
        
        self.scroll.setWidget(self.list_container)
        main.addWidget(self.scroll)

    def refresh_data(self):
        if not self.adb.is_online():
            self.lbl_stats.setText("Mất kết nối")
            return
        
        # Clear selections on refresh
        self.selected_packages.clear()
        self.update_batch_bar()
        
        # Stop and cleanup old scanner if exists
        if hasattr(self, 'scanner') and self.scanner:
            try:
                self.scanner.stop()
                self.scanner.wait(1000)  # Wait max 1 second
                self.scanner.deleteLater()
            except Exception as _e:

                pass  # TODO: consider LogManager.log
        
        self.lbl_stats.setText("Đang quét...")
        self.clear_list()
        self.scanner = AppScanner(self.adb)
        self.scanner.finished.connect(self.on_scan_done)
        self.scanner.start()

    def on_scan_done(self, apps):
        self.apps_all = apps
        self.filter_apps()

    def clear_list(self):
        # IMPORTANT: Clear cache because we are destroying the widgets
        # If we don't, render_app_row will try to reuse deleted widgets
        widget_cache.clear()
        
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): 
                item.widget().deleteLater()

    def filter_apps(self):
        """Filter and display apps (optimized with batch rendering)"""
        # Note: clear_list() is called at the start of filter_apps in the original code? 
        # Yes, line 462 calls self.clear_list().
        # So we just improved clear_list to wipe the cache.
        
        self.clear_list()
        query = self.search_input.text().strip().lower()
        mode = self.tab_group.checkedId()
        
        filtered = []
        for app in self.apps_all:
            # Safe logic for filtering
            if query:
                name_match = app.name and query in app.name.lower()
                pkg_match = query in app.package.lower()
                if not (name_match or pkg_match): continue
                
            if mode == 2 and not app.is_system: continue
            if mode == 3 and app.is_system: continue
            if mode == 4 and app.is_enabled: continue
            filtered.append(app)
        
        # Optimized: Batch render apps để tránh UI freeze với danh sách lớn
        def render_app_row(app):
            # Check cache first
            cache_key = f"app_row_{app.package}"
            row = widget_cache.get(cache_key)
            
            if row is None:
                row = ModernAppRow(app)
                row.action_triggered.connect(self.handle_row_action)
                row.toggled.connect(self.handle_row_toggled)
                widget_cache.put(cache_key, row)
            
            # Update checkbox state from current selections
            row.set_checked(app.package in self.selected_packages)
            
            self.list_layout.addWidget(row)
        
        # Render first 30 immediately, rest in batches
        if len(filtered) <= 30:
            for app in filtered:
                render_app_row(app)
        else:
            # Render first batch immediately
            for app in filtered[:30]:
                render_app_row(app)
            
            # Rest in background batches
            self.batch_processor.process(
                filtered[30:],
                render_app_row,
                lambda: self.lbl_stats.setText(f"Hiển thị {len(filtered)}/{len(self.apps_all)}")
            )
            
        self.lbl_stats.setText(f"Hiển thị {len(filtered)}/{len(self.apps_all)}")

    def handle_row_action(self, action, app: AppInfo):
        print(f"DEBUG: handle_row_action called. Action={action}, App={app.package}")
        if not self.adb.is_online():
            print("DEBUG: ADB not online")
            LogManager.log("App Manager", "Thiết bị mất kết nối!", "error")
            return
            
        if action != "enable":
            print(f"DEBUG: Showing confirmation dialog for {action}")
            title_map = {"uninstall": "Gỡ ứng dụng?", "disable": "Xử lý ứng dụng?", "restore": "Khôi phục?"}
            msg_map = {
                "uninstall": f"Bạn có chắc muốn gỡ bỏ hoàn toàn ứng dụng này?",
                "disable": f"Bạn muốn vô hiệu hóa ứng dụng này?",
                "restore": f"Khôi phục ứng dụng về trạng thái ban đầu?"
            }
            
            dlg = ConfirmationDialog(
                self,
                title=title_map.get(action, "Xác nhận"),
                message=msg_map.get(action, "Bạn có chắc chắn?"),
                details=f"Ứng dụng: {app.name}\nPackage: {app.package}\n\n⚠️ Lưu ý: Hành động này sẽ thay đổi hệ thống.",
                confirm_text="Tiến hành",
                cancel_text="Hủy",
                warning_mode=(action != "restore")
            )
            
            if dlg.exec_() != QDialog.Accepted:
                print("DEBUG: User cancelled")
                return

        print(f"DEBUG: About to call execute_action")
        self.execute_action([app], action)

    def handle_row_toggled(self, checked, app: AppInfo):
        """Update selected packages set and sync UI"""
        if checked:
            self.selected_packages.add(app.package)
        else:
            self.selected_packages.discard(app.package)
        self.update_batch_bar()

    def update_batch_bar(self):
        """Update batch button text and state"""
        count = len(self.selected_packages)
        self.btn_batch_uninstall.setText(f"🗑️ Gỡ hàng loạt ({count})")
        self.btn_batch_uninstall.setEnabled(count > 0)
        # Update chk_all state if needed - semi-manual sync
        
    def toggle_all(self, checked):
        """Select or deselect all CURRENTLY VISIBLE apps"""
        # We only select what's currently in the filtered list for better UX
        # 1. Get packages from visible widgets
        visible_packages = []
        for i in range(self.list_layout.count()):
            widget = self.list_layout.itemAt(i).widget()
            if isinstance(widget, ModernAppRow):
                pkg = widget.app.package
                visible_packages.append(pkg)
                widget.set_checked(checked)
                
        # 2. Update set
        if checked:
            for pkg in visible_packages:
                self.selected_packages.add(pkg)
        else:
            for pkg in visible_packages:
                self.selected_packages.discard(pkg)
                
        self.update_batch_bar()

    def handle_batch_uninstall(self):
        """Confirm and execute batch action"""
        if not self.selected_packages: return
        
        count = len(self.selected_packages)
        dlg = ConfirmationDialog(
            self,
            title=f"Gỡ {count} ứng dụng?",
            message=f"Bạn có chắc chắn muốn gỡ bỏ {count} ứng dụng đã chọn?",
            details=f"Danh sách package:\n" + "\n".join(list(self.selected_packages)[:10]) + ("\n..." if count > 10 else ""),
            confirm_text="Gỡ hàng loạt",
            cancel_text="Hủy",
            warning_mode=True
        )
        
        if dlg.exec_() != QDialog.Accepted:
            return
            
        # Find AppInfo objects for selected packages
        apps_to_proc = [a for a in self.apps_all if a.package in self.selected_packages]
        if not apps_to_proc: return
        
        self.execute_action(apps_to_proc, "disable") # Use disable mode for smart cascade

    def execute_action(self, apps_to_proc: List[AppInfo], action):
        count = len(apps_to_proc)
        app_name = apps_to_proc[0].name if count == 1 else f"{count} ứng dụng"
        
        print(f"DEBUG: execute_action {action} on {count} apps")

        # Progress Feedback
        pd = QProgressDialog(f"Đang {action} ứng dụng...", None, 0, 0, self)
        pd.setWindowTitle("Vui lòng đợi")
        pd.setWindowModality(Qt.WindowModal)
        pd.setCancelButton(None)
        pd.setStyleSheet(ThemeManager.get_main_window_style())
        pd.show()
        
        # Guard: wait for old worker before creating new
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.wait(3000)
        self.worker = SmartAppActionThread(self.adb, apps_to_proc, action)
        
        def on_finished(success, msg):
            print(f"DEBUG: worker finished. Success={success}, Msg={msg}")
            pd.close()
            
            # Show Result Feedback
            if success:
                # Clear selection after success
                self.selected_packages.clear()
                self.update_batch_bar()
                self.chk_all.setChecked(False)

                # Parse the method used from worker message
                action_desc = "xử lý"  # Default fallback
                
                if "Uninstall" in msg or "uninstalled" in msg.lower():
                    action_desc = "gỡ bỏ"
                elif "Disable" in msg or "disabled" in msg.lower():
                    action_desc = "tắt"
                
                # Notify User via Center
                res_msg = f"✓ Đã {action_desc} {app_name} thành công!"
                LogManager.log("App Manager", res_msg, "success")
                
                # Full refresh is safer for batch actions to sync state
                self.refresh_data()
            else:
                LogManager.log("App Manager", f"✗ Lỗi khi xử lý {app_name}: {msg}", "error")

        self.worker.finished.connect(on_finished)
        self.worker.start()


        
    def on_install_apk_clicked(self):
        if not self.adb.is_online():
            LogManager.log("App Manager", "Thiết bị mất kết nối!", "error")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file APK", "", "Android Package (*.apk)"
        )
        
        if not file_path:
            return
            
        # Progress Dialog
        self.install_pd = QProgressDialog("Đang cài đặt APK...", "Hủy", 0, 0, self)
        self.install_pd.setWindowTitle("Cài đặt")
        self.install_pd.setWindowModality(Qt.WindowModal)
        self.install_pd.setStyleSheet(ThemeManager.get_main_window_style())
        self.install_pd.show()
        
        # Start Installer Thread
        self.installer = InstallerThread(self.adb, [file_path])
        self.installer.progress.connect(self.install_pd.setLabelText)
        self.installer.finished.connect(self.on_install_finished)
        self.installer.start()

    def on_install_finished(self, success, msg):
        self.install_pd.close()
        if success:
            LogManager.log("App Manager", f"✓ Cài đặt APK thành công!", "success")
            self.refresh_data()
        else:
            LogManager.log("App Manager", f"✗ Cài đặt APK thất bại: {msg}", "error")

    def hideEvent(self, event):
        """Dọn dẹp Worker khi chuyển tab"""
        if hasattr(self, 'search_timer'):
            self.search_timer.stop()
        if hasattr(self, 'scanner') and self.scanner:
            try:
                self.scanner.stop()
                self.scanner.wait(1000)
            except Exception:
                pass
        super().hideEvent(event)

    def showEvent(self, event):
        """Tải lại nếu chưa có dữ liệu"""
        if self.adb.is_online() and not self.apps_all:
            self.refresh_data()
        super().showEvent(event)

    def reset(self): self.refresh_data()
