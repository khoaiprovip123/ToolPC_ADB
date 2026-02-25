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
    QListWidget, QListWidgetItem, QStackedWidget, QSizePolicy, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QGradient
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager
from src.ui.dialogs.confirmation_dialog import ConfirmationDialog

# Imports from refactored modules
from src.workers.debloat_worker import DebloatWorker
from src.workers.optimization_worker import OptimizationWorker
from src.workers.generic_worker import GenericShellWorker
from src.data.bloatware_data import BLOATWARE_DICT
from src.ui.widgets.ota_downloader import OTADownloaderWidget, HyperOSAppsWidget
from src.ui.widgets.fastboot_toolbox import FastbootToolboxWidget

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

        # Service Tiles (Consolidated Indexing)
        self.add_tile("Gỡ Rác & Tối Ưu (Debloater)", "Quét và gỡ bỏ ứng dụng rác, app thừa.", "🗑️", 1, ["#FF9A9E", "#FECFEF"])
        self.add_tile("Tối Ưu & Tinh Chỉnh (AIO)", "120Hz, Tắt OTA, Việt Hóa, Tối ưu ART Chuyên sâu.", "✨", 2, ["#a18cd1", "#fbc2eb"])
        self.add_tile("Quản Lý ROM & Apps", "Tải ROM HyperOS, App Gốc.", "☁️", 3, ["#e0c3fc", "#8ec5fc"])
        self.add_tile("Công Cụ Fastboot", "Flash ROM, Unlock, Format.", "🛠️", 4, ["#43e97b", "#38f9d7"])
        self.add_tile("Kho Ứng Dụng (Store)", "Tải APK/XAPK từ kho online.", "🛍️", 5, ["#ff9a9e", "#fecfef"]) 

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
        LogManager.log(title, message, "error")
        if "Bảo Mật" in title or "Security" in title:
            dlg = ConfirmationDialog(
                self, title=title, message="Lỗi quyền Bảo mật ADB",
                details=message.replace("**", "").replace("`", ""),
                confirm_text="Mở Cài đặt ⚙️", cancel_text="Đóng", warning_mode=True
            )
            if dlg.exec_() == QDialog.Accepted:
                try: self.adb.open_developer_options()
                except Exception as _e:

                    pass  # TODO: consider LogManager.log
    
    def check_device(self, status_label):
        if not self.adb.current_device:
            status_label.setText("🚫 Chưa kết nối thiết bị")
            self.setEnabled(False)
            return
        try:
            info = self.adb.get_detailed_system_info()
            brand = info.get('device_friendly_name') or self.adb.shell("getprop ro.product.brand").strip()
            model = info.get('model') or self.adb.shell("getprop ro.product.model").strip()
            status_label.setText(f"✅ Đã kết nối: {brand} | {model}")
            self.setEnabled(True)
        except Exception as _e:
            status_label.setText("❓ Lỗi đọc thông tin thiết bị")
            self.setEnabled(True)
            
    def show_status_dialog(self, status):
        msg = "<b>Trạng thái Ngôn ngữ & Vùng hiện tại:</b><br><br>"
        for k, v in status.items():
            color = "#2ecc71" if "VN" in v or "vi" in v else "#e74c3c"
            msg += f"<b>{k}:</b> <span style='color:{color}'>{v}</span><br>"
        msg += "<br><i>Vui lòng Khởi động lại nếu các thông số đã đúng nhưng chưa áp dụng.</i>"
        LogManager.log("Kiểm tra Hệ thống", msg, "info")

