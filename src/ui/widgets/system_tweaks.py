# src/ui/widgets/system_tweaks.py
"""
System Tweaks Widget - Rebuilt with Hub Style
Style: Modern Gradient Cards (Clone of XiaomiHub)
Features: Display, Performance, and System Utilities
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QScrollArea, QCheckBox, QLineEdit, QGridLayout,
    QMessageBox, QGraphicsDropShadowEffect, QInputDialog, QTabWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QLinearGradient, QGradient
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager
from src.workers.optimization_worker import OptimizationWorker

# === Re-implement ModernCard for consistency with Xiaomi Hub ===
class ModernCard(QFrame):
    def __init__(self, title, desc, icon, callback, gradient_colors=None, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.gradient_colors = gradient_colors
        
        # Base Style
        self.setObjectName("ModernCard")
        self.setup_style()
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Header (Icon & Title)
        header = QHBoxLayout()
        header.setSpacing(15)
        
        # Icon Container
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setFixedSize(48, 48)
        
        icon_bg = "rgba(255,255,255,0.1)" if gradient_colors else f"{ThemeManager.COLOR_ACCENT}15"
        self.icon_lbl.setStyleSheet(f"""
            font-size: 26px; 
            background: {icon_bg}; 
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        """)
        
        title_lbl = QLabel(title)
        title_color = "white" if gradient_colors else ThemeManager.COLOR_TEXT_PRIMARY
        title_lbl.setStyleSheet(f"font-size: 17px; font-weight: 800; color: {title_color}; background: transparent; border: none;")
        
        header.addWidget(self.icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Description
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_color = "rgba(255,255,255,0.85)" if gradient_colors else ThemeManager.COLOR_TEXT_SECONDARY
        desc_lbl.setStyleSheet(f"font-size: 13.5px; color: {desc_color}; background: transparent; border: none; line-height: 1.4;")
        layout.addWidget(desc_lbl)
        
        layout.addStretch()
        
        # Action Row
        action_row = QHBoxLayout()
        self.status_badge = QLabel("Sẵn sàng")
        badge_bg = "rgba(255,255,255,0.15)" if gradient_colors else "rgba(0,0,0,0.03)"
        self.status_badge.setStyleSheet(f"""
            font-size: 11px; 
            font-weight: 700; 
            color: {desc_color}; 
            padding: 4px 10px; 
            background: {badge_bg}; 
            border-radius: 6px;
        """)
        action_row.addWidget(self.status_badge)
        action_row.addStretch()
        
        btn = QPushButton("Kích hoạt")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.on_click)
        btn.setFixedSize(100, 36)
        
        btn_style = "background: white; color: black;" if gradient_colors else f"background: {ThemeManager.COLOR_ACCENT}; color: white;"
        btn.setStyleSheet(f"""
            QPushButton {{
                {btn_style}
                border-radius: 10px;
                font-weight: 700;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background: white;
                opacity: 0.9;
            }}
        """)
        action_row.addWidget(btn)
        layout.addLayout(action_row)

    def setup_style(self, hover=False):
        bg_style = f"background: {ThemeManager.COLOR_GLASS_WHITE};"
        if self.gradient_colors:
            bg_style = f"background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {self.gradient_colors[0]}, stop:1 {self.gradient_colors[1]});"
            
        hover_transform = "margin-top: -5px;" if hover else ""
        self.setStyleSheet(f"""
            #ModernCard {{
                {bg_style}
                border-radius: 20px;
                border: none;
                {hover_transform}
            }}
        """)

    def enterEvent(self, event):
        self.setup_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setup_style(False)
        super().leaveEvent(event)

    def on_click(self):
        if self.callback:
            self.callback()

class SystemTweaksWidget(QWidget):
    """
    Main Tweak Widget with Tabbed Hub Interface
    """
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.opt_worker = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                min-width: 150px;
                padding: 12px 20px;
                margin-right: 6px;
                font-weight: 700;
                color: #666;
                background: rgba(255,255,255,0.5);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            QTabBar::tab:selected {
                color: #2575FC;
                background: white;
                border-bottom: 3px solid #2575FC;
            }
        """)
        
        self.tabs.addTab(self.create_tab_scroll(self.setup_display_tab), "📱 Màn Hình")
        self.tabs.addTab(self.create_tab_scroll(self.setup_performance_tab), "🚀 Hiệu Năng")
        self.tabs.addTab(self.create_tab_scroll(self.setup_system_tab), "🛠️ Hệ Thống")

        layout.addWidget(self.tabs)

    def create_tab_scroll(self, setup_func):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 40)
        layout.setSpacing(25)
        
        setup_func(layout)
        
        scroll.setWidget(container)
        return scroll

    def add_section_header(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY}; margin-top: 10px;")
        layout.addWidget(lbl)

    def setup_display_tab(self, layout):
        # Hero
        self.add_hero_banner(layout, "Cài đặt Hiển thị", "Tùy chỉnh tần số quét, độ sáng và giao diện.", "#4facfe", "#00f2fe")
        
        self.add_section_header(layout, "Chế Độ Màn Hình")
        grid = QGridLayout()
        grid.setSpacing(20)
        
        grid.addWidget(ModernCard("Always-On Display", "Bật/Tắt chế độ màn hình luôn hiển thị.", "🔆", 
                                 lambda: self.toggle_dialog("enable_aod", "AOD"), ["#a8e063", "#56ab2f"]), 0, 0)
        
        grid.addWidget(ModernCard("Smooth Display (120Hz)", "Ép buộc tần số quét 120Hz mượt mà.", "🌫️", 
                                 lambda: self.toggle_dialog("force_refresh_rate", "120Hz", extra_val_on=120, extra_val_off=0), ["#bdc3c7", "#2c3e50"]), 0, 1)

        grid.addWidget(ModernCard("Hiệu Ứng Blur", "Bật hiệu ứng làm mờ mịn màng trên MIUI/HyperOS.", "💧", 
                                 lambda: self.run_task("smart_blur"), ["#89f7fe", "#66a6ff"]), 1, 0)
        
        grid.addWidget(ModernCard("Control Center Mới", "Sử dụng giao diện Trung tâm điều khiển mới.", "🎛️", 
                                 lambda: self.toggle_dialog("new_cc", "Control Center"), ["#e1eec3", "#f05053"]), 1, 1)

        grid.addWidget(ModernCard("Độ Phân Giải (WM)", "Thay đổi kích thước màn hình và DPI.", "📐", 
                                 self.ask_resolution, None), 2, 0)

        grid.addWidget(ModernCard("Độ Sáng Tối Thiểu", "Giảm độ sáng xuống mức thấp hơn cả mặc định.", "🌑", 
                                 self.ask_min_brightness, None), 2, 1)

        layout.addLayout(grid)

    def setup_performance_tab(self, layout):
        self.add_hero_banner(layout, "Hiệu Năng & Pin", "Tối ưu hóa tài nguyên hệ thống và tốc độ sạc.", "#f12711", "#f5af19")
        
        self.add_section_header(layout, "Tối Ưu Hóa Game & Pin")
        grid = QGridLayout()
        grid.setSpacing(20)
        
        grid.addWidget(ModernCard("Game Turbo", "Tối ưu hóa GPU và CPU cho chơi game.", "🚀", 
                                 lambda: self.toggle_dialog("game_perf_tune", "Game Turbo"), ["#f12711", "#f5af19"]), 0, 0)
        
        grid.addWidget(ModernCard("Sạc Nhanh Cấp Tốc", "Mở khóa giới hạn sạc (Yêu cầu củ sạc hỗ trợ).", "⚡", 
                                 lambda: self.toggle_dialog("fast_charge", "Sạc Nhanh"), ["#FDC830", "#F37335"]), 0, 1)
        
        grid.addWidget(ModernCard("Giới Hạn Process Nền", "Kiểm soát số lượng app chạy ngầm tối đa.", "🛑", 
                                 self.ask_bg_limit, None), 1, 0)

        grid.addWidget(ModernCard("Tối Ưu ART VM", "Biên dịch lại App để mở nhanh hơn (Cần chờ).", "💎", 
                                 lambda: self.run_task("compile_apps", mode="speed"), ["#43e97b", "#38f9d7"]), 1, 1)

        layout.addLayout(grid)

    def setup_system_tab(self, layout):
        self.add_hero_banner(layout, "Hệ Thống & Gỡ Lỗi", "Các công cụ can thiệp hệ thống nâng cao.", "#8360c3", "#2ebf91")
        
        self.add_section_header(layout, "Công Cụ Tiện Ích")
        grid = QGridLayout()
        grid.setSpacing(20)
        
        grid.addWidget(ModernCard("Việt Hóa 1-Click", "Cài đặt Tiếng Việt & Múi giờ VN ngay lập tức.", "🇻🇳", 
                                 lambda: self.run_task("set_language_vn"), ["#ff0000", "#ff6666"]), 0, 0)
        
        grid.addWidget(ModernCard("Tắt Cập Nhật OTA", "Ngăn chặn MIUI/HyperOS tự động cập nhật.", "🚫", 
                                 lambda: self.run_task("disable_ota"), ["#2c3e50", "#000000"]), 0, 1)
        
        grid.addWidget(ModernCard("Bỏ Qua Setup Wizard", "Bỏ qua màn hình chào mừng sau khi Reset.", "⏭️", 
                                 lambda: self.run_task("skip_setup"), None), 1, 0)
        
        grid.addWidget(ModernCard("Ẩn Thanh Điều Hướng", "Chuyển sang cử chỉ full màn hình.", "📱", 
                                 lambda: self.toggle_dialog("hide_nav", "Ẩn Navigation"), None), 1, 1)

        grid.addWidget(ModernCard("Tắt Kiểm Tra APK", "Bỏ qua Verify App khi cài đặt qua ADB.", "🛡️", 
                                 lambda: self.toggle_dialog("pkg_verifier", "Package Verifier", invert=True), ["#00b09b", "#96c93d"]), 2, 0)

        grid.addWidget(ModernCard("Desktop Mode", "Mở khóa chế độ máy tính khi xuất màn hình.", "🖥️", 
                                 lambda: self.toggle_dialog("desktop_mode", "Desktop Mode"), None), 2, 1)

        layout.addLayout(grid)

    def add_hero_banner(self, layout, title, desc, c1, c2):
        hero = QFrame()
        hero.setFixedHeight(140)
        hero.setObjectName("TweaksHero")
        hero.setStyleSheet(f"""
            #TweaksHero {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {c1}, stop:1 {c2});
                border-radius: 24px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(30, 0, 30, 0)
        
        v = QVBoxLayout()
        t = QLabel(title)
        t.setStyleSheet("font-size: 24px; font-weight: 800; color: white; background: transparent;")
        d = QLabel(desc)
        d.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.9); background: transparent;")
        v.addStretch()
        v.addWidget(t)
        v.addWidget(d)
        v.addStretch()
        hl.addLayout(v)
        layout.addWidget(hero)

    # === Interaction Helpers ===
    def toggle_dialog(self, task, name, extra_val_on=True, extra_val_off=False, invert=False):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Cấu hình {name}")
        msg.setText(f"Bạn muốn BẬT hay TẮT {name}?")
        
        btn_on = msg.addButton("Bật", QMessageBox.YesRole)
        btn_off = msg.addButton("Tắt", QMessageBox.NoRole)
        msg.addButton("Hủy", QMessageBox.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == btn_on:
            self.run_task(task, enable=not invert)
        elif msg.clickedButton() == btn_off:
            self.run_task(task, enable=invert)

    def ask_resolution(self):
        text, ok = QInputDialog.getText(self, "Độ Phân Giải", "Nhập độ phân giải (VD: 1080x2400) hoặc 'reset':")
        if ok and text:
            self.run_task("wm_size", size=text)

    def ask_min_brightness(self):
        text, ok = QInputDialog.getText(self, "Độ Sáng Min", "Nhập giá trị (0.001 - 1.0):")
        if ok and text:
            self.run_task("min_brightness", value=text)

    def ask_bg_limit(self):
         text, ok = QInputDialog.getText(self, "Giới Hạn Nền", "Nhập số lượng (VD: 2) hoặc -1 để Reset:")
         if ok and text:
             self.run_task("bg_limit", limit=text)

    def run_task(self, task_type, **kwargs):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Đang xử lý tác vụ khác...", "warning")
            return
            
        self.opt_worker = OptimizationWorker(self.adb, task_type)
        self.opt_worker.kwargs = kwargs 
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Tweaks", msg, "info"))
        self.opt_worker.finished.connect(lambda: LogManager.log("Tweaks", "Thực hiện thành công!", "success"))
        self.opt_worker.start()
