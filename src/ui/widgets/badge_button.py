from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon


class NotifBadgeButton(QWidget):
    """
    B1: Nút thông báo có badge số đỏ overlay góc trên phải.
    Thay thế QPushButton đơn trong header của MainWindow.

    Sử dụng:
        btn = NotifBadgeButton(icon_path, tooltip="Thông báo")
        btn.clicked.connect(handler)
        btn.increment("error")  # Tăng badge, màu theo level
        btn.reset()             # Xóa badge khi mở panel
    """

    # Màu badge theo log level (error > warning > info = success = default)
    BADGE_COLORS = {
        "error":   "#FF4B2B",  # Modern Red Gradient Start
        "warning": "#F59E0B",  # Orange
        "info":    "#007AFF",  # iOS Blue
        "success": "#34C759",  # iOS Green
    }

    def __init__(self, icon_path: str = "", tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(42, 42)
        self._count = 0
        self._highest_level = "info"  # Level cao nhất hiện tại

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Nút chính
        self.btn = QPushButton()
        self.btn.setFixedSize(36, 36)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setToolTip(tooltip)
        self._apply_button_style()

        if icon_path:
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.btn.setIcon(icon)
                self.btn.setIconSize(QSize(18, 18))
            else:
                self.btn.setText("🔔")
        else:
            self.btn.setText("🔔")

        layout.addWidget(self.btn)

        # Badge label (ẩn ban đầu)
        self.badge = QLabel(self)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setFixedSize(18, 18)
        self.badge.move(22, 2)  # Góc trên phải
        self.badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.badge.hide()
        self._update_badge_style()

        # Forward clicked signal
        self.clicked = self.btn.clicked

    def _apply_button_style(self):
        from src.ui.theme_manager import ThemeManager
        self.btn.setStyleSheet(ThemeManager.get_icon_button_style())

    def _update_badge_style(self):
        color = self.BADGE_COLORS.get(self._highest_level, "#FF4B2B")
        self.badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 9px;
                font-size: 10px;
                font-weight: 800;
                border: 0.5px solid rgba(255,255,255,0.4);
                font-family: 'Outfit', sans-serif;
            }}
        """)

    def increment(self, level: str = "info"):
        """Tăng badge count. Level cao hơn ghi đè màu."""
        self._count += 1
        # Cập nhật level cao nhất (error > warning > info/success)
        priority = {"error": 3, "warning": 2, "info": 1, "success": 1}
        if priority.get(level, 1) >= priority.get(self._highest_level, 1):
            self._highest_level = level
        self._refresh()

    def reset(self):
        """Xóa badge khi user mở notification panel."""
        self._count = 0
        self._highest_level = "info"
        self.badge.hide()

    def set_count(self, n: int, level: str = "info"):
        """Đặt giá trị badge trực tiếp."""
        self._count = n
        self._highest_level = level
        self._refresh()

    def _refresh(self):
        if self._count <= 0:
            self.badge.hide()
            return
        display = str(self._count) if self._count < 100 else "99+"
        self.badge.setText(display)
        # Điều chỉnh width cho số lớn
        w = max(18, len(display) * 8 + 4)
        self.badge.setFixedWidth(w)
        self.badge.move(42 - w - 2, 2)
        self._update_badge_style()
        self.badge.show()
        self.badge.raise_()
