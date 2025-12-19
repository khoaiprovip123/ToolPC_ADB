from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QHeaderView,
    QMessageBox, QMenu, QProgressDialog, QGroupBox, QFrame, QGraphicsDropShadowEffect,
    QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor, QBrush, QCursor
from typing import List, Dict, Optional
from dataclasses import dataclass
import re
import os
import time
import zipfile
import tempfile
import shutil
import unicodedata
from src.ui.theme_manager import ThemeManager
from src.core.adb.adb_manager import DeviceStatus

@dataclass
class AppInfo:
    """Application information model"""
    package: str
    name: str
    version: str
    version_code: int
    is_system: bool
    is_enabled: bool
    size: int  # bytes
    install_time: int  # timestamp
    update_time: int
    path: str


class InstallerThread(QThread):
    """Background thread for installing apps"""
    progress = Signal(str) # Status message
    finished = Signal(bool, str) # Success, Message
    
    def __init__(self, adb_manager, paths: List[str], is_split: bool = False, cleanup_paths: List[str] = None):
        super().__init__()
        self.adb = adb_manager
        self.paths = paths
        self.is_split = is_split
        self.cleanup_paths = cleanup_paths or []
        
    def run(self):
        try:
            if not self.paths:
                self.finished.emit(False, "No files provided")
                return

            if self.is_split:
                # Install Multiple (Split APKs)
                self.progress.emit("Đang đẩy file lên thiết bị...")
                remote_paths = []
                for local_path in self.paths:
                    fname = os.path.basename(local_path)
                    remote = f"/data/local/tmp/{fname}"
                    self.adb.push_file(local_path, remote)
                    remote_paths.append(remote)
                
                self.progress.emit("Đang cài đặt (Split APKs)...")
                
                # Use 'install-multiple' directly via shell if possible, 
                # but 'pm install-create' session flow is more standard for split apks.
                
                # 1. Create Session
                session_out = self.adb.shell("pm install-create -r") 
                session_id = 0
                match = re.search(r'(\d+)', session_out)
                if match: 
                    session_id = match.group(1)
                else: 
                    # If regex fails, try to parse cleaner or just fail
                    raise Exception(f"Failed to create install session: {session_out}")
                
                # 2. Write APKs to session
                total = len(remote_paths)
                for i, remote in enumerate(remote_paths):
                    self.progress.emit(f"Writing apk {i+1}/{total}...")
                    # Get size from local file to be safe, or remote? Local is safer for match.
                    size = os.path.getsize(self.paths[i])
                    self.adb.shell(f"pm install-write -S {size} {session_id} {i}.apk {remote}")
                
                # 3. Commit
                self.progress.emit("Committing session...")
                res = self.adb.shell(f"pm install-commit {session_id}")
                
                # Cleanup Remote
                for remote in remote_paths:
                    self.adb.shell(f"rm {remote}")
                    
                if "Success" in res:
                    self.finished.emit(True, "Cài đặt thành công!")
                else:
                    self.finished.emit(False, f"Lỗi: {res}")
            
            else:
                # Single APK
                for path in self.paths:
                    self.progress.emit(f"Đang cài đặt {os.path.basename(path)}...")
                    res = self.adb.execute(f"install -r \"{path}\"")
                    
                    if "Success" in res:
                        continue
                    else:
                        self.finished.emit(False, f"Lỗi khi cài {os.path.basename(path)}: {res}")
                        return
                
                self.finished.emit(True, "Cài đặt thành công!")
                
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            # Cleanup Local Temp Files
            for path in self.cleanup_paths:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    elif os.path.isfile(path):
                        os.remove(path)
                except:
                    pass



