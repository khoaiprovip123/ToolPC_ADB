# src/ui/pages/about_page.py
"""
About Page - Standalone About & Info page
Extracted from Settings widget
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QLabel
)
from src.ui.theme_manager import ThemeManager
from src.version import __version__


class AboutPage(QWidget):
    """
    Standalone About page showing app info, features, and roadmap
    """
    
    def __init__(self, adb_manager=None):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup About page UI"""
        content_layout = QVBoxLayout(self)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area for long content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_container = QWidget()
        content_layout_inner = QVBoxLayout(content_container)
        content_layout_inner.setSpacing(20)
        
        # About Header
        about_group = QGroupBox("Giới thiệu")
        about_group.setStyleSheet(self.get_group_style())
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel(
            "<h2>📱 Xiaomi ADB Commander</h2>"
            f"<p><b>Phiên bản:</b> {__version__} (Latest)</p>"
            "<p><b>Tác giả:</b> Van Khoai</p>"
            "<p>Công cụ quản lý thiết bị Android toàn diện, tối ưu hóa đặc biệt cho Xiaomi/MIUI/HyperOS.</p>"
        )
        about_text.setWordWrap(True)
        about_text.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        about_layout.addWidget(about_text)
        content_layout_inner.addWidget(about_group)
        
        # New Features / Changelog Preview
        changelog_group = QGroupBox(f"Cập nhật mới (v{__version__})")
        changelog_group.setStyleSheet(self.get_group_style())
        changelog_layout = QVBoxLayout(changelog_group)
        
        changelog_html = """
        <h3 style="margin-bottom: 5px;">✨ UI Polish & Dialog Fixes (v2.5.5.2)</h3>
        <ul style="margin-top: 0px; margin-bottom: 10px; margin-left: -20px; color: #333;">
            <li>🎨 <b>Glass Dialogs:</b> Hộp thoại thông báo mới với hiệu ứng kính mờ (Glassmorphism), không còn bị lỗi đen nền.</li>
            <li>🧹 <b>Clean UI:</b> Loại bỏ hoàn toàn các viền dư thừa (boxy borders) trên tiêu đề các nhóm chức năng.</li>
            <li>🛡️ <b>Stability:</b> Thêm kiểm tra kết nối thiết bị chặt chẽ trước khi chạy lệnh tối ưu hóa.</li>
            <li>🐛 <b>Bug Fixes:</b> Sửa lỗi Crash khởi động và các lỗi hiển thị nhỏ khác.</li>
        </ul>
        """
        if ThemeManager.get_theme() == "dark":
            changelog_html = changelog_html.replace("#333", "#eee")
        
        changelog_label = QLabel(changelog_html)
        changelog_label.setWordWrap(True)
        changelog_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        changelog_layout.addWidget(changelog_label)
        content_layout_inner.addWidget(changelog_group)
        
        # Features List
        features_group = QGroupBox("Tính năng Chính")
        features_group.setStyleSheet(self.get_group_style())
        features_layout = QVBoxLayout(features_group)
        
        features_html = """
        <ul style="margin-top: 0px; margin-bottom: 0px; margin-left: -20px; color: #333;">
            <li><b>Dashboard:</b> Xem thông tin chi tiết thiết bị, tình trạng pin, bộ nhớ.</li>
            <li><b>Quản lý Ứng dụng:</b> Cài đặt, gỡ bỏ, vô hiệu hóa ứng dụng hệ thống (Debloat).</li>
            <li><b>File Manager:</b> Quản lý tệp tin, kéo thả, upload/download nhanh chóng.</li>
            <li><b>Screen Mirror:</b> Phản chiếu màn hình điện thoại lên máy tính (Scrcpy tích hợp).</li>
            <li><b>Xiaomi Tools:</b> Bỏ qua tài khoản Mi, tắt quảng cáo hệ thống (MSA), tối ưu MIUI.</li>
            <li><b>Fastboot & Recovery:</b> Các công cụ nạp ROM, xóa dữ liệu, reboot nâng cao.</li>
        </ul>
        """
        if ThemeManager.get_theme() == "dark":
            features_html = features_html.replace("#333", "#eee")
        
        features_label = QLabel(features_html)
        features_label.setWordWrap(True)
        features_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        features_layout.addWidget(features_label)
        content_layout_inner.addWidget(features_group)
        
        # Roadmap / Dev Status
        dev_group = QGroupBox("Lộ trình Phát triển (Roadmap)")
        dev_group.setStyleSheet(self.get_group_style())
        dev_layout = QVBoxLayout(dev_group)
        
        dev_html = """
        <p><b>Đang phát triển (Upcoming):</b></p>
        <ul style="margin-top: 0px; margin-left: -20px;">
            <li>☁️ <b>Cloud Sync Global:</b> Đồng bộ trực tiếp Google Drive API (Không cần qua thư mục máy tính).</li>
            <li>🐧 <b>Linux/Mac Support:</b> Hỗ trợ đa nền tảng tốt hơn.</li>
            <li>⚡ <b>Flash ROM Auto:</b> Tự động tải và flash ROM Stock cho Xiaomi.</li>
            <li>🔋 <b>Battery Cycle Reset:</b> (Cần Root) Reset số lần sạc pin.</li>
        </ul>
        <p><i>Mọi ý kiến đóng góp xin vui lòng liên hệ tác giả.</i></p>
        """
        dev_label = QLabel(dev_html)
        dev_label.setWordWrap(True)
        dev_label.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        dev_layout.addWidget(dev_label)
        content_layout_inner.addWidget(dev_group)
        
        content_layout_inner.addStretch()
        
        scroll.setWidget(content_container)
        content_layout.addWidget(scroll)
    
    def get_group_style(self):
        """Get group box styling"""
        return f"""
            QGroupBox {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                margin-top: 10px;
                padding: 15px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """
    
    def reset(self):
        """Reset page (compatibility method for main window)"""
        pass
