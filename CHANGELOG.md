# Changelog

## [2.5.5.4] - 2026-02-25
### Added
- **Log Rotation**: Triển khai `RotatingFileHandler` cho `LogManager` (5 files × 5MB), chống phình log.
- **Unit Tests**: 22 bài test tự động cho `LogManager`, `ADBManager`, `CallableWorker` (pytest).
- **SECURITY.md**: Tài liệu hóa các thực hành bảo mật (subprocess safety, exception handling, worker thread safety).

### Changed
- **🎨 Battery Health UI Redesign**: Thiết kế lại hoàn toàn widget Pin & Sức khỏe:
  - Dark glass morphism cards (`#1a1a2e`), circular battery gauge lớn hơn.
  - Stat mini-cards riêng biệt cho từng chỉ số, badge trạng thái nhiệt độ.
  - Cải thiện contrast text trên nền gradient.
- **🎨 Cleaner Widget Redesign**: Thiết kế lại hoàn toàn widget Dọn Rác:
  - Dark glass cards, icon circles lớn, gradient header.
  - Phản hồi trạng thái (✓/✗) sau mỗi thao tác dọn dẹp.
  - Kiểm tra kết nối thiết bị trước khi thực thi, log chi tiết qua `LogManager`.
- **🎨 Debloater Widget Redesign**: Thiết kế lại hoàn toàn trang Gỡ Ứng Dụng:
  - Cards tương thích cả nền sáng/tối (ThemeManager-based colors).
  - **Chọn nhóm**: Nút tích/bỏ chọn theo từng danh mục (category).
  - **Real-time counter**: Số lượng ứng dụng được chọn cập nhật ngay khi tích.
  - **Progress tracking**: Hiển thị tiến trình xử lý từng package (Đang xử lý: X/Y).
  - **Visual feedback**: Badge "✓ Đã gỡ" / "✗ Lỗi" trên mỗi card sau khi gỡ.
  - Nút "Gỡ bỏ" tự disable và đổi text khi đang xử lý, kết nối `finished` signal.
- **Cleaner Logic (ADB)**: Mở rộng `clean_messenger_data` hỗ trợ thêm Telegram Audio, Documents, Nekogram cache.
- **QProcess Refactor**: Chuyển `subprocess.Popen` → `QProcess` cho `scrcpy` trên Dashboard.
- **Sidebar Spacing**: Tăng khoảng cách giữa logo và menu điều hướng (2px → 20px).

### Fixed
- **Version Label Border**: Xóa viền khung dư thừa quanh nhãn phiên bản trên sidebar.
- **Debloater Counter Bug**: Sửa lỗi counter "0 ứng dụng" không cập nhật khi tích chọn.
- **Debloater Finished Handler**: Kết nối `DebloatWorker.finished` signal (trước đó bị bỏ sót).

## [2.5.5.3] - 2026-02-11
### Added
- **Navigation Architecture Overhaul**: Thay đổi hoàn toàn cấu trúc điều hướng làm phẳng (Flat Management). Chuyển từ các tab ngang lồng nhau sang **Thanh điều hướng dọc thứ cấp (Secondary Sidebar)** cho các trang phức tạp (Xiaomi Tools, Dev Tools).
- **AIO Optimizer (Consolidated)**: Hợp nhất 3 tab "Tối ưu nhanh", "Tính năng ẩn" và "Tinh chỉnh hệ thống" thành một widget **"Tối Ưu & Tinh Chỉnh (AIO)"** duy nhất với bố cục thẻ lưới (Grid Card) hiện đại.
- **Confirmation System**: Triển khai hệ thống xác nhận an toàn mới (`ConfirmationDialog`) thay thế hoàn toàn `QMessageBox` mặc định, tích hợp cho tất cả các hành động gỡ ứng dụng, dọn rác và tinh chỉnh hệ thống.
- **Ocean Breeze / Sea Blue Theme**: Cập nhật toàn diện chủ đề sáng (Light Theme) sang tông xanh nước biển và trắng, sử dụng hiệu ứng kính mờ (Acrylic tint) cao cấp theo phong cách HyperOS.
- **Centralized Notifications**: Đồng bộ hóa toàn bộ phản hồi từ hệ thống, ADB, Fastboot về Trung tâm thông báo (Notification Center - LogManager).

