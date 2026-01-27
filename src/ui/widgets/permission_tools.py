# src/ui/widgets/permission_tools.py
"""
Permission Tools Widget - Centralized permission management
Contains: Shizuku Manager, SetEdit Permission Granting
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QGraphicsDropShadowEffect,
    QTextEdit, QDialog, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from src.ui.theme_manager import ThemeManager

class PermissionWorker(QThread):
    finished = Signal(str)
    
    def __init__(self, adb, cmd):
        super().__init__()
        self.adb = adb
        self.cmd = cmd
        
    def run(self):
        try:
            res = self.adb.shell(self.cmd)
            self.finished.emit(res)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

class PermissionCard(QFrame):
    def __init__(self, title, desc, icon_text, button_text, button_color, callback):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: {ThemeManager.RADIUS_CARD};
                border: 1px solid rgba(0,0,0,0.05);
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(ThemeManager.COLOR_SHADOW)
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Icon/Label Section
        info_layout = QVBoxLayout()
        title_lbl = QLabel(f"{icon_text} {title}")
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY}; border: none; background: transparent;")
        
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; border: none; background: transparent; font-size: 13px;")
        
        info_layout.addWidget(title_lbl)
        info_layout.addWidget(desc_lbl)
        layout.addLayout(info_layout, stretch=1)
        
        # Button
        btn = QPushButton(button_text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(160, 42)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_color}; 
                color: white; 
                font-weight: bold; 
                border-radius: 8px; 
                border: none;
            }}
            QPushButton:hover {{ background-color: {button_color}; opacity: 0.9; }}
        """)
        btn.clicked.connect(callback)
        layout.addWidget(btn)

class PermissionToolsWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 10, 0)
        
        # 1. Shizuku Card
        shizuku_card = PermissionCard(
            "Shizuku Manager",
            "Kích hoạt Shizuku để sử dụng các tính năng nâng cao không cần Root. (Yêu cầu đã cài app Shizuku)",
            "⚡",
            "Kích hoạt Shizuku",
            "#f1c40f",
            self.start_shizuku
        )
        layout.addWidget(shizuku_card)
        
        # 2. SetEdit Card
        setedit_card = PermissionCard(
            "SetEdit Permission",
            "Cấp quyền WRITE_SECURE_SETTINGS cho app SetEdit để chỉnh sửa các thiết lập hệ thống ẩn.",
            "⚙️",
            "Cấp quyền SetEdit",
            "#3498db",
            self.grant_setedit
        )
        layout.addWidget(setedit_card)
        
        # 3. Brevent Card (Relocated)
        brevent_card = PermissionCard(
            "Kích hoạt Brevent",
            "Kích hoạt Brevent Server và cấp quyền Secure Settings để quản lý ứng dụng chạy ngầm.",
            "🛡️",
            "Kích hoạt Brevent",
            "#2980b9",
            self.run_brevent_activation
        )
        layout.addWidget(brevent_card)
        
        # 4. System UI Tuner (Bonus)
        ui_tuner_card = PermissionCard(
            "System UI Tuner",
            "Cấp quyền đặc biệt cho các app tùy biến giao diện hệ thống (SystemUI Tuner, v.v.)",
            "🎨",
            "Cấp quyền UI",
            "#9b59b6",
            self.grant_ui_tuner
        )
        layout.addWidget(ui_tuner_card)
        
        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def start_shizuku(self):
        cmd = "sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh"
        self._run_perm_cmd("Kích hoạt Shizuku", cmd, True)

    def grant_setedit(self):
        # Common SetEdit package
        pkg = "by4a.setedit22"
        cmd = f"pm grant {pkg} android.permission.WRITE_SECURE_SETTINGS"
        self._run_perm_cmd("Cấp quyền SetEdit", cmd)

    def grant_ui_tuner(self):
        pkg = "com.zacharee1.systemuituner"
        cmd = f"pm grant {pkg} android.permission.WRITE_SECURE_SETTINGS && pm grant {pkg} android.permission.DUMP && pm grant {pkg} android.permission.PACKAGE_USAGE_STATS"
        self._run_perm_cmd("Cấp quyền SystemUI Tuner", cmd)

    def run_brevent_activation(self):
        """Kích hoạt Brevent qua OptimizationWorker"""
        from src.workers.optimization_worker import OptimizationWorker
        from src.core.log_manager import LogManager
        
        confirm = QMessageBox.question(
            self, "Kích hoạt Brevent", 
            "Giữ thiết bị kết nối. Lệnh này sẽ kích hoạt Brevent Server (Rootless) và cấp quyền Write Secure Settings.\n\nTiếp tục?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            # We use PermissionWorker for simple commands, but activate_brevent is complex logic
            # However, for consistency with other perm tools, let's see if we can use the existing manager method
            # Actually OptimizationManager has activate_brevent()
            self.opt_worker = OptimizationWorker(self.adb, "activate_brevent")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Brevent", msg, "info"))
            self.opt_worker.start()
            QMessageBox.information(self, "Đã gửi lệnh", "Lệnh kích hoạt Brevent đã được gửi. Vui lòng kiểm tra Log để xem tiến trình.")

    def _run_perm_cmd(self, title, cmd, show_output=False):
        if not self.adb.current_device:
            QMessageBox.warning(self, "Lỗi", "Chưa kết nối thiết bị!")
            return

        # Show Loading
        self.progress = QDialog(self)
        self.progress.setWindowTitle(title)
        self.progress.setFixedSize(300, 100)
        l = QVBoxLayout(self.progress)
        l.addWidget(QLabel(f"Đang thực hiện: {title}..."))
        self.progress.show()
        
        self.worker = PermissionWorker(self.adb, cmd)
        self.worker.finished.connect(lambda out: self._on_cmd_done(title, out, show_output))
        self.worker.start()

    def _on_cmd_done(self, title, output, show_output):
        self.progress.close()
        
        if show_output or ("Error" in output and len(output) > 20):
            result_dialog = QDialog(self)
            result_dialog.setWindowTitle(f"Kết quả: {title}")
            result_dialog.resize(400, 300)
            l = QVBoxLayout(result_dialog)
            txt = QTextEdit()
            txt.setPlainText(output)
            txt.setReadOnly(True)
            l.addWidget(txt)
            
            if "info: shizuku_starter exit with 0" in output or not output.strip():
                l.addWidget(QLabel("✅ Thực hiện thành công!"))
            else:
                l.addWidget(QLabel("⚠️ Có thông báo hoặc lỗi phát sinh."))
            result_dialog.exec()
        else:
            QMessageBox.information(self, "Thành công", f"Đã thực hiện xong lệnh: {title}")

    def reset(self):
        pass
