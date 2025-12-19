
"""
APK Analyzer Widget
Style: Glassmorphism
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QScrollArea, QGridLayout, QGroupBox,
    QTextEdit, QListWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap
from src.ui.theme_manager import ThemeManager
from src.core.apk_parser import APKParser

class DropZone(QFrame):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setAcceptDrops(True)
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {ThemeManager.COLOR_ACCENT};
                border-radius: 15px;
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
            }}
            QFrame:hover {{
                background-color: rgba(255, 255, 255, 0.4);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        icon = QLabel("📦")
        icon.setStyleSheet("font-size: 48px; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        text = QLabel("Kéo thả file APK vào đây\nhoặc nhấn để chọn")
        text.setStyleSheet(f"font-size: 14px; color: {ThemeManager.COLOR_TEXT_SECONDARY}; background: transparent;")
        text.setAlignment(Qt.AlignCenter)
        layout.addWidget(text)
        
    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn File APK", "", "Android Package (*.apk)")
        if file_path:
            self.callback(file_path)
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.endswith('.apk'):
                self.callback(f)
                break

class APKAnalyzerWidget(QWidget):
    def __init__(self, adb_manager=None):
        super().__init__()
        self.adb = adb_manager
        self.apk_path = None
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🔍 Phân Tích APK")
        header.setStyleSheet(f"""
            font-size: 20px;
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
            font-weight: bold;
        """)
        main_layout.addWidget(header)
        
        # Drop Zone
        self.drop_zone = DropZone(self.analyze_apk)
        self.drop_zone.setFixedHeight(120)
        main_layout.addWidget(self.drop_zone)
        
        # Results Area (Hidden initially)
        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_area.setStyleSheet("border: none; background: transparent;")
        self.results_area.setVisible(False)
        
        container = QWidget()
        self.details_layout = QVBoxLayout(container)
        self.details_layout.setSpacing(15)
        
        # 1. Basic Info Card
        self.info_card = self.create_section("Thông tin cơ bản")
        self.lbl_package = self.add_info_row(self.info_card, "Package Name:", "N/A")
        self.lbl_version = self.add_info_row(self.info_card, "Version:", "N/A")
        self.lbl_sdk = self.add_info_row(self.info_card, "SDK (Min/Target):", "N/A")
        self.details_layout.addWidget(self.info_card)
        
        # 2. Permissions
        self.perm_group = QGroupBox("Quyền hạn (Permissions)")
        self.perm_group.setStyleSheet(ThemeManager.get_group_box_style())
        self.perm_layout = QVBoxLayout(self.perm_group)
        self.perm_list = QListWidget()
        self.perm_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
        """)
        self.perm_layout.addWidget(self.perm_list)
        self.details_layout.addWidget(self.perm_group)
        
        self.results_area.setWidget(container)
        main_layout.addWidget(self.results_area)
        
        main_layout.addStretch()
        
    def create_section(self, title):
        group = QGroupBox(title)
        group.setStyleSheet(ThemeManager.get_group_box_style())
        group.setLayout(QVBoxLayout())
        return group
        
    def add_info_row(self, group, label_text, value_text):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-weight: bold; color: {ThemeManager.COLOR_TEXT_SECONDARY};")
        val = QLabel(value_text)
        val.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        group.layout().addLayout(row)
        return val
        
    def analyze_apk(self, path):
        self.apk_path = path
        self.drop_zone.setVisible(False)
        self.results_area.setVisible(True)
        
        # Parse
        parser = APKParser(path)
        if parser.parse():
            self.lbl_package.setText(parser.package_name)
            self.lbl_version.setText(f"{parser.version_name} ({parser.version_code})")
            self.lbl_sdk.setText(f"Min: {parser.min_sdk} | Target: {parser.target_sdk}")
            
            self.perm_list.clear()
            for p in parser.permissions:
                # Beautify permission name
                short_name = p.split('.')[-1]
                item = f"{short_name} ({p})"
                self.perm_list.addItem(item)
        else:
            self.lbl_package.setText("Lỗi đọc file")
            
    def reset(self):
        self.drop_zone.setVisible(True)
        self.results_area.setVisible(False)
        self.apk_path = None
