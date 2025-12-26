from PySide6.QtCore import QThread, Signal

class OptimizationWorker(QThread):
    """Background worker for optimizations"""
    progress = Signal(str)
    result_ready = Signal(dict) # new signal for results
    error_occurred = Signal(str, str) # title, message
    finished = Signal()
    
    def __init__(self, adb, task_type):
        super().__init__()
        self.adb = adb
        self.task_type = task_type
        
    def run(self):
        try:
            if self.task_type == "full_scan":
                self.progress.emit("🔍 Đang quét hệ thống...")
                self.progress.emit("Đang kiểm tra MSA...")
                self.adb.disable_msa()
                self.progress.emit("✅ Đã xử lý System Ads")
                self.progress.emit("Đang xử lý Analytics...")
                self.adb.disable_analytics()
                self.progress.emit("✅ Đã tắt Theo dõi")
                self.progress.emit("Đang tối ưu hiệu ứng...")
                self.adb.optimize_animations(0.5)
                self.progress.emit("✅ Đã tăng tốc hiệu ứng")
                
            elif self.task_type == "animations":
                self.progress.emit("Đang tăng tốc hiệu ứng (0.5x)...")
                self.adb.optimize_animations(0.5)
                self.progress.emit("✅ Đã đặt tỷ lệ hiệu ứng 0.5x")

            elif self.task_type == "set_vietnamese":
                self.progress.emit("🇻🇳 Đang cài đặt Tiếng Việt...")
                result = self.adb.set_language_vietnamese()
                self.progress.emit(f"ℹ️ {result}")
                
            elif self.task_type == "fix_eu_vn":
                self.progress.emit("🌍 Đang sửa lỗi vùng EU_VN...")
                self.adb.set_prop("persist.sys.country", "VN")
                self.adb.set_prop("ro.product.locale", "vi-VN") 
                self.adb.set_system_setting("system", "time_12_24", "24")
                self.progress.emit("✅ Đã cập nhật Region VN & Time 24h")

            elif self.task_type == "check_status":
                self.progress.emit("🔍 Đang đọc thông số hệ thống...")
                status = self.adb.get_language_region_status()
                self.result_ready.emit(status)
                self.progress.emit("✅ Đã đọc dữ liệu xong")

            elif self.task_type == "smart_blur":
                self.progress.emit("✨ Đang phân tích cấu hình & kích hoạt Blur...")
                result = self.adb.apply_smart_blur()
                self.progress.emit(f"✅ {result}")

            elif self.task_type == "stacked_recent":
                self.progress.emit("📚 Đang kích hoạt giao diện Xếp chồng (HyperOS Native)...")
                # 1. New native method
                result = self.adb.set_recents_style(1)
                self.progress.emit(result)
                # 2. Legacy method
                self.adb.shell("settings put global task_stack_view_layout_style 2")
                
                self.progress.emit("🔄 Đang khởi động lại Launcher để áp dụng...")
                self.adb.shell("am force-stop com.miui.home")
                self.progress.emit("✅ Đã áp dụng giao diện Xếp chồng")

            elif self.task_type == "skip_setup":
                self.progress.emit("⏩ Đang bỏ qua Setup Wizard...")
                result = self.adb.skip_setup_wizard()
                self.progress.emit(result)

            elif self.task_type == "disable_ota":
                self.progress.emit("🛑 Đang chặn cập nhật hệ thống...")
                result = self.adb.disable_miui_ota()
                self.progress.emit(result)

            elif self.task_type == "force_refresh_rate":
                hz = 0
                if hasattr(self, 'refresh_rate'):
                    hz = self.refresh_rate
                label = "Mặc định (Auto)" if hz <= 0 else f"{hz}Hz"
                self.progress.emit(f"⚡ Đang áp dụng tần số quét {label}...")
                result = self.adb.set_refresh_rate(hz)
                self.progress.emit(result)

            elif self.task_type == "force_dark_mode_on":
                self.progress.emit("🌙 Đang bật Dark Mode hệ thống...")
                result = self.adb.force_dark_mode(True)
                self.progress.emit(result)

            elif self.task_type == "force_dark_mode_off":
                self.progress.emit("☀️ Đang tắt Dark Mode hệ thống...")
                result = self.adb.force_dark_mode(False)
                self.progress.emit(result)

            elif self.task_type == "hide_nav_on":
                self.progress.emit("↔️ Đang ẩn thanh điều hướng...")
                result = self.adb.hide_navigation_bar(True)
                self.progress.emit(result)

            elif self.task_type == "hide_nav_off":
                self.progress.emit("↔️ Đang hiện thanh điều hướng...")
                result = self.adb.hide_navigation_bar(False)
                self.progress.emit(result)

            elif self.task_type == "set_dpi":
                if hasattr(self, 'dpi_value'):
                    self.progress.emit(f"📱 Đang đổi DPI sang {self.dpi_value}...")
                    result = self.adb.set_display_density(self.dpi_value)
                    self.progress.emit(result)

            elif self.task_type == "show_fps_on":
                 self.progress.emit("📈 Đang bật bộ đếm FPS...")
                 result = self.adb.show_refresh_rate_overlay(True)
                 self.progress.emit(result)

            elif self.task_type == "show_fps_off":
                 self.progress.emit("📉 Đang tắt bộ đếm FPS...")
                 result = self.adb.show_refresh_rate_overlay(False)
                 self.progress.emit(result)

            elif self.task_type == "open_dev_options":
                 self.progress.emit("⚙️ Đang mở Cài đặt nhà phát triển...")
                 result = self.adb.open_developer_options()
                 self.progress.emit(result)

            elif self.task_type == "expert_optimize":
                 self.progress.emit("🚀 Đang kích hoạt Tối ưu hóa Chuyên sâu (HyperOS 3+)...")
                 result = self.adb.apply_performance_props()
                 self.progress.emit(result)
                 self.progress.emit("🔄 Đang tối ưu hóa Compiler (speed-profile)...")
                 result = self.adb.compile_apps("speed-profile", timeout=300, callback=self.progress.emit)
                 self.progress.emit(result)

            elif self.task_type == "art_tuning":
                 self.progress.emit("⚡ Đang tối ưu hóa ART (Full Speed)...")
                 result = self.adb.compile_apps("speed", timeout=600, callback=self.progress.emit)
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
