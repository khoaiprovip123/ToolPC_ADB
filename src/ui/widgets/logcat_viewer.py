
"""
Logcat Viewer Widget
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QTextCursor, QFont
from src.ui.theme_manager import ThemeManager
import re

class LogcatWorker(QThread):
    log_received = Signal(str)
    
    def __init__(self, adb_manager, filters="", grep=""):
        super().__init__()
        self.adb = adb_manager
        self.filters = filters
        self.grep = grep
        self._is_running = True
        
    def run(self):
        # Use subprocess directly to read stream
        import subprocess
        # -v color is nice for terminal but we parse manually. -v time is good.
        cmd = f"{self.adb.adb_path} logcat -v time {self.filters}"
        
        try:
            # Creation flags for no window
            creation_flags = 0x08000000 if subprocess.os.name == 'nt' else 0
            
            self.process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace',
                creationflags=creation_flags
            )
            
            while self._is_running:
                line = self.process.stdout.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line: continue
                
                # Manual Grep
                if self.grep and self.grep.lower() not in line.lower():
                    continue
                    
                self.log_received.emit(line)
        except Exception as e:
            self.log_received.emit(f"Error: {str(e)}")
            
    def stop(self):
        self._is_running = False
        if hasattr(self, 'process'):
            try:
                self.process.terminate()
            except: pass

class LogcatViewerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.worker = None
        self.current_app_pid = None
        self.log_buffer = []  # Queue for batch processing
        self.update_timer = QTimer()
        self.update_timer.setInterval(100) # Update UI every 100ms
        self.update_timer.timeout.connect(self.process_log_buffer)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("📜 Smart Logcat")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(header)
        
        # Smart Tools Group
        tools_group = QGroupBox("Bộ lọc thông minh")
        tools_group.setStyleSheet(ThemeManager.get_group_box_style())
        tools_layout = QHBoxLayout(tools_group)
        
        self.cb_smart_filter = QCheckBox("Chỉ hiện App đang mở (Foreground)")
        self.cb_smart_filter.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-weight: bold;")
        tools_layout.addWidget(self.cb_smart_filter)
        
        self.cb_errors_only = QCheckBox("Chỉ hiện Lỗi (Errors/Crash)")
        self.cb_errors_only.setStyleSheet(f"color: {ThemeManager.COLOR_DANGER}; font-weight: bold;")
        self.cb_errors_only.stateChanged.connect(self.on_error_filter_change)
        tools_layout.addWidget(self.cb_errors_only)
        
        tools_layout.addStretch()
        layout.addWidget(tools_group)
        
        # Standard Controls
        controls = QHBoxLayout()
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Tìm kiếm / Grep (e.g. ActivityManager)")
        self.filter_input.setStyleSheet(ThemeManager.get_input_style())
        controls.addWidget(self.filter_input)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Verbose", "Debug", "Info", "Warning", "Error", "Fatal"])
        self.level_combo.setCurrentIndex(0) # Verbose default
        self.level_combo.setStyleSheet(ThemeManager.get_input_style())
        controls.addWidget(self.level_combo)
        
        self.btn_start = QPushButton("▶️ Start")
        self.btn_start.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.btn_start.clicked.connect(self.toggle_logcat)
        controls.addWidget(self.btn_start)
        
        self.btn_clear = QPushButton("🧹 Clear")
        self.btn_clear.setStyleSheet(ThemeManager.get_button_style("outline"))
        self.btn_clear.clicked.connect(self.clear_log)
        controls.addWidget(self.btn_clear)
        
        layout.addLayout(controls)
        
        # Log Output
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.NoWrap) # Better performance
        
        # Optimize global font size if needed, but 11px is fine
        self.log_view.document().setMaximumBlockCount(2000) # Limit lines to prevent memory overflow
        
        self.log_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ThemeManager.COLOR_GLASS_CARD};
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: {ThemeManager.RADIUS_CARD};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.log_view)
        
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 10px;")
        layout.addWidget(self.status_lbl)
        
    def on_error_filter_change(self, state):
        if state == Qt.Checked:
            self.level_combo.setCurrentText("Error")
            self.level_combo.setEnabled(False)
        else:
            self.level_combo.setEnabled(True)
            
    def get_foreground_pid(self):
        """Try to get PID of current foreground app"""
        try:
            # Method 1: dumpsys window (More universal)
            out = self.adb.shell("dumpsys window | grep mCurrentFocus")
            # Output format: mCurrentFocus=Window{... u0 com.package.name/com.package.name.Activity}
            
            match = re.search(r'u0 (.*?)/', out)
            package_name = None
            if match:
                package_name = match.group(1)
            
            if not package_name:
                return None, None
                
            # Get PID
            pid_out = self.adb.shell(f"pidof -s {package_name}")
            if pid_out and pid_out.isdigit():
                return package_name, pid_out.strip()
                
            return package_name, None
            
        except:
            return None, None

    def toggle_logcat(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.update_timer.stop()
            self.btn_start.setText("▶️ Start")
            self.btn_start.setStyleSheet(ThemeManager.get_button_style("primary"))
            self.status_lbl.setText("Stopped")
        else:
            if not self.adb.current_device:
                self.log_view.append("⚠️ Chưa kết nối thiết bị")
                return
            
            # Reset buffer
            self.log_buffer = []
            
            # Build filter
            level_map = {"Verbose": "V", "Debug": "D", "Info": "I", "Warning": "W", "Error": "E", "Fatal": "F"}
            level_char = level_map[self.level_combo.currentText()]
            
            # Base filter: *:Level
            adb_filter = f"*:{level_char}"
            grep_keyword = self.filter_input.text().strip()
            
            # Smart Filter Application
            if self.cb_smart_filter.isChecked():
                pkg, pid = self.get_foreground_pid()
                if pid:
                    adb_filter = f"--pid={pid} {adb_filter}"
                    self.status_lbl.setText(f"Filtering for App: {pkg} (PID: {pid})")
                elif pkg:
                    grep_keyword = pkg
                    self.status_lbl.setText(f"Filtering for Package: {pkg}")
                else:
                    self.status_lbl.setText("Could not detect foreground app, showing all")
            
            self.worker = LogcatWorker(self.adb, adb_filter, grep_keyword)
            self.worker.log_received.connect(self.queue_log) # Connect to Queue
            self.worker.start()
            self.update_timer.start()
            
            self.btn_start.setText("⏹️ Stop")
            self.btn_start.setStyleSheet(ThemeManager.get_button_style("danger"))
            
    def queue_log(self, text):
        """Add log to buffer instead of direct UI update"""
        self.log_buffer.append(text)
        
    def process_log_buffer(self):
        """Flush buffer to UI"""
        if not self.log_buffer:
            return
            
        # Process in chunks if too big
        lines = self.log_buffer[:]
        self.log_buffer = [] # Clear buffer
        
        html_lines = []
        for text in lines:
            # Colorize
            color = ThemeManager.COLOR_TEXT_PRIMARY
            
            if " E " in text or " F " in text or "/E" in text or "/F" in text: 
                color = "#FF5252" # Red
            elif " W " in text or "/W" in text: 
                color = "#FFAB40" # Orange
            elif " D " in text or "/D" in text: 
                color = "#448AFF" # Blue
            elif " I " in text or "/I" in text: 
                color = "#69F0AE" # Green
                
            if "exception" in text.lower() or "crash" in text.lower() or "fatal" in text.lower():
                text = f"<b>{text}</b>"
                color = "#FF1744" # Deep Red
            
            html_lines.append(f'<span style="color:{color}">{text}</span>')
            
        # Bulk append
        if html_lines:
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.End)
            # cursor.insertHtml("<br>".join(html_lines)) # Can be slow for huge chunks
            # Better:
            for line in html_lines:
                 self.log_view.append(line)
            self.log_view.moveCursor(QTextCursor.End)
        
    def clear_log(self):
        self.log_view.clear()
        self.log_buffer = []
        self.adb.shell("logcat -c") # Clear buffer on device too