### Changed
- **UI Responsiveness**: Tối ưu hóa giao diện cho độ phân giải động (mặc định 1400x800), đảm bảo các thành phần không bị cắt hoặc tràn khi thay đổi kích thước cửa sổ.
- **Cleanup**: Xóa bỏ các file và widget dư thừa (`system_tweaks.py`, `unified_tools.py`, `screen_mirror.py`) để tối ưu dung lượng và tốc độ khởi động.

### Fixed
- **Stability**: Sửa lỗi `ImportError` nghiêm trọng sau khi gộp công cụ Xiaomi, đảm bảo tab AIO hoạt động ổn định.
- **Bug Fixes**: Sửa lỗi hiển thị màu sắc trên các hộp thoại kết quả và cải thiện logic nhảy trang từ Dashboard.

## [2.5.5.2] - 2026-01-30
### Added
- **UI Polish**: Sửa lỗi "boxy borders" (viền dư thừa) trên tiêu đề các nhóm chức năng trong Xiaomi Optimizer.
- **Glass Dialogs**: Cập nhật ThemeManager để hỗ trợ hộp thoại (Dialog) với hiệu ứng kính (Glass Effect), khắc phục hoàn toàn lỗi đen nền (black background) trên Windows.
- **Icon Update**: Logo ứng dụng được cập nhật đồng bộ trong cả giao diện và file cài đặt (setup).

### Fixed
- **Stability**: Thêm cơ chế kiểm tra kết nối thiết bị chặt chẽ (Strict Device Check) trong OptimizationWorker. Ngăn chặn báo "Thành công" ảo khi không có thiết bị.
- **Crash Fix**: Sửa lỗi `NameError: QFrame` khi khởi động App Manager/Logcat.

## [2.5.5.1] - 2026-01-27
### Fixed
- **Hotfix ADB & UI**: Sửa lỗi không nhận ADB sau khi cập nhật và fix lỗi crash startup (mutex error).
- **Cải thiện hiển thị**: Badge trạng thái ADB trên Dashboard hiển thị chính xác hơn.

## [2.5.5.0] - 2026-01-27
### Added
- **System Tweaks UI Refactor**: Tái cấu trúc hoàn toàn Tab Tweaks đồng bộ phong cách "Xiaomi Hub" với hệ thống Card Gradient hiện đại.
- **Relocated Brevent Activation**: Chuyển công cụ "Kích hoạt Brevent" sang mục "Công Cụ Khác -> Cấp Quyền" để tối ưu trải nghiệm.
- **Bổ sung Tweaks quan trọng**: Khôi phục các tính năng Việt hóa 1-Click, Tắt OTA MIUI, Bỏ qua Setup Wizard.
- **Fixed Hub Icons**: Sửa lỗi hiển thị icon (dấu hỏi chấm) cho các mục Store và Fastboot trong Hub.

### Fixed
- **Indentation Error**: Sửa lỗi cú pháp nghiêm trọng trong `optimization_manager.py` gây treo ứng dụng.
- **Optimization Worker**: Cải thiện logic xử lý tác vụ ngầm cho tính năng Tweaks mới.


## [2.5.4.1] - 2026-01-24
### Added
- **App Manager - Aggressive Cascade Strategy**: 
  - System apps now automatically try multiple removal methods in sequence (disable-user → uninstall-user → disable → hide → clear data → force-stop) until one succeeds.
  - Significantly improves success rate for stubborn HyperOS/MIUI system apps that previously failed to disable.

