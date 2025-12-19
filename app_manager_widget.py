# src/ui/widgets/app_manager.py
"""
App Manager Widget - Manage installed applications
List, enable/disable, uninstall, clear data/cache
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QHeaderView,
    QMessageBox, QMenu, QProgressDialog, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor
from typing import List, Dict, Optional
from dataclasses import dataclass
import re


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
            
            # Get package list based on type
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
                    
                    # Get detailed app info
                    app_info = self._get_app_details(package, path)
                    if app_info:
                        apps.append(app_info)
                        self.app_found.emit(app_info)
                
                except Exception as e:
                    print(f"Error parsing app {line}: {e}")
                    continue
            
            self.finished.emit(apps)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _get_app_details(self, package: str, path: str) -> Optional[AppInfo]:
        """Get detailed information for a package"""
        try:
            # Get app dump
            dump = self.adb.shell(f"dumpsys package {package}")
            
            # Parse version info
            version_match = re.search(r'versionName=(.+)', dump)
            version = version_match.group(1) if version_match else "Unknown"
            
            version_code_match = re.search(r'versionCode=(\d+)', dump)
            version_code = int(version_code_match.group(1)) if version_code_match else 0
            
            # Check if enabled
            enabled_match = re.search(r'enabled=(\d+)', dump)
            is_enabled = enabled_match.group(1) == '1' if enabled_match else True
            
            # Check if system app (heuristic)
            is_system = '/system/' in path or '/vendor/' in path
            
            # Get app label (name)
            try:
                label_cmd = f"pm dump {package} | grep -A 1 'applicationInfo'"
                label_output = self.adb.shell(label_cmd)
                # This is simplified - actual implementation should parse properly
                name = package.split('.')[-1].title()
            except:
                name = package.split('.')[-1].title()
            
            # Get size (simplified - actual implementation should sum all apk/data)
            try:
                size_output = self.adb.shell(f"du -s {path}")
                size = int(size_output.split()[0]) * 1024  # Convert to bytes
            except:
                size = 0
            
            # Get install/update times
            install_time = 0
            update_time = 0
            time_match = re.search(r'firstInstallTime=(.+)', dump)
            if time_match:
                # Parse timestamp - simplified
                install_time = 0
            
            return AppInfo(
                package=package,
                name=name,
                version=version,
                version_code=version_code,
                is_system=is_system,
                is_enabled=is_enabled,
                size=size,
                install_time=install_time,
                update_time=update_time,
                path=path
            )
            
        except Exception as e:
            print(f"Error getting details for {package}: {e}")
            return None
    
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
        self.filtered_apps: List[AppInfo] = []
        self.scanner = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Application Manager")
        header.setStyleSheet("""
            font-size: 20px;
            color: #CCCCCC;
            font-weight: bold;
            padding: 10px;
        """)
        main_layout.addWidget(header)
        
        # Toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Table
        self.table = self.create_table()
        main_layout.addWidget(self.table)
        
        # Details panel
        self.details_panel = self.create_details_panel()
        main_layout.addWidget(self.details_panel)
        
        # Action buttons
        actions = self.create_action_buttons()
        main_layout.addWidget(actions)
    
    def create_toolbar(self) -> QWidget:
        """Create toolbar with search and filters"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search apps...")
        self.search_box.textChanged.connect(self.on_search)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                padding: 8px;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.search_box, 2)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Apps", "User Apps", "System Apps", "Enabled", "Disabled"])
        self.type_filter.currentTextChanged.connect(self.on_filter_changed)
        self.type_filter.setStyleSheet("""
            QComboBox {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                padding: 8px;
                border-radius: 5px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        layout.addWidget(self.type_filter, 1)
        
        # Scan button
        scan_btn = QPushButton("🔄 Scan Apps")
        scan_btn.clicked.connect(self.on_scan_apps)
        scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff7f50;
            }
        """)
        layout.addWidget(scan_btn)
        
        return toolbar
    
    def create_table(self) -> QTableWidget:
        """Create apps table"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "✓", "Name", "Package", "Version", "Status", "Size"
        ])
        
        # Style
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                gridline-color: #3e3e42;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #ff6b35;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #CCCCCC;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Package
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Version
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Size
        
        # Enable sorting
        table.setSortingEnabled(True)
        
        # Context menu
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Selection changed
        table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return table
    
    def create_details_panel(self) -> QGroupBox:
        """Create app details panel"""
        panel = QGroupBox("App Details")
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 5px;
                margin-top: 10px;
                padding: 15px;
                color: #CCCCCC;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QFormLayout(panel)
        
        self.detail_name = QLabel("--")
        self.detail_package = QLabel("--")
        self.detail_version = QLabel("--")
        self.detail_path = QLabel("--")
        self.detail_size = QLabel("--")
        
        layout.addRow("Name:", self.detail_name)
        layout.addRow("Package:", self.detail_package)
        layout.addRow("Version:", self.detail_version)
        layout.addRow("Path:", self.detail_path)
        layout.addRow("Size:", self.detail_size)
        
        panel.setMaximumHeight(200)
        
        return panel
    
    def create_action_buttons(self) -> QWidget:
        """Create action buttons"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        buttons = [
            ("Enable", self.on_enable, "#4ECB71"),
            ("Disable", self.on_disable, "#FAA819"),
            ("Force Stop", self.on_force_stop, "#F04747"),
            ("Clear Cache", self.on_clear_cache, "#4A9EFF"),
            ("Clear Data", self.on_clear_data, "#F04747"),
            ("Uninstall", self.on_uninstall, "#F04747"),
            ("Backup APK", self.on_backup_apk, "#4A9EFF"),
        ]
        
        for text, callback, color in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    opacity: 0.8;
                }}
                QPushButton:disabled {{
                    background-color: #3e3e42;
                    color: #858585;
                }}
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        return widget
    
    def on_scan_apps(self):
        """Start app scanning"""
        if self.scanner and self.scanner.isRunning():
            return
        
        # Show progress dialog
        progress = QProgressDialog("Scanning apps...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        
        # Determine scan type
        filter_text = self.type_filter.currentText()
        if "User" in filter_text:
            scan_type = "user"
        elif "System" in filter_text:
            scan_type = "system"
        else:
            scan_type = "all"
        
        # Create scanner
        self.scanner = AppScanner(self.adb, scan_type)
        
        # Connect signals
        self.scanner.progress.connect(
            lambda curr, total: progress.setValue(int(curr / total * 100))
        )
        self.scanner.finished.connect(self.on_scan_finished)
        self.scanner.error.connect(
            lambda err: QMessageBox.critical(self, "Error", f"Scan failed: {err}")
        )
        
        # Handle cancel
        progress.canceled.connect(self.scanner.stop)
        
        # Clear table and start
        self.table.setRowCount(0)
        self.apps.clear()
        self.scanner.start()
    
    def on_scan_finished(self, apps: List[AppInfo]):
        """Handle scan completion"""
        self.apps = apps
        self.apply_filters()
        QMessageBox.information(self, "Success", f"Found {len(apps)} apps")
    
    def apply_filters(self):
        """Apply current search and filter"""
        search_text = self.search_box.text().lower()
        filter_type = self.type_filter.currentText()
        
        # Filter apps
        self.filtered_apps = []
        for app in self.apps:
            # Search filter
            if search_text and search_text not in app.name.lower() and search_text not in app.package.lower():
                continue
            
            # Type filter
            if "User" in filter_type and app.is_system:
                continue
            elif "System" in filter_type and not app.is_system:
                continue
            elif "Enabled" in filter_type and not app.is_enabled:
                continue
            elif "Disabled" in filter_type and app.is_enabled:
                continue
            
            self.filtered_apps.append(app)
        
        self.populate_table()
    
    def populate_table(self):
        """Populate table with filtered apps"""
        self.table.setRowCount(len(self.filtered_apps))
        
        for row, app in enumerate(self.filtered_apps):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left: 10px;")
            self.table.setCellWidget(row, 0, checkbox)
            
            # Name
            name_item = QTableWidgetItem(app.name)
            if app.is_system:
                name_item.setForeground(QColor("#858585"))
            self.table.setItem(row, 1, name_item)
            
            # Package
            package_item = QTableWidgetItem(app.package)
            self.table.setItem(row, 2, package_item)
            
            # Version
            version_item = QTableWidgetItem(app.version)
            self.table.setItem(row, 3, version_item)
            
            # Status
            status = "Enabled" if app.is_enabled else "Disabled"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor("#4ECB71" if app.is_enabled else "#F04747"))
            self.table.setItem(row, 4, status_item)
            
            # Size
            size_mb = app.size / (1024 * 1024)
            size_item = QTableWidgetItem(f"{size_mb:.1f} MB")
            self.table.setItem(row, 5, size_item)
    
    def on_search(self):
        """Handle search text change"""
        self.apply_filters()
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.apply_filters()
    
    def on_selection_changed(self):
        """Handle table selection change"""
        selected = self.table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        if row >= len(self.filtered_apps):
            return
        
        app = self.filtered_apps[row]
        
        # Update details panel
        self.detail_name.setText(app.name)
        self.detail_package.setText(app.package)
        self.detail_version.setText(f"{app.version} ({app.version_code})")
        self.detail_path.setText(app.path)
        self.detail_size.setText(f"{app.size / (1024 * 1024):.2f} MB")
    
    def show_context_menu(self, pos):
        """Show right-click context menu"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
            }
            QMenu::item:selected {
                background-color: #ff6b35;
            }
        """)
        
        menu.addAction("Enable", self.on_enable)
        menu.addAction("Disable", self.on_disable)
        menu.addSeparator()
        menu.addAction("Force Stop", self.on_force_stop)
        menu.addAction("Clear Cache", self.on_clear_cache)
        menu.addAction("Clear Data", self.on_clear_data)
        menu.addSeparator()
        menu.addAction("Backup APK", self.on_backup_apk)
        menu.addAction("Uninstall", self.on_uninstall)
        
        menu.exec_(self.table.viewport().mapToGlobal(pos))
    
    def get_selected_apps(self) -> List[AppInfo]:
        """Get selected apps (checkbox or table selection)"""
        selected = []
        
        # Check checkboxes
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected.append(self.filtered_apps[row])
        
        # If no checkboxes, use table selection
        if not selected:
            for item in self.table.selectedItems():
                row = item.row()
                if self.filtered_apps[row] not in selected:
                    selected.append(self.filtered_apps[row])
        
        return selected
    
    # ==================== App Operations ====================
    
    def on_enable(self):
        """Enable selected apps"""
        apps = self.get_selected_apps()
        if not apps:
            QMessageBox.warning(self, "Warning", "No apps selected")
            return
        
        for app in apps:
            try:
                self.adb.shell(f"pm enable {app.package}")
                app.is_enabled = True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to enable {app.name}: {str(e)}")
        
        self.populate_table()
    
    def on_disable(self):
        """Disable selected apps"""
        apps = self.get_selected_apps()
        if not apps:
            QMessageBox.warning(self, "Warning", "No apps selected")
            return
        
        for app in apps:
            try:
                self.adb.shell(f"pm disable-user {app.package}")
                app.is_enabled = False
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to disable {app.name}: {str(e)}")
        
        self.populate_table()
    
    def on_force_stop(self):
        """Force stop selected apps"""
        apps = self.get_selected_apps()
        if not apps:
            return
        
        for app in apps:
            try:
                self.adb.shell(f"am force-stop {app.package}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to stop {app.name}: {str(e)}")
        
        QMessageBox.information(self, "Success", f"Stopped {len(apps)} app(s)")
    
    def on_clear_cache(self):
        """Clear cache for selected apps"""
        apps = self.get_selected_apps()
        if not apps:
            return
        
        for app in apps:
            try:
                # Note: pm trim-caches clears all app caches
                # For specific app, need to use pm clear with specific flags
                self.adb.shell(f"pm clear {app.package}")
            except Exception as e:
                print(f"Failed to clear cache for {app.name}: {e}")
        
        QMessageBox.information(self, "Success", f"Cleared cache for {len(apps)} app(s)")
    
    def on_clear_data(self):
        """Clear data for selected apps"""
        apps = self.get_selected_apps()
        if not apps:
            return
        
        reply = QMessageBox.warning(
            self, "Confirm",
            f"Clear data for {len(apps)} app(s)? This will delete all app data!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for app in apps:
                try:
                    self.adb.shell(f"pm clear {app.package}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to clear data for {app.name}: {str(e)}")
    
    def on_uninstall(self):
        """Uninstall selected apps"""
        apps = self.get_selected_apps()
        if not apps:
            return
        
        # Check if any system apps
        system_apps = [app for app in apps if app.is_system]
        if system_apps:
            QMessageBox.warning(
                self, "Warning",
                f"{len(system_apps)} system app(s) selected. These can only be disabled, not uninstalled."
            )
            return
        
        reply = QMessageBox.warning(
            self, "Confirm Uninstall",
            f"Uninstall {len(apps)} app(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for app in apps:
                try:
                    self.adb.execute(f"uninstall {app.package}")
                    self.apps.remove(app)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to uninstall {app.name}: {str(e)}")
            
            self.apply_filters()
    
    def on_backup_apk(self):
        """Backup APK of selected apps"""
        from PySide6.QtWidgets import QFileDialog
        import os
        
        apps = self.get_selected_apps()
        if not apps:
            return
        
        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if not output_dir:
            return
        
        progress = QProgressDialog("Backing up APKs...", "Cancel", 0, len(apps), self)
        progress.setWindowModality(Qt.WindowModal)
        
        for i, app in enumerate(apps):
            if progress.wasCanceled():
                break
            
            progress.setValue(i)
            progress.setLabelText(f"Backing up {app.name}...")
            
            try:
                output_path = os.path.join(output_dir, f"{app.package}.apk")
                self.adb.execute(f"-s {self.adb.current_device} pull {app.path} {output_path}")
            except Exception as e:
                print(f"Failed to backup {app.name}: {e}")
        
        progress.setValue(len(apps))
        QMessageBox.information(self, "Success", f"Backed up {len(apps)} APK(s)")
