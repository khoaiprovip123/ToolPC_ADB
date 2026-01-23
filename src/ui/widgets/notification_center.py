
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
        
        # Geometry: Right side drawer
        self.setFixedWidth(380)
        self.setFixedHeight(parent.height())
        self.hide() # START HIDDEN
        
        self.is_open = False
        self.setup_ui()
        
        # Connect LogManager singleton
        LogManager.get_instance().log_signal.connect(self.add_notification)
        
        # Poll timer for status
        self.poll_timer = QTimer(self)
        self.poll_timer.interval = 5000 # 5s
        self.poll_timer.timeout.connect(self.update_status)
        
    def setup_ui(self):
        # Apply Glassmorphism & Base Styling
        self.setStyleSheet(f"""
            NotificationCenter {{
                background-color: rgba(255, 255, 255, 0.98);
                border-left: 1px solid rgba(0, 0, 0, 0.1);
            }}
            QProgressBar {{
                background-color: rgba(0,0,0,0.05);
                border-radius: 4px;
                text-align: center;
                border: none;
                height: 6px;
                color: transparent;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
            }}
            /* Enhanced Slider Styling */
            QSlider::groove:horizontal {{
                border: 1px solid #e0e0e0;
                background: #f5f5f5;
                height: 6px;
                border-radius: 3px;
                margin: 0px;
            }}
            QSlider::sub-page:horizontal {{
                background: {ThemeManager.COLOR_ACCENT};
                border-radius: 3px;
            }}
            QSlider::add-page:horizontal {{
                background: #e0e0e0;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: white;
                border: 1px solid #d0d0d0;
                width: 20px;
                height: 20px;
                margin: -7px 0; /* Center handle verticaly */
                border-radius: 10px;
                margin-right: -10px; /* Fix cut-off */
                margin-left: -10px;
            }}
            QSlider::handle:horizontal:hover {{
                border-color: {ThemeManager.COLOR_ACCENT};
                background: #fff;
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
        
        # > Sliders
        sliders_frame = QFrame()
        sliders_frame.setStyleSheet("background: rgba(0,0,0,0.03); border-radius: 12px; padding: 10px;")
        sliders_layout = QVBoxLayout(sliders_frame)
        sliders_layout.setSpacing(10)
        # Brightness
        b_row = QHBoxLayout()
        b_row.addWidget(QLabel("🔆"))
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(0, 255)
        self.bright_slider.setValue(128)
        self.bright_slider.sliderReleased.connect(self.on_brightness_change)
        b_row.addWidget(self.bright_slider)
        sliders_layout.addLayout(b_row)
        # Volume
        v_row = QHBoxLayout()
        v_row.addWidget(QLabel("🔊"))
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 15)
        self.vol_slider.setValue(8)
        self.vol_slider.sliderReleased.connect(self.on_volume_change)
        v_row.addWidget(self.vol_slider)
        sliders_layout.addLayout(v_row)
        scroll_l.addWidget(sliders_frame)
        
        # > Quick Toggles
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
        scroll_l.addLayout(grid)
        
        scroll_l.addStretch()
        scroll.setWidget(scroll_content)
        ctrl_layout.addWidget(scroll)
        
        self.stack.addWidget(control_page)
        
        # === TAB 2: Notifications ===
        notif_page = QWidget()
        notif_layout = QVBoxLayout(notif_page)
        notif_layout.setContentsMargins(0, 5, 0, 0)
        
        # Clear All Btn
        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_btn = QPushButton("Xóa tất cả")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; border: none; font-weight: 600;")
        clear_btn.clicked.connect(self.clear_notifications)
        clear_row.addWidget(clear_btn)
        notif_layout.addLayout(clear_row)
        
        self.notif_list = QListWidget()
        self.notif_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; }}
            QListWidget::item {{
                background: white; border-radius: 8px; padding: 2px;
                margin-bottom: 6px; border: 1px solid rgba(0,0,0,0.05);
            }}
        """)
        notif_layout.addWidget(self.notif_list)
        
        self.stack.addWidget(notif_page)
        
    def handle_close(self):
        # If in Notification tab (1), switch back to Control (0)
        if self.stack.currentIndex() == 1:
            self.switch_tab(0)
        else:
            self.toggle()
            
    def switch_tab(self, id):
        self.stack.setCurrentIndex(id)
        # Update Title based on mode
        if id == 0:
            self.title.setText("Trung tâm Điều khiển")
        else:
            self.title.setText("Thông báo")

    def create_status_card(self, title, icon, value, color):
        card = QFrame()
        card.setFixedHeight(94) # Fixed height
        # Fix: QLabel inherits QFrame, so we must explicitly remove border from children
        card.setStyleSheet("""
            .QFrame {
                background: white; 
                border-radius: 16px; 
                border: 1px solid #f0f0f0;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        # Light shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0,0,0,10))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        l = QVBoxLayout(card)
        l.setSpacing(4)
        l.setContentsMargins(12, 12, 12, 12)
        
        top = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 20px;")
        
        l_info = QVBoxLayout()
        l_info.setSpacing(0)
        lbl_val = QLabel(value)
        lbl_val.setObjectName("value_label")
        lbl_val.setStyleSheet(f"font-weight: 800; font-size: 14px; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 11px; color: #999; font-weight: 600; text-transform: uppercase;")
        l_info.addWidget(lbl_title)
        l_info.addWidget(lbl_val)
        
        top.addWidget(lbl_icon)
        top.addSpacing(10)
        top.addLayout(l_info)
        top.addStretch()
        l.addLayout(top)
        
        pbar = QProgressBar()
        pbar.setTextVisible(False)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet(f"QProgressBar {{ background: #f0f0f0; border-radius: 3px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}")
        l.addWidget(pbar)
        
        return card

    def create_big_toggle(self, grid, text, icon, color, callback, r, c):
        btn = QPushButton()
        btn.setFixedSize(140, 60)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        l = QHBoxLayout(btn)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 20px; background: transparent;")
        lbl_text = QLabel(text)
        lbl_text.setStyleSheet("font-size: 13px; font-weight: 600; color: white;")
        
        l.addWidget(lbl_icon)
        l.addWidget(lbl_text)
        l.addStretch()
        
        btn.setStyleSheet(f"background-color: {color}; border-radius: 10px; border: none;")
        grid.addWidget(btn, r, c, 1, 2)

    def create_toggle_btn(self, grid, text, icon, callback, r, c, checkable=False):
        btn = QPushButton(icon)
        btn.setFixedSize(65, 65)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(checkable)
        btn.setToolTip(text)
        btn.clicked.connect(callback)
        
        style = f"""
            QPushButton {{
                background-color: rgba(0,0,0,0.05); border-radius: 14px; border: none; font-size: 24px;
            }}
            QPushButton:hover {{ background-color: rgba(0,0,0,0.1); }}
            QPushButton:checked {{ background-color: {ThemeManager.COLOR_ACCENT}; color: white; }}
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
        """Fetch and update system info - Optimized"""
        if not self.adb.current_device: return
        
        # Battery
        try:
            info = self.adb.get_battery_info()
            level = info.get('level', 0)
            self.batt_bar.setValue(level)
            self.batt_card.findChild(QLabel, "value_label").setText(f"{level}%")
        except: pass
        
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
        except: pass

    # --- Actions ---
    def on_brightness_change(self):
        val = self.bright_slider.value()
        self.adb.set_brightness(val)
        
    def on_volume_change(self):
        val = self.vol_slider.value()
        self.adb.set_volume(val)
        
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

    def on_mirror(self):
        # Toggle Mirror
        if self.scrcpy_process and self.scrcpy_process.state() == QProcess.Running:
            self.stop_mirroring()
        else:
            self.start_mirroring()
            # Close center to see the mirror
            self.toggle()

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
        
        # Start Process
        self.scrcpy_process = QProcess()
        self.scrcpy_process.finished.connect(self.on_mirror_finished)
        
        # Env setup for ADB finding
        scrcpy_dir = os.path.dirname(scrcpy_path)
        self.scrcpy_process.setWorkingDirectory(scrcpy_dir)
        
        self.scrcpy_process.start(scrcpy_path, args)
        if self.scrcpy_process.waitForStarted(1000):
            self.add_notification("Mirror", "Đã bắt đầu phản chiếu (Optimized)", "success")
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
        self.toggle()
        
    def on_screenshot(self):
        self.adb.screenshot("recents_screenshot.png")
        self.add_notification("Screenshot", "Đã chụp màn hình", "success")

    def add_notification(self, title, message, type="info"):
        try:
            item = QListWidgetItem()
            widget = QWidget()
            l = QVBoxLayout(widget)
            l.setContentsMargins(10, 8, 10, 8)
            l.setSpacing(2)
            
            t = QLabel(title)
            col = ThemeManager.COLOR_TEXT_PRIMARY
            if type == "error": col = ThemeManager.COLOR_DANGER
            elif type == "success": col = ThemeManager.COLOR_SUCCESS
            
            # Add timestamp
            import datetime
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
            t.setText(f"{title}  <span style='color:#999; font-weight:normal; font-size:10px;'>{time_str}</span>")
            t.setTextFormat(Qt.RichText)
            
            t.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {col};")
            
            m = QLabel(message)
            m.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 11px;")
            m.setWordWrap(True)
            
            l.addWidget(t)
            l.addWidget(m)
            
            widget.adjustSize()
            item.setSizeHint(QSize(self.notif_list.width() - 25, widget.sizeHint().height() + 10))
            
            self.notif_list.addItem(item)
            self.notif_list.setItemWidget(item, widget)
            
            self.notif_list.scrollToBottom()

            # [AUTO-OPEN] Automatically open notification tab on new message
            # Check if C++ object is still valid
            try:
                if not self.isVisible():
                    self.toggle(tab_index=1)
                elif self.stack.currentIndex() != 1:
                    self.switch_tab(1)
            except RuntimeError:
                pass # Object deleted
            except AttributeError:
                pass 
                
        except Exception as e:
            # print(f"Error adding notification: {e}") # Silent fail
            pass

    def clear_notifications(self):
        self.notif_list.clear()

    def eventFilter(self, obj, event):
        # Allow MainWindow to use this filter if needed, but logic is mainly in MainWindow
        return super().eventFilter(obj, event)