class BackupThread(QThread):
    """Background thread for backing up apps"""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, adb_manager, apps: List[AppInfo], dest_folder: str, mode: str = "apk"):
        super().__init__()
        self.adb = adb_manager
        self.apps = apps
        self.dest_folder = dest_folder
        self.mode = mode # 'apk' or 'data'
        self._is_running = True
        
    def run(self):
        try:
            total = len(self.apps)
            success_count = 0
            
            if self.mode == "data":
                # ADB Backup Mode (.ab file)
                packages = [app.package for app in self.apps]
                pkg_str = " ".join(packages)
                timestamp = int(time.time())
                
                # Single backup file for all (or loop?)
                # 'adb backup' for multiple packages creates one .ab file
                backup_file = os.path.join(self.dest_folder, f"backup_{timestamp}.ab")
                
                self.progress.emit("⚠️ Đang chờ xác nhận TRÊN ĐIỆN THOẠI...\nVui lòng mở khóa và nhấn 'Back up my data'!")
                
                # Command: adb backup -apk -shared -all -f file.ab (for all)
                # For specific: adb backup -apk -shared -f file.ab pkg1 pkg2
                # Including -shared to try and get external data (images)
                
                cmd = f"backup -apk -shared -f \"{backup_file}\" {pkg_str}"
                res = self.adb.execute(cmd, timeout=300) # Long timeout for user interaction
                
                if "error" not in res.lower():
                    self.finished.emit(True, f"Đã gửi lệnh Backup Data!\nFile: {os.path.basename(backup_file)}\n\nLưu ý: Kiểm tra file .ab có dung lượng > 0KB không.")
                else:
                    self.finished.emit(False, f"Lỗi: {res}")
                return

            # APK Mode (Default)
            for i, app in enumerate(self.apps):
                if not self._is_running: break
                
                self.progress.emit(f"Đang sao lưu ({i+1}/{total}): {app.name}...")
                
                # Get paths
                out = self.adb.shell(f"pm path {app.package}")
                paths = []
                for line in out.splitlines():
                    if line.startswith("package:"):
                        paths.append(line.replace("package:", "").strip())
                
                if not paths:
                    continue # Skip if no path found
                
                if len(paths) == 1:
                    src = paths[0]
                    dst_name = f"{app.package}_{app.version_code}.apk" if app.version_code else f"{app.package}.apk"
                    dst = os.path.join(self.dest_folder, dst_name)
                    self.adb.pull_file(src, dst)
                else:
                    # Split APKs
                    save_dir = os.path.join(self.dest_folder, f"{app.package}_backup")
                    os.makedirs(save_dir, exist_ok=True)
                    
                    for src in paths:
                        fname = os.path.basename(src)
                        dst = os.path.join(save_dir, fname)
                        self.adb.pull_file(src, dst)
                        
                success_count += 1
            
            self.finished.emit(True, f"Đã sao lưu hoàn tất {success_count}/{total} ứng dụng!")
            
        except Exception as e:
            self.finished.emit(False, str(e))
            
    def stop(self):
        self._is_running = False


class AppScanner(QThread):
    """Background thread for scanning apps"""
    
    progress = Signal(int, int)  # current, total
    app_found = Signal(object)  # AppInfo
    finished = Signal(list)  # List[AppInfo]
    error = Signal(str)
    
    def __init__(self, adb_manager, app_type: str = "all"):
        super().__init__()
        self.adb = adb_manager
        self.app_type = app_type  # all, user, system
        self._is_running = True
    
    def run(self):
        """Scan for installed apps"""
        try:
            apps = []
            
            # 1. Fetch Disabled Packages List First (Fast)
            disabled_output = self.adb.shell("pm list packages -d")
            disabled_pkgs = set()
            for line in disabled_output.splitlines():
                # parsing: package:com.example.pkg
                if line.startswith("package:"):
                    disabled_pkgs.add(line.replace("package:", "").strip())
            
            # 2. Get package list based on type
            if self.app_type == "user":
                cmd = "pm list packages -3 -f"
            elif self.app_type == "system":
                cmd = "pm list packages -s -f"
            else:
                cmd = "pm list packages -f"
            
            output = self.adb.shell(cmd)
            lines = output.strip().split('\n')
            total = len(lines)
            
            for i, line in enumerate(lines):
                if not self._is_running:
                    break
                
                self.progress.emit(i + 1, total)
                
                try:
                    # Parse: package:/path/to/base.apk=com.example.app
                    match = re.match(r'package:(.+)=(.+)', line)
                    if not match:
                        continue
                    
                    path, package = match.groups()
                    
                    # Check if disabled
                    is_enabled = package not in disabled_pkgs
                    
                    # Get detailed app info (Simplified for speed in this implementation)
                    app_info = self._get_app_details_fast(package, path, is_enabled)
                    if app_info:
                        apps.append(app_info)
                        self.app_found.emit(app_info)
                
                except Exception as e:
                    continue
            
            self.finished.emit(apps)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def _get_app_details_fast(self, package: str, path: str, is_enabled: bool = True) -> Optional[AppInfo]:
        """Fast getter for list view"""
        # Heuristics for name
        name = package.split('.')[-1].title()
        is_system = '/system/' in path or '/vendor/' in path
        
        # Fetch Real Size and Date using valid path
        # Using ONE generic command to try to get info: 'stat -c "%s %Y" path'
        # To optimize, we might rely on cached lookup or batch, but for now individual query
        # per item is safer for correctness, though slower.
        # Speed optimization: Check if we have processed this pkg before? No state here.
        
        size = 0
        timestamp = 0
        
        try:
             # Fast stat
             # Check if path is valid on device (it comes from pm list)
             cmd = f"stat -c \"%s %Y\" {path}"
             out = self.adb.shell(cmd).strip()
             # output format: "123456 167890123" (Size Time)
             parts = out.split()
             if len(parts) >= 2:
                 size = int(parts[0])
                 timestamp = int(parts[1])
        except:
             pass

        return AppInfo(
            package=package,
            name=name,
            version="...",
            version_code=0,
            is_system=is_system,
            is_enabled=is_enabled,
            size=size,
            install_time=timestamp,
            update_time=timestamp,
            path=path
        )
    
    def stop(self):
        """Stop scanning"""
        self._is_running = False


