# Changelog — Xiaomi ADB Commander

Tất cả các thay đổi đáng chú ý được ghi chép tại đây theo chuẩn [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]
### Added
- Bộ template quản lý tài liệu dự án: `docs/context.md`, `docs/plan.md`, `docs/agent.md`, `docs/changelog.md`
- Di chuyển `USER_GUIDE.md` → `docs/user_guide.md`
- Di chuyển `BUILD.md` → `docs/build.md`

### UI Enhancements (Phase 3)
- **Sidebar Group Labels**: Phân nhóm 9 công cụ thành 3 nhóm (⚡ Hiệu Năng / 📢 Ứng Dụng / 🌐 ROM & Hệ Thống) trong `XiaomiToolsPage`
- **Debloater Filter Combo**: Lọc app theo mức an toàn (Tất Cả / An Toàn / Cảnh Báo / Nguy Hiểm)
- **Debloater Quick-Select Buttons**: Nút "✅ Chọn An Toàn" chỉ tích những app `safety=safe`, kèm "Chọn Tất Cả" / "Bỏ Chọn"
- **Debloater Progress Bar**: Thanh tiến trình 4px hiện trong lúc đang gỡ, tự ẩn khi xong
- **NotificationFix Preset Buttons**: Nút chọn nhanh "Zalo + Messenger", "Tất cả MXH", "Email & Calendar"
- **Battery Auto-Refresh**: `QTimer` 5 giây sẵn sàng trong `BatteryHealthWidget` (kích hoạt khi cần)
- **Lazy Device Reset**: `XiaomiToolsPage.reset()` chỉ reset widget đang active, các widget khác reset khi navigate đến

### Fixed
- **[P1] Mutex lệch:** Đồng bộ `AppMutex=XiaomiADBCommanderMutex_v4` trong `installer.iss` với runtime `main.py`
- **[P1] Worker Shutdown:** Thay `terminate()` bằng `requestInterruption()+wait(3000ms)` trong `closeEvent` để tránh resource leak
- **[P1] `shell(log_error=False)` → TypeError:** Xóa tham số không tồn tại khỏi tất cả lần gọi trong `optimization_worker.py`
- **[P1] Dead Code 800 dòng:** Xóa `XiaomiHubWidget` và `XiaomiOptimizerWidget` cũ khỏi `xiaomi_optimizer.py` (59KB → ~43KB)
- **[P1] scroll.setWidget() gọi 2 lần:** Fix widget leak în `XiaomiExpertTweaksWidget`
- **[P1] AttributeError Fastboot:** Xóa `run_write_cid()` / `run_flash_token()` tham chiếu attrs chưa khởi tạo
- **[P1] error_occurred signal:** Connect signal trong `run_task()` để SecurityException không bị nuốt im lặng
- **[P2] Sideload typo:** Sửa `'sideloade'` → `'sideload'` trong `adb_manager.py`
- **[P2] Shell() kwargs:** Xóa `*args, **kwargs` thừa khỏi `ADBManager.shell()`
- **[P2] Silent failures:** Thay `except: pass` bằng `except Exception as _pkg_err` + log, và `LogManager.log(warning)` trong OTA fetch
- **[P2] Theme Hardcode:** Màu `#1a1a1a` / `#5f6368` → `ThemeManager.COLOR_TEXT_PRIMARY/SECONDARY` trong `NotificationAppItem`
- **[P2] Cleaner Race Condition:** Worker guard đặt trước `worker.start()` thay vì sau
- **[P2] DebloatWorker Interruption:** Đổi `_is_running` flag → Qt-native `isInterruptionRequested()`

---

## [2.5.5.5] - 2026-03-19
### Changed
- **Release Packaging**: Đồng bộ version 2.5.5.5 giữa app, installer và cấu hình mặc định.
- **Inno Setup Output**: Cập nhật tên file cài đặt theo version mới (XiaomiADBCommander_Setup_v2.5.5.5.exe).

---

## [2.5.5.4] - 2026-02-25
### Added
- **Log Rotation**: Triển khai `RotatingFileHandler` cho `LogManager` (5 files × 5MB), chống phình log.
- **Unit Tests**: 22 bài test tự động cho `LogManager`, `ADBManager`, `CallableWorker` (pytest).
- **SECURITY.md**: Tài liệu hóa các thực hành bảo mật (subprocess safety, exception handling, worker thread safety).

### Changed
- **🎨 Battery Health UI Redesign**: Dark glass morphism cards (`#1a1a2e`), circular battery gauge lớn hơn. Stat mini-cards riêng biệt, badge trạng thái nhiệt độ.
- **🎨 Cleaner Widget Redesign**: Dark glass cards, icon circles lớn, gradient header. Phản hồi trạng thái (✓/✗) sau mỗi thao tác, kiểm tra kết nối trước khi thực thi.
- **🎨 Debloater Widget Redesign**: Cards tương thích sáng/tối (ThemeManager). Real-time counter, progress tracking, visual feedback badge. Nút "Gỡ bỏ" tự disable khi đang xử lý.
- **Cleaner Logic (ADB)**: Mở rộng `clean_messenger_data` hỗ trợ Telegram Audio, Documents, Nekogram cache.
- **QProcess Refactor**: Chuyển `subprocess.Popen` → `QProcess` cho scrcpy trên Dashboard.
- **Sidebar Spacing**: Tăng khoảng cách giữa logo và menu điều hướng (2px → 20px).

