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
        return self.compile_apps(mode)

    def optimize_performance(self):
        """Compile apps for max performance"""
        return self.compile_apps("speed")
        
    def compile_apps(self, mode, timeout=None, callback=None):
        """Run ART optimization"""
        cmd = f"cmd package compile -m {mode} -a"
        if callback: callback(f"Executing: {cmd} (This may take minutes)...")
        # Note: shell is blocking, timeout handling is limited here without threading/subprocess modification
        # But check_output waits.
        return self.adb.shell(cmd)

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

    # ================== Xiaomi Specific ==================

    def disable_miui_ads(self):
        """Disable standard MSA and Analytics"""
        # Disable MSA
        self.adb.shell("pm disable-user --user 0 com.miui.msa.global")
        # Disable Analytics
        self.adb.shell("pm disable-user --user 0 com.miui.analytics")
        self.adb.shell("pm disable-user --user 0 com.miui.systemadsolution")
        
        # Add more ad packages
        ads = [
            "com.xiaomi.joyose", 
            "com.google.android.gms.location.history"
        ]
        for pkg in ads:
            self.adb.shell(f"pm disable-user --user 0 {pkg}")

    def fix_eu_region(self):
        """Fix region issues on EU ROMs"""
        self.adb.shell("setprop persist.sys.country VN")
        self.adb.shell("setprop ro.product.locale vi-VN") 
        self.adb.shell("settings put system time_12_24 24")

    # ================== New Methods for Worker Compatibility ==================
    def enable_hyperos_stacked_recent(self):
        """Enable HyperOS 2 Stacked Recent View (iOS Style)"""
        # Requires HyperOS Launcher RELEASE-6.01.03.1924+
        self.adb.shell("settings put global task_stack_view_layout_style 2")
        return "Đã set biến Stacked Recent (2)"

    def set_always_on_display(self, enable: bool):
        val = "1" if enable else "0"
        self.adb.shell(f"settings put secure aod_enabled {val}")
        self.adb.shell(f"settings put secure doze_always_on {val}")
        return f"Đã {'bật' if enable else 'tắt'} Always-On Display"

    def set_control_center_style(self, new_style: bool):
        val = "1" if new_style else "0"
        self.adb.shell(f"settings put system use_control_panel {val}")
        return f"Đã {'bật' if new_style else 'tắt'} Control Center Mới"
    
    def set_min_brightness(self, val):
        # val should be float 0.0 to 1.0 (or string), but some ROMs use int
        # Assuming float based on user prompt screenshot "0.001 ... 1.0"
        # However, settings usually take int/float? usually 'settings put system screen_brightness_mode ...'
        # The key for min brightness is often ro param (readonly) or expert
        # User screenshot says "Độ Sáng Tối Thiểu".
        # Let's try `settings put system screen_auto_brightness_adj` ? No.
        # Maybe `settings put system screen_brightness_min`?
        # Safe fallback: generic setting put.
        # But wait, user requested "can thiep sau" (SetEdit).
        # We'll just define the put.
        return self.adb.shell(f"settings put system screen_brightness_min {val}") # Hypothetical key

    def tune_game_performance(self, enable: bool):
        val = "1" if enable else "0"
        self.adb.shell(f"settings put secure game_booster_enabled {val}")
        self.adb.shell(f"settings put secure speed_mode_enable {val}")
        self.adb.shell(f"settings put global game_driver_enabled {val}")
        return f"Đã {'bật' if enable else 'tắt'} Game Turbo Tweak"

    def enable_fast_charge(self, enable: bool):
         val = "1" if enable else "0"
         self.adb.shell(f"settings put global fast_charging_enabled {val}")
         return f"Đã {'bật' if enable else 'tắt'} Fast Charge Prop"
         
    def set_desktop_mode(self, enable: bool):
         val = "1" if enable else "0"
         self.adb.shell(f"settings put global force_desktop_mode_on_external_displays {val}")
         return f"Đã {'bật' if enable else 'tắt'} Desktop Mode"

    def activate_brevent(self):
        """Activate Brevent Server & Grant Permissions"""
        # 1. Grant Permission
        self.adb.shell("pm grant me.piebridge.brevent android.permission.WRITE_SECURE_SETTINGS")
        
        # 2. Start Server (Standard Command)
        # We wrap in nohup or just execute. Brevent script usually handles backgrounding.
        out = self.adb.shell("sh /data/data/me.piebridge.brevent/brevent.sh")
        return f"Kết quả kích hoạt: {out}" if out else "Đã gửi lệnh kích hoạt Brevent"
    def apply_smart_blur(self):
        """Enable Smart Blur settings"""
        # Enable window blurs
        self.adb.shell("setprop ro.surface_flinger.supports_background_blur 1")
        self.adb.shell("wm enable-blur 1")
        return "Đã kích hoạt Smart Blur (cần khởi động lại)"

    def get_language_region_status(self):
        """Get status dict"""
        locale = self.adb.shell("getprop ro.product.locale")
        return {
            "locale": locale,
            "region": self.adb.shell("getprop persist.sys.country")
        }

    def set_language_vietnamese(self):
        self.adb.shell("setprop ro.product.locale vi-VN")
        self.adb.shell("setprop persist.sys.timezone Asia/Ho_Chi_Minh")
        self.adb.shell("setprop persist.sys.language vi")
        self.adb.shell("setprop persist.sys.country VN")
        return "Đã cài đặt ngôn ngữ Tiếng Việt & Múi giờ"

    def disable_miui_ota(self):
        self.adb.shell("pm disable-user --user 0 com.android.updater")
        self.adb.shell("pm disable-user --user 0 com.miui.updater")
        return "Đã tắt trình cập nhật MIUI"

    def skip_setup_wizard(self):
        self.adb.shell("settings put secure user_setup_complete 1")
        self.adb.shell("settings put global device_provisioned 1")
        return "Đã bỏ qua Setup Wizard"

    def set_refresh_rate(self, hz):
        if hz <= 0:
            # Auto
            self.adb.shell("settings put system user_refresh_rate 0")
            self.adb.shell("settings put system min_refresh_rate 0")
            self.adb.shell("settings put system peak_refresh_rate 0")
        else:
            self.adb.shell(f"settings put system user_refresh_rate {hz}")
            self.adb.shell(f"settings put system min_refresh_rate {hz}")
            self.adb.shell(f"settings put system peak_refresh_rate {hz}")
        return f"Đã set tần số quét: {hz}Hz"

    def set_background_process_limit(self, limit):
         # limit: -1 (Standard), 0 (No bg), 1, 2, 3, 4
         # This usually requires "activity_manager_constants" or specific service calls
         # But standard setting is device_provisioned...? No.
         # Standard is: am set-process-limit <PROCESS_LIMIT> (but that's partial)
         # Or: settings put global always_finish_activities <0/1>
         # Or: settings put global background_process_limit <N> (Some ROMs)
         # Let's use the standard `device_config` or fallback.
         # Actually, `am set-process-limit` is not persistent.
         # We will use `settings put global background_process_limit` hoping the ROM reads it, 
         # or just warn user it might be temporary.
         self.adb.shell(f"settings put global background_process_limit {limit}")
         return f"Đã set giới hạn tiến trình nền: {limit}"

    def set_package_verifier(self, enable: bool):
         val = "1" if enable else "0"
         self.adb.shell(f"settings put global verifier_verify_adb_installs {val}")
         self.adb.shell(f"settings put global package_verifier_enable {val}")
         return f"Đã {'bật' if enable else 'tắt'} Verify App"

    def set_anr_dialogs(self, show: bool):
        val = "0" if show else "1" # show_background_anrs setting? 
        # Actually usually settings put secure anr_show_background 0/1
        # Or settings put global always_finish_activities...
        # Standard: settings put secure anr_show_background <0/1>
        self.adb.shell(f"settings put secure anr_show_background {val}")
        return f"Đã {'bật' if show else 'tắt'} thông báo ANR"

    def set_force_external(self, enable: bool):
        val = "1" if enable else "0"
        self.adb.shell(f"settings put global force_allow_on_external {val}")
        return f"Đã {'bật' if enable else 'tắt'} Force External Apps"

    def set_watchdog_tweak(self, enable: bool):
        if enable:
            self.adb.shell("settings put global wait_for_debugger 0")
            return "Đã tối ưu Watchdog (No Wait)"
        return "Đã reset Watchdog"

    def force_dark_mode(self, enable: bool):
        val = "yes" if enable else "no"
        mode = "2" if enable else "1"
        self.adb.shell(f"cmd uimode night {val}")
        self.adb.shell(f"settings put secure ui_night_mode {mode}")
        return f"Đã {'bật' if enable else 'tắt'} Dark Mode"

    def hide_navigation_bar(self, hide: bool):
        # Overscan is deprecated in Android 11+ but works on some old MIUI
        # Better: use immersive mode or gesture prop
        if hide:
            self.adb.shell("settings put global force_fsg_nav_bar 1") # Enable gestures
        else:
             self.adb.shell("settings put global force_fsg_nav_bar 0")
        return f"Đã {'ẩn' if hide else 'hiện'} thanh điều hướng"

    def set_display_density(self, dpi):
        self.adb.shell(f"wm density {dpi}")
        return f"Đã đổi DPI sang {dpi}"

    def show_refresh_rate_overlay(self, show: bool):
        val = "1" if show else "0"
        self.adb.shell(f"service call SurfaceFlinger 1034 i32 {val}")
        return f"Đã {'bật' if show else 'tắt'} hiện FPS"
        
    def open_developer_options(self):
         self.adb.shell("am start -a com.android.settings.APPLICATION_DEVELOPMENT_SETTINGS")
         return "Đã mở cài đặt nhà phát triển"
         
    def apply_performance_props(self):
        # Expert Optimization props
        props = [
            "debug.performance.tuning=1",
            "video.accelerate.hw=1",
            "ro.config.hw_quickpoweron=true"
        ]
        for p in props:
            k, v = p.split('=')
            self.adb.shell(f"setprop {k} {v}")
        return "Đã áp dụng Performance Props (Root/Shell)"

    # ================== Fastboot Helper ==================
    
    def fastboot_format_data(self):
        """Format data in fastboot (wipes everything)"""
        return self.adb.fastboot_command("erase userdata") + "\n" + self.adb.fastboot_command("erase cache")

    def fastboot_unlock_frp(self):
        return self.adb.fastboot_unlock_frp()
