# src/ui/widgets/dashboard.py
"""
Dashboard Widget - System Overview
Style: Modern Premium "Glass & Gradient" - Xiaomi Theme
Optimized: Performance improvements with caching and throttling
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QScrollArea, QMenu, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QIcon, QAction, QCursor, QColor, QFont, QLinearGradient, QGradient, QPainter, QPen
from src.ui.theme_manager import ThemeManager
from src.ui.performance_utils import worker_pool, data_cache, throttle
import datetime


class StatCard(QFrame):
    """Modern Glass Card for Stats - Redesigned"""
    def __init__(self, title, value, icon, gradient_stops, parent=None):
        super().__init__(parent)
        self.setFixedHeight(130) # Increased height
        
        # Style
        self.setObjectName("StatCard")
        grad_str = f"qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {gradient_stops[0]}, stop:1 {gradient_stops[1]})"
        self.setStyleSheet(f"""
            #StatCard {{
                background: {grad_str};
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30)) # Slightly darker shadow
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        
        # Row 1: Icon + Title
        h_layout = QHBoxLayout()
        h_layout.setSpacing(15)
        
        # Icon Container (Glass bubble)
        icon_bg = QLabel()
        icon_bg.setFixedSize(48, 48)
        icon_bg.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); border-radius: 14px; border: none;")
        icon_bg.setAlignment(Qt.AlignCenter)
        
        icon_lbl = QLabel(icon_bg)
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        import os
        if icon and os.path.isfile(icon):
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(icon)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pixmap)
            else:
                icon_lbl.setText("📌")
        else:
            icon_lbl.setText(icon if icon else "📌")
            
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: rgba(255,255,255,0.9); font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; background: transparent; border: none;")
        
        h_layout.addWidget(icon_bg)
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        layout.addStretch()
        
        # Value (Big & Bold)
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet("color: white; font-size: 32px; font-weight: 800; background: transparent; border: none;")
        self.value_lbl.setWordWrap(True)
        layout.addWidget(self.value_lbl, alignment=Qt.AlignRight | Qt.AlignBottom)

    def update_value(self, value):
        self.value_lbl.setText(value)