### Fixed
- **Version Label Border**: Xóa viền thừa quanh nhãn phiên bản trên sidebar.
- **Debloater Counter Bug**: Sửa lỗi counter "0 ứng dụng" không cập nhật khi tích chọn.
- **Debloater Finished Handler**: Kết nối `DebloatWorker.finished` signal (trước đó bị bỏ sót).

---

## [2.5.5.3] - 2026-02-11
### Added
- **Navigation Architecture Overhaul**: Chuyển từ tab ngang lồng nhau sang **Thanh điều hướng dọc thứ cấp (Secondary Sidebar)** cho các trang phức tạp (Xiaomi Tools, Dev Tools).
- **AIO Optimizer**: Hợp nhất 3 tab thành một widget duy nhất với bố cục thẻ lưới (Grid Card).
- **Confirmation System**: `ConfirmationDialog` thay thế hoàn toàn `QMessageBox` cho tất cả hành động nguy hiểm.
- **Ocean Breeze / Sea Blue Theme**: Light Theme mới tông xanh nước biển, hiệu ứng Acrylic tint phong cách HyperOS.
- **Centralized Notifications**: Đồng bộ toàn bộ feedback từ ADB, Fastboot, Optimization về Notification Center.

### Changed
- **UI Responsiveness**: Tối ưu hóa cho độ phân giải động (mặc định 1400x800).
- **Cleanup**: Xóa `system_tweaks.py`, `unified_tools.py`, `screen_mirror.py` dư thừa.

### Fixed
- **Stability**: Sửa `ImportError` nghiêm trọng sau khi gộp công cụ Xiaomi, đảm bảo tab AIO ổn định.
- **Bug Fixes**: Sửa màu sắc hộp thoại kết quả, cải thiện logic nhảy trang từ Dashboard.

---

## [2.5.5.2] - 2026-01-30
### Added
- **Glass Dialogs**: Hỗ trợ Dialog với Glass Effect, khắc phục lỗi đen nền trên Windows.
- **Icon Update**: Logo ứng dụng cập nhật đồng bộ trong cả giao diện và installer.

### Fixed
- **Stability**: Thêm Strict Device Check trong OptimizationWorker — ngăn báo "Thành công" ảo khi không có thiết bị.
- **Crash Fix**: Sửa `NameError: QFrame` khi khởi động App Manager/Logcat.

---

## [2.5.5.1] - 2026-01-27
### Fixed
- **Hotfix ADB & UI**: Sửa lỗi không nhận ADB sau khi cập nhật, fix crash startup (mutex error).
- **Badge ADB Dashboard**: Hiển thị chính xác hơn trạng thái kết nối.

---

## [2.5.5.0] - 2026-01-27
### Added
- **System Tweaks UI Refactor**: Tái cấu trúc hoàn toàn Tab Tweaks theo phong cách "Xiaomi Hub" với Card Gradient.
- **Relocated Brevent Activation**: Chuyển sang mục "Công Cụ Khác → Cấp Quyền".
- **Bổ sung Tweaks**: Việt hóa 1-Click, Tắt OTA MIUI, Bỏ qua Setup Wizard.

### Fixed
- **Indentation Error**: Sửa lỗi cú pháp nghiêm trọng trong `optimization_manager.py`.
- **Optimization Worker**: Cải thiện logic xử lý tác vụ ngầm cho Tweaks.

---

## [2.5.4.1] - 2026-01-24
### Added
- **App Manager — Aggressive Cascade Strategy**: System apps tự động thử nhiều phương thức xóa theo thứ tự (disable-user → uninstall-user → disable → hide → clear data → force-stop).

### Changed
- **Simplified Action Buttons**: System apps chỉ 1 nút "Xóa", user apps chỉ 1 nút "Gỡ" với cascade fallback.
- **Clear Success Notifications**: Thông báo nêu rõ phương thức đã dùng.
- **Removed App Display Limit**: Hiển thị ALL apps thay vì giới hạn 100.

### Fixed
- **Duplicate Error Notifications**: Loại bỏ thông báo lỗi trùng lặp cho cascade attempts.
- **Refresh Crash Bug**: Fix crash khi click "Làm mới" nhiều lần liên tiếp.

---

## [2.5.4.0] - 2026-01-23
### Added
- **Xiaomi Brevent Tools**: 4 mã tối ưu mới (No App Label, Device Blur, Super Wallpaper, Native Call Recording).
- **Status Bar Alert**: Hiển thị cảnh báo "Unauthorized" trực tiếp trên status bar.

