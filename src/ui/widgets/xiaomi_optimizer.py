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
    QListWidget, QListWidgetItem, QStackedWidget, QSizePolicy, QDialog,
    QComboBox, QButtonGroup
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
        
        btn_style = "background: #1a1a1a; color: white;" if gradient_colors and gradient_colors[0] == "#ffffff" else ("background: white; color: black;" if gradient_colors else f"background: {ThemeManager.COLOR_ACCENT}; color: white;")
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

# XiaomiHubWidget removed — replaced by XiaomiToolsPage sidebar navigation

class XiaomiBaseWidget(QWidget):
    """Base widget with shared helper methods"""
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.opt_worker = None
        self.worker = None
        self.parent_page = None # Reference to XiaomiToolsPage

    def set_parent_page(self, page):
        self.parent_page = page

    def switch_to_tab(self, name_fragment):
        """Redirect to another tab in the parent container"""
        if self.parent_page and hasattr(self.parent_page, 'switch_to_tool'):
            return self.parent_page.switch_to_tool(name_fragment)
        
        # Fallback for old XiaomiOptimizerWidget (Hub version)
        curr = self.parent()
        while curr:
            if hasattr(curr, 'switch_page'):
                # Mapping for legacy hub indices
                mapping = {"debloat": 1, "system": 2, "expert": 3, "notify": 4}
                for k, v in mapping.items():
                    if k in name_fragment.lower():
                        curr.switch_page(v)
                        return True
            curr = curr.parent()
        return False

    def run_task(self, task_type, name="Tác vụ", **kwargs):
        if self.opt_worker and self.opt_worker.isRunning(): return
        self.opt_worker = OptimizationWorker(self.adb, task_type, **kwargs)
        self.opt_worker.progress.connect(lambda m: LogManager.log(name, m, "info" if "✅" not in m and "❌" not in m else ("success" if "✅" in m else "error")))
        self.opt_worker.error_occurred.connect(lambda t, m: self.show_error(t, m))  # P1-5: connect security errors
        if task_type == "check_status": self.opt_worker.result_ready.connect(self.show_status_dialog)
        self.opt_worker.start()
        
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
                    pass
    
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

    def add_section_header(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; border-bottom: 2px solid {ThemeManager.COLOR_ACCENT}50; padding-bottom: 5px; margin-top: 10px;")
        layout.addWidget(lbl)

    def run_art_tuning(self):
        from PySide6.QtWidgets import QInputDialog
        items = ["Tốc độ (Speed)", "Cân bằng (Profile)", "Pin (Quicken)"]
        item, ok = QInputDialog.getItem(self, "ART Tuning", "Chọn chế độ (Quá trình mất 5-10 phút):", items, 0, False)
        if ok: self.run_task("compile_apps", name="ART", mode=("speed" if "Speed" in item else ("speed-profile" if "Profile" in item else "quicken")))

    def run_set_vietnamese(self):
        if ConfirmationDialog(self, title="Việt Hóa", message="Cài tiếng Việt cho ứng dụng hệ thống?", warning_mode=True).exec_() == QDialog.Accepted:
            self.run_task("set_vietnamese", name="Language")

    def run_disable_ota(self):
        if ConfirmationDialog(self, title="Tắt OTA", message="Chặn thông báo cập nhật hệ thống?", warning_mode=True).exec_() == QDialog.Accepted:
            self.run_task("disable_ota", name="OTA")

    def run_open_developer_options(self): self.run_task("open_dev_options", name="Dev Settings")
    
    def run_enable_call_recording(self):
        if ConfirmationDialog(self, title="Ghi âm", message="Kích hoạt tính năng ghi âm cuộc gọi MIUI gốc?").exec_() == QDialog.Accepted:
            self.run_task("enable_call_recording", name="Recording")

    def run_verify_status(self): self.run_task("check_status", name="System Check")
            
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

    def __init__(self, app_info, category=""):
        super().__init__()
        if isinstance(app_info, dict):
            self.app_name = app_info.get("name", "")
            self.package_name = app_info.get("pkg", "")
            self.safety = app_info.get("safe", "safe")
            self.desc = app_info.get("desc", "")
        else:
            self.app_name = app_info
            self.package_name = app_info
            self.safety = "safe"
            self.desc = ""
            
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
        self.icon_lbl = QLabel(self.app_name[0].upper() if self.app_name else "?")
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
        
        # Title Row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.name_lbl = QLabel(self.app_name)
        self.name_lbl.setStyleSheet(f"font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px;")
        title_row.addWidget(self.name_lbl)
        
        # Safety Badge
        self.safety_badge = QLabel()
        self.safety_badge.setFixedHeight(18)
        self.safety_badge.setAlignment(Qt.AlignCenter)
        if self.safety == "safe":
            self.safety_badge.setText(" An Toàn ")
            self.safety_badge.setStyleSheet("background: rgba(46, 204, 113, 0.15); color: #2ecc71; border-radius: 4px; font-weight: 700; font-size: 10px; padding: 0 6px;")
        elif self.safety == "warning":
            self.safety_badge.setText(" Cảnh Báo ")
            self.safety_badge.setStyleSheet("background: rgba(241, 196, 15, 0.15); color: #f39c12; border-radius: 4px; font-weight: 700; font-size: 10px; padding: 0 6px;")
        elif self.safety == "danger":
            self.safety_badge.setText(" Nguy Hiểm ")
            self.safety_badge.setStyleSheet("background: rgba(231, 76, 60, 0.15); color: #e74c3c; border-radius: 4px; font-weight: 700; font-size: 10px; padding: 0 6px;")
        title_row.addWidget(self.safety_badge)
        title_row.addStretch()
        info_layout.addLayout(title_row)
        
        self.pkg_lbl = QLabel(self.package_name)
        self.pkg_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 11px;")
        info_layout.addWidget(self.pkg_lbl)
        
        if hasattr(self, 'desc') and self.desc:
            self.desc_lbl = QLabel(self.desc)
            self.desc_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 10px; font-style: italic;")
            info_layout.addWidget(self.desc_lbl)
            
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
        
        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tất Cả", "✅ An Toàn", "⚠️ Cảnh Báo", "❌ Nguy Hiểm"])
        self.filter_combo.setFixedWidth(140)
        self.filter_combo.setStyleSheet(ThemeManager.get_input_style() + "height: 28px;")
        self.filter_combo.currentIndexChanged.connect(self._apply_safety_filter)
        header_l.addWidget(self.filter_combo)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm ứng dụng...")
        self.search_input.setFixedWidth(220)
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
                self.app_cards[card.package_name] = card
                self._category_cards[category].append(card)
        
        self.content_layout.addSpacing(80)  # Space for bottom bar
        
        scroll.setWidget(self.content)
        layout.addWidget(scroll, 1)
        
        # ─── BOTTOM ACTION BAR ───
        actions_bar = QFrame()
        actions_bar.setFixedHeight(80)
        actions_bar.setObjectName("DebloatBar")
        actions_bar.setStyleSheet(f"""
            #DebloatBar {{
                background: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
                border-top: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        actions_layout = QVBoxLayout(actions_bar)
        actions_layout.setContentsMargins(24, 8, 24, 8)
        actions_layout.setSpacing(6)
        
        # Row 1: select buttons + stats + action button
        row1 = QHBoxLayout()
        
        btn_select_safe = QPushButton("✅ Chọn An Toàn")
        btn_select_safe.setFixedHeight(30)
        btn_select_safe.setCursor(Qt.PointingHandCursor)
        btn_select_safe.setStyleSheet(f"""
            QPushButton {{ background: rgba(46,204,113,0.15); color: #2ecc71;
                border: 1px solid rgba(46,204,113,0.3); border-radius: 8px;
                font-size: 11px; font-weight: 700; padding: 0 10px; }}
            QPushButton:hover {{ background: rgba(46,204,113,0.25); }}
        """)
        btn_select_safe.clicked.connect(self._select_safe_only)
        row1.addWidget(btn_select_safe)
        
        btn_select_all = QPushButton("Chọn Tất Cả")
        btn_select_all.setFixedHeight(30)
        btn_select_all.setCursor(Qt.PointingHandCursor)
        btn_select_all.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {ThemeManager.COLOR_TEXT_SECONDARY};
                border: 1px solid rgba(128,128,128,0.3); border-radius: 8px;
                font-size: 11px; padding: 0 10px; }}
            QPushButton:hover {{ color: {ThemeManager.COLOR_ACCENT}; border-color: {ThemeManager.COLOR_ACCENT}50; }}
        """)
        btn_select_all.clicked.connect(lambda: self._set_all_checked(True))
        row1.addWidget(btn_select_all)
        
        btn_deselect = QPushButton("Bỏ Chọn")
        btn_deselect.setFixedHeight(30)
        btn_deselect.setCursor(Qt.PointingHandCursor)
        btn_deselect.setStyleSheet(btn_select_all.styleSheet())
        btn_deselect.clicked.connect(lambda: self._set_all_checked(False))
        row1.addWidget(btn_deselect)
        
        row1.addStretch()
        
        self.stats_lbl = QLabel("0 ứng dụng được chọn")
        self.stats_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px; font-weight: 600;")
        row1.addWidget(self.stats_lbl)
        
        self.btn_clean = QPushButton("🗑️ Gỡ bỏ ngay")
        self.btn_clean.setCursor(Qt.PointingHandCursor)
        self.btn_clean.setFixedSize(150, 36)
        self.btn_clean.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
                color: white; font-weight: 700; border-radius: 18px;
                border: none; font-size: 13px;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6b6b, stop:1 #e74c3c); }}
            QPushButton:disabled {{ background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.25); }}
        """)
        self.btn_clean.clicked.connect(self.start_debloat)
        row1.addWidget(self.btn_clean)
        
        actions_layout.addLayout(row1)
        
        # Row 2: Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background: rgba(255,255,255,0.08); border-radius: 2px; border: none; }}
            QProgressBar::chunk {{ background: {ThemeManager.COLOR_ACCENT}; border-radius: 2px; }}
        """)
        self.progress_bar.hide()
        actions_layout.addWidget(self.progress_bar)
        
        layout.addWidget(actions_bar)

    def _on_card_toggled(self, checked, package):
        count = sum(1 for c in self.app_cards.values() if c.isChecked())
        self.stats_lbl.setText(f"{count} ứng dụng được chọn")
        clr = "#e74c3c" if count > 0 else ThemeManager.COLOR_TEXT_SECONDARY
        weight = "700" if count > 0 else "600"
        self.stats_lbl.setStyleSheet(f"color: {clr}; font-size: 13px; font-weight: {weight};")

    def _set_all_checked(self, checked):
        for card in self.app_cards.values():
            if card.cb.isEnabled() and card.isVisible():
                card.setChecked(checked)

    def _select_safe_only(self):
        """Chọn chỉ các app có safety='safe'"""
        for card in self.app_cards.values():
            if card.cb.isEnabled():
                card.setChecked(card.safety == "safe")

    def _toggle_category(self, category):
        cards = self._category_cards.get(category, [])
        any_unchecked = any(not c.isChecked() and c.cb.isEnabled() for c in cards if c.isVisible())
        for c in cards:
            if c.cb.isEnabled() and c.isVisible():
                c.setChecked(any_unchecked)

    def _apply_safety_filter(self, index):
        """Filter cards by safety level"""
        safety_map = {0: None, 1: "safe", 2: "warning", 3: "danger"}
        target = safety_map.get(index)
        for card in self.app_cards.values():
            if target is None:
                card.setVisible(True)
            else:
                card.setVisible(card.safety == target)
        # Re-apply text search on top
        self.filter_apps(self.search_input.text())

    def filter_apps(self, text):
        txt = text.lower()
        safety_map = {0: None, 1: "safe", 2: "warning", 3: "danger"}
        target_safety = safety_map.get(self.filter_combo.currentIndex())
        for pkg, card in self.app_cards.items():
            text_match = not txt or txt in pkg.lower() or txt in card.app_name.lower()
            safety_match = target_safety is None or card.safety == target_safety
            card.setVisible(text_match and safety_match)
            
    def start_debloat(self):
        if self._processing:
            return
        selected = [card.package_name for card in self.app_cards.values() if card.isChecked()]
        if not selected:
            LogManager.log("Debloater", "⚠ Chưa chọn ứng dụng nào!", "warning")
            return
        if ConfirmationDialog(self, title="Xác nhận gỡ bỏ", message=f"Gỡ {len(selected)} ứng dụng?\nThao tác này an toàn và có thể khôi phục.", warning_mode=True).exec_() != QDialog.Accepted:
            return
        
        self._processing = True
        self._processed_results = {}
        self.btn_clean.setEnabled(False)
        self.btn_clean.setText("⏳ Đang xử lý...")
        self.progress_bar.setMaximum(len(selected))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        self.opt_worker = DebloatWorker(self.adb, selected)
        self.opt_worker.progress.connect(self._on_debloat_progress)
        self.opt_worker.finished.connect(self._on_debloat_finished)
        self.opt_worker.start()
    
    def _on_debloat_progress(self, message):
        LogManager.log("Debloater", message, "info")
        for pkg, card in self.app_cards.items():
            if pkg in message:
                if "✅" in message or "👌" in message or "⚠️" in message:
                    self._processed_results[pkg] = True
                elif "❌" in message or "🔒" in message:
                    self._processed_results[pkg] = False
                break
        # Update progress bar
        total_selected = sum(1 for c in self.app_cards.values() if c.isChecked() or c.package_name in self._processed_results)
        done = len(self._processed_results)
        if total_selected > 0:
            self.progress_bar.setMaximum(total_selected)
            self.progress_bar.setValue(done)
        self.stats_lbl.setText(f"Đang xử lý: {done}/{total_selected}")
    
    def _on_debloat_finished(self):
        self._processing = False
        self.btn_clean.setEnabled(True)
        self.btn_clean.setText("🗑️ Gỡ bỏ ngay")
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        
        success_count = 0
        fail_count = 0
        for pkg, success in self._processed_results.items():
            if pkg in self.app_cards:
                self.app_cards[pkg].mark_processed(success)
                if success: success_count += 1
                else: fail_count += 1
        
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
        
        # Fix Thông Báo - Clean redirection using the new helper
        grid_v.addWidget(ModernCard("Fix Thông Báo", "Sửa lỗi chậm tin nhắn (Bản NC v3).", "🔔", lambda: self.switch_to_tab("Thông Báo"), ["#ffffff", "#f1f3f4"]), 5, 0)
        grid_v.addWidget(ModernCard("Chuyển MIUI Apps", "Đổi Dialer/SMS sang MIUI.", "📲", self.run_switch_miui_apps, ["#11998e", "#38ef7d"]), 5, 1)
        c_layout.addLayout(grid_v)

        # --- SECTION 2: PERFORMANCE & BATTERY ---
        self.add_section_header(c_layout, "🚀 Hiệu Năng & Pin")
        grid_p = QGridLayout()
        grid_p.setSpacing(20)
        grid_p.addWidget(ModernCard("Tối Ưu ART VM", "Biên dịch lại app để mở nhanh.", "💎", self.run_art_tuning, ["#43e97b", "#38f9d7"]), 0, 0)
        grid_p.addWidget(ModernCard("Fix Thông Báo (Chọn lọc)", "Fix trễ thông báo và tự động bật app.", "🔔", lambda: self.switch_to_tab("Thông Báo"), ["#ff9a9e", "#fecfef"]), 0, 1)
        grid_p.addWidget(ModernCard("Game Turbo", "Tối ưu GPU/CPU khi chơi game.", "🎮", lambda: self.run_task("game_perf_tune", name="Game Turbo"), ["#f12711", "#f5af19"]), 1, 0)
        grid_p.addWidget(ModernCard("Sạc Nhanh Cấp Tốc", "Mở khóa giới hạn sạc.", "⚡", lambda: self.run_task("fast_charge", name="Sạc Nhanh"), ["#FDC830", "#F37335"]), 1, 1)
        grid_p.addWidget(ModernCard("Giới Hạn App Nền (Basic)", "Kiểm soát app chạy ngầm cơ bản.", "🛑", self.ask_bg_limit, ["#bdc3c7", "#2c3e50"]), 2, 0)
        grid_p.addWidget(ModernCard("Tối Ưu Chuyên Sâu", "Tối ưu kernel cho HyperOS.", "⚡", lambda: self.switch_to_tab("Chuyên Sâu"), ["#f093fb", "#f5576c"]), 2, 1)
        c_layout.addLayout(grid_p)

        # --- SECTION 3: SYSTEM & UTILITIES ---
        self.add_section_header(c_layout, "🛠️ Hệ Thống & Tiện Ích")
        grid_s = QGridLayout()
        grid_s.setSpacing(20)
        grid_s.addWidget(ModernCard("Bỏ Qua Setup", "Vào thẳng màn hình chính sau Reset.", "⏭️", self.run_skip_setup, ["#11998e", "#38ef7d"]), 0, 0)
        grid_s.addWidget(ModernCard("Ẩn Thanh Điều Hướng", "Cử chỉ vuốt full màn hình.", "📱", self.run_hide_nav_bar, ["#00c6ff", "#0072ff"]), 0, 1)
        grid_s.addWidget(ModernCard("Fix Region EU/VN", "Sửa lỗi vùng và định dạng.", "🌍", self.run_fix_eu_vn, ["#11998e", "#38ef7d"]), 1, 0)
        grid_s.addWidget(ModernCard("Dọn Rác (Cleaner)", "Xóa rác và cache hệ thống.", "🧹", lambda: self.switch_to_tab("Dọn Rác"), ["#a1c4fd", "#c2e9fb"]), 1, 1)
        c_layout.addLayout(grid_s)
        
        btn_verify = QPushButton("🔍 Kiểm tra trạng thái hệ thống")
        btn_verify.setFixedHeight(45)
        btn_verify.setStyleSheet(f"QPushButton {{ background-color: {ThemeManager.COLOR_ACCENT}15; color: {ThemeManager.COLOR_ACCENT}; border: 1px solid {ThemeManager.COLOR_ACCENT}; border-radius: 12px; margin-top:10px; font-weight:bold; }}")
        btn_verify.clicked.connect(self.run_verify_status)
        c_layout.addWidget(btn_verify)

        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def run_animations(self): self.run_task("animations", name="Animations")
    def run_smart_blur(self): self.run_task("smart_blur", name="Smart Blur")
    def run_expert_optimization(self): self.run_task("expert_optimize", name="Expert Opt")
    def run_social_fix_dialog(self):
        # Redirect to the new dedicated tab (Index 3 in Sidebar) - Updated index
        if hasattr(self.parent(), 'setCurrentIndex'):
            self.parent().setCurrentIndex(3)
        elif hasattr(self.parent(), 'switch_page'):
            self.parent().switch_page(3) 

    def run_hyperos_stacked_recent(self):
        """Luồng xử lý Stacked Recents theo phiên bản OS"""
        from src.core.optimization_manager import OptimizationManager
        opt = OptimizationManager(self.adb)
        os_ver = opt.detect_hyperos_version()
        if os_ver <= 1:
            LogManager.log("Stacked Recent", "❌ MIUI / HyperOS 1 không hỗ trợ tính năng Xếp chồng", "error")
            return
        # Basic logic for now
        self.run_task("stacked_recent", name="Stacked Recent")

    def run_remove_app_label(self): self.run_task("remove_app_label", name="No Label")
    def run_force_blur_level(self): self.run_task("force_blur_level", name="Force Blur")
    def run_unlock_super_wallpaper(self): self.run_task("unlock_super_wallpaper", name="Super Wallpaper")
    def run_fix_eu_vn(self): self.run_task("fix_eu_vn", name="Region Fix")
    def run_force_refresh_rate(self):
        from PySide6.QtWidgets import QInputDialog
        items = ["Auto", "60Hz", "90Hz", "120Hz", "144Hz"]
        item, ok = QInputDialog.getItem(self, "Chỉnh Hz", "Chọn mức làm tươi:", items, 0, False)
        if ok: self.run_task("force_refresh_rate", name="Hz", refresh_rate=(0 if item=="Auto" else int(item.replace("Hz",""))))
    def run_show_fps(self):
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        btn_on = msg.addButton("Bật FPS", QMessageBox.ActionRole)
        btn_off = msg.addButton("Tắt FPS", QMessageBox.ActionRole)
        msg.exec()
        if msg.clickedButton() in [btn_on, btn_off]: self.run_task("show_fps_on" if msg.clickedButton()==btn_on else "show_fps_off", name="FPS")
    def ask_resolution(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Độ phân giải", "Nhập độ phân giải (VD: 1080x2400):")
        if ok and text: self.run_task("wm_size", name="Resolution", size=text)
    def run_force_dark_mode(self):
        if ConfirmationDialog(self, title="Dark Mode", message="Ép chế độ tối?", warning_mode=True).exec_() == QDialog.Accepted:
            self.run_task("force_dark_mode_on", name="Dark Mode")
    def ask_bg_limit(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Giới hạn nền", "Nhập số lượng (VD: 2):")
        if ok: self.run_task("bg_limit", name="BG Limit", limit=text)
    def run_skip_setup(self):
        if ConfirmationDialog(self, title="Skip Setup", message="Bypass Setup?").exec_() == QDialog.Accepted:
            self.run_task("skip_setup", name="Skip Setup")
    def run_hide_nav_bar(self):
        dlg = ConfirmationDialog(self, title="Nav Bar", message="Ẩn hay Hiện?", confirm_text="Ẩn", cancel_text="Hiện")
        self.run_task("hide_nav_on" if dlg.exec_()==QDialog.Accepted else "hide_nav_off", name="Nav Bar")
    def run_switch_miui_apps(self):
        self.run_task("miui_apps", name="MIUI Apps")

class XiaomiExpertTweaksWidget(XiaomiBaseWidget):
    """DEDICATED: Expert & HyperOS System Tweaks"""
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

        # --- SECTION 1: PERFORMANCE TWEAKS (CPU/GPU) ---
        self.add_section_header(c_layout, "🔥 Ép Xung & Hiệu Năng Chuyên Sâu")
        grid_p = QGridLayout()
        grid_p.setSpacing(20)
        grid_p.addWidget(ModernCard("HyperOS Expert Perf", "Ép CPU/GPU Level 6 & Visual Release 3.", "⚡", lambda: self.run_task("expert_service_call", name="Expert Service"), ["#FF416C", "#FF4B2B"]), 0, 0)
        grid_p.addWidget(ModernCard("Fixed Perf Mode", "Bật chế độ Hiệu suất cố định hệ thống.", "🏎️", lambda: self.run_task("hyperos_perf_mode", name="HyperOS Perf"), ["#f4c4f3", "#fc67fa"]), 0, 1)
        grid_p.addWidget(ModernCard("Tối Ưu ART VM", "Biên dịch lại app để mở cực nhanh.", "💎", self.run_art_tuning, ["#43e97b", "#38f9d7"]), 1, 0)
        grid_p.addWidget(ModernCard("Tối Ưu Cảm Ứng", "Giảm độ trễ & Tăng phản hồi màn hình.", "👆", lambda: self.run_task("touch_optimize", name="Touch Opt"), ["#36d1dc", "#5b86e5"]), 1, 1)
        c_layout.addLayout(grid_p)

        # --- SECTION 2: SYSTEM & RAM ---
        self.add_section_header(c_layout, "🧠 Hệ Thống & Bộ Nhớ (RAM)")
        grid_s = QGridLayout()
        grid_s.setSpacing(20)
        grid_s.addWidget(ModernCard("RAM Phantom Fix", "Tăng giới hạn tiến trình Phantom (HyperOS).", "🧠", lambda: self.run_task("phantom_proc_limit", name="Phantom Fix"), ["#8e44ad", "#c39bd3"]), 0, 0)
        grid_s.addWidget(ModernCard("Speed Up HyperOS", "Tắt log rác & Tối ưu App launch.", "🚀", lambda: self.run_task("system_logging_off", name="System Log Off"), ["#00B4DB", "#0083B0"]), 0, 1)
        grid_s.addWidget(ModernCard("Cài Tiếng Việt", "Việt Hóa & Múi giờ VN 1-Click.", "🇻🇳", self.run_set_vietnamese, ["#ff0000", "#ff6666"]), 1, 0)
        grid_s.addWidget(ModernCard("Mở Dev Settings", "Truy cập nhanh Cài đặt nhà phát triển.", "⚙️", self.run_open_developer_options, ["#757f9a", "#d7dde8"]), 1, 1)
        c_layout.addLayout(grid_s)

        # --- SECTION 3: UTILITIES ---
        self.add_section_header(c_layout, "🛠️ Tiện Ích Khác")
        grid_u = QGridLayout()
        grid_u.setSpacing(20)
        grid_u.addWidget(ModernCard("Ghi Âm Cuộc Gọi", "Khôi phục ghi âm MIUI gốc.", "📞", self.run_enable_call_recording, ["#fa709a", "#fee140"]), 0, 0)
        grid_u.addWidget(ModernCard("Tắt Cập Nhật OTA", "Chặn thông báo cập nhật ROM.", "🚫", self.run_disable_ota, ["#2c3e50", "#000000"]), 0, 1)
        c_layout.addLayout(grid_u)

        btn_verify = QPushButton("🔍 Kiểm tra trạng thái hệ thống")
        btn_verify.setFixedHeight(45)
        btn_verify.setStyleSheet(f"QPushButton {{ background-color: {ThemeManager.COLOR_ACCENT}15; color: {ThemeManager.COLOR_ACCENT}; border: 1px solid {ThemeManager.COLOR_ACCENT}; border-radius: 12px; margin-top:20px; font-weight:bold; }}")
        btn_verify.clicked.connect(self.run_verify_status)
        c_layout.addWidget(btn_verify)

        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

class NotificationAppItem(QFrame):
    """Modern list item for App selection"""
    def __init__(self, pkg, name, icon_char, checked=False, parent=None):
        super().__init__(parent)
        self.pkg = pkg
        self.setFixedHeight(60)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(35, 5, 20, 5) # Tăng lề cực rộng (35) để tránh bo góc Card đè lên ô tích
        layout.setSpacing(15)
        
        self.cb = QCheckBox()
        self.cb.setChecked(checked)
        self.cb.setFixedSize(32, 32)
        # Bỏ margin-left bên trong checkbox để indicator nằm sát trái hơn trong vùng layout mới
        self.cb.setStyleSheet(ThemeManager.get_checkbox_style().replace("padding: 4px;", "padding: 0px; margin-left: 0px;"))
        
        self.icon_lbl = QLabel(icon_char)
        self.icon_lbl.setFixedSize(40, 40)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet(f"font-size: 22px; background: {ThemeManager.COLOR_ACCENT}10; border-radius: 8px;")
        
        info = QVBoxLayout()
        info.setSpacing(2)
        self.name_lbl = QLabel(name)
        self.name_lbl.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        self.pkg_lbl = QLabel(pkg)
        self.pkg_lbl.setStyleSheet(f"font-size: 11px; color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        info.addWidget(self.name_lbl)
        info.addWidget(self.pkg_lbl)
        
        layout.addWidget(self.cb)
        layout.addWidget(self.icon_lbl)
        layout.addLayout(info)
        layout.addStretch()
        
        self.update_style()

    def update_style(self):
        checked = self.cb.isChecked()
        theme = ThemeManager.get_theme()
        bg = theme['COLOR_GLASS_WHITE'] if checked else "transparent"
        border = f"1px solid {ThemeManager.COLOR_ACCENT}50" if checked else "1px solid transparent"
        self.setStyleSheet(f"""
            NotificationAppItem {{
                background-color: {bg};
                border: {border};
                border-radius: 12px;
            }}
            NotificationAppItem:hover {{
                background-color: #f1f3f4;
            }}
        """)

    def mousePressEvent(self, event):
        self.cb.setChecked(not self.cb.isChecked())
        self.update_style()
        super().mousePressEvent(event)

class XiaomiNotificationFixWidget(XiaomiBaseWidget):
    """DEDICATED PAGE: Intensive Notification Fixer V3.0"""
    def __init__(self, adb):
        super().__init__(adb)
        self._all_apps = []
        self.app_items = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header Section
        header = QHBoxLayout()
        title_v = QVBoxLayout()
        title = QLabel("🔔 Fix Thông Báo Chuyên Sâu v3.0")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        desc = QLabel("Khắc phục triệt để tình trạng chậm tin nhắn (Zalo, Messenger...) bằng cách tối ưu Pin và Quyền tự chạy.")
        desc.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px;")
        title_v.addWidget(title)
        title_v.addWidget(desc)
        header.addLayout(title_v)
        header.addStretch()
        
        self.btn_refresh = QPushButton("↻ Làm mới danh sách")
        self.btn_refresh.setStyleSheet(ThemeManager.get_button_style("normal"))
        self.btn_refresh.clicked.connect(self.load_apps)
        header.addWidget(self.btn_refresh)
        layout.addLayout(header)
        
        # --- Top Section: Options ---
        opt_panel = QFrame()
        opt_panel.setStyleSheet("background: #f8f9fa; border: 1px solid #dadce0; border-radius: 16px;")
        opt_layout = QHBoxLayout(opt_panel)
        opt_layout.setContentsMargins(20, 15, 20, 15)
        
        self.chk_notify = QCheckBox("Bật thông báo ứng dụng")
        self.chk_battery = QCheckBox("Pin không hạn chế")
        self.chk_autostart = QCheckBox("Tự động chạy & Launch")
        for chk in [self.chk_notify, self.chk_battery, self.chk_autostart]:
            chk.setChecked(True)
            chk.setStyleSheet(ThemeManager.get_checkbox_style())
            opt_layout.addWidget(chk)
            
        # --- Preset Buttons ---
        preset_panel = QFrame()
        preset_panel.setStyleSheet(f"background: transparent;")
        preset_row = QHBoxLayout(preset_panel)
        preset_row.setContentsMargins(0, 0, 0, 0)
        preset_row.setSpacing(8)
        
        lbl_preset = QLabel("⚡ Chọn nhanh:")
        lbl_preset.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600; font-size: 12px;")
        preset_row.addWidget(lbl_preset)
        
        PRESETS = [
            ("Zalo + Messenger", ["com.zing.zalo", "com.facebook.orca"]),
            ("Tất cả mạng xã hội", ["com.zing.zalo", "com.facebook.orca", "org.telegram.messenger", "com.viber.voip", "com.whatsapp"]),
            ("Email & Calendar", ["com.google.android.gm", "com.microsoft.outlook", "com.google.android.calendar"]),
        ]
        for preset_name, preset_pkgs in PRESETS:
            btn_p = QPushButton(preset_name)
            btn_p.setCursor(Qt.PointingHandCursor)
            btn_p.setFixedHeight(28)
            btn_p.setStyleSheet(f"""
                QPushButton {{ background: {ThemeManager.COLOR_ACCENT}15; color: {ThemeManager.COLOR_ACCENT};
                    border: 1px solid {ThemeManager.COLOR_ACCENT}40; border-radius: 14px;
                    font-size: 11px; font-weight: 600; padding: 0 12px; }}
                QPushButton:hover {{ background: {ThemeManager.COLOR_ACCENT}25; }}
            """)
            pkgs_copy = preset_pkgs[:]
            btn_p.clicked.connect(lambda _, pkgs=pkgs_copy: self._select_by_packages(pkgs))
            preset_row.addWidget(btn_p)
        preset_row.addStretch()
        layout.addWidget(preset_panel)
        
        # --- Top Section: Options ---
        list_group = QGroupBox("Danh sách ứng dụng người dùng")
        list_group.setStyleSheet(ThemeManager.get_group_box_style())
        list_layout = QVBoxLayout(list_group)
        
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm nhanh ứng dụng (ví dụ: zalo, telegram)...")
        self.search_input.setStyleSheet(ThemeManager.get_input_style() + "height: 40px; border-radius: 20px;")
        self.search_input.textChanged.connect(self.filter_apps)
        search_box.addWidget(self.search_input)
        
        self.btn_select_all = QPushButton("Chọn tất cả")
        self.btn_select_all.setCheckable(True)
        self.btn_select_all.setStyleSheet(ThemeManager.get_button_style("normal"))
        self.btn_select_all.clicked.connect(self.toggle_all_selection)
        search_box.addWidget(self.btn_select_all)
        list_layout.addLayout(search_box)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: 1px solid #dadce0; border-radius: 12px; background: #ffffff; }")
        
        self.scroll_content = QWidget()
        self.scroll_v = QVBoxLayout(self.scroll_content)
        self.scroll_v.setContentsMargins(10, 10, 10, 10)
        self.scroll_v.setSpacing(5)
        self.scroll_v.addStretch()
        
        self.scroll.setWidget(self.scroll_content)
        list_layout.addWidget(self.scroll)
        layout.addWidget(list_group)
        
        # --- Bottom Section: Action ---
        self.btn_apply = QPushButton("🚀 Bắt đầu tối ưu ngay (Apply Fix)")
        self.btn_apply.setFixedHeight(55)
        self.btn_apply.setStyleSheet(ThemeManager.get_button_style("primary") + "font-size: 16px; border-radius: 16px;")
        self.btn_apply.clicked.connect(self.run_fix)
        layout.addWidget(self.btn_apply)

    def load_apps(self):
        if not self.adb.is_online(): return
        self.btn_refresh.setEnabled(False)
        self.btn_apply.setEnabled(False)
        self.search_input.setPlaceholderText("⏳ Đang quét danh sách app từ máy...")
        
        # Clear current
        for i in reversed(range(self.scroll_v.count())):
            item = self.scroll_v.itemAt(i)
            if item.widget(): item.widget().setParent(None)
        self.app_items = []
        
        try:
            output = self.adb.shell("pm list packages -3")
            pkgs = [line.replace("package:", "").strip() for line in output.splitlines() if line.startswith("package:")]
            pkgs.sort()
            
            for pkg in pkgs:
                name = pkg.split('.')[-1].title()
                icon = "📦"
                checked = False
                
                # Logic phân loại icon (Không tự động chọn để tránh nhầm lẫn)
                if "zalo" in pkg: icon, name = "💬", "Zalo"
                elif "orca" in pkg: icon, name = "🔵", "Messenger"
                elif "katana" in pkg: icon, name = "🟦", "Facebook"
                elif "telegram" in pkg: icon, name = "✈️", "Telegram"
                elif "whatsapp" in pkg: icon, name = "🟢", "WhatsApp"
                elif "viber" in pkg: icon, name = "🟣", "Viber"
                elif "revanced" in pkg: icon, name = "⚙️", "MicroG"
                elif "youtube" in pkg: icon, name = "📺", "YouTube"
                
                item = NotificationAppItem(pkg, name, icon, checked=False)
                self.app_items.append(item)
                self.scroll_v.insertWidget(self.scroll_v.count()-1, item)
                
            self.search_input.setPlaceholderText("🔍 Tìm nhanh ứng dụng...")
        except Exception as e:
            LogManager.log("Fix", f"Lỗi nạp app: {e}", "error")
        finally:
            self.btn_refresh.setEnabled(True)
            self.btn_apply.setEnabled(True)

    def filter_apps(self, text):
        text = text.lower()
        for item in self.app_items:
            item.setVisible(text in item.pkg.lower() or text in item.name_lbl.text().lower())

    def _select_by_packages(self, pkg_list):
        """Select items matching pkg_list (preset). Uncheck others."""
        for item in self.app_items:
            item.cb.setChecked(item.pkg in pkg_list)
            item.update_style()

    def toggle_all_selection(self, checked):
        for item in self.app_items:
            if item.isVisible():
                item.cb.setChecked(checked)
                item.update_style()
        self.btn_select_all.setText("Bỏ chọn tất cả" if checked else "Chọn tất cả")

    def run_fix(self):
        selected = [item.pkg for item in self.app_items if item.cb.isChecked()]
        if not selected:
            LogManager.log("Fix", "Vui lòng chọn ít nhất 1 ứng dụng.", "warning")
            return
            
        opts = {
            'notify': self.chk_notify.isChecked(),
            'battery': self.chk_battery.isChecked(),
            'autostart': self.chk_autostart.isChecked()
        }
        
        self.run_task("fix_social_notifications", 
                     name="Fix Social", 
                     packages=selected, 
                     options=opts)
    
    def refresh_state(self):
        if not self.app_items:
            self.load_apps()

    def reset(self):
        """Reset widget when device changes — clear app list"""
        self.app_items = []
        # Clear the scroll layout
        if hasattr(self, 'scroll_layout'):
            for i in reversed(range(self.scroll_layout.count())):
                item = self.scroll_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
        if hasattr(self, 'search_input'):
            self.search_input.clear()

# XiaomiOptimizerWidget (Hub version) removed — replaced by XiaomiToolsPage sidebar.
# Use XiaomiToolsPage from src/ui/pages/xiaomi_tools_page.py instead.
