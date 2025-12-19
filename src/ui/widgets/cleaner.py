# src/ui/widgets/cleaner.py
"""
Cleaner Widget
Displays cleaning options with a clean list interface.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QGraphicsDropShadowEffect, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
from src.ui.theme_manager import ThemeManager

class CleanerWorker(QThread):
    finished = Signal(str)
    
    def __init__(self, adb, action_type):
        super().__init__()
        self.adb = adb
        self.action_type = action_type
        
    def run(self):
        result = ""
        if self.action_type == "cache":
            result = self.adb.clean_app_cache()
        elif self.action_type == "dex":
            result = self.adb.clean_obsolete_dex()
        elif self.action_type == "telegram":
            result = self.adb.clean_messenger_data()
        
        self.finished.emit(result)

class CleanerItem(QFrame):
    def __init__(self, title, desc, btn_text, action_key, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.action_key = action_key
        
        self.setObjectName("CleanerItem")
        self.setStyleSheet(f"""
            #CleanerItem {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.05);
            }}
            #CleanerItem:hover {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}80; /* Slight tint on hover */
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Text Section
        v_text = QVBoxLayout()
        v_text.setSpacing(5)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        
        self.lbl_desc = QLabel(desc)
        self.lbl_desc.setStyleSheet(f"font-size: 13px; color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        self.lbl_desc.setWordWrap(True)
        
        v_text.addWidget(self.lbl_title)
        v_text.addWidget(self.lbl_desc)
        
        layout.addLayout(v_text, stretch=1)
        
        # Button Section
        self.btn = QPushButton(f"🗑️ {btn_text}")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setFixedSize(120, 40)
        # Red style for cleaner buttons (Danger/Warning)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff4757; 
                color: white;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                font-size: 13px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: #ff6b81;
            }}
            QPushButton:pressed {{
                background-color: #ced6e0;
                color: #2f3542;
            }}
            QPushButton:disabled {{
                background-color: #f1f2f6;
                color: #a4b0be;
            }}
        """)
        self.btn.clicked.connect(self.on_click)
        
        layout.addWidget(self.btn)
        
    def on_click(self):
        self.btn.setEnabled(False)
        self.btn.setText("Đang chạy...")
        self.parent_widget.run_cleaner(self.action_key, self)

    def reset_btn(self, original_text):
        self.btn.setEnabled(True)
        self.btn.setText(f"🗑️ {original_text}")

class CleanerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Scroll Area container for long lists
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(10, 10, 10, 10)
        c_layout.setSpacing(15) 
        
        # Header (optional, usually provided by tab)
        # We can add a hero section if we expect it to be empty, e.g. "Scanning..."
        
        # Item 1: Cache
        self.item_cache = CleanerItem(
            "Dọn Dẹp Bộ Nhớ Đệm Tất Cả Ứng Dụng",
            "Xóa cache hệ thống để giải phóng dung lượng (pm trim-caches)",
            "Dọn Dẹp",
            "cache",
            self
        )
        c_layout.addWidget(self.item_cache)
        
        # Item 2: Dex
        self.item_dex = CleanerItem(
            "Dọn Dẹp Tệp Dex Lỗi Thời",
            "Xóa các file biên dịch cũ không còn sử dụng (prune-dex-opt)",
            "Dọn Dẹp",
            "dex",
            self
        )
        c_layout.addWidget(self.item_dex)
        
        # Item 3: Telegram
        self.item_tele = CleanerItem(
            "Dọn Dẹp Dữ Liệu Telegram, Nekogram",
            "Xóa cache hình ảnh, video đã tải xuống của Telegram",
            "Dọn Dẹp",
            "telegram",
            self
        )
        c_layout.addWidget(self.item_tele)
        
        c_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def run_cleaner(self, action_key, item_widget):
        worker = CleanerWorker(self.adb, action_key)
        
        def on_done(result):
            # Restore button state
            item_widget.reset_btn("Dọn Dẹp")
            
            # Since we don't have a toast notification system readily available in this scope, 
            # we rely on the button text or console.
            # Assuming main window might handle logs, but here we just reset.
            # Ideally: pop a small message or change desc.
            pass
            
        worker.finished.connect(on_done)
        worker.start()
        self.worker = worker