### Changed
- **Performance Optimization**: Offload ALL ADB tasks sang background threads — loại bỏ UI freeze.
- **UI Improvements**: Sửa Invisible Text (white on white) trong QMessageBox. Suppress intrusive ADB Unauthorized popup.

---

## [2.5.3.3] - 2025-12-31
### Changed
- Cập nhật phiên bản bảo trì, cải thiện độ ổn định.

---

## [2.5.3.2] - 2025-12-30
### Added
- Expanded SOC database 200+ devices (Xiaomi, Samsung, OPPO, vivo, Realme, Pixel).
- Hiển thị friendly marketing names trên Dashboard.
- New "Screen Toggle" button (📺) trong Control Center.

### Changed
- Dashboard Hero ưu tiên marketing name hơn model code.
- Refined App Manager UI: Theme-consistent highlights.

---

## [2.5.3.1] - 2025-12-30
### Added
- **Cleanup Script**: `scripts/cleanup.py` — dọn `__pycache__/`, `*.pyc`, build artifacts, log files cũ.

### Changed
- **Project Optimization**: Giảm từ 265.66 MB → 95.59 MB (tiết kiệm 64%).

---

## [2.5.3.0] - 2025-12-26
### Added
- **App Manager UX Overhaul (Premium Glass UI)**: Glassmorphism aesthetic, Floating Action Bar, Vietnamese tags, Dynamic Icons, Optimistic UI, Smart Fallback, Selection Indicator.

---

## [2.5.2.0] - 2025-12-24
### Fixed
- **Dashboard "Checking..." Freeze**: Fix `shell()` trả `None`, gây hang vô tận khi khởi động.
- **Battery Health Error**: Xử lý non-standard dumpsys output.
- **ART Tuning Feedback**: Real-time progress streaming, fix "Destroyed while thread running" crash.
- **Log System**: Thêm persistent file logging (`logs/app_log.txt`) với timestamp và level.

---

## [2.5.1.3] - 2025-12-23
### Added
- HyperOS 3 & Android 16 Support. Stacked Recent View. Improved Debloater list.

### Fixed
- **Installer "File in Use"**: AppMutex + auto terminate `adb.exe` trong installer.
- **Permission Denied**: Silent Fail cho battery/CPU data trên Android 16 restricted mode.

---

## [2.5.1.1] - 2025-12-22
### Fixed
- **Update System**: Cải thiện parsing version tag không chuẩn (`v.2.5.1.0`).

---

## [2.5.1.0] - 2025-12-22
### Added
- **Show FPS & Refresh Rate Monitor**: Toggle FPS overlay, Auto và Manual fallback.
- **Advanced Refresh Rate Control**: Force Hz (60/90/120/144) hoặc reset Auto.
- **Xiaomi Suite (Unified Menu)**: Gộp Debloater, Quick Tools, Advanced vào menu phẳng.

### Changed
- **UI Refactoring**: Module hoá `XiaomiOptimizerWidget` thành các component độc lập.
- **Window Size**: Tăng kích thước mặc định lên 1450×850.

---

## [2.5.0.5] - 2025-12-20
### Added
- HyperOS 3 Optimization: Bật Stacked task view (iOS style).

---

## [2.4.1] - 2025-12-19
### Added
- **Auto-Update System**: GitHub Releases API, background check lúc khởi động (3s delay), manual check trong Settings, download progress, one-click install.
- **New Settings Tab**: "Cập Nhật" với đầy đủ tùy chọn cấu hình.
- **Version Management**: Centralized `src/version.py`.

---

## [2.4.0] - 2025-12-19
### Added
- **File Manager Overhaul (HyperOS Style)**: Large Header, Category Grid, Storage Selector, Image Preview, Context Menu (Copy/Cut/Paste/Rename/Delete/Download).
- **Shizuku Manager**: Card UI, improved feedback dialogs.
- **Battery Health**: Premium Dark UI với "Disconnected" state.
- **Fastboot Repair**: UI hiện đại, tách Flash/Wipe tools.
- **Global Layout**: Scroll support cho tất cả unified tool tabs.

---

## [2.3.0] - 2025-12-11
### Added
- **Horizontal Tab UI**: Refactor "Công cụ" và "Cài Đặt" sang horizontal segmented control.
- **Centralized Notifications**: Mọi action route về Notification Center.
- **Mirroring Integration**: Screen Mirroring controls vào Notification Center.

---

## [2.2.0] - 2025-12-10
### Added
- **Fastboot Rescue Tool**: FRP Unlock, advanced reboot modes.
- **Unified Tools**: Gộp utilities thành tabs logic (Dev Tools, System Utils, Xiaomi Suite).

---

## [2.1.0] - 2025-12-01
### Added
- **Initial Release**: Core features — Dashboard, App Manager, File Manager.
