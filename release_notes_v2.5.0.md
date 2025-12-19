# Version 2.5.0 - Auto-Update System

## 🎉 Tính Năng Mới

### ✨ Hệ Thống Auto-Update
- **Tự động kiểm tra cập nhật** từ GitHub Releases khi khởi động app
- **Kiểm tra thủ công** từ Settings → tab "Cập Nhật"
- **Download tự động** với thanh progress, tốc độ và thời gian còn lại
- **Cài đặt một click** - chỉ cần nhấn "Cập nhật ngay"
- **Cấu hình linh hoạt**: 
  - ☑ Tự động kiểm tra khi khởi động
  - ☐ Bao gồm phiên bản beta
  - Bỏ qua phiên bản cụ thể

### 🎨 UI Components
- Tab mới trong Settings: **"Cập Nhật"**
- Dialog thông báo update đẹp mắt với changelog
- Progress dialog với real-time tracking
- Hiển thị phiên bản hiện tại: v2.4.0

## 🔧 Technical Details

- **GitHub API Integration**: Tự động query releases từ repository
- **Background Checking**: QThread-based, không block UI
- **Semantic Versioning**: So sánh version thông minh (v2.4.0 vs v2.5.0)
- **Streaming Download**: Download file với chunks 8KB
- **Settings Persistence**: QSettings lưu preferences người dùng

## 📦 New Files

- `src/version.py` - Centralized version management
- `src/core/update_manager.py` - Core update logic
- `src/core/downloader.py` - File download handler
- `src/ui/dialogs/update_dialog.py` - Update UI dialogs

## 🐛 Bug Fixes

- Fixed missing `COLOR_BORDER` class variables in ThemeManager
- Fixed duplicate `COLOR_BG_SECONDARY` definition

## 📝 Documentation

- Updated README.md with Auto-Update feature
- Updated CHANGELOG.md with v2.4.1 entry

---

## 🚀 Installation

1. Download `XiaomiADBCommander_Setup_v2.5.0.exe`
2. Run installer
3. App will auto-update từ bây giờ!

## 📸 Screenshots

*Auto-update check in Settings*
*Update notification dialog*
*Download progress*

---

**Full Changelog**: https://github.com/khoaiprovip123/ToolPC_ADB/compare/v2.4.0...v2.5.0
