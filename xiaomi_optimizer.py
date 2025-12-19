# src/ui/widgets/xiaomi_optimizer.py
"""
Xiaomi Optimizer Widget - Debloat and optimize MIUI devices
Remove bloatware, apply tweaks, optimize battery and performance
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QCheckBox, QTextEdit,
    QProgressBar, QMessageBox, QTabWidget, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
from typing import List, Dict
import json


# Xiaomi Bloatware Database
XIAOMI_BLOATWARE = {
    "safe": [
        # Analytics & Telemetry
        ("com.miui.analytics", "MIUI Analytics", "Collects usage data"),
        ("com.miui.msa.global", "MSA/MACE", "Ad tracking service"),
        ("com.xiaomi.joyose", "Joyose Service", "Advertisement service"),
        
        # Xiaomi Services
        ("com.xiaomi.mipicks", "Mi Picks", "App recommendations"),
        ("com.xiaomi.payment", "Mi Payment", "Payment service"),
        ("com.mipay.wallet", "Mi Pay", "Wallet app"),
        ("com.mi.health", "Mi Health", "Health app"),
        ("com.xiaomi.miplay_client", "Mi Play", "Media sharing"),
        
        # Cloud & Sync
        ("com.miui.cloudservice", "Mi Cloud", "Cloud sync (if not used)"),
        ("com.miui.cloudbackup", "Cloud Backup", "Backup service"),
        ("com.xiaomi.midrop", "Mi Drop", "File sharing"),
        
        # System Apps (rarely used)
        ("com.android.browser", "Mi Browser", "Can use Chrome instead"),
        ("com.miui.video", "Mi Video", "Video player"),
        ("com.miui.player", "Mi Music", "Music player"),
        ("com.xiaomi.scanner", "Mi Scanner", "QR/barcode scanner"),
        ("com.miui.notes", "Notes", "If using other note app"),
        ("com.miui.compass", "Compass", "Rarely used"),
        ("com.miui.miuibugre port", "Bug Report", "System tool"),
        ("com.miui.screenrecorder", "Screen Recorder", "If not needed"),
        
        # Xiaomi Store & GetApps
        ("com.xiaomi.glgm", "Games", "Game center"),
        ("com.xiaomi.ab", "MAB", "Ad service"),
        ("com.xiaomi.market", "GetApps", "App store (use Play Store)"),
        
        # Misc
        ("com.miui.yellowpage", "Yellow Pages", "Phone directory"),
        ("com.xiaomi.mipet", "Mipet", "Unknown service"),
        ("com.miui.hybrid", "Quick Apps", "Mini programs"),
        ("com.miui.hybrid.accessory", "Quick Apps Accessory", "Mini programs support"),
    ],
    
    "caution": [
        # These may affect some features
        ("com.miui.gallery", "Gallery", "If prefer Google Photos"),
        ("com.android.calendar", "Calendar", "If using Google Calendar"),
        ("com.miui.weather2", "Weather", "If using other weather app"),
        ("com.miui.backup", "Local Backup", "May affect system backup"),
        ("com.xiaomi.account", "Mi Account", "Required for Mi Cloud, OTA"),
        ("com.xiaomi.finddevice", "Find Device", "Anti-theft feature"),
        ("com.miui.securitycenter", "Security", "May affect app permissions"),
    ],
    
    "critical": [
        # NEVER remove these
        ("com.android.settings", "Settings", "System settings"),
        ("com.android.systemui", "System UI", "User interface"),
        ("com.miui.home", "MIUI Launcher", "Home screen"),
        ("com.android.phone", "Phone", "Dialer"),
        ("com.android.mms", "Messages", "SMS/MMS"),
        ("com.android.contacts", "Contacts", "Contact management"),
        ("com.android.vending", "Play Store", "App store"),
    ]
}


# MIUI Tweaks
MIUI_TWEAKS = {
    "Performance": {
        "unlock_performance": {
            "name": "Unlock Performance",
            "description": "Disable MIUI power management restrictions",
            "commands": [
                "pm disable com.miui.powerkeeper",
                "settings put global force_fsg_nav_bar 1",
            ],
            "reversible": True
        },
        "reduce_animations": {
            "name": "Reduce Animations",
            "description": "Make UI feel faster by reducing animation scale",
            "commands": [
                "settings put global window_animation_scale 0.5",
                "settings put global transition_animation_scale 0.5",
                "settings put global animator_duration_scale 0.5",
            ],
            "reversible": True,
            "revert_commands": [
                "settings put global window_animation_scale 1.0",
                "settings put global transition_animation_scale 1.0",
                "settings put global animator_duration_scale 1.0",
            ]
        },
    },
    
    "Battery": {
        "aggressive_doze": {
            "name": "Aggressive Doze Mode",
            "description": "Force device into deep sleep when screen off",
            "commands": [
                "dumpsys deviceidle enable",
                "dumpsys deviceidle force-idle",
            ],
            "reversible": False
        },
        "optimize_apps": {
            "name": "Optimize All Apps",
            "description": "Re-compile apps for better performance",
            "commands": [
                "cmd package bg-dexopt-job",
            ],
            "reversible": False
        },
    },
    
    "Privacy": {
        "disable_analytics": {
            "name": "Disable Analytics",
            "description": "Turn off MIUI telemetry and analytics",
            "commands": [
                "pm disable com.miui.analytics",
                "settings put global msa_enabled 0",
            ],
            "reversible": True
        },
        "disable_ads": {
            "name": "Disable Ads",
            "description": "Disable MIUI system ads",
            "commands": [
                "pm disable com.xiaomi.joyose",
                'settings put secure ad_id ""',
            ],
            "reversible": True
        },
    },
    
    "UI": {
        "enable_gestures": {
            "name": "Enable Full-Screen Gestures",
            "description": "Use gestures instead of navigation buttons",
            "commands": [
                "settings put global force_fsg_nav_bar 1",
            ],
            "reversible": True
        },
        "dark_mode": {
            "name": "Force Dark Mode",
            "description": "Enable system-wide dark theme",
            "commands": [
                "cmd uimode night yes",
            ],
            "reversible": True,
            "revert_commands": [
                "cmd uimode night no",
            ]
        },
    }
}


class DebloatWorker(QThread):
    """Worker thread for debloating"""
    
    progress = Signal(int, int)  # current, total
    package_removed = Signal(str, bool, str)  # package, success, message
    finished = Signal(list)  # results
    
    def __init__(self, adb_manager, packages: List[str], action: str = "disable"):
        super().__init__()
        self.adb = adb_manager
        self.packages = packages
        self.action = action  # disable, uninstall, restore
    
    def run(self):
        """Execute debloat operations"""
        results = []
        total = len(self.packages)
        
        for i, package in enumerate(self.packages):
            self.progress.emit(i + 1, total)
            
            try:
                if self.action == "disable":
                    self.adb.shell(f"pm disable-user --user 0 {package}")
                    success = True
                    msg = "Disabled"
                elif self.action == "uninstall":
                    self.adb.shell(f"pm uninstall -k --user 0 {package}")
                    success = True
                    msg = "Uninstalled"
                elif self.action == "restore":
                    self.adb.shell(f"pm enable {package}")
                    self.adb.shell(f"cmd package install-existing {package}")
                    success = True
                    msg = "Restored"
                else:
                    success = False
                    msg = "Unknown action"
                
                results.append((package, success, msg))
                self.package_removed.emit(package, success, msg)
                
            except Exception as e:
                results.append((package, False, str(e)))
                self.package_removed.emit(package, False, str(e))
        
        self.finished.emit(results)


class XiaomiOptimizerWidget(QWidget):
    """
    Xiaomi Optimizer Widget
    Provides debloat and optimization tools specifically for Xiaomi devices
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.selected_packages = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🤖 Xiaomi Optimizer")
        header.setStyleSheet("""
            font-size: 20px;
            color: #CCCCCC;
            font-weight: bold;
            padding: 10px;
        """)
        main_layout.addWidget(header)
        
        # Device check
        self.device_info = QLabel("Device: Not detected")
        self.device_info.setStyleSheet("color: #858585; padding: 5px 10px;")
        main_layout.addWidget(self.device_info)
        
        # Warning
        warning = QLabel("⚠️ Warning: Always backup your data before debloating!")
        warning.setStyleSheet("""
            background-color: #FAA819;
            color: #1e1e1e;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        """)
        main_layout.addWidget(warning)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3e3e42;
                background-color: #2d2d30;
            }
            QTabBar::tab {
                background-color: #252526;
                color: #CCCCCC;
                padding: 10px 20px;
                border: 1px solid #3e3e42;
            }
            QTabBar::tab:selected {
                background-color: #ff6b35;
            }
        """)
        
        # Debloat tab
        debloat_tab = self.create_debloat_tab()
        tabs.addTab(debloat_tab, "📦 Debloat")
        
        # Tweaks tab
        tweaks_tab = self.create_tweaks_tab()
        tabs.addTab(tweaks_tab, "⚙️ Tweaks")
        
        # Backup tab
        backup_tab = self.create_backup_tab()
        tabs.addTab(backup_tab, "💾 Backup")
        
        main_layout.addWidget(tabs)
    
    def create_debloat_tab(self) -> QWidget:
        """Create debloat tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scan button
        scan_btn = QPushButton("🔍 Scan Bloatware")
        scan_btn.clicked.connect(self.on_scan_bloatware)
        scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff7f50;
            }
        """)
        layout.addWidget(scan_btn)
        
        # Lists
        lists_layout = QHBoxLayout()
        
        # Safe to remove
        safe_group = QGroupBox("✅ Safe to Remove")
        safe_group.setStyleSheet("""
            QGroupBox {
                color: #4ECB71;
                font-weight: bold;
                border: 1px solid #3e3e42;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
        """)
        safe_layout = QVBoxLayout(safe_group)
        
        self.safe_list = QListWidget()
        self.safe_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #4ECB71;
            }
        """)
        self.safe_list.setSelectionMode(QListWidget.MultiSelection)
        safe_layout.addWidget(self.safe_list)
        
        select_all_safe = QPushButton("Select All")
        select_all_safe.clicked.connect(lambda: self.safe_list.selectAll())
        safe_layout.addWidget(select_all_safe)
        
        lists_layout.addWidget(safe_group)
        
        # Caution
        caution_group = QGroupBox("⚠️ Remove with Caution")
        caution_group.setStyleSheet("""
            QGroupBox {
                color: #FAA819;
                font-weight: bold;
                border: 1px solid #3e3e42;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
            }
        """)
        caution_layout = QVBoxLayout(caution_group)
        
        self.caution_list = QListWidget()
        self.caution_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #FAA819;
            }
        """)
        self.caution_list.setSelectionMode(QListWidget.MultiSelection)
        caution_layout.addWidget(self.caution_list)
        
        lists_layout.addWidget(caution_group)
        
        layout.addLayout(lists_layout)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        disable_btn = QPushButton("🚫 Disable Selected")
        disable_btn.clicked.connect(self.on_disable_bloatware)
        disable_btn.setStyleSheet(self.get_action_button_style("#4A9EFF"))
        actions_layout.addWidget(disable_btn)
        
        uninstall_btn = QPushButton("🗑️ Uninstall Selected")
        uninstall_btn.clicked.connect(self.on_uninstall_bloatware)
        uninstall_btn.setStyleSheet(self.get_action_button_style("#F04747"))
        actions_layout.addWidget(uninstall_btn)
        
        restore_btn = QPushButton("♻️ Restore All")
        restore_btn.clicked.connect(self.on_restore_bloatware)
        restore_btn.setStyleSheet(self.get_action_button_style("#4ECB71"))
        actions_layout.addWidget(restore_btn)
        
        layout.addLayout(actions_layout)
        
        # Progress
        self.debloat_progress = QProgressBar()
        self.debloat_progress.setVisible(False)
        layout.addWidget(self.debloat_progress)
        
        # Log
        self.debloat_log = QTextEdit()
        self.debloat_log.setReadOnly(True)
        self.debloat_log.setMaximumHeight(150)
        self.debloat_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.debloat_log)
        
        return widget
    
    def create_tweaks_tab(self) -> QWidget:
        """Create MIUI tweaks tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Description
        desc = QLabel(
            "Apply optimizations and tweaks to improve MIUI performance, battery life, and privacy."
        )
        desc.setStyleSheet("color: #858585; padding: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Tweaks by category
        for category, tweaks in MIUI_TWEAKS.items():
            group = QGroupBox(f"{category} Optimizations")
            group.setStyleSheet("""
                QGroupBox {
                    color: #CCCCCC;
                    font-weight: bold;
                    border: 1px solid #3e3e42;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding: 15px;
                }
            """)
            group_layout = QVBoxLayout(group)
            
            for tweak_id, tweak in tweaks.items():
                # Tweak item
                tweak_widget = QWidget()
                tweak_layout = QHBoxLayout(tweak_widget)
                tweak_layout.setContentsMargins(0, 5, 0, 5)
                
                # Checkbox
                checkbox = QCheckBox(tweak['name'])
                checkbox.setStyleSheet("color: #CCCCCC;")
                checkbox.setProperty("tweak_id", tweak_id)
                checkbox.setProperty("category", category)
                tweak_layout.addWidget(checkbox)
                
                # Description
                desc_label = QLabel(tweak['description'])
                desc_label.setStyleSheet("color: #858585; font-size: 12px;")
                tweak_layout.addWidget(desc_label, 1)
                
                group_layout.addWidget(tweak_widget)
            
            layout.addWidget(group)
        
        # Apply button
        apply_btn = QPushButton("✅ Apply Selected Tweaks")
        apply_btn.clicked.connect(self.on_apply_tweaks)
        apply_btn.setStyleSheet(self.get_action_button_style("#ff6b35"))
        layout.addWidget(apply_btn)
        
        # Tweak log
        self.tweak_log = QTextEdit()
        self.tweak_log.setReadOnly(True)
        self.tweak_log.setMaximumHeight(150)
        self.tweak_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.tweak_log)
        
        layout.addStretch()
        
        return widget
    
    def create_backup_tab(self) -> QWidget:
        """Create backup/restore tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        desc = QLabel(
            "Backup and restore your debloat configuration. "
            "This allows you to revert changes if needed."
        )
        desc.setStyleSheet("color: #858585; padding: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Backup list
        self.backup_list = QListWidget()
        self.backup_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
            }
        """)
        layout.addWidget(self.backup_list)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton("💾 Create Backup")
        create_backup_btn.clicked.connect(self.on_create_backup)
        create_backup_btn.setStyleSheet(self.get_action_button_style("#4A9EFF"))
        actions_layout.addWidget(create_backup_btn)
        
        restore_backup_btn = QPushButton("♻️ Restore Backup")
        restore_backup_btn.clicked.connect(self.on_restore_backup)
        restore_backup_btn.setStyleSheet(self.get_action_button_style("#4ECB71"))
        actions_layout.addWidget(restore_backup_btn)
        
        delete_backup_btn = QPushButton("🗑️ Delete Backup")
        delete_backup_btn.clicked.connect(self.on_delete_backup)
        delete_backup_btn.setStyleSheet(self.get_action_button_style("#F04747"))
        actions_layout.addWidget(delete_backup_btn)
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        return widget
    
    def get_action_button_style(self, color: str) -> str:
        """Get styled button CSS"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
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
        """
    
    def check_device(self) -> bool:
        """Check if connected device is Xiaomi"""
        try:
            info = self.adb.get_device_info()
            if info.manufacturer.lower() == "xiaomi":
                self.device_info.setText(f"Device: {info.model} (Xiaomi)")
                self.device_info.setStyleSheet("color: #4ECB71; padding: 5px 10px;")
                return True
            else:
                self.device_info.setText(f"Device: {info.model} (Not Xiaomi)")
                self.device_info.setStyleSheet("color: #FAA819; padding: 5px 10px;")
                return False
        except:
            self.device_info.setText("Device: Not connected")
            self.device_info.setStyleSheet("color: #F04747; padding: 5px 10px;")
            return False
    
    def on_scan_bloatware(self):
        """Scan for installed bloatware"""
        if not self.check_device():
            QMessageBox.warning(self, "Warning", "Please connect a Xiaomi device first")
            return
        
        # Get installed packages
        try:
            output = self.adb.shell("pm list packages")
            installed = set()
            for line in output.split('\n'):
                if line.startswith('package:'):
                    pkg = line.replace('package:', '').strip()
                    installed.add(pkg)
            
            # Clear lists
            self.safe_list.clear()
            self.caution_list.clear()
            
            # Populate safe list
            for pkg, name, desc in XIAOMI_BLOATWARE['safe']:
                if pkg in installed:
                    item = QListWidgetItem(f"{name}\n{pkg}\n{desc}")
                    item.setData(Qt.UserRole, pkg)
                    item.setToolTip(desc)
                    self.safe_list.addItem(item)
            
            # Populate caution list
            for pkg, name, desc in XIAOMI_BLOATWARE['caution']:
                if pkg in installed:
                    item = QListWidgetItem(f"{name}\n{pkg}\n{desc}")
                    item.setData(Qt.UserRole, pkg)
                    item.setToolTip(desc)
                    self.caution_list.addItem(item)
            
            self.log_debloat(
                f"Scan complete: Found {self.safe_list.count()} safe + "
                f"{self.caution_list.count()} caution bloatware"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Scan failed: {str(e)}")
    
    def on_disable_bloatware(self):
        """Disable selected bloatware"""
        self.execute_debloat_action("disable")
    
    def on_uninstall_bloatware(self):
        """Uninstall selected bloatware"""
        reply = QMessageBox.warning(
            self, "Confirm Uninstall",
            "Uninstalling system apps is risky. Disable is recommended instead. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.execute_debloat_action("uninstall")
    
    def on_restore_bloatware(self):
        """Restore all bloatware"""
        reply = QMessageBox.question(
            self, "Confirm Restore",
            "This will restore all disabled/uninstalled bloatware. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            all_packages = [pkg for pkg, _, _ in XIAOMI_BLOATWARE['safe'] + XIAOMI_BLOATWARE['caution']]
            self.execute_debloat_worker(all_packages, "restore")
    
    def execute_debloat_action(self, action: str):
        """Execute debloat action on selected packages"""
        packages = []
        
        # Get selected from both lists
        for item in self.safe_list.selectedItems():
            packages.append(item.data(Qt.UserRole))
        
        for item in self.caution_list.selectedItems():
            packages.append(item.data(Qt.UserRole))
        
        if not packages:
            QMessageBox.warning(self, "Warning", "No packages selected")
            return
        
        self.execute_debloat_worker(packages, action)
    
    def execute_debloat_worker(self, packages: List[str], action: str):
        """Execute debloat in worker thread"""
        self.debloat_progress.setVisible(True)
        self.debloat_progress.setMaximum(len(packages))
        self.debloat_progress.setValue(0)
        
        self.log_debloat(f"Starting {action} for {len(packages)} package(s)...")
        
        worker = DebloatWorker(self.adb, packages, action)
        worker.progress.connect(lambda c, t: self.debloat_progress.setValue(c))
        worker.package_removed.connect(self.on_package_processed)
        worker.finished.connect(self.on_debloat_finished)
        worker.start()
    
    def on_package_processed(self, package: str, success: bool, message: str):
        """Handle package processing result"""
        status = "✅" if success else "❌"
        self.log_debloat(f"{status} {package}: {message}")
    
    def on_debloat_finished(self, results: List):
        """Handle debloat completion"""
        success_count = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        self.log_debloat(f"\nComplete: {success_count}/{total} successful")
        self.debloat_progress.setVisible(False)
        
        QMessageBox.information(
            self, "Complete",
            f"Processed {total} package(s)\n{success_count} successful"
        )
    
    def log_debloat(self, message: str):
        """Add message to debloat log"""
        self.debloat_log.append(message)
    
    def on_apply_tweaks(self):
        """Apply selected MIUI tweaks"""
        # Find all checked tweaks
        tweaks_to_apply = []
        
        for category, tweaks in MIUI_TWEAKS.items():
            for tweak_id, tweak_data in tweaks.items():
                # Find checkbox (needs proper widget tracking in production)
                # For now, simplified implementation
                pass
        
        # Execute tweak commands
        # Implementation similar to debloat worker
        self.tweak_log.append("Feature under development")
    
    def on_create_backup(self):
        """Create backup of current state"""
        # Implementation: Save disabled/removed packages to JSON
        self.backup_list.addItem(f"Backup {QDateTime.currentDateTime().toString()}")
    
    def on_restore_backup(self):
        """Restore from backup"""
        selected = self.backup_list.currentItem()
        if selected:
            QMessageBox.information(self, "Info", "Feature under development")
    
    def on_delete_backup(self):
        """Delete selected backup"""
        selected = self.backup_list.currentItem()
        if selected:
            self.backup_list.takeItem(self.backup_list.row(selected))
