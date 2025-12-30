# src/ui/widgets/dashboard.py
"""
Dashboard Widget - System Overview
Style: Modern Premium "Glass & Gradient" - Xiaomi Theme
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QScrollArea, QMenu, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QIcon, QAction, QCursor, QColor, QFont, QLinearGradient, QGradient, QPainter, QPen
from src.ui.theme_manager import ThemeManager
import datetime

class CircularProgress(QWidget):
    """Circular Progress Bar - Xiaomi Style"""
    def __init__(self, title, value, color, suffix="%", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        self.suffix = suffix
        self.setFixedSize(160, 160)
        
    def set_value(self, value):
        self.value = value
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions
        width = self.width()
        height = self.height()
        rect = QRectF(10, 10, width-20, height-20)
        
        # Draw Background Circle
        pen = QPen()
        pen.setWidth(10)
        pen.setColor(QColor(ThemeManager.get_theme()['COLOR_BORDER']))
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        
        # Draw Progress Arc
        pen.setColor(QColor(self.color))
        painter.setPen(pen)
        angle = int(-self.value * 3.6 * 16) # Negative for clockwise
        painter.drawArc(rect, 90 * 16, angle)
        
        # Draw Text
        painter.setPen(QColor(ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']))
        font = QFont(ThemeManager.FONT_FAMILY, 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{self.value}{self.suffix}")
        
        # Draw Title
        painter.setPen(QColor(ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']))
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        # Offset text slightly down
        text_rect = QRectF(rect)
        text_rect.adjust(0, 45, 0, 0)
        painter.drawText(text_rect, Qt.AlignCenter, self.title)

class StatCard(QFrame):
    """Modern Glass Card for Stats"""
    def __init__(self, title, value, icon, gradient_stops, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110) # Compact height
        
        # Style
        grad_str = f"qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {gradient_stops[0]}, stop:1 {gradient_stops[1]})"
        self.setStyleSheet(f"""
            QFrame {{
                background: {grad_str};
                border-radius: 20px;
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Header
        h_layout = QHBoxLayout()
        
        # Icon - load from file or use emoji fallback
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setAlignment(Qt.AlignCenter)
        import os
        if icon and os.path.isfile(icon):
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(icon)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pixmap)
            else:
                icon_lbl.setText("📌")
        else:
            icon_lbl.setText(icon if icon else "📌")
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        
        h_layout.addWidget(icon_lbl)
        h_layout.addSpacing(10)
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        layout.addStretch()
        
        # Value
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet("color: white; font-size: 20px; font-weight: 700; background: transparent; border: none;")
        self.value_lbl.setWordWrap(True)
        layout.addWidget(self.value_lbl)

    def update_value(self, value):
        self.value_lbl.setText(value)

class SpecItem(QFrame):
    """Modern Spec Item with Icon and Value"""
    def __init__(self, title, value, icon, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(70) # Allow expansion
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}40; /* Very light bg */
                border-radius: 12px;
                border: 1px solid transparent;
            }}
            QFrame:hover {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}80;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 15, 10)
        layout.setSpacing(15)
        
        # Icon Container - load from PNG file
        icon_container = QLabel()
        icon_container.setFixedSize(42, 42)
        icon_container.setAlignment(Qt.AlignCenter)
        
        # Load icon from file path
        import os
        if icon and os.path.isfile(icon):
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(icon)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_container.setPixmap(pixmap)
            else:
                icon_container.setText("📌")
        else:
            # Fallback to emoji if file not found
            icon_container.setText("📌")
        
        icon_container.setStyleSheet(f"""
            background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}60;
            border-radius: 12px;
            border: none;
            padding: 5px;
        """)
        layout.addWidget(icon_container)
        
        # Text Info
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 2, 0, 2)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; background: transparent; border: none;")
        text_layout.addWidget(title_lbl)
        
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']}; font-weight: 700; background: transparent; border: none;")
        self.value_lbl.setWordWrap(True)
        text_layout.addWidget(self.value_lbl)
        
        layout.addLayout(text_layout)
        layout.addStretch()

    def set_value(self, text):
        self.value_lbl.setText(text)

class DashboardWorker(QThread):
    """Background worker to fetch dashboard data"""
    data_ready = Signal(dict)
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self._stop_requested = False
        
    def run(self):
        try:
            if self._stop_requested or self.isInterruptionRequested():
                return
            info = self.adb.get_detailed_system_info()
            if not self._stop_requested and not self.isInterruptionRequested():
                self.data_ready.emit(info)
        except Exception as e:
            if not self._stop_requested:
                print(f"Error getting system info: {e}")
                self.data_ready.emit({})
    
    def stop(self):
        self._stop_requested = True
        self.requestInterruption()