### Changed
- **Simplified Action Buttons**: 
  - System apps now show only one "Xóa" (Remove) button instead of separate "Tắt" and "Gỡ" buttons.
  - User apps now show only one "Gỡ" (Uninstall) button with cascade fallback.
- **Clear Success Notifications**: 
  - Notifications now explicitly state the method used (e.g., "đã được gỡ khỏi thiết bị" vs "đã được tắt" vs "đã được ẩn").
  - Action results are crystal clear to users.
- **Removed App Display Limit**: 
  - App list now displays ALL filtered apps instead of only the first 100.
  - Status bar shows accurate count (e.g., "Hiển thị 485/485" instead of "100/485").

### Fixed
- **Duplicate Error Notifications**: 
  - Eliminated redundant error notifications for cascade attempts.
  - Only final failures are reported, preventing notification spam.
- **Refresh Crash Bug**: 
  - Fixed application crash when clicking "Làm mới" (Refresh) multiple times rapidly.
  - Properly stops and cleans up old scanner threads before starting new ones.

## [2.5.4.0] - 2026-01-23
### Added
- **Xiaomi Brevent Tools**: Integrates 4 new optimization codes:
  - **No App Label**: Hide app names on home screen (`miui_home_no_word_model`).
  - **Device Blur**: Force enable high-end blur for folders & recents (`deviceLevelList`).
  - **Super Wallpaper**: Unlock Super Wallpaper feature (`aod_using_super_wallpaper`).
  - **Native Call Recording**: Uninstall overlay to restore native call recording (`com.android.phone.cust.overlay.miui`).
- **Status Bar Alert**: Shows "Unauthorized" warning directly on the status bar if device is connected but not allowed.

### Changed
- **Performance Optimization**: 
  - Offloaded ALL ADB tasks (Uninstall, Debloat, Device Check, Refresh) to background threads.
  - Eliminated UI freezing/lag during device operations.
  - Optimized app startup and shutdown sequence (safe thread termination).
- **UI Improvements**:
  - Fixed "Invisible Text" (White text on White background) in QMessageBox for all themes.
  - Suppressed intrusive "ADB Unauthorized/Offline" popup errors (now logs silently).

## [2.5.3.3] - 2025-12-31
### Changed
- Cập nhật phiên bản bảo trì và tối ưu hóa hệ thống.
- Cải thiện độ ổn định.

## [2.5.3.2] - 2025-12-30

### Added
- Expanded SOC database with 200+ devices (Xiaomi, Samsung, OPPO, vivo, Realme, Pixel).
- Display friendly marketing names (e.g., "Xiaomi 11 Lite 5G NE") in Dashboard.
- New "Screen Toggle" button (📺) in Control Center (virtual power button).

### Changed
- Dashboard Hero section now prioritizes marketing names over model codes.
- Simplified Dashboard hardware specs (removed redundant device name label).
- Refined App Manager UI: Light/Theme-consistent selection and hover highlights (removed dark overlays).

## [2.5.3.1] - 2025-12-30
### Added
- **Cleanup Script**: Tạo `scripts/cleanup.py` - công cụ tự động dọn dẹp file thừa, cache và build artifacts
  - Tự động xóa tất cả `__pycache__/` và `*.pyc` files
  - Dọn dẹp build artifacts (`build/`, `dist/`)
  - Làm sạch log files cũ
  - Báo cáo chi tiết dung lượng tiết kiệm được

### Changed
- **Project Optimization**: Tối ưu hóa dung lượng dự án
  - Giảm từ 265.66 MB xuống 95.59 MB (tiết kiệm 170.07 MB - 64%)
  - Xóa các file debug không cần thiết (`debug_import.py`, `debug_import_no_app.py`)
  - Xóa log files cũ (`crash_log.txt`, `launch_log.txt`)
  - Cập nhật `.gitignore` để tránh track debug files và logs trong tương lai

