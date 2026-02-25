"""
B3: FavoritesWidget — Hiển thị danh sách lệnh ADB yêu thích trong DeveloperPage.
Sử dụng FavoritesManager để lưu/tải từ QSettings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from src.ui.theme_manager import ThemeManager
from src.core.favorites_manager import FavoritesManager
from src.core.log_manager import LogManager


class FavoritesWidget(QWidget):
    """
    Widget hiển thị và quản lý danh sách lệnh ADB yêu thích.
    Emit signal run_command khi user click Chạy.
    """
    run_command = Signal(str)  # Emit lệnh ADB cần chạy

    def __init__(self, adb_manager, parent=None):
        super().__init__(parent)
        self.adb = adb_manager
        self.manager = FavoritesManager()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QHBoxLayout()
        title = QLabel("⭐ Lệnh Yêu Thích")
        title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {ThemeManager.COLOR_ACCENT};")
        header.addWidget(title)
        header.addStretch()

        clear_btn = QPushButton("Xóa tất cả")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("background: transparent; border: none; color: #888; font-size: 13px;")
        clear_btn.clicked.connect(self.clear_all)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # Add new command bar
        add_card = QFrame()
        add_card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_CARD']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER']};
                border-radius: 12px;
                padding: 5px;
            }}
        """)
        add_layout = QHBoxLayout(add_card)
        add_layout.setContentsMargins(12, 8, 12, 8)
        add_layout.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Tên lệnh (e.g. Reboot Recovery)")
        self.name_input.setStyleSheet(ThemeManager.get_input_style())
        self.name_input.setFixedWidth(200)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Lệnh ADB (e.g. reboot recovery)")
        self.cmd_input.setStyleSheet(ThemeManager.get_input_style())
        self.cmd_input.returnPressed.connect(self.add_favorite)

        save_btn = QPushButton("♥ Lưu")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        save_btn.clicked.connect(self.add_favorite)

        add_layout.addWidget(QLabel("Tên:"))
        add_layout.addWidget(self.name_input)
        add_layout.addSpacing(5)
        add_layout.addWidget(QLabel("Lệnh:"))
        add_layout.addWidget(self.cmd_input, stretch=1)
        add_layout.addWidget(save_btn)
        layout.addWidget(add_card)

        # Danh sách yêu thích
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, stretch=1)

        self.refresh_list()

    def refresh_list(self):
        """Tải lại danh sách từ FavoritesManager."""
        # Xóa hết card cũ
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = self.manager.get_all()
        if not items:
            empty = QLabel("Chưa có lệnh yêu thích nào.\nThêm lệnh ở thanh trên để bắt đầu! ⭐")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #aaa; font-size: 14px; padding: 40px;")
            self.list_layout.addWidget(empty)
            return

        for i, item in enumerate(items):
            card = self._create_cmd_card(item["name"], item["command"], i)
            self.list_layout.addWidget(card)

    def _create_cmd_card(self, name: str, command: str, index: int) -> QFrame:
        """Tạo card cho một lệnh yêu thích."""
        theme = ThemeManager.get_theme()
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {theme['COLOR_GLASS_CARD']};
                border: 1px solid {theme['COLOR_BORDER']};
                border-radius: 10px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        # Icon + Name
        star = QLabel("⭐")
        star.setStyleSheet("font-size: 16px;")
        layout.addWidget(star)

        info = QVBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {theme['COLOR_TEXT_PRIMARY']};")
        cmd_lbl = QLabel(command)
        cmd_lbl.setStyleSheet(f"font-size: 12px; color: {theme['COLOR_TEXT_SECONDARY']}; font-family: monospace;")
        info.addWidget(name_lbl)
        info.addWidget(cmd_lbl)
        layout.addLayout(info, stretch=1)

        # Nút Chạy
        run_btn = QPushButton("▶ Chạy")
        run_btn.setFixedWidth(80)
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        run_btn.clicked.connect(lambda _, cmd=command: self._run_command(cmd))
        layout.addWidget(run_btn)

        # Nút Xóa
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("background: transparent; border: none; color: #888; font-size: 14px; font-weight: bold;")
        del_btn.clicked.connect(lambda _, cmd=command: self._remove_command(cmd))
        layout.addWidget(del_btn)

        return card

    def _run_command(self, command: str):
        """Chạy lệnh ADB, emit signal để parent xử lý."""
        LogManager.log("Favorites", f"▶ Chạy lệnh: {command}", "info")
        self.run_command.emit(command)

    def _remove_command(self, command: str):
        """Xóa lệnh khỏi danh sách."""
        self.manager.remove(command)
        self.refresh_list()

    def add_favorite(self):
        """Thêm lệnh mới từ input box."""
        name = self.name_input.text().strip()
        command = self.cmd_input.text().strip()

        if not name:
            name = command  # Dùng command làm tên nếu không nhập tên

        if not command:
            return

        success = self.manager.add(name, command)
        if success:
            self.name_input.clear()
            self.cmd_input.clear()
            self.refresh_list()
            LogManager.log("Favorites", f"✓ Đã lưu lệnh yêu thích: {name}", "success")
        else:
            LogManager.log("Favorites", f"⚠ Lệnh '{command}' đã tồn tại trong danh sách", "warning")

    def clear_all(self):
        """Xóa toàn bộ danh sách."""
        self.manager.clear()
        self.refresh_list()
        LogManager.log("Favorites", "🗑️ Đã xóa tất cả lệnh yêu thích", "info")

    def reset(self):
        """Reset widget (gọi từ DeveloperPage.reset)."""
        self.refresh_list()
