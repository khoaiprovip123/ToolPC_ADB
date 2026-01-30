# src/ui/widgets/xiaomi_optimizer.py
"""
Xiaomi Optimizer Widget - Debloat and Optimize MIUI
Style: Glassmorphism & Gradient Cards
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QCheckBox, QHeaderView, QMessageBox,
    QTabWidget, QTextEdit, QGroupBox, QProgressBar, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QGridLayout, QLineEdit, QProgressDialog,
    QListWidget, QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QGradient
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager
from PySide6.QtWidgets import QDialog

# Imports from refactored modules
from src.workers.debloat_worker import DebloatWorker
from src.workers.optimization_worker import OptimizationWorker
from src.workers.generic_worker import GenericShellWorker
from src.data.bloatware_data import BLOATWARE_DICT
from src.ui.widgets.system_tweaks import SystemTweaksWidget
from src.ui.widgets.ota_downloader import OTADownloaderWidget, HyperOSAppsWidget
from src.ui.widgets.app_manager import AppManagerWidget
from src.ui.widgets.fastboot_toolbox import FastbootToolboxWidget
# Internal classes used directly: XiaomiDebloaterWidget, XiaomiAdvancedWidget, XiaomiQuickToolsWidget

# Reuse GradientCard logic or import if shared (Defining here for simplicity/independence)
# Updated for stability check
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
        
        # Badge or Status (Optional)
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
        
        btn = QPushButton("Bắt đầu")
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
        border_color = "rgba(0,0,0,0.06)"
        
        if self.gradient_colors:
            bg_style = f"background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {self.gradient_colors[0]}, stop:1 {self.gradient_colors[1]});"
            border_color = "rgba(255,255,255,0.2)"
            
        hover_transform = "margin-top: -5px;" if hover else ""
        border_width = "2px" if hover else "1px"
        
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

class XiaomiHubWidget(QWidget):
    """
    Modern Hub for Xiaomi Tools
    Displays high-level tiles and device status.
    """
    switch_page = Signal(int) # Signal to parent (index)

    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add ScrollArea because outer scroll was removed
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(25)

        # 1. Hero Banner
        self.hero = QFrame()
        self.hero.setFixedHeight(220)
        self.hero.setObjectName("HubHero")
        self.hero.setStyleSheet(f"""
            #HubHero {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {ThemeManager.COLOR_ACCENT}, stop:1 #6A11CB);
                border-radius: 24px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        hero_layout = QHBoxLayout(self.hero)
        hero_layout.setContentsMargins(40, 0, 40, 0)
        
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignVCenter)
        
        welcome_lbl = QLabel("Xiaomi Turbo Suite")
        welcome_lbl.setStyleSheet("font-size: 32px; font-weight: 800; color: white;")
        
        desc_lbl = QLabel("Tận dụng tối đa sức mạnh thiết bị MIUI/HyperOS của bạn.")
        desc_lbl.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.8); margin-top: 8px;")
        
        text_layout.addWidget(welcome_lbl)
        text_layout.addWidget(desc_lbl)
        hero_layout.addLayout(text_layout)
        hero_layout.addStretch()
        
        # Quick Optimization Button
        scan_btn = QPushButton(" ⚡  Quét Hệ Thống")
        scan_btn.setFixedSize(200, 56)
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #2575FC;
                border-radius: 24px;
                font-weight: 800;
                font-size: 15px;
            }
            QPushButton:hover {
                background: #f8f9fa;
            }
        """)
        hero_layout.addWidget(scan_btn)
        
        layout.addWidget(self.hero)

        # 2. Main Services Grid
        grid_container = QWidget()
        self.grid = QGridLayout(grid_container)
        self.grid.setSpacing(20)
        self.grid.setContentsMargins(0, 0, 0, 0)

        # Service Tiles
        self.add_tile("Gỡ Rác & Tối Ưu (Debloater)", "Quét và gỡ bỏ ứng dụng rác, app thừa.", "🗑️", 1, ["#FF9A9E", "#FECFEF"])
        self.add_tile("Tiện Ích Nhanh (Quick Tools)", "FPS, 90Hz, Dark Mode, Brevent.", "✨", 2, ["#a18cd1", "#fbc2eb"])
        self.add_tile("Tính Năng Nâng Cao (Advanced)", "Chặn Update, Skip Setup, Region.", "⚙️", 3, ["#84fab0", "#8fd3f4"])
        self.add_tile("Hiệu Năng (Tweaks)", "Animation, SetEdit, 120Hz.", "🚀", 5, ["#fccb90", "#d57eeb"])
        self.add_tile("Quản Lý ROM & Apps", "Tải ROM HyperOS, App Gốc.", "☁️", 4, ["#e0c3fc", "#8ec5fc"])
        self.add_tile("Kho Ứng Dụng (Store)", "Tải APK/XAPK từ kho online.", "🛍️", 7, ["#ff9a9e", "#fecfef"]) 
        self.add_tile("Công Cụ Fastboot", "Flash ROM, Unlock, Format.", "🛠️", 6, ["#43e97b", "#38f9d7"])

        layout.addWidget(grid_container)
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def add_tile(self, title, desc, icon, index, colors):
        card = ModernCard(title, desc, icon, lambda: self.switch_page.emit(index), gradient_colors=colors)
        row = (index - 1) // 2
        col = (index - 1) % 2
        self.grid.addWidget(card, row, col)



class XiaomiBaseWidget(QWidget):
    """Base widget with shared helper methods"""
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.opt_worker = None
        self.worker = None
        
    def show_error(self, title, message):
        # Use LogManager instead of Popup
        LogManager.log(title, message, "error")
        
        # Smart Alert for Security Permission
        if "Bảo Mật" in title or "Security" in title:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(title)
            # Strip markdown for MessageBox
            clean_msg = message.replace("**", "").replace("`", "")
            msg.setText(clean_msg)
            
            btn_open = msg.addButton("Mở Cài đặt Developer ⚙️", QMessageBox.ActionRole)
            msg.addButton("Đóng", QMessageBox.RejectRole)
            msg.exec()
            
            if msg.clickedButton() == btn_open:
                try:
                    self.adb.open_developer_options()
                    LogManager.log("System", "Đã gửi lệnh mở Cài đặt nhà phát triển", "info")
                except Exception as e:
                    LogManager.log("Error", f"Không thể mở cài đặt: {e}", "error")
    
    def check_device(self, status_label):
        """Helper to update a status label with device info"""
        if not self.adb.current_device:
            status_label.setText("🚫 Chưa kết nối thiết bị")
            self.setEnabled(False)
            return

        try:
            # Use get_detailed_system_info (returns dict) instead of get_device_info
            info = self.adb.get_detailed_system_info()
            
            # Use dictionary .get() access
            brand = info.get('device_friendly_name') or self.adb.shell("getprop ro.product.brand").strip()
            model = info.get('model') or self.adb.shell("getprop ro.product.model").strip()
            
            status_label.setText(f"✅ Đã kết nối: {brand} | {model}")
            self.setEnabled(True)
            
            # Optional: Check Xiaomi ID compatibility logic if needed
            # manufacturer = info.get('manufacturer', '').lower()
            # ...
            
        except Exception as e:
            
            is_xiaomi_brand = any(x in brand or x in manufacturer for x in xiaomi_ids)
            is_xiaomi_os = bool(info.miui_version or info.hyperos_version)
            
            if is_xiaomi_brand or is_xiaomi_os:
                text = f"✅ Đã kết nối: {info.model}"
                if info.hyperos_version:
                    if info.hyperos_version.startswith("OS3"):
                        text = f"✅ Đã kết nối: Xiaomi HyperOS 3 ({info.hyperos_version})"
                    else:
                        text = f"✅ Đã kết nối: Xiaomi HyperOS ({info.hyperos_version})"
                elif info.miui_version:
                    text = f"✅ Đã kết nối: MIUI ({info.miui_version})"
                status_label.setText(text)
                self.setEnabled(True)
            else:
                status_label.setText(f"⛔ Thiết bị {info.model} không được hỗ trợ (Chỉ dành cho Xiaomi)")
                self.setEnabled(False)
        except Exception as e:
            status_label.setText(f"❓ Lỗi đọc thông tin: {str(e)}")
            # self.setEnabled(False) # Don't disable completely on read error, allow retry
            self.setEnabled(True) 
            
    def show_status_dialog(self, status):
        msg = "<b>Trạng thái Ngôn ngữ & Vùng hiện tại:</b><br><br>"
        for k, v in status.items():
            color = "#2ecc71" if "VN" in v or "vi" in v else "#e74c3c"
            msg += f"<b>{k}:</b> <span style='color:{color}'>{v}</span><br>"
        msg += "<br><i>Vui lòng Khởi động lại nếu các thông số đã đúng nhưng chưa áp dụng.</i>"
        QMessageBox.information(self, "Kiểm tra Hệ thống", msg)

class AppItemCard(QFrame):
    """Modern Card for a single app in Debloater"""
    toggled = Signal(bool, str)

    def __init__(self, app_name, package_name="", category=""):
        super().__init__()
        self.app_name = app_name
        self.package_name = package_name or app_name
        
        self.setObjectName("AppItemCard")
        self.setStyleSheet(f"""
            #AppItemCard {{
                background: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.05);
            }}
            #AppItemCard:hover {{
                border: 1px solid {ThemeManager.COLOR_ACCENT}50;
                background: rgba(255,255,255,0.8);
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        # Icon / Initial
        self.icon_lbl = QLabel(app_name[0].upper())
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setFixedSize(40, 40)
        self.icon_lbl.setStyleSheet(f"""
            background: {ThemeManager.COLOR_ACCENT}15;
            color: {ThemeManager.COLOR_ACCENT};
            border-radius: 10px;
            font-weight: 800;
            font-size: 18px;
        """)
        layout.addWidget(self.icon_lbl)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.name_lbl = QLabel(app_name)
        self.name_lbl.setStyleSheet(f"font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 14px; background:transparent;")
        
        self.pkg_lbl = QLabel(self.package_name)
        self.pkg_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 11px; background:transparent;")
        
        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(self.pkg_lbl)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Checkbox
        self.cb = QCheckBox()
        self.cb.setCursor(Qt.PointingHandCursor)
        self.cb.setFixedSize(24, 24)
        self.cb.stateChanged.connect(lambda s: self.toggled.emit(s == 2, self.package_name))
        
        theme = ThemeManager.get_theme()
        self.cb.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border: 2px solid {theme['COLOR_BORDER']};
                border-radius: 6px;
                background: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: {ThemeManager.COLOR_ACCENT};
                border-color: {ThemeManager.COLOR_ACCENT};
            }}
        """)
        layout.addWidget(self.cb)
    
    def isChecked(self):
        return self.cb.isChecked()
    
    def setChecked(self, checked):
        self.cb.setChecked(checked)

class XiaomiDebloaterWidget(XiaomiBaseWidget):
    """REDESIGNED: Widget for removing bloatware using Modern Cards"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.app_cards = {}
        self.setup_ui()
        # self.check_device(self.status_label) # Deferred to refresh_state

    def refresh_state(self):
        """Called when widget becomes visible"""
        self.check_device(self.status_label)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Upper info row
        header = QHBoxLayout()
        header.setContentsMargins(20, 10, 20, 0)
        
        self.status_label = QLabel("Đang kiểm tra...")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600;")
        header.addWidget(self.status_label)
        
        # Add Refresh Button
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(32, 32)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setToolTip("Làm mới trạng thái")
        btn_refresh.clicked.connect(lambda: self.check_device(self.status_label))
        header.addWidget(btn_refresh)
        
        header.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm ứng dụng...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(ThemeManager.get_input_style() + "padding-left: 10px;")
        self.search_input.textChanged.connect(self.filter_apps)
        header.addWidget(self.search_input)
        
        layout.addLayout(header)
        
        # Main List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignTop)

        # Build App Cards from Data
        from src.data.bloatware_data import BLOATWARE_DICT
        for category, apps in BLOATWARE_DICT.items():
            cat_lbl = QLabel(category.upper())
            cat_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_SECONDARY}; margin-top: 15px; margin-left: 5px;")
            self.content_layout.addWidget(cat_lbl)
            
            for app in apps:
                card = AppItemCard(app)
                self.content_layout.addWidget(card)
                self.app_cards[app] = card
        
        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        
        # Bottom Actions Bar
        actions_bar = QFrame()
        actions_bar.setFixedHeight(80)
        actions_bar.setObjectName("ActionsBar")
        actions_bar.setStyleSheet(f"""
            #ActionsBar {{
                background: {ThemeManager.COLOR_GLASS_WHITE};
                border-top: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        actions_layout = QHBoxLayout(actions_bar)
        actions_layout.setContentsMargins(30, 0, 30, 0)
        
        self.stats_lbl = QLabel("0 ứng dụng được chọn")
        self.stats_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600;")
        actions_layout.addWidget(self.stats_lbl)
        
        actions_layout.addStretch()
        
        btn_clean = QPushButton("🗑️ Gỡ bỏ ngay")
        btn_clean.setFixedSize(180, 48)
        btn_clean.setCursor(Qt.PointingHandCursor)
        btn_clean.setStyleSheet(ThemeManager.get_button_style("danger"))
        btn_clean.clicked.connect(self.start_debloat)
        actions_layout.addWidget(btn_clean)
        
        layout.addWidget(actions_bar)

    def filter_apps(self, text):
        search_text = text.lower()
        for app_name, card in self.app_cards.items():
            match = search_text in app_name.lower() or search_text in card.package_name.lower()
            card.setVisible(match)
            
    def start_debloat(self):
        selected = [app for app, card in self.app_cards.items() if card.isChecked()]
        if not selected:
            LogManager.log("Cảnh báo", "Vui lòng chọn ít nhất một ứng dụng", "warning")
            return
            
        confirm = QMessageBox.warning(
            self, "Xác nhận",
            f"Bạn sắp gỡ bỏ {len(selected)} ứng dụng rác.\nLưu ý: Một số app hệ thống quan trọng có thể gây treo logo if gỡ nhầm.\nBạn có chắc chắn?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.opt_worker = DebloatWorker(self.adb, selected)
            self.opt_worker.progress.connect(lambda m: LogManager.log("Debloater", m, "info"))
            self.opt_worker.start()
            
    def reset(self):
        self.check_device(self.status_label)
        for card in self.app_cards.values():
            card.setChecked(False)
        self.stats_lbl.setText("0 ứng dụng được chọn")


class XiaomiQuickToolsWidget(XiaomiBaseWidget):
    """Widget for quick optimizations"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(20)
        
        # Animation Card
        card_anim = ModernCard(
            "Tăng Tốc Hiệu Ứng", 
            "Giảm thời gian chuyển cảnh hệ thống (0.5x) giúp cảm giác mượt mà hơn.", 
            "🐇", 
            self.optimize_animations,
            gradient_colors=["#4facfe", "#00f2fe"]
        )
        grid.addWidget(card_anim, 0, 0)
        
        # Smart Blur Card
        card_blur = ModernCard(
            "Smart Blur (Tự động)", 
            "Tự động bật độ mờ Control Center đẹp nhất dựa trên RAM của máy.", 
            "💧",
            self.run_smart_blur,
            gradient_colors=["#4facfe", "#00f2fe"]
        )
        grid.addWidget(card_blur, 0, 1)
        
        # Stacked Recent Card (HyperOS 2)
        card_stack = ModernCard(
            "HyperOS 2 Đa nhiệm Xếp chồng",
            "Kích hoạt giao diện đa nhiệm kiểu Stack (iOS). Cần HyperOS Launcher mới nhất.",
            "📚",
            self.run_hyperos_stacked_recent,
            gradient_colors=["#a18cd1", "#fbc2eb"]
        )
        grid.addWidget(card_stack, 1, 0)
        
        # Expert Optimization Card
        card_expert = ModernCard(
            "Tối Ưu Chuyên Sâu (Expert)",
            "Tăng tốc animations, tối ưu hóa kernel và compiler cho HyperOS 3 / Android 16.",
            "💎",
            self.run_expert_optimization,
            gradient_colors=["#f093fb", "#f5576c"]
        )
        grid.addWidget(card_expert, 1, 1)

        # ART Tuning Card
        card_art = ModernCard(
            "Tăng Tốc Ứng Dụng (ART)",
            "Ép hệ thống biên dịch lại ứng dụng sang mã máy (speed) để phản hồi tức thì.",
            "🔥",
            self.run_art_tuning,
            gradient_colors=["#84fab0", "#8fd3f4"]
        )
        grid.addWidget(card_art, 2, 0)
        
        # New Social App Fix Card
        card_social = ModernCard(
            "Fix Thông Báo & Pin (Social)",
            "Chạy nền & Không giới hạn pin cho: Facebook, Messenger, Zalo, MicroG.",
            "🔔",
            self.run_fix_social_notifications,
            gradient_colors=["#ff9a9e", "#fecfef"]
        )
        grid.addWidget(card_social, 2, 1)

        # Row 3: Visual Tweaks
        card_nolabel = ModernCard(
            "Ẩn Tên Ứng Dụng (No Word)",
            "Ẩn toàn bộ tên ứng dụng ngoài màn hình chính (Chỉ hiện Icon). Reset máy để áp dụng.",
            "📝",
            self.run_remove_app_label,
            gradient_colors=["#a18cd1", "#fbc2eb"]
        )
        grid.addWidget(card_nolabel, 3, 0)

        card_blur = ModernCard(
            "Kích Hoạt Blur (Device Level)",
            "Ép buộc bật hiệu ứng Blur (Làm mờ) cho Folder và Đa nhiệm trên máy yếu.",
            "💧",
            self.run_force_blur_level,
            gradient_colors=["#84fab0", "#8fd3f4"]
        )
        grid.addWidget(card_blur, 3, 1)

        # Row 4: Unlock Features
        card_superwall = ModernCard(
            "Mở Khóa Super Wallpaper",
            "Mở khóa tính năng Siêu hình nền (Cần cài đặt APK SuperWallpaper trước).",
            "🪐",
            self.run_unlock_super_wallpaper,
            gradient_colors=["#f093fb", "#f5576c"]
        )
        grid.addWidget(card_superwall, 4, 0)

        card_record = ModernCard(
            "Ghi Âm Cuộc Gọi (Native)",
            "Kích hoạt ghi âm cuộc gọi gốc (Gỡ bỏ Overlay chặn của Google/Global ROM).",
            "📞",
            self.run_enable_call_recording,
            gradient_colors=["#fa709a", "#fee140"]
        )
        grid.addWidget(card_record, 4, 1)

        
        grid.setRowStretch(6, 1) # Push to top
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def optimize_animations(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "animations")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Animations", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_fix_social_notifications(self):
        """Fix notifications for social apps"""
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
            
        self.opt_worker = OptimizationWorker(self.adb, "fix_social_notifications")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Fix Social", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_smart_blur(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "smart_blur")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Smart Blur", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_remove_app_label(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "remove_app_label")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("No Label", msg, "info"))
        self.opt_worker.start()

    def run_force_blur_level(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "force_blur_level")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Force Blur", msg, "info"))
        self.opt_worker.start()

    def run_unlock_super_wallpaper(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "unlock_super_wallpaper")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Super Wallpaper", msg, "info"))
        self.opt_worker.start()

    def run_enable_call_recording(self):
        confirm = QMessageBox.question(
            self, "Xác nhận", 
            "Lệnh này sẽ gỡ bỏ lớp phủ (overlay) của MIUI Global/Google nhằm khôi phục trình gọi điện gốc (hoặc tính năng bị ẩn).\nTiếp tục?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.opt_worker and self.opt_worker.isRunning():
                LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
                return
            self.opt_worker = OptimizationWorker(self.adb, "enable_call_recording")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Call Recording", msg, "info"))
            self.opt_worker.start()

    def run_hyperos_stacked_recent(self):
        try:
            info = self.adb.get_detailed_system_info()
            android_ver = 0
            
            # Use info.get() logic
            av_str = info.get('android_version', '0')
            if av_str and av_str != "Unknown":
                try:
                    android_ver = int(str(av_str).split('.')[0])  
                except: pass
            
            if android_ver < 14:
                LogManager.log("Compat", f"Yêu cầu Android 14+ (Hiện tại: {av_str})", "warning")
                return

            if 'HyperOS' not in info.get('os_version', ''):
                 LogManager.log("Compat", "Chỉ hỗ trợ Xiaomi HyperOS.", "warning")
                 return

            brand = self.adb.shell("getprop ro.product.brand").strip().lower()
            if "poco" in brand:
                 LogManager.log("Compat", "POCO Launcher chưa được hỗ trợ chính thức.", "warning")
                 # return # Allow POCO to try if they want? No, keep restricted if risky. 
                 return
                 
        except Exception as e:
            LogManager.log("System Check", f"Lỗi: {e}", "error")
            return

        # Check Launcher Version
        try:
            cmd = "dumpsys package com.miui.home | grep versionName"
            output = self.adb.shell(cmd).strip()
            
            if "versionName=" in output:
                version_str = output.split("versionName=")[1].strip().split()[0]
                
                # Simple parser for major.minor...
                import re
                def parse_version(v_str):
                    return [int(n) for n in re.findall(r'\d+', v_str)]

                current_ver = parse_version(version_str)
                # Requirement: RELEASE-4.39.14.8145-05301748 (Example old) vs HyperOS new
                # HyperOS 2 target: RELEASE-6.01.03.1924
                required_ver = parse_version("RELEASE-6.01.03.1924")
                
                # Compare only first 3 segments for safety? No, compare list.
                if current_ver < required_ver:
                     from PySide6.QtGui import QDesktopServices
                     from PySide6.QtCore import QUrl
                     
                     msg = QMessageBox(self)
                     msg.setIcon(QMessageBox.Warning)
                     msg.setWindowTitle("Phiên bản Launcher cũ")
                     msg.setText(f"Tính năng này yêu cầu HyperOS Launcher mới nhất.\n\nHiện tại: {version_str}\nYêu cầu: RELEASE-6.01.03+\n\nBạn có muốn tải bản mới không?")
                     
                     btn_download = msg.addButton("Tải bản cập nhật (Web) 🌐", QMessageBox.ActionRole)
                     btn_force = msg.addButton("Ép chạy (Can thiệp sâu) ⚡", QMessageBox.ActionRole)
                     btn_cancel = msg.addButton("Hủy bỏ", QMessageBox.RejectRole)
                     
                     msg.exec()
                     
                     if msg.clickedButton() == btn_download:
                         QDesktopServices.openUrl(QUrl("https://hyperosupdates.com/apps/com.miui.home"))
                         return
                     elif msg.clickedButton() == btn_force:
                         LogManager.log("Deep Action", "Đang kích hoạt can thiệp sâu (Force Mode)...", "warning")
                         # Fall through to execution
                     else:
                         return
            else:
                 # Version check failed or not found
                 from PySide6.QtGui import QDesktopServices
                 from PySide6.QtCore import QUrl
                 
                 msg = QMessageBox(self)
                 msg.setIcon(QMessageBox.Warning)
                 msg.setWindowTitle("Không thể kiểm tra phiên bản")
                 msg.setText(f"Không thể xác định phiên bản Launcher hiện tại.\n\nYêu cầu: RELEASE-6.01.03+\nĐể an toàn, bạn nên kiểm tra cập nhật trước.")
                 
                 btn_download = msg.addButton("Tải bản cập nhật 🌐", QMessageBox.ActionRole)
                 btn_force = msg.addButton("Ép chạy (Force) ⚡", QMessageBox.ActionRole)
                 btn_cancel = msg.addButton("Hủy bỏ", QMessageBox.RejectRole)
                 
                 msg.exec()
                 
                 if msg.clickedButton() == btn_download:
                      QDesktopServices.openUrl(QUrl("https://hyperosupdates.com/apps/com.miui.home"))
                      return
                 elif msg.clickedButton() == btn_force:
                      LogManager.log("Deep Action", "Đang kích hoạt can thiệp sâu (Unknown Version)...", "warning")
                 else:
                      return
                 
        except Exception as e:
             LogManager.log("Debug", f"Lỗi check version: {e} (Tiếp tục xử lý...)", "warning")

        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return

        self.opt_worker = OptimizationWorker(self.adb, "stacked_recent")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Stacked Recent", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_expert_optimization(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return

        self.opt_worker = OptimizationWorker(self.adb, "expert_optimize")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Expert Opt", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_art_tuning(self):
        # Confirm because it takes time
        confirm = QMessageBox.question(
            self, "Xác nhận", 
            "Quá trình này có thể mất 5-10 phút và làm nóng máy nhẹ. Bạn có muốn tiếp tục?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if self.opt_worker and self.opt_worker.isRunning():
                LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
                return

            self.opt_worker = OptimizationWorker(self.adb, "art_tuning")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("ART Tuning", msg, "info"))
            self.opt_worker.error_occurred.connect(self.show_error)
            self.opt_worker.start()


            self.opt_worker.start()



class XiaomiAdvancedWidget(XiaomiBaseWidget):
    """Widget for advanced system tweaks"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        main_grid = QGridLayout(content)
        main_grid.setSpacing(20)
        
        # --- 1. Display ---
        group_display = QGroupBox("Màn hình & Hiển thị")
        group_display.setStyleSheet(f"font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 14px;")
        grid_display = QGridLayout(group_display)
        grid_display.setSpacing(15)

        card_refresh = ModernCard(
            "Chỉnh Tần Số Quét (Hz)", "Tùy chỉnh tần số quét màn hình (60/90/120/144Hz) hoặc Auto.", "⚡",
            self.run_force_refresh_rate, gradient_colors=["#f83600", "#f9d423"]
        )
        grid_display.addWidget(card_refresh, 0, 0)

        card_fps = ModernCard(
            "Hiện FPS (Power Monitor)", "Hiển thị tần số quét/FPS trực tiếp trên màn hình.", "📈",
            self.run_show_fps, gradient_colors=["#fc4a1a", "#f7b733"]
        )
        grid_display.addWidget(card_fps, 0, 1)

        card_dpi = ModernCard(
            "Đổi Độ Phân Giải (DPI)", "Thay đổi mật độ hiển thị (DPI) để icon to/nhỏ tùy ý.", "📱",
            self.run_set_dpi, gradient_colors=["#1d976c", "#93f9b9"]
        )
        grid_display.addWidget(card_dpi, 1, 0)

        card_dark = ModernCard(
            "Dark Mode Toàn Hệ Thống", "Ép chế độ tối cho tất cả ứng dụng (Facebook, Shopee...).", "🌙",
            self.run_force_dark_mode, gradient_colors=["#434343", "#000000"]
        )
        grid_display.addWidget(card_dark, 1, 1)
        main_grid.addWidget(group_display, 0, 0)
        
        # --- 2. System ---
        group_system = QGroupBox("Hệ thống & Tinh chỉnh")
        group_system.setStyleSheet(f"font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 14px; margin-top: 10px;")
        grid_system = QGridLayout(group_system)
        grid_system.setSpacing(15)

        card_ota = ModernCard(
            "Chặn Cập Nhật (Disable OTA)", "Tắt vĩnh viễn thông báo cập nhật hệ thống & chặn tải về bản mới.", "🛑",
            self.run_disable_ota, gradient_colors=["#ff416c", "#ff4b2b"]
        )
        grid_system.addWidget(card_ota, 0, 0)
        
        card_skip = ModernCard(
            "Bỏ qua Setup Wizard", "Vào thẳng màn hình chính sau khi Reset (Bypass FRP/Wifi).", "⏩",
            self.run_skip_setup, gradient_colors=["#11998e", "#38ef7d"]
        )
        grid_system.addWidget(card_skip, 0, 1)

        card_nav = ModernCard(
            "Ẩn Thanh Điều Hướng", "Ẩn thanh vuốt ngang bên dưới để full màn hình.", "↔️",
            self.run_hide_nav_bar, gradient_colors=["#00c6ff", "#0072ff"]
        )
        grid_system.addWidget(card_nav, 1, 0)
        main_grid.addWidget(group_system, 1, 0)

        # --- 3. Language ---
        group_lang = QGroupBox("Ngôn ngữ & Khu vực (Language)")
        group_lang.setStyleSheet(f"font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 14px; margin-top: 10px;")
        grid_lang = QGridLayout(group_lang)
        grid_lang.setSpacing(15)
        
        card_vn = ModernCard(
            "Cài Tiếng Việt (VN)", "Ép buộc ngôn ngữ hệ thống sang Tiếng Việt (vi-VN) qua ADB. Yêu cầu khởi động lại.", "🇻🇳", 
            self.run_set_vietnamese, gradient_colors=["#ee0979", "#ff6a00"]
        )
        grid_lang.addWidget(card_vn, 0, 0)
        
        card_region = ModernCard(
            "Fix Region EU_VN", "Sửa lỗi định dạng vùng, ngày giờ và quốc gia cho ROM EU/Convert.", "🌍",
            self.run_fix_eu_vn, gradient_colors=["#11998e", "#38ef7d"]
        )
        grid_lang.addWidget(card_region, 0, 1)
        
        btn_verify = QPushButton("🔍 Kiểm tra cài đặt hiện tại")
        btn_verify.setCursor(Qt.PointingHandCursor)
        btn_verify.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {ThemeManager.COLOR_ACCENT}; border: 1px solid {ThemeManager.COLOR_ACCENT}; border-radius: 6px; padding: 5px 15px; }} QPushButton:hover {{ background-color: {ThemeManager.COLOR_ACCENT}; color: white; }}")
        btn_verify.clicked.connect(self.run_verify_status)
        grid_lang.addWidget(btn_verify, 1, 0, 1, 2)

        main_grid.addWidget(group_lang, 2, 0)
        main_grid.setRowStretch(2, 1)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def run_force_refresh_rate(self):
        from PySide6.QtWidgets import QInputDialog
        items = ["Mặc định (Auto)", "60Hz (Tiết kiệm pin)", "90Hz (Cân bằng)", "120Hz (Mượt mà)", "144Hz (Gaming)"]
        item, ok = QInputDialog.getItem(self, "Chỉnh Tần Số Quét", "Chọn mức làm tươi màn hình mong muốn:", items, 0, False)
        if ok and item:
            hz = 0
            if "60Hz" in item: hz = 60
            elif "90Hz" in item: hz = 90
            elif "120Hz" in item: hz = 120
            elif "144Hz" in item: hz = 144
            if self.opt_worker and self.opt_worker.isRunning():
                LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
                return
            self.opt_worker = OptimizationWorker(self.adb, "force_refresh_rate")
            self.opt_worker.refresh_rate = hz
            self.opt_worker.progress.connect(lambda m: LogManager.log("Refresh Rate", m, "info"))
            self.opt_worker.start()

    def run_show_fps(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("FPS / Refresh Rate Monitor")
        msg.setText("Bật/Tắt công cụ theo dõi tần số quét màn hình.\n\nNếu chế độ Auto không hoạt động, hãy chọn 'Mở Cài Đặt' để bật thủ công.")
        btn_on = msg.addButton("Bật FPS (Auto)", QMessageBox.ActionRole)
        btn_off = msg.addButton("Tắt FPS", QMessageBox.ActionRole)
        btn_manual = msg.addButton("Mở Cài Đặt (Manual)", QMessageBox.ActionRole)
        msg.addButton("Hủy", QMessageBox.RejectRole)
        msg.exec()

        if msg.clickedButton() == btn_on: task = "show_fps_on"
        elif msg.clickedButton() == btn_off: task = "show_fps_off"
        elif msg.clickedButton() == btn_manual: task = "open_dev_options"
        else: return

        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return

        self.opt_worker = OptimizationWorker(self.adb, task)
        self.opt_worker.progress.connect(lambda m: LogManager.log("FPS Monitor", m, "info"))
        self.opt_worker.start()

    def run_set_dpi(self):
        from PySide6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getInt(self, "Đổi DPI Màn hình", "Nhập giá trị DPI mong muốn (Ví dụ: 392, 440, 480...)\nNhập 0 để Reset về mặc định.", value=0, minValue=0, maxValue=999)
        if ok:
            if self.opt_worker and self.opt_worker.isRunning():
                LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
                return
            self.opt_worker = OptimizationWorker(self.adb, "set_dpi")
            self.opt_worker.dpi_value = val
            self.opt_worker.progress.connect(lambda m: LogManager.log("DPI Modifier", m, "info"))
            self.opt_worker.start()

    def run_force_dark_mode(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Chế độ Tối (Dark Mode)")
        msg.setText("Cài đặt ép buộc Dark Mode toàn hệ thống:")
        btn_on = msg.addButton("Bật (Force Dark)", QMessageBox.ActionRole)
        btn_off = msg.addButton("Tắt / Mặc định", QMessageBox.ActionRole)
        msg.addButton("Hủy", QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_on: task = "force_dark_mode_on"
        elif msg.clickedButton() == btn_off: task = "force_dark_mode_off"
        else: return
        
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
            
        self.opt_worker = OptimizationWorker(self.adb, task)
        self.opt_worker.progress.connect(lambda m: LogManager.log("Dark Mode", m, "info"))
        self.opt_worker.start()

    def run_disable_ota(self):
        reply = QMessageBox.question(self, "Chặn Cập Nhật", "Bạn có muốn chặn vĩnh viễn tính năng Cập nhật Hệ thống (OTA)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.opt_worker and self.opt_worker.isRunning():
                LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
                return
            self.opt_worker = OptimizationWorker(self.adb, "disable_ota")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Disable OTA", msg, "info"))
            self.opt_worker.start()

    def run_skip_setup(self):
        reply = QMessageBox.question(self, "Xác nhận", "Tiện ích này giúp bỏ qua các bước thiết lập ban đầu sau khi Reset máy.\nBạn có muốn tiếp tục?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.opt_worker and self.opt_worker.isRunning():
                LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
                return
            self.opt_worker = OptimizationWorker(self.adb, "skip_setup")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Skip Setup", msg, "info"))
            self.opt_worker.error_occurred.connect(self.show_error)
            self.opt_worker.start()

    def run_hide_nav_bar(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Thanh Điều Hướng")
        msg.setText("Cài đặt hiển thị thanh điều hướng (Navigation Bar):")
        btn_hide = msg.addButton("Ẩn (Full Screen)", QMessageBox.ActionRole)
        btn_show = msg.addButton("Hiện (Mặc định)", QMessageBox.ActionRole)
        msg.addButton("Hủy", QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_hide: task = "hide_nav_on"
        elif msg.clickedButton() == btn_show: task = "hide_nav_off"
        else: return
        
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
            
        self.opt_worker = OptimizationWorker(self.adb, task)
        self.opt_worker.progress.connect(lambda m: LogManager.log("Nav Bar", m, "info"))
        self.opt_worker.start()

    def run_set_vietnamese(self):
        confirm = QMessageBox.question(self, "Xác nhận", "Thao tác này sẽ gửi lệnh thay đổi ngôn ngữ hệ thống sang vi-VN.\nThiết bị cần KHỞI ĐỘNG LẠI để áp dụng.\n\nBạn có muốn tiếp tục?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            if self.opt_worker and self.opt_worker.isRunning():
                LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
                return
            self.opt_worker = OptimizationWorker(self.adb, "set_vietnamese")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Language", msg, "info"))
            self.opt_worker.error_occurred.connect(self.show_error)
            self.opt_worker.start()

    def run_fix_eu_vn(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "fix_eu_vn")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Region Fix", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_verify_status(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "check_status")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("System Check", msg, "info"))
        self.opt_worker.result_ready.connect(self.show_status_dialog)
        self.opt_worker.start()


class XiaomiOptimizerWidget(XiaomiBaseWidget):
    """
    Main Wrapper for Xiaomi Tools (Legacy Support)
    Aggregates the modular widgets into the original tabbed view.
    """
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.setup_ui()
        
    def setup_ui(self):
        # Main Layout (Stack + Nav Overlay)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Navigation Bar (Back Button + Title) - Hidden on Hub
        # 1. Navigation Bar (Back Button + Title) - Hidden on Hub
        self.nav_bar = QFrame()
        self.nav_bar.setFixedHeight(50)
        self.nav_bar.setObjectName("OptimizerNavBar")
        self.nav_bar.setStyleSheet(f"""
            #OptimizerNavBar {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-bottom: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(15, 5, 15, 5)
        nav_layout.setSpacing(15)
        
        # Back Button
        btn_back = QPushButton("⬅ Quay lại Hub")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.switch_page(0))
        btn_back.setStyleSheet("""
            QPushButton {
                background: transparent; border: 1px solid #ccc; 
                border-radius: 12px; padding: 6px 16px; font-weight: bold; color: #333;
            }
            QPushButton:hover { background: rgba(0,0,0,0.05); }
        """)
        nav_layout.addWidget(btn_back)
        
        # Title
        self.page_title = QLabel("Xiaomi Turbo Suite")
        self.page_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        nav_layout.addWidget(self.page_title)
        
        nav_layout.addStretch()
        layout.addWidget(self.nav_bar)
        
        # 2. Content Stack
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Initialize Pages
        self.init_pages()
        
        # Initial State
        self.switch_page(0)

    def init_pages(self):
        # 0. Hub
        self.hub = XiaomiHubWidget(self.adb)
        self.hub.switch_page.connect(self.switch_page)
        self.stack.addWidget(self.hub)
        
        # 1. Debloater
        self.stack.addWidget(XiaomiDebloaterWidget(self.adb))
        
        # 2. Quick Tools
        self.stack.addWidget(XiaomiQuickToolsWidget(self.adb))
        
        # 3. Advanced
        self.stack.addWidget(XiaomiAdvancedWidget(self.adb))
        
        # 4. ROM & Apps
        self.stack.addWidget(OTADownloaderWidget(self.adb))
        
        # 5. Tweaks
        self.stack.addWidget(SystemTweaksWidget(self.adb))
        
        # 6. Fastboot
        self.stack.addWidget(FastbootToolboxWidget(self.adb))
        
        # 7. Apps
        self.stack.addWidget(HyperOSAppsWidget(self.adb))

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        
        # Determine Title
        titles = [
            "Xiaomi Turbo Hub", 
            "Gỡ Rác & Debloat", 
            "Tiện Ích Xiaomi", 
            "Tính Năng Nâng Cao", 
            "Tải ROM & Check OTA", 
            "Tối Ưu Hóa (Tweaks)",
            "Fastboot Toolkit", 
            "Kho Ứng Dụng (HyperOS)"
        ]
        
        current_title = titles[index] if 0 <= index < len(titles) else "Chi tiết"
        self.page_title.setText(f"|  {current_title}")
            
        # Toggle Nav Bar
        if index == 0:
            self.nav_bar.setVisible(False)
        if index == 0:
            self.nav_bar.setVisible(False)
        else:
            self.nav_bar.setVisible(True)
            
        # [AUTO-REFRESH] Trigger connection check on the target widget
        current_widget = self.stack.widget(index)
        if hasattr(current_widget, 'refresh_state'):
            current_widget.refresh_state()
        elif hasattr(current_widget, 'check_device') and hasattr(current_widget, 'status_label'):
             # Fallback if refresh_state not defined but check_device is
             current_widget.check_device(current_widget.status_label)

    def run_full_optimization(self):
        if self.opt_worker and self.opt_worker.isRunning():
            LogManager.log("System", "Một tiến trình tối ưu hóa khác đang chạy. Vui lòng đợi.", "warning")
            return
        self.opt_worker = OptimizationWorker(self.adb, "full_scan")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Optimization", msg, "info"))
        self.opt_worker.start()

