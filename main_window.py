# src/main.py & src/ui/main_window.py
"""
ADB Manager Pro - Main Application Entry Point
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame, QStackedWidget,
    QMessageBox, QStatusBar, QMenuBar, QMenu, QDialog, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QIcon, QAction, QFont, QPalette, QColor


# Import core and UI modules
from adb_core_manager import ADBManager
# from ui.widgets.dashboard import DashboardWidget
# from ui.widgets.app_manager import AppManagerWidget
# from ui.widgets.xiaomi_optimizer import XiaomiOptimizerWidget


class Sidebar(QFrame):
    """Sidebar navigation widget"""
    
    page_changed = Signal(int)
    
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(220)
        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-right: 1px solid #3e3e42;
            }
        """)
        
        self.buttons = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup sidebar UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo/Title
        logo = QLabel("ADB Manager Pro")
        logo.setStyleSheet("""
            QLabel {
                background-color: #ff6b35;
                color: white;
                padding: 20px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        
        # Navigation buttons
        pages = [
            ("📊", "Dashboard", 0),
            ("📱", "Apps", 1),
            ("📦", "APK", 2),
            ("📁", "Files", 3),
            ("🖥️", "Screen", 4),
            ("🌐", "DNS", 5),
            ("🤖", "Xiaomi", 6),
            ("⚡", "Scripts", 7),
            ("📋", "Logcat", 8),
            ("💾", "ROM", 9),
            ("⚙️", "Settings", 10),
        ]
        
        for icon, text, index in pages:
            btn = self.create_nav_button(icon, text, index)
            self.buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Version info
        version = QLabel("v2.0.0")
        version.setStyleSheet("color: #858585; padding: 10px; font-size: 11px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
    
    def create_nav_button(self, icon: str, text: str, index: int) -> QPushButton:
        """Create navigation button"""
        btn = QPushButton(f"{icon}  {text}")
        btn.setCheckable(True)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #CCCCCC;
                border: none;
                padding: 15px 20px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2d2d30;
            }
            QPushButton:checked {
                background-color: #ff6b35;
                color: white;
                border-left: 3px solid white;
            }
        """)
        btn.clicked.connect(lambda: self.on_button_clicked(index))
        
        return btn
    
    def on_button_clicked(self, index: int):
        """Handle button click"""
        # Uncheck all buttons
        for btn in self.buttons:
            btn.setChecked(False)
        
        # Check clicked button
        self.buttons[index].setChecked(True)
        
        # Emit signal
        self.page_changed.emit(index)
    
    def set_active(self, index: int):
        """Set active page"""
        self.on_button_clicked(index)


