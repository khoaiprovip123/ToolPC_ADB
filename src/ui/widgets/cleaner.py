# src/ui/widgets/cleaner.py
"""
Cleaner Widget — Redesigned with dark glass cards and proper feedback.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QGraphicsDropShadowEffect, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager


class CleanerWorker(QThread):
    finished = Signal(str)
    
    def __init__(self, adb, action_type):
        super().__init__()
        self.adb = adb
        self.action_type = action_type
        
    def run(self):
        try:
            result = ""
            if self.action_type == "cache":
                result = self.adb.clean_app_cache()
            elif self.action_type == "dex":
                result = self.adb.clean_obsolete_dex()
            elif self.action_type == "telegram":
                result = self.adb.clean_messenger_data()
            
            # Normalize: empty/None = success, check for ADB errors
            result = (result or "").strip()
            error_keywords = ["exception", "error", "failed", "not found", "denied", "no device"]
            has_error = any(kw in result.lower() for kw in error_keywords)
            
            if has_error:
                self.finished.emit(f"ADB_ERROR:{result}")
            else:
                self.finished.emit("OK")
        except Exception as e:
            self.finished.emit(f"ADB_ERROR:{str(e)}")


class CleanerCard(QFrame):
    """Modern dark glass cleaner item card"""
    def __init__(self, icon, title, desc, action_key, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget
        self.action_key = action_key
        self._original_title = title
        
        self.setObjectName("CleanCard")
        self.setStyleSheet(f"""
            #CleanCard {{
                background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1, stop:0 #1a1a2e, stop:1 #16213e);
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            #CleanCard:hover {{
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(18)
        
        # Icon circle
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(50, 50)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("""
            font-size: 24px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        layout.addWidget(icon_lbl)
        
        # Text section
        v_text = QVBoxLayout()
        v_text.setSpacing(4)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: white;")
        
        self.lbl_desc = QLabel(desc)
        self.lbl_desc.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.5);")
        self.lbl_desc.setWordWrap(True)
        
        # Status label (hidden by default, shows result after clean)
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 12px; color: #2ecc71; font-weight: 600;")
        self.lbl_status.hide()
        
        v_text.addWidget(self.lbl_title)
        v_text.addWidget(self.lbl_desc)
        v_text.addWidget(self.lbl_status)
        
        layout.addLayout(v_text, 1)
        
        # Action button
        self.btn = QPushButton("Dọn Dẹp")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setFixedSize(110, 40)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                font-weight: 700;
                border-radius: 20px;
                border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6b6b, stop:1 #e74c3c);
            }}
            QPushButton:pressed {{
                background: #c0392b;
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }}
        """)
        self.btn.clicked.connect(self.on_click)
        layout.addWidget(self.btn)
        
    def on_click(self):
        self.btn.setEnabled(False)
        self.btn.setText("⏳ Đang...")
        self.lbl_status.hide()
        self.parent_widget.run_cleaner(self.action_key, self)

    def show_result(self, success, message=""):
        self.btn.setEnabled(True)
        self.btn.setText("Dọn Dẹp")
        self.lbl_status.show()
        if success:
            self.lbl_status.setText("✓ Hoàn tất!")
            self.lbl_status.setStyleSheet("font-size: 12px; color: #2ecc71; font-weight: 600; border: none;")
        else:
            self.lbl_status.setText(f"✗ {message[:50]}")
            self.lbl_status.setStyleSheet("font-size: 12px; color: #e74c3c; font-weight: 600; border: none;")


class CleanerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(14)
        
        # ─── HEADER ───
        header = QFrame()
        header.setObjectName("CleanHeader")
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            #CleanHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e74c3c, stop:1 #c0392b);
                border-radius: 18px;
                border: none;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        h_shadow = QGraphicsDropShadowEffect(header)
        h_shadow.setBlurRadius(25)
        h_shadow.setColor(QColor(231, 76, 60, 80))
        h_shadow.setOffset(0, 6)
        header.setGraphicsEffect(h_shadow)
        
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        h_icon = QLabel("🧹")
        h_icon.setStyleSheet("font-size: 30px;")
        h_layout.addWidget(h_icon)
        
        h_info = QVBoxLayout()
        h_title = QLabel("Dọn Dẹp Thiết Bị")
        h_title.setStyleSheet("font-size: 20px; font-weight: 800; color: white;")
        h_desc = QLabel("Giải phóng dung lượng và tăng hiệu suất")
        h_desc.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8);")
        h_info.addWidget(h_title)
        h_info.addWidget(h_desc)
        h_layout.addLayout(h_info, 1)
        
        # Connection status label in header
        self.h_status = QLabel("Chưa kết nối")
        self.h_status.setStyleSheet("font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.7); background: rgba(0,0,0,0.2); padding: 4px 10px; border-radius: 10px;")
        h_layout.addWidget(self.h_status, 0, Qt.AlignVCenter)
        
        layout.addWidget(header)
        layout.addSpacing(4)
        
        # Initial status update
        self.refresh_state()

        
        # ─── CLEANER CARDS ───
        self.card_cache = CleanerCard(
            "📦", 
            "Bộ Nhớ Đệm Ứng Dụng",
            "Xóa cache toàn bộ ứng dụng để giải phóng bộ nhớ (pm trim-caches)",
            "cache", self
        )
        layout.addWidget(self.card_cache)
        
        self.card_dex = CleanerCard(
            "⚙️",
            "Tệp Dex Lỗi Thời", 
            "Xóa file biên dịch cũ không còn sử dụng (prune-dex-opt)",
            "dex", self
        )
        layout.addWidget(self.card_dex)
        
        self.card_tele = CleanerCard(
            "💬",
            "Dữ Liệu Telegram / Nekogram",
            "Xóa cache hình ảnh, video, audio, tài liệu đã tải xuống",
            "telegram", self
        )
        layout.addWidget(self.card_tele)
        
        layout.addStretch()
        
        scroll.setWidget(container)
        main.addWidget(scroll)

    def refresh_state(self):
        """Update UI based on current ADB connection"""
        if self.adb.is_online():
            self.h_status.setText(f"● {self.adb.current_device}")
            self.h_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #2ecc71; background: rgba(0,0,0,0.2); padding: 4px 10px; border-radius: 10px;")
        else:
            self.h_status.setText("○ Chưa kết nối")
            self.h_status.setStyleSheet("font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.5); background: rgba(0,0,0,0.2); padding: 4px 10px; border-radius: 10px;")

    def run_cleaner(self, action_key, card: CleanerCard):
        # Auto-connect if serial is missing but devices are present
        if not self.adb.current_device:
            self.adb.check_connection()
            self.refresh_state()

        # Check device online
        if not self.adb.is_online():
            card.show_result(False, "Chưa kết nối thiết bị")
            LogManager.log("Dọn Rác", "⚠ Chưa kết nối thiết bị!", "warning")
            return
        
        # Map action to display name for logging
        action_names = {
            "cache": "Bộ Nhớ Đệm",
            "dex": "Tệp Dex",
            "telegram": "Telegram/Nekogram"
        }
        display_name = action_names.get(action_key, action_key)
        
        worker = CleanerWorker(self.adb, action_key)
        
        def on_done(result):
            is_error = result.startswith("ADB_ERROR:")
            if is_error:
                error_msg = result.replace("ADB_ERROR:", "").strip()
                # Specific message for dex cleaning failures
                if "dex" in display_name.lower() and "failed" in error_msg.lower():
                    error_msg = "ADB command failed"
                card.show_result(False, error_msg)
                LogManager.log("Dọn Rác", f"✗ Lỗi khi dọn {display_name}: {error_msg}", "error")
            else:
                card.show_result(True)
                LogManager.log("Dọn Rác", f"✓ Đã dọn {display_name} thành công!", "success")
            
        # Guard: wait for old worker if still running (before start to avoid race condition)
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.wait(3000)
        worker.finished.connect(on_done)
        self.worker = worker
        worker.start()
