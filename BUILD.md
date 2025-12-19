# Build Instructions - Windows Installer

## Yêu cầu (Requirements)
- Python 3.x
- PyInstaller (`pip install pyinstaller`)
- Inno Setup 6 (auto-installed by process)

## Cách build installer (How to Build)

### Bước 1: Build ứng dụng với PyInstaller
```bash
python build_exe_v2.py
```
- Tạo folder `dist/XiaomiADBCommander/` chứa ứng dụng và tất cả dependencies
- Bao gồm: Python runtime, PySide6, ADB binaries, databases

### Bước 2: Tạo file Setup.exe với Inno Setup
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```
- Đầu ra: `installer_output/XiaomiADBCommander_Setup_v2.4.0.exe`
- Kích thước: ~50-100MB (bao gồm toàn bộ thư viện)

## Tính năng Installer
✅ Chọn đường dẫn cài đặt tùy ý
✅ Tạo shortcut Desktop (tùy chọn)
✅ Tạo shortcut Start Menu
✅ Chương trình gỡ cài đặt (Uninstaller)
✅ Đóng gói đầy đủ Python + PySide6 + ADB tools

## Cấu trúc thư mục sau khi build
```
installer_output/
  └── XiaomiADBCommander_Setup_v2.4.0.exe  (File cài đặt)

dist/
  └── XiaomiADBCommander/
      ├── XiaomiADBCommander.exe           (App chính)
      ├── _internal/                       (Thư viện Python, PySide6...)
      ├── resources/
      │   ├── adb/                         (ADB binaries)
      │   └── scrcpy/                      (Scripts)
      └── src/
          └── data/
              └── soc_database.json
```

## Chạy thử (Test)
Chỉ cần double-click file `XiaomiADBCommander_Setup_v2.4.0.exe` và làm theo hướng dẫn cài đặt.