class AppItemCard(QFrame):
    """Modern dark glass card for a single app in Debloater"""
    toggled = Signal(bool, str)

    def __init__(self, app_name, package_name="", category=""):
        super().__init__()
        self.app_name = app_name
        self.package_name = package_name or app_name
        self._processed = False
        self.setObjectName("AppItemCard")
        self.setStyleSheet(f"""
            #AppItemCard {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 14px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
            #AppItemCard:hover {{
                border: 1px solid {ThemeManager.COLOR_ACCENT}60;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)
        
        # Icon circle
        self.icon_lbl = QLabel(app_name[0].upper())
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setFixedSize(40, 40)
        self.icon_lbl.setStyleSheet(f"""
            background: {ThemeManager.COLOR_ACCENT}15;
            color: {ThemeManager.COLOR_ACCENT};
            border-radius: 20px;
            font-weight: 800;
            font-size: 16px;
            border: 1px solid {ThemeManager.COLOR_ACCENT}30;
        """)
        layout.addWidget(self.icon_lbl)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        self.name_lbl = QLabel(app_name)
        self.name_lbl.setStyleSheet(f"font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.pkg_lbl = QLabel(self.package_name)
        self.pkg_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 11px;")
        info_layout.addWidget(self.name_lbl)
        info_layout.addWidget(self.pkg_lbl)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Status badge (hidden until processed)
        self.status_badge = QLabel("")
        self.status_badge.setFixedHeight(24)
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.hide()
        layout.addWidget(self.status_badge)
        
        # Checkbox
        self.cb = QCheckBox()
        self.cb.setCursor(Qt.PointingHandCursor)
        self.cb.setStyleSheet("""
            QCheckBox::indicator {
                width: 22px; height: 22px;
                border-radius: 6px;
                border: 2px solid rgba(128,128,128,0.4);
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background: #e74c3c;
                border: 2px solid #e74c3c;
                image: none;
            }
            QCheckBox::indicator:hover {
                border: 2px solid {ThemeManager.COLOR_ACCENT};
            }
        """)
        self.cb.stateChanged.connect(lambda s: self.toggled.emit(s == 2, self.package_name))
        layout.addWidget(self.cb)
    
    def isChecked(self): return self.cb.isChecked()
    def setChecked(self, checked): self.cb.setChecked(checked)
    
    def mark_processed(self, success, message=""):
        """Mark this card as processed after uninstall attempt"""
        self._processed = True
        self.cb.setChecked(False)
        self.cb.setEnabled(False)
        self.status_badge.show()
        if success:
            self.status_badge.setText("✓ Đã gỡ")
            self.status_badge.setStyleSheet("""
                color: #2ecc71; font-size: 11px; font-weight: 700;
                padding: 2px 10px; background: rgba(46,204,113,0.15);
                border-radius: 12px; border: none;
            """)
            self.icon_lbl.setStyleSheet("""
                background: rgba(46,204,113,0.15); color: #2ecc71;
                border-radius: 20px; font-weight: 800; font-size: 16px;
                border: 1px solid rgba(46,204,113,0.3);
            """)
        else:
            self.status_badge.setText("✗ Lỗi")
            self.status_badge.setStyleSheet("""
                color: #e74c3c; font-size: 11px; font-weight: 700;
                padding: 2px 10px; background: rgba(231,76,60,0.15);
                border-radius: 12px; border: none;
            """)
    
    def reset_state(self):
        """Reset card to original state"""
        self._processed = False
        self.cb.setEnabled(True)
        self.cb.setChecked(False)
        self.status_badge.hide()
        self.icon_lbl.setStyleSheet(f"""
            background: {ThemeManager.COLOR_ACCENT}15;
            color: {ThemeManager.COLOR_ACCENT};
            border-radius: 20px; font-weight: 800; font-size: 16px;
            border: 1px solid {ThemeManager.COLOR_ACCENT}30;
        """)

class XiaomiDebloaterWidget(XiaomiBaseWidget):
    """Widget for removing bloatware — Redesigned with batch select + visual feedback"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.app_cards = {}
        self._category_cards = {}  # category -> list of cards
        self._processing = False
        self._processed_results = {}  # package -> success bool
        self.setup_ui()

    def refresh_state(self): self.check_device(self.status_label)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ─── HEADER BAR ───
        header = QFrame()
        header.setStyleSheet("background: transparent;")
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(20, 10, 20, 10)
        
        self.status_label = QLabel("Đang kiểm tra...")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600; font-size: 12px;")
        header_l.addWidget(self.status_label)
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(32, 32)
        btn_refresh.setStyleSheet("background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; font-size: 14px;")
        btn_refresh.clicked.connect(lambda: self.check_device(self.status_label))
        header_l.addWidget(btn_refresh)
        header_l.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm ứng dụng...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(ThemeManager.get_input_style())
        self.search_input.textChanged.connect(self.filter_apps)
        header_l.addWidget(self.search_input)
        
        layout.addWidget(header)
        
        # ─── APP LIST ───
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 5, 20, 5)
        self.content_layout.setSpacing(8)
        self.content_layout.setAlignment(Qt.AlignTop)

        for category, apps in BLOATWARE_DICT.items():
            self._category_cards[category] = []
            
            # Category header with select button
            cat_row = QHBoxLayout()
            cat_lbl = QLabel(f"  {category.upper()}")
            cat_lbl.setStyleSheet(f"""
                font-size: 11px; font-weight: 800; 
                color: {ThemeManager.COLOR_TEXT_SECONDARY}; 
                margin-top: 12px; margin-bottom: 4px;
                letter-spacing: 0.5px;
            """)
            cat_row.addWidget(cat_lbl)
            
            count_badge = QLabel(f"{len(apps)}")
            count_badge.setFixedSize(24, 18)
            count_badge.setAlignment(Qt.AlignCenter)
            count_badge.setStyleSheet(f"""
                background: {ThemeManager.COLOR_ACCENT}15; color: {ThemeManager.COLOR_TEXT_SECONDARY};
                border-radius: 9px; font-size: 10px; font-weight: 700;
            """)
            cat_row.addWidget(count_badge)
            cat_row.addStretch()
            
            # Per-category select all
            btn_cat_sel = QPushButton("Chọn nhóm")
            btn_cat_sel.setCursor(Qt.PointingHandCursor)
            btn_cat_sel.setFixedHeight(22)
            btn_cat_sel.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {ThemeManager.COLOR_TEXT_SECONDARY};
                    border: none; font-size: 11px; font-weight: 500;
                    padding: 0 8px;
                }}
                QPushButton:hover {{ color: {ThemeManager.COLOR_ACCENT}; }}
            """)
            cat_name = category  # capture
            btn_cat_sel.clicked.connect(lambda checked=False, c=cat_name: self._toggle_category(c))
            cat_row.addWidget(btn_cat_sel)
            
            self.content_layout.addLayout(cat_row)
            
            for app in apps:
                card = AppItemCard(app)
                card.toggled.connect(self._on_card_toggled)
                self.content_layout.addWidget(card)
                self.app_cards[app] = card
                self._category_cards[category].append(card)
        
        self.content_layout.addSpacing(80)  # Space for bottom bar
        
        scroll.setWidget(self.content)
        layout.addWidget(scroll, 1)
        
        # ─── BOTTOM ACTION BAR ───
        actions_bar = QFrame()
        actions_bar.setFixedHeight(70)
        actions_bar.setObjectName("DebloatBar")
        actions_bar.setStyleSheet(f"""
            #DebloatBar {{
                background: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
                border-top: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        actions_layout = QHBoxLayout(actions_bar)
        actions_layout.setContentsMargins(24, 0, 24, 0)
        
        self.stats_lbl = QLabel("0 ứng dụng được chọn")
        self.stats_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px; font-weight: 600;")
        actions_layout.addWidget(self.stats_lbl)
        actions_layout.addStretch()
        
        self.btn_clean = QPushButton("🗑️ Gỡ bỏ ngay")
        self.btn_clean.setCursor(Qt.PointingHandCursor)
        self.btn_clean.setFixedSize(170, 44)
        self.btn_clean.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
                color: white; font-weight: 700; border-radius: 22px;
                border: none; font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6b6b, stop:1 #e74c3c);
            }}
            QPushButton:disabled {{
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.25);
            }}
        """)
        self.btn_clean.clicked.connect(self.start_debloat)
        actions_layout.addWidget(self.btn_clean)
        layout.addWidget(actions_bar)

    def _on_card_toggled(self, checked, package):
        """Update counter when checkbox toggled"""
        count = sum(1 for c in self.app_cards.values() if c.isChecked())
        self.stats_lbl.setText(f"{count} ứng dụng được chọn")
        if count > 0:
            self.stats_lbl.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: 700;")
        else:
            self.stats_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px; font-weight: 600;")

    def _set_all_checked(self, checked):
        for card in self.app_cards.values():
            if card.cb.isEnabled():
                card.setChecked(checked)

    def _toggle_category(self, category):
        cards = self._category_cards.get(category, [])
        # Toggle: if any unchecked → check all, else uncheck all
        any_unchecked = any(not c.isChecked() and c.cb.isEnabled() for c in cards)
        for c in cards:
            if c.cb.isEnabled():
                c.setChecked(any_unchecked)

    def filter_apps(self, text):
        for name, card in self.app_cards.items():
            card.setVisible(text.lower() in name.lower() or text.lower() in card.package_name.lower())
            
    def start_debloat(self):
        if self._processing:
            return
        selected = [app for app, card in self.app_cards.items() if card.isChecked()]
        if not selected:
            LogManager.log("Debloater", "⚠ Chưa chọn ứng dụng nào!", "warning")
            return
        if ConfirmationDialog(self, title="Xác nhận gỡ bỏ", message=f"Gỡ {len(selected)} ứng dụng?\nThao tác này an toàn và có thể khôi phục.", warning_mode=True).exec_() != QDialog.Accepted:
            return
        
        self._processing = True
        self._processed_results = {}
        self.btn_clean.setEnabled(False)
        self.btn_clean.setText("⏳ Đang xử lý...")
        
        self.opt_worker = DebloatWorker(self.adb, selected)
        self.opt_worker.progress.connect(self._on_debloat_progress)
        self.opt_worker.finished.connect(self._on_debloat_finished)
        self.opt_worker.start()
    
    def _on_debloat_progress(self, message):
        """Track per-package results from progress messages"""
        LogManager.log("Debloater", message, "info")
        # Parse which package and success/fail
        for pkg, card in self.app_cards.items():
            if pkg in message:
                if "✅" in message or "👌" in message or "⚠️" in message:
                    self._processed_results[pkg] = True
                elif "❌" in message or "🔒" in message:
                    self._processed_results[pkg] = False
                break
        # Update counter
        done = len(self._processed_results)
        total = sum(1 for c in self.app_cards.values() if c.isChecked() or c.package_name in self._processed_results)
        self.stats_lbl.setText(f"Đang xử lý: {done}/{total}")
    
    def _on_debloat_finished(self):
        """Mark processed cards, reset button"""
        self._processing = False
        self.btn_clean.setEnabled(True)
        self.btn_clean.setText("🗑️ Gỡ bỏ ngay")
        
        # Mark each processed card
        success_count = 0
        fail_count = 0
        for pkg, success in self._processed_results.items():
            if pkg in self.app_cards:
                self.app_cards[pkg].mark_processed(success)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
        
        self.stats_lbl.setText(f"✓ Hoàn tất: {success_count} thành công, {fail_count} lỗi")
        self.stats_lbl.setStyleSheet("color: #2ecc71; font-size: 13px; font-weight: 700;")
        LogManager.log("Debloater", f"✓ Hoàn tất: {success_count} gỡ thành công, {fail_count} lỗi", "success")

class XiaomiAIOOptimizerWidget(XiaomiBaseWidget):
    """UNIFIED: Xiaomi All-In-One (AIO) Optimizer"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(10, 10, 10, 10)
        c_layout.setSpacing(30)
        
        # --- SECTION 1: VISUAL & DISPLAY ---
        self.add_section_header(c_layout, "🎨 Hiển Thị & Giao Diện")
        grid_v = QGridLayout()
        grid_v.setSpacing(20)
        grid_v.addWidget(ModernCard("Chỉnh Tần Số Quét", "Tùy chỉnh 60Hz/90Hz/120Hz/144Hz hoặc Auto.", "⚡", self.run_force_refresh_rate, ["#f83600", "#f9d423"]), 0, 0)
        grid_v.addWidget(ModernCard("Tối Ưu Animation", "Giảm thời gian chuyển cảnh hệ thống (0.5x).", "🐇", self.run_animations, ["#4facfe", "#00f2fe"]), 0, 1)
        grid_v.addWidget(ModernCard("Hiện FPS / Hz", "Hiển thị thông số mượt mà trên màn hình.", "📈", self.run_show_fps, ["#fc4a1a", "#f7b733"]), 1, 0)
        grid_v.addWidget(ModernCard("Hiệu Ứng Blur", "Bật hiệu ứng mờ CC/Folder.", "💧", self.run_smart_blur, ["#89f7fe", "#66a6ff"]), 1, 1)
        grid_v.addWidget(ModernCard("Đa Nhiệm Xếp Chồng", "Giao diện đa nhiệm kiểu iOS.", "📚", self.run_hyperos_stacked_recent, ["#a18cd1", "#fbc2eb"]), 2, 0)
        grid_v.addWidget(ModernCard("Control Center Mới", "Kích hoạt CC giao diện mới.", "🎛️", lambda: self.run_task("new_cc", name="Control Center"), ["#e1eec3", "#f05053"]), 2, 1)
        grid_v.addWidget(ModernCard("Độ Phân Giải (WM)", "Thay đổi kích thước và DPI.", "📐", self.ask_resolution, ["#1d976c", "#93f9b9"]), 3, 0)
        grid_v.addWidget(ModernCard("Siêu Hình Nền", "Mở khóa Super Wallpaper.", "🪐", self.run_unlock_super_wallpaper, ["#f093fb", "#f5576c"]), 3, 1)
        grid_v.addWidget(ModernCard("Ẩn Nhãn Icon", "Chế độ No Word ẩn tên icon.", "📝", self.run_remove_app_label, ["#a18cd1", "#fbc2eb"]), 4, 0)
        grid_v.addWidget(ModernCard("Force Dark Mode", "Ép chế độ tối cho toàn bộ app.", "🌙", self.run_force_dark_mode, ["#434343", "#000000"]), 4, 1)
        c_layout.addLayout(grid_v)

        # --- SECTION 2: PERFORMANCE & BATTERY ---
        self.add_section_header(c_layout, "🚀 Hiệu Năng & Pin")
        grid_p = QGridLayout()
        grid_p.setSpacing(20)
        grid_p.addWidget(ModernCard("Tối Ưu ART VM", "Biên dịch lại app để mở nhanh.", "💎", self.run_art_tuning, ["#43e97b", "#38f9d7"]), 0, 0)
        grid_p.addWidget(ModernCard("Fix Trễ Thông Báo", "Không giới hạn pin cho FB/Zalo.", "🔔", self.run_fix_social_notifications, ["#ff9a9e", "#fecfef"]), 0, 1)
        grid_p.addWidget(ModernCard("Game Turbo", "Tối ưu GPU/CPU khi chơi game.", "🎮", lambda: self.run_task("game_perf_tune", name="Game Turbo"), ["#f12711", "#f5af19"]), 1, 0)
        grid_p.addWidget(ModernCard("Sạc Nhanh Cấp Tốc", "Mở khóa giới hạn sạc.", "⚡", lambda: self.run_task("fast_charge", name="Sạc Nhanh"), ["#FDC830", "#F37335"]), 1, 1)
        grid_p.addWidget(ModernCard("Giới Hạn App Nền", "Kiểm soát app chạy ngầm.", "🛑", self.ask_bg_limit, ["#bdc3c7", "#2c3e50"]), 2, 0)
        grid_p.addWidget(ModernCard("Tối Ưu Chuyên Sâu", "Tối ưu kernel cho HyperOS.", "⚡", self.run_expert_optimization, ["#f093fb", "#f5576c"]), 2, 1)
        c_layout.addLayout(grid_p)

        # --- SECTION 3: SYSTEM & UTILITIES ---
        self.add_section_header(c_layout, "🛠️ Hệ Thống & Tiện Ích")
        grid_s = QGridLayout()
        grid_s.setSpacing(20)
        grid_s.addWidget(ModernCard("Việt Hóa 1-Click", "Cài tiếng Việt & Múi giờ VN.", "🇻🇳", self.run_set_vietnamese, ["#ff0000", "#ff6666"]), 0, 0)
        grid_s.addWidget(ModernCard("Tắt Cập Nhật OTA", "Chặn thông báo cập nhật ROM.", "🚫", self.run_disable_ota, ["#2c3e50", "#000000"]), 0, 1)
        grid_s.addWidget(ModernCard("Bỏ Qua Setup", "Vào thẳng màn hình chính sau Reset.", "⏭️", self.run_skip_setup, ["#11998e", "#38ef7d"]), 1, 0)
        grid_s.addWidget(ModernCard("Ẩn Thanh Điều Hướng", "Cử chỉ vuốt full màn hình.", "📱", self.run_hide_nav_bar, ["#00c6ff", "#0072ff"]), 1, 1)
        grid_s.addWidget(ModernCard("Ghi Âm Cuộc Gọi", "Khôi phục ghi âm MIUI gốc.", "📞", self.run_enable_call_recording, ["#fa709a", "#fee140"]), 2, 0)
        grid_s.addWidget(ModernCard("Fix Region EU/VN", "Sửa lỗi vùng và định dạng.", "🌍", self.run_fix_eu_vn, ["#11998e", "#38ef7d"]), 2, 1)
        c_layout.addLayout(grid_s)
        
        btn_verify = QPushButton("🔍 Kiểm tra trạng thái hệ thống")
        btn_verify.setFixedHeight(45)
        btn_verify.setStyleSheet(f"QPushButton {{ background-color: {ThemeManager.COLOR_ACCENT}15; color: {ThemeManager.COLOR_ACCENT}; border: 1px solid {ThemeManager.COLOR_ACCENT}; border-radius: 12px; margin-top:10px; font-weight:bold; }}")
        btn_verify.clicked.connect(self.run_verify_status)
        c_layout.addWidget(btn_verify)

        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def add_section_header(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; border-bottom: 2px solid {ThemeManager.COLOR_ACCENT}50; padding-bottom: 5px; margin-top: 10px;")
        layout.addWidget(lbl)

    def run_task(self, task_type, name="Tác vụ", **kwargs):
        if self.opt_worker and self.opt_worker.isRunning(): return
        self.opt_worker = OptimizationWorker(self.adb, task_type)
        for k, v in kwargs.items(): setattr(self.opt_worker, k, v)
        self.opt_worker.progress.connect(lambda m: LogManager.log(name, m, "info"))
        self.opt_worker.finished.connect(lambda: LogManager.log(name, f"Xử lý '{name}' thành công!", "success"))
        if task_type == "check_status": self.opt_worker.result_ready.connect(self.show_status_dialog)
        self.opt_worker.start()

    def run_animations(self): self.run_task("animations", name="Animations")
    def run_smart_blur(self): self.run_task("smart_blur", name="Smart Blur")
    def run_expert_optimization(self): self.run_task("expert_optimize", name="Expert Opt")
    def run_fix_social_notifications(self): self.run_task("fix_social_notifications", name="Fix Social")
    def run_hyperos_stacked_recent(self): self.run_task("stacked_recent", name="Stacked Recent")
    def run_remove_app_label(self): self.run_task("remove_app_label", name="No Label")
    def run_force_blur_level(self): self.run_task("force_blur_level", name="Force Blur")
    def run_unlock_super_wallpaper(self): self.run_task("unlock_super_wallpaper", name="Super Wallpaper")
    def run_fix_eu_vn(self): self.run_task("fix_eu_vn", name="Region Fix")
    def run_verify_status(self): self.run_task("check_status", name="System Check")

    def run_force_refresh_rate(self):
        from PySide6.QtWidgets import QInputDialog
        items = ["Auto", "60Hz", "90Hz", "120Hz", "144Hz"]
        item, ok = QInputDialog.getItem(self, "Chỉnh Hz", "Chọn mức làm tươi:", items, 0, False)
        if ok: self.run_task("force_refresh_rate", name="Hz", refresh_rate=(0 if item=="Auto" else int(item.replace("Hz",""))))

    def run_show_fps(self):
        msg = QMessageBox(self)
        btn_on = msg.addButton("Bật FPS", QMessageBox.ActionRole)
        btn_off = msg.addButton("Tắt FPS", QMessageBox.ActionRole)
        msg.exec()
        if msg.clickedButton() in [btn_on, btn_off]: self.run_task("show_fps_on" if msg.clickedButton()==btn_on else "show_fps_off", name="FPS")

    def ask_resolution(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Độ phân giải", "Nhập độ phân giải (VD: 1080x2400):")
        if ok and text: self.run_task("wm_size", name="Resolution", size_value=text)

    def run_force_dark_mode(self):
        if ConfirmationDialog(self, title="Dark Mode", message="Ép chế độ tối?", warning_mode=True).exec_() == QDialog.Accepted:
            self.run_task("force_dark_mode_on", name="Dark Mode")

    def run_art_tuning(self):
        from PySide6.QtWidgets import QInputDialog
        items = ["Tốc độ (Speed)", "Cân bằng (Profile)", "Pin (Quicken)"]
        item, ok = QInputDialog.getItem(self, "ART Tuning", "Chọn chế độ:", items, 0, False)
        if ok: self.run_task("compile_apps", name="ART", compile_mode=("speed" if "Speed" in item else ("speed-profile" if "Profile" in item else "quicken")))

    def ask_bg_limit(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Giới hạn nền", "Nhập số lượng (VD: 2):")
        if ok: self.run_task("bg_limit", name="BG Limit", limit_value=text)

    def run_set_vietnamese(self):
        if ConfirmationDialog(self, title="Việt Hóa", message="Cài tiếng Việt?", warning_mode=True).exec_() == QDialog.Accepted:
            self.run_task("set_vietnamese", name="Language")

    def run_disable_ota(self):
        if ConfirmationDialog(self, title="Tắt OTA", message="Chặn cập nhật?", warning_mode=True).exec_() == QDialog.Accepted:
            self.run_task("disable_ota", name="OTA")

    def run_skip_setup(self):
        if ConfirmationDialog(self, title="Skip Setup", message="Bypass Setup?").exec_() == QDialog.Accepted:
            self.run_task("skip_setup", name="Skip Setup")

    def run_hide_nav_bar(self):
        dlg = ConfirmationDialog(self, title="Nav Bar", message="Ẩn hay Hiện?", confirm_text="Ẩn", cancel_text="Hiện")
        self.run_task("hide_nav_on" if dlg.exec_()==QDialog.Accepted else "hide_nav_off", name="Nav Bar")

    def run_enable_call_recording(self):
        if ConfirmationDialog(self, title="Ghi âm", message="Kích hoạt ghi âm gốc?").exec_() == QDialog.Accepted:
            self.run_task("enable_call_recording", name="Recording")

class XiaomiOptimizerWidget(XiaomiBaseWidget):
    """Main Wrapper for Xiaomi Turbo Suite"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.nav_bar = QFrame()
        self.nav_bar.setFixedHeight(50)
        self.nav_bar.setObjectName("OptimizerNavBar")
        self.nav_bar.setStyleSheet(f"background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']}; border-bottom: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};")
        
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(15, 5, 15, 5)
        
        btn_back = QPushButton("⬅ Quay lại Hub")
        btn_back.clicked.connect(lambda: self.switch_page(0))
        btn_back.setStyleSheet("QPushButton { background: transparent; border: 1px solid #ccc; border-radius: 12px; padding: 6px 16px; font-weight: bold; }")
        nav_layout.addWidget(btn_back)
        
        self.page_title = QLabel("Xiaomi Turbo Suite")
        self.page_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        nav_layout.addWidget(self.page_title)
        nav_layout.addStretch()
        layout.addWidget(self.nav_bar)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        self.init_pages()
        self.switch_page(0)

    def init_pages(self):
        self.hub = XiaomiHubWidget(self.adb)
        self.hub.switch_page.connect(self.switch_page)
        self.stack.addWidget(self.hub)
        self.stack.addWidget(XiaomiDebloaterWidget(self.adb))
        self.stack.addWidget(XiaomiAIOOptimizerWidget(self.adb))
        self.stack.addWidget(OTADownloaderWidget(self.adb))
        self.stack.addWidget(FastbootToolboxWidget(self.adb))
        self.stack.addWidget(HyperOSAppsWidget(self.adb))

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        titles = ["Xiaomi Turbo Hub", "Gỡ Rác & Debloat", "Tối Ưu & Tinh Chỉnh (AIO)", "Tải ROM & Check OTA", "Fastboot Toolkit", "Kho Ứng Dụng"]
        self.page_title.setText(f"|  {titles[index]}")
        self.nav_bar.setVisible(index != 0)
        curr = self.stack.widget(index)
        if hasattr(curr, 'refresh_state'): curr.refresh_state()
