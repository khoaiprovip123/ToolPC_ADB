## [2.5.2] - 2025-12-24
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
