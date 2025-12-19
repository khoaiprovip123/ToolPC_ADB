# Changelog

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
