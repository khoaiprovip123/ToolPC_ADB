import re
from typing import List, Dict, Callable
from PySide6.QtCore import QObject, Signal, QThread

class OptimizationWorker(QThread):
    """Background worker for optimization tasks"""
    progress = Signal(str, int)  # message, percent
    finished = Signal()
    error = Signal(str)

    def __init__(self, tasks: List[Callable], parent=None):
        super().__init__(parent)
        self.tasks = tasks

    def run(self):
        total = len(self.tasks)
        for i, task in enumerate(self.tasks):
            try:
                # Calculate progress
                pct = int((i / total) * 100)
                
                # Execute task (which should emit its own status updates if complex, 
                # or we just rely on the fact that it's running)
                # We expect the task to return a description or we wrap it in a tuple
                if isinstance(task, tuple):
                    func, desc = task
                    self.progress.emit(f"Đang thực hiện: {desc}...", pct)
                    func()
                else:
                    self.progress.emit(f"Đang xử lý bước {i+1}...", pct)
                    task()
                    
            except Exception as e:
                self.error.emit(str(e))
                
        self.progress.emit("Hoàn tất!", 100)
        self.finished.emit()

class OptimizationManager:
    """
    Central Logic for System Optimizations (ADB & Fastboot wrappers)
    Separates logic from UI.
    """
    def __init__(self, adb_manager):
        self.adb = adb_manager

    # ================== General ADB Optimizations ==================
    
    def set_animation_scale(self, scale: float):
        """Set all animation scales"""
        self.adb.shell(f"settings put global window_animation_scale {scale}")
        self.adb.shell(f"settings put global transition_animation_scale {scale}")
        self.adb.shell(f"settings put global animator_duration_scale {scale}")

    def optimize_battery(self, mode="quicken"):
        """Compile apps for battery/balanced optimization"""
        # modes: quicken, speed, space
        self.adb.compile_apps(mode)

    def optimize_performance(self):
        """Compile apps for max performance"""
        self.adb.compile_apps("speed")

    def clean_junk_files(self):
        """Clean standard cache and tmp files"""
        self.adb.clean_app_cache()
        self.adb.clean_obsolete_dex()
        
    def clean_social_app_cache(self):
        """Clean heavy social media caches"""
        self.adb.clean_messenger_data()

    def set_screen_timeout(self, ms: int):
        self.adb.set_system_setting("system", "screen_off_timeout", str(ms))

    # ================== Xiaomi Specific ==================

    def disable_miui_ads(self):
        """Disable standard MSA and Analytics"""
        self.adb.disable_msa()
        self.adb.disable_analytics()
        # Add more ad packages
        ads = [
            "com.miui.systemadsolution",
            "com.xiaomi.joyose", 
            "com.google.android.gms.location.history"
        ]
        for pkg in ads:
            self.adb.disable_package(pkg)

    def fix_eu_region(self):
        """Fix region issues on EU ROMs"""
        self.adb.set_prop("persist.sys.country", "VN")
        self.adb.set_prop("ro.product.locale", "vi-VN") 
        self.adb.set_system_setting("system", "time_12_24", "24")

    def enable_hyperos_stacked_recent(self):
        """Enable HyperOS 3 Stacked Recent View (iOS Style)"""
        # Requires HyperOS Launcher RELEASE-6.01.03.1924+
        self.adb.shell("settings put global task_stack_view_layout_style 2")

    # ================== Fastboot Helper ==================
    
    def fastboot_format_data(self):
        """Format data in fastboot (wipes everything)"""
        return self.adb.fastboot_command("erase userdata") + "\n" + self.adb.fastboot_command("erase cache")

    def fastboot_unlock_frp(self):
        return self.adb.fastboot_unlock_frp()
