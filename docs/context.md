# Project Context — Xiaomi ADB Commander

## 🎯 Mục tiêu dự án
Xiaomi ADB Commander là ứng dụng desktop Python + PySide6 để quản lý thiết bị Android qua ADB/Fastboot, tối ưu mạnh cho Xiaomi/MIUI/HyperOS. Hướng đến 3 nhóm người dùng:
- **Người dùng phổ thông** muốn tối ưu Xiaomi nhanh chóng
- **Kỹ thuật viên** sửa chữa/ROM/ADB
- **Power users** cần script, command nâng cao, debug

GitHub: `https://github.com/khoaiprovip123/ToolPC_ADB`

---

## 💻 Tech Stack
- **UI Framework:** PySide6 (+ PySide6-Addons), pyqtgraph
- **Backend / Logic:** Python 3.11+, psutil, requests / httpx / aiofiles
- **Data Validation:** pydantic, pydantic-settings
- **Logging:** `logging.handlers.RotatingFileHandler`
- **Build:** PyInstaller (onedir) + Inno Setup 6
- **Platform:** Windows 10/11 (ưu tiên), hỗ trợ Linux/macOS

---

## 🚀 Các tính năng chính
- **Device Connection:** USB và Wireless (TCP/IP, Pairing code Android 11+)
- **Dashboard:** CPU, RAM, Battery, Storage, Network — real-time polling nền
- **App Manager:** Scan, install/uninstall/disable/enable/backup — cascade strategy
- **APK Analyzer:** Parse thông tin APK (tên gói, version, SDK, permissions)
- **File Manager:** Browse, push/pull, image preview, context menu
- **Xiaomi Suite:**
  - Debloater — gỡ 100+ MIUI bloatware theo nhóm (An Toàn/Cảnh Báo/Nguy Hiểm)
  - AIO Optimizer — 3-Tab Control (Hiển Thị, Hiệu Năng, Hệ Thống) cho HyperOS/MIUI
  - Expert Tweaks — ép xung, fix RAM, tối ưu cảm ứng HyperOS
  - Fix Notification — cho Zalo, Messenger, Telegram... (Presets tích hợp)
  - Cleaner (Fix trim-caches 999G), Battery Health (Auto-refresh), OTA Downloader, App Store
- **Dev Tools:** Script Engine, Advanced Commands, Wireless Debug, DNS, Shizuku, Permissions
- **Auto-Update:** Kiểm tra release từ GitHub Releases (background)

---

## 🏗️ Kiến trúc & Cấu trúc thư mục

```
src/
  main.py                    # Entrypoint, mutex, QApplication, global style
  version.py                 # Source of truth cho version string
  core/
    adb/adb_manager.py       # ADB/Fastboot wrapper — mọi lệnh đi qua đây
    optimization_manager.py  # Tập hợp lệnh tối ưu MIUI/HyperOS
    log_manager.py           # Signal-based log + rotating file (5×5MB)
    update_manager.py        # Kiểm tra bản mới từ GitHub API
    plugin_manager.py        # Discover/load plugin .py
  ui/
    main_window.py           # Sidebar chính, device selector, page container
    pages/                   # Các trang cấp cao (dashboard, xiaomi, dev, settings…)
    widgets/                 # Widget chi tiết theo từng tính năng
  workers/                   # QThread tác vụ nền (không block UI)
  data/
    app_data.py              # AppInfo dataclass
    file_data.py             # FileEntry dataclass
    bloatware_data.py        # Danh sách package theo nhóm

resources/                   # ADB binaries, scrcpy, icons, data tĩnh
docs/                        # Tài liệu kỹ thuật (context, plan, agent, changelog)
tools/                       # Script build/phát hành
scripts/                     # Utility scripts (setup_dev, cleanup...)
```

---

## 🔄 Luồng vận hành quan trọng

### Khởi động
1. `main.py` tạo mutex (`XiaomiADBCommanderMutex_v4`) → ngăn chạy 2 instance
2. Tạo `QApplication` + áp global stylesheet từ `ThemeManager`
3. Khởi tạo `ADBManager` → mở `MainWindow`

### Device Lifecycle
- `MainWindow.refresh_devices()` → worker nền quét ADB/Fastboot
- Đổi thiết bị: `on_device_changed()` → set serial → reset từng widget → tải lại lazy

### Tác vụ ADB
- Mọi lệnh đi qua `ADBManager.execute()` (host-side) hoặc `ADBManager.shell()` (device-side)
- Hầu hết widget call qua `QThread` worker → emit `progress / finished / error`

---

## 📦 Build & Release

| Bước | Lệnh |
|------|-------|
| Build app | `venv\Scripts\python.exe tools\build_exe_v2.py` |
| Build installer | `venv\Scripts\python.exe tools\build_installer.py` |
| Output | `installer_output/XiaomiADBCommander_Setup_vX.X.X.X.exe` |

**Checklist release:** Đồng bộ version `src/version.py` + `installer.iss` + `docs/changelog.md` → Build sạch → Smoke test → Tag Git + GitHub Release.

---

## 🔒 Nguyên tắc bảo mật
1. **Subprocess Safety:** Không dùng `shell=True`. Command truyền dạng list. Timeout 30s mọi subprocess call.
2. **Exception Handling:** Không `except: pass`. Lỗi log qua `LogManager`. API key bị redact trong log.
3. **Log Management:** RotatingFileHandler — 5 files × 5MB. File permission `0o600`.
4. **Worker Thread Safety:** Kiểm tra `isRunning()` trước khi tạo worker mới. `wait()` worker cũ trước khi thay thế.
5. **UI Notifications:** Mọi thông báo đi qua `LogManager.log()` → `NotificationCenter`. Không dùng `QMessageBox` trực tiếp.

---

## 🔗 Cấu hình & Lưu trữ
- **Runtime settings:** `QSettings("VanKhoai", "XiaomiADBCommander")`
- **App log:** `logs/app_log.txt` (rotation 5×5MB)
- **config.yaml:** chỉ dùng cho Cloud Sync — chưa là config runtime trung tâm
