# src/ui/widgets/ota_downloader.py
"""
OTA Downloader Widget - Download MIUI ROMs
Style: Glassmorphism
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager
import httpx
import asyncio

class ROMSearchWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, codename, region, type_):
        super().__init__()
        self.codename = codename
        self.region = region
        self.type = type_

    def run(self):
        try:
            results = []
            
            # 1. Try to fetch from known JSON (Old/Stable API)
            url = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-downloads/master/stable/stable.json"
            try:
                r = httpx.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    
                    # Filter local
                    for rom in data:
                        if rom.get('codename', '').lower() == self.codename.lower():
                            if self.region == "Global" or self.region in rom.get('filename', ''):
                                results.append({
                                    "version": rom.get('version', 'Unknown'),
                                    "android": rom.get('android', '?'),
                                    "region": "Stable",
                                    "type": "Recovery",
                                    "size": "Check Link",
                                    "link": rom.get('download', '')
                                })
            except Exception as _e:

                pass  # TODO: consider LogManager.log # Fail silently and use fallback
            
            # 2. If no results (Newer device like 'lisa' or API fail), add Web Fallback
            if not results:
                # Add 'HyperOS Fans' link (User Requested)
                results.append({
                    "version": "HyperOS Fans (Mới)",
                    "android": "14/15",
                    "region": "All",
                    "type": "External",
                    "size": "-",
                    "link": f"https://hyperos.fans/en/devices/{self.codename}"
                })

                # Add 'Official Page' link
                results.append({
                    "version": "Xiaomi Firmware Updater",
                    "android": "Legacy",
                    "region": "All",
                    "type": "External",
                    "size": "-",
                    "link": f"https://xiaomifirmwareupdater.com/miui/{self.codename}/"
                })
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class OTADownloaderWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("☁️ MIUI OTA Downloader")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(header)
        
        # Search Area
        search_group = QGroupBox("Tìm kiếm ROM")
        search_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                margin-top: 10px;
                padding-top: 15px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        search_layout = QHBoxLayout(search_group)
        
        self.input_codename = QLineEdit()
        self.input_codename.setPlaceholderText("Tên mã thiết bị (vd: Alioth)")
        self.input_codename.setStyleSheet(ThemeManager.get_input_style())
        search_layout.addWidget(QLabel("Thiết bị:"))
        search_layout.addWidget(self.input_codename)
        
        # Auto-detect button
        btn_detect = QPushButton("🔍 Auto")
        btn_detect.setToolTip("Tự động phát hiện thiết bị")
        btn_detect.setStyleSheet(ThemeManager.get_button_style("outline"))
        btn_detect.clicked.connect(self.auto_detect)
        search_layout.addWidget(btn_detect)
        
        self.combo_region = QComboBox()
        self.combo_region.addItems(["Global", "EEA", "China", "India", "Russia", "Turkey", "Taiwan"])
        self.combo_region.setStyleSheet(ThemeManager.get_input_style())
        search_layout.addWidget(QLabel("Khu vực:"))
        search_layout.addWidget(self.combo_region)
        
        # Search Buttons
        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.btn_search.clicked.connect(self.search_roms)
        search_layout.addWidget(self.btn_search)
        
        layout.addWidget(search_group)
        
        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Phiên bản", "Android", "Khu vực", "Loại", "Kích thước", "Hành động"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: {ThemeManager.RADIUS_BUTTON};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                gridline-color: {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                padding: 5px;
                border: none;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.table)
        
        # Status
        self.status_label = QLabel("Sẵn sàng")
        layout.addWidget(self.status_label)
        
    def auto_detect(self):
        if self.adb.current_device:
            # Try to get product info
            product = self.adb.shell("getprop ro.product.device").strip()
            if product:
                self.input_codename.setText(product)
                self.status_label.setText(f"Đã phát hiện thiết bị: {product}")
                LogManager.log("Thiết bị", f"Phát hiện: {product}", "success")
            else:
                LogManager.log("Thiết bị", "Không thể đọc thông tin thiết bị", "error")
        else:
            LogManager.log("Thiết bị", "Vui lòng kết nối thiết bị trước", "warning")

    def search_roms(self):
        codename = self.input_codename.text().strip()
        if not codename:
            LogManager.log("ROM", "Vui lòng nhập tên mã thiết bị", "warning")
            return
            
        self.btn_search.setEnabled(False)
        self.btn_search.setText("Đang tìm...")
        self.status_label.setText(f"Đang tìm ROM cho {codename}...")
        self.table.setRowCount(0)
        
        # Guard: wait for old worker before creating new
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.wait(5000)
        self.worker = ROMSearchWorker(codename, self.combo_region.currentText(), "Recovery")
        self.worker.finished.connect(self.on_search_finished)
        self.worker.error.connect(self.on_search_error)
        self.worker.start()
        
    def on_search_finished(self, results):
        # Add the mandated HyperOS Updates link
        codename = self.input_codename.text().strip()
        
        # Insert at the top (Priority Order)
        
        # 1. Author / Telegram Support
        results.insert(0, {
            "version": "Mod bởi Thangnguyen",
            "android": "-",
            "region": "Telegram",
            "type": "Community",
            "size": "-",
            "link": "https://t.me/nvthang2303"
        })

        # 2. HyperTN V3.2 (Direct Link)
        results.insert(1, {
            "version": "HyperTN V3.2",
            "android": "14/15",
            "region": "Global",
            "type": "Custom ROM",
            "size": "Check Link",
            "link": f"https://hypertn.koyeb.app/ROM/V3.2/{codename.capitalize()}"
        })

        # 3. HyperOS Updates (Web)
        results.insert(2, {
            "version": "HyperOSUpdates (Web)",
            "android": "-",
            "region": "All",
            "type": "Web Source",
            "size": "-",
            "link": f"https://hyperosupdates.com/hyperos/{codename}"
        })

        self.btn_search.setEnabled(True)
        self.btn_search.setText("Tìm kiếm")
        self.status_label.setText(f"Tìm thấy {len(results)} bản ROM")
        
        self.table.setRowCount(len(results))
        for i, rom in enumerate(results):
            self.table.setItem(i, 0, QTableWidgetItem(rom['version']))
            self.table.setItem(i, 1, QTableWidgetItem(rom['android']))
            self.table.setItem(i, 2, QTableWidgetItem(rom['region']))
            self.table.setItem(i, 3, QTableWidgetItem(rom['type']))
            self.table.setItem(i, 4, QTableWidgetItem(rom['size']))
            
            is_external = rom['type'] in ["External", "Web Source"]
            btn_text = "🌐 Mở Web" if is_external else "Tải xuống"
            btn_color = "#9B59B6" if is_external else "#3498DB" # Purple for external
            
            btn_dl = QPushButton(btn_text)
            btn_dl.setCursor(Qt.PointingHandCursor)
            btn_dl.setStyleSheet(f"""
                QPushButton {{
                    background-color: {btn_color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px;
                }}
                QPushButton:hover {{ filter: brightness(110%); }}
            """)
            # Use a lambda with default arg to capture the link correctly
            btn_dl.clicked.connect(lambda checked=False, link=rom['link']: self.download_rom(link))
            self.table.setCellWidget(i, 5, btn_dl)
            
    def on_search_error(self, error):
        self.btn_search.setEnabled(True)
        self.btn_search.setText("Tìm kiếm")
        self.status_label.setText(f"Lỗi: {error}")
        
    def download_rom(self, link):
        QDesktopServices.openUrl(QUrl(link))
        self.status_label.setText("Đang mở link tải xuống trong trình duyệt...")
        
    def reset(self):
        self.input_codename.clear()
        self.table.setRowCount(0)
        self.status_label.setText("Sẵn sàng")

class HyperOSAppsWidget(QWidget):
    """
    Dedicated widget for searching/browsing HyperOS System Apps & GCam.
    """
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("Kho Ứng Dụng HyperOS & GCam")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # --- Section 1: System Apps ---
        group_apps = QGroupBox("1. Ứng dụng Hệ thống")
        group_apps.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                border-radius: 12px;
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                margin-top: 25px;
            }}
            QGroupBox::title {{ top: -12px; left: 15px; background: transparent; }}
        """)
        layout_apps = QVBoxLayout(group_apps)
        layout_apps.setContentsMargins(20, 30, 20, 20)
        
        icon_apps = QLabel("📱")
        icon_apps.setStyleSheet("font-size: 48px;")
        icon_apps.setAlignment(Qt.AlignCenter)
        layout_apps.addWidget(icon_apps)
        
        desc_apps = QLabel("Cập nhật Launcher, Gallery, Security,\nTheme Manager phiên bản mới nhất.")
        desc_apps.setAlignment(Qt.AlignCenter)
        desc_apps.setWordWrap(True)
        layout_apps.addWidget(desc_apps)
        
        btn_apps = QPushButton("🌐 Duyệt Hệ Thống App")
        btn_apps.setCursor(Qt.PointingHandCursor)
        btn_apps.setMinimumHeight(45)
        btn_apps.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498DB; color: white; font-weight: bold; border-radius: 8px; border: none;
            }}
            QPushButton:hover {{ background-color: #2980B9; }}
        """)
        btn_apps.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://hyperosupdates.com/apps")))
        layout_apps.addWidget(btn_apps)
        layout_apps.addStretch()
        
        content_layout.addWidget(group_apps)
        
        # --- Section 2: GCam ---
        group_gcam = QGroupBox("2. Google Camera (GCam)")
        group_gcam.setStyleSheet(group_apps.styleSheet())
        layout_gcam = QVBoxLayout(group_gcam)
        layout_gcam.setContentsMargins(20, 30, 20, 20)
        
        icon_gcam = QLabel("📷")
        icon_gcam.setStyleSheet("font-size: 48px;")
        icon_gcam.setAlignment(Qt.AlignCenter)
        layout_gcam.addWidget(icon_gcam)
        
        desc_gcam = QLabel("Tìm bản GCam ổn định\ncho thiết bị của bạn.")
        desc_gcam.setAlignment(Qt.AlignCenter)
        desc_gcam.setWordWrap(True)
        layout_gcam.addWidget(desc_gcam)
        
        # Input for codename
        self.input_gcam_device = QLineEdit()
        self.input_gcam_device.setPlaceholderText("Tên mã máy (vd: Lisa)")
        self.input_gcam_device.setAlignment(Qt.AlignCenter)
        self.input_gcam_device.setStyleSheet(ThemeManager.get_input_style())
        layout_gcam.addWidget(self.input_gcam_device)
        
        # Auto button
        btn_auto = QPushButton("🔍 Auto Detect")
        btn_auto.setCursor(Qt.PointingHandCursor)
        btn_auto.setStyleSheet(ThemeManager.get_button_style("secondary"))
        btn_auto.clicked.connect(self.auto_detect_gcam)
        layout_gcam.addWidget(btn_auto)

        btn_gcam = QPushButton("🌐 Tìm GCam Ngay")
        btn_gcam.setCursor(Qt.PointingHandCursor)
        btn_gcam.setMinimumHeight(45)
        btn_gcam.setStyleSheet(f"""
            QPushButton {{
                background-color: #9B59B6; color: white; font-weight: bold; border-radius: 8px; border: none;
            }}
            QPushButton:hover {{ background-color: #8E44AD; }}
        """)
        btn_gcam.clicked.connect(self.open_gcam)
        layout_gcam.addWidget(btn_gcam)
        layout_gcam.addStretch()
        
        content_layout.addWidget(group_gcam)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
    def auto_detect_gcam(self):
        if self.adb.current_device:
            product = self.adb.shell("getprop ro.product.device").strip()
            if product:
                self.input_gcam_device.setText(product)
            else:
                LogManager.log("Thiết bị", "Không thể đọc thông tin thiết bị", "error")
        else:
            LogManager.log("Thiết bị", "Vui lòng kết nối thiết bị trước", "warning")
            
    def open_gcam(self):
        code = self.input_gcam_device.text().strip()
        if code:
            # https://hyperosupdates.com/hyperos/lisa/gcam
            url = f"https://hyperosupdates.com/hyperos/{code}/gcam"
            QDesktopServices.openUrl(QUrl(url))
        else:
            LogManager.log("GCam", "Vui lòng nhập tên mã máy (Codename)", "warning")

