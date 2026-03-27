# Project Plan & Roadmap — Xiaomi ADB Commander

## 📍 Tình trạng hiện tại (v2.5.5.5)
- [x] Khởi tạo dự án & cấu trúc thư mục
- [x] ADBManager core + device lifecycle
- [x] Dashboard UI + real-time polling
- [x] App Manager (scan, uninstall, cascade strategy)
- [x] File Manager (push/pull, image preview, context menu)
- [x] Xiaomi Suite (Debloater, AIO Optimizer, Expert Tweaks, Cleaner, Battery)
- [x] Dev Tools (Script Engine, Wireless Debug, DNS, Shizuku, Permission)
- [x] Auto-Update via GitHub Releases
- [x] Build pipeline: PyInstaller + Inno Setup
- [x] Log rotation, Security baseline
- [x] Bộ template quản lý tài liệu (context, agent, plan, changelog)

---

## 🚀 Roadmap

### Phase 1: Stabilization (Ưu tiên cao)
- [x] **[P1]** Fix lệch mutex giữa runtime (`XiaomiADBCommanderMutex_v4`) và installer (`XiaomiADBCommanderMutex`) → đồng bộ 1 tên duy nhất
- [x] **[P1]** Thay `terminate()` bằng `requestInterruption()` + `wait(timeout)` trong luồng đóng app (`main_window.py:751, 755`)
- [x] **[P2]** Bổ sung log warning cho silent failures trong startup update check (`main_window.py:858, 867, 889`)
- [x] **[P2]** Sửa typo `'sideloade'` → `'sideload'` trong `adb_manager.py:80`
- [x] **[P2]** Làm rõ interface `ADBManager.shell()` — remove `*args, **kwargs` không dùng

### Phase 2: Architecture Quality
- [x] **[P2]** Chuẩn hóa `ADBManager.shell()` — đã xóa *args/**kwargs để fail-fast
- [ ] **[P2]** Chuẩn hóa `ADBManager` trả `ADBResult (ok, stdout, stderr, code)` thay vì plain string
- [ ] **[P3]** Chốt `config.yaml` là config runtime trung tâm (hoặc dùng `QSettings` hoàn toàn — tránh 2 nguồn)
- [ ] **[P3]** Tách text UI ra resource map `{vi, en}` để hỗ trợ i18n sau này
- [ ] **[P3]** Bổ sung test suite cơ bản: parser/version/update + mock ADB

### Phase 3: Feature Expansion
- [ ] ☁️ Cloud Sync hoàn chỉnh (Google Drive / Dropbox)
- [ ] 🔌 Plugin System — đăng ký plugin từ thư mục ngoài
- [ ] 📋 Logcat Viewer nâng cao (filter regex, export)
- [ ] 🌐 Real-time OTA Downloader với mirror list

---

## 📝 Sprint hiện tại
1. **Dọn dẹp và tổ chức lại tài liệu** — ✅ Hoàn thành (2026-03-27)
2. **Fix Phase 1 & 2 (P1 + P2 issues)** — ✅ Hoàn thành (2026-03-27)
3. **Fix Phase 2 còn lại (ADBResult, P3 items)** — (To Do)

---

## 💡 Backlog / Ý tưởng
- Màn hình Mirroring nâng cao (touch annotation)
- Hỗ trợ Samsung OneUI debloat list
- CLI mode (chạy không cần GUI)
- Smoke test script tự động chạy trước mỗi release

---

## 📚 Tài liệu tham chiếu
- Chi tiết kỹ thuật ADBManager: [`docs/adb_manager_spec.md`](adb_manager_spec.md)
- Build instructions: [`docs/build.md`](build.md)
- Hướng dẫn sử dụng: [`docs/user_guide.md`](user_guide.md)