class SpecItem(QFrame):
    """Modern Spec Item with Icon and Value"""
    def __init__(self, title, value, icon, parent=None):
        super().__init__(parent)
        self.setObjectName("SpecItem")
        self.setMinimumHeight(70) # Allow expansion
        self.setStyleSheet(f"""
            #SpecItem {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}40; /* Very light bg */
                border-radius: 12px;
                border: 1px solid transparent;
            }}
            #SpecItem:hover {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}80;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
            QLabel {{
                border: none;
                background: transparent;
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
        print(f"Worker: Starting system info check for {self.adb.current_device}...")
        try:
            if self._stop_requested or self.isInterruptionRequested():
                print("Worker: Stop requested.")
                return
            
            # Start fetch
            info = self.adb.get_detailed_system_info()
            print(f"Worker: Info fetched. Keys: {list(info.keys()) if info else 'None'}")
            
            if not self._stop_requested and not self.isInterruptionRequested():
                self.data_ready.emit(info)
            else:
                print("Worker: Interrupted after fetch.")
        except Exception as e:
            if not self._stop_requested:
                print(f"Worker Error: {e}")
                import traceback
                traceback.print_exc()
                self.data_ready.emit({})
    
    def stop(self):
        self._stop_requested = True
        self.requestInterruption()

class DashboardWidget(QWidget):
    """Main Dashboard - Modern Xiaomi Redesign (Performance Optimized)"""
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        print("Dashboard: Initializing UI (Performance Mode)...")
        self.setup_ui()
        
        # Worker - sử dụng từ pool để tái sử dụng
        self.worker = DashboardWorker(self.adb)
        self.worker.data_ready.connect(self._on_data_ready_throttled)
        self._last_update_data = None  # Cache last data
        
        # Optimized: Tăng interval từ 5s lên 10s để giảm CPU usage
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.setInterval(10000)  # Refresh every 10s (was 5s)

        # Optimized: Clock timer with throttle
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock_throttled)
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
        """Xiaomi Style Hero Section - Modern Revamp (Fixed)"""
        self.hero = QFrame()
        self.hero.setFixedHeight(220)
        self.hero.setObjectName("HeroFrame")
        # Force Dark Premium Look regardless of app theme to match S23 Ultra reference
        self.hero.setStyleSheet(f"""
            #HeroFrame {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #141e30, stop:1 #243b55);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        # Shadow
        shadow = QGraphicsDropShadowEffect(self.hero)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80)) 
        shadow.setOffset(0, 10)
        self.hero.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self.hero)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)
        
        # --- COL 1: Device Image ---
        img_container = QLabel()
        img_container.setFixedSize(110, 160)
        # Removed border, added subtle glow/bg
        img_container.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
        """)
        img_container.setAlignment(Qt.AlignCenter)
        img_label = QLabel("📱")
        img_label.setStyleSheet("font-size: 60px; background: transparent; border: none;") # Increased size
        img_layout = QVBoxLayout(img_container)
        img_layout.addWidget(img_label)
        img_layout.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(img_container)
        
        # --- COL 2: Info Section ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        info_layout.setAlignment(Qt.AlignVCenter) # Center vertically
        
        # Title and Clock Row
        title_row = QHBoxLayout()
        self.device_name_lbl = QLabel("Checking Device...")
        self.device_name_lbl.setStyleSheet(f"font-size: 30px; font-weight: 800; color: white; background: transparent; border: none; letter-spacing: 0.5px;")
        
        self.time_lbl = QLabel("--:--:--")
        self.time_lbl.setStyleSheet("font-size: 16px; color: rgba(255, 255, 255, 0.4); font-weight: 600; font-family: 'Consolas', monospace;")
        
        title_row.addWidget(self.device_name_lbl)
        title_row.addStretch()
        title_row.addWidget(self.time_lbl)
        info_layout.addLayout(title_row)
        
        # Specs Row (Chip, Storage, Battery)
        specs_row = QHBoxLayout()
        specs_row.setSpacing(20)
        
        self.chip_lbl = self.create_hero_spec("chipset.png", "CPU")
        self.storage_lbl = self.create_hero_spec("files.png", "Storage") 
        self.batt_lbl = self.create_hero_spec("notification.png", "Battery") # Fallback
        
        specs_row.addWidget(self.chip_lbl)
        specs_row.addWidget(self.storage_lbl)
        specs_row.addWidget(self.batt_lbl)
        specs_row.addStretch()
        info_layout.addLayout(specs_row)
        
        # Badges Row
        badges_row = QHBoxLayout()
        badges_row.setSpacing(12)
        badges_row.setContentsMargins(0, 5, 0, 0)
        
        self.auth_badge = QLabel(" Unauthorized ")
        self.auth_badge.setStyleSheet("background-color: rgba(255, 71, 87, 0.2); color: #ff6b81; border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 12px; border: 1px solid rgba(255, 71, 87, 0.4);")
        
        self.android_badge = QLabel(" Android -- ")
        self.android_badge.setStyleSheet("background-color: rgba(46, 134, 222, 0.2); color: #54a0ff; border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 12px; border: 1px solid rgba(46, 134, 222, 0.4);")
        
        badges_row.addWidget(self.auth_badge)
        badges_row.addWidget(self.android_badge)
        badges_row.addStretch()
        info_layout.addLayout(badges_row)
        
        layout.addLayout(info_layout, stretch=60)
        
        # --- COL 3: Actions ---
        action_layout = QVBoxLayout()
        action_layout.setSpacing(15)
        action_layout.setAlignment(Qt.AlignVCenter)
        
        # Mirror Button (Blue Gradient)
        btn_mirror = QPushButton(" Mirror Screen")
        btn_mirror.setIcon(QIcon(self.get_icon_path("mirror.png")))
        btn_mirror.setCursor(Qt.PointingHandCursor)
        btn_mirror.setFixedHeight(50)
        btn_mirror.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2980b9, stop:1 #6dd5fa);
                color: white;
                border-radius: 12px;
                font-weight: 700;
                font-size: 13px;
                padding: 0 20px;
                border: none;
                text-align: left;
            }}
            QPushButton:hover {{ 
                 background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #3498db, stop:1 #87e0fd);
            }}
        """)
        btn_mirror.clicked.connect(self.launch_scrcpy) 
        
        # WiFi Connect (Glass)
        btn_wifi = QPushButton(" Connect via Wi-Fi")
        btn_wifi.setIcon(QIcon(self.get_icon_path("cloud.png")))
        btn_wifi.setCursor(Qt.PointingHandCursor)
        btn_wifi.setFixedHeight(50)
        btn_wifi.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                font-weight: 600;
                font-size: 13px;
                padding: 0 20px;
                border: 1px solid rgba(255, 255, 255, 0.15);
                text-align: left;
            }}
            QPushButton:hover {{ 
                background-color: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)
        btn_wifi.clicked.connect(self.switch_to_wireless_debug)
        
        action_layout.addWidget(btn_mirror)
        action_layout.addWidget(btn_wifi)
        
        layout.addLayout(action_layout, stretch=25)
        
        self.content_layout.addWidget(self.hero)

    def create_hero_spec(self, icon_name, placeholder):
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
            }}
        """)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 5, 10, 5)
        layout.setSpacing(8)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setAlignment(Qt.AlignCenter)
        
        import os
        icon_path = self.get_icon_path(icon_name)
        if os.path.isfile(icon_path):
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pixmap)
        
        layout.addWidget(icon_lbl)
        
        # Text
        label = QLabel(placeholder)
        label.setStyleSheet(f"color: rgba(255, 255, 255, 0.9); font-size: 12px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(label)
        
        def set_text(text):
            label.setText(text)
        container.setText = set_text
        
        return container

    def launch_scrcpy(self):
        """Helper to find and launch scrcpy"""
        if not self.adb.current_device:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn hoặc kết nối thiết bị trước khi sử dụng Mirror Screen.")
            return

        import shutil
        import os
        scrcpy_path = shutil.which("scrcpy")
        
        # Check bundled locations
        if not scrcpy_path:
            local_paths = [
                os.path.join(os.getcwd(), "resources", "scrcpy", "scrcpy.exe"),
                os.path.join(os.getcwd(), "scripts", "scrcpy.exe"),
                os.path.join(os.getcwd(), "scrcpy", "scrcpy.exe")
            ]
            for p in local_paths:
                if os.path.exists(p):
                    scrcpy_path = p
                    break
                    
        if not scrcpy_path:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy scrcpy.exe. Vui lòng cài đặt scrcpy hoặc sao chép vào thư mục resources/scrcpy/")
            return

        # Simple launch
        import subprocess
        try:
            # CREATE_NO_WINDOW (0x08000000) might hide errors, 
            # but we usually want it to avoid cmd popup.
            cmd = [scrcpy_path, "-s", self.adb.current_device, "--no-audio"]
            subprocess.Popen(cmd, creationflags=0x08000000) 
            self.window().statusBar().showMessage("✓ Đang khởi chạy Mirror Screen...", 3000)
        except Exception as e:
            print(f"Failed to launch scrcpy: {e}")

    def switch_to_wireless_debug(self):
        """Find main window and switch to wireless debug tab"""
        parent = self.window()
        
        # Find QStackedWidget named 'pages' in MainWindow
        if hasattr(parent, "pages"):
            # Index 4 is General Tools
            parent.pages.setCurrentIndex(4)
            
            # Find GeneralToolsWidget and its tabs
            if hasattr(parent, "general_tools"):
                # Index 5 is Wireless tab
                parent.general_tools.tabs.setCurrentIndex(5)
                parent.statusBar().showMessage("✓ Đã chuyển sang Kết nối không dây", 3000)
        else:
            # Fallback for complex nesting
            # Try to find nav buttons in sidebar and click one
            if hasattr(parent, "sidebar") and hasattr(parent.sidebar, "buttons"):
                for btn in parent.sidebar.buttons:
                    if "Công Cụ" in btn.text():
                        btn.click()
                        break
        
    def setup_stats_grid(self):
        """2x2 Grid of Stat Cards"""
        if hasattr(self, 'stats_added'): return
        self.stats_added = True
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # RAM Card (Deep Blue Gradient)
        self.card_ram = StatCard("RAM", "Đang tải...", self.get_icon_path("ram.png"), ["#00c6ff", "#0072ff"])
        grid.addWidget(self.card_ram, 0, 0)
        
        # CPU Card (Rich Purple Gradient)
        self.card_cpu = StatCard("CPU", "Đang tải...", self.get_icon_path("cpu.png"), ["#8E2DE2", "#4A00E0"])
        grid.addWidget(self.card_cpu, 0, 1)
        
        # Android (Luscious Green Gradient)
        self.card_android = StatCard("Android", "Đang tải...", self.get_icon_path("android.png"), ["#11998e", "#38ef7d"])
        grid.addWidget(self.card_android, 1, 0)
        
        # OS Version (Sunset Orange Gradient)
        self.card_os = StatCard("Hệ điều hành", "Đang tải...", self.get_icon_path("shield.png"), ["#FF416C", "#FF4B2B"])
        grid.addWidget(self.card_os, 1, 1)
        
        self.content_layout.addLayout(grid)
        
    def setup_details_section(self):
        """Detail Section"""
        if hasattr(self, 'details_added'): return
        self.details_added = True
        
        self.details_card = QFrame()
        self.details_card.setObjectName("details_card")
        self.details_card.setStyleSheet(f"""
            QFrame#details_card {{
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
        item = SpecItem(title, "Đang quét...", icon)
        layout.addWidget(item)
        self.rows[key] = item

    def add_software_spec(self, title, key, icon, layout):
        item = SpecItem(title, "Đang quét...", icon)
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
        # Optimized: Check cache first
        cached_data = data_cache.get('dashboard_data')
        if cached_data:
            self.on_data_ready(cached_data)
        else:
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
        """Refresh dashboard data (with cache check)"""
        # Optimized: Check nếu worker đang chạy thì skip
        if self.worker.isRunning():
            print("Dashboard: Worker still running, skipping refresh")
            return
            
        self.worker._stop_requested = False
        self.worker.start()
    
    @throttle(wait=500)  # Throttle để tránh update quá nhanh
    def _update_clock_throttled(self):
        """Update clock (throttled)"""
        now = datetime.datetime.now()
        self.time_lbl.setText(now.strftime("%H:%M:%S"))
    
    def update_clock(self):
        """Legacy method, redirect to throttled version"""
        self._update_clock_throttled()

    @throttle(wait=300)  # Throttle updates để tránh flicker
    def _on_data_ready_throttled(self, info):
        """Throttled wrapper for on_data_ready"""
        self.on_data_ready(info)
    
    def on_data_ready(self, info):
        """Handle data from worker (optimized with caching)"""
        # Optimized: Cache data with TTL=10s
        if info:
            data_cache.put('dashboard_data', info)
        
        # Optimized: Skip update nếu data giống hệt lần trước (tránh redundant UI updates)
        if self._last_update_data == info:
            print("Dashboard: Data unchanged, skipping UI update")
            return
        self._last_update_data = info
        
        # Always update authorization status first
        is_online = self.adb.is_online()
        # Find real status for the current device from detected list if possible
        # Or just use the status from info if get_detailed_system_info succeeded
        
        device_status = "UNKNOWN"
        if info:
            # If we got info, it's mostly online, but double check devices
            devices = self.adb.get_devices()
            for serial, status in devices:
                if serial == self.adb.current_device:
                    from src.core.adb.adb_manager import DeviceStatus
                    if status == DeviceStatus.ONLINE:
                        device_status = "ONLINE"
                    elif status == DeviceStatus.UNAUTHORIZED:
                        device_status = "UNAUTHORIZED"
                    break
        
        if device_status == "ONLINE":
            self.auth_badge.setText(" DEVICE AUTHORIZED ")
            self.auth_badge.setStyleSheet("background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 11px; border: 1px solid rgba(46, 204, 113, 0.4);")
        elif device_status == "UNAUTHORIZED":
            self.auth_badge.setText(" UNAUTHORIZED ")
            self.auth_badge.setStyleSheet("background-color: rgba(255, 71, 87, 0.2); color: #ff6b81; border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 11px; border: 1px solid rgba(255, 71, 87, 0.4);")
        else:
             # Fallback if no specific status found but is_online (has serial)
             if is_online:
                 self.auth_badge.setText(" CONNECTED ")
                 self.auth_badge.setStyleSheet("background-color: rgba(46, 134, 222, 0.2); color: #54a0ff; border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 11px; border: 1px solid rgba(46, 134, 222, 0.4);")
             else:
                 self.auth_badge.setText(" DISCONNECTED ")
                 self.auth_badge.setStyleSheet("background-color: rgba(255, 71, 87, 0.2); color: #ff6b81; border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 11px; border: 1px solid rgba(255, 71, 87, 0.4);")

        if not info:
            if not is_online:
                self.device_name_lbl.setText("Device Unauthorized")
                self.chip_lbl.setText("Please check your phone screen")
            return
            
        try:
            # DEBUG: Print received info keys (only if changed)
            print(f"Dashboard: Updating UI with new data")
            
            # 1. Update Hero Section
            if 'device_friendly_name' in info and info['device_friendly_name']:
                self.device_name_lbl.setText(info['device_friendly_name'])
            elif 'model' in info:
                self.device_name_lbl.setText(info.get('model', 'Unknown Device'))
            else:
                self.device_name_lbl.setText("Unknown Device")
                
            # Specs Row
            soc = info.get("soc_name")
            if not soc or soc == "Unknown":
                soc = info.get("board", "Unknown SoC")
            self.chip_lbl.setText(f"{soc}")
            
            ram = info.get('ram_total', '?')
            store_total = info.get('storage_total', '0GB')
            # If ram_total returns 0GB/?, check memory_info raw
            if ram == "?" or ram == "0GB":
                 # Fallback logic if needed, but UI just shows what it gets
                 pass
                 
            self.storage_lbl.setText(f"{ram} | {store_total}")
            # Note: storage_total might not be directly in 'info' as clean string, dependent on adb worker.
            # Let's use specific keys if available or fallback
            
            batt = info.get("battery_level", 0)
            self.batt_lbl.setText(f"{batt}%")
            
            android_ver = info.get("android_version", "--")
            self.android_badge.setText(f" ANDROID {android_ver} ")
            self.android_badge.setStyleSheet("background-color: rgba(25, 118, 210, 0.2); color: #64b5f6; border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 11px; border: 1px solid rgba(25, 118, 210, 0.4);")
            
            
            # 2. Update Stats Grid
            # RAM: Just Total Capacity as requested
            ram_txt = f"{info.get('ram_total', '0GB')}"
            self.card_ram.update_value(ram_txt)
            
            self.card_android.update_value(str(android_ver))
            
            # OS Version (HyperOS / MIUI)
            os_ver = info.get("os_version", "Unknown")
            self.card_os.update_value(os_ver)
            
            # CPU: Show Manufacturer/Branding + Model if possible
            soc_name = info.get("soc_name", "Không rõ")
            self.card_cpu.update_value(soc_name)
            
            if 'model' in self.rows:
                self.rows['model'].set_value(info.get('model', 'Không rõ'))
            if 'device_name' in self.rows: # Codename - keep original
                self.rows['device_name'].set_value(info.get('device_name', 'Không rõ'))
            if 'soc_name' in self.rows: # Chipset
                self.rows['soc_name'].set_value(soc_name if soc_name else info.get('board', 'Không rõ'))
            
            if 'build_id' in self.rows:
                self.rows['build_id'].set_value(info.get('build_id', 'Không rõ'))
            if 'security_patch' in self.rows:
                self.rows['security_patch'].set_value(info.get('security_patch', 'Không rõ'))
            if 'kernel' in self.rows:
                self.rows['kernel'].set_value(info.get('kernel', 'Không rõ'))
            
        except Exception as e:
            print(f"Error updating Dashboard: {e}")
            
    def closeEvent(self, event):
        self.stop_updates()
        super().closeEvent(event)
