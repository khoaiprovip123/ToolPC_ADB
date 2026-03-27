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
- [x] **[P1]** Fix lệch mutex giữa runtime (`XiaomiADBCommanderMutex_v4`) và installer (`XiaomiADBCommanderMutex`)
- [x] **[P1]** Thay `terminate()` bằng `requestInterruption()` trong luồng đóng app
- [x] **[P1]** Sửa lỗi `TypeError` khi gọi `shell(log_error=True)` trên toàn hệ thống
- [x] **[P1]** Loại bỏ 800+ dòng Dead Code dư thừa

### Phase 2: Architecture & Engine
- [x] **[P2]** Thêm `ADBResult` struct hoàn chỉnh cho `execute_result()` / `shell_result()`
- [x] **[P2]** Sửa lỗi dọn rác (App Cache: `999G`, Telegram: quoted paths, Dex: fallback)
- [x] **[P2]** Đồng bộ `ThemeManager` cho toàn bộ widget (Fix Dark Mode)

### Phase 3: UX & Feature Expansion
- [x] **[P3]** **AIO Optimizer 3.0**: Chuyển sang layout 3-Tab ngang (Hiển Thị / Hiệu Năng / Hệ Thống)
- [x] **[P3]** **Sidebar 2.0**: Phân nhóm công cụ thông minh (⚡ Hiệu năng / 📢 Ứng dụng / 🌐 Hệ thống / 🛠️ Hỗ trợ)
- [x] **[P3]** **Debloater Pro**: Filter an toàn, Chọn nhanh (Safe-only), Progress Monitoring
- [ ] **[P3]** Chốt `config.yaml` là config runtime trung tâm
- [ ] **[P3]** Tách text UI ra resource map `{vi, en}` để hỗ trợ i18n sau này

---

## 📝 Sprint hiện tại
1. **Xiaomi Tools Suite 2.0 (Refactor & UI)** — ✅ Hoàn thành (2026-03-27)
2. **Cleaner & ADB Engine Fixes** — ✅ Hoàn thành (2026-03-27)
3. **P3 items (config, i18n, test suite)** — (To Do)
---

## 📚 Tài liệu tham chiếu
- Chi tiết kỹ thuật ADBManager: [`docs/adb_manager_spec.md`](adb_manager_spec.md)
- Build instructions: [`docs/build.md`](build.md)
- Hướng dẫn sử dụng: [`docs/user_guide.md`](user_guide.md)
