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
                
                # Check MSA
                self.progress.emit("Đang kiểm tra MSA...")
                self.adb.disable_msa() # Attempt disable
                self.progress.emit("✅ Đã xử lý System Ads")
                
                # Check Analytics
                self.progress.emit("Đang xử lý Analytics...")
                self.adb.disable_analytics()
                self.progress.emit("✅ Đã tắt Theo dõi")
                
                # Speed Animations
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
                # We access the optimization manager indirectly or just run raw command here as per current pattern
                # Current pattern in worker seems to be direct adb calls or adb manager methods. 
                # Let's check if optimization methods are in ADBManager or we should use OptimizationManager.
                # The existing worker uses self.adb which is ADBManager.
                # Since I added enable_hyperos_stacked_recent to OptimizationManager, I should ideally use that,
                # BUT this worker takes 'adb' (ADBManager). 
                # To be consistent with existing pattern in this file which calls adb methods directly:
                self.adb.shell("settings put global task_stack_view_layout_style 2")
                self.progress.emit("✅ Đã áp dụng (Yêu cầu HyperOS Launcher mới)")


                
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


class XiaomiOptimizerWidget(QWidget):
    """
    Xiaomi Optimizer Widget
    """
    
    BLOATWARE = {
        "Dịch vụ Quảng cáo & Theo dõi 🚫": [
            "com.miui.analytics",
            "com.miui.msa.global",
            "com.xiaomi.joyose", # Game booster but also throttles
            "com.google.android.gms.location.history",
            "com.miui.systemadsolution",
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
            "com.xiaomi.midrop", # Mi Share
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
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.worker = None
        self.opt_worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll Area for main content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(0,0,0,0.03);
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.2);
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0,0,0,0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # 1. Header with One-Click
        self.setup_header(content_layout)
        
        # 2. Optimization Cards Grid
        self.setup_opt_grid(content_layout)

        # 2.5 Language Section
        self.setup_language_section(content_layout)
        
        # 3. Debloat Section
        self.setup_debloat_section(content_layout)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        self.check_device()
        
    def setup_header(self, layout):
        container = QFrame()
        container.setObjectName("HeaderContainer")
        container.setStyleSheet(f"""
            #HeaderContainer {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #FF9A9E, stop:1 #FECFEF);
                border-radius: 20px;
                border: none;
            }}
        """)
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0,20))
        shadow.setOffset(0,5)
        container.setGraphicsEffect(shadow)
        
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(30, 30, 30, 30)
        
        # Text
        text_layout = QVBoxLayout()
        title = QLabel("Xiaomi Turbo Suite")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: white; background: transparent;")
        desc = QLabel("Tối ưu hóa toàn diện cho thiết bị MIUI/HyperOS của bạn chỉ với một cú nhấp chuột.")
        desc.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.9); margin-top: 5px; background: transparent;")
        desc.setWordWrap(True)
        
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        h_layout.addLayout(text_layout)
        
        h_layout.addSpacing(20)
        
        # Big Button
        btn = QPushButton("⚡ Quét & Tối Ưu Ngay")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(200, 50)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #FF9A9E;
                font-weight: bold;
                font-size: 16px;
                border-radius: 25px;
                border: none;
            }
            QPushButton:hover {
                background-color: #fafafa;
                margin-top: -2px;
            }
            QPushButton:pressed {
                margin-top: 0px;
            }
        """)
        btn.clicked.connect(self.run_full_optimization)
        
        # Button Shadow
        btn_shadow = QGraphicsDropShadowEffect(btn)
        btn_shadow.setBlurRadius(15)
        btn_shadow.setColor(QColor(0,0,0,30))
        btn_shadow.setOffset(0,4)
        btn.setGraphicsEffect(btn_shadow)
        
        h_layout.addWidget(btn)
        
        layout.addWidget(container)
        
        # Status Label below header
        self.status_label = QLabel("Đang kiểm tra thiết bị...")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600; margin-left: 10px;")
        layout.addWidget(self.status_label)

    def setup_opt_grid(self, layout):
        label = QLabel("Công cụ nhanh")
        label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(label)
        
        grid = QGridLayout()
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
        
        # Stacked Recent Card (HyperOS 3)
        card_stack = ModernCard(
            "HyperOS 3 Đa nhiệm Xếp chồng",
            "Kích hoạt giao diện đa nhiệm kiểu Stack (iOS). Cần HyperOS Launcher mới nhất.",
            "📚",
            self.run_hyperos_stacked_recent,
            gradient_colors=["#a18cd1", "#fbc2eb"]
        )
        grid.addWidget(card_stack, 1, 0)

        layout.addLayout(grid)

    def setup_language_section(self, layout):
        label = QLabel("Ngôn ngữ & Khu vực (Language & Region)")
        label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY}; margin-top: 10px;")
        layout.addWidget(label)
        
        grid = QGridLayout()
        grid.setSpacing(20)
        
        # Set Vietnamese
        card_vn = ModernCard(
            "Cài Tiếng Việt (VN)", 
            "Ép buộc ngôn ngữ hệ thống sang Tiếng Việt (vi-VN) qua ADB. Yêu cầu khởi động lại.", 
            "🇻🇳", 
            self.run_set_vietnamese,
            gradient_colors=["#ee0979", "#ff6a00"]
        )
        grid.addWidget(card_vn, 0, 0)
        
        # Fix Region EU
        card_region = ModernCard(
            "Fix Region EU_VN", 
            "Sửa lỗi định dạng vùng, ngày giờ và quốc gia cho ROM EU/Convert.", 
            "🌍",
            self.run_fix_eu_vn,
            gradient_colors=["#11998e", "#38ef7d"]
        )
        grid.addWidget(card_region, 0, 1)

        # Verify Link
        btn_verify = QPushButton("🔍 Kiểm tra cài đặt hiện tại")
        btn_verify.setCursor(Qt.PointingHandCursor)
        btn_verify.setStyleSheet(f"""
            QPushButton {{
                color: {ThemeManager.COLOR_ACCENT};
                background: transparent;
                border: 1px solid {ThemeManager.COLOR_ACCENT};
                border-radius: 8px;
                padding: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(0,0,0,0.05);
            }}
        """)
        btn_verify.clicked.connect(self.run_verify_status)
        layout.addWidget(btn_verify)
        
        layout.addLayout(grid)

    def setup_debloat_section(self, layout):
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
        
        for category, apps in self.BLOATWARE.items():
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

    def check_device(self):
        if not self.adb.current_device:
            self.status_label.setText("🚫 Chưa kết nối thiết bị")
            self.setEnabled(False)
            return

        try:
            brand = self.adb.shell("getprop ro.product.brand").strip().lower()
            
            # Fetch full info to get HyperOS version
            info = self.adb.get_device_info()
            
            if "xiaomi" in brand or "redmi" in brand or "poco" in brand:
                if info.hyperos_version:
                     self.status_label.setText(f"✅ Đã kết nối: Xiaomi HyperOS ({info.hyperos_version})")
                elif info.miui_version:
                     self.status_label.setText(f"✅ Đã kết nối: MIUI ({info.miui_version})")
                else:
                     self.status_label.setText("✅ Đã phát hiện thiết bị Xiaomi/Redmi/Poco")
                     
                self.setEnabled(True)
            else:
                self.status_label.setText(f"⚠️ Thiết bị {brand} có thể không tương thích hoàn toàn")
                self.setEnabled(True)
        except:
            self.status_label.setText("❓ Không thể xác định thiết bị")

    def run_full_optimization(self):
        # self.log_panel.clear()
        self.opt_worker = OptimizationWorker(self.adb, "full_scan")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Optimization", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def optimize_animations(self):
        # self.log_panel.clear()
        self.opt_worker = OptimizationWorker(self.adb, "animations")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Animations", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_set_vietnamese(self):
        confirm = QMessageBox.question(
            self, "Xác nhận", 
            "Thao tác này sẽ gửi lệnh thay đổi ngôn ngữ hệ thống sang vi-VN.\nThiết bị cần KHỞI ĐỘNG LẠI để áp dụng.\n\nBạn có muốn tiếp tục?",
            QMessageBox.Yes | QMessageBox.No
        )
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

    def run_smart_blur(self):
        self.opt_worker = OptimizationWorker(self.adb, "smart_blur")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Smart Blur", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def run_hyperos_stacked_recent(self):
        self.opt_worker = OptimizationWorker(self.adb, "stacked_recent")
        self.opt_worker.progress.connect(lambda msg: LogManager.log("Stacked Recent", msg, "info"))
        self.opt_worker.error_occurred.connect(self.show_error)
        self.opt_worker.start()

    def show_status_dialog(self, status):
        msg = "<b>Trạng thái Ngôn ngữ & Vùng hiện tại:</b><br><br>"
        
        # Color code functionality
        for k, v in status.items():
            color = "#2ecc71" if "VN" in v or "vi" in v else "#e74c3c"
            msg += f"<b>{k}:</b> <span style='color:{color}'>{v}</span><br>"
            
        msg += "<br><i>Vui lòng Khởi động lại nếu các thông số đã đúng nhưng chưa áp dụng.</i>"
        
        QMessageBox.information(self, "Kiểm tra Hệ thống", msg)

    def show_error(self, title, message):
        QMessageBox.warning(self, title, message)

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
            # self.log_panel.clear()
            self.worker = DebloatWorker(self.adb, selected)
            self.worker.progress.connect(lambda msg: LogManager.log("Debloater", msg, "info"))
            self.worker.start()
            
    def reset(self):
        self.check_device()
        # self.log_panel.clear()
        for cb in self.check_groups.values():
            cb.setChecked(False)
