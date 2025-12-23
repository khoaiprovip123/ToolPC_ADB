# src/ui/widgets/xiaomi_optimizer.py
"""
Xiaomi Optimizer Widget - Debloat and Optimize MIUI
Style: Glassmorphism & Gradient Cards
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QCheckBox, QHeaderView, QMessageBox,
    QTabWidget, QTextEdit, QGroupBox, QProgressBar, QScrollArea, QFrame,
    QGraphicsDropShadowEffect, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QGradient
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager
from PySide6.QtWidgets import QDialog

# Reuse GradientCard logic or import if shared (Defining here for simplicity/independence)
class ModernCard(QFrame):
    def __init__(self, title, desc, icon, callback, gradient_colors=None, parent=None):
        super().__init__(parent)
        self.callback = callback
        
        bg_style = "background-color: white;"
        text_color = ThemeManager.COLOR_TEXT_PRIMARY
        desc_color = ThemeManager.COLOR_TEXT_SECONDARY
        
        if gradient_colors:
            bg_style = f"background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {gradient_colors[0]}, stop:1 {gradient_colors[1]});"
            text_color = "white"
            desc_color = "rgba(255,255,255,0.8)"
            
        self.setObjectName("ModernCard")
        self.setStyleSheet(f"""
            #ModernCard {{
                {bg_style}
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,0.05);
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {text_color}; background: transparent; border: none;")
        
        header.addWidget(icon_lbl)
        header.addSpacing(10)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        # Description
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 13px; color: {desc_color}; margin-top: 5px; background: transparent; border: none;")
        layout.addWidget(desc_lbl)
        
        layout.addStretch()
        
        # Button
        btn = QPushButton("Thực hiện 🚀")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.on_click)
        
        btn_bg = "rgba(255,255,255,0.2)" if gradient_colors else ThemeManager.COLOR_ACCENT
        btn_text = "white"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.3);
            }}
        """)
        layout.addWidget(btn)

    def on_click(self):
        if self.callback:
            self.callback()


class DebloatWorker(QThread):
    """Background worker for debloating"""
    progress = Signal(str)
    finished = Signal()
    
    def __init__(self, adb, packages):
        super().__init__()
        self.adb = adb
        self.packages = packages
        self._is_running = True
        
    def run(self):
        for package in self.packages:
            if not self._is_running:
                break
            
            try:
                self.progress.emit(f"Đang xử lý: {package}...")
                # Uninstall for user 0 (safe removal)
                result = self.adb.shell(f"pm uninstall --user 0 {package}")
                
                if "success" in result.lower():
                    self.progress.emit(f"✅ Đã gỡ: {package}")
                else:
                    # Try disable if uninstall fails
                    self.adb.shell(f"pm disable-user --user 0 {package}")
                    self.progress.emit(f"⚠️ Đã tắt: {package}")
                    
            except Exception as e:
                self.progress.emit(f"❌ Lỗi {package}: {e}")
                
        self.finished.emit()
        
    def stop(self):
        self._is_running = False


class OptimizationWorker(QThread):
    """Background worker for optimizations"""
    progress = Signal(str)
    result_ready = Signal(dict) # new signal for results
    error_occurred = Signal(str, str) # title, message
    finished = Signal()
    
    def __init__(self, adb, task_type):
        super().__init__()
        self.adb = adb
        self.task_type = task_type
        
    def run(self):
        try:
            if self.task_type == "full_scan":
                self.progress.emit("🔍 Đang quét hệ thống...")
                self.progress.emit("Đang kiểm tra MSA...")
                self.adb.disable_msa()
                self.progress.emit("✅ Đã xử lý System Ads")
                self.progress.emit("Đang xử lý Analytics...")
                self.adb.disable_analytics()
                self.progress.emit("✅ Đã tắt Theo dõi")
                self.progress.emit("Đang tối ưu hiệu ứng...")
                self.adb.optimize_animations(0.5)
                self.progress.emit("✅ Đã tăng tốc hiệu ứng")
                
            elif self.task_type == "animations":
                self.progress.emit("Đang tăng tốc hiệu ứng (0.5x)...")
                self.adb.optimize_animations(0.5)
                self.progress.emit("✅ Đã đặt tỷ lệ hiệu ứng 0.5x")

            elif self.task_type == "set_vietnamese":
                self.progress.emit("🇻🇳 Đang cài đặt Tiếng Việt...")
                result = self.adb.set_language_vietnamese()
                self.progress.emit(f"ℹ️ {result}")
                
            elif self.task_type == "fix_eu_vn":
                self.progress.emit("🌍 Đang sửa lỗi vùng EU_VN...")
                self.adb.set_prop("persist.sys.country", "VN")
                self.adb.set_prop("ro.product.locale", "vi-VN") 
                self.adb.set_system_setting("system", "time_12_24", "24")
                self.progress.emit("✅ Đã cập nhật Region VN & Time 24h")

            elif self.task_type == "check_status":
                self.progress.emit("🔍 Đang đọc thông số hệ thống...")
                status = self.adb.get_language_region_status()
                self.result_ready.emit(status)
                self.progress.emit("✅ Đã đọc dữ liệu xong")

            elif self.task_type == "smart_blur":
                self.progress.emit("✨ Đang phân tích cấu hình & kích hoạt Blur...")
                result = self.adb.apply_smart_blur()
                self.progress.emit(f"✅ {result}")

            elif self.task_type == "stacked_recent":
                self.progress.emit("📚 Đang kích hoạt giao diện Xếp chồng...")
                self.adb.shell("settings put global task_stack_view_layout_style 2")
                self.progress.emit("🔄 Đang khởi động lại Launcher để áp dụng...")
                self.adb.shell("am force-stop com.miui.home")
                self.progress.emit("✅ Đã áp dụng giao diện Xếp chồng")

            elif self.task_type == "skip_setup":
                self.progress.emit("⏩ Đang bỏ qua Setup Wizard...")
                result = self.adb.skip_setup_wizard()
                self.progress.emit(result)

            elif self.task_type == "disable_ota":
                self.progress.emit("🛑 Đang chặn cập nhật hệ thống...")
                result = self.adb.disable_miui_ota()
                self.progress.emit(result)

            elif self.task_type == "force_refresh_rate":
                hz = 0
                if hasattr(self, 'refresh_rate'):
                    hz = self.refresh_rate
                label = "Mặc định (Auto)" if hz <= 0 else f"{hz}Hz"
                self.progress.emit(f"⚡ Đang áp dụng tần số quét {label}...")
                result = self.adb.set_refresh_rate(hz)
                self.progress.emit(result)

            elif self.task_type == "force_dark_mode_on":
                self.progress.emit("🌙 Đang bật Dark Mode hệ thống...")
                result = self.adb.force_dark_mode(True)
                self.progress.emit(result)

            elif self.task_type == "force_dark_mode_off":
                self.progress.emit("☀️ Đang tắt Dark Mode hệ thống...")
                result = self.adb.force_dark_mode(False)
                self.progress.emit(result)

            elif self.task_type == "hide_nav_on":
                self.progress.emit("↔️ Đang ẩn thanh điều hướng...")
                result = self.adb.hide_navigation_bar(True)
                self.progress.emit(result)

            elif self.task_type == "hide_nav_off":
                self.progress.emit("↔️ Đang hiện thanh điều hướng...")
                result = self.adb.hide_navigation_bar(False)
                self.progress.emit(result)

            elif self.task_type == "set_dpi":
                if hasattr(self, 'dpi_value'):
                    self.progress.emit(f"📱 Đang đổi DPI sang {self.dpi_value}...")
                    result = self.adb.set_display_density(self.dpi_value)
                    self.progress.emit(result)

            elif self.task_type == "show_fps_on":
                 self.progress.emit("📈 Đang bật bộ đếm FPS...")
                 result = self.adb.show_refresh_rate_overlay(True)
                 self.progress.emit(result)

            elif self.task_type == "show_fps_off":
                 self.progress.emit("📉 Đang tắt bộ đếm FPS...")
                 result = self.adb.show_refresh_rate_overlay(False)
                 self.progress.emit(result)

            elif self.task_type == "open_dev_options":
                 self.progress.emit("⚙️ Đang mở Cài đặt nhà phát triển...")
                 result = self.adb.open_developer_options()
                 self.progress.emit(result)

        except Exception as e:
            err_str = str(e)
            if "SecurityException" in err_str:
                self.progress.emit("⚠️ Lỗi: Thiếu quyền Bảo mật Xiaomi")
                details = (
                    "Hệ thống báo lỗi bảo mật:\n\n"
                    f"{err_str}\n\n"
                    "👉 Hãy chắc chắn bạn đã bật cả 2 dòng trong Tùy chọn nhà phát triển:\n"
                    "1. Gỡ lỗi USB\n"
                    "2. Gỡ lỗi USB (Cài đặt bảo mật) [- Cần SIM]"
                )
                self.error_occurred.emit("Thiếu Quyền Bảo Mật", details)
            else:
                self.progress.emit(f"❌ Lỗi: {e}")
                
        self.finished.emit()


# Module Level Constants
BLOATWARE_DICT = {
    "Dịch vụ Quảng cáo & Theo dõi 🚫": [
        "com.miui.analytics",
        "com.miui.msa.global",
        "com.xiaomi.joyose", 
        "com.google.android.gms.location.history",
        "com.miui.systemadsolution",
        "com.miui.hybrid.accessory",
        "com.xiaomi.discover",
    ],
    "Ứng dụng Rác Hệ thống (An toàn) 🗑️": [
        "com.miui.calculator",
        "com.miui.compass",
        "com.miui.fm",
        "com.miui.notes",
        "com.miui.screenrecorder",
        "com.miui.videoplayer",
        "com.miui.player",
        "com.android.email",
        "com.miui.yellowpage",
        "com.miui.bugreport",
        "com.miui.miservice",
    ],
    "Xiaomi Cloud & Sync ☁️": [
        "com.miui.cloudservice",
        "com.miui.cloudbackup",
        "com.miui.micloudsync",
        "com.xiaomi.midrop", 
        "com.miui.virtualsim",
        "com.xiaomi.payment",
    ],
    "Partner Apps & Facebook 👎": [
        "com.facebook.appmanager",
        "com.facebook.services",
        "com.facebook.system",
        "com.netflix.partner.activation",
        "com.ebay.carrier",
        "com.ebay.mobile",
        "com.linkedin.android",
    ]
}


class XiaomiBaseWidget(QWidget):
    """Base widget with shared helper methods"""
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.opt_worker = None
        self.worker = None
        
    def show_error(self, title, message):
        QMessageBox.warning(self, title, message)
    
    def check_device(self, status_label):
        """Helper to update a status label with device info"""
        if not self.adb.current_device:
            status_label.setText("🚫 Chưa kết nối thiết bị")
            self.setEnabled(False)
            return

        try:
            info = self.adb.get_device_info()
            brand_raw = self.adb.shell("getprop ro.product.brand")
            brand = brand_raw.strip().lower() if brand_raw else ""
            manufacturer = (info.manufacturer or "").lower()
            xiaomi_ids = ["xiaomi", "redmi", "poco", "blackshark", "mi", "mix", "meitu"]
            
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
            self.setEnabled(False)
            
    def show_status_dialog(self, status):
        msg = "<b>Trạng thái Ngôn ngữ & Vùng hiện tại:</b><br><br>"
        for k, v in status.items():
            color = "#2ecc71" if "VN" in v or "vi" in v else "#e74c3c"
            msg += f"<b>{k}:</b> <span style='color:{color}'>{v}</span><br>"
        msg += "<br><i>Vui lòng Khởi động lại nếu các thông số đã đúng nhưng chưa áp dụng.</i>"
        QMessageBox.information(self, "Kiểm tra Hệ thống", msg)


class XiaomiDebloaterWidget(XiaomiBaseWidget):
    """Widget for removing bloatware"""
    def __init__(self, adb_manager):
        super().__init__(adb_manager)
        self.check_groups = {}
        self.setup_ui()
        self.check_device(self.status_label)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header - Simplified for tab context
        # self.setup_header(layout) # Only if standalone? Or reuse.
        
        # We add a status label here since we check device
        self.status_label = QLabel("Đang kiểm tra...")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600; margin-bottom: 10px;")
        layout.addWidget(self.status_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # App List Table logic
        self.setup_app_table(content_layout)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def setup_app_table(self, layout):
        label = QLabel("Gỡ ứng dụng rác (Debloater)")
        label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY}; margin-top: 10px;")
        layout.addWidget(label)
        
        container = QFrame()
        container.setObjectName("DebloatContainer")
        container.setStyleSheet(f"""
            #DebloatContainer {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.6);
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        self.check_groups = {}
        
        # Use Global BLOATWARE_DICT
        for category, apps in BLOATWARE_DICT.items():
            group = QGroupBox(category)
            group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 1px solid rgba(0,0,0,0.1);
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 20px;
                    color: {ThemeManager.COLOR_TEXT_PRIMARY};
                    background: rgba(255,255,255,0.4);
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }}
            """)
            group_layout = QVBoxLayout(group)
            
            for app in apps:
                cb = QCheckBox(app)
                cb.setCursor(Qt.PointingHandCursor)
                theme = ThemeManager.get_theme()
                cb.setStyleSheet(f"""
                    QCheckBox {{
                        color: {ThemeManager.COLOR_TEXT_PRIMARY};
                        font-size: 14px;
                        spacing: 12px;
                    }}
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
                        image: url(none);
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: {ThemeManager.COLOR_ACCENT};
                    }}
                """)
                group_layout.addWidget(cb)
                self.check_groups[app] = cb
            
            container_layout.addWidget(group)
            
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_clean = QPushButton("🗑️ Gỡ bỏ các mục đã chọn")
        btn_clean.setStyleSheet(ThemeManager.get_button_style("danger"))
        btn_clean.setFixedSize(220, 45)
        btn_clean.clicked.connect(self.start_debloat)
        
        btn_layout.addWidget(btn_clean)
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(container)

    def start_debloat(self):
        selected = [app for app, cb in self.check_groups.items() if cb.isChecked()]
        
        if not selected:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất một ứng dụng")
            return
            
        confirm = QMessageBox.warning(
            self, "Xác nhận An toàn",
            f"Bạn sắp gỡ bỏ {len(selected)} ứng dụng hệ thống.\nHãy chắc chắn bạn đã sao lưu!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.worker = DebloatWorker(self.adb, selected)
            self.worker.progress.connect(lambda msg: LogManager.log("Debloater", msg, "info"))
            self.worker.start()
            
    def reset(self):
        self.check_device(self.status_label)
        for cb in self.check_groups.values():
            cb.setChecked(False)


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

        grid.setRowStretch(2, 1) # Push to top
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def optimize_animations(self):
        self.opt_worker = OptimizationWorker(self.adb, "animations")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Animations", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_smart_blur(self):
        self.opt_worker = OptimizationWorker(self.adb, "smart_blur")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Smart Blur", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_hyperos_stacked_recent(self):
        try:
            info = self.adb.get_device_info()
            android_ver = 0
            if info.android_version and info.android_version != "Unknown":
                try:
                    android_ver = int(str(info.android_version).split('.')[0])  
                except:
                    pass
            
            if android_ver < 14:
                QMessageBox.warning(self, "Không hỗ trợ", f"Yêu cầu Android 14+ (Hiện tại: {info.android_version})")
                return

            if not info.hyperos_version:
                 QMessageBox.warning(self, "Không hỗ trợ", "Chỉ hỗ trợ Xiaomi HyperOS.")
                 return

            brand = self.adb.shell("getprop ro.product.brand").strip().lower()
            if "poco" in brand:
                 QMessageBox.warning(self, "Chưa hỗ trợ POCO", "POCO Launcher chưa hỗ trợ tính năng này.")
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
                import re
                def parse_version(v_str):
                    return [int(n) for n in re.findall(r'\d+', v_str)]

                current_ver = parse_version(version_str)
                required_ver = parse_version("RELEASE-6.01.03.1924")
                
                if current_ver < required_ver:
                     from PySide6.QtGui import QDesktopServices
                     from PySide6.QtCore import QUrl
                     
                     msg = QMessageBox(self)
                     msg.setIcon(QMessageBox.Warning)
                     msg.setWindowTitle("Phiên bản Launcher cũ")
                     msg.setText(f"Yêu cầu HyperOS Launcher >= RELEASE-6.01.03.1924\nHiện tại: {version_str}")
                     btn_download = msg.addButton("Tải bản cập nhật 🌐", QMessageBox.ActionRole)
                     msg.addButton("Đóng", QMessageBox.RejectRole)
                     msg.exec()
                     
                     if msg.clickedButton() == btn_download:
                         QDesktopServices.openUrl(QUrl("https://hyperosupdates.com/apps/com.miui.home"))
                     return
        except:
             pass

        self.opt_worker = OptimizationWorker(self.adb, "stacked_recent")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Stacked Recent", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
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

        self.opt_worker = OptimizationWorker(self.adb, task)
        self.opt_worker.progress.connect(lambda m: LogManager.log("FPS Monitor", m, "info"))
        self.opt_worker.start()

    def run_set_dpi(self):
        from PySide6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getInt(self, "Đổi DPI Màn hình", "Nhập giá trị DPI mong muốn (Ví dụ: 392, 440, 480...)\nNhập 0 để Reset về mặc định.", value=0, minValue=0, maxValue=999)
        if ok:
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
        self.opt_worker = OptimizationWorker(self.adb, task)
        self.opt_worker.progress.connect(lambda m: LogManager.log("Dark Mode", m, "info"))
        self.opt_worker.start()

    def run_disable_ota(self):
        reply = QMessageBox.question(self, "Chặn Cập Nhật", "Bạn có muốn chặn vĩnh viễn tính năng Cập nhật Hệ thống (OTA)?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.opt_worker = OptimizationWorker(self.adb, "disable_ota")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Disable OTA", msg, "info"))
            self.opt_worker.start()

    def run_skip_setup(self):
        reply = QMessageBox.question(self, "Xác nhận", "Tiện ích này giúp bỏ qua các bước thiết lập ban đầu sau khi Reset máy.\nBạn có muốn tiếp tục?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
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
        self.opt_worker = OptimizationWorker(self.adb, task)
        self.opt_worker.progress.connect(lambda m: LogManager.log("Nav Bar", m, "info"))
        self.opt_worker.start()

    def run_set_vietnamese(self):
        confirm = QMessageBox.question(self, "Xác nhận", "Thao tác này sẽ gửi lệnh thay đổi ngôn ngữ hệ thống sang vi-VN.\nThiết bị cần KHỞI ĐỘNG LẠI để áp dụng.\n\nBạn có muốn tiếp tục?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.opt_worker = OptimizationWorker(self.adb, "set_vietnamese")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Language", msg, "info"))
            self.opt_worker.error_occurred.connect(self.show_error)
            self.opt_worker.start()

    def run_fix_eu_vn(self):
        self.opt_worker = OptimizationWorker(self.adb, "fix_eu_vn")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Region Fix", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_verify_status(self):
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
        self.check_device(self.status_label)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header (Unified Banner)
        self.setup_header(layout)

        # Status Label
        self.status_label = QLabel("Đang kiểm tra thiết bị...")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600; margin-left: 20px;")
        layout.addWidget(self.status_label)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{
                background: transparent;
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                padding: 12px 20px;
                font-weight: 600;
                font-size: 14px;
                margin-right: 5px;
                border-bottom: 3px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {ThemeManager.COLOR_ACCENT};
                border-bottom: 3px solid {ThemeManager.COLOR_ACCENT};
            }}
            QTabBar::tab:hover {{ background: rgba(0,0,0,0.05); border-radius: 5px; }}
        """)
        
        # Add modular widgets
        self.tabs.addTab(XiaomiDebloaterWidget(self.adb), "Tối Ưu Chung")
        self.tabs.addTab(XiaomiQuickToolsWidget(self.adb), "Tiện Ích Xiaomi")
        self.tabs.addTab(XiaomiAdvancedWidget(self.adb), "Tính năng Nâng cao")
        
        layout.addWidget(self.tabs)

    def setup_header(self, layout):
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #FF9A9E, stop:1 #FECFEF);
                border-radius: 20px;
                border: none;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0,20))
        shadow.setOffset(0,5)
        container.setGraphicsEffect(shadow)
        
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(30, 30, 30, 30)
        
        text_layout = QVBoxLayout()
        title = QLabel("Xiaomi Turbo Suite")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: white; background: transparent;")
        desc = QLabel("Tối ưu hóa toàn diện cho thiết bị MIUI/HyperOS.")
        desc.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px; background: transparent;")
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        h_layout.addLayout(text_layout)
        h_layout.addSpacing(20)
        
        btn = QPushButton("⚡ Quét & Tối Ưu")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(180, 50)
        btn.setStyleSheet("QPushButton { background-color: white; color: #FF9A9E; font-weight: bold; border-radius: 25px; border: none; } QPushButton:hover { background-color: #fafafa; }")
        btn.clicked.connect(self.run_full_optimization)
        h_layout.addWidget(btn)
        
        layout.addWidget(container)
        
    def run_full_optimization(self):
        self.opt_worker = OptimizationWorker(self.adb, "full_scan")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Optimization", msg, "info"))
        self.opt_worker.start()

