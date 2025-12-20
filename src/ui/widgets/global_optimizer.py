# src/ui/widgets/global_optimizer.py
"""
Global Optimizer Widget (Unified)
Integrates General Tweaks, Xiaomi Specifics, and Fastboot Tools into a clear model.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QScrollArea, QCheckBox, QLineEdit, QGridLayout,
    QProgressBar, QMessageBox, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon
from src.ui.theme_manager import ThemeManager
from src.core.optimization_manager import OptimizationManager

# Import sub-modules for integration
try:
    from src.ui.widgets.xiaomi_optimizer import XiaomiOptimizerWidget
    from src.ui.widgets.fastboot_toolbox import FastbootToolboxWidget
except ImportError:
    # Fallback or placeholder if circular import issues (though unlikely here)
    XiaomiOptimizerWidget = None
    FastbootToolboxWidget = None

class OptimizerThread(QThread):
    progress = Signal(str, int)  # msg, percent
    finished_all = Signal()
    
    def __init__(self, manager, tasks):
        super().__init__()
        self.manager = manager
        self.tasks = tasks # List of (func_name, args, description)
        
    def run(self):
        total = len(self.tasks)
        for i, task in enumerate(self.tasks):
            t_func, t_args, t_desc = task
            
            # percent calculation
            pct = int(((i) / total) * 100)
            self.progress.emit(f"Đang chạy: {t_desc}...", pct)
            
            try:
                # Execute function from manager or callable
                if callable(t_func):
                    t_func()
                else:
                    # It's a method name on manager
                    if hasattr(self.manager, t_func):
                        method = getattr(self.manager, t_func)
                        if t_args is not None:
                            if isinstance(t_args, tuple):
                                method(*t_args)
                            else:
                                method(t_args)
                        else:
                            method()
                    elif hasattr(self.manager.adb, t_func):
                        # Fallback to direct ADB access for things not yet in manager
                        method = getattr(self.manager.adb, t_func)
                        if t_args is not None:
                            if isinstance(t_args, tuple):
                                method(*t_args)
                            else:
                                method(t_args)
                        else:
                            method()
                    
            except Exception as e:
                print(f"Error in task {t_desc}: {e}")
            
            # Update complete for this step
            pct = int(((i + 1) / total) * 100)
            self.progress.emit(f"Hoàn tất: {t_desc}", pct)
                
        self.finished_all.emit()

class GeneralTweaksWidget(QWidget):
    """
    Redesigned 'Global Optimizer' with Card-based UI.
    """
    def __init__(self, adb_manager, optimization_manager):
        super().__init__()
        self.adb = adb_manager
        self.opt_manager = optimization_manager
        self.toggles = {} 
        self.inputs = {}
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                border: none;
                background: rgba(0,0,0,0.03);
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.15);
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        
        container = QWidget()
        container.setStyleSheet(f"background-color: transparent;")
        self.c_layout = QVBoxLayout(container)
        self.c_layout.setContentsMargins(10, 10, 10, 20)
        self.c_layout.setSpacing(20)
        
        # Grid for Cards (2 columns)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(20)
        
        # --- Card 1: Performance & Cleaning ---
        card_opt_frame, card_opt_content = self.create_card("🚀 Tối Ưu & Dọn Dẹp")
        l_opt = QVBoxLayout(card_opt_content)
        l_opt.setSpacing(12)
        
        self.add_toggle(l_opt, "opt_battery", "Tối Ưu Hóa Pin (Quicken)", "🔋")
        self.add_toggle(l_opt, "opt_speed", "Tăng Tốc Mở App (Speed)", "🚀")
        self.add_toggle(l_opt, "clean_tele", "Dọn Rác Telegram/Nekogram", "🧹")
        self.add_toggle(l_opt, "clean_cache", "Dọn Cache Toàn Bộ App", "🗑️")
        self.add_toggle(l_opt, "clean_dex", "Dọn Tệp Rác (.dex)", "📄")
        
        cards_grid.addWidget(card_opt_frame, 0, 0)
        
        # --- Card 2: ART Runtime ---
        card_art_frame, card_art_content = self.create_card("🤖 ART Runtime")
        l_art = QVBoxLayout(card_art_content)
        l_art.setSpacing(12)
        
        self.add_toggle(l_art, "art_daily", "Tối Ưu Hàng Ngày (Speed)", "📅")
        self.add_toggle(l_art, "art_boot", "Tối Ưu Khởi Động (Verify)", "🔌")
        self.add_toggle(l_art, "art_ota", "Tối Ưu Sau OTA (Bg-Dexopt)", "🆙")
        self.add_toggle(l_art, "multi_task", "Tăng Đa Nhiệm (Purgeable)", "⚡")
        l_art.addStretch() # Align top
        
        cards_grid.addWidget(card_art_frame, 0, 1)
        
        self.c_layout.addLayout(cards_grid)
        
        # --- Card 3: Display Tweaks (Full Width) ---
        card_disp_frame, card_disp_content = self.create_card("✨ Tinh Chỉnh Hiển Thị")
        l_disp = QGridLayout(card_disp_content)
        l_disp.setSpacing(15)
        
        # Col 1
        self.add_input_toggle(l_disp, 0, 0, "anim_duration", "Độ Mượt (Duration)", "0.65", "⏱️")
        self.add_input_toggle(l_disp, 1, 0, "window_scale", "Cửa Sổ (Window)", "0.95", "🔲")
        self.add_input_toggle(l_disp, 2, 0, "trans_scale", "Chuyển Tiếp (Trans)", "0.95", "↔️")
        
        # Col 2
        self.add_input_toggle(l_disp, 0, 1, "anim_scale", "Hiệu Ứng (Animator)", "0.95", "🏃")
        self.add_input_toggle(l_disp, 1, 1, "long_press", "Chờ Nhấn Giữ (ms)", "400", "👆")
        
        self.c_layout.addWidget(card_disp_frame)
        
        # --- Card 4: System & Other ---
        card_sys_frame, card_sys_content = self.create_card("🛠️ Hệ Thống & Khác")
        l_sys = QHBoxLayout(card_sys_content)
        l_sys.setSpacing(20)
        
        # Left: Whitelist
        v_sys_l = QVBoxLayout()
        self.add_input_toggle_v(v_sys_l, "notify_opt", "Whitelist Thông Báo (Package)", "com.facebook.orca,com.zing.zalo", "🔔")
        l_sys.addLayout(v_sys_l, 1)
        
        # Right: Toggles
        v_sys_r = QVBoxLayout()
        self.add_toggle(v_sys_r, "opt_sysui", "Tối Ưu SystemUI (Compile)", "⚙️")
        self.add_toggle(v_sys_r, "restart", "Tự Động Khởi Động Lại", "🔄")
        l_sys.addLayout(v_sys_r, 1)
        
        self.c_layout.addWidget(card_sys_frame)
        
        self.c_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Action Bar (Pinned Bottom)
        self.setup_action_bar(main_layout)

    def create_card(self, title):
        card = QFrame()
        card.setObjectName("Card")
        # Glassmorphism Card Style
        card.setStyleSheet(f"""
            #Card {{
                background-color: {ThemeManager.COLOR_GLASS_WHITE};
                border: 1px solid rgba(255, 255, 255, 0.6);
                border-radius: 16px;
            }}
        """)
        
        # Title wrapper to add header
        wrapper_layout = QVBoxLayout(card)
        wrapper_layout.setContentsMargins(0,0,0,0)
        
        # Header
        header = QLabel(title)
        header.setStyleSheet(f"""
            background-color: rgba(0,0,0,0.03); 
            color: {ThemeManager.COLOR_TEXT_PRIMARY};
            font-weight: bold;
            font-size: 14px;
            padding: 10px 15px;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        """)
        wrapper_layout.addWidget(header)
        
        # Content placeholder
        content_widget = QWidget()
        wrapper_layout.addWidget(content_widget)
        
        return card, content_widget # Return frame AND content

    def setup_action_bar(self, parent_layout):
        action_bar = QFrame()
        action_bar.setStyleSheet(f"""
            background: {ThemeManager.COLOR_GLASS_WHITE}; 
            border: 1px solid rgba(255,255,255,0.5);
            border-radius: 16px;
        """)
        ab_layout = QVBoxLayout(action_bar)
        ab_layout.setContentsMargins(20, 15, 20, 15)
        
        # Row 1: Status & Button
        row1 = QHBoxLayout()
        
        status_vBox = QVBoxLayout()
        self.status_lbl = QLabel("Sẵn sàng")
        self.status_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-weight: 600; font-size: 14px;")
        
        self.sub_status_lbl = QLabel("Chọn các mục cần tối ưu và nhấn Thực Hiện")
        self.sub_status_lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_SECONDARY}; font-size: 12px;")
        
        status_vBox.addWidget(self.status_lbl)
        status_vBox.addWidget(self.sub_status_lbl)
        row1.addLayout(status_vBox)
        
        row1.addStretch()
        
        self.apply_btn = QPushButton("🚀 Thực Hiện")
        self.apply_btn.setStyleSheet(ThemeManager.get_button_style("primary") + "padding: 8px 30px; font-size: 14px; font-weight: bold;")
        self.apply_btn.setCursor(Qt.PointingHandCursor)
        self.apply_btn.clicked.connect(self.run_process)
        row1.addWidget(self.apply_btn)
        
        ab_layout.addLayout(row1)
        
        # Row 2: Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: rgba(0,0,0,0.05);
                border-radius: 3px;
                height: 6px;
                margin-top: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeManager.COLOR_ACCENT};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.hide()
        ab_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(action_bar)

    def add_toggle(self, layout, key, text, icon_char=""):
        container = QWidget()
        l = QHBoxLayout(container)
        l.setContentsMargins(5, 2, 5, 2)
        
        lbl = QLabel(f"{icon_char}  {text}")
        lbl.setStyleSheet(f"color: {ThemeManager.COLOR_TEXT_PRIMARY}; font-size: 13px;")
        
        chk = QCheckBox()
        chk.setCursor(Qt.PointingHandCursor)
        chk.setStyleSheet(self.get_switch_style())
        self.toggles[key] = chk
        
        l.addWidget(lbl)
        l.addStretch()
        l.addWidget(chk)
        
        layout.addWidget(container)
        
    def add_input_toggle(self, grid_layout, row, col, key, text, placeholder, icon_char=""):
        container = QFrame()
        container.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(container)
        l.setContentsMargins(10, 8, 10, 8)
        
        # Text + Input
        v = QVBoxLayout()
        v.setSpacing(5)
        lbl = QLabel(f"{icon_char} {text}")
        lbl.setStyleSheet(f"font-weight: 500; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setText(placeholder)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background: {ThemeManager.COLOR_GLASS_CARD}; 
                border: 1px solid {ThemeManager.COLOR_BORDER}; 
                border-radius: 6px; 
                padding: 4px 8px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border: 1px solid {ThemeManager.COLOR_ACCENT}; }}
        """)
        self.inputs[key] = inp
        
        v.addWidget(lbl)
        v.addWidget(inp)
        
        chk = QCheckBox()
        chk.setCursor(Qt.PointingHandCursor)
        chk.setStyleSheet(self.get_switch_style())
        self.toggles[key] = chk
        
        l.addLayout(v)
        l.addStretch()
        l.addWidget(chk)
        
        grid_layout.addWidget(container, row, col)

    def add_input_toggle_v(self, layout, key, text, placeholder, icon_char=""):
        # Vertical version for non-grid layouts
        container = QFrame()
        container.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(container)
        l.setContentsMargins(10, 8, 10, 8)
        
        v = QVBoxLayout()
        v.setSpacing(5)
        lbl = QLabel(f"{icon_char} {text}")
        lbl.setStyleSheet(f"font-weight: 500; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setText(placeholder)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background: {ThemeManager.COLOR_GLASS_CARD}; 
                border: 1px solid {ThemeManager.COLOR_BORDER}; 
                border-radius: 6px; 
                padding: 4px 8px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border: 1px solid {ThemeManager.COLOR_ACCENT}; }}
        """)
        self.inputs[key] = inp
        
        v.addWidget(lbl)
        v.addWidget(inp)
        
        chk = QCheckBox()
        chk.setCursor(Qt.PointingHandCursor)
        chk.setStyleSheet(self.get_switch_style())
        self.toggles[key] = chk
        
        l.addLayout(v)
        l.addStretch()
        l.addWidget(chk)
        layout.addWidget(container)

    def get_switch_style(self):
        return f"""
            QCheckBox::indicator {{ width: 40px; height: 22px; }}
            QCheckBox::indicator:unchecked {{
                image: none; background: #E0E0E0; border-radius: 11px;
                border: 2px solid white;
            }}
            QCheckBox::indicator:checked {{
                image: none; background: {ThemeManager.COLOR_ACCENT}; border-radius: 11px;
                border: 2px solid white;
            }}
        """

    def is_checked(self, key):
        return self.toggles[key].isChecked()
        
    def get_input(self, key):
        return self.inputs[key].text()

    def run_process(self):
        tasks = []
        
        # 1. Opt & Clean
        if self.is_checked("opt_battery"):
            tasks.append(("optimize_battery", "quicken", "Tối ưu hóa Pin"))
        if self.is_checked("opt_speed"):
            tasks.append(("optimize_performance", None, "Tối ưu hóa Tốc độ"))
        if self.is_checked("clean_tele"):
            tasks.append(("clean_social_app_cache", None, "Dọn dẹp Telegram/Nekogram"))
        if self.is_checked("clean_cache"):
            tasks.append(("clean_app_cache", None, "Dọn dẹp Cache ứng dụng"))
        if self.is_checked("clean_dex"):
            tasks.append(("clean_obsolete_dex", None, "Dọn dẹp tệp rác Dex"))
            
        # ART
        if self.is_checked("art_daily"):
            tasks.append(("compile_apps", ("speed-profile",), "Tối ưu ART - Hàng ngày"))
        if self.is_checked("art_boot"):
            tasks.append(("compile_apps", ("verify",), "Tối ưu ART - Khởi động"))
        if self.is_checked("art_ota"):
            tasks.append(("compile_apps", ("bg-dexopt-job",), "Tối ưu ART - Sau OTA"))
            
        if self.is_checked("multi_task"):
            tasks.append(("set_system_property", ("persist.sys.purgeable_assets", "1"), "Tăng khả năng đa nhiệm"))
            
        # Tweaks
        if self.is_checked("anim_duration"):
            val = self.get_input("anim_duration")
            tasks.append(("set_system_setting", ("global", "animator_duration_scale", val), "Settings: Animator Duration"))
            
        if self.is_checked("window_scale"):
            val = self.get_input("window_scale")
            tasks.append(("set_system_setting", ("global", "window_animation_scale", val), "Settings: Window Scale"))
            
        if self.is_checked("trans_scale"):
            val = self.get_input("trans_scale")
            tasks.append(("set_system_setting", ("global", "transition_animation_scale", val), "Settings: Transition Scale"))

        if self.is_checked("anim_scale"):
             val = self.get_input("anim_scale")
             tasks.append(("set_system_setting", ("global", "animator_duration_scale", val), "Settings: Animator Scale"))

        if self.is_checked("long_press"):
            val = self.get_input("long_press")
            tasks.append(("set_system_setting", ("secure", "long_press_timeout", val), "Settings: Long Press Timeout"))
            
        # Other
        if self.is_checked("notify_opt"):
            val = self.get_input("notify_opt")
            tasks.append(("optimize_notifications", val, "Tối ưu hóa Thông báo"))
            
        if self.is_checked("opt_sysui"):
            tasks.append(("shell", ("cmd package compile -m speed com.android.systemui", 600), "Tối ưu SystemUI"))
            
        if self.is_checked("restart"):
            tasks.append(("reboot", None, "Khởi động lại thiết bị"))

        if not tasks:
            QMessageBox.warning(self, "Chưa chọn mục nào", "Vui lòng chọn ít nhất một tác vụ để thực hiện!")
            return
            
        self.apply_btn.setEnabled(False)
        self.apply_btn.setText("⏳ Đang xử lý...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.status_lbl.setText(f"Đang xử lý {len(tasks)} tác vụ...")
        self.sub_status_lbl.setText("Vui lòng không ngắt kết nối...")
        
        self.worker = OptimizerThread(self.opt_manager, tasks)
        self.worker.progress.connect(self.update_status)
        self.worker.finished_all.connect(self.on_process_done)
        self.worker.start()

    def update_status(self, msg, pct):
        self.status_lbl.setText(msg)
        self.progress_bar.setValue(pct)
        
    def on_process_done(self):
        self.apply_btn.setEnabled(True)
        self.apply_btn.setText("🚀 Thực Hiện")
        self.status_lbl.setText("✅ Hoàn tất tất cả tác vụ!")
        self.sub_status_lbl.setText("Đã tối ưu hóa thành công.")
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Thành công", "Đã thực hiện xong các tối ưu hóa đã chọn!")
        QTimer.singleShot(3000, self.progress_bar.hide) # Clean up after 3s


class GlobalOptimizerWidget(QWidget):
    """
    Unified Container for all Optimization Features.
    Structure:
    - Tab 1: ADB (Power on)
      - General (Checklist)
      - Xiaomi (Cards)
    - Tab 2: Fastboot (Bootloader)
      - Tools
    """
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.opt_manager = OptimizationManager(adb_manager)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        # Create Main Tab Widget
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 6px;
                background: white;
            }
            QTabBar::tab {
                min-width: 150px;
                padding: 10px;
                font-weight: bold;
                color: #555;
            }
            QTabBar::tab:selected {
                color: #007bff;
                background: #f8f9fa;
                border-bottom: 2px solid #007bff;
            }
        """)
        
        # === TAB 1: ADB Optimization ===
        self.adb_tab_widget = QWidget()
        self.setup_adb_tab(self.adb_tab_widget)
        self.main_tabs.addTab(self.adb_tab_widget, "📱 ADB Optimization")
        
        # === TAB 2: Fastboot Tools ===
        self.fastboot_tab_widget = QWidget()
        self.setup_fastboot_tab(self.fastboot_tab_widget)
        self.main_tabs.addTab(self.fastboot_tab_widget, "🔌 Fastboot & Repair")
        
        layout.addWidget(self.main_tabs)
        
    def setup_adb_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Inner tabs for clearer organization
        adb_subtabs = QTabWidget()
        
        # 1. General Tweaks (The original GlobalOptimizer logic)
        self.general_tweaks = GeneralTweaksWidget(self.adb, self.opt_manager)
        adb_subtabs.addTab(self.general_tweaks, "Tinh Chỉnh Chung")
        
        # 2. Xiaomi Extensions (The XiaomiOptimizer cards)
        if XiaomiOptimizerWidget:
            self.xiaomi_tweaks = XiaomiOptimizerWidget(self.adb)
            adb_subtabs.addTab(self.xiaomi_tweaks, "Tiện Ích Xiaomi")
        else:
            adb_subtabs.addTab(QLabel("Không thể tải Xiaomi Module"), "Lỗi")
            
        layout.addWidget(adb_subtabs)
        
    def setup_fastboot_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if FastbootToolboxWidget:
            self.fastboot_tools = FastbootToolboxWidget(self.adb)
            layout.addWidget(self.fastboot_tools)
        else:
            layout.addWidget(QLabel("Không thể tải Fastboot Module"))
