from PySide6.QtCore import QThread, Signal
from src.core.optimization_manager import OptimizationManager

class OptimizationWorker(QThread):
    """Background worker for optimizations"""
    progress = Signal(str)
    result_ready = Signal(dict) # new signal for results
    error_occurred = Signal(str, str) # title, message
    finished = Signal()
    
    def __init__(self, adb, task_type):
        super().__init__()
        self.adb = adb
        self.opt = OptimizationManager(adb)
        self.task_type = task_type
        
    def run(self):
        # 1. Strict Device Check
        if not self.adb.is_online():
            self.error_occurred.emit("Lỗi Kết Nối", "Không tìm thấy thiết bị! Vui lòng kiểm tra kết nối USB/Wifi.")
            self.finished.emit()
            return
            
        try:
            if self.task_type == "full_scan":
                self.progress.emit("🔍 Đang quét hệ thống...")
                self.progress.emit("Đang xử lý System Ads & Analytics...")
                self.opt.disable_miui_ads()
                self.progress.emit("✅ Đã tắt Quảng cáo & Theo dõi")
                
                self.progress.emit("Đang tối ưu hiệu ứng...")
                self.opt.set_animation_scale(0.5)
                self.progress.emit("✅ Đã tăng tốc hiệu ứng")
                
            elif self.task_type == "animations":
                self.progress.emit("Đang tăng tốc hiệu ứng (0.5x)...")
                self.opt.set_animation_scale(0.5)
                self.progress.emit("✅ Đã đặt tỷ lệ hiệu ứng 0.5x")

            elif self.task_type == "set_vietnamese":
                self.progress.emit("🇻🇳 Đang cài đặt Tiếng Việt...")
                result = self.opt.set_language_vietnamese()
                self.progress.emit(f"ℹ️ {result}")
                
            elif self.task_type == "fix_eu_vn":
                self.progress.emit("🌍 Đang sửa lỗi vùng EU_VN...")
                self.opt.fix_eu_region()
                self.progress.emit("✅ Đã cập nhật Region VN & Time 24h")

            elif self.task_type == "check_status":
                self.progress.emit("🔍 Đang đọc thông số hệ thống...")
                status = self.opt.get_language_region_status()
                self.result_ready.emit(status)
                self.progress.emit("✅ Đã đọc dữ liệu xong")

            elif self.task_type == "smart_blur":
                self.progress.emit("✨ Đang phân tích cấu hình & kích hoạt Blur...")
                result = self.opt.apply_smart_blur()
                self.progress.emit(f"✅ {result}")

            elif self.task_type == "stacked_recent":
                self.progress.emit("📚 Đang kích hoạt giao diện Xếp chồng (HyperOS Native)...")
                self.opt.enable_hyperos_stacked_recent()
                
                self.progress.emit("🔄 Đang khởi động lại Launcher để áp dụng...")
                self.adb.shell("am force-stop com.miui.home")
                self.progress.emit("✅ Đã áp dụng giao diện Xếp chồng")

            elif self.task_type == "skip_setup":
                self.progress.emit("⏩ Đang bỏ qua Setup Wizard...")
                result = self.opt.skip_setup_wizard()
                self.progress.emit(result)

            elif self.task_type == "disable_ota":
                self.progress.emit("🛑 Đang chặn cập nhật hệ thống...")
                result = self.opt.disable_miui_ota()
                self.progress.emit(result)

            elif self.task_type == "force_refresh_rate":
                hz = 0
                if hasattr(self, 'refresh_rate'):
                    hz = self.refresh_rate
                label = "Mặc định (Auto)" if hz <= 0 else f"{hz}Hz"
                self.progress.emit(f"⚡ Đang áp dụng tần số quét {label}...")
                result = self.opt.set_refresh_rate(hz)
                self.progress.emit(result)

            elif self.task_type == "force_dark_mode_on":
                self.progress.emit("🌙 Đang bật Dark Mode hệ thống...")
                result = self.opt.force_dark_mode(True)
                self.progress.emit(result)

            elif self.task_type == "force_dark_mode_off":
                self.progress.emit("☀️ Đang tắt Dark Mode hệ thống...")
                result = self.opt.force_dark_mode(False)
                self.progress.emit(result)

            elif self.task_type == "hide_nav_on":
                self.progress.emit("↔️ Đang ẩn thanh điều hướng...")
                result = self.opt.hide_navigation_bar(True)
                self.progress.emit(result)

            elif self.task_type == "hide_nav_off":
                self.progress.emit("↔️ Đang hiện thanh điều hướng...")
                result = self.opt.hide_navigation_bar(False)
                self.progress.emit(result)

            elif self.task_type == "set_dpi":
                if hasattr(self, 'dpi_value'):
                    self.progress.emit(f"📱 Đang đổi DPI sang {self.dpi_value}...")
                    result = self.opt.set_display_density(self.dpi_value)
                    self.progress.emit(result)

            elif self.task_type == "show_fps_on":
                 self.progress.emit("📈 Đang bật bộ đếm FPS...")
                 result = self.opt.show_refresh_rate_overlay(True)
                 self.progress.emit(result)

            elif self.task_type == "show_fps_off":
                 self.progress.emit("📉 Đang tắt bộ đếm FPS...")
                 result = self.opt.show_refresh_rate_overlay(False)
                 self.progress.emit(result)

            elif self.task_type == "open_dev_options":
                 self.progress.emit("⚙️ Đang mở Cài đặt nhà phát triển...")
                 result = self.opt.open_developer_options()
                 self.progress.emit(result)

            elif self.task_type == "expert_optimize":
                 self.progress.emit("🚀 Đang kích hoạt Tối ưu hóa Chuyên sâu (HyperOS 3+)...")
                 result = self.opt.apply_performance_props()
                 self.progress.emit(result)
                 self.progress.emit("🔄 Đang tối ưu hóa Compiler (speed-profile)...")
                 result = self.opt.compile_apps("speed-profile", timeout=300, callback=self.progress.emit)
                 self.progress.emit(result)

            elif self.task_type == "art_tuning":
                 self.progress.emit("⚡ Đang tối ưu hóa ART (Full Speed)...")
                 result = self.opt.compile_apps("speed", timeout=600, callback=self.progress.emit)
                 self.progress.emit(result)

            elif self.task_type == "fix_social_notifications":
                 self.progress.emit("🔧 Đang xử lý thông báo & pin cho Social Apps...")
                 
                 targets = [
                    "app.revanced.android.gms", # MicroG
                    "com.facebook.katana",      # Facebook
                    "com.facebook.orca",        # Messenger
                    "com.zing.zalo"             # Zalo
                 ]
                 
                 count = 0
                 for pkg in targets:
                    try:
                         self.progress.emit(f"   ► Xử lý {pkg.split('.')[-1]}...")
                         # 1. Battery Optimization (Unlimited / Ignore)
                         self.adb.shell(f"dumpsys deviceidle whitelist +{pkg}", log_error=False)
                         
                         # 2. Allow Background Run
                         self.adb.shell(f"cmd appops set {pkg} RUN_IN_BACKGROUND allow", log_error=False)
                         self.adb.shell(f"cmd appops set {pkg} RUN_ANY_IN_BACKGROUND allow", log_error=False)
                         
                         # 3. Autostart (Xiaomi OpCode 10008)
                         self.adb.shell(f"cmd appops set {pkg} 10008 allow", log_error=False)
                         self.adb.shell(f"cmd appops set {pkg} START_FOREGROUND allow", log_error=False)
                         
                         # 4. Remove from App Standby
                         self.adb.shell(f"am set-inactive {pkg} false", log_error=False)
                         count += 1
                    except:
                         pass
                 
                 self.progress.emit(f"✅ Đã tối ưu hóa {count} ứng dụng!")
                 
            elif self.task_type == "remove_app_label":
                self.progress.emit("📝 Đang ẩn tên ứng dụng trên màn hình chính...")
                self.adb.shell("settings put system miui_home_no_word_model 1")
                self.adb.shell("am force-stop com.miui.home")
                self.progress.emit("✅ Đã ẩn tên ứng dụng (Launcher đã được khởi động lại)")

            elif self.task_type == "force_blur_level":
                self.progress.emit("💧 Đang ép buộc hiệu ứng Blur cao cấp (Device Level)...")
                # v:1 (High End), c:3 (Blur Level), g:3 (Graphics)
                self.adb.shell("settings put system deviceLevelList v:1,c:3,g:3")
                self.adb.shell("am force-stop com.miui.home")
                self.progress.emit("✅ Đã kích hoạt Blur Folder & Background")

            elif self.task_type == "unlock_super_wallpaper":
                self.progress.emit("🪐 Đang mở khóa Super Wallpaper...")
                self.adb.shell("settings put secure aod_using_super_wallpaper 1")
                self.progress.emit("✅ Đã mở khóa tính năng Super Wallpaper")

            elif self.task_type == "enable_call_recording":
                self.progress.emit("📞 Đang kích hoạt Ghi âm cuộc gọi...")
                # Try to uninstall the overlay that hides native features
                result = self.adb.shell("pm uninstall -k --user 0 com.android.phone.cust.overlay.miui")
                if "Success" in result:
                    self.progress.emit("✅ Đã gỡ bỏ giới hạn (Overlay Uninstalled)")
                else:
                    self.progress.emit(f"ℹ️ Kết quả: {result.strip()} (Có thể đã gỡ trước đó)")

            elif self.task_type == "activate_brevent":
                self.progress.emit("🛡️ Đang kích hoạt Brevent Server...")
                # Grant verify
                self.progress.emit("Đang cấp quyền WRITE_SECURE_SETTINGS...")
                result = self.opt.activate_brevent()
                self.progress.emit(f"Run script: {result}")
                self.progress.emit("✅ Hoàn tất kích hoạt. Vui lòng mở app Brevent!")
                
            # === System Tweaks ===
            elif self.task_type == "enable_aod":
                self.progress.emit("📱 Đang bật/tắt Always On Display...")
                result = self.opt.set_always_on_display(self.kwargs.get('enable', True))
                self.progress.emit(result)
            
            elif self.task_type == "new_cc":
                self.progress.emit("🎨 Đang thay đổi Control Center...")
                result = self.opt.set_control_center_style(self.kwargs.get('enable', True))
                self.progress.emit(result)

            elif self.task_type == "min_brightness":
                val = self.kwargs.get('value', '0.001')
                self.progress.emit(f"🔆 Đang set Min Brightness = {val}...")
                result = self.opt.set_min_brightness(val)
                self.progress.emit(f"✅ Đã set: {result}")

            elif self.task_type == "game_perf_tune":
                self.progress.emit("🚀 Đang tối ưu hóa Game...")
                result = self.opt.tune_game_performance(self.kwargs.get('enable', True))
                self.progress.emit(result)
                
            elif self.task_type == "fast_charge":
                self.progress.emit("⚡ Đang chỉnh prop sạc nhanh...")
                result = self.opt.enable_fast_charge(self.kwargs.get('enable', True))
                self.progress.emit(result)
                
            elif self.task_type == "desktop_mode":
                self.progress.emit("🖥️ Đang bật/tắt Desktop Mode...")
                result = self.opt.set_desktop_mode(self.kwargs.get('enable', True))
                self.progress.emit(result)
                
            elif self.task_type == "wm_size":
                size = self.kwargs.get('size', 'reset')
                self.progress.emit(f"📐 Đang set độ phân giải: {size}...")
                if size == 'reset':
                     self.adb.shell("wm size reset")
                     self.progress.emit("✅ Đã reset độ phân giải mặc định")
                else:
                     self.adb.shell(f"wm size {size}")
                     self.progress.emit(f"✅ Đã set {size}")

            elif self.task_type == "bg_limit":
                val = self.kwargs.get('limit', '-1')
                self.progress.emit(f"⚙️ Set giới hạn tiến trình nền: {val}...")
                result = self.opt.set_background_process_limit(val)
                self.progress.emit(result)

            elif self.task_type == "pkg_verifier":
                self.progress.emit("🛡️ Đang bật/tắt kiểm tra APK...")
                result = self.opt.set_package_verifier(self.kwargs.get('enable', True))
                self.progress.emit(result)

            elif self.task_type == "set_language_vn":
                self.progress.emit("🇻🇳 Đang cài đặt Tiếng Việt & Múi giờ...")
                result = self.opt.set_language_vietnamese()
                self.progress.emit(result)

            elif self.task_type == "disable_ota":
                self.progress.emit("🚫 Đang tắt cập nhật OTA...")
                result = self.opt.disable_miui_ota()
                self.progress.emit(result)

            elif self.task_type == "skip_setup":
                self.progress.emit("⏭️ Đang bỏ qua Setup Wizard...")
                result = self.opt.skip_setup_wizard()
                self.progress.emit(result)

            elif self.task_type == "force_refresh_rate":
                hz = self.kwargs.get('enable', 0)
                # If 'enable' is boolean from toggle_dialog, we need logic
                if isinstance(hz, bool):
                    hz = 120 if hz else 0
                self.progress.emit(f"🌫️ Đang set tần số quét: {hz}Hz...")
                result = self.opt.set_refresh_rate(hz)
                self.progress.emit(result)

            elif self.task_type == "smart_blur":
                self.progress.emit("💧 Đang kích hoạt Smart Blur...")
                result = self.opt.apply_smart_blur()
                self.progress.emit(result)

            elif self.task_type == "hide_nav":
                hide = self.kwargs.get('enable', True)
                self.progress.emit(f"📱 {'Ẩn' if hide else 'Hiện'} thanh điều hướng...")
                result = self.opt.hide_navigation_bar(hide)
                self.progress.emit(result)

            elif self.task_type == "compile_apps":
                mode = self.kwargs.get('mode', 'speed')
                self.progress.emit(f"💎 Đang tối ưu hóa App (Mode: {mode}). Vui lòng chờ...")
                result = self.opt.compile_apps(mode)
                self.progress.emit("✅ Hoàn tất biên dịch App.")

        except Exception as e:
            err_str = str(e)
            if "SecurityException" in err_str:
                self.progress.emit("⚠️ Lỗi: Thiếu quyền Bảo mật Xiaomi")
                details = (
                    "🔒 **YÊU CẦU QUYỀN BẢO MẬT**\n\n"
                    "Tính năng này bị chặn bởi bảo mật của Xiaomi (Permisson Denial).\n"
                    "Để khắc phục, bạn BẮT BUỘC phải thực hiện:\n\n"
                    "1️⃣ Vào **Cài đặt cho nhà phát triển**\n"
                    "2️⃣ Tìm và BẬT dòng: **Gỡ lỗi USB (Cài đặt bảo mật)**\n"
                    "   *(Lưu ý: Bạn cần đăng nhập Mi Account và lắp SIM để bật)*\n\n"
                    "👇 Sau khi bật xong, hãy thử lại tính năng này."
                )
                self.error_occurred.emit("Thiếu Quyền Bảo Mật", details)
            else:
                self.progress.emit(f"❌ Lỗi: {e}")
                
        self.finished.emit()
