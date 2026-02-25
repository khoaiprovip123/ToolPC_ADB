# src/ui/dialogs/confirmation_dialog.py
"""
Reusable Confirmation Dialog - Soft UI / Premium Style
Used for dangerous or destructive actions.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsDropShadowEffect, QCheckBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QFont
from src.ui.theme_manager import ThemeManager

class ConfirmationDialog(QDialog):
    """
    Premium Confirmation Dialog for critical actions
    """
    def __init__(self, parent=None, 
                 title="Xác nhận", 
                 message="Bạn có chắc chắn muốn thực hiện hành động này?",
                 details=None,
                 confirm_text="Xác nhận",
                 cancel_text="Hủy bỏ",
                 warning_mode=True,
                 show_dont_ask=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(450)
        
        self.dont_ask_again = False
        
        self.setup_ui(message, details, confirm_text, cancel_text, warning_mode, show_dont_ask)
        
    def setup_ui(self, message, details, confirm_text, cancel_text, warning_mode, show_dont_ask):
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Container
        self.container = QFrame()
        self.container.setObjectName("ConfirmContainer")
        theme = ThemeManager.get_theme()
        
        bg_color = theme['COLOR_BG_MAIN']
        border_color = theme['COLOR_BORDER']
        
        self.container.setStyleSheet(f"""
            #ConfirmContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 20px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(15)
        
        # Header (Icon + Message)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_char = "⚠️" if warning_mode else "❓"
        icon_color = "#ff4757" if warning_mode else "#2f3542"
        
        icon_lbl.setText(icon_char)
        icon_lbl.setStyleSheet(f"""
            background-color: {icon_color}20;
            color: {icon_color};
            border-radius: 12px;
            font-size: 24px;
            font-weight: bold;
        """)
        header_layout.addWidget(icon_lbl)
        
        # Message
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {theme['COLOR_TEXT_PRIMARY']};")
        header_layout.addWidget(msg_lbl, 1)
        
        container_layout.addLayout(header_layout)
        
        # Details (Sub-message)
        if details:
            details_lbl = QLabel(details)
            details_lbl.setWordWrap(True)
            details_lbl.setStyleSheet(f"font-size: 13px; color: {theme['COLOR_TEXT_SECONDARY']}; line-height: 1.4;")
            container_layout.addWidget(details_lbl)
            
        # "Don't ask again" checkbox
        if show_dont_ask:
            self.chk_dont_ask = QCheckBox("Không hiện lại xác nhận này")
            self.chk_dont_ask.setStyleSheet(f"""
                QCheckBox {{ color: {theme['COLOR_TEXT_SECONDARY']}; font-size: 12px; margin-top: 10px; }}
                QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 1px solid {theme['COLOR_BORDER']}; }}
                QCheckBox::indicator:checked {{ background-color: {ThemeManager.COLOR_ACCENT}; border: none; }}
            """)
            container_layout.addWidget(self.chk_dont_ask)
            
        container_layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        btn_cancel = QPushButton(cancel_text)
        btn_cancel.setFixedHeight(42)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(ThemeManager.get_button_style("outline"))
        btn_cancel.clicked.connect(self.reject)
        
        btn_confirm = QPushButton(confirm_text)
        btn_confirm.setFixedHeight(42)
        btn_confirm.setCursor(Qt.PointingHandCursor)
        confirm_style = "danger" if warning_mode else "primary"
        btn_confirm.setStyleSheet(ThemeManager.get_button_style(confirm_style))
        btn_confirm.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_confirm)
        
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(self.container)
        
    def exec_(self):
        """Override exec to return checkbox state"""
        result = super().exec_()
        if hasattr(self, 'chk_dont_ask'):
            self.dont_ask_again = self.chk_dont_ask.isChecked()
        return result