## [2.5.3.0] - 2025-12-26
### Added
- **App Manager UX Overhaul (Premium Glass UI)**:
  - **New Design**: Completely redesigned the interface with a "Glassmorphism" aesthetic, featuring subtle blurs and rounded cards.
  - **Floating Action Bar**: Introduced a context-aware floating bar at the bottom for quick actions (Uninstall, Disable, Enable, Restore).
  - **Vietnamese Localization**: Translated all app tags (`HỆ THỐNG`, `NGƯỜI DÙNG`, `ĐÃ BẬT`, `ĐÃ TẮT`, `ĐÃ GỠ`) for better accessibility.
  - **Dynamic Icons**: Added colorful generated icons for app list items.
  - **Optimistic UI**: Implement instant visual feedback for management actions.
  - **Smart Fallback**: Automatically attempts to "Archive" (Uninstall user 0) system apps if "Disable" fails.
  - **Selection Indicator**: Added a sleek side-accent bar for selected rows.
  - **Error Handling**: Suppressed aggressive "ADB Error" dialogs for expected scenarios.

## [2.5.2.0] - 2025-12-24
### Fixed
- **Dashboard "Checking..." Freeze**: 
  - Fixed critical bug where `shell()` returned `None`, causing the dashboard to hang indefinitely on startup.
  - Resolved `AttributeError: legacy_shell` by restoring the return statement implementation.
- **Battery Health Error**: Adjusted log parsing to handle non-standard dumpsys output gracefully.
- **ART Tuning Feedback**:
  - Implemented real-time progress streaming for "Tăng tốc ứng dụng (ART Tuning)".
  - Fixed "Destroyed while thread is still running" crash by adding proper thread state checks.
  - Corrected log display bug which showed "OK: package" instead of actual app names.
- **Log System**:
  - Added persistent file logging to `logs/app_log.txt` for easier troubleshooting.
  - Logs now include timestamp, level (INFO/ERROR), and category.



## [2.5.1.3] - 2025-12-23
### Added
- **HyperOS 3 & Android 16 Support**: Enhanced detection for newer OS versions (`OS3.x.x`).
- **Stacked Recent View**: Improved reliability on HyperOS 3 with automatic launcher restart.
- **Improved Debloater**: Expanded bloatware list (added `com.xiaomi.discover`) and added `pm uninstall --user 0` fallback for newer Android versions.
- **Smart Blur**: Added support for Control Center and Recents blur on HyperOS 3.

### Fixed
- **Installer "File in Use"**: Added `AppMutex` and automated `adb.exe` termination in the installer script to prevent "Access is denied" errors during updates.
- **Permission Denied Errors**: Implemented "Silent Fail" for battery/CPU data access on restricted Android 16 systems to prevent crash logs.

## [2.5.1.1] - 2025-12-22
### Hotfix
- **Update System**: Improved version tag parsing matching logic to support non-standard tags (e.g., `v.2.5.1.0`), ensuring reliable update notifications for future releases.

## [2.5.1.0] - 2025-12-22
### Added
- **Show FPS & Refresh Rate Monitor**: New tool to toggle system FPS overlay, with Auto and Manual (Developer Options) fallback modes.
- **Advanced Refresh Rate Control**: Added ability to force specific Hz values (60, 90, 120, 144Hz) or reset to Auto.
- **Xiaomi Suite (Unified Menu)**: consolidated all Xiaomi tools (Debloater, Quick Tools, Advanced) into a single, flattened "Bộ Xiaomi" menu.

### Changed
- **UI Refactoring**: Modularized `XiaomiOptimizerWidget` into standalone components (`XiaomiDebloaterWidget`, `XiaomiQuickToolsWidget`, `XiaomiAdvancedWidget`) for better maintainability and navigation.
- **Window Size**: Increased default application window size to 1450x850 for improved layout visibility.

### Fixed
- **UI Layout Overlap**: Fixed widget collision in the "Tính năng Nâng cao" (Advanced Features) tab.
- **Menu Structure**: Resolved "tabs within tabs" design issue by promoting sub-tabs to the main suite level.

