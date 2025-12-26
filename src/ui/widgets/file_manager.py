# src/ui/widgets/file_manager.py
"""
File Manager Widget - HyperOS Style
Supports Internal/External Storage, File Operations, PC<->Mobile Transfer, and Image Preview
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QLineEdit, QMenu, QMessageBox, QFileDialog,
    QProgressDialog, QHeaderView, QComboBox, QFrame, QGridLayout, 
    QGraphicsDropShadowEffect, QInputDialog, QDialog, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QDir
from PySide6.QtGui import QIcon, QAction, QColor, QFont, QPixmap
import os
import shutil
import tempfile
from src.ui.theme_manager import ThemeManager
from src.workers.file_worker import FileWorker
from src.data.file_data import FileEntry

class CategoryCard(QFrame):
    """Clickable Category Card (HyperOS Style)"""
    clicked = Signal(str)

    def __init__(self, title, icon, color, suffix_path, parent=None):
        super().__init__(parent)
        self.suffix_path = suffix_path
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(100)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 20px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
            QFrame:hover {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_HOVER']};
                border: 1px solid {ThemeManager.COLOR_ACCENT};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            background-color: {color}20;
            color: {color};
            border-radius: 12px;
            font-size: 24px;
            border: none;
        """)
        layout.addWidget(icon_lbl)
        
        text = QLabel(title)
        text.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 600;
            color: {ThemeManager.get_theme()['COLOR_TEXT_PRIMARY']};
            background: transparent;
            border: none;
        """)
        layout.addWidget(text)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.suffix_path)
        super().mousePressEvent(event)

class ImagePreviewDialog(QDialog):
    """Simple Image Viewer Dialog"""
    def __init__(self, image_path, file_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Xem ảnh: {file_name}")
        self.resize(1000, 800)
        self.setStyleSheet(f"background-color: {ThemeManager.get_theme()['COLOR_BG_MAIN']};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        # Image Label
        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignCenter)
        
        # Load Image
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale down if larger than screen/dialog logic (simplified)
            if pixmap.width() > 1600 or pixmap.height() > 1200:
                 pixmap = pixmap.scaled(1600, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_lbl.setPixmap(pixmap)
        else:
            self.img_lbl.setText("Không thể tải ảnh")
            self.img_lbl.setStyleSheet("color: red; font-size: 16px;")
            
        scroll.setWidget(self.img_lbl)
        layout.addWidget(scroll)
        
        # Controls (Close)
        btn_close = QPushButton("Đóng")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(ThemeManager.get_button_style('outline'))
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        btn_layout.setContentsMargins(10, 10, 10, 10)
        
        layout.addLayout(btn_layout)


class FileManagerWidget(QWidget):
    """File Manager Widget"""
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        
        # Defaults
        self.internal_root = "/storage/emulated/0"
        self.current_root = self.internal_root
        self.current_path = self.internal_root
        
        self.detected_storages = {} 
        
        # Cache dir for previews
        self.cache_dir = os.path.join(tempfile.gettempdir(), "xiaomi_adb_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.setup_ui()
        
        # Initialize Worker
        self.file_worker = FileWorker(self.adb)
        self.file_worker.listing_ready.connect(self.on_listing_ready)
        self.file_worker.op_finished.connect(self.on_op_finished)
        
        # Initial Load
        if self.adb.current_device:
            self.refresh_storages()
            self.refresh_files()

    def on_listing_ready(self, entries):
        """Update UI with file list from worker"""
        self.tree.clear()
        self.path_lbl.setText(self.current_path)
        
        for entry in entries:
            self.add_tree_item(entry)
            
    def on_op_finished(self, success, msg):
        """Handle operation result"""
        if success:
            # self.status_bar.showMessage(msg) # If we had access to status bar
            self.refresh_files() # Refresh list
            if msg: QMessageBox.information(self, "Thành công", msg)
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # 1. Header
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.storage_btn = QPushButton("Bộ nhớ trong ▼")
        self.storage_btn.setCursor(Qt.PointingHandCursor)
        self.storage_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 26px;
                font-weight: 300;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                border: none;
                background: transparent;
                text-align: left;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: rgba(0,0,0,0.05);
                border-radius: 10px;
            }}
        """)
        self.storage_btn.clicked.connect(self.show_storage_menu)
        header_layout.addWidget(self.storage_btn)
        header_layout.addStretch()
        
        for icon, func in [("➕ New", self.create_folder), ("🔄", self.refresh_files)]:
            btn = QPushButton(icon)
            btn.setFixedSize(60 if "New" in icon else 40, 40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(func)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {ThemeManager.get_theme()['COLOR_GLASS_CARD']};
                    font-size: 16px;
                    border-radius: 12px;
                    border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                    color: {ThemeManager.COLOR_TEXT_PRIMARY};
                }}
                QPushButton:hover {{
                    background-color: {ThemeManager.COLOR_ACCENT}15;
                    border-color: {ThemeManager.COLOR_ACCENT};
                }}
            """)
            header_layout.addWidget(btn)
        main_layout.addWidget(header_container)
        
        # 2. Categories
        self.cat_grid = QGridLayout()
        self.cat_grid.setSpacing(15)
        self.cat_grid.setContentsMargins(10, 0, 10, 0)
        self.cards = [
            ("Tài liệu", "📄", "#FF9800", "Documents", 0, 0),
            ("Hình ảnh", "🖼️", "#F44336", "Pictures", 0, 1),
            ("Video", "🎬", "#9C27B0", "Movies", 1, 0),
            ("Âm thanh", "🎵", "#4CAF50", "Music", 1, 1),
        ]
        for title, icon, color, suffix, r, c in self.cards:
            card = CategoryCard(title, icon, color, suffix)
            card.clicked.connect(self.navigate_category)
            self.cat_grid.addWidget(card, r, c)
        main_layout.addLayout(self.cat_grid)
        
        # 3. Breadcrumbs
        nav_row = QHBoxLayout()
        nav_row.setContentsMargins(15, 0, 15, 0)
        back_btn = QPushButton("⬅")
        back_btn.setFixedSize(36, 36)
        back_btn.clicked.connect(self.go_up)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border-radius: 12px;
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                border-color: {ThemeManager.COLOR_ACCENT};
            }}
        """)
        nav_row.addWidget(back_btn)
        self.path_lbl = QLabel(self.current_path)
        self.path_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 13px; font-weight: 500;")
        nav_row.addWidget(self.path_lbl)
        nav_row.addStretch()
        main_layout.addLayout(nav_row)
        
        # 4. Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(3)
        self.tree.setIndentation(0)
        self.tree.setRootIsDecorated(False)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                border: none;
                margin: 0px 10px;
            }}
            QTreeWidget::item {{
                padding: 12px 10px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {ThemeManager.COLOR_ACCENT}15;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                border-radius: 12px;
            }}
            QTreeWidget::item:hover {{
                background-color: rgba(255,255,255,0.4);
                border-radius: 12px;
            }}
        """)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.setColumnWidth(1, 100)
        self.tree.hideColumn(2)
        main_layout.addWidget(self.tree)
        
        # 5. Bottom
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(15, 0, 15, 0)
        action_bar.addStretch()
        btn_upload = QPushButton("📥 Chép file từ Máy tính")
        btn_upload.clicked.connect(self.upload_file)
        btn_upload.setCursor(Qt.PointingHandCursor)
        btn_upload.setFixedHeight(45)
        btn_upload.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeManager.COLOR_ACCENT};
                color: white;
                font-weight: 600;
                border-radius: 22px;
                padding: 0 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #6aca3f;
            }}
        """)
        action_bar.addWidget(btn_upload)
        main_layout.addLayout(action_bar)
        
        if self.adb.current_device:
            self.refresh_storages()
            self.refresh_files()

    def refresh_storages(self):
        self.detected_storages = {}
        self.detected_storages["Bộ nhớ trong"] = self.internal_root
        try:
            output = self.adb.shell("ls /storage")
            if output and "No such" not in output:
                for line in output.split():
                    line = line.strip()
                    if line not in ["emulated", "self", "knox-emulated", "enc_emulated", "sdcard0"]:
                         self.detected_storages[f"Thẻ nhớ ({line})"] = f"/storage/{line}"
        except: pass
            
    def show_storage_menu(self):
        self.refresh_storages()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_CARD']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 12px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 10px 20px;
                border-radius: 8px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                font-size: 14px;
            }}
            QMenu::item:selected {{
                background-color: {ThemeManager.COLOR_ACCENT};
                color: white;
            }}
        """)
        for name, path in self.detected_storages.items():
            action = menu.addAction(name)
            action.setData(path)
        pos = self.storage_btn.mapToGlobal(self.storage_btn.rect().bottomLeft())
        selected = menu.exec(pos)
        if selected:
            self.switch_root(selected.data(), selected.text())

    def switch_root(self, root_path, display_name):
        self.current_root = root_path
        self.current_path = root_path
        self.storage_btn.setText(f"{display_name.split(' (')[0]} ▼")
        self.refresh_files()

    def navigate_category(self, suffix):
        self.navigate(f"{self.current_root}/{suffix}".replace('//', '/'))

    def navigate(self, path):
        self.current_path = path
        self.refresh_files()

    def refresh_files(self):
        if not self.adb.current_device: return
        self.tree.clear()
        self.path_lbl.setText(self.current_path + " (Đang tải...)")
        # Async call
        self.file_worker.list_files(self.current_path)
            
    def add_tree_item(self, entry: FileEntry):
        item = QTreeWidgetItem(self.tree)
        is_dir = entry.is_dir
        name = entry.name
        
        if is_dir: icon = "📁"
        else:
            icon = "📄"
            if name.lower().endswith('.apk'): icon = "🤖"
            elif name.lower().endswith(('.jpg','.png','.jpeg','.webp')): icon = "🖼️"
            elif name.lower().endswith(('.mp4','.avi','.mkv')): icon = "🎬"
            elif name.lower().endswith(('.mp3','.wav','.m4a')): icon = "🎵"
            elif name.lower().endswith('.zip'): icon = "📦"
            
        item.setText(0, f"{icon}  {name}")
        item.setData(0, Qt.UserRole, is_dir)
        item.setData(0, Qt.UserRole + 1, name)
        
        if not is_dir:
            item.setText(1, self.format_size(entry.size))
            item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
        
    def format_size(self, size_str):
        # TODO: Worker doesn't parse size yet (ls -1p limitation)
        # We can implement 'ls -la' parsing later for size
        return size_str if size_str else ""
            
    def go_up(self):
        if self.current_path == "/": return
        parent = os.path.dirname(self.current_path)
        if parent == self.current_path: return
        self.navigate(parent)
        
    def on_item_double_clicked(self, item, column):
        is_dir = item.data(0, Qt.UserRole)
        name = item.data(0, Qt.UserRole + 1)
        if is_dir:
            new_path = f"{self.current_path}/{name}".replace('//', '/')
            self.navigate(new_path)
        else:
            # Check for image
            if name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')):
                self.preview_image(name)
    
    def preview_image(self, filename):
        """Download and Preview Image"""
        src = f"{self.current_path}/{filename}".replace('//', '/')
        local_path = os.path.join(self.cache_dir, filename)
        
        # Show progress for large files
        progress = QProgressDialog("Đang tải ảnh...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            self.adb.pull_file(src, self.cache_dir)
            progress.close()
            
            # Open Dialog
            if os.path.exists(local_path):
                dlg = ImagePreviewDialog(local_path, filename, self)
                dlg.exec()
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể tải ảnh về để xem.")
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Lỗi", f"Lỗi hiển thị ảnh: {str(e)}")

    def create_folder(self):
        name, ok = QInputDialog.getText(self, "Tạo thư mục", "Tên thư mục mới:")
        if ok and name:
            target = f"{self.current_path}/{name}"
            # Use Worker
            self.file_worker.create_folder(target)

    def upload_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Chọn tập tin từ Máy tính")
        if files:
            dest_path, ok = QInputDialog.getText(self, "Chọn đích đến", "Thư mục đích:", text=self.current_path)
            if not ok or not dest_path: return
            progress = QProgressDialog("Đang chép...", "Hủy", 0, len(files), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            for i, file in enumerate(files):
                if progress.wasCanceled(): break
                try:
                    filename = os.path.basename(file)
                    target = f"{dest_path}/{filename}".replace('//', '/')
                    self.adb.push_file(file, target)
                except: pass
                progress.setValue(i+1)
            self.navigate(dest_path)
            QMessageBox.information(self, "Hoàn tất", f"Đã chép {len(files)} tập tin.")

    def download_selected(self):
        item = self.tree.currentItem()
        if not item: return
        name = item.data(0, Qt.UserRole + 1)
        source = f"{self.current_path}/{name}".replace('//', '/')
        target = QFileDialog.getExistingDirectory(self, "Lưu vào")
        if target:
            try:
                self.adb.pull_file(source, target)
                QMessageBox.information(self, "Thành công", f"Đã tải {name}")
            except Exception as e: QMessageBox.critical(self, "Lỗi", str(e))

    def rename_item(self):
        item = self.tree.currentItem()
        if not item: return
        old_name = item.data(0, Qt.UserRole + 1)
        new_name, ok = QInputDialog.getText(self, "Đổi tên", "Tên mới:", text=old_name)
        if ok and new_name and new_name != old_name:
            src = f"{self.current_path}/{old_name}"
            dst = f"{self.current_path}/{new_name}"
            self.file_worker.rename_item(src, dst)

    def delete_selected(self):
        item = self.tree.currentItem()
        if not item: return
        name = item.data(0, Qt.UserRole + 1)
        path = f"{self.current_path}/{name}"
        if QMessageBox.question(self, "Xóa", f"Xóa {name}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.file_worker.delete_item(path)

    def copy_selected(self): self._set_clipboard("copy")
    def cut_selected(self): self._set_clipboard("cut")
    def _set_clipboard(self, action):
        item = self.tree.currentItem()
        if not item: return
        name = item.data(0, Qt.UserRole + 1)
        self.clipboard_path = f"{self.current_path}/{name}".replace('//', '/')
        self.clipboard_action = action
        QMessageBox.information(self, "Clipboard", f"Đã {action}: {name}")
        
    def paste_clipboard(self):
        if not hasattr(self, 'clipboard_path') or not self.clipboard_path: return
        filename = os.path.basename(self.clipboard_path)
        dest = f"{self.current_path}/{filename}".replace('//', '/')
        
        if self.clipboard_action == "copy":
            self.file_worker.copy_item(self.clipboard_path, dest)
        elif self.clipboard_action == "cut":
            self.file_worker.move_item(self.clipboard_path, dest)
            self.clipboard_path = None # Clear after cut->paste request

    def show_context_menu(self, position):
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {ThemeManager.get_theme()['COLOR_GLASS_CARD']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 8px;
            }}
            QMenu::item {{ padding: 8px 20px; }}
            QMenu::item:selected {{ background-color: {ThemeManager.COLOR_ACCENT}; color: white; }}
        """)
        menu.addAction("📂 Mở / Xem", lambda: self.on_item_double_clicked(self.tree.currentItem(), 0))
        menu.addSeparator()
        menu.addAction("📋 Sao chép", self.copy_selected)
        menu.addAction("✂️ Cắt", self.cut_selected)
        if hasattr(self, 'clipboard_path') and self.clipboard_path: menu.addAction("📋 Dán vào đây", self.paste_clipboard)
        menu.addSeparator()
        menu.addAction("⬇ Tải về máy tính", self.download_selected)
        menu.addAction("✏ Đổi tên", self.rename_item)
        menu.addAction("🗑️ Xóa", self.delete_selected)
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def reset(self):
        self.refresh_storages()
        self.current_path = self.internal_root
        self.refresh_files()
