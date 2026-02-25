# src/ui/widgets/dns_config.py
"""
DNS Config Widget - Manage Private DNS
Style: Glassmorphism
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QLineEdit, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager

class DNSConfigWidget(QWidget):
    """
    Private DNS Configuration Widget
    """
    
    DNS_PROVIDERS = {
        "Google": "dns.google",
        "Cloudflare": "1dot1dot1dot1.cloudflare-dns.com",
        "AdGuard": "dns.adguard.com",
        "Quad9": "dns.quad9.net"
    }
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🌐 Cấu Hình Private DNS")
        header.setStyleSheet(f"""
            font-size: 20px;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
            font-weight: bold;
            padding: 10px;
        """)
        main_layout.addWidget(header)
        
        # Current Status
        self.status_label = QLabel("Trạng thái hiện tại: Đang kiểm tra...")
        self.status_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; padding-left: 10px;")
        main_layout.addWidget(self.status_label)
        
        # Mode Selection
        mode_group = QGroupBox("Chế độ DNS")
        mode_group.setStyleSheet(f"""
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
        mode_layout = QVBoxLayout(mode_group)
        
        self.bg_mode = QButtonGroup()
        
        self.rb_off = QRadioButton("Tắt (Off)")
        self.rb_auto = QRadioButton("Tự động (Automatic)")
        self.rb_hostname = QRadioButton("Hostname riêng (Private DNS provider hostname)")
        
        for rb in [self.rb_off, self.rb_auto, self.rb_hostname]:
            rb.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
            mode_layout.addWidget(rb)
            self.bg_mode.addButton(rb)
            
        self.rb_hostname.toggled.connect(self.toggle_hostname_input)
        
        main_layout.addWidget(mode_group)
        
        # Hostname Input
        self.hostname_group = QGroupBox("Nhà cung cấp DNS")
        self.hostname_group.setStyleSheet(f"""
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
        hostname_layout = QVBoxLayout(self.hostname_group)
        
        # Quick Select
        quick_layout = QHBoxLayout()
        for name, host in self.DNS_PROVIDERS.items():
            btn = QPushButton(name)
            def set_dns(checked=False, h=host):
                self.input_hostname.setText(h)
                self.rb_hostname.setChecked(True) # Auto-select mode
            btn.clicked.connect(set_dns)
            btn.setStyleSheet(ThemeManager.get_button_style("outline"))
            quick_layout.addWidget(btn)
            
        hostname_layout.addLayout(quick_layout)
        
        self.input_hostname = QLineEdit()
        self.input_hostname.setPlaceholderText("Nhập hostname (ví dụ: dns.google)")
        self.input_hostname.setStyleSheet(ThemeManager.get_input_style())
        hostname_layout.addWidget(self.input_hostname)
        
        main_layout.addWidget(self.hostname_group)
        
        # Apply Button
        btn_apply = QPushButton("Áp dụng thay đổi")
        btn_apply.clicked.connect(self.apply_dns)
        btn_apply.setStyleSheet(ThemeManager.get_button_style("primary"))
        main_layout.addWidget(btn_apply)
        
        main_layout.addStretch()
        
        # Initial check
        self.check_current_dns()
        
    def toggle_hostname_input(self, checked):
        self.hostname_group.setEnabled(checked)
        
    def check_current_dns(self):
        if not self.adb.current_device:
            self.status_label.setText("Trạng thái: Chưa kết nối")
            return
            
        try:
            mode = self.adb.shell("settings get global private_dns_mode").strip()
            hostname = self.adb.shell("settings get global private_dns_specifier").strip()
            
            status_text = f"Mode: {mode}"
            if mode == "hostname":
                status_text += f" ({hostname})"
                self.rb_hostname.setChecked(True)
                self.input_hostname.setText(hostname)
            elif mode == "automatic":
                self.rb_auto.setChecked(True)
            else:
                self.rb_off.setChecked(True)
                
            self.status_label.setText(f"Trạng thái hiện tại: {status_text}")
            
        except Exception as e:
            self.status_label.setText(f"Lỗi kiểm tra: {e}")
            
    def apply_dns(self):
        if not self.adb.current_device:
            LogManager.log("Lỗi", "Chưa kết nối thiết bị", "warning")
            return
            
        try:
            if self.rb_off.isChecked():
                self.adb.shell("settings put global private_dns_mode off")
            elif self.rb_auto.isChecked():
                self.adb.shell("settings put global private_dns_mode automatic")
            elif self.rb_hostname.isChecked():
                hostname = self.input_hostname.text().strip()
                if not hostname:
                    LogManager.log("Lỗi", "Vui lòng nhập hostname", "warning")
                    return
                self.adb.shell(f"settings put global private_dns_specifier {hostname}")
                self.adb.shell("settings put global private_dns_mode hostname")
                
            LogManager.log("Thành công", "Đã cập nhật cấu hình DNS", "success")
            self.check_current_dns()
            
        except Exception as e:
            LogManager.log("Lỗi", f"Không thể cập nhật DNS: {e}", "error")
            
    def reset(self):
        self.check_current_dns()