## [2.5.0.5] - 2025-12-20
### Added
- **HyperOS 3 Optimization**: Added support for enabling "Stacked" task view (iOS style) on HyperOS 3.

## [2.4.1] - 2025-12-19
### Added
- **Auto-Update System**: Comprehensive automatic update functionality
  - GitHub Releases API integration for version checking
  - Automatic update check on startup (3-second delay)
  - Manual update check from Settings tab
  - Download progress tracking with speed and ETA
  - One-click update installation
  - Configurable settings: auto-check toggle, pre-release option, skip version
  - Settings persistence with QSettings
  - Silent background checking without blocking UI
- **New Settings Tab**: "Cập Nhật" (Update) with full configuration options
- **Version Management**: Centralized version constant in `src/version.py`
- **Update Dialogs**: Beautiful notification and progress dialogs

### Changed
- Updated version display to use centralized `__version__` constant
- Enhanced ThemeManager with `COLOR_BORDER` and `COLOR_BORDER_LIGHT` class variables

### Technical
- New modules: `update_manager.py`, `downloader.py`, `update_dialog.py`
- QThread-based background update checking
- Streaming file download with progress callbacks
- Semantic version comparison (tuple-based)
- GitHub API v3 integration

## [2.4.0] - 2025-12-19
### Added
- **File Manager**: Complete overhaul (HyperOS Style), Storage Selector, File Ops (Copy/Cut/Paste), Image Preview.
- **Shizuku Manager**: Redesigned with Card UI, improved feedback dialogs, and borderless layout.
- **Battery Health**: Premium Dark UI with "Disconnected" state handling (fixes 0mAh bug).
- **Fastboot Repair**: Modernized UI with clear separation of Flash/Wipe tools.
- **Global Layout**: Added scroll support for all unified tool tabs (Dev Tools, Xiaomi Suite, etc.) to prevent clipping.
- **File Manager Overhaul (HyperOS Style)**:
    - Redesigned UI with Large Header and Category Grid (Documents, Images, Video, Audio).
    - **Storage Selector**: Dropdown to switch between Internal Storage and SD Card (auto-detected).
    - **PC Transfer**: "Import from PC" button with destination prompt and auto-navigation.
    - **Image Preview**: Double-click images (`.jpg`, `.png`, etc.) to view directly in-app.
    - **Context Menu**: Added Copy, Cut, Paste (Internal), Rename, Delete, Download to PC.
    - **Robust Listing**: Switched to `ls -1p` parsing to fix folder visibility on some devices.
- **Fastboot Repair UI**:
    - Rebuilt interface to match new design (Green Status Bar, Blue Reboot Grid, Red FRP Button).
    - Renamed tab "Fastboot & Repair" to "Fastboot Repair".

## [2.3.0] - 2025-12-11
### Added
- **Horizontal Tab UI**: Refactored "Công cụ" (Tools) and "Cài Đặt" (Settings) to use a modern horizontal segmented control layout, replacing legacy vertical menus.
- **Centralized Notifications**: All system actions (ADB, Fastboot, Optimization) now route feedback to the Notification Center.
- **Mirroring Integration**: Screen Mirroring controls moved directly into the Notification Center.

### Changed
- **Xiaomi Optimizer**: Removed local log panel in favor of centralized notifications for a cleaner look.
- **Fastboot Toolbox**: Replacing blocking popups with non-intrusive notifications for success messages.

## [2.2.0] - 2025-12-10
### Added
- **Fastboot Rescue Tool**: Helper for FRP Unlock and advanced reboot modes.
- **Unified Tools**: Grouped scattered utilities into logical tabs (Dev Tools, System Utils, Xiaomi Suite).

### Fixed
- **ADB Prune Dex**: Handled errors gracefully on unsupported devices.
- **UI Scaling**: Fixed brand icon truncation on Dashboard.

## [2.1.0] - 2025-12-01
### Added
- **Initial Release**: Core features including Dashboard, App Manager, File Manager.
