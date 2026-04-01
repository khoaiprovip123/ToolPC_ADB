"""
C1: notification_card.py — Tách helper functions khỏi NotificationCenter.
Cung cấp create_notification_card() và create_empty_state() độc lập.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QDialog, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics, QFont

from src.ui.theme_manager import ThemeManager
from PySide6.QtWidgets import QGraphicsDropShadowEffect


def create_empty_state() -> QWidget:
    """Tạo widget trạng thái rỗng khi chưa có thông báo."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignCenter)
    layout.setSpacing(8)

    icon = QLabel("🔔")
    icon.setStyleSheet(f"font-size: 48px; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}40; background: transparent; border: none;")
    icon.setAlignment(Qt.AlignCenter)

    text1 = QLabel("Không có thông báo")
    text1.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}; font-family: {ThemeManager.FONT_FAMILY}; background: transparent; border: none;")
    text1.setAlignment(Qt.AlignCenter)

    text2 = QLabel("Tất cả đều đã xử lý xong!")
    text2.setStyleSheet(f"font-size: 13px; font-weight: 400; color: {ThemeManager.get_theme()['COLOR_TEXT_SECONDARY']}80; font-family: {ThemeManager.FONT_FAMILY}; background: transparent; border: none;")
    text2.setAlignment(Qt.AlignCenter)

    layout.addWidget(icon)
    layout.addWidget(text1)
    layout.addWidget(text2)
    widget.setMinimumHeight(200)
    return widget


def create_notification_card(parent: QWidget, notif_type: str, message: str,
                              title: str = "System", timestamp=None) -> QFrame:
    """
    Tạo card thông báo hiện đại với gradient theo loại.

    Args:
        parent: Widget cha (để làm parent cho dialogs)
        notif_type: 'success' | 'error' | 'warning' | 'info'
        message: Nội dung thông báo
        title: Tiêu đề ngắn (mặc định 'System')
        timestamp: datetime object, dùng now() nếu None
    """
    from datetime import datetime as dt

    if timestamp is None:
        timestamp = dt.now()

    gradients = {
        'success': (ThemeManager.COLOR_SUCCESS_GRADIENT,
                    QColor(16, 185, 129, 60), '✓', ThemeManager.COLOR_SUCCESS),
        'error':   (ThemeManager.COLOR_ERROR_GRADIENT,
                    QColor(239, 68, 68, 60), '✗', ThemeManager.COLOR_ERROR),
        'warning': ('qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f59e0b, stop:1 #fbbf24)',
                    QColor(245, 158, 11, 50), '⚠', '#f59e0b'),
        'info':    (ThemeManager.COLOR_ACCENT_GRADIENT,
                    QColor(59, 130, 246, 50), 'ℹ', ThemeManager.COLOR_ACCENT),
    }
    gradient, shadow_color, icon_text, _border = gradients.get(notif_type, gradients['info'])

    card = QFrame()
    card.setMinimumHeight(85)
    card.setMaximumHeight(130)
    card.setCursor(Qt.PointingHandCursor)
    card.setStyleSheet(f"""
        QFrame {{
            background: {gradient};
            border-radius: 18px;
            border: 0.5px solid rgba(255,255,255,0.2);
        }}
    """)

    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(15)
    shadow.setColor(shadow_color)
    shadow.setOffset(0, 4)
    card.setGraphicsEffect(shadow)

    layout = QHBoxLayout(card)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(10)

    # Icon circle
    icon_container = QFrame()
    icon_container.setFixedSize(32, 32)
    icon_container.setStyleSheet("""
        QFrame { background-color: rgba(0, 0, 0, 0.15); border-radius: 16px; }
    """)
    icon_layout = QVBoxLayout(icon_container)
    icon_layout.setContentsMargins(0, 0, 0, 0)
    icon_layout.setAlignment(Qt.AlignCenter)

    icon_label = QLabel(icon_text)
    icon_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; background: transparent; border: none;")
    icon_label.setAlignment(Qt.AlignCenter)
    icon_layout.addWidget(icon_label)
    layout.addWidget(icon_container)

    # Content
    content_layout = QVBoxLayout()
    content_layout.setSpacing(2)

    time_str = timestamp.strftime("%H:%M %p")
    header_row = QHBoxLayout()
    header_row.setSpacing(10)

    title_label = QLabel(title.upper())
    title_label.setStyleSheet(f"""
        font-size: 11px; font-weight: 800; color: rgba(255,255,255,0.95);
        background: transparent; letter-spacing: 0.5px;
        font-family: {ThemeManager.FONT_FAMILY};
    """)
    header_row.addWidget(title_label)
    header_row.addStretch()

    time_label = QLabel(time_str)
    time_label.setStyleSheet("""
        font-size: 10px; color: rgba(255,255,255,0.6);
        background: transparent; font-weight: 500;
    """)
    header_row.addWidget(time_label)
    content_layout.addLayout(header_row)

    # Message with truncation
    font = QFont()
    font.setPixelSize(13)
    font.setBold(True)
    fm = QFontMetrics(font)
    max_width = 220

    lines = []
    current_line = ""
    for word in message.split():
        test_line = current_line + (" " if current_line else "") + word
        if fm.horizontalAdvance(test_line) > max_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    is_truncated = len(lines) > 2
    if is_truncated:
        elided = " ".join(lines[:2]) + "... <a href='#' style='color: rgba(255,255,255,0.9);'>Xem thêm ›</a>"
    else:
        elided = message

    msg_label = QLabel()
    msg_label.setWordWrap(True)
    msg_label.setFont(font)
    msg_label.setText(elided)
    msg_label.setTextFormat(Qt.RichText)
    msg_label.setOpenExternalLinks(False)
    msg_label.setStyleSheet(f"""
        font-size: 13px; font-weight: 600; color: white;
        background: transparent; line-height: 1.4;
        font-family: {ThemeManager.FONT_FAMILY};
    """)

    if is_truncated:
        def show_full():
            dialog = QDialog(parent)
            dialog.setWindowTitle("Chi tiết thông báo")
            dialog.setMinimumSize(400, 200)
            dlg_layout = QVBoxLayout(dialog)
            dlg_layout.setContentsMargins(20, 20, 20, 20)
            full_msg = QTextEdit()
            full_msg.setPlainText(message)
            full_msg.setReadOnly(True)
            dlg_layout.addWidget(full_msg)
            dialog.exec()

        msg_label.linkActivated.connect(lambda _: show_full())

    content_layout.addWidget(msg_label)
    layout.addLayout(content_layout)

    return card