class DashboardWidget(QWidget):
    """Main Dashboard - Modern Xiaomi Redesign"""
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
        # Worker and Timer
        self.worker = DashboardWorker(self.adb)
        self.worker.data_ready.connect(self.on_data_ready)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.setInterval(5000)  # Refresh every 5s

        # Clock Timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.setInterval(1000) # Every second
        
    def get_icon_path(self, icon_name):
        """Get path to icon file in resources/icons folder"""
        from pathlib import Path
        # dashboard.py is in src/ui/widgets, need to go up 3 levels to reach root
        # widgets -> ui -> src -> Xiaomi_ADB_Commander (root)
        base_path = Path(__file__).resolve().parent.parent.parent.parent / 'resources' / 'icons' / icon_name
        return str(base_path)
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(25)
        self.content_layout.setContentsMargins(0, 0, 0, 20)
        
        # 1. Hero Section (Xiaomi Style)
        self.setup_hero()
        
        # 2. Stats Grid
        self.setup_stats_grid()
        
        # 3. Detailed Info
        self.setup_details_section()
        
        self.content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Floating Action Button
        self.setup_fab()
        
    def setup_hero(self):
        """Xiaomi Style Hero Section"""
        hero = QFrame()
        hero.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 24px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
        """)
        # Shadow
        shadow = QGraphicsDropShadowEffect(hero)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 8)
        hero.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(35, 30, 35, 30)
        
        # Left: Device Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        # Brand Pill
        brand_pill = QLabel("  XIAOMI   ")
        brand_pill.setStyleSheet(f"background-color: #ff6700; color: white; border-radius: 6px; font-weight: bold; font-size: 11px; padding: 4px;")
        brand_pill.setFixedHeight(22)
        brand_pill.setFixedWidth(70)
        
        self.device_name_lbl = QLabel("My Xiaomi")
        self.device_name_lbl.setStyleSheet(f"font-size: 32px; font-weight: 800; color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']}; background: transparent; font-family: {ThemeManager.FONT_FAMILY}; border: none;")
        
        self.os_lbl = QLabel("HyperOS | Android 14")
        self.os_lbl.setStyleSheet(f"font-size: 18px; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-weight: 500; background: transparent; border: none;")
        
        # Clock (Small)
        self.time_lbl = QLabel("--:--")
        # Explicit background: transparent and adjusted color
        self.time_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-family: {ThemeManager.FONT_FAMILY_MONO}; margin-top: 10px; background: transparent; border: none;")
        
        info_layout.addWidget(brand_pill)
        info_layout.addWidget(self.device_name_lbl)
        info_layout.addWidget(self.os_lbl)
        info_layout.addWidget(self.time_lbl)
        info_layout.addStretch()
        
        layout.addLayout(info_layout, 50)
        
        # Right: Circles
        circles_layout = QHBoxLayout()
        circles_layout.setSpacing(30)
        
        self.batt_circle = CircularProgress("Pin", 0, "#34C759", "%")
        self.storage_circle = CircularProgress("Bộ nhớ", 0, "#FF9500", "%")
        
        circles_layout.addWidget(self.batt_circle)
        circles_layout.addWidget(self.storage_circle)
        
        layout.addLayout(circles_layout)
        
        self.content_layout.addWidget(hero)
        
    def setup_stats_grid(self):
        """2x2 Grid of Stat Cards"""
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # RAM Card (Cyan) - Shows Total Capacity
        self.card_ram = StatCard("RAM", "Checking...", self.get_icon_path("ram.png"), ["#4facfe", "#00f2fe"])
        grid.addWidget(self.card_ram, 0, 0)
        
        # CPU Card (Purple) - Shows Chipset
        self.card_cpu = StatCard("CPU", "Checking...", self.get_icon_path("cpu.png"), ["#a18cd1", "#fbc2eb"])
        grid.addWidget(self.card_cpu, 0, 1)
        
        # Android (Green)
        self.card_android = StatCard("Android", "Checking...", self.get_icon_path("android.png"), ["#43e97b", "#38f9d7"])
        grid.addWidget(self.card_android, 1, 0)
        
        # Security (Orange/Yellow - Xiaomi Vibe)
        self.card_os = StatCard("Bảo mật", "Checking...", self.get_icon_path("shield.png"), ["#fa709a", "#fee140"])
        grid.addWidget(self.card_os, 1, 1)
        
        self.content_layout.addLayout(grid)
        
    def setup_details_section(self):
        """Detail Section"""
        self.details_card = QFrame()
        self.details_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 20px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
        """)
        layout = QVBoxLayout(self.details_card)
        layout.setSpacing(10)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Title
        title = QLabel("Thông số kỹ thuật")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY}; margin-bottom: 5px; border: none;")
        layout.addWidget(title)
        
        # Rows
        self.rows = {}
        
        # Main Horizontal Layout for Columns
        h_layout = QHBoxLayout()
        h_layout.setSpacing(20)
        
        # --- LEFT COLUMN: HARDWARE ---
        hw_container = QFrame()
        hw_container.setStyleSheet("background: transparent; border: none;")
        hw_layout = QVBoxLayout(hw_container)
        hw_layout.setContentsMargins(0, 0, 0, 0)
        hw_layout.setSpacing(10)
        
        # Header
        hw_header = QLabel("PHẦN CỨNG")
        hw_header.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ThemeManager.COLOR_ACCENT}; letter-spacing: 1px; margin-bottom: 5px;")
        hw_layout.addWidget(hw_header)
        
        self.add_hardware_spec("Model", "model", self.get_icon_path("model.png"), hw_layout)
        self.add_hardware_spec("Codename", "device_name", self.get_icon_path("codename.png"), hw_layout)
        self.add_hardware_spec("Chipset", "soc_name", self.get_icon_path("chipset.png"), hw_layout)
        
        hw_layout.addStretch()
        h_layout.addWidget(hw_container)
        
        # Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet(f"color: {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};")
        h_layout.addWidget(line)
        
        # --- RIGHT COLUMN: SOFTWARE ---
        sw_container = QFrame()
        sw_container.setStyleSheet("background: transparent; border: none;")
        sw_layout = QVBoxLayout(sw_container)
        sw_layout.setContentsMargins(0, 0, 0, 0)
        sw_layout.setSpacing(10)
        
        # Header
        sw_header = QLabel("PHẦN MỀM")
        sw_header.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ThemeManager.COLOR_ACCENT}; letter-spacing: 1px; margin-bottom: 5px;")
        sw_layout.addWidget(sw_header)
        
        self.add_software_spec("Build ID", "build_id", self.get_icon_path("build_id.png"), sw_layout)
        self.add_software_spec("Security Patch", "security_patch", self.get_icon_path("security.png"), sw_layout)
        self.add_software_spec("Kernel", "kernel", self.get_icon_path("kernel.png"), sw_layout)
        
        sw_layout.addStretch()
        h_layout.addWidget(sw_container)
        
        layout.addLayout(h_layout)
        
        self.content_layout.addWidget(self.details_card)
        
    def add_hardware_spec(self, title, key, icon, layout):
        item = SpecItem(title, "Scanning...", icon)
        layout.addWidget(item)
        self.rows[key] = item

    def add_software_spec(self, title, key, icon, layout):
        item = SpecItem(title, "Scanning...", icon)
        layout.addWidget(item)
        self.rows[key] = item
        
    def setup_fab(self):
        """Power Menu FAB"""
        self.fab = QPushButton("⏻", self)
        
        self.fab.setFixedSize(64, 64)
        self.fab.setCursor(Qt.PointingHandCursor)
        self.fab.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #FF512F, stop:1 #DD2476);
                color: white;
                border-radius: 32px;
                font-size: 28px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #FF6E40, stop:1 #ff3d00);
                margin-top: -2px;
            }
            QPushButton:pressed {
                margin-top: 0px;
            }
        """)
        # Shadow for FAB
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(221, 36, 118, 100))
        shadow.setOffset(0, 8)
        self.fab.setGraphicsEffect(shadow)
        
        self.fab.clicked.connect(self.show_power_menu)
        self.fab.move(self.width() - 90, self.height() - 90)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fab.move(self.width() - 94, self.height() - 94)

    def show_power_menu(self):
        """Extended Power Menu"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: white;
                border-radius: 12px;
                padding: 8px;
                border: 1px solid #eee;
            }}
            QMenu::item {{
                padding: 12px 24px;
                border-radius: 8px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background-color: {ThemeManager.COLOR_ACCENT}15;
                color: {ThemeManager.COLOR_ACCENT};
            }}
            QMenu::separator {{
                height: 1px;
                background: #eee;
                margin: 4px 0;
            }}
        """)
        
        actions = [
            ("⏻ Tắt nguồn", "shutdown"),
            ("🔄 Khởi động lại", "normal"),
            ("separator", None),
            ("🛠️ System ➔ Recovery", "recovery"),
            ("⚡ System ➔ Bootloader", "bootloader"),
            ("separator", None),
            ("▶️ Fastboot ➔ System", "fastboot_system"),
            ("🛠️ Fastboot ➔ Recovery", "fastboot_recovery"),
            ("🚀 Fastboot ➔ FastbootD", "fastboot_fastbootd"),
            ("💀 Fastboot ➔ EDL", "fastboot_edl"),
        ]
        
        for text, mode in actions:
            if text == "separator":
                menu.addSeparator()
                continue
            
            action = QAction(text, self)
            
            # Map modes to adb methods
            if mode == "shutdown":
                action.triggered.connect(lambda: self.adb.shutdown())
            elif mode == "normal":
                action.triggered.connect(lambda: self.adb.reboot("normal"))
            elif mode == "recovery":
                action.triggered.connect(lambda: self.adb.reboot("recovery"))
            elif mode == "bootloader":
                action.triggered.connect(lambda: self.adb.reboot("bootloader"))
            elif mode == "fastboot_system":
                action.triggered.connect(lambda: self.adb.fastboot_reboot())
            elif mode == "fastboot_recovery":
                action.triggered.connect(lambda: self.adb.fastboot_reboot_recovery())
            elif mode == "fastboot_fastbootd":
                action.triggered.connect(lambda: self.adb.fastboot_reboot_fastbootd())
            elif mode == "fastboot_edl":
                action.triggered.connect(lambda: self.adb.fastboot_reboot_edl())
                
            menu.addAction(action)
            
        menu.exec(QCursor.pos())

    def start_updates(self):
        """Start auto-refresh updates"""
        self.refresh_data()
        self.update_timer.start()
        self.clock_timer.start()
        
    def stop_updates(self):
        """Stop updates and cleanup worker thread safely"""
        self.update_timer.stop()
        self.clock_timer.stop()
        if self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait(2000)

    def refresh_data(self):
        """Refresh dashboard data"""
        if not self.worker.isRunning():
            self.worker._stop_requested = False
            self.worker.start()
            
    def update_clock(self):
        now = datetime.datetime.now()
        self.time_lbl.setText(now.strftime("%H:%M:%S"))

    def on_data_ready(self, info):
        """Handle data from worker"""
        if not info:
            return
            
        try:
            # 1. Update Hero Section
            self.device_name_lbl.setText(info.get("model", "Device"))
            self.os_lbl.setText(info.get("os_version", "Android"))
            
            # Update Circles
            batt = info.get("battery_level", 0)
            self.batt_circle.set_value(batt)
            
            store_used_p = info.get("storage_percent", 0)
            self.storage_circle.set_value(store_used_p)
            self.storage_circle.title = f"Bộ nhớ ({info.get('storage_used', '0')} used)"
            
            # 2. Update Stats Grid
            # RAM: Just Total Capacity as requested
            ram_txt = f"{info.get('ram_total', '0GB')}"
            self.card_ram.update_value(ram_txt)
            
            self.card_android.update_value(info.get("android_version", "N/A"))
            self.card_os.update_value(info.get("security_patch", "N/A"))
            
            # CPU: Show Manufacturer/Branding + Model if possible
            soc_name = info.get("soc_name", "Unknown Processor")
            self.card_cpu.update_value(soc_name)
            
            # 3. Details
            if 'model' in self.rows:
                self.rows['model'].set_value(info.get('model', 'Unknown'))
            if 'device_name' in self.rows: # Codename
                friendly_name = info.get('device_friendly_name', info.get('device_name', 'Unknown'))
                codename = info.get('device_name', '').lower()
                # Show friendly name with codename in parentheses if different
                if friendly_name != codename and codename != friendly_name.lower():
                    display = f"{friendly_name}"
                else:
                    display = friendly_name
                self.rows['device_name'].set_value(display)
            if 'soc_name' in self.rows: # Chipset
                self.rows['soc_name'].set_value(soc_name if soc_name else info.get('board', 'Unknown'))
            
            if 'build_id' in self.rows:
                self.rows['build_id'].set_value(info.get('build_id', 'Unknown'))
            if 'security_patch' in self.rows:
                self.rows['security_patch'].set_value(info.get('security_patch', 'Unknown'))
            if 'kernel' in self.rows:
                self.rows['kernel'].set_value(info.get('kernel', 'Unknown'))
            
        except Exception as e:
            print(f"Error updating Dashboard: {e}")
