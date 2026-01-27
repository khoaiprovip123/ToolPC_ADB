# src/ui/widgets/battery_health.py
"""
Battery Health Widget
Premium redesign with Dark Cards on Light Background.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGraphicsDropShadowEffect, QGridLayout, QTextEdit, QPushButton,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QRectF, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient, QConicalGradient
from src.ui.theme_manager import ThemeManager

class BatteryWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, adb):
        super().__init__()
        self.adb = adb
        
    def run(self):
        try:
            # Ensure connected
            if not self.adb.is_online():
                self.adb.check_connection()
            
            info = self.adb.get_battery_info()
            
            if not info:
                 # If empty, try one more time causing check_connection
                 if self.adb.check_connection():
                     info = self.adb.get_battery_info()
            
            if not info:
                 self.finished.emit({'debug_log': 'No data returned. Device offline or ADB error.'})
            else:
                 self.finished.emit(info)
        except Exception as e:
            self.finished.emit({'debug_log': str(e)})

class BatteryIcon(QWidget):
    """Custom painted battery icon"""
    def __init__(self, level=50, charging=False):
        super().__init__()
        self.level = level
        self.charging = charging
        self.setFixedSize(80, 40)
        
    def set_data(self, level, charging):
        self.level = level
        self.charging = charging
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Main Body
        rect = QRectF(2, 5, 70, 30)
        path = QBrush(QColor("#353b48"))
        painter.setBrush(path) # Dark body
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Cap
        painter.setBrush(QColor("#7f8fa6"))
        painter.drawRoundedRect(72, 12, 4, 16, 2, 2)
        
        # Level
        fill_width = (self.level / 100) * 66
        fill_width = max(0, min(fill_width, 66)) # Clamp
        fill_rect = QRectF(4, 7, fill_width, 26)
        
        # Color based on level
        c = "#2ecc71" # Green
        if self.level <= 20: c = "#e74c3c" # Red
        elif self.level <= 40: c = "#f1c40f" # Yellow
        if self.charging: c = "#3498db" # Blue
        
        painter.setBrush(QColor(c))
        painter.drawRoundedRect(fill_rect, 2, 2)
        
        # Lightning icon if charging
        if self.charging:
            painter.setPen(QColor("white"))
            font = QFont("Segoe UI Symbol", 14, QFont.Bold)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, "⚡")

class TempGauge(QWidget):
    """Modern Temperature Gauge"""
    def __init__(self, temp=0):
        super().__init__()
        self.temp = temp
        self.setFixedSize(120, 120)
        
    def set_temp(self, t):
        self.temp = t
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 15
        
        # Arc Area
        rect = QRectF(margin, margin, w - 2*margin, h - 2*margin)
        
        # Background Track (Dark Grey)
        painter.setPen(QPen(QColor(60, 60, 60), 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225 * 16, -270 * 16)
        
        # Active Arc
        ratio = min(max(self.temp, 0), 60) / 60.0
        span = -270 * ratio
        
        # Solid color for active
        color = QColor("#2ecc71")
        if self.temp > 35: color = QColor("#f1c40f")
        if self.temp > 42: color = QColor("#e74c3c")
        
        painter.setPen(QPen(color, 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225 * 16, int(span * 16))
        
        # Center Text
        painter.setPen(QColor(ThemeManager.COLOR_TEXT_PRIMARY))
        painter.setFont(QFont("Arial", 22, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{int(self.temp)}°C")

class BatteryHealthWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # --- 1. Header Card (Gradient) ---
        self.top_card = QFrame()
        self.gradient_style = f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ThemeManager.COLOR_ACCENT}, stop:1 #2d3436);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            QLabel {{ background: transparent; border: none; }}
        """
        self.top_card.setStyleSheet(self.gradient_style)
        self.top_card.setFixedHeight(140)
        top_layout = QHBoxLayout(self.top_card)
        top_layout.setContentsMargins(40, 0, 40, 0)
        
        # Info Group
        v_info = QVBoxLayout()
        v_info.setAlignment(Qt.AlignVCenter)
        self.lbl_main_cap = QLabel("--- mAh")
        self.lbl_main_cap.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; border: none;")
        
        self.lbl_percent = QLabel("--%")
        self.lbl_percent.setStyleSheet(f"font-size: 24px; color: {ThemeManager.COLOR_TEXT_SECONDARY}; border: none;")
        
        self.lbl_status = QLabel("Bộ sạc: ---")
        self.lbl_status.setStyleSheet(f"font-size: 14px; color: {ThemeManager.COLOR_TEXT_SECONDARY}; margin-top: 5px; border: none;")
        
        v_info.addWidget(self.lbl_main_cap)
        v_info.addWidget(self.lbl_percent)
        v_info.addWidget(self.lbl_status)
        top_layout.addLayout(v_info)
        
        top_layout.addStretch()
        
        # Battery Icon
        self.bat_icon = BatteryIcon()
        self.bat_icon.setFixedSize(120, 60) # Scale up
        top_layout.addWidget(self.bat_icon)
        
        layout.addWidget(self.top_card)
        
        # --- 2. Lower Split Section ---
        split_layout = QHBoxLayout()
        split_layout.setSpacing(15)
        
        # Left: Details Card
        self.info_card = QFrame()
        self.info_card.setStyleSheet(self.top_card.styleSheet()) # Reuse
        info_l = QVBoxLayout(self.info_card)
        info_l.setContentsMargins(30, 30, 30, 30)
        
        header_info = QLabel("Chi Tiết Pin")
        header_info.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-weight: bold; font-size: 16px; margin-bottom: 5px; border: none;")
        desc_info = QLabel("Thông số từ kernel/hardware. Kết quả chính xác nhất khi sạc đầy 100%.")
        desc_info.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; font-style: italic; margin-bottom: 20px; border: none;")
        desc_info.setWordWrap(True)
        
        info_l.addWidget(header_info)
        info_l.addWidget(desc_info)
        
        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"color: {ThemeManager.get_theme()['COLOR_BORDER']}; background: {ThemeManager.get_theme()['COLOR_BORDER']}; height: 1px; border: none;")
        info_l.addWidget(div)
        info_l.addSpacing(20)

        # Grid
        grid = QGridLayout()
        grid.setVerticalSpacing(20)
        grid.setHorizontalSpacing(10)
        
        # Use initial "..." instead of "Scanning..." to look cleaner
        self.lbl_design = self.add_stat_row(grid, 0, "🔋", "Dung Lượng Thiết Kế")
        self.lbl_real = self.add_stat_row(grid, 1, "⚡", "Dung Lượng Thực Tế")
        self.lbl_loss = self.add_stat_row(grid, 2, "📉", "Độ Chai Pin (Loss)")
        self.lbl_volt = self.add_stat_row(grid, 3, "🔌", "Điện Áp (Voltage)")
        
        info_l.addLayout(grid)
        info_l.addStretch()
        
        # Right: Temp Card
        self.temp_card = QFrame()
        self.temp_card.setStyleSheet(self.top_card.styleSheet())
        self.temp_card.setFixedWidth(220)
        temp_l = QVBoxLayout(self.temp_card)
        temp_l.setContentsMargins(20, 30, 20, 30)
        temp_l.setAlignment(Qt.AlignHCenter)
        
        temp_header = QLabel("Nhiệt Độ")
        temp_header.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-weight: bold; font-size: 16px; margin-bottom: 20px; border: none;")
        temp_l.addWidget(temp_header)
        
        self.gauge = TempGauge()
        temp_l.addWidget(self.gauge)
        temp_l.addStretch()
        
        split_layout.addWidget(self.info_card)
        split_layout.addWidget(self.temp_card)
        
        layout.addLayout(split_layout)
        
        # --- 3. Debug Toggle ---
        btn_debug = QPushButton("Xem Log Chi Tiết")
        btn_debug.setCheckable(True)
        btn_debug.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 11px;
            }}
            QPushButton:checked {{
                background: {ThemeManager.COLOR_ACCENT};
                color: white;
            }}
        """)
        btn_debug.toggled.connect(self.toggle_debug)
        layout.addWidget(btn_debug, alignment=Qt.AlignLeft)
        
        self.txt_debug = QTextEdit()
        self.txt_debug.setFixedHeight(120)
        self.txt_debug.setReadOnly(True)
        self.txt_debug.setStyleSheet(f"background: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-family: Consolas; border-radius: 8px;")
        self.txt_debug.hide()
        layout.addWidget(self.txt_debug)
        
        # Refresh Data
        self.refresh_data()
        
    def add_stat_row(self, grid, row, icon, title):
        l_icon = QLabel(icon)
        l_icon.setStyleSheet("font-size: 16px; border: none; background: transparent;")
        l_title = QLabel(title)
        l_title.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px; border: none; background: transparent;")
        l_val = QLabel("...")
        l_val.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        
        grid.addWidget(l_icon, row, 0)
        grid.addWidget(l_title, row, 1)
        grid.addWidget(l_val, row, 2, Qt.AlignRight)
        return l_val
        
    def toggle_debug(self, is_visible):
        self.txt_debug.setVisible(is_visible)

    def refresh_data(self):
        # Reset UI to scanning state if needed, but keeping old data is fine too
        # self.lbl_main_cap.setText("Scanning...") 
        worker = BatteryWorker(self.adb)
        worker.finished.connect(self.update_ui)
        worker.start()
        self.worker = worker
        
    def update_ui(self, info):
        if not info: return
        
        # Check for errors first
        if "debug_log" in info:
            self.txt_debug.setText(info["debug_log"])
            if "no devices/emulators" in info["debug_log"] or "error" in info.get("debug_log", "").lower():
                # Show disconnected state if critical data is missing
                if info.get("charge_full", 0) == 0:
                    self.lbl_main_cap.setText("Mất Kết Nối")
                    self.lbl_main_cap.setStyleSheet("font-size: 28px; font-weight: bold; color: #e74c3c; border: none;")
                    self.lbl_percent.setText("--%")
                    self.lbl_status.setText("Không tìm thấy thiết bị")
                    self.lbl_design.setText("---")
                    self.lbl_real.setText("---")
                    self.lbl_loss.setText("---")
                    self.bat_icon.set_data(0, False) # Empty battery
                    return

        # Restore normal style & Apply Gradient to ALL Cards
        gradient_style = f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ThemeManager.COLOR_ACCENT}, stop:1 #2d3436);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            QLabel {{ background: transparent; border: none; }}
        """
        self.top_card.setStyleSheet(gradient_style)
        self.info_card.setStyleSheet(gradient_style)
        self.temp_card.setStyleSheet(gradient_style)

        self.lbl_main_cap.setStyleSheet("font-size: 36px; font-weight: bold; color: white; border: none;")
        self.lbl_percent.setStyleSheet("font-size: 20px; color: rgba(255, 255, 255, 0.8); border: none;")
        self.lbl_status.setStyleSheet("font-size: 14px; color: rgba(255, 255, 255, 0.6); margin-top: 5px; border: none;")
        
        # Parse Info
        full_mah = info.get("charge_full", 0)
        design_mah = info.get("charge_full_design", 0)
        level = info.get("level", 0)
        
        # Maps for VN Translation
        status_map_vn = {"Charging": "Đang sạc", "Discharging": "Đang dùng", "Not charging": "Không sạc", "Full": "Đầy", "Unknown": "Không rõ"}
        status_raw = info.get("status", "Unknown")
        status_txt = status_map_vn.get(status_raw, status_raw)
        
        tech = info.get("technology", "Li-poly")
        volt = info.get("voltage", 0)
        temp = info.get("temperature", 0)

        # Update Main Header
        if full_mah > 0:
            self.lbl_main_cap.setText(f"{full_mah:,} mAh")
        else:
            self.lbl_main_cap.setText(f"{level}%")
            
        self.lbl_percent.setText(f"Trạng thái: {status_txt}")
        self.lbl_status.setText(f"Công nghệ: {tech}\n(Sạc tới 100% để kiểm tra chính xác hơn nhé)")

        # Update Icon
        is_charging = str(status_raw).lower() == "charging" or info.get("status_code", 0) == 2
        self.bat_icon.set_data(level, is_charging)
        
        # Update Details
        if design_mah > 0:
            self.lbl_design.setText(f"{design_mah:,} mAh")
        else:
            self.lbl_design.setText("Hạn chế (No Root)")
            
        if full_mah > 0:
            self.lbl_real.setText(f"{full_mah:,} mAh")
            loss = max(0, design_mah - full_mah)
            health = (full_mah / design_mah) * 100 if design_mah > 0 else 0
            self.lbl_loss.setText(f"{loss:,} mAh ({int(100-health)}%)")
        else:
            self.lbl_real.setText("Hạn chế")
            health_code = info.get("health", 0)
            health_str = {2: "Tốt", 3: "Quá nhiệt", 4: "Hỏng", 5: "Quá áp", 7: "Lạnh"}.get(health_code, "Không rõ")
            self.lbl_loss.setText(f"Sức khỏe: {health_str}")
            
        # Voltage logic
        if volt > 10000: volt = volt / 1000.0
        elif volt > 1000: volt = volt / 1000.0 # mV -> V
        
        self.lbl_volt.setText(f"{volt:.2f} V")
        
        # Temp logic
        if temp > 100: temp = temp / 10.0
        self.gauge.set_temp(temp)
