# src/ui/widgets/plugin_manager_ui.py
"""
Plugin Manager UI
Manage and view loaded plugins.
Style: Glassmorphism
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from src.ui.theme_manager import ThemeManager
from src.core.plugin_manager import PluginManager

class PluginManagerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager 
        self.plugin_manager = PluginManager()
        self.setup_ui()
        self.refresh_list()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🧩 Quản lý Plugin")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout.addWidget(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_reload = QPushButton("🔄 Tải lại Plugins")
        btn_reload.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_reload.clicked.connect(self.on_reload)
        toolbar.addWidget(btn_reload)
        
        btn_folder = QPushButton("📂 Mở thư mục Plugins")
        btn_folder.setStyleSheet(ThemeManager.get_button_style("outline"))
        btn_folder.clicked.connect(self.open_folder)
        toolbar.addWidget(btn_folder)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Description
        desc = QLabel("Đặt các file plugin (.py) vào thư mục 'plugins' để mở rộng chức năng.")
        desc.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # List
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tên Plugin", "Phiên bản", "Tác giả", "Mô tả"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: {ThemeManager.RADIUS_BUTTON};
                border: 1px solid rgba(0,0,0,0.1);
                gridline-color: rgba(0,0,0,0.1);
            }}
            QHeaderView::section {{
                background-color: rgba(0,0,0,0.05);
                padding: 5px;
                border: none;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.table)
        
    def refresh_list(self):
        self.plugin_manager.discover_plugins()
        plugins = self.plugin_manager.plugins
        
        self.table.setRowCount(len(plugins))
        for i, p in enumerate(plugins):
            self.table.setItem(i, 0, QTableWidgetItem(p.name))
            self.table.setItem(i, 1, QTableWidgetItem(p.version))
            self.table.setItem(i, 2, QTableWidgetItem(p.author))
            self.table.setItem(i, 3, QTableWidgetItem(p.description))
            
    def on_reload(self):
        self.refresh_list()
        QMessageBox.information(self, "Đã tải lại", f"Đã tải {len(self.plugin_manager.plugins)} plugins.")
        
    def open_folder(self):
        folder = self.plugin_manager.plugins_dir
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        
    def reset(self):
        self.refresh_list()
