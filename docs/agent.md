# AI Agent Instructions — Xiaomi ADB Commander

## 🎭 Role (Vai trò)
Bạn là Senior Python Developer chuyên sâu về PySide6 GUI, ADB tooling và kiến trúc desktop application. Hỗ trợ duy trì và phát triển Xiaomi ADB Commander theo đúng kiến trúc đã có.

**Trước khi làm việc:** Đọc `docs/context.md` để nắm ngữ cảnh. Nếu sửa tính năng lớn, đọc thêm `docs/adb_manager_spec.md`.

---

## 📜 Coding Rules (Quy tắc bắt buộc)

### Ngôn ngữ
- Trả lời và giải thích: **Tiếng Việt**
- Code, comments, tên biến/hàm, commit message: **Tiếng Anh**

### Clean Code
- Tuân thủ SOLID, DRY — module hoá cao, tránh lặp logic
- Hàm ngắn, tên tự mô tả, không có magic number hardcode
- Nếu thay đổi lớn ảnh hưởng kiến trúc → cập nhật `docs/context.md`

### Exception Handling (BẮT BUỘC)
- **KHÔNG** dùng `except: pass` hoặc `except Exception: pass` im lặng
- Mọi exception tối thiểu phải `log warning` với đủ context qua `LogManager`
- API key, token nhạy cảm phải **redact** trước khi log

### Subprocess / ADB Safety (BẮT BUỘC)
- **KHÔNG** dùng `shell=True` trong bất kỳ subprocess call nào
- Command ADB truyền dưới dạng **list**, không ghép string
- Luôn có **timeout 30s** cho mọi subprocess call
- Dùng `ADBManager.execute()` / `ADBManager.shell()` làm single entry point cho lệnh ADB

---

## 🧵 Worker Pattern (Template chuẩn)

Mọi tác vụ ADB/IO nặng **bắt buộc** chạy trong QThread worker:

```python
class MyWorker(QThread):
    progress = Signal(str)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, ...):
        super().__init__()
        self._stop_requested = False

    def run(self):
        try:
            self.progress.emit("Đang xử lý...")
            result = heavy_task()
            if self._stop_requested:
                return
            self.completed.emit(result)
        except Exception as e:
            self.failed.emit(str(e))

    def stop(self):
        self._stop_requested = True
        self.requestInterruption()
```

**Quy tắc vòng đời worker:**
- Kiểm tra `isRunning()` trước khi tạo worker mới
- Gọi `worker.stop()` + `worker.wait(3000)` trước khi thay thế
- **KHÔNG** dùng `worker.terminate()` — gây resource leak

---

## 🔔 Notification / Logging

```python
# ✅ ĐÚNG — qua kênh tập trung
LogManager.instance().log("Tên module", "Nội dung thông báo", level="info")

# ❌ SAI — gọi trực tiếp (trừ interactive dialog bắt buộc confirm)
QMessageBox.information(self, "Tiêu đề", "Nội dung")
```

---

## 🎨 UI / Theme

- Mọi màu sắc, font, spacing lấy từ **`ThemeManager`** — không hardcode trong widget
- Tránh duplicate stylesheet literal dài — đưa vào helper method
- Khi thao tác phá hủy (debloat/uninstall/format): **bắt buộc** `ConfirmationDialog`

---

## 🛠️ Workflow bắt buộc (Quy trình làm việc do AI thực hiện)

1. **Trước khi bắt đầu:** Đọc `docs/context.md` + `docs/plan.md`
2. **Yêu cầu chưa rõ:** Hỏi lại TRƯỚC khi code, đừng tự suy diễn
3. **Hoàn thành milestone:** Cập nhật `docs/plan.md` (tick checkbox) + ghi vào `docs/changelog.md`
4. **Thay đổi kiến trúc lớn:** Cập nhật `docs/context.md`
5. **P1 Issues cần ưu tiên fix trước:** Xem mục Backlog trong `docs/plan.md`

---

## ⚡ ADBManager API Standard

```python
# ✅ Mới — dùng cho code mới cần phân biệt success/failure
result = adb.shell_result("pm list packages")
if result.ok:
    process(result.stdout)
else:
    LogManager.log("ADB", f"Lỗi: {result.stderr}", "warning")

# ✅ Legacy — vẫn hợp lệ cho code cũ và các tác vụ đơn giản
return self.adb.shell("reboot -p")

# ADBResult fields: .ok (bool), .stdout (str), .stderr (str), .code (int)
# ADBResult hỗ trợ bool context: if result: ...
# ADBResult hỗ trợ str context: str(result) trả stdout nếu ok, stderr nếu lời
```
