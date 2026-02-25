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
from src.core.log_manager import LogManager

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
        self.setObjectName("PermissionCard")
        self.setStyleSheet(f"""
            #PermissionCard {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: {ThemeManager.RADIUS_CARD};
                border: 1px solid rgba(0,0,0,0.05);
            }}
            QLabel {{ border: none; background: transparent; }}
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
        
        dlg = ConfirmationDialog(
            self,
            title="Kích hoạt Brevent",
            message="Bạn muốn thực hiện kích hoạt Brevent Server?",
            details="Giữ thiết bị kết nối. Lệnh này sẽ kích hoạt Brevent Server (Rootless) và cấp quyền Write Secure Settings.\n\n⚠️ Lưu ý: Hành động này sẽ thay đổi thiết lập ứng dụng chạy ngầm.",
            confirm_text="Kích hoạt ngay",
            cancel_text="Hủy",
            warning_mode=True
        )
        if dlg.exec_() == QDialog.Accepted:
            # We use PermissionWorker for simple commands, but activate_brevent is complex logic
            # However, for consistency with other perm tools, let's see if we can use the existing manager method
            # Actually OptimizationManager has activate_brevent()
            self.opt_worker = OptimizationWorker(self.adb, "activate_brevent")
            self.opt_worker.progress.connect(lambda msg: LogManager.log("Brevent", msg, "info"))
            self.opt_worker.start()
            LogManager.log("Hệ thống", "Đang gửi lệnh kích hoạt Brevent...", "info")

    def _run_perm_cmd(self, title, cmd, show_output=False):
        if not self.adb.current_device:
            LogManager.log("Cảnh báo", "Vui lòng kết nối thiết bị trước!", "warning")
            return

        # Show Loading
        self.progress = QDialog(self)
        self.progress.setWindowTitle(title)
        self.progress.setFixedSize(320, 110)
        self.progress.setStyleSheet(ThemeManager.get_main_window_style())
        
        l = QVBoxLayout(self.progress)
        l.setContentsMargins(20, 20, 20, 20)
        
        msg_lbl = QLabel(f"<b>{title}</b><br>Đang thực hiện, vui lòng đợi...")
        msg_lbl.setStyleSheet(f"color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']}; font-size: 13px;")
        msg_lbl.setAlignment(Qt.AlignCenter)
        l.addWidget(msg_lbl)
        self.progress.show()
        
        # Guard: stop old worker before creating new
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.worker.wait(3000)
        self.worker = PermissionWorker(self.adb, cmd)
        self.worker.finished.connect(lambda out: self._on_cmd_done(title, out, show_output))
        self.worker.start()

    def _on_cmd_done(self, title, output, show_output):
        self.progress.close()
        
        if show_output or ("Error" in output and len(output) > 20):
            result_dialog = QDialog(self)
            result_dialog.setWindowTitle(f"Kết quả: {title}")
            result_dialog.resize(450, 350)
            result_dialog.setStyleSheet(ThemeManager.get_main_window_style())
            
            l = QVBoxLayout(result_dialog)
            l.setContentsMargins(20, 20, 20, 20)
            
            # Label with contrast color
            header_lbl = QLabel(f"<b>Chi tiết lệnh:</b> {title}")
            header_lbl.setStyleSheet(f"color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']}; font-size: 14px;")
            l.addWidget(header_lbl)
            
            txt = QTextEdit()
            txt.setStyleSheet(ThemeManager.get_text_edit_style())
            txt.setPlainText(output)
            txt.setReadOnly(True)
            l.addWidget(txt)
            
            status_container = QHBoxLayout()
            if "info: shizuku_starter exit with 0" in output or not output.strip():
                status_lbl = QLabel("✅ Thực hiện thành công!")
                status_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_SUCCESS}; font-weight: bold; font-size: 13px;")
            else:
                status_lbl = QLabel("⚠️ Có thông báo hoặc lỗi phát sinh.")
                status_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_WARNING if not ThemeManager.is_dark() else '#F2994A'}; font-weight: bold; font-size: 13px;")
            
            status_container.addWidget(status_lbl)
            status_container.addStretch()
            
            btn_close = QPushButton("Đóng")
            btn_close.setFixedSize(80, 32)
            btn_close.setCursor(Qt.PointingHandCursor)
            btn_close.setStyleSheet(ThemeManager.get_button_style("outline"))
            btn_close.clicked.connect(result_dialog.close)
            status_container.addWidget(btn_close)
            
            l.addLayout(status_container)
            result_dialog.exec()
        else:
            LogManager.log("Thành công", f"Đã thực hiện xong lệnh: {title}", "success")

    def reset(self):
        pass
