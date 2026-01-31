# src/ui/widgets/file_manager.py
"""
File Manager - Windows 12 Style
Features: Glassmorphism, Grid/List Views, Breadcrumbs, Smooth UX
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QLineEdit, QMenu, QMessageBox, QFileDialog,
    QProgressDialog, QHeaderView, QFrame, QSplitter, QListWidget, QListWidgetItem,
    QAbstractItemView, QStyle, QApplication, QStackedWidget, QScrollArea, QDialog,
    QProgressBar, QGridLayout, QToolButton
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QMimeData, QPoint
from PySide6.QtGui import QIcon, QAction, QColor, QFont, QPixmap, QCursor, QDrag, QPainter, QBrush, QPen
import os
import tempfile
import math
from src.ui.theme_manager import ThemeManager
from src.workers.file_worker import FileWorker
from src.data.file_data import FileEntry

# --- Helper Classes ---

class GlassFrame(QFrame):
    """A Frame with simulated Glassmorphism background"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GlassFrame {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}CC; /* 80% Opacity */
                border-radius: 12px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
        """)

class BreadcrumbBar(QWidget):
    """Interactive Breadcrumb Navigation"""
    path_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.layout.setAlignment(Qt.AlignLeft)

    def set_path(self, path):
        # Clear existing
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        
        # Build new
        parts = path.strip('/').split('/')
        current_build = ""
        
        # Root Item
        if not path.startswith("/"): # Should be absolute
             parts.insert(0, "") # Dummy for root processing if needed
        
        # Always add Root "/"
        btn_root = self.create_btn("📱", "/")
        self.layout.addWidget(btn_root)
        self.layout.addWidget(self.create_separator())
        
        full_path = ""
        for i, part in enumerate(parts):
            if not part: continue
            full_path += f"/{part}"
            
            # Create button
            btn = self.create_btn(part, full_path)
            self.layout.addWidget(btn)
            
            # Separator if not last
            if i < len(parts) - 1:
                self.layout.addWidget(self.create_separator())
                
        self.layout.addStretch()

    def create_btn(self, text, path):
        btn = QPushButton(text)
        btn.setProperty("path", path)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.path_clicked.emit(btn.property("path")))
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                color: #3B82F6; /* Blue-500 */
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #EFF6FF; /* Blue-50 */
            }
        """)
        return btn

    def create_separator(self):
        lbl = QLabel("/")
        lbl.setStyleSheet("color: #9CA3AF; font-weight: normal; font-size: 13px;")
        return lbl