class AppManagerWidget(QWidget):
    """
    Main App Manager Widget
    Displays list of apps with search, filter, and operations
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.apps: List[AppInfo] = []
        self.scanner = None
        self.install_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Parent has padding
        main_layout.setSpacing(20)
        
        # 1. Header & Toolbar Area
        header_container = QFrame()
        header_container.setObjectName("AppManagerHeader")
        header_container.setStyleSheet(f"""
            #AppManagerHeader {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.6);
            }}
        """)
        # Shadow
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(15)
        header_shadow.setColor(QColor(0, 0, 0, 10))
        header_shadow.setOffset(0, 4)
        header_container.setGraphicsEffect(header_shadow)
        
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title Row
        title_row = QHBoxLayout()
        icon_lbl = QLabel("📱")
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")
        title = QLabel("Quản Lý Ứng Dụng")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_PRIMARY}; background: transparent;")
        
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title)
        title_row.addStretch()
        
        self.count_label = QLabel("0 ứng dụng")
        self.count_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600; background: transparent;")
        title_row.addWidget(self.count_label)
        
        header_layout.addLayout(title_row)
        header_layout.addSpacing(15)
        
        # Controls Row
        controls_layout = QHBoxLayout()
        
        # Install Button
        self.btn_install = QPushButton("📥 Cài đặt / Phục hồi")
        self.btn_install.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.btn_install.clicked.connect(self.show_install_menu)
        controls_layout.addWidget(self.btn_install)
        
        # Input Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 10px;
                padding: 10px 15px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ThemeManager.COLOR_ACCENT};
                background: white;
            }}
        """)
        self.search_input.textChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.search_input, 1) # Stretch
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Tất cả", "Người dùng", "Hệ thống", "Đã bật", "Đã tắt"])
        self.type_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 10px;
                padding: 8px 15px;
                min-width: 120px;
            }}
        """)
        self.type_filter.currentIndexChanged.connect(self.on_type_filter_changed)
        controls_layout.addWidget(self.type_filter)
        
        # Refresh Btn
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setToolTip("Làm mới danh sách")
        refresh_btn.clicked.connect(lambda: self.refresh_apps(self.get_current_type_filter()))
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 10px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: white;
                border: 1px solid {ThemeManager.COLOR_ACCENT};
            }}
        """)
        controls_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(controls_layout)
        
        main_layout.addWidget(header_container)
        
        # 2. Table Area
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Tên ứng dụng", "Gói (Package)", "Kích thước", "Ngày cài", "Loại", "Trạng thái"])
        
        # Modern Table Style
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.6);
                outline: none;
                gridline-color: rgba(0,0,0,0.05);
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QTableWidget::item:selected {{
                background-color: rgba(126, 217, 87, 0.3); /* Green Tint for visibility */
                border: 1px solid {ThemeManager.COLOR_ACCENT};
                color: black;
            }}
            QHeaderView::section {{
                background-color: rgba(255, 255, 255, 0.5);
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                padding: 12px;
                border: none;
                border-bottom: 1px solid rgba(0,0,0,0.1);
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
            }}
            QTableWidget QTableCornerButton::section {{
                background: transparent;
                border: none;
            }}
        """)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setSortingEnabled(True)

# ... (StartLine Adjust needed for context match, splitting into chunks is safer)

        
        # Column Resizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        
        self.table.setColumnWidth(2, 80)  # Size
        self.table.setColumnWidth(3, 120) # Date
        self.table.setColumnWidth(4, 100) # Type
        self.table.setColumnWidth(5, 100) # Status
        
        # Connect selection change
        self.table.itemSelectionChanged.connect(self.update_action_bar)
        
        main_layout.addWidget(self.table)
        
        # 3. Floating Action Bar (Initially hidden or integrated at bottom)
        self.action_bar = QFrame()
        self.action_bar.setObjectName("ActionBar")
        self.action_bar.setStyleSheet(f"""
            #ActionBar {{
                background-color: white;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,0.1);
            }}
        """)
        action_layout = QHBoxLayout(self.action_bar)
        action_layout.setContentsMargins(20, 15, 20, 15)
        
        self.selected_label = QLabel("Đã chọn: 0")
        self.selected_label.setStyleSheet(f"font-weight: 600; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        action_layout.addWidget(self.selected_label)
        
        action_layout.addStretch()
        
        # Action Buttons
        self.btn_backup = QPushButton("💾 Sao lưu")
        self.btn_backup.setStyleSheet(ThemeManager.get_button_style("success"))
        self.btn_backup.clicked.connect(self.on_backup)
        action_layout.addWidget(self.btn_backup)

        self.btn_uninstall = QPushButton("🗑️ Gỡ cài đặt")
        self.btn_uninstall.setStyleSheet(ThemeManager.get_button_style("danger"))
        self.btn_uninstall.clicked.connect(self.on_uninstall)
        action_layout.addWidget(self.btn_uninstall)
        
        self.btn_disable = QPushButton("🚫 Tắt")
        self.btn_disable.setStyleSheet(ThemeManager.get_button_style("warning"))
        self.btn_disable.clicked.connect(self.on_disable)
        action_layout.addWidget(self.btn_disable)
        
        self.btn_enable = QPushButton("✅ Bật")
        self.btn_enable.setStyleSheet(ThemeManager.get_button_style("success"))
        self.btn_enable.clicked.connect(self.on_enable)
        action_layout.addWidget(self.btn_enable)
        
        self.btn_more = QPushButton("⚙️ Thêm")
        self.btn_more.setStyleSheet(ThemeManager.get_button_style("outline"))
        self.btn_more.clicked.connect(self.show_more_menu)
        action_layout.addWidget(self.btn_more)
        
        # Shadow for action bar
        bar_shadow = QGraphicsDropShadowEffect()
        bar_shadow.setBlurRadius(20)
        bar_shadow.setColor(QColor(0, 0, 0, 15))
        bar_shadow.setOffset(0, -5)
        self.action_bar.setGraphicsEffect(bar_shadow)
        
        main_layout.addWidget(self.action_bar)
        self.action_bar.hide() # Hide initially

    def get_current_type_filter(self):
        idx = self.type_filter.currentIndex()
        if idx == 1: return "user"
        if idx == 2: return "system"
        return "all"

    def on_type_filter_changed(self, index):
        # Apply filter locally without re-scanning
        self.apply_filters()
    
    def refresh_apps(self, app_type: str = "all"):
        """Refresh app list with scanner"""
        if not self.adb.current_device:
            return
        
        if self.scanner and self.scanner.isRunning():
            self.scanner.stop()
            self.scanner.wait()
        
        self.apps.clear()
        self.table.setRowCount(0)
        self.count_label.setText("Đang tải...")
        self.action_bar.hide()
        
        # ALWAYS scan "all" apps to cache them. Filtering is done client-side.
        self.scanner = AppScanner(self.adb, "all")
        self.scanner.app_found.connect(self.on_app_found)
        self.scanner.finished.connect(self.on_scan_finished)
        self.scanner.start()
    
    def on_app_found(self, app: AppInfo):
        """Handle individual app found"""
        self.apps.append(app)
        self.add_app_row(app)
        
    def add_app_row(self, app: AppInfo):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(app.name)
        if app.is_system:
             name_item.setData(Qt.ForegroundRole, QColor(ThemeManager.COLOR_WARNING))
        else:
             name_item.setData(Qt.ForegroundRole, QColor(ThemeManager.COLOR_TEXT_PRIMARY))
             
        # Use simple text icon for now
        name_item.setIcon(QIcon()) # Placeholder
        self.table.setItem(row, 0, name_item)
        
        # Package
        pkg_item = QTableWidgetItem(app.package)
        pkg_item.setData(Qt.ForegroundRole, QColor(ThemeManager.COLOR_TEXT_SECONDARY))
        self.table.setItem(row, 1, pkg_item)
        
        # Size
        size_str = self.format_size(app.size)
        size_item = QTableWidgetItem(size_str)
        size_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, size_item)
        
        # Date
        date_str = self.format_date(app.install_time)
        date_item = QTableWidgetItem(date_str)
        date_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, date_item)
        
        # Type
        type_str = "Hệ thống" if app.is_system else "Người dùng"
        type_item = QTableWidgetItem(type_str)
        type_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, type_item)
        
        # Status
        status_str = "✅ Bật" if app.is_enabled else "🚫 Tắt"
        status_item = QTableWidgetItem(status_str)
        status_item.setTextAlignment(Qt.AlignCenter)
        if not app.is_enabled:
             status_item.setData(Qt.ForegroundRole, QColor(ThemeManager.COLOR_DANGER))
        else:
             status_item.setData(Qt.ForegroundRole, QColor(ThemeManager.COLOR_SUCCESS))
        self.table.setItem(row, 5, status_item)
        
        # Store Data
        self.table.item(row, 0).setData(Qt.UserRole, app)
        
        # Update count live
        self.count_label.setText(f"{len(self.apps)} ứng dụng")

    def format_size(self, size_bytes: int) -> str:
        if not size_bytes: return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def format_date(self, timestamp: int) -> str:
        if not timestamp: return "-"
        from datetime import datetime
        try:
             dt = datetime.fromtimestamp(timestamp)
             return dt.strftime("%Y-%m-%d")
        except:
             return "-"

    def on_scan_finished(self, apps):
        self.apply_filters()
        self.count_label.setText(f"{len(self.apps)} ứng dụng")
    
    def apply_filters(self):
        try:
            search_text = self.remove_accents(self.search_input.text().lower().strip())
            filter_type = self.type_filter.currentText()
            
            hidden_count = 0
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if not item: continue
                app = item.data(Qt.UserRole)
                if not app: continue
                
                match = True
                
                # Type/State Filter
                if filter_type == "Đã bật" and not app.is_enabled:
                    match = False
                elif filter_type == "Đã tắt" and app.is_enabled:
                     match = False
                elif filter_type == "Người dùng" and app.is_system:
                     match = False
                elif filter_type == "Hệ thống" and not app.is_system:
                     match = False
                
                # Search Filter
                if match and search_text:
                    # Normalize app name too
                    name_norm = self.remove_accents(app.name.lower())
                    if search_text not in name_norm and search_text not in app.package.lower():
                        match = False
                
                self.table.setRowHidden(row, not match)
                if not match:
                    hidden_count += 1
                    
            visible = self.table.rowCount() - hidden_count
            self.count_label.setText(f"{visible} / {len(self.apps)} ứng dụng")
        except Exception as e:
            print(f"Search Error: {e}")

    def update_action_bar(self):
        selected = self.table.selectedItems()
        # Divide by columns to get rough row count
        rows = set(item.row() for item in selected)
        count = len(rows)
        
        if count > 0:
            self.action_bar.show()
            self.selected_label.setText(f"Đã chọn: {count}")
        else:
            self.action_bar.hide()
            
    def get_selected_apps(self) -> List[AppInfo]:
        apps = []
        rows = set(item.row() for item in self.table.selectedItems())
        for row in rows:
            apps.append(self.table.item(row, 0).data(Qt.UserRole))
        return apps

    def remove_accents(self, text: str) -> str:
        """Remove accents for search"""
        if not text: return ""
        return ''.join(c for c in unicodedata.normalize('NFD', text)
                      if unicodedata.category(c) != 'Mn')

    # --- Actions ---
    
    def show_install_menu(self):
        """Show install options menu"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_CARD']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 8px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {ThemeManager.COLOR_ACCENT};
                color: white;
            }}
        """)
        menu.addAction("📄 Cài đặt APK / APKS / XAPK / ZIP", self.install_file)
        menu.addAction("📂 Cài đặt từ Thư mục (Splits)", self.install_folder)
        menu.exec(QCursor.pos())

    def install_file(self):
        """Install single or multiple files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Chọn file cài đặt", 
            "", 
            "Android Apps (*.apk *.apks *.xapk *.zip)"
        )
        if not files: return
        
        # Process files
        self.process_install_files(files)

    def install_folder(self):
        """Install all apks from a folder (Split)"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa APKs")
        if not folder: return
        
        # Find all apks
        files = []
        for root, _, filenames in os.walk(folder):
            for filename in filenames:
                if filename.lower().endswith(".apk"):
                    files.append(os.path.join(root, filename))
        
        if not files:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file APK nào trong thư mục!")
            return
            
        # Treat as split install
        self.start_install_thread(files, is_split=True)

    def process_install_files(self, files: List[str]):
        """Analyze files and start install"""
        # If single file is .apks, .xapk or .zip -> Extract and install as split
        # If multiple .apk -> Assume split install or batch? 
        # Usually user selects multiple parts of a split to install together.
        
        is_split = False
        target_files = files
        cleanup_paths = []
        
        # Case 1: Single Archive
        if len(files) == 1:
            f = files[0].lower()
            if f.endswith(('.apks', '.xapk', '.zip')):
                # Extraction needed
                # Create temp dir
                temp_dir = tempfile.mkdtemp()
                cleanup_paths.append(temp_dir)
                
                try:
                    with zipfile.ZipFile(files[0], 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Find apks
                    extracted_apks = []
                    for root, _, filenames in os.walk(temp_dir):
                        for filename in filenames:
                            if filename.lower().endswith(".apk"):
                                extracted_apks.append(os.path.join(root, filename))
                    
                    if not extracted_apks:
                        QMessageBox.warning(self, "Lỗi", "Không tìm thấy APK trong file nén!")
                        shutil.rmtree(temp_dir)
                        return
                        
                    target_files = extracted_apks
                    is_split = True # Treat as split
                    
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Lỗi giải nén: {e}")
                    shutil.rmtree(temp_dir)
                    return
        
        elif len(files) > 1:
            # Multiple files selected. Assume split installation if they look like it.
            # Or asking user? For now assume split (install-multiple) as it's safer for split apks, 
            # and works for single apks too (mostly).
            is_split = True

        self.start_install_thread(target_files, is_split, cleanup_paths)

    def start_install_thread(self, files, is_split, cleanup_paths=None):
        self.progress = QProgressDialog("Đang chuẩn bị...", "Hủy", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()
        
        self.install_thread = InstallerThread(self.adb, files, is_split, cleanup_paths)
        self.install_thread.progress.connect(self.progress.setLabelText)
        self.install_thread.finished.connect(self.on_install_finished)
        self.install_thread.start()

    def on_install_finished(self, success, msg):
        self.progress.close()
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.refresh_apps("user") # Refresh list
        else:
            QMessageBox.critical(self, "Thất bại", msg)

    def on_backup(self):
        """Backup selected apps"""
        # 1. Force Refresh Device Check
        devices = self.adb.get_devices()
        connected_serials = [d[0] for d in devices if d[1] == DeviceStatus.ONLINE]
        
        if not self.adb.current_device or self.adb.current_device not in connected_serials:
            if len(connected_serials) == 1:
                self.adb.current_device = connected_serials[0]
            else:
                QMessageBox.warning(self, "Chưa kết nối", "Không tìm thấy thiết bị online! Vui lòng kiểm tra lại cáp USB.")
                return

        try:
            state = self.adb.execute(f"-s {self.adb.current_device} get-state").strip()
            if state != "device":
                 QMessageBox.critical(self, "Lỗi kết nối", f"Thiết bị '{self.adb.current_device}' không sẵn sàng (State: {state})!")
                 return
        except Exception:
             QMessageBox.critical(self, "Lỗi kết nối", "Mất kết nối với thiết bị!")
             return

        apps = self.get_selected_apps()
        if not apps:
            QMessageBox.warning(self, "Chưa chọn app", "Vui lòng chọn ít nhất 1 ứng dụng để sao lưu!")
            return
        
        # Choice Dialog
        box = QMessageBox(self)
        box.setWindowTitle("Chọn chế độ sao lưu")
        box.setText("Bạn muốn sao lưu gì?")
        box.setIcon(QMessageBox.Question)
        
        btn_apk = box.addButton("Chỉ file Cài đặt (APK)", QMessageBox.ActionRole)
        btn_data = box.addButton("Toàn bộ Dữ liệu (Full Data)", QMessageBox.ActionRole)
        btn_cancel = box.addButton("Hủy", QMessageBox.RejectRole)
        
        box.exec()
        
        clicked = box.clickedButton()
        if clicked == btn_cancel or clicked is None:
            return
            
        mode = "apk"
        if clicked == btn_data:
            mode = "data"
            QMessageBox.information(self, "Lưu ý Quan trọng", 
                "📱 Sắp tới, bạn CẦN MỞ KHÓA điện thoại và nhấn xác nhận 'Back up my data' trên màn hình!\n\n"
                "⚠️ Lưu ý: Tính năng này phụ thuộc vào ứng dụng có cho phép backup hay không."
            )
        
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu Backup")
        if not folder: return
        
        self.progress = QProgressDialog("Đang chuẩn bị...", "Hủy", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.show()
        
        self.backup_thread = BackupThread(self.adb, apps, folder, mode)
        self.backup_thread.progress.connect(self.progress.setLabelText)
        self.backup_thread.finished.connect(self.on_backup_finished)
        self.backup_thread.start()
        
    def on_backup_finished(self, success, msg):
        self.progress.close()
        if success:
            QMessageBox.information(self, "Thành công", msg)
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def on_uninstall(self):
        apps = self.get_selected_apps()
        if not apps: return
        
        msg = f"Bạn có chắc muốn gỡ bỏ {len(apps)} ứng dụng đã chọn?"
        if QMessageBox.question(self, "Xác nhận", msg) == QMessageBox.Yes:
            try:
                success_count = 0
                errors = []
                for app in apps:
                    try:
                        cmd = f"pm uninstall --user 0 {app.package}"
                        # Allow failure in shell execution to handle it manually if needed, 
                        # but ADBManager raises on non-zero. 
                        # We try/catch the raise.
                        res = self.adb.shell(cmd)
                        
                        # Check for output failure (Success/Failure is usually printed)
                        if "Failure" in res or "failure" in res:
                            # Clean up failure message
                            clean_res = res.replace("Failure", "").strip(" []")
                            errors.append(f"{app.name}: {clean_res if clean_res else res}")
                        elif "Success" in res or not res: 
                            # 'Success' or empty output (sometimes) -> considered success
                             success_count += 1
                        else:
                             # Some other output? assume success if no error code
                             success_count += 1

                    except Exception as e:
                        # Clean up error message
                        err_str = str(e)
                        # Remove the generic "ADB command failed: ..." prefix
                        if "ADB command failed:" in err_str:
                            # Try to extract the actual Error part
                            if "Error:" in err_str:
                                err_str = err_str.split("Error:", 1)[1].strip()
                        
                        # Removing command string if present in error (heuristic)
                        if "-s " in err_str and " shell " in err_str:
                             # It's likely dumping the command line
                             err_str = "Lỗi thực thi ADB (Permission/Not Installed)"

                        if not err_str:
                            err_str = "Lỗi không xác định"
                            
                        errors.append(f"{app.name}: {err_str}")
                
                if not errors:
                    QMessageBox.information(self, "Hoàn tất", f"Đã gỡ cài đặt {success_count} ứng dụng.")
                else:
                    err_msg = "\n".join(errors[:5])
                    if len(errors) > 5: err_msg += "\n..."
                    QMessageBox.warning(self, "Hoàn tất có lỗi", f"Đã gỡ {success_count} app.\nLỗi {len(errors)} app:\n\n{err_msg}")
                    
                self.refresh_apps(self.get_current_type_filter())
            except Exception as e:
                QMessageBox.critical(self, "Lỗi hệ thống", f"Không thể thực hiện tác vụ: {e}")

    def on_disable(self):
        apps = self.get_selected_apps()
        if not apps: return
        
        if QMessageBox.question(self, "Xác nhận", f"Tắt {len(apps)} ứng dụng?") == QMessageBox.Yes:
            success_count = 0
            errors = []
            for app in apps:
                try:
                    res = self.adb.shell(f"pm disable-user --user 0 {app.package}")
                    if "SecurityException" in res:
                        raise Exception("System Protected")
                    app.is_enabled = False # Update Local State
                    success_count += 1
                except Exception as e:
                    if "System Protected" in str(e) or "SecurityException" in str(e):
                         errors.append(f"{app.name}: Không thể tắt ứng dụng hệ thống bảo mật.")
                    else:
                         errors.append(f"{app.name}: {str(e)}")
            
            # Refresh Rows Visuals
            self.refresh_rows_state()
            
            if not errors:
                QMessageBox.information(self, "Hoàn tất", f"Đã tắt {success_count} ứng dụng.")
            else:
                err_msg = "\n".join(errors[:5])
                if len(errors) > 5: err_msg += "\n..."
                QMessageBox.warning(self, "Hoàn tất có lỗi", f"Đã tắt {success_count} app.\nLỗi {len(errors)} app:\n\n{err_msg}")

    def on_enable(self):
        apps = self.get_selected_apps()
        if not apps: return
        
        success_count = 0
        for app in apps:
            try:
                self.adb.shell(f"pm enable {app.package}")
                app.is_enabled = True # Update Local State
                success_count += 1
            except: pass
            
        # Refresh Rows Visuals
        self.refresh_rows_state()
        QMessageBox.information(self, "Hoàn tất", f"Đã bật {success_count} ứng dụng.")

    def refresh_rows_state(self):
        """Update Status Column for all rows based on AppInfo data"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            app = item.data(Qt.UserRole)
            
            # Update Status Column (index 3)
            status_str = "✅ Bật" if app.is_enabled else "🚫 Tắt"
            status_item = self.table.item(row, 3)
            status_item.setText(status_str)
            
            if not app.is_enabled:
                 status_item.setData(Qt.ForegroundRole, QColor(ThemeManager.COLOR_DANGER))
            else:
                 status_item.setData(Qt.ForegroundRole, QColor(ThemeManager.COLOR_SUCCESS))
                 
        # Re-apply filter if we are in Enabled/Disabled view
        self.apply_filters()

    def show_more_menu(self):
        menu = QMenu(self)
        menu.addAction("Buộc dừng (Force Stop)", self.on_force_stop)
        menu.addAction("Xóa dữ liệu (Clear Data)", self.on_clear_data)
        menu.exec(QCursor.pos())

    def on_force_stop(self):
        apps = self.get_selected_apps()
        for app in apps:
            self.adb.shell(f"am force-stop {app.package}")
        QMessageBox.information(self, "Info", f"Đã buộc dừng {len(apps)} ứng dụng.")

    def on_clear_data(self):
        apps = self.get_selected_apps()
        if QMessageBox.warning(self, "Cảnh báo", "Xóa dữ liệu sẽ làm mất thông tin ứng dụng!", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            for app in apps:
                self.adb.shell(f"pm clear {app.package}")
            QMessageBox.information(self, "Info", "Đã xóa dữ liệu.")
    
    def reset(self):
        """Reset and reload app list"""
        # Clear current list
        self.apps.clear()
        self.table.setRowCount(0)
        self.count_label.setText("Đang tải...")
        self.action_bar.hide()
        
        # Auto-load if device is connected
        if self.adb.current_device:
            self.refresh_apps(self.get_current_type_filter())