class DeviceSelector(QWidget):
    """Device selection widget in toolbar"""
    
    device_changed = Signal(str)
    refresh_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Device label
        label = QLabel("Device:")
        label.setStyleSheet("color: #CCCCCC; font-weight: bold;")
        layout.addWidget(label)
        
        # Device selector
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        self.device_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d30;
                color: #CCCCCC;
                selection-background-color: #ff6b35;
            }
        """)
        self.device_combo.currentTextChanged.connect(self.device_changed)
        layout.addWidget(self.device_combo)
        
        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh devices")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self.refresh_clicked)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
            }
        """)
        layout.addWidget(refresh_btn)
        
        # Connect wireless button
        wireless_btn = QPushButton("📡 Wireless")
        wireless_btn.setToolTip("Connect wirelessly")
        wireless_btn.clicked.connect(self.on_wireless_connect)
        wireless_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A9EFF;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5AAFFF;
            }
        """)
        layout.addWidget(wireless_btn)
    
    def set_devices(self, devices: list):
        """Update device list"""
        self.device_combo.clear()
        for serial, status in devices:
            display = f"{serial} ({status.value})"
            self.device_combo.addItem(display, serial)
    
    def get_current_device(self) -> str:
        """Get currently selected device"""
        return self.device_combo.currentData()
    
    def on_wireless_connect(self):
        """Show wireless connection dialog"""
        from PySide6.QtWidgets import QInputDialog
        
        ip, ok = QInputDialog.getText(
            self, 
            "Wireless Connection",
            "Enter device IP address:"
        )
        
        if ok and ip:
            # Emit connect signal or handle directly
            QMessageBox.information(self, "Info", f"Connecting to {ip}...")


class AboutDialog(QDialog):
    """About dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About ADB Manager Pro")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Logo
        logo = QLabel("🤖 ADB Manager Pro")
        logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #ff6b35;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        
        # Version
        version = QLabel("Version 2.0.0")
        version.setStyleSheet("font-size: 14px; color: #858585;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        # Description
        desc = QLabel(
            "A comprehensive tool for managing Android devices via ADB.\n"
            "Optimized for Xiaomi devices with debloat and MIUI tweaks."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #CCCCCC; padding: 20px;")
        layout.addWidget(desc)
        
        # Credits
        credits = QTextEdit()
        credits.setReadOnly(True)
        credits.setHtml("""
            <p style='color: #CCCCCC;'>
            <b>Developed by:</b> Your Name<br>
            <b>License:</b> MIT License<br>
            <b>GitHub:</b> <a href='https://github.com/yourname/adb-manager'>github.com/yourname/adb-manager</a><br><br>
            
            <b>Built with:</b><br>
            • Python 3.11+<br>
            • PySide6 (Qt6)<br>
            • ADB Platform Tools<br>
            • Scrcpy for screen mirroring
            </p>
        """)
        credits.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d30;
                color: #CCCCCC;
                border: 1px solid #3e3e42;
                border-radius: 5px;
            }
        """)
        layout.addWidget(credits)
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b35;
                color: white;
                border: none;
                padding: 8px 30px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(ok_btn, alignment=Qt.AlignCenter)


class MainWindow(QMainWindow):
    """
    Main Application Window
    Contains sidebar navigation, content area, and device selector
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.current_device = None
        
        self.setWindowTitle("ADB Manager Pro")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setup_ui()
        self.apply_theme()
        self.setup_menu_bar()
        self.setup_status_bar()
        
        # Auto-refresh devices
        self.refresh_devices()
        
        # Setup timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # 5 seconds
    
    def setup_ui(self):
        """Setup main UI layout"""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.on_page_changed)
        main_layout.addWidget(self.sidebar)
        
        # Right side (toolbar + content)
        right_side = QWidget()
        right_layout = QVBoxLayout(right_side)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Toolbar
        toolbar = self.create_toolbar()
        right_layout.addWidget(toolbar)
        
        # Content area (stacked widget for pages)
        self.content_stack = QStackedWidget()
        right_layout.addWidget(self.content_stack)
        
        # Add pages (in production, import actual widgets)
        # For now, add placeholder widgets
        self.add_pages()
        
        main_layout.addWidget(right_side, 1)
        
        # Set initial page
        self.sidebar.set_active(0)
    
    def create_toolbar(self) -> QWidget:
        """Create top toolbar"""
        toolbar = QFrame()
        toolbar.setMaximumHeight(60)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-bottom: 1px solid #3e3e42;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        
        # Device selector
        self.device_selector = DeviceSelector()
        self.device_selector.device_changed.connect(self.on_device_changed)
        self.device_selector.refresh_clicked.connect(self.refresh_devices)
        layout.addWidget(self.device_selector)
        
        layout.addStretch()
        
        # Quick actions
        actions = [
            ("🔄", "Reboot", self.on_reboot),
            ("📸", "Screenshot", self.on_screenshot),
            ("🧹", "Clear Cache", self.on_clear_cache),
        ]
        
        for icon, tooltip, callback in actions:
            btn = QPushButton(icon)
            btn.setToolTip(tooltip)
            btn.setMaximumWidth(40)
            btn.clicked.connect(callback)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #252526;
                    color: #CCCCCC;
                    border: 1px solid #3e3e42;
                    padding: 5px;
                    border-radius: 5px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3e3e42;
                }
            """)
            layout.addWidget(btn)
        
        return toolbar
    
    def add_pages(self):
        """Add pages to content stack"""
        # In production, these would be actual widget imports
        # For now, create placeholder pages
        
        pages = [
            "Dashboard",
            "App Manager", 
            "APK Manager",
            "File Manager",
            "Screen Mirror",
            "DNS Config",
            "Xiaomi Optimizer",
            "Script Engine",
            "Logcat Viewer",
            "ROM Downloader",
            "Settings",
        ]
        
        for page_name in pages:
            # Create placeholder
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            
            label = QLabel(f"{page_name}\n\n(Widget implementation goes here)")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 18px; color: #858585;")
            layout.addWidget(label)
            
            # In production, replace with actual widgets:
            # if page_name == "Dashboard":
            #     widget = DashboardWidget(self.adb)
            # elif page_name == "App Manager":
            #     widget = AppManagerWidget(self.adb)
            # ...
            
            self.content_stack.addWidget(placeholder)
    
    def setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d30;
                color: #CCCCCC;
            }
            QMenuBar::item:selected {
                background-color: #ff6b35;
            }
            QMenu {
                background-color: #2d2d30;
                color: #CCCCCC;
            }
            QMenu::item:selected {
                background-color: #ff6b35;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        connect_action = QAction("Connect Device", self)
        connect_action.triggered.connect(self.refresh_devices)
        file_menu.addAction(connect_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        logcat_action = QAction("Open Logcat", self)
        tools_menu.addAction(logcat_action)
        
        shell_action = QAction("ADB Shell", self)
        tools_menu.addAction(shell_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        docs_action = QAction("Documentation", self)
        help_menu.addAction(docs_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        status = self.statusBar()
        status.setStyleSheet("""
            QStatusBar {
                background-color: #252526;
                color: #858585;
                border-top: 1px solid #3e3e42;
            }
        """)
        
        self.status_label = QLabel("Ready")
        status.addWidget(self.status_label)
        
        status.addPermanentWidget(QLabel("  |  "))
        
        self.device_status = QLabel("No device")
        status.addPermanentWidget(self.device_status)
    
    def apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #CCCCCC;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 14px;
            }
            QScrollBar:vertical {
                background-color: #252526;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
        """)
    
    def on_page_changed(self, index: int):
        """Handle page change"""
        self.content_stack.setCurrentIndex(index)
    
    def refresh_devices(self):
        """Refresh device list"""
        try:
            devices = self.adb.get_devices()
            self.device_selector.set_devices(devices)
            
            if devices:
                self.status_label.setText(f"Found {len(devices)} device(s)")
            else:
                self.status_label.setText("No devices found")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh devices: {str(e)}")
    
    def on_device_changed(self, serial: str):
        """Handle device selection change"""
        if serial:
            self.adb.select_device(serial)
            self.current_device = serial
            self.update_status()
    
    def update_status(self):
        """Update status bar"""
        if self.current_device:
            try:
                info = self.adb.get_device_info()
                self.device_status.setText(
                    f"Device: {info.model} | "
                    f"Android {info.android_version} | "
                    f"Battery: {info.battery_level}%"
                )
            except:
                self.device_status.setText("Device: Error")
        else:
            self.device_status.setText("No device selected")
    
    def show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()
    
    # Quick actions
    def on_reboot(self):
        """Quick reboot"""
        if not self.current_device:
            return
        
        reply = QMessageBox.question(
            self, "Confirm",
            "Reboot device?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.adb.reboot()
                QMessageBox.information(self, "Success", "Device is rebooting...")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def on_screenshot(self):
        """Quick screenshot"""
        from PySide6.QtWidgets import QFileDialog
        import datetime
        
        if not self.current_device:
            return
        
        default_name = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Screenshot',
            default_name,
            'PNG Images (*.png)'
        )
        
        if file_path:
            try:
                self.adb.screenshot(file_path)
                QMessageBox.information(self, "Success", "Screenshot saved")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def on_clear_cache(self):
        """Quick cache clear"""
        if not self.current_device:
            return
        
        try:
            self.adb.shell("pm trim-caches 1G")
            QMessageBox.information(self, "Success", "Cache cleared")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ==============================================
# MAIN ENTRY POINT
# ==============================================

def main():
    """Application entry point"""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("ADB Manager Pro")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("YourName")
    
    # Set dark palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, QColor(204, 204, 204))
    dark_palette.setColor(QPalette.Base, QColor(45, 45, 48))
    dark_palette.setColor(QPalette.AlternateBase, QColor(37, 37, 38))
    dark_palette.setColor(QPalette.Text, QColor(204, 204, 204))
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 48))
    dark_palette.setColor(QPalette.ButtonText, QColor(204, 204, 204))
    dark_palette.setColor(QPalette.Highlight, QColor(255, 107, 53))
    dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(dark_palette)
    
    try:
        # Initialize ADB Manager
        adb = ADBManager()
        
        # Create and show main window
        window = MainWindow(adb)
        window.show()
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"Application failed to start:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
