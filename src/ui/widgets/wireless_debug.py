# src/ui/widgets/wireless_debug.py
"""
Wireless Debugging Widget
Style: HyperOS Card Design
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QFormLayout, QMessageBox, QGraphicsDropShadowEffect,
    QTextEdit, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager

# ShizukuWorker removed - moved to permission_tools.py

class Card(QFrame):
    def __init__(self, title, layout_type=QVBoxLayout):
        super().__init__()
        self.setObjectName("CustomCard")
        self.setStyleSheet(f"""
            #CustomCard {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: {ThemeManager.RADIUS_CARD};
                border: 1px solid rgba(0,0,0,0.05);
            }}
            QLabel {{
                border: none;
                background: transparent;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(ThemeManager.COLOR_SHADOW)
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Header
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: bold; 
            color: {ThemeManager.COLOR_TEXT_PRIMARY}; 
            border: none; 
            background: transparent;
        """)
        self.main_layout.addWidget(self.lbl_title)
        
        # Content Layout
        self.content_layout = layout_type()
        self.content_layout.setContentsMargins(0, 5, 0, 0)
        self.main_layout.addLayout(self.content_layout)

class WirelessDebugWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # --- 1. Info Section ---
        info_card = Card("Thông tin", QVBoxLayout)
        info_lbl = QLabel("Công cụ hỗ trợ kết nối và gỡ lỗi không dây (Wireless Debugging).\nYêu cầu cùng mạng Wifi.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; border: none; background: transparent;")
        info_card.content_layout.addWidget(info_lbl)
        layout.addWidget(info_card)
        
        # --- 2. Pairing Section ---
        pair_card = Card("Android 11+ (Pairing)", QFormLayout)
        
        self.pair_ip = QLineEdit()
        self.pair_ip.setPlaceholderText("192.168.1.x")
        self.pair_ip.setStyleSheet(ThemeManager.get_input_style())
        pair_card.content_layout.addRow("IP Address:", self.pair_ip)
        
        self.pair_port = QLineEdit()
        self.pair_port.setPlaceholderText("Port (e.g. 34567)")
        self.pair_port.setStyleSheet(ThemeManager.get_input_style())
        pair_card.content_layout.addRow("Port:", self.pair_port)
        
        self.pair_code = QLineEdit()
        self.pair_code.setPlaceholderText("6 digit code")
        self.pair_code.setStyleSheet(ThemeManager.get_input_style())
        pair_card.content_layout.addRow("Pairing Code:", self.pair_code)
        
        pair_btn = QPushButton("🔗 Ghép đôi (Pair)")
        pair_btn.setCursor(Qt.PointingHandCursor)
        pair_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        pair_btn.clicked.connect(self.on_pair)
        pair_card.content_layout.addRow("", pair_btn)
        
        layout.addWidget(pair_card)
        
        # --- 3. Connect Section ---
        connect_card = Card("Kết nối (Connect)", QFormLayout)
        
        self.connect_ip = QLineEdit()
        self.connect_ip.setPlaceholderText("192.168.1.x")
        self.connect_ip.setStyleSheet(ThemeManager.get_input_style())
        connect_card.content_layout.addRow("IP Address:", self.connect_ip)
        
        self.connect_port = QLineEdit("5555")
        self.connect_port.setStyleSheet(ThemeManager.get_input_style())
        connect_card.content_layout.addRow("Port:", self.connect_port)
        
        connect_btn = QPushButton("🔌 Kết nối")
        connect_btn.setCursor(Qt.PointingHandCursor)
        connect_btn.setStyleSheet(ThemeManager.get_button_style("success"))
        connect_btn.clicked.connect(self.on_connect)
        connect_card.content_layout.addRow("", connect_btn)
        
        layout.addWidget(connect_card)
        
        # --- 4. Legacy Section ---
        legacy_card = Card("Kích hoạt qua USB (Android < 11)", QVBoxLayout)
        
        info = QLabel("Kết nối thiết bị qua USB trước, sau đó nhấn nút dưới để mở cổng 5555.")
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; border: none; background: transparent;")
        legacy_card.content_layout.addWidget(info)
        
        enable_btn = QPushButton("🔓 Mở cổng 5555 (adb tcpip 5555)")
        enable_btn.setCursor(Qt.PointingHandCursor)
        enable_btn.setStyleSheet(ThemeManager.get_button_style("warning"))
        enable_btn.clicked.connect(self.on_enable_tcpip)
        legacy_card.content_layout.addWidget(enable_btn)
        
        layout.addWidget(legacy_card)
        layout.addStretch()

    def on_pair(self):
        ip = self.pair_ip.text().strip()
        port = self.pair_port.text().strip()
        code = self.pair_code.text().strip()
        
        if not ip or not port or not code:
            LogManager.log("Thiếu thông tin", "Vui lòng nhập IP, Port và Code", "warning")
            return
            
        try:
            result = self.adb.execute(f"pair {ip}:{port} {code}")
            if "Successfully paired" in result:
                LogManager.log("Thành công", f"Đã ghép đôi với {ip}:{port}", "success")
                self.connect_ip.setText(ip)
                self.connect_port.setText("") 
            else:
                LogManager.log("Thất bại", f"Không thể ghép đôi:\n{result}", "warning")
        except Exception as e:
            LogManager.log("Lỗi", str(e), "error")

    def on_connect(self):
        ip = self.connect_ip.text().strip()
        port = self.connect_port.text().strip()
        
        if not ip:
            LogManager.log("Thiếu thông tin", "Vui lòng nhập IP", "warning")
            return
            
        addr = f"{ip}:{port}" if port else ip
        
        try:
            if self.adb.connect_wireless(ip, int(port) if port else 5555):
                LogManager.log("Thành công", f"Đã kết nối với {addr}", "success")
            else:
                LogManager.log("Thất bại", "Không thể kết nối. Kiểm tra lại IP/Port hoặc ghép đôi trước.", "warning")
        except Exception as e:
            LogManager.log("Lỗi", str(e), "error")

    def on_enable_tcpip(self):
        if not self.adb.current_device:
            LogManager.log("Lỗi", "Cần kết nối USB trước", "warning")
            return
            
        if self.adb.enable_wireless_adb():
            LogManager.log("Thành công", "Đã mở cổng 5555. Bây giờ bạn có thể rút cáp và kết nối qua IP.", "success")
        else:
            LogManager.log("Lỗi", "Không thể kích hoạt TCP/IP", "warning")

    # start_shizuku moved to permission_tools.py
