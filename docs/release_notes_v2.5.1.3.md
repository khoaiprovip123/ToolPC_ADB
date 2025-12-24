# Release Notes - v2.5.1.3

## 🚀 HyperOS 3 & Android 16 Support
- **Full Compatibility**: Optimized core ADB logic to support the latest Xiaomi HyperOS 3 and Android 16.
- **Smart OS Detection**: Improved detection for OS version strings on newer devices (`OS3.x.x`).
- **Enhanced Security Handling**: Graceful handling of Android 16 permission restrictions to prevent crashes.

## 🛠 Xiaomi Optimizer Improvements
- **Improved Debloater**: Now uses `pm uninstall --user 0` for core services (MSA, Analytics) to ensure effective removal on newer Android versions.
- **Stacked Recent View**: Enhanced the "Stacked Recent" feature with an automatic launcher restart, making it work instantly.
- **Advanced Smart Blur**: Added extra support for Control Center and Recents blur on HyperOS 3.
- **Bloatware List Update**: Added `com.xiaomi.discover` and other tracker packages to the debloat list.

## 📦 System & UI
- **Refined Status Display**: The device connection label now specifically identifies HyperOS 3 devices.
- **Stability Fixes**: Resolved various minor issues when reading battery and CPU data on restricted systems.
