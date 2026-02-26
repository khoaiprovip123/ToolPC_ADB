
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QListWidget, QGraphicsDropShadowEffect, QGridLayout,
    QScrollArea, QListWidgetItem, QProgressBar, QSlider, QStackedWidget,
    QButtonGroup
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint, QSize, QTimer, 
    QProcess, QSettings, QUrl
)
from PySide6.QtGui import QColor, QIcon, QDesktopServices
import os
import shutil
from src.ui.theme_manager import ThemeManager
from src.core.log_manager import LogManager
from src.ui.widgets.notification_card import create_notification_card, create_empty_state

class NotificationCenter(QFrame):
    """
    Expanded Control Center with Tabbed Layout
    Tab 1: Control Panel (Status, Sliders, Toggles)
    Tab 2: Notifications (Log List)
    """
    
    def __init__(self, parent, adb_manager):
        super().__init__(parent)
        self.adb = adb_manager
        self.scrcpy_process = None
        self.settings = QSettings("XiaomiADB", "ScreenMirror")
        self.turn_screen_off_enabled = False  # Track screen-off state
        
        # Geometry: Right side drawer
        self.setFixedWidth(380)
        self.setFixedHeight(parent.height())
        self.hide() # START HIDDEN
        
        self.is_open = False
        self.setup_ui()
        
        # LogManager connection removed - now handled centrally by MainWindow dispatcher
        # to avoid duplication and allow better control over badges/UI.
        
        # Poll timer for status
        self.poll_timer = QTimer(self)
        self.poll_timer.interval = 5000 # 5s
        self.poll_timer.timeout.connect(self.update_status)
        
    def setup_ui(self):
        # Tech Gradient Style with Blur Background
        self.setStyleSheet(f"""
            NotificationCenter {{
                background-color: rgba(255, 255, 255, 0.95);
                border-left: 1px solid rgba(0, 0, 0, 0.08);
            }}
            QProgressBar {{
                background-color: rgba(255,255,255,0.3);
                border-radius: 3px;
                text-align: center;
                border: none;
                height: 6px;
                color: transparent;
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
            }}
            /* Simplified Slider - NO MARGINS */
            QSlider::groove:horizontal {{
                border: none;
                background: rgba(0,0,0,0.08);
                height: 20px;
                border-radius: 10px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4facfe, stop:1 #00f2fe);
                border-radius: 10px;
            }}
            QSlider::add-page:horizontal {{
                background: rgba(0,0,0,0.08);
                border-radius: 10px;
            }}
            QSlider::handle:horizontal {{
                background: white;
                border: 3px solid #4facfe;
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                border-color: #00f2fe;
                background: #fff;
                border-width: 4px;
            }}
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(-5, 0)
        self.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 30, 20, 20)
        main_layout.setSpacing(15)
        
        # --- 1. Header ---
        header = QHBoxLayout()
        self.title = QLabel("Trung tâm Điều khiển")
        self.title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        self.title.setWordWrap(False)  # Không cho xuống dòng
        self.title.setMinimumWidth(200)  # Đủ rộng cho text
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.handle_close)
        close_btn.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #888;")
        
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(close_btn)
        main_layout.addLayout(header)
        
        # --- 2. Content Stack ---
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # === TAB 1: Controls ===
        control_page = QWidget()
        ctrl_layout = QVBoxLayout(control_page)
        ctrl_layout.setContentsMargins(0, 5, 0, 0)
        ctrl_layout.setSpacing(15)
        
        # Scroll Area for Controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Fix horizontal scroll
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_l = QVBoxLayout(scroll_content)
        scroll_l.setContentsMargins(5, 0, 5, 0) # Add padding to prevent cut-off
        scroll_l.setSpacing(15)

        # > Status Cards
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        self.batt_card = self.create_status_card("Pin", "🔋", "-%", ThemeManager.COLOR_SUCCESS)
        self.batt_bar = self.batt_card.findChild(QProgressBar)
        status_layout.addWidget(self.batt_card)
        
        self.store_card = self.create_status_card("Bộ nhớ", "💾", "-/- GB", ThemeManager.COLOR_WARNING)
        self.store_bar = self.store_card.findChild(QProgressBar)
        status_layout.addWidget(self.store_card)
        scroll_l.addLayout(status_layout)
        
        # > Quick Toggles (no sliders)
        quick_label = QLabel("Tác vụ Nhanh")
        quick_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #888; text-transform: uppercase;")
        scroll_l.addWidget(quick_label)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        self.create_big_toggle(grid, "Mirror", "📱", "#007AFF", self.on_mirror, 0, 0)
        self.create_big_toggle(grid, "Wireless", "📡", "#34C759", self.on_debug, 0, 2)
        self.create_toggle_btn(grid, "Screen", "📷", self.on_screenshot, 1, 0)
        self.create_toggle_btn(grid, "Show Taps", "👆", self.toggle_taps, 1, 1, checkable=True)
        self.create_toggle_btn(grid, "Layout", "📐", self.toggle_layout, 1, 2, checkable=True)
        self.create_toggle_btn(grid, "Airplane", "✈️", self.toggle_airplane, 1, 3, checkable=True)
        self.create_toggle_btn(grid, "Settings", "⚙️", lambda: self.adb.shell("am start -a android.settings.SETTINGS"), 2, 0)
        self.create_toggle_btn(grid, "Dev Ops", "🛠️", lambda: self.adb.shell("am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS"), 2, 1)
        self.create_toggle_btn(grid, "Reboot", "↻", self.adb.reboot, 2, 2)
        self.create_toggle_btn(grid, "Màn hình", "📺", self.adb.toggle_screen, 2, 3)
        self.screen_off_btn = self.create_toggle_btn(grid, "Screen Off", "🌙", self.toggle_screen_off, 3, 0, checkable=True)
        scroll_l.addLayout(grid)
        
        scroll_l.addStretch()
        scroll.setWidget(scroll_content)
        ctrl_layout.addWidget(scroll)
        
        self.stack.addWidget(control_page)
        
        # === TAB 2: Notifications ===
        notif_page = QWidget()
        notif_layout = QVBoxLayout(notif_page)
        notif_layout.setContentsMargins(0, 5, 0, 0)
        
        notif_layout.setSpacing(10)
        
        # Header with Clear All button
        header = QHBoxLayout()
        header_label = QLabel(" ")
        header.addWidget(header_label)
        header.addStretch()
        self.clear_all_btn = QPushButton("Xóa tất cả")
        self.clear_all_btn.setCursor(Qt.PointingHandCursor)
        self.clear_all_btn.clicked.connect(self.clear_all_notifications)
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888;
                font-size: 13px;
                font-weight: 600;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #4facfe;
            }
        """)
        header.addWidget(self.clear_all_btn)
        notif_layout.addLayout(header)
        
        # Scroll area for notifications
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.notif_container = QWidget()
        self.notif_container_layout = QVBoxLayout(self.notif_container)
        self.notif_container_layout.setContentsMargins(5, 0, 5, 0)
        self.notif_container_layout.setSpacing(10)
        self.notif_container_layout.setAlignment(Qt.AlignTop)  # Align top instead of stretch
        
        scroll.setWidget(self.notif_container)
        notif_layout.addWidget(scroll)
        
        # Empty state (initially shown)
        self.empty_state = create_empty_state()
        self.notif_container_layout.addWidget(self.empty_state)
        
        # Store notification cards
        self.notification_cards = []
        
        self.stack.addWidget(notif_page)
        
    def handle_close(self):
        # If in Notification tab (1), switch back to Control (0)
        if self.stack.currentIndex() == 1:
            self.switch_tab(0)
        else:
            self.toggle()
            
    def switch_tab(self, idx):
        self.stack.setCurrentIndex(idx)
        if idx == 0:
            self.title.setText("Trung tâm Điều khiển")
        else:
            self.title.setText("Thông báo")

    def create_status_card(self, title, icon, value, color):
        card = QFrame()
        card.setFixedHeight(100)
        card.setObjectName("StatusCard")
        
        # Gradient background based on title
        if "Pin" in title or "PIN" in title:
            gradient_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #11998e, stop:1 #38ef7d)"
            shadow_color = QColor(17, 153, 142, 60)
        else:  # Storage
            gradient_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f093fb, stop:1 #f5576c)"
            shadow_color = QColor(240, 147, 251, 60)
        
        card.setStyleSheet(f"""
            #StatusCard {{
                background: {gradient_bg};
                border-radius: 20px;
                border: none;
            }}
            QLabel {{
                border: none;
                background: transparent;
                color: white;
            }}
        """)
        
        # Gradient glow shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(shadow_color)
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        
        l = QVBoxLayout(card)
        l.setSpacing(6)
        l.setContentsMargins(16, 14, 16, 14)
        
        top = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 24px; color: white;")
        
        l_info = QVBoxLayout()
        l_info.setSpacing(2)
        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.9); font-weight: 600; letter-spacing: 0.5px;")
        lbl_val = QLabel(value)
        lbl_val.setObjectName("value_label")
        lbl_val.setStyleSheet("font-weight: 800; font-size: 16px; color: white;")
        l_info.addWidget(lbl_title)
        l_info.addWidget(lbl_val)
        
        top.addWidget(lbl_icon)
        top.addSpacing(12)
        top.addLayout(l_info)
        top.addStretch()
        l.addLayout(top)
        
        pbar = QProgressBar()
        pbar.setTextVisible(False)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet("QProgressBar { background: rgba(255,255,255,0.3); border-radius: 3px; } QProgressBar::chunk { background: rgba(255,255,255,0.95); border-radius: 3px; }")
        l.addWidget(pbar)
        
        return card

    def create_big_toggle(self, grid, text, icon, color, callback, r, c):
        btn = QPushButton()
        btn.setFixedSize(145, 65)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        l = QHBoxLayout(btn)
        l.setContentsMargins(12, 0, 12, 0)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 24px; background: transparent; color: white;")
        lbl_text = QLabel(text)
        lbl_text.setStyleSheet("font-size: 14px; font-weight: 700; color: white;")
        
        l.addWidget(lbl_icon)
        l.addWidget(lbl_text)
        l.addStretch()
        
        # Gradient backgrounds
        if "Mirror" in text:
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff9a56, stop:1 #ff6a88)"
        else:  # Wireless
            gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a8edea, stop:1 #fed6e3)"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {gradient};
                border-radius: 16px;
                border: none;
            }}
            QPushButton:hover {{
                margin-top: -2px;
                margin-bottom: 2px;
            }}
            QPushButton:pressed {{
                margin-top: 1px;
                margin-bottom: -1px;
            }}
        """)
        grid.addWidget(btn, r, c, 1, 2)

    def create_toggle_btn(self, grid, text, icon, callback, r, c, checkable=False):
        btn = QPushButton(icon)
        btn.setFixedSize(68, 68)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(checkable)
        btn.setToolTip(text)
        btn.clicked.connect(callback)
        
        style = f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 18px;
                font-size: 28px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.9);
                margin-top: -1px;
                margin-bottom: 1px;
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
            }}
            QPushButton:pressed {{
                margin-top: 1px;
                margin-bottom: -1px;
            }}
        """
        btn.setStyleSheet(style)
        grid.addWidget(btn, r, c)
        return btn

    def toggle(self, tab_index=None):
        parent = self.parent()
        if not parent: return
        
        # Determine target state
        should_open = False
        
        if tab_index is not None:
            # Check if we are already open and on the same tab
            if self.isVisible() and self.stack.currentIndex() == tab_index:
                should_open = False # Toggle Close
            elif self.isVisible() and self.stack.currentIndex() != tab_index:
                # Just switch tab, stay open
                self.switch_tab(tab_index)
                return 
            else:
                # Open with specific tab
                self.switch_tab(tab_index)
                should_open = True
        else:
            # Default toggle behavior
            should_open = not self.isVisible()

        if not should_open:
            # Close
            self.hide()
            self.poll_timer.stop()
            self.is_open = False
        else:
            # Open
            # Force update geometry to ensure it fits parent height
            parent_rect = parent.rect()
            # Since we are parented to CentralWidget, we use its rect
            self.setFixedHeight(parent_rect.height())
            self.setGeometry(
                parent_rect.width() - self.width(), 
                0, 
                self.width(), 
                parent_rect.height()
            )
            self.raise_()
            self.show()
            
            self.is_open = True
            
            # Refresh data on open
            self.update_status()
            self.poll_timer.start()

    def update_status(self):
        """Fetch and update system info - Optimized with Real Values"""
        if not self.adb.current_device: return
        
        # Battery
        try:
            info = self.adb.get_battery_info()
            level = info.get('level', 0)
            self.batt_bar.setValue(level)
            self.batt_card.findChild(QLabel, "value_label").setText(f"{level}%")
        except Exception as _e:

            pass  # TODO: consider LogManager.log
        
        # Storage
        try:
            store = self.adb.get_storage_info()
            # store returns Bytes. Convert to GB.
            used_bytes = store.get('used', 0)
            total_bytes = store.get('total', 0)
            
            used_gb = used_bytes / (1024 * 1024 * 1024)
            total_gb = total_bytes / (1024 * 1024 * 1024)
            
            pct = 0
            if total_bytes > 0:
                pct = int((used_bytes / total_bytes) * 100)
                
            self.store_card.findChild(QLabel, "value_label").setText(f"{used_gb:.1f}/{total_gb:.0f} GB")
            self.store_bar.setValue(pct)
        except Exception as _e:

            pass  # TODO: consider LogManager.log
        
        # Get Real Brightness from Device
        try:
            result = self.adb.shell("settings get system screen_brightness")
            if result and result.strip().isdigit():
                brightness = int(result.strip())
                self.bright_slider.blockSignals(True)
                self.bright_slider.setValue(brightness)
                self.bright_slider.blockSignals(False)
                pct = int((brightness / 255) * 100)
                self.bright_value_lbl.setText(f"{pct}%")
        except Exception as _e:

            pass  # TODO: consider LogManager.log
        
        # Get Real Volume from Device (try multiple streams)
        try:
            # Try media volume first (stream 3)
            result = self.adb.shell("cmd media_session volume --show --stream 3")
            if not result or "volume" not in result.lower():
                # Fallback: get from settings
                result = self.adb.shell("settings get system volume_music")
            
            # Parse volume value
            if result and result.strip():
                # Extract number from result
                import re
                match = re.search(r'\d+', result.strip())
                if match:
                    volume = int(match.group())
                    # Ensure in range 0-15
                    volume = max(0, min(15, volume))
                    self.vol_slider.blockSignals(True)
                    self.vol_slider.setValue(volume)
                    self.vol_slider.blockSignals(False)
                    self.vol_value_lbl.setText(str(volume))
                    # Check if muted
                    if volume == 0 and not self.vol_muted:
                        self.vol_muted = True
                        self.vol_icon_btn.setText("🔇")
                    elif volume > 0 and self.vol_muted:
                        self.vol_muted = False
                        self.vol_icon_btn.setText("🔊")
        except Exception as _e:

            pass  # TODO: consider LogManager.log

    # --- Actions ---
    def toggle_mute(self):
        """Toggle volume mute/unmute"""
        if self.vol_muted:
            # Unmute: restore previous volume
            self.vol_slider.setValue(self.vol_before_mute)
            self.adb.set_volume(self.vol_before_mute)
            self.vol_icon_btn.setText("🔊")
            self.vol_muted = False
        else:
            # Mute: save current volume and set to 0
            self.vol_before_mute = self.vol_slider.value()
            self.vol_slider.setValue(0)
            self.adb.set_volume(0)
            self.vol_icon_btn.setText("🔇")
            self.vol_muted = True
    
    def on_brightness_change(self):
        val = self.bright_slider.value()
        pct = int((val / 255) * 100)
        self.bright_value_lbl.setText(f"{pct}%")
        self.adb.set_brightness(val)
        
    def on_volume_change(self):
        val = self.vol_slider.value()
        self.vol_value_lbl.setText(str(val))
        # Use media session to set volume (more reliable)
        try:
            # Method 1: Use media session (Android 5+)
            self.adb.shell(f"cmd media_session volume --set {val} --stream 3")
        except Exception as _e:
            # Fallback: Traditional method
            self.adb.set_volume(val)
        
        # Update mute icon based on volume
        if val == 0:
            self.vol_icon_btn.setText("🔇")
            self.vol_muted = True
        else:
            self.vol_icon_btn.setText("🔊")
            self.vol_muted = False
        
    def toggle_taps(self):
        btn = self.sender()
        self.adb.toggle_show_taps(btn.isChecked())
        
    def toggle_layout(self):
        btn = self.sender()
        self.adb.toggle_layout_bounds(btn.isChecked())

    def toggle_airplane(self):
        btn = self.sender()
        val = 1 if btn.isChecked() else 0
        self.adb.shell(f"settings put global airplane_mode_on {val}")
        self.adb.shell("am broadcast -a android.intent.action.AIRPLANE_MODE")
    
    def toggle_screen_off(self):
        """Toggle screen-off mode for mirroring"""
        btn = self.sender()
        self.turn_screen_off_enabled = btn.isChecked()
        
        if btn.isChecked():
            self.add_notification("info", "🌙 Screen Off enabled - Màn hình phone sẽ tắt khi mirror")
        else:
            self.add_notification("info", "☀️ Screen Off disabled - Màn hình phone sẽ bật khi mirror")

    def on_mirror(self):
        # Toggle Mirror
        if self.scrcpy_process and self.scrcpy_process.state() == QProcess.Running:
            self.stop_mirroring()
        else:
            self.start_mirroring()
    
    # === Notification Methods ===
    # create_empty_state() và create_notification_card()
    # đã được chuyển sang src/ui/widgets/notification_card.py (C1)

    def add_notification(self, notif_type='info', message='', title='System'):
        """Add a new notification to the panel"""
        # Tránh hiện thông báo kỹ thuật mức debug/verbose
        if notif_type.lower() in ['debug', 'verbose']:
            return
            
        # Hide empty state
        if hasattr(self, 'empty_state'):
            self.empty_state.hide()
        
        # C1: Dùng module-level helper từ notification_card.py
        card = create_notification_card(self, notif_type, message, title)
        # Thêm nút Đóng riêng (vì helper không biết dismiss callback)
        from PySide6.QtWidgets import QPushButton as _QPushButton
        close_btn = _QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: white; font-size: 20px; font-weight: bold; }
            QPushButton:hover { background: rgba(255,255,255,0.2); border-radius: 12px; }
        """)
        close_btn.clicked.connect(lambda: self.dismiss_notification(card))
        card.layout().addWidget(close_btn)
        
        self.notification_cards.append(card)
        
        # Insert at top (after empty_state which is at index 0)
        insert_pos = len(self.notification_cards)
        self.notif_container_layout.insertWidget(insert_pos, card)
        
        # Auto-open notification center if hidden
        if not self.isVisible():
            parent = self.parent()
            if parent:
                # Set geometry
                parent_rect = parent.rect()
                self.setFixedHeight(parent_rect.height())
                self.setGeometry(
                    parent_rect.width() - self.width(), 
                    0, 
                    self.width(), 
                    parent_rect.height()
                )
                # Force show
                self.raise_()
                self.show()
                self.is_open = True
                # Start polling
                self.update_status()
                self.poll_timer.start()
        
        # Switch to notification tab
        self.switch_tab(1)
        
        # Show clear all button
        self.clear_all_btn.setVisible(True)
    
    def dismiss_notification(self, card):
        """Remove a specific notification"""
        if card in self.notification_cards:
            self.notification_cards.remove(card)
        card.deleteLater()
        
        # Show empty state if no cards left
        if len(self.notification_cards) == 0:
            self.empty_state.show()
            self.clear_all_btn.setVisible(False)
    
    def clear_all_notifications(self):
        """Clear all notifications"""
        for card in self.notification_cards:
            card.deleteLater()
        self.notification_cards.clear()
        self.empty_state.show()
        self.clear_all_btn.setVisible(False)
    
    def start_mirroring(self):
        if not self.adb.current_device:
            self.add_notification("Mirror Error", "Chưa kết nối thiết bị", "error")
            return

        scrcpy_path = self.find_scrcpy()
        if not scrcpy_path:
            self.add_notification("Mirror Error", "Không tìm thấy scrcpy.exe", "error")
            return

        # Optimized Arguments for Smoothness
        # -b 4M: 4Mbps bitrate (Balance quality/latency)
        # --max-size 1024: 1024p max dimension (Good enough for control)
        # --no-audio: Prevent crashes/latency
        # --max-fps 60: Cap FPS
        args = [
            "-s", self.adb.current_device,
            "--video-bit-rate", "4M",
            "--max-size", "1024",
            "--no-audio",
            "--max-fps", "60",
            "--window-title", f"Mirror - {self.adb.current_device}"
        ]
        
        # Add --turn-screen-off if enabled
        if self.turn_screen_off_enabled:
            args.append("--turn-screen-off")
        
        # Start Process
        self.scrcpy_process = QProcess()
        self.scrcpy_process.finished.connect(self.on_mirror_finished)
        
        # Env setup for ADB finding
        scrcpy_dir = os.path.dirname(scrcpy_path)
        self.scrcpy_process.setWorkingDirectory(scrcpy_dir)
        
        self.scrcpy_process.start(scrcpy_path, args)
        if self.scrcpy_process.waitForStarted(1000):
            mode_text = " (Screen Off)" if self.turn_screen_off_enabled else ""
            self.add_notification("Mirror", f"Đã bắt đầu phản chiếu{mode_text}", "success")
        else:
            self.add_notification("Mirror Error", f"Lỗi khởi động: {self.scrcpy_process.errorString()}", "error")

    def stop_mirroring(self):
        if self.scrcpy_process and self.scrcpy_process.state() == QProcess.Running:
            self.scrcpy_process.terminate()
            self.scrcpy_process.waitForFinished(1000)
            self.scrcpy_process = None
            self.add_notification("Mirror", "Đã dừng phản chiếu", "info")

    def on_mirror_finished(self):
        self.scrcpy_process = None
        # self.add_notification("Mirror", "Kết thúc phiên phản chiếu", "info")

    def find_scrcpy(self):
        # 1. Check settings
        saved = self.settings.value("scrcpy_path", "")
        if saved and os.path.exists(saved): return saved
        
        # 2. Check bundled resources (PyInstaller)
        import sys
        if hasattr(sys, '_MEIPASS'):
            bundled = os.path.join(sys._MEIPASS, "resources", "scrcpy", "scrcpy.exe")
            if os.path.exists(bundled): return bundled
            
        # 3. Check local resources
        root = os.getcwd()
        defaults = [
            os.path.join(root, "scripts", "scrcpy.exe"),
            os.path.join(root, "resources", "scrcpy", "scrcpy.exe")
        ]
        for p in defaults:
            if os.path.exists(p): return p
            
        # 4. System path
        return shutil.which("scrcpy")

    def on_debug(self):
        pass
    
    def on_screenshot(self):
        self.adb.screenshot()

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)
