# 📖 HƯỚNG DẪN SỬ DỤNG XIAOMI ADB COMMANDER
*Phiên bản 2.3.0*

Chào mừng bạn đến với bộ công cụ quản lý và tối ưu hóa mạnh mẽ dành cho thiết bị Android và Xiaomi.

---

## 🚀 1. Kết nối Thiết bị
### Kết nối qua USB
1.  Bật **Tùy chọn nhà phát triển**:
    *   `Cài đặt` -> `Giới thiệu điện thoại` -> Chạm 7 lần vào `Phiên bản MIUI`.
2.  Bật **Gỡ lỗi USB** trong `Tùy chọn nhà phát triển`.
3.  *(Xiaomi)* Bật **Gỡ lỗi USB (Cài đặt bảo mật)**.
4.  Cắm cáp, nhấn "Cho phép" trên điện thoại.

### Kết nối qua Wi-Fi
1.  Vào tab **Wireless Debug**.
2.  **Android 11+**:
    *   Trên điện thoại: `Gỡ lỗi không dây` -> `Ghép nối bằng mã`.
    *   Trên App: Nhập IP, Port, Code -> Nhấn `Ghép đôi` -> Sau đó nhập IP/Port kết nối -> `Kết nối`.
3.  **Android <11**: Cắm cáp -> Nhấn `Mở cổng 5555` -> Rút cáp -> Nhập IP -> `Kết nối`.

---

## 🛠 2. Bộ công cụ Xiaomi (Xiaomi Tools)
*Giao diện mới dạng Sidebar giúp truy cập nhanh các tính năng.*

### 🧹 Gỡ Ứng Dụng (Debloater)
1.  Vào mục **Gỡ Ứng Dụng** ở thanh bên trái.
2.  Tích chọn nhóm ứng dụng (Quảng cáo, Rác hệ thống...) hoặc tìm kiếm ứng dụng cụ thể.
3.  Nhấn **🗑️ Gỡ bỏ ngay**.

### ✨ Tối Ưu Hệ Thống (AIO)
1.  Vào mục **Tối Ưu Hệ Thống**.
2.  Sử dụng các thẻ chức năng: Tần số quét (Hz), Animation, Blur hiệu ứng, Dark Mode...
3.  Nhấn **Quét Hệ Thống** ở đầu trang để tự động hóa toàn bộ.

### 💀 Tối Ưu Chuyên Sâu (Expert)
*Chỉ dành cho người dùng có kinh nghiệm.*
1.  Vào mục **Tối Ưu Chuyên Sâu**.
2.  Kích hoạt các tính năng: Ép xung CPU/GPU Level 6, Fix RAM Phantom, Tối ưu cảm ứng HyperOS.

### 🔔 Fix Thông Báo
1.  Vào mục **Fix Thông Báo 🔔**.
2.  Chọn các ứng dụng bị trễ tin nhắn (Zalo, Messenger, Telegram...).
3.  Tích chọn các option fix (Auto start, Battery No Limit) và nhấn **🚀 Bắt đầu tối ưu**.

---

## 📦 3. Quản lý Ứng dụng & APK Analyzer
### Quản lý Apps
1.  Menu **Quản lý Ứng dụng**.
2.  Kéo thả APK để cài đặt.
3.  Chọn ứng dụng -> Nhấn **Gỡ cài đặt** hoặc **Backup**.

### 🔍 APK Analyzer (Mới)
1.  Vào **Dev Tools** -> **APK Analyzer**.
2.  Kéo thả file `.apk` vào khu vực hình hộp.
3.  Xem chi tiết: Tên gói, Phiên bản, SDK, Quyền hạn.

---

## ⚡ 4. Script / Macro Engine (Mới)
*Tự động hóa thao tác không cần Root.*
1.  Vào **Dev Tools** -> **Script Engine**.
2.  Tạo kịch bản bằng các nút: **Click**, **Swipe**, **Text**, **Wait**.
3.  Nhấn **▶ CHẠY MACRO** để thực thi.
4.  Lưu lại (`.json`) để dùng sau.

---

## 📡 5. Shizuku Manager
1.  Vào **Dev Tools** -> **Wireless Debug**.
2.  Nhấn **Start Shizuku** để kích hoạt dịch vụ Shizuku.

---

## ❓ FAQ
*   **Lỗi Permission Denial?**: Bật "Gỡ lỗi USB (Bảo mật)".
*   **Không thấy thiết bị?**: Kiểm tra Driver hoặc Cáp USB.
