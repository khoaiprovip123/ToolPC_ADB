# src/ui/widgets/advanced_optimizer.py
"""
Advanced Optimizer Widget
Features: Notification Whitelist, App Compilation (Speed/Battery), ART Optimization.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QLineEdit, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal
from src.ui.theme_manager import ThemeManager

class OptimizerWorker(QThread):
    finished = Signal(str)
    
    def __init__(self, adb, action_type, payload=None):
        super().__init__()
        self.adb = adb
        self.action_type = action_type
        self.payload = payload
        
    def run(self):
        result = ""
        if self.action_type == "notify":
            result = self.adb.optimize_notifications(self.payload)
        elif self.action_type == "compile":
            result = self.adb.compile_apps(self.payload)
        
        self.finished.emit(result)

class AdvancedOptimizerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(10, 10, 10, 10)
        c_layout.setSpacing(15)
        
        # 1. Notification Optimization
        self.create_section(
            c_layout, 
            "Tối Ưu Hóa Thông Báo", 
            "Giúp ứng dụng nhận thông báo ngay lập tức (Thêm vào Doze Whitelist)",
            self.create_notify_ui()
        )
        
        # 2. Speed Optimization
        self.create_section(
            c_layout,
            "Tối Ưu Hóa Tốc Độ Mở Ứng Dụng",
            "Biên dịch toàn bộ ứng dụng sang mã máy (Mode: Speed)",
            self.create_action_ui("Tối Ưu Hóa", "speed")
        )
        
        # 3. Battery Optimization
        self.create_section(
            c_layout,
            "Tối Ưu Hóa Pin",
            "Cân bằng giữa hiệu năng và dung lượng (Mode: Quicken)",
            self.create_action_ui("Tối Ưu Hóa", "quicken")
        )
        
        # 4. ART Optimization
        self.create_art_section(c_layout)

        c_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def create_section(self, parent_layout, title, desc, content_widget=None):
        frame = QFrame()
        frame.setStyleSheet(ThemeManager.get_card_style())
        
        l = QVBoxLayout(frame)
        l.setContentsMargins(20, 20, 20, 20)
        
        t = QLabel(title)
        t.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        d = QLabel(desc)
        d.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px; margin-bottom: 15px;")
        
        l.addWidget(t)
        l.addWidget(d)
        if content_widget:
            l.addWidget(content_widget)
            
        parent_layout.addWidget(frame)

    def create_notify_ui(self):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        self.input_pkgs = QLineEdit()
        self.input_pkgs.setPlaceholderText("com.facebook.orca, com.zing.zalo, ...")
        self.input_pkgs.setText("com.facebook.orca,com.facebook.katana,com.zing.zalo")
        self.input_pkgs.setStyleSheet(ThemeManager.get_input_style())
        
        btn = QPushButton("Tối Ưu Hóa")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn.clicked.connect(lambda: self.run_notify_opt(btn))
        
        l.addWidget(self.input_pkgs)
        l.addWidget(btn)
        return w

    def create_action_ui(self, btn_text, mode):
        btn = QPushButton(f"{btn_text}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn.clicked.connect(lambda: self.run_compile(mode, btn))
        return btn

    def create_art_section(self, parent_layout):
        frame = QFrame()
        frame.setStyleSheet(ThemeManager.get_card_style())
        
        l = QVBoxLayout(frame)
        l.setContentsMargins(20, 20, 20, 20)
        
        t = QLabel("Tối Ưu Hóa ART")
        t.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        l.addWidget(t)
        
        # Grid of options
        options = [
            ("Dành Cho Sử Dụng Hàng Ngày", "speed-profile"),
            ("Dành Cho Khởi Động Lần Đầu", "verify"),
            ("Dành Cho Sau Khi Cập Nhật OTA", "bg-dexopt-job"),
            ("Dành Cho Sau Tại Cập Nhật Google Play", "quicken") 
        ]
        
        for text, mode in options:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 5, 0, 5)
            
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 14px;")
            
            btn = QPushButton("Tối Ưu Hóa")
            btn.setFixedSize(120, 35)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(ThemeManager.get_button_style("outline"))
            btn.clicked.connect(lambda checked=False, m=mode, b=btn: self.run_compile(m, b))
            
            rl.addWidget(lbl)
            rl.addStretch()
            rl.addWidget(btn)
            l.addWidget(row)
            
        parent_layout.addWidget(frame)

    def run_notify_opt(self, btn):
        pkgs = self.input_pkgs.text()
        self.start_worker("notify", pkgs, btn)

    def run_compile(self, mode, btn):
        self.start_worker("compile", mode, btn)

    def start_worker(self, action, payload, btn):
        # Disable button and show running state
        original_text = btn.text()
        btn.setEnabled(False)
        btn.setText("Đang chạy...")
        
        worker = OptimizerWorker(self.adb, action, payload)
        
        def on_done(res):
            print(res) 
            # Show completed state
            btn.setText("Hoàn tất!")
            QThread.msleep(500) # Valid wait for visual feedback
            
            # Reset
            btn.setEnabled(True)
            btn.setText(original_text)
            
        worker.finished.connect(on_done)
        worker.start()
        self.worker = worker
