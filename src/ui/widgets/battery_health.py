# src/ui/widgets/battery_health.py
"""
Battery Health Widget
Redesigned: Glass-morphism cards with high-contrast text.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGraphicsDropShadowEffect, QGridLayout, QTextEdit, QPushButton,
    QSpacerItem, QSizePolicy, QScrollArea
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
        retries = 3
        last_error = ""
        while retries > 0:
            try:
                if not self.adb.is_online():
                    self.adb.check_connection()
                
                info = self.adb.get_battery_info()
                
                if info and info.get('level', 0) > 0:
                     self.finished.emit(info)
                     return
                
                retries -= 1
                if retries > 0:
                    import time
                    time.sleep(1)
            except Exception as e:
                last_error = str(e)
                retries -= 1
                if retries > 0:
                    import time
                    time.sleep(1)
        
        self.finished.emit({'debug_log': f'Failed after 3 retries. Last error: {last_error or "Unknown"}'})

class BatteryRing(QWidget):
    """Circular battery ring gauge — big & clean"""
    def __init__(self, level=0, charging=False):
        super().__init__()
        self.level = level
        self.charging = charging
        self.setFixedSize(160, 160)
        
    def set_data(self, level, charging):
        self.level = level
        self.charging = charging
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 18
        rect = QRectF(margin, margin, w - 2*margin, h - 2*margin)
        
        # Background track
        painter.setPen(QPen(QColor(255, 255, 255, 25), 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, -360 * 16)
        
        # Active arc
        color = QColor("#2ecc71")  # Green
        if self.level <= 20: color = QColor("#e74c3c")
        elif self.level <= 40: color = QColor("#f1c40f")
        if self.charging: color = QColor("#54a0ff")
        
        span = -int(360 * self.level / 100)
        painter.setPen(QPen(color, 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 90 * 16, span * 16)
        
        # Center text — big percentage
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 36, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.level}%")
        
        # Charging icon below %
        if self.charging:
            painter.setFont(QFont("Segoe UI Symbol", 14))
            painter.setPen(QColor("#54a0ff"))
            sub_rect = QRectF(0, h * 0.58, w, 30)
            painter.drawText(sub_rect, Qt.AlignHCenter, "⚡ Đang sạc")

class TempGauge(QWidget):
    """Modern Temperature Gauge"""
    def __init__(self, temp=0):
        super().__init__()
        self.temp = temp
        self.setFixedSize(140, 140)
        
    def set_temp(self, t):
        self.temp = t
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 18
        rect = QRectF(margin, margin, w - 2*margin, h - 2*margin)
        
        # Background Track
        painter.setPen(QPen(QColor(255, 255, 255, 25), 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225 * 16, -270 * 16)
        
        # Active Arc
        ratio = min(max(self.temp, 0), 60) / 60.0
        span = -270 * ratio
        
        color = QColor("#2ecc71")
        if self.temp > 35: color = QColor("#f1c40f")
        if self.temp > 42: color = QColor("#e74c3c")
        
        painter.setPen(QPen(color, 10, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, 225 * 16, int(span * 16))
        
        # Center Text
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{int(self.temp)}°")

# ===========================
# STAT MINI-CARD
# ===========================
class StatMiniCard(QFrame):
    """Individual stat row with glass background for readability"""
    def __init__(self, icon, title, value="..."):
        super().__init__()
        self.setObjectName("StatMini")
        self.setStyleSheet(f"""
            #StatMini {{
                background-color: rgba(255, 255, 255, 0.06);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        self.setFixedHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 18, 8)
        layout.setSpacing(14)
        
        # Icon circle
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("""
            font-size: 18px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 18px;
        """)
        layout.addWidget(icon_lbl)
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.65);
            font-size: 13px;
            font-weight: 500;
        """)
        layout.addWidget(title_lbl, 1)
        
        # Value
        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: 700;
        """)
        self.val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.val_lbl)
        
    def set_value(self, text):
        self.val_lbl.setText(text)

