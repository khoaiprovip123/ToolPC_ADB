# src/ui/widgets/screen_mirror.py
"""
Screen Mirror Widget - Control scrcpy
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSpinBox, QComboBox, QGroupBox, QMessageBox,
    QLineEdit, QFileDialog
)
from PySide6.QtCore import QProcess, Qt, QSettings, QUrl
from PySide6.QtGui import QDesktopServices
import os
import shutil
from src.ui.theme_manager import ThemeManager

class ScreenMirrorWidget(QWidget):
    """
    Screen Mirroring Widget using scrcpy
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.scrcpy_process = None
        self.settings = QSettings("XiaomiADB", "ScreenMirror")
        self.scrcpy_path = self.settings.value("scrcpy_path", "")
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("📱 Phản Chiếu Màn Hình (Scrcpy)")
        header.setStyleSheet(f"""
            font-size: 20px;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
            font-weight: bold;
            padding: 10px;
        """)
        main_layout.addWidget(header)
        
        # Settings Group
        settings_group = QGroupBox("Cấu hình")
        settings_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                margin-top: 10px;
                padding-top: 15px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        settings_layout = QVBoxLayout(settings_group)
        
        # Info Label (Missing scrcpy warning)
        self.info_lbl = QLabel("")
        self.info_lbl.setWordWrap(True)
        self.info_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_WARNING}; font-style: italic; font-size: 12px;")
        
        # Scrcpy Path Configuration
        # Check for bundled scrcpy (Priority: scripts/ > resources/scrcpy/)
        root_dir = os.getcwd()
        scripts_path = os.path.join(root_dir, "scripts", "scrcpy.exe")
        resources_path = os.path.join(root_dir, "resources", "scrcpy", "scrcpy.exe")
        
        bundled_path = None
        if os.path.exists(scripts_path):
            bundled_path = scripts_path
        elif os.path.exists(resources_path):
            bundled_path = resources_path
            
        is_bundled = bundled_path is not None
        
        path_layout = QHBoxLayout()
        if is_bundled:
             # Bundled Mode
             self.scrcpy_path = bundled_path
             # Ensure settings has this path if it's new
             if self.scrcpy_path != bundled_path:
                 self.save_path(bundled_path)
             
             path_lbl = QLabel(f"✅ Đã tìm thấy Scrcpy (scripts)")
             if "resources" in bundled_path:
                 path_lbl.setText("✅ Đã tìm thấy Scrcpy (resources)")
                 
             path_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_SUCCESS}; font-weight: bold;")
             path_layout.addWidget(path_lbl)
        else:
             # Custom Mode
             path_lbl = QLabel("Đường dẫn Scrcpy:")
             path_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
             path_layout.addWidget(path_lbl)
             
             self.path_input = QLineEdit()
             self.path_input.setPlaceholderText("Tự động tìm kiếm hoặc chọn đường dẫn scrcpy.exe...")
             self.path_input.setText(self.scrcpy_path)
             self.path_input.setStyleSheet(ThemeManager.get_input_style())
             self.path_input.textChanged.connect(self.save_path)
             path_layout.addWidget(self.path_input)
             
             btn_browse = QPushButton("📁")
             btn_browse.setFixedSize(40, 36)
             btn_browse.setToolTip("Chọn file scrcpy.exe")
             btn_browse.clicked.connect(self.browse_scrcpy)
             btn_browse.setStyleSheet(ThemeManager.get_button_style("outline"))
             path_layout.addWidget(btn_browse)
             
             # Download Button
             btn_download = QPushButton("⬇️")
             btn_download.setFixedSize(40, 36)
             btn_download.setToolTip("Tải Scrcpy từ Github")
             btn_download.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/Genymobile/scrcpy/releases")))
             btn_download.setStyleSheet(ThemeManager.get_button_style("primary"))
             path_layout.addWidget(btn_download)
        
        settings_layout.addLayout(path_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.cb_always_on_top = QCheckBox("Luôn ở trên cùng")
        self.cb_always_on_top.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        options_layout.addWidget(self.cb_always_on_top)
        
        self.cb_turn_screen_off = QCheckBox("Tắt màn hình thiết bị")
        self.cb_turn_screen_off.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        options_layout.addWidget(self.cb_turn_screen_off)
        
        self.cb_stay_awake = QCheckBox("Giữ thiết bị luôn bật")
        self.cb_stay_awake.setChecked(True)
        self.cb_stay_awake.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        options_layout.addWidget(self.cb_stay_awake)
        
        settings_layout.addLayout(options_layout)
        
        # Quality Settings
        quality_layout = QHBoxLayout()
        
        quality_layout.addWidget(QLabel("Bitrate (Mbps):"))
        self.spin_bitrate = QSpinBox()
        self.spin_bitrate.setRange(1, 50)
        self.spin_bitrate.setValue(8)
        self.spin_bitrate.setStyleSheet(ThemeManager.get_input_style())
        quality_layout.addWidget(self.spin_bitrate)
        
        quality_layout.addWidget(QLabel("Max Size:"))
        self.combo_size = QComboBox()
        self.combo_size.addItems(["Tự động", "1920", "1600", "1280", "1024", "800"])
        self.combo_size.setStyleSheet(ThemeManager.get_input_style())
        quality_layout.addWidget(self.combo_size)
        
        settings_layout.addLayout(quality_layout)
        
        main_layout.addWidget(settings_group)
        main_layout.addWidget(self.info_lbl) # Add info label to layout
        
        # Check initially
        if not self.find_scrcpy():
             self.info_lbl.setText("⚠️ Không tìm thấy Scrcpy. Vui lòng tải về và chọn đường dẫn scrcpy.exe ở trên.")
        
        # Control Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ Bắt đầu")
        self.btn_start.clicked.connect(self.start_mirroring)
        self.btn_start.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹ Dừng")
        self.btn_stop.clicked.connect(self.stop_mirroring)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(ThemeManager.get_button_style("danger"))
        btn_layout.addWidget(self.btn_stop)
        
        main_layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel("Trạng thái: Sẵn sàng")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; margin-top: 10px;")
        main_layout.addWidget(self.status_label)
        
        main_layout.addStretch()
        
    def browse_scrcpy(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn Scrcpy Executable", "", "Executables (*.exe);;All Files (*)")
        if path:
            self.path_input.setText(path)
            self.save_path(path)
            
    def save_path(self, path):
        self.scrcpy_path = path
        self.settings.setValue("scrcpy_path", path)
        if os.path.exists(path):
            self.info_lbl.setText("")
        else:
            self.info_lbl.setText("⚠️ Đường dẫn không tồn tại")
            
    def start_mirroring(self):
        if not self.adb.current_device:
            QMessageBox.warning(self, "Lỗi", "Chưa kết nối thiết bị")
            return
            
        # Find scrcpy
        scrcpy_path = self.find_scrcpy()
        if not scrcpy_path:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy scrcpy.\nVui lòng tải scrcpy và chọn đường dẫn scrcpy.exe trong phần Cấu hình.")
            return
            
        # Build arguments
        args = ["-s", self.adb.current_device]
        
        if self.cb_always_on_top.isChecked():
            args.append("--always-on-top")
        if self.cb_turn_screen_off.isChecked():
            args.append("--turn-screen-off")
        if self.cb_stay_awake.isChecked():
            args.append("--stay-awake")
        
        # Disable audio by default to prevent crashes on unsupported devices/Win10
        # The user reported crashes after 15s (Demuxer error) commonly caused by audio sync issues
        args.append("--no-audio")
            
        # Scrcpy 2.0+ uses --video-bit-rate instead of --bit-rate
        args.extend(["--video-bit-rate", f"{self.spin_bitrate.value()}M"])
        
        size = self.combo_size.currentText()
        if size != "Tự động":
            args.extend(["--max-size", size])
            
        # Start process
        self.scrcpy_process = QProcess()
        self.scrcpy_process.readyReadStandardOutput.connect(self.handle_stdout)
        self.scrcpy_process.readyReadStandardError.connect(self.handle_stderr)
        self.scrcpy_process.finished.connect(self.on_process_finished)
        self.scrcpy_process.errorOccurred.connect(self.on_process_error)
        
        # Set ADB environment variable if possible
        if hasattr(self.adb, 'adb_path') and self.adb.adb_path:
             # Scrcpy relies on ADB. It usually expects 'adb' in PATH.
             # We can set the ADB environment variable which scrcpy checks (if supported)
             # Or we can modify PATH to include directory of our adb
             
             env = QProcess.systemEnvironment()
             adb_dir = os.path.dirname(self.adb.adb_path)
             
             # Create a clean environment dictionary
             # QProcess environment is a list of "KEY=VALUE" strings
             # But setProcessEnvironment expects that.
             # PySide6's QProcess.setProcessEnvironment takes QProcessEnvironment object.
             
             from PySide6.QtCore import QProcessEnvironment
             q_env = QProcessEnvironment.systemEnvironment()
             q_env.insert("ADB", self.adb.adb_path) # Some tools use this
             
             # Also add to PATH
             current_path = q_env.value("PATH")
             q_env.insert("PATH", f"{adb_dir};{current_path}")
             
             current_path = q_env.value("PATH")
             q_env.insert("PATH", f"{adb_dir};{current_path}")
             
             self.scrcpy_process.setProcessEnvironment(q_env) 

        # IMPORTANT: Set working directory to scrcpy's folder so it finds its DLLs and bundled adb
        scrcpy_dir = os.path.dirname(scrcpy_path)
        self.scrcpy_process.setWorkingDirectory(scrcpy_dir)

        print(f"[Scrcpy] Starting: {scrcpy_path}")
        print(f"[Scrcpy] Args: {args}")
        print(f"[Scrcpy] CWD: {scrcpy_dir}")

        self.scrcpy_process.start(scrcpy_path, args)
        
        if self.scrcpy_process.waitForStarted(1000):
            self.status_label.setText("Trạng thái: Đang chạy...")
            self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_SUCCESS};")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
        else:
             self.status_label.setText("Trạng thái: Lỗi khởi động")
             QMessageBox.warning(self, "Lỗi", f"Không thể khởi động scrcpy.\nLỗi: {self.scrcpy_process.errorString()}")

    def handle_stdout(self):
        data = self.scrcpy_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        print(f"[Scrcpy Out] {data}")

    def handle_stderr(self):
        data = self.scrcpy_process.readAllStandardError().data().decode('utf-8', errors='ignore')
        print(f"[Scrcpy Err] {data}")
        # If critical error, show it? Scrcpy prints info to stderr too.
        if "error" in data.lower() or "aborted" in data.lower():
             self.status_label.setText(f"Lỗi: {data[:50]}...")

    def on_process_error(self, error):
        QMessageBox.warning(self, "Lỗi Process", f"Có lỗi xảy ra khi chạy Scrcpy: {error}")

        
    def stop_mirroring(self):
        if self.scrcpy_process and self.scrcpy_process.state() == QProcess.Running:
            self.scrcpy_process.terminate()
            self.scrcpy_process.waitForFinished(1000)
            
    def on_process_finished(self):
        self.status_label.setText("Trạng thái: Đã dừng")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.scrcpy_process = None
        
    def find_scrcpy(self):
        # 1. Check configured path
        if self.scrcpy_path and os.path.exists(self.scrcpy_path):
            return self.scrcpy_path
            
        # 2. Check system path
        path = shutil.which("scrcpy")
        if path:
            return path
            
        # 3. Check local resources
        local_path = os.path.join(os.getcwd(), "resources", "scrcpy", "scrcpy.exe")
        if os.path.exists(local_path):
             # Auto-update setting if found locally
             self.path_input.setText(local_path) 
             return local_path
            
        return None
        
    def reset(self):
        self.stop_mirroring()