class ImagePreviewDialog(QDialog):
    def __init__(self, image_path, file_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Xem ảnh: {file_name}")
        self.resize(1000, 800)
        self.setStyleSheet(f"background-color: {ThemeManager.get_theme()['COLOR_BG_MAIN']}; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            if pixmap.width() > 1600 or pixmap.height() > 1200:
                 pixmap = pixmap.scaled(1600, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_lbl.setPixmap(pixmap)
        else:
            self.img_lbl.setText("Không thể tải ảnh")
        scroll.setWidget(self.img_lbl)
        layout.addWidget(scroll)

class DriveUsageWidget(QWidget):
    """Bottom Sidebar Widget: Drive Usage"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
                border-top: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
            QLabel {{ color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-size: 11px; font-weight: 600; }}
            QProgressBar {{
                background-color: {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']}; 
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeManager.COLOR_ACCENT}; 
                border-radius: 4px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        self.lbl_title = QLabel("Bộ nhớ hệ thống")
        layout.addWidget(self.lbl_title)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(25) # Mock
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        
        self.lbl_desc = QLabel("Đang tải...")
        self.lbl_desc.setAlignment(Qt.AlignRight)
        self.lbl_desc.setStyleSheet(f"font-size: 10px; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']};")
        layout.addWidget(self.lbl_desc)

    def update_data(self, total_gb, used_gb):
        if total_gb <= 0: return
        
        percent = int((used_gb / total_gb) * 100)
        self.progress.setValue(percent)
        
        free_gb = total_gb - used_gb
        self.lbl_desc.setText(f"Còn trống {free_gb:.1f} GB")
        
        # Color coding
        if percent > 90:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {ThemeManager.COLOR_DANGER}; border-radius: 4px; }}") 
        elif percent > 75:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {ThemeManager.COLOR_WARNING}; border-radius: 4px; }}")
        else:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {ThemeManager.COLOR_ACCENT}; border-radius: 4px; }}")

class SidebarItem(QListWidgetItem):
    def __init__(self, text, icon_char, path=None, is_header=False, parent=None):
        super().__init__(text, parent)
        self.path = path
        self.icon_char = icon_char
        self.is_header = is_header
        
        if is_header:
            self.setFlags(Qt.NoItemFlags)
            self.setForeground(QColor(ThemeManager.get_theme()['COLOR_TEXT_SECONDARY'])) 
            self.setFont(QFont("Segoe UI", 8, QFont.Bold))
            self.setText(text.upper())
        else:
            self.setText(f"  {icon_char}  {text}")
            self.setFont(QFont("Segoe UI", 10))

# ... (Existing ExplorerTree and ExplorerGrid classes remain unchanged as they use separate update logic if needed, but for now we skip them to keep contiguous edit logic simple or check if we need to jump)
class ExplorerTree(QTreeWidget):
    """Details View"""
    files_dropped = Signal(list) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: super().dragEnterEvent(event)
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: super().dragMoveEvent(event)
            
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if files:
                self.files_dropped.emit(files)
                event.acceptProposedAction()
        else:
            super().dropEvent(event)

class ExplorerGrid(QListWidget):
    """Grid/Icon View"""
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(64, 64))
        self.setResizeMode(QListWidget.Adjust)
        self.setGridSize(QSize(100, 100))
        self.setSpacing(10)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: super().dragEnterEvent(event)
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: super().dragMoveEvent(event)
            
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if files:
                self.files_dropped.emit(files)
                event.acceptProposedAction()
        else:
            super().dropEvent(event)

# --- Main Widget ---

class FileManagerWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        
        # State
        self.internal_root = "/storage/emulated/0"
        self.current_path = self.internal_root
        self.history = []
        self.history_index = -1
        self.cache_dir = os.path.join(tempfile.gettempdir(), "xiaomi_adb_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.view_mode = "list" # 'list' or 'grid'
        self.clipboard_data = {}
        
        # Worker
        self.worker = FileWorker(self.adb)
        self.setup_ui()

        # Connect Signals after UI creation
        self.worker.listing_ready.connect(self.on_listing_ready)
        self.worker.storages_ready.connect(self.on_storages_ready)
        self.worker.usage_ready.connect(self.usage_widget.update_data)
        self.worker.op_finished.connect(self.on_op_finished)
        
        # Initial Load
        
        # Initial Load
        if self.adb.current_device and self.adb.is_online():
            self.load_path(self.internal_root)
            self.worker.list_storages()
            self.worker.get_usage()
            
        # --- Main Layout (HBox: Sidebar | Right Panel) ---
    def setup_ui(self):
        if self.layout() is not None:
            return
            
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LEFT: Full Height Sidebar ---
        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(260)
        self.sidebar_container.setStyleSheet(f"""
            QWidget {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
                border-right: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
        """)
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # 1. Brand / Logo Area
        brand_frame = QFrame()
        brand_frame.setFixedHeight(60)
        brand_layout = QHBoxLayout(brand_frame)
        brand_layout.setContentsMargins(20, 0, 0, 0)
        brand_lbl = QLabel("CloudFile")
        brand_lbl.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {ThemeManager.COLOR_ACCENT};")
        brand_layout.addWidget(brand_lbl)
        sidebar_layout.addWidget(brand_frame)
        
        # 2. Sidebar List
        self.sidebar = QListWidget()
        self.sidebar.setFrameShape(QFrame.NoFrame)
        self.sidebar.setFocusPolicy(Qt.NoFocus)
        self.sidebar.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                height: 38px;
                padding-left: 10px;
                border-radius: 6px;
                margin-left: 10px; 
                margin-right: 10px;
                margin-bottom: 2px;
                color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']};
            }}
            QListWidget::item:hover {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeManager.COLOR_ACCENT}20; /* 20% opacity */
                color: {ThemeManager.COLOR_ACCENT};
                font-weight: 600;
            }}
        """)
        self.sidebar.itemClicked.connect(self.on_sidebar_click)
        
        sidebar_layout.addWidget(self.sidebar)
        
        # 3. Drive Usage Widget (Bottom)
        self.usage_widget = DriveUsageWidget()
        sidebar_layout.addWidget(self.usage_widget)
        
        main_layout.addWidget(self.sidebar_container)

        # --- RIGHT: Right Panel (Top Bar + Content) ---
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: transparent;") # Transparent for Acrylic
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 1. Top Bar (Header)
        top_bar = QFrame()
        top_bar.setFixedHeight(56) # h-14
        top_bar.setObjectName("FileTopBar")
        top_bar.setStyleSheet(f"""
            #FileTopBar {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-bottom: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        top_layout.setSpacing(15)
        
        # Nav Buttons
        self.btn_back = self.create_nav_btn("←", self.go_back)
        self.btn_forward = self.create_nav_btn("→", self.go_forward)
        self.btn_up = self.create_nav_btn("↑", self.go_up)
        
        top_layout.addWidget(self.btn_back)
        top_layout.addWidget(self.btn_forward)
        top_layout.addWidget(self.btn_up)
        
        # Breadcrumbs
        self.breadcrumbs = BreadcrumbBar()
        self.breadcrumbs.path_clicked.connect(self.load_path)
        top_layout.addWidget(self.breadcrumbs)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Tìm kiếm...")
        self.search_bar.setFixedHeight(36)
        self.search_bar.setFixedWidth(250)
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 6px;
                padding: 0 12px;
                color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']};
            }}
        """)
        top_layout.addWidget(self.search_bar)
        
        top_layout.addStretch() 

        # Actions
        # View Toggles
        toggle_frame = QFrame()
        toggle_frame.setFixedSize(70, 32)
        toggle_frame.setStyleSheet(f"background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']}; border-radius: 6px; border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};")
        toggle_layout = QHBoxLayout(toggle_frame)
        toggle_layout.setContentsMargins(2, 2, 2, 2)
        toggle_layout.setSpacing(0)
        
        self.btn_view_list = QPushButton("📜")
        self.btn_view_list.setCheckable(True)
        self.btn_view_list.clicked.connect(lambda: self.set_view_mode('list'))
        
        self.btn_view_grid = QPushButton("🪟")
        self.btn_view_grid.setCheckable(True)
        self.btn_view_grid.clicked.connect(lambda: self.set_view_mode('grid'))
        
        for btn in [self.btn_view_list, self.btn_view_grid]:
            btn.setFixedSize(30, 26)
            btn.setStyleSheet(f"""
                QPushButton {{ border: none; border-radius: 4px; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; }}
                QPushButton:checked {{ background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']}; color: {ThemeManager.COLOR_ACCENT}; }}
                QPushButton:hover {{ color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']}; }}
            """)
            toggle_layout.addWidget(btn)
            
        top_layout.addWidget(toggle_frame)
        
        right_layout.addWidget(top_bar)

        # 2. Action Bar (New)
        action_bar = QFrame()
        action_bar.setFixedHeight(40)
        action_bar.setStyleSheet(f"background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']}; border-bottom: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};")
        ab_layout = QHBoxLayout(action_bar)
        ab_layout.setContentsMargins(15, 0, 15, 0)
        ab_layout.setSpacing(10)
        
        # Fixed duplicate New button
        self.btn_new = self.create_action_btn(ab_layout, "Mới", "➕", True)
        self.btn_new.clicked.connect(self.action_new_folder)
        
        self.btn_upload = self.create_action_btn(ab_layout, "Tải lên", "⬆")
        self.btn_upload.clicked.connect(self.upload_dialog)
        
        self.create_separator_v(ab_layout)
        
        self.btn_download = self.create_action_btn(ab_layout, "Tải về", "⬇")
        self.btn_download.clicked.connect(self.action_download)
        
        self.create_separator_v(ab_layout)
        
        self.btn_cut = self.create_action_btn(ab_layout, "Cắt", "✂")
        self.btn_cut.clicked.connect(self.action_cut)
        
        self.btn_copy = self.create_action_btn(ab_layout, "Sao chép", "📄")
        self.btn_copy.clicked.connect(self.action_copy)
        
        self.btn_paste = self.create_action_btn(ab_layout, "Dán", "📋")
        self.btn_paste.clicked.connect(self.action_paste)
        
        self.btn_rename = self.create_action_btn(ab_layout, "Đổi tên", "✎")
        self.btn_rename.clicked.connect(self.action_rename)
        
        self.btn_delete = self.create_action_btn(ab_layout, "Xóa", "🗑")
        self.btn_delete.clicked.connect(self.action_delete)
        
        ab_layout.addStretch()
        right_layout.addWidget(action_bar)
        
        # 2. Content Area
        self.content_container = QWidget()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        self.stack = QStackedWidget()
        
        # Tree View
        self.tree = ExplorerTree()
        self.tree.files_dropped.connect(self.handle_dropped_files)
        # ... (Tree setup same as before, abbreviated here for clarity but keeping properties)
        self.tree.setFrameShape(QFrame.NoFrame)
        self.tree.setHeaderLabels(["TÊN", "NGÀY SỬA ĐỔI", "LOẠI", "KÍCH THƯỚC"])
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemSelectionChanged.connect(self.update_actions_state)
        self.tree.itemDoubleClicked.connect(self.on_item_double_click)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background: transparent;
                border: none;
                font-family: "Segoe UI";
            }
            QHeaderView::section {
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                padding: 10px 5px;
                color: #64748B; /* Slate-500 */
                font-weight: 600;
                font-size: 11px;
                text-transform: none;
            }
            QTreeWidget::item {
                height: 48px;
                color: #334155; /* Slate-700 */
                border-bottom: 1px solid transparent;
            }
            QTreeWidget::item:hover {
                background-color: #F8FAFC;
            }
            QTreeWidget::item:selected {
                background-color: #EFF6FF; /* Blue-50 */
                color: #1D4ED8; /* Blue-700 */
                border-bottom: 1px solid #DBEAFE;
            }
        """)
        self.tree.setColumnWidth(0, 500) 
        self.stack.addWidget(self.tree)
        
        # Grid View
        
        # Grid View
        self.grid = ExplorerGrid()
        self.grid.files_dropped.connect(self.handle_dropped_files)
        self.grid.setFrameShape(QFrame.NoFrame)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.show_context_menu)
        self.grid.itemSelectionChanged.connect(self.update_actions_state)
        self.grid.itemDoubleClicked.connect(self.on_item_double_click)
        self.grid.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                color: #334155;
                border: 1px solid transparent;
                border-radius: 8px;
                padding: 10px;
                margin: 10px;
            }
            QListWidget::item:hover {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
            }
            QListWidget::item:selected {
                background-color: #EFF6FF; /* Blue-50 */
                border: 1px solid #BFDBFE; /* Blue-200 */
                color: #1E40AF;
                /* Note: box-shadow not directly supported in QSS for items */
            }
        """)
        self.stack.addWidget(self.grid)
        
        content_layout.addWidget(self.stack)
        
        # Status Bar
        # Status Bar (Blue Footer)
        self.status_bar_container = QWidget()
        self.status_bar_container.setFixedHeight(28)
        self.status_bar_container.setStyleSheet("background-color: #2563EB; color: white;")
        sb_layout = QHBoxLayout(self.status_bar_container)
        sb_layout.setContentsMargins(15, 0, 15, 0)
        
        self.status_bar = QLabel("Sẵn sàng")
        self.status_bar.setStyleSheet("font-size: 11px; font-weight: 500;")
        sb_layout.addWidget(self.status_bar)
        
        sb_layout.addStretch()
        
        self.lbl_display_opt = QLabel("Cài đặt hiển thị")
        self.lbl_display_opt.setStyleSheet("font-size: 11px; opacity: 0.8;")
        sb_layout.addWidget(self.lbl_display_opt)
        
        content_layout.addWidget(self.status_bar_container)
        
        right_layout.addWidget(self.content_container)
        
        main_layout.addWidget(right_panel)
        
        # Populate Sidebar
        # Populate Sidebar
        self.populate_sidebar()
        self.set_view_mode('grid') # Default to grid as per mockup

    def populate_sidebar(self):
        self.sidebar.clear()
        
        self.add_sidebar_header("Truy cập nhanh")
        self.add_sidebar_item("Trang chính", "🏠", self.internal_root)
        self.add_sidebar_item("Gần đây", "⭐", None) # Placeholder
        self.add_sidebar_item("Tải xuống", "⬇", f"{self.internal_root}/Download")
        self.add_sidebar_item("Tài liệu", "📄", f"{self.internal_root}/Documents")
        
        self.add_sidebar_header("Ổ đĩa")
        # Items "Hệ thống" and "Thẻ nhớ" will be added dynamically by list_storages

    def set_view_mode(self, mode):
        self.view_mode = mode
        if mode == 'list':
            self.stack.setCurrentIndex(0)
            self.btn_view_list.setChecked(True)
            self.btn_view_grid.setChecked(False)
        else:
            self.stack.setCurrentIndex(1)
            self.btn_view_list.setChecked(False)
            self.btn_view_grid.setChecked(True)
        self.refresh()

    def create_action_btn(self, layout, text, icon, primary=False):
        btn = QPushButton(f" {icon}  {text} ")
        btn.setCursor(Qt.PointingHandCursor)
        if primary:
            # Accent Button (New)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeManager.COLOR_ACCENT}; 
                    color: white; 
                    border: none; 
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-family: "Segoe UI", sans-serif;
                }}
                QPushButton:hover {{ background-color: {ThemeManager.COLOR_ACCENT}DD; }}
                QPushButton:pressed {{ background-color: {ThemeManager.COLOR_ACCENT}AA; }}
            """)
        else:
            # Standard Command Bar Button (Windows 11 style)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent; 
                    color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']}; 
                    border: none; 
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-family: "Segoe UI", sans-serif;
                }}
                QPushButton:hover {{ background-color: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']}; }}
                QPushButton:pressed {{ background-color: {ThemeManager.get_theme()['COLOR_BORDER']}; }}
                QPushButton:disabled {{ color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; }}
            """)
        layout.addWidget(btn)
        return btn
        
    def create_separator_v(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFixedSize(1, 16)
        line.setStyleSheet(f"background-color: {ThemeManager.get_theme()['COLOR_BORDER']};")
        layout.addWidget(line)

    def create_nav_btn(self, text, slot):
        btn = QPushButton(text)
        btn.setFixedSize(36, 36)
        btn.clicked.connect(slot)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 6px;
                color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
            }}
            QPushButton:pressed {{
                background-color: {ThemeManager.get_theme()['COLOR_BG_SECONDARY']};
            }}
        """)
        return btn

    def add_sidebar_header(self, text):
        item = SidebarItem(text, "", is_header=True)
        self.sidebar.addItem(item)
        
    def add_sidebar_item(self, text, icon, path):
        item = SidebarItem(text, icon, path)
        self.sidebar.addItem(item)
        
    def update_listing_ui(self):
        # Update Nav Buttons
        self.btn_back.setEnabled(self.history_index > 0)
        self.btn_forward.setEnabled(self.history_index < len(self.history) - 1)
        self.btn_up.setEnabled(self.current_path != "/")
        
        # Update Breadcrumbs
        self.breadcrumbs.set_path(self.current_path)
        
        # Request Files
        if not self.adb.is_online():
            self.status_bar.setText("Thiết bị Offline/Fastboot")
            return

        self.status_bar.setText(f"Đang tải: {self.current_path}...")
        self.tree.clear()
        self.grid.clear()
        self.worker.list_files(self.current_path)

    def on_storages_ready(self, entries):
        # Update Sidebar Drives
        # Allow same path if it's a Drive entry (e.g. System vs Home)
        # Only check if we have an item with the same NAME
        current_names = []
        for i in range(self.sidebar.count()):
           it = self.sidebar.item(i)
           if isinstance(it, SidebarItem): current_names.append(it.text())

        for entry in entries:
           if entry.name not in current_names:
               self.add_sidebar_item(entry.name, "💾" if "Thẻ" in entry.name or "ngoài" in entry.name else "📱", entry.path)

    def on_listing_ready(self, entries):
        # Normal File Listing
        self.tree.setUpdatesEnabled(False)
        self.grid.setUpdatesEnabled(False)
        
        # CLEAR VIEWS BEFORE POPULATING TO PREVENT DUPLICATES
        self.tree.clear()
        self.grid.clear()
        
        count = 0
        for entry in entries:
            count += 1
            # Determine Icon
            icon_char = "📄"
            if entry.is_dir: icon_char = "📁"
            else:
                ext = entry.name.split('.')[-1].lower() if '.' in entry.name else ""
                if ext in ['jpg', 'png', 'jpeg', 'webp', 'gif']: icon_char = "🖼️"
                elif ext in ['mp4', 'avi', 'mkv', 'mov']: icon_char = "🎬"
                elif ext in ['mp3', 'wav', 'flac']: icon_char = "🎵"
                elif ext in ['apk']: icon_char = "🤖"
                elif ext in ['zip', 'rar', '7z']: icon_char = "📦"
                elif ext in ['pdf', 'doc', 'txt', 'xml', 'json']: icon_char = "📝"
            
            # 1. Populate List/Tree
            t_item = QTreeWidgetItem(self.tree)
            t_item.setText(0, f"  {icon_char}  {entry.name}")
            t_item.setText(1, entry.date)
            t_item.setText(2, "Thư mục" if entry.is_dir else "Tập tin")
            t_item.setText(3, entry.size)
            t_item.setData(0, Qt.UserRole, entry)
            
            # 2. Populate Grid
            g_item = QListWidgetItem(entry.name)
            g_item.setTextAlignment(Qt.AlignCenter)
            # Create a simple pixmap from char for now (In real app, use Svg/Png)
            # We can use a helper to draw text to pixmap
            pix = self.emoji_to_pixmap(icon_char, 64)
            g_item.setIcon(QIcon(pix))
            g_item.setData(Qt.UserRole, entry)
            self.grid.addItem(g_item)

        self.tree.setUpdatesEnabled(True)
        self.grid.setUpdatesEnabled(True)
        self.status_bar.setText(f"{count} mục | {self.current_path}")

    def emoji_to_pixmap(self, icon_char, size):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setFont(QFont("Segoe UI Emoji", int(size * 0.6)))
        painter.drawText(pix.rect(), Qt.AlignCenter, icon_char)
        painter.end()
        return pix

    def load_path(self, path):
        if not path: return
        path = path.replace('//', '/')
        if self.current_path == path and self.tree.topLevelItemCount() > 0: return # Already there
        
        # History
        if self.history_index == -1 or self.history[self.history_index] != path:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index+1]
            self.history.append(path)
            self.history_index += 1
            
        self.current_path = path
        self.update_listing_ui()
        self.worker.get_usage(path)

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            self.update_listing_ui()

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_path = self.history[self.history_index]
            self.update_listing_ui()
            
    def go_up(self):
        if self.current_path == "/": return
        parent = os.path.dirname(self.current_path)
        self.load_path(parent)
        
    def refresh(self):
        self.worker.list_files(self.current_path)
        
    def on_sidebar_click(self, item):
        if isinstance(item, SidebarItem) and item.path:
            self.load_path(item.path)
            
    def on_item_double_click(self, item, col=0):
        # Supports both List and Grid items
        entry = item.data(0, Qt.UserRole) if isinstance(item, QTreeWidgetItem) else item.data(Qt.UserRole)
        
        if entry.is_dir:
            self.load_path(entry.path)
        else:
            self.open_file(entry)

    def open_file(self, entry):
        if entry.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
             self.preview_image(entry)
        else:
             QMessageBox.information(self, "Thông tin", f"Mở: {entry.name}\n(Tính năng mở file khác đang phát triển)")

    def preview_image(self, entry):
        local_path = os.path.join(self.cache_dir, entry.name)
        progress = QProgressDialog("Đang tải ảnh...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        # Force event loop to show dialog
        QApplication.processEvents()
        
        try:
             self.adb.pull_file(entry.path, self.cache_dir)
             progress.close()
             if os.path.exists(local_path):
                 dlg = ImagePreviewDialog(local_path, entry.name, self)
                 dlg.exec()
        except Exception as e:
             progress.close()
             QMessageBox.critical(self, "Lỗi", str(e))

    def reset(self):
        """Reset to initial state"""
        self.history = []
        self.history_index = -1
        if self.adb.current_device and self.adb.is_online():
            self.load_path(self.internal_root)
            self.worker.list_storages()
            self.worker.get_usage()
        else:
            self.tree.clear()
            self.grid.clear()
            self.status_bar.setText("Chưa kết nối thiết bị")

    def on_op_finished(self, success, msg):
        self.refresh()
        if not success:
             # Suppress specific connection errors
             msg_low = msg.lower()
             conn_errors = ["device", "not found", "offline", "no devices", "transport", "unauthorized"]
             if any(x in msg_low for x in conn_errors):
                 self.status_bar.setText(f"Lỗi: {msg}")
                 return 
             QMessageBox.warning(self, "Thông báo", msg)
        else:
             self.status_bar.setText(msg)
             
    def show_context_menu(self, pos):
        # Handle both views
        if self.stack.currentIndex() == 0:
             sender = self.tree
             item = sender.itemAt(pos)
             is_grid = False
        else:
             sender = self.grid
             item = sender.itemAt(pos)
             is_grid = True

        if not item: 
            # Background menu
            menu = QMenu()
            menu.addAction("➕ Tạo thư mục mới", self.create_folder)
            menu.addAction("🔄 Làm mới", self.refresh)
            if hasattr(self, 'clipboard_data') and self.clipboard_data:
                menu.addSeparator()
                menu.addAction(f"📋 Dán ({self.clipboard_data.get('action')})", self.paste_item)
            menu.exec(sender.mapToGlobal(pos))
            return
            
        entry = item.data(0, Qt.UserRole) if not is_grid else item.data(Qt.UserRole)
        menu = QMenu()
        menu.addAction("📂 Mở", lambda: self.on_item_double_click(item))
        menu.addSeparator()
        menu.addAction("Copy", lambda: self.set_clipboard("copy", entry))
        menu.addAction("Cut", lambda: self.set_clipboard("move", entry))
        menu.addSeparator()
        menu.addAction("✏️ Đổi tên", lambda: self.rename_item(entry))
        menu.addAction("🗑️ Xóa", lambda: self.delete_item(entry))
        menu.addSeparator()
        menu.addAction("⬇ Tải về máy tính", lambda: self.download_item(entry))
        menu.exec(sender.mapToGlobal(pos))

    # --- Actions (Same as before) ---
    def create_folder(self):
        name, ok = self.input_dialog("Tạo thư mục", "Tên thư mục:")
        if ok and name:
            self.worker.create_folder(f"{self.current_path}/{name}")

    def rename_item(self, entry):
        name, ok = self.input_dialog("Đổi tên", "Tên mới:", entry.name)
        if ok and name and name != entry.name:
            self.worker.rename_item(entry.path, f"{self.current_path}/{name}")

    def delete_item(self, entry):
        if QMessageBox.question(self, "Xóa", f"Bạn có chắc muốn xóa {entry.name}?") == QMessageBox.Yes:
            self.worker.delete_item(entry.path)

    def download_item(self, entry):
        target = QFileDialog.getExistingDirectory(self, "Chọn nơi lưu")
        if target:
            try:
                self.adb.pull_file(entry.path, target)
                QMessageBox.information(self, "Thành công", f"Đã tải {entry.name}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def upload_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn tập tin để tải lên")
        if files: self.upload_files(files)
            
    def handle_dropped_files(self, files):
        self.upload_files(files)

    def upload_files(self, files):
        if not files: return
        progress = QProgressDialog(f"Đang tải lên {len(files)} tập tin...", "Hủy", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            for i, local_path in enumerate(files):
                if progress.wasCanceled(): break
                filename = os.path.basename(local_path)
                dest = f"{self.current_path}/{filename}".replace('//', '/')
                self.adb.push_file(local_path, dest)
                progress.setValue(i+1)
            
            QMessageBox.information(self, "Hoàn tất", f"Đã tải lên {len(files)} tập tin.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
        finally:
            progress.close()

    def set_clipboard(self, action, entry):
        self.clipboard_data = {"action": action, "path": entry.path, "name": entry.name}
        self.status_bar.setText(f"Đã chọn {action}: {entry.name}")
        self.update_actions_state()

    def paste_item(self):
        if not self.clipboard_data: return
        src = self.clipboard_data['path']
        name = self.clipboard_data['name']
        dst = f"{self.current_path}/{name}"
        action = self.clipboard_data['action']
        if action == "copy": self.worker.copy_item(src, dst)
        elif action == "move": 
            self.worker.move_item(src, dst)
            self.clipboard_data = {}

    def input_dialog(self, title, label, text=""):
        from PySide6.QtWidgets import QInputDialog
        return QInputDialog.getText(self, title, label, text=text)

    # --- Action Bar handlers ---
    def get_selected_item(self):
        if self.stack.currentIndex() == 0:
             items = self.tree.selectedItems()
             if not items: return None
             return items[0].data(0, Qt.UserRole)
        else:
             items = self.grid.selectedItems()
             if not items: return None
             return items[0].data(Qt.UserRole)

    def action_new_folder(self):
        self.create_folder()

    def action_cut(self):
        entry = self.get_selected_item()
        if entry: self.set_clipboard("move", entry)

    def action_copy(self):
        entry = self.get_selected_item()
        if entry: self.set_clipboard("copy", entry)

    def action_paste(self):
        self.paste_item()
        self.update_actions_state()

    def action_rename(self):
        entry = self.get_selected_item()
        if entry: self.rename_item(entry)

    def action_delete(self):
        entry = self.get_selected_item()
        if entry: self.delete_item(entry)

    def update_actions_state(self):
        # 1. Selection
        if self.stack.currentIndex() == 0:
             count = len(self.tree.selectedItems())
        else:
             count = len(self.grid.selectedItems())
        
        has_sel = count > 0
        single_sel = count == 1
        
        # Guard against unitialized buttons
        if hasattr(self, 'btn_cut'):
            self.btn_cut.setEnabled(single_sel)
            self.btn_copy.setEnabled(single_sel)
            self.btn_rename.setEnabled(single_sel)
            self.btn_download.setEnabled(single_sel or has_sel) # Allow multi-download? 
            # For now single download if download_item doesn't support multi
            self.btn_download.setEnabled(single_sel) 
            self.btn_delete.setEnabled(has_sel)
            
            # 2. Clipboard
            has_clip = hasattr(self, 'clipboard_data') and self.clipboard_data
            self.btn_paste.setEnabled(bool(has_clip))

    def action_download(self):
        entry = self.get_selected_item()
        if entry: self.download_item(entry)