# ===========================
# MAIN WIDGET
# ===========================
class BatteryHealthWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self._auto_refresh = False
        from PySide6.QtCore import QTimer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(5000)  # 5 seconds
        self._refresh_timer.timeout.connect(self.refresh_data)
        self.setup_ui()
        
    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(0)
        
        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(16)
        
        # ─── 1. HERO CARD ───
        self.hero_card = QFrame()
        self.hero_card.setObjectName("BattHero")
        self._apply_hero_gradient()
        self.hero_card.setFixedHeight(200)
        
        shadow = QGraphicsDropShadowEffect(self.hero_card)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 8)
        self.hero_card.setGraphicsEffect(shadow)
        
        hero_layout = QHBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(35, 20, 35, 20)
        hero_layout.setSpacing(20)
        
        # Left: Info
        v_info = QVBoxLayout()
        v_info.setAlignment(Qt.AlignVCenter)
        v_info.setSpacing(6)
        
        self.lbl_main_cap = QLabel("--- mAh")
        self.lbl_main_cap.setStyleSheet("font-size: 34px; font-weight: 800; color: white; border: none; letter-spacing: -0.5px;")
        
        self.lbl_status_detailed = QLabel("Trạng thái: ---")
        self.lbl_status_detailed.setStyleSheet("font-size: 15px; color: rgba(255,255,255,0.85); border: none; font-weight: 500;")
        
        self.lbl_tech = QLabel("Công nghệ: ---")
        self.lbl_tech.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.5); border: none;")
        
        v_info.addWidget(self.lbl_main_cap)
        v_info.addWidget(self.lbl_status_detailed)
        v_info.addWidget(self.lbl_tech)
        
        self.btn_retry = QPushButton("🔄 Thử lại")
        self.btn_retry.setCursor(Qt.PointingHandCursor)
        self.btn_retry.setFixedSize(120, 36)
        self.btn_retry.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 18px;
                font-weight: bold;
                font-size: 13px;
                margin-top: 5px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.3); }
        """)
        self.btn_retry.clicked.connect(self.refresh_data)
        self.btn_retry.hide()
        v_info.addWidget(self.btn_retry)
        
        hero_layout.addLayout(v_info, 1)
        
        # Right: Battery Ring
        self.bat_ring = BatteryRing()
        hero_layout.addWidget(self.bat_ring, 0, Qt.AlignVCenter)
        
        layout.addWidget(self.hero_card)
        
        # ─── 2. STATS + TEMP ROW ───
        split = QHBoxLayout()
        split.setSpacing(14)
        
        # Left: Detail Stats
        stats_card = QFrame()
        stats_card.setObjectName("BattStats")
        stats_card.setStyleSheet(f"""
            #BattStats {{
                background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        stats_shadow = QGraphicsDropShadowEffect(stats_card)
        stats_shadow.setBlurRadius(20)
        stats_shadow.setColor(QColor(0, 0, 0, 40))
        stats_shadow.setOffset(0, 5)
        stats_card.setGraphicsEffect(stats_shadow)
        
        stats_l = QVBoxLayout(stats_card)
        stats_l.setContentsMargins(20, 22, 20, 22)
        stats_l.setSpacing(10)
        
        header_info = QLabel("Chi Tiết Pin")
        header_info.setStyleSheet("color: white; font-weight: 700; font-size: 17px; border: none;")
        stats_l.addWidget(header_info)
        
        desc_info = QLabel("Sạc đầy 100% để xem kết quả chính xác nhất")
        desc_info.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 12px; margin-bottom: 8px; border: none;")
        stats_l.addWidget(desc_info)
        
        # Stat mini-cards 
        self.stat_design = StatMiniCard("🔋", "Dung Lượng Thiết Kế")
        self.stat_real = StatMiniCard("⚡", "Dung Lượng Thực Tế")
        self.stat_loss = StatMiniCard("📉", "Độ Chai Pin")
        self.stat_volt = StatMiniCard("🔌", "Điện Áp")
        
        stats_l.addWidget(self.stat_design)
        stats_l.addWidget(self.stat_real)
        stats_l.addWidget(self.stat_loss)
        stats_l.addWidget(self.stat_volt)
        stats_l.addStretch()
        
        split.addWidget(stats_card, 3)
        
        # Right: Temperature
        temp_card = QFrame()
        temp_card.setObjectName("BattTemp")
        temp_card.setStyleSheet(f"""
            #BattTemp {{
                background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        temp_shadow = QGraphicsDropShadowEffect(temp_card)
        temp_shadow.setBlurRadius(20)
        temp_shadow.setColor(QColor(0, 0, 0, 40))
        temp_shadow.setOffset(0, 5)
        temp_card.setGraphicsEffect(temp_shadow)
        
        temp_card.setFixedWidth(220)
        temp_l = QVBoxLayout(temp_card)
        temp_l.setContentsMargins(20, 22, 20, 22)
        temp_l.setAlignment(Qt.AlignHCenter)
        
        temp_header = QLabel("Nhiệt Độ")
        temp_header.setStyleSheet("color: white; font-weight: 700; font-size: 17px; border: none;")
        temp_l.addWidget(temp_header, 0, Qt.AlignHCenter)
        
        temp_l.addSpacing(10)
        
        self.gauge = TempGauge()
        temp_l.addWidget(self.gauge, 0, Qt.AlignHCenter)
        
        # Temp label below gauge
        self.temp_status = QLabel("Bình thường")
        self.temp_status.setAlignment(Qt.AlignCenter)
        self.temp_status.setStyleSheet("""
            color: #2ecc71;
            font-size: 13px;
            font-weight: 600;
            padding: 6px 16px;
            background: rgba(46, 204, 113, 0.15);
            border-radius: 12px;
        """)
        temp_l.addSpacing(10)
        temp_l.addWidget(self.temp_status, 0, Qt.AlignHCenter)
        temp_l.addStretch()
        
        split.addWidget(temp_card, 1)
        
        layout.addLayout(split)
        
        # ─── 3. DEBUG TOGGLE ───
        btn_debug = QPushButton("📋 Xem Log Chi Tiết")
        btn_debug.setCheckable(True)
        btn_debug.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 15px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:checked {{
                background: {ThemeManager.COLOR_ACCENT};
                color: white;
                border: none;
            }}
        """)
        btn_debug.toggled.connect(self.toggle_debug)
        layout.addWidget(btn_debug, alignment=Qt.AlignLeft)
        
        self.txt_debug = QTextEdit()
        self.txt_debug.setFixedHeight(120)
        self.txt_debug.setReadOnly(True)
        self.txt_debug.setStyleSheet(f"""
            background: rgba(0,0,0,0.3);
            color: rgba(255,255,255,0.8);
            font-family: Consolas;
            border-radius: 10px;
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.05);
        """)
        self.txt_debug.hide()
        layout.addWidget(self.txt_debug)
        
        layout.addStretch()
        
        scroll.setWidget(container)
        main.addWidget(scroll)
        
        # Refresh Data
        self.refresh_data()
        
    def _apply_hero_gradient(self, accent=None):
        """Apply gradient to hero card"""
        c = accent or ThemeManager.COLOR_ACCENT
        self.hero_card.setStyleSheet(f"""
            #BattHero {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c}, stop:1 #0f3460);
                border-radius: 22px;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        
    def toggle_debug(self, is_visible):
        self.txt_debug.setVisible(is_visible)

    def refresh_data(self):
        worker = BatteryWorker(self.adb)
        worker.finished.connect(self.update_ui)
        worker.start()
        # Guard: wait for old worker if still running
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.wait(3000)
        self.worker = worker
        
    def update_ui(self, info):
        if not info: return
        
        # Check for errors first
        if "debug_log" in info:
            self.txt_debug.setText(info["debug_log"])
            self.lbl_main_cap.setText("Mất Kết Nối")
            self.lbl_main_cap.setStyleSheet("font-size: 28px; font-weight: bold; color: #ff5252; border: none;")
            self.bat_ring.set_data(0, False)
            self.lbl_status_detailed.setText("Thiết bị không phản hồi")
            self.lbl_tech.setText("Vui lòng kiểm tra cáp hoặc ADB")
            self.stat_design.set_value("---")
            self.stat_real.set_value("---")
            self.stat_loss.set_value("---")
            self.stat_volt.set_value("---")
            self.btn_retry.show()
            return

        self.btn_retry.hide()

        # Restore normal style
        self.lbl_main_cap.setStyleSheet("font-size: 34px; font-weight: 800; color: white; border: none; letter-spacing: -0.5px;")
        self.lbl_status_detailed.setStyleSheet("font-size: 15px; color: rgba(255,255,255,0.85); border: none; font-weight: 500;")
        self.lbl_tech.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.5); border: none;")
        self._apply_hero_gradient()
        
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
            self.lbl_main_cap.setText("Pin Thiết Bị")
            
        self.lbl_status_detailed.setText(f"Trạng thái: {status_txt}")
        self.lbl_tech.setText(f"Công nghệ: {tech}  •  Sạc 100% để kiểm tra chính xác")

        # Update Ring
        is_charging = str(status_raw).lower() == "charging" or info.get("status_code", 0) == 2
        self.bat_ring.set_data(level, is_charging)
        
        # Update Details
        if design_mah > 0:
            self.stat_design.set_value(f"{design_mah:,} mAh")
        else:
            self.stat_design.set_value("Hạn chế (No Root)")
            
        if full_mah > 0:
            self.stat_real.set_value(f"{full_mah:,} mAh")
            loss = max(0, design_mah - full_mah)
            health = (full_mah / design_mah) * 100 if design_mah > 0 else 0
            self.stat_loss.set_value(f"{loss:,} mAh ({int(100-health)}%)")
        else:
            self.stat_real.set_value("Hạn chế")
            health_code = info.get("health", 0)
            health_str = {2: "Tốt", 3: "Quá nhiệt", 4: "Hỏng", 5: "Quá áp", 7: "Lạnh"}.get(health_code, "Không rõ")
            self.stat_loss.set_value(f"Sức khỏe: {health_str}")
            
        # Voltage logic
        if volt > 10000: volt = volt / 1000.0
        elif volt > 1000: volt = volt / 1000.0
        
        self.stat_volt.set_value(f"{volt:.2f} V")
        
        # Temp logic
        if temp > 100: temp = temp / 10.0
        self.gauge.set_temp(temp)
        
        # Temp status text
        if temp <= 35:
            self.temp_status.setText("✓ Bình thường")
            self.temp_status.setStyleSheet("""
                color: #2ecc71; font-size: 13px; font-weight: 600;
                padding: 6px 16px; background: rgba(46, 204, 113, 0.15);
                border-radius: 12px; border: none;
            """)
        elif temp <= 42:
            self.temp_status.setText("⚠ Hơi nóng")
            self.temp_status.setStyleSheet("""
                color: #f1c40f; font-size: 13px; font-weight: 600;
                padding: 6px 16px; background: rgba(241, 196, 15, 0.15);
                border-radius: 12px; border: none;
            """)
        else:
            self.temp_status.setText("🔥 Quá nóng!")
            self.temp_status.setStyleSheet("""
                color: #e74c3c; font-size: 13px; font-weight: 600;
                padding: 6px 16px; background: rgba(231, 76, 60, 0.15);
                border-radius: 12px; border: none;
            """)
