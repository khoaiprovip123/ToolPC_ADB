import sys
import os
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, 
    QMessageBox, QFrame, QButtonGroup, QScrollArea, QCheckBox, QDialog,
    QApplication, QGraphicsDropShadowEffect, QProgressBar, QProgressDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPoint
from PySide6.QtGui import QIcon, QColor, QFont, QPainter, QPainterPath

from src.ui.theme_manager import ThemeManager
from src.core.adb.adb_manager import DeviceStatus
from src.data.app_data import AppInfo
from src.workers.app_worker import (
    InstallerThread, BackupThread, AppScanner, SmartAppActionThread
)
from src.core.log_manager import LogManager

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
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_MAIN']};
                border-radius: 20px;
                border: 1px solid {ThemeManager.COLOR_BORDER_LIGHT};
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

class AppConfirmDialog(SoftDialog):
    def __init__(self, action_type, app_name, pkg_name, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        
        # Header
        icon_map = {"uninstall": "🗑️", "disable": "🚫", "restore": "♻️"}
        title_map = {"uninstall": "Gỡ ứng dụng?", "disable": "Tắt ứng dụng?", "restore": "Khôi phục?"}
        
        header = QHBoxLayout()
        icon = QLabel(icon_map.get(action_type, "❓"))
        icon.setStyleSheet("font-size: 28px;")
        title = QLabel(title_map.get(action_type, "Xác nhận?"))
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        header.addWidget(icon)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Info
        info_bg = ThemeManager.COLOR_BG_SECONDARY
        info_box = QFrame()
        info_box.setStyleSheet(f"background: {info_bg}; border-radius: 12px; padding: 10px;")
        ib_layout = QVBoxLayout(info_box)
        
        lbl_name = QLabel(app_name)
        lbl_name.setStyleSheet("font-weight: bold; font-size: 14px; border: none; background: transparent;")
        lbl_pkg = QLabel(pkg_name)
        lbl_pkg.setStyleSheet("color: #7f8c8d; font-size: 12px; font-family: Consolas; border: none; background: transparent;")
        
        ib_layout.addWidget(lbl_name)
        ib_layout.addWidget(lbl_pkg)
        layout.addWidget(info_box)
        
        label = QLabel("Hành động này sẽ thực thi lệnh ADB trực tiếp.")
        label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; margin-top: 5px;")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(ThemeManager.get_button_style("outline"))
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Tiến hành")
        btn_ok.setCursor(Qt.PointingHandCursor)
        color = "danger" if action_type == "uninstall" else "warning" if action_type == "disable" else "success"
        btn_ok.setStyleSheet(ThemeManager.get_button_style(color))
        btn_ok.clicked.connect(self.accept)
        
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)
        
        self.set_content(layout)

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

    def __init__(self, app: AppInfo, parent=None):
        super().__init__(parent)
        self.app = app
        self.setFixedHeight(85)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 18px; /* Softer */
                border: 1px solid {ThemeManager.COLOR_BORDER_LIGHT};
            }}
            QFrame:hover {{
                background-color: {ThemeManager.COLOR_GLASS_HOVER};
                border: 1px solid {ThemeManager.COLOR_BORDER};
            }}
        """)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        
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
        type_text = "SYSTEM" if self.app.is_system else "USER"
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
            status_text = "RUNNING"
            status_color = "#2ecc71"
        else:
            status_text = "DISABLED"
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

class AppManagerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.apps_all: List[AppInfo] = []
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_apps)
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
                border-radius: 25px; /* Softer */
                padding-left: 20px;
                font-size: 15px;
            }}
            QLineEdit:focus {{ border: 2px solid {ThemeManager.COLOR_ACCENT}; }}
        """)
        self.search_input.textChanged.connect(lambda: self.search_timer.start(300))
        
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
        
        search_layout.addWidget(self.search_input)
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
                    background-color: transparent;
                    border: 1px solid {ThemeManager.COLOR_BORDER};
                    border-radius: 20px; /* Softer Pills */
                    padding: 0 24px;
                    color: {ThemeManager.COLOR_TEXT_SECONDARY};
                    font-weight: 600;
                }}
                QPushButton:checked {{
                    background-color: {ThemeManager.COLOR_ACCENT};
                    color: white;
                    border: none;
                }}
            """)
            self.tab_group.addButton(btn, id)
            pill_layout.addWidget(btn)
            
        self.tab_group.button(1).setChecked(True)
        self.tab_group.idClicked.connect(self.filter_apps)
        
        pill_layout.addStretch()
        self.lbl_stats = QLabel("0 apps")
        pill_layout.addWidget(self.lbl_stats)
        main.addLayout(pill_layout)
        
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
        
        # Stop and cleanup old scanner if exists
        if hasattr(self, 'scanner') and self.scanner:
            try:
                self.scanner.stop()
                self.scanner.wait(1000)  # Wait max 1 second
                self.scanner.deleteLater()
            except:
                pass
        
        self.lbl_stats.setText("Đang quét...")
        self.clear_list()
        self.scanner = AppScanner(self.adb)
        self.scanner.finished.connect(self.on_scan_done)
        self.scanner.start()

    def on_scan_done(self, apps):
        self.apps_all = apps
        self.filter_apps()

    def clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def filter_apps(self):
        self.clear_list()
        query = self.search_input.text().strip().lower()
        mode = self.tab_group.checkedId()
        
        filtered = []
        for app in self.apps_all:
            if query and not ((app.name and query in app.name.lower()) or (query in app.package.lower())): continue
            if mode == 2 and not app.is_system: continue
            if mode == 3 and app.is_system: continue
            if mode == 4 and app.is_enabled: continue
            filtered.append(app)
            
        # Display ALL filtered apps (removed [:100] limit)
        for app in filtered:
            row = ModernAppRow(app)
            row.action_triggered.connect(self.handle_row_action)
            self.list_layout.addWidget(row)
            
        self.lbl_stats.setText(f"Hiển thị {len(filtered)}/{len(self.apps_all)}")

    def handle_row_action(self, action, app: AppInfo):
        print(f"DEBUG: handle_row_action called. Action={action}, App={app.package}")
        if not self.adb.is_online():
            print("DEBUG: ADB not online")
            QMessageBox.warning(self, "Lỗi", "Thiết bị mất kết nối!")
            return
            
        if action != "enable":
            print(f"DEBUG: Showing confirmation dialog for {action}")
            dlg = AppConfirmDialog(action, app.name, app.package, self)
            result = dlg.exec()
            print(f"DEBUG: Confirmation dialog result: {result}")
            if result != QDialog.Accepted:
                print("DEBUG: User cancelled")
                return

        print(f"DEBUG: About to call execute_action")
        self.execute_action(app, action)

    def execute_action(self, app: AppInfo, action):
        print(f"DEBUG: execute_action {action} on {app.package}")
        # Progress Feedback
        pd = QProgressDialog(f"Đang {action} ứng dụng...", None, 0, 0, self)
        pd.setWindowTitle("Vui lòng đợi")
        pd.setWindowModality(Qt.WindowModal)
        pd.setCancelButton(None)
        
        pd.show()
        
        self.worker = SmartAppActionThread(self.adb, [app], action)
        
        def on_finished(success, msg):
            print(f"DEBUG: worker finished. Success={success}, Msg={msg}")
            pd.close()
            
            # Show Result Feedback
            if success:
                # Parse the method used from worker message
                action_desc = "xử lý"  # Default fallback
                
                if "Uninstall" in msg or "uninstalled" in msg.lower():
                    action_desc = "gỡ bỏ"
                    app_status = "đã được gỡ khỏi thiết bị"
                elif "Disable" in msg or "disabled" in msg.lower():
                    action_desc = "tắt"
                    app_status = "đã được tắt"
                elif "Hide" in msg or "hidden" in msg.lower():
                    action_desc = "ẩn"
                    app_status = "đã được ẩn"
                elif "Clear" in msg or "cleared" in msg.lower():
                    action_desc = "xóa dữ liệu"
                    app_status = "dữ liệu đã được xóa"
                elif "Force Stop" in msg:
                    action_desc = "dừng"
                    app_status = "đã được dừng"
                else:
                    app_status = "đã được xử lý"
                
                # Notify User via Center with clear message
                LogManager.log("App Manager", f"✓ {app.name} {app_status} thành công!", "success")
                
                # Update State
                if action == "disable": app.is_enabled = False
                elif action == "enable": app.is_enabled = True
                elif action == "uninstall" and app in self.apps_all: self.apps_all.remove(app)
                
                self.filter_apps()
            else:
                # Only show error if truly failed (no success at all)
                LogManager.log("App Manager", f"✗ Không thể xử lý {app.name}: {msg}", "error")
                QMessageBox.warning(self, "Thất bại", f"Lỗi: {msg}")

        self.worker.finished.connect(on_finished)
        self.worker.start()



        
    def reset(self): self.refresh_data()
