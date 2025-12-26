import sys
import os
import shutil
import unicodedata
import tempfile
import zipfile
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QMenu, QProgressDialog, QFrame, QGraphicsDropShadowEffect,
    QFileDialog, QButtonGroup, QStackedWidget, QScrollArea, QSizePolicy, QApplication, QGroupBox, QAbstractItemView,
    QTabWidget
)
from PySide6.QtCore import Qt, QSize, QTimer, QRect
from PySide6.QtGui import QIcon, QColor, QCursor

from src.ui.theme_manager import ThemeManager
from src.core.adb.adb_manager import DeviceStatus
from src.data.app_data import AppInfo
from src.workers.app_worker import InstallerThread, BackupThread, AppScanner, RestoreThread
import webbrowser

# OneDrive APK Repository
ONEDRIVE_APK_FOLDER = "https://4wl8ft-my.sharepoint.com/:f:/g/personal/vankhoai_4wl8ft_onmicrosoft_com/IgDXdoT3HHxqTLwC2ClHOMPsATiYFsuCYtWBDTH1zBQaYG0?e=mjZW4R"

# --- Imports for Delegate ---
from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtGui import QPainter, QFont, QBrush, QPen, QFontMetrics

# --- Custom Delegate for Premium App List ---
class AppListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.font_name = QFont(ThemeManager.FONT_FAMILY, 10, QFont.Bold)
        self.font_pkg = QFont(ThemeManager.FONT_FAMILY, 8)
        self.font_tag = QFont(ThemeManager.FONT_FAMILY, 8, QFont.Bold)
        
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background (Hover/Select)
        rect = option.rect
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, QColor(ThemeManager.COLOR_ACCENT + "15")) 
            # Left Accent Bar
            accent_bar = rect.adjusted(0, 4, -rect.width()+4, -4)
            painter.setBrush(QColor(ThemeManager.COLOR_ACCENT))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(accent_bar, 2, 2)
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(rect, QColor(ThemeManager.COLOR_BG_SECONDARY))

        app: AppInfo = index.data(Qt.UserRole)
        if not app:
            painter.restore()
            return

        col = index.column()
        
        # 0: App Info (Icon + Name + Package)
        if col == 0:
            # Icon Box
            icon_size = 38
            icon_rect = rect.adjusted(12, (rect.height()-icon_size)//2, 0, 0)
            icon_rect.setWidth(icon_size)
            icon_rect.setHeight(icon_size)
            
            # Dynamic Icon Color
            colors = ["#FF5252", "#448AFF", "#69F0AE", "#E040FB", "#FFAB40", "#607D8B"]
            color_idx = abs(hash(app.package)) % len(colors)
            bg_color = QColor(colors[color_idx])
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg_color)
            painter.drawRoundedRect(icon_rect, 10, 10)
            
            # Letter
            painter.setPen(Qt.white)
            painter.setFont(self.font_name)
            letter = app.name[0].upper() if app.name else "?"
            painter.drawText(icon_rect, Qt.AlignCenter, letter)
            
            # Text Area
            text_x = icon_rect.right() + 15
            name_rect = rect.adjusted(text_x, (rect.height()//2)-18, -10, 0)
            pkg_rect = rect.adjusted(text_x, (rect.height()//2)+2, -10, 0)
            
            # Name
            painter.setPen(QColor(ThemeManager.COLOR_TEXT_PRIMARY))
            painter.setFont(self.font_name)
            painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignTop, self.elide_text(app.name, painter.fontMetrics(), name_rect.width()))
            
            # Package
            painter.setPen(QColor(ThemeManager.COLOR_TEXT_SECONDARY))
            painter.setFont(self.font_pkg)
            painter.drawText(pkg_rect, Qt.AlignLeft | Qt.AlignTop, self.elide_text(app.package, painter.fontMetrics(), pkg_rect.width()))
            
        # 1: Type (Pill Tag)
        elif col == 1:
            is_system = app.is_system
            text = "HỆ THỐNG" if is_system else "NGƯỜI DÙNG"
            
            tag_w, tag_h = 80, 22
            tag_rect = QRect(rect.left()+(rect.width()-tag_w)//2, rect.top()+(rect.height()-tag_h)//2, tag_w, tag_h)
            
            bg = QColor(ThemeManager.COLOR_PURPLE if is_system else ThemeManager.COLOR_ACCENT)
            bg.setAlpha(30)
            fg = QColor(ThemeManager.COLOR_PURPLE if is_system else ThemeManager.COLOR_ACCENT)
                
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(tag_rect, 6, 6)
            
            painter.setPen(fg)
            painter.setFont(self.font_tag)
            painter.drawText(tag_rect, Qt.AlignCenter, text)
            
        # 2: Status Tag
        elif col == 2:
            is_enabled = app.is_enabled
            is_archived = app.is_archived
            
            text = "ĐÃ BẬT" if is_enabled else "ĐÃ TẮT"
            if is_archived: text = "ĐÃ GỠ"
            
            color = QColor(ThemeManager.COLOR_SUCCESS if is_enabled else ThemeManager.COLOR_DANGER)
            if is_archived: color = QColor(ThemeManager.COLOR_TEXT_SECONDARY)
            
            tag_w, tag_h = 85, 22
            tag_rect = QRect(rect.left()+(rect.width()-tag_w)//2, rect.top()+(rect.height()-tag_h)//2, tag_w, tag_h)
            
            bg = QColor(color)
            bg.setAlpha(20)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(tag_rect, 6, 6)
            
            painter.setPen(color)
            painter.setFont(self.font_tag)
            painter.drawText(tag_rect, Qt.AlignCenter, text)
            
        # 3: Size
        elif col == 3:
            size_str = f"{app.size / 1024 / 1024:.1f} MB" if app.size > 0 else "-"
            painter.setPen(QColor(ThemeManager.COLOR_DATA if ThemeManager.is_dark() else ThemeManager.COLOR_TEXT_PRIMARY))
            painter.setFont(self.font_name)
            painter.drawText(rect, Qt.AlignCenter, size_str)
            
        painter.restore()

    def elide_text(self, text, fm, width):
        return fm.elidedText(text, Qt.ElideRight, width)

# --- End Delegate ---

class AppManagerWidget(QWidget):
    """
    App Manager V2: Modern, Clean, and Stable.
    """
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        
        # Data Stores
        self.apps_user: List[AppInfo] = []
        self.apps_system: List[AppInfo] = []
        self.current_tab = "manager" # manager, restore, install
        
        self.scanner = None
        self.install_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # 0. Global Layout for self
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # 1. Header Frame (Search & Stats)
        header = QFrame()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search Container
        search_card = QFrame()
        search_card.setFixedWidth(400)
        search_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 14px;
                border: 1px solid {ThemeManager.COLOR_BORDER_LIGHT};
            }}
        """)
        s_layout = QHBoxLayout(search_card)
        s_layout.setContentsMargins(10, 6, 10, 6)
        
        lbl_search_icon = QLabel("🔍")
        lbl_search_icon.setStyleSheet("background: transparent; opacity: 0.6;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm ứng dụng...")
        self.search_input.setStyleSheet("background: transparent; border: none; font-size: 14px;")
        self.search_input.textChanged.connect(self.filter_apps)
        
        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setFixedSize(32, 32)
        self.btn_refresh.setStyleSheet(ThemeManager.get_button_style("outline"))
        self.btn_refresh.clicked.connect(self.refresh_data)
        
        s_layout.addWidget(lbl_search_icon)
        s_layout.addWidget(self.search_input)
        s_layout.addWidget(self.btn_refresh)
        
        h_layout.addWidget(search_card)
        h_layout.addStretch()
        
        self.lbl_stats = QLabel("Đang tải dữ liệu...")
        self.lbl_stats.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-weight: 600; font-size: 12px;")
        h_layout.addWidget(self.lbl_stats)
        
        main_layout.addWidget(header)
        
        # 2. Tabs for Content
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{
                padding: 10px 25px;
                background: transparent;
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 700;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {ThemeManager.COLOR_ACCENT};
                border-bottom: 2px solid {ThemeManager.COLOR_ACCENT};
            }}
        """)
        
        self.table_user = self.create_table()
        self.table_system = self.create_table()
        self.page_install = self.create_install_page()
        
        self.tabs.addTab(self.table_user, "📱 QUẢN LÝ")
        self.tabs.addTab(self.table_system, "♻️ KHÔI PHỤC")
        self.tabs.addTab(self.page_install, "🔌 CÀI ĐẶT APK")
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs, 1) # Set stretch to 1
        
        # 3. Floating Action Bar
        self.action_bar = QFrame()
        self.action_bar.setFixedHeight(70)
        self.action_bar.setGraphicsEffect(self._get_shadow())
        self.action_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.COLOR_GLASS_CARD};
                border-radius: 20px;
                border: 1px solid {ThemeManager.COLOR_BORDER_LIGHT};
            }}
        """)
        
        ab_layout = QHBoxLayout(self.action_bar)
        ab_layout.setContentsMargins(20, 0, 20, 0)
        
        self.lbl_selection = QLabel("Đã chọn: 0")
        self.lbl_selection.setStyleSheet(f"font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        ab_layout.addWidget(self.lbl_selection)
        ab_layout.addStretch()
        
        # Actions
        self.btn_restore = self.create_action_btn("♻️ Khôi Phục", "primary", self.action_restore)
        self.btn_backup = self.create_action_btn("💾 Sao Lưu", "success", self.action_backup)
        self.btn_enable = self.create_action_btn("✅ Bật App", "success", self.action_enable)
        self.btn_disable = self.create_action_btn("🚫 Tắt App", "warning", self.action_disable)
        self.btn_uninstall = self.create_action_btn("🗑️ Gỡ Cài Đặt", "danger", self.action_uninstall)
        
        ab_layout.addWidget(self.btn_restore)
        ab_layout.addWidget(self.btn_backup)
        ab_layout.addWidget(self.btn_enable)
        ab_layout.addWidget(self.btn_disable)
        ab_layout.addWidget(self.btn_uninstall)
        
        main_layout.addWidget(self.action_bar)
        self.action_bar.hide()
        
        # Auto refresh
        QTimer.singleShot(100, self.refresh)

    def _get_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0,0,0,15))
        shadow.setOffset(0, 4)
        return shadow

    def on_tab_changed(self, index):
        tab_ids = ["manager", "restore", "install"]
        if index < len(tab_ids):
            self.current_tab = tab_ids[index]
        
        # Hide action bar on tab change to reset selection context
        if hasattr(self, 'action_bar'):
            self.action_bar.hide()
            self.update_selection()
            
        # Optional: Auto-refresh data if switching to a data tab for the first time
        if self.current_tab in ["manager", "restore"]:
            # Logic handled by refresh or user click
            pass

    def switch_tab(self, tab_id):
        """Programmatic tab switching"""
        mapping = {"manager": 0, "restore": 1, "install": 2}
        if tab_id in mapping:
            self.tabs.setCurrentIndex(mapping[tab_id])
    
    def create_action_btn(self, text, style_key, slot):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(ThemeManager.get_button_style(style_key))
        btn.clicked.connect(slot)
        return btn
        
    def create_table(self):
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ỨNG DỤNG / PACKAGE", "LOẠI", "TRẠNG THÁI", "DUNG LƯỢNG"])
        
        # Sizing & Headers
        h = table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Fixed)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 120)
        table.setColumnWidth(3, 100)
        
        # Row Height for 2 lines of text
        table.verticalHeader().setDefaultSectionSize(60)
        table.verticalHeader().setVisible(False)
        
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        table.setAlternatingRowColors(True)
        table.setMouseTracking(True)
        
        # Apply Delegate
        table.setItemDelegate(AppListDelegate(table))
        
        # Modern Table Style (Clean Glass)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                alternate-background-color: rgba(0,0,0,0.02);
                border: none;
                gridline-color: transparent;
                selection-background-color: {ThemeManager.COLOR_ACCENT}15;
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {ThemeManager.COLOR_TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 700;
                border: none;
                border-bottom: 1px solid {ThemeManager.COLOR_BORDER};
                padding: 10px;
                text-transform: uppercase;
            }}
        """)
        
        table.itemSelectionChanged.connect(self.update_selection)
        return table




            
    def create_install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 1. Compact Install Card
        install_card = QFrame()
        install_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.6);
            }}
        """)
        # Shadow
        card_shadow = QGraphicsDropShadowEffect()
        card_shadow.setBlurRadius(20)
        card_shadow.setColor(QColor(0,0,0,8))
        card_shadow.setOffset(0, 4)
        install_card.setGraphicsEffect(card_shadow)
        
        card_layout = QVBoxLayout(install_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Header
        lbl_title = QLabel("Cài Đặt APK Ngoài")
        lbl_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        card_layout.addWidget(lbl_title)
        
        # Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        
        self.apk_path_input = QLineEdit()
        self.apk_path_input.setPlaceholderText("Chọn file .apk, .xapk, .apks...")
        self.apk_path_input.setReadOnly(True)
        self.apk_path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(0,0,0,0.03);
                border: 1px solid {ThemeManager.COLOR_BORDER};
                border-radius: 8px;
                padding: 10px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
        """)
        
        btn_browse = QPushButton("📂 Chọn File")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setFixedSize(100, 38)
        btn_browse.setStyleSheet(ThemeManager.get_button_style("outline"))
        btn_browse.clicked.connect(self.choose_apk_file_ui)
        
        input_row.addWidget(self.apk_path_input)
        input_row.addWidget(btn_browse)
        card_layout.addLayout(input_row)
        
        # Action Row
        btn_install = QPushButton("⬇️ Cài Đặt Ngay")
        btn_install.setCursor(Qt.PointingHandCursor)
        btn_install.setFixedHeight(40)
        btn_install.setStyleSheet(ThemeManager.get_button_style("primary"))
        btn_install.clicked.connect(self.install_selected_file)
        
        card_layout.addWidget(btn_install)
        
        layout.addWidget(install_card)
        
        # 2. Quick Install Header
        lbl_quick = QLabel("🔥 ĐỀ XUẤT CÀI ĐẶT")
        lbl_quick.setStyleSheet(f"font-weight: 700; color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px; letter-spacing: 0.5px; margin-left: 5px;")
        layout.addWidget(lbl_quick)
        
        # 3. Quick Install List (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(content)
        c_layout.setSpacing(10)
        c_layout.setContentsMargins(5, 5, 5, 5)
        
        # Add Premium Cards
        self.add_quick_card(c_layout, "MicroG Services", "v0.3.1.4 (GmsCore)", "MicroG Services v0.3.1.4.240913.apk", "🧩")
        self.add_quick_card(c_layout, "YouTube ReVanced", "v20.14.43 (No Ads)", "YouTube_ReVanced_v20.14.43_P5.47.0.apk", "📺")
        self.add_quick_card(c_layout, "YouTube Music", "v8.30.54 (Premium)", "YT Music v8.30.54 Blue_v5.13.1-dev.2.apk", "🎵")
        self.add_quick_card(c_layout, "Google Photos", "Unlimited Backup", "GPhotos ReVanced v7.57.0.843750501.apk", "📷")
        self.add_quick_card(c_layout, "CapCut Pro", "Unlocked All", "CapCut v16.0.0 Mod.apk", "🎬")
        self.add_quick_card(c_layout, "Telegram Premium", "Optimized", "Telegram v12.2.7 Mod.apk", "✈️")
        
        c_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return page

    def choose_apk_file_ui(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn File Cài Đặt", "", "Android Apps (*.apk *.apks *.xapk *.zip)")
        if files:
            display_text = "; ".join([os.path.basename(f) for f in files])
            self.apk_path_input.setText(display_text)
            self.apk_path_input.setProperty("file_paths", files)
            
    def install_selected_file(self):
        files = self.apk_path_input.property("file_paths")
        if not files:
            QMessageBox.warning(self, "Chưa chọn file", "Vui lòng chọn file APK trước!")
            return
        
        self.install_files(files)

    def add_quick_card(self, layout, name, version, filename, icon_text="📱"):
        card = QFrame()
        card.setFixedHeight(70)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.6);
            }}
            QFrame:hover {{
                background-color: white;
                border: 1px solid {ThemeManager.COLOR_ACCENT};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0,0,0,5))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)
        
        h = QHBoxLayout(card)
        h.setContentsMargins(15, 10, 15, 10)
        h.setSpacing(15)
        
        lbl_icon = QLabel(icon_text)
        lbl_icon.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        h.addWidget(lbl_icon)
        
        info = QVBoxLayout()
        info.setSpacing(2)
        
        t = QLabel(name)
        t.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {ThemeManager.COLOR_TEXT_PRIMARY}; background: transparent; border: none;")
        v = QLabel(version)
        v.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 11px; background: transparent; border: none;")
        info.addWidget(t)
        info.addWidget(v)
        h.addLayout(info)
        
        h.addStretch()
        
        btn = QPushButton("TẢI VỀ")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(80, 32)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeManager.COLOR_GLASS_HOVER};
                color: {ThemeManager.COLOR_ACCENT};
                border: 1px solid {ThemeManager.COLOR_ACCENT}40;
                border-radius: 8px;
                font-weight: 700;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.COLOR_ACCENT};
                color: white;
            }}
        """)
        btn.clicked.connect(lambda: self.install_single_apk(filename))
        h.addWidget(btn)
        
        layout.addWidget(card)
        
    def filter_apps(self, text=None):
        self.update_tables()
        
    def refresh_data(self, force=True):
        if not self.adb.current_device: return
        
        if self.scanner and self.scanner.isRunning(): return

        self.lbl_stats.setText("Đang quét dữ liệu...")
        self.btn_refresh.setDisabled(True)
        
        self.scanner = AppScanner(self.adb, "all")
        self.scanner.finished.connect(self.on_scan_done)
        self.scanner.start()
        
    def on_scan_done(self, apps_raw):
        self.btn_refresh.setDisabled(False)
        self.apps_user.clear()
        self.apps_system.clear()
        
        for app in apps_raw:
            # Separation Logic:
            # Manager: All INSTALLED apps (User + System)
            # Restore: All ARCHIVED apps (Uninstalled System Apps)
            
            if app.is_archived:
                self.apps_system.append(app) # Use 'system' list for Restore Tab
            else:
                self.apps_user.append(app) # Use 'user' list for Manager Tab
        
        self.update_tables()
        self.lbl_stats.setText(f"Installed: {len(self.apps_user)} | Restore: {len(self.apps_system)}")
        
    def update_tables(self):
        search = self.remove_accents(self.search_input.text().lower())
        
        def populate(table, source_list, is_restore_tab=False):
            table.setRowCount(0)
            table.setSortingEnabled(False)
            
            for app in source_list:
                if search:
                    name = self.remove_accents(app.name.lower())
                    pkg = app.package.lower()
                    if search not in name and search not in pkg:
                        continue
                        
                row = table.rowCount()
                table.insertRow(row)
                
                # Col 0: App Info (Delegate uses UserRole)
                item0 = QTableWidgetItem(app.name) 
                item0.setData(Qt.UserRole, app) 
                table.setItem(row, 0, item0)
                
                # Col 1: Type (Delegate uses UserRole)
                item1 = QTableWidgetItem("")
                item1.setData(Qt.UserRole, app)
                table.setItem(row, 1, item1)
                
                # Col 2: Status (Delegate uses UserRole)
                item2 = QTableWidgetItem("")
                item2.setData(Qt.UserRole, app)
                table.setItem(row, 2, item2)
                
                # Col 3: Size
                item3 = QTableWidgetItem("") 
                item3.setData(Qt.UserRole, app)
                table.setItem(row, 3, item3)
                
            table.setSortingEnabled(True)

        populate(self.table_user, self.apps_user, is_restore_tab=False)
        populate(self.table_system, self.apps_system, is_restore_tab=True)
        
    def update_selection(self):
        if not hasattr(self, 'action_bar'): return
        
        if self.current_tab == 'manager':
            items = self.table_user.selectedItems()
        elif self.current_tab == 'restore':
            items = self.table_system.selectedItems()
        else:
            self.action_bar.hide()
            return
            
        rows = set(i.row() for i in items)
        count = len(rows)
        
        if count > 0:
            self.action_bar.show()
            self.lbl_selection.setText(f"Đã chọn: {count}")
            # Dynamic Buttons
            if self.current_tab == 'manager':
                self.btn_restore.setVisible(False)
                self.btn_backup.setVisible(True)
                self.btn_enable.setVisible(True)
                self.btn_disable.setVisible(True)
                self.btn_uninstall.setVisible(True)
            elif self.current_tab == 'restore':
                self.btn_restore.setVisible(True)
                self.btn_backup.setVisible(False)
                self.btn_enable.setVisible(False)
                self.btn_disable.setVisible(False)
                self.btn_uninstall.setVisible(False)
        else:
            self.action_bar.hide()
            
    # --- Actions ---
    def get_selected_app_infos(self) -> List[AppInfo]:
        if self.current_tab == 'manager':
            table = self.table_user
        else:
            table = self.table_system
            
        apps = []
        rows = set(i.row() for i in table.selectedItems())
        for r in rows:
            app = table.item(r, 0).data(Qt.UserRole)
            if app: apps.append(app)
        return apps

    def action_uninstall(self):
        apps = self.get_selected_app_infos()
        if not apps: return
        msg = f"Gỡ cài đặt {len(apps)} ứng dụng?\n" + "\n".join([a.name for a in apps[:5]])
        if QMessageBox.question(self, "Xác nhận", msg) == QMessageBox.Yes:
            # Logic to uninstall
            for app in apps:
                self.adb.shell(f"pm uninstall --user 0 {app.package}")
            QMessageBox.information(self, "Xong", "Đã gửi lệnh gỡ cài đặt.")
            self.refresh_data()

    def action_disable(self):
        apps = self.get_selected_app_infos()
        count = 0
        for app in apps:
            if app.is_enabled:
                 self.adb.shell(f"pm disable-user --user 0 {app.package}")
                 count += 1
        if count > 0:
            QMessageBox.information(self, "Xong", f"Đã tắt {count} ứng dụng.")
            self.refresh_data()
        else:
            QMessageBox.information(self, "Info", "Không có ứng dụng nào cần tắt (đã tắt rồi).")

    def action_enable(self):
        apps = self.get_selected_app_infos()
        count = 0
        for app in apps:
            if not app.is_enabled:
                 self.adb.shell(f"pm enable {app.package}")
                 count += 1
        if count > 0:
            QMessageBox.information(self, "Xong", f"Đã bật {count} ứng dụng.")
            self.refresh_data()
            
    def action_restore(self):
         apps = self.get_selected_app_infos()
         # Restore logic (same as before)
         pkgs = [a.package for a in apps if a.is_archived]
         if not pkgs: return
         
         self.restore_thread = RestoreThread(self.adb, pkgs)
         self.restore_thread.finished.connect(lambda s,m: [QMessageBox.information(self,"Xong",m), self.refresh_data()])
         self.restore_thread.start()
         
    def action_backup(self):
        apps = self.get_selected_app_infos()
        # Backup Logic placeholder
        QMessageBox.information(self, "Backup", f"Sao lưu {len(apps)} app (Chưa implement deep logic)")

    def choose_apk_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn APK", "", "APK (*.apk)")
        if files:
            self.install_files(files)
            
    def install_single_apk(self, filename):
        """Open OneDrive folder in browser for user to download APK"""
        try:
            webbrowser.open(ONEDRIVE_APK_FOLDER)
            QMessageBox.information(
                self, 
                "Mở OneDrive", 
                f"Đã mở thư mục APK trong trình duyệt.\n\n"
                f"Vui lòng tải file: {filename}\n"
                f"Sau đó sử dụng nút 'Chọn File' để cài đặt."
            )
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể mở trình duyệt: {str(e)}")

    def install_files(self, files):
        self.install_thread = InstallerThread(self.adb, files, False)
        self.install_thread.finished.connect(lambda s, m: QMessageBox.information(self, "Install", m))
        self.install_thread.start()

    def reset(self):
        """Reset state (Called by MainWindow)"""
        self.search_input.clear()
        self.apps_user.clear()
        self.apps_system.clear()
        self.table_user.setRowCount(0)
        self.table_system.setRowCount(0)
        self.lbl_stats.setText("Sẵn sàng")
        self.action_bar.hide()
        
    def refresh(self):
        """Alias for refresh_data (Called by UnifiedTools or others)"""
        self.refresh_data(force=True)

    def remove_accents(self, text: str) -> str:
        if not text: return ""
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
