# Security Policy — Xiaomi ADB Commander

## Nguyên tắc bảo mật đã áp dụng

### 1. Subprocess Safety
- **Không sử dụng `shell=True`** trong bất kỳ `subprocess` call nào
- Tất cả commands được truyền dưới dạng **list** (tránh command injection)
- Sử dụng `shlex.split()` để parse command strings an toàn
- **Timeout 30s** cho mọi subprocess call (tránh app bị treo)

### 2. Exception Handling
- Không có bare `except: pass` (tất cả đã chuyển sang `except Exception as e:`)
- Lỗi được log qua `LogManager` thay vì bị nuốt im lặng
- API key (`GEMINI_API_KEY`) được redact trong log files

### 3. Log Management
- **Log Rotation**: `RotatingFileHandler` với giới hạn 5 files × 5MB
- File permissions: `0o600` (chỉ owner đọc/ghi)
- Sensitive data tự động bị redact trước khi ghi

### 4. Worker Thread Safety
- Mỗi widget kiểm tra `isRunning()` trước khi tạo worker mới
- Worker cũ được `wait()` với timeout trước khi bị thay thế
- Tránh memory leak và race condition

### 5. UI Notifications
- Thông báo đi qua `LogManager.log()` → `NotificationCenter`
- Không sử dụng `QMessageBox` trực tiếp (trừ interactive dialogs)

## Báo cáo lỗ hổng
Nếu phát hiện vấn đề bảo mật, vui lòng tạo Issue trên GitHub với tag `security`.
