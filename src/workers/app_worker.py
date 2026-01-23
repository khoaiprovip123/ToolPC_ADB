from PySide6.QtCore import QThread, Signal
from typing import List, Optional
import os
import re
import shutil
import time
from src.data.app_data import AppInfo

class InstallerThread(QThread):
    """Background thread for installing apps"""
    progress = Signal(str) # Status message
    finished = Signal(bool, str) # Success, Message
    
    def __init__(self, adb_manager, paths: List[str], is_split: bool = False, cleanup_paths: List[str] = None):
        super().__init__()
        self.adb = adb_manager
        self.paths = paths
        self.is_split = is_split
        self.cleanup_paths = cleanup_paths or []
        
    def run(self):
        try:
            if not self.paths:
                self.finished.emit(False, "No files provided")
                return

            if self.is_split:
                # Install Multiple (Split APKs)
                self.progress.emit("Đang đẩy file lên thiết bị...")
                remote_paths = []
                for local_path in self.paths:
                    fname = os.path.basename(local_path)
                    remote = f"/data/local/tmp/{fname}"
                    self.adb.push_file(local_path, remote)
                    remote_paths.append(remote)
                
                self.progress.emit("Đang cài đặt (Split APKs)...")
                
                # Use 'install-multiple' directly via shell if possible, 
                # but 'pm install-create' session flow is more standard for split apks.
                
                # 1. Create Session
                session_out = self.adb.shell("pm install-create -r") 
                session_id = 0
                match = re.search(r'(\d+)', session_out)
                if match: 
                    session_id = match.group(1)
                else: 
                    # If regex fails, try to parse cleaner or just fail
                    raise Exception(f"Failed to create install session: {session_out}")
                
                # 2. Write APKs to session
                total = len(remote_paths)
                for i, remote in enumerate(remote_paths):
                    self.progress.emit(f"Writing apk {i+1}/{total}...")
                    # Get size from local file to be safe, or remote? Local is safer for match.
                    size = os.path.getsize(self.paths[i])
                    self.adb.shell(f"pm install-write -S {size} {session_id} {i}.apk {remote}")
                
                # 3. Commit
                self.progress.emit("Committing session...")
                res = self.adb.shell(f"pm install-commit {session_id}")
                
                # Cleanup Remote
                for remote in remote_paths:
                    self.adb.shell(f"rm {remote}")
                    
                if "Success" in res:
                    self.finished.emit(True, "Cài đặt thành công!")
                else:
                    self.finished.emit(False, f"Lỗi: {res}")
            
            else:
                # Single APK
                for path in self.paths:
                    self.progress.emit(f"Đang cài đặt {os.path.basename(path)}...")
                    # Secure install execution with downgrade and replace flags
                    try:
                        res = self.adb.execute(["install", "-r", "-d", "-g", path])
                    except Exception as install_error:
                        res = str(install_error)
                    
                    if "Success" in res:
                        continue
                    else:
                        # Friendly Error Handling
                        msg = f"Lỗi khi cài {os.path.basename(path)}: {res}"
                        
                        if "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in res:
                            # Extract package name if possible (often not in output, but we can try)
                            # Or just use the known package if we entered via a mode that knows it.
                            # Since we are installing an APK, we might need to parse the APK to get the package name,
                            # OR we rely on the error message which sometimes contains it.
                            # Standard error: "signatures do not match the previously installed version; ignoring!"
                            # It doesn't always give the package name.
                            
                            # Better approach: We need the package name to uninstall.
                            # We can try to use aapt or a helper to get package name from the APK file.
                            # But we don't have aapt easily. 
                            # Alternative: Let the UI handle the "Reinstall" logic by just signaling CONFLICT.
                            # The UI might ask the worker to "Get Package Name" first?
                            
                            # Let's try to get package name from the file using build-tools if available?
                            # Or simpler: The user knows what they are installing? No, we need to uninstall the SPECIFIC package.
                            
                            # Let's use aapt dump badging if possible, OR use the 'aapt' from the adb directory?
                            # Actually, we can use the 'AppScanner' logic to parse? No that's for installed.
                            
                            # Quick hack: parsing the error MIGHT show "Existing package com.foo.bar signatures..."
                            # Output in previous turn: "Failure [INSTALL_FAILED_UPDATE_INCOMPATIBLE: Existing package com.miui.home signatures...]"
                            # YES! It contains the package name.
                            
                            match = re.search(r'Existing package ([a-zA-Z0-9_\.]+) signatures', res)
                            if match:
                                pkg = match.group(1)
                                msg = f"[CONFLICT:{pkg}]"
                            else:
                                # If we can't find it, we can't auto-uninstall. Fallback to generic text.
                                msg = (
                                    "Lỗi: Chữ ký không khớp (Signature Mismatch).\n"
                                    "Không thể xác định tên gói ứng dụng để gỡ tự động.\n"
                                    "Vui lòng gỡ thủ công phiên bản cũ trước."
                                )

                        elif "INSTALL_FAILED_VERSION_DOWNGRADE" in res:
                            msg = "Lỗi: Phiên bản cài đặt thấp hơn phiên bản hiện có (Downgrade blocked)."
                            
                        self.finished.emit(False, msg)
                        return
                
                self.finished.emit(True, "Cài đặt thành công!")
                
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            # Cleanup Local Temp Files
            for path in self.cleanup_paths:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    elif os.path.isfile(path):
                        os.remove(path)
                except:
                    pass



class BackupThread(QThread):
    """
    Super Backup Worker
    Supports:
    - Single APK
    - Split APKs (saved as folder)
    - App Data (via adb backup)
    """
    progress = Signal(str)
    finished = Signal(bool, str) # Success, Summary
    
    def __init__(self, adb_manager, apps: List[AppInfo], dest_folder: str, backup_apk: bool = True, backup_data: bool = False):
        super().__init__()
        self.adb = adb_manager
        self.apps = apps
        self.dest_folder = dest_folder
        self.backup_apk = backup_apk
        self.backup_data = backup_data
        self._is_running = True
        
    def run(self):
        try:
            total = len(self.apps)
            success_count = 0
            fail_count = 0
            
            # Create timestamped folder for this batch
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_folder = os.path.join(self.dest_folder, f"Backup_{timestamp}")
            os.makedirs(batch_folder, exist_ok=True)
            
            # 1. OPTIONAL: Data Backup (Batch)
            if self.backup_data:
                self.progress.emit("⏳ Đang chuẩn bị sao lưu dữ liệu (ADB Backup)...")
                packages = [app.package for app in self.apps]
                backup_file = os.path.join(batch_folder, "FullData.ab")
                
                self.progress.emit("⚠️ CẢNH BÁO: Kiểm tra màn hình điện thoại!\nNhấn 'Back up my data' để cho phép sao lưu.")
                
                # Command: adb backup -f file.ab -apk -obb -shared -all (if all) or specific packages
                # We intentionally DON'T use -apk here if we are pulling AKPs manually, 
                # but 'adb backup' is often safer for compact restore. 
                # Let's use -noapk to just get data, since we handle APKs separately and better.
                cmd = ["backup", "-f", backup_file, "-noapk", "-obb", "-shared"] + packages
                
                # This blocks until user accepts or timeout
                res = self.adb.execute(cmd, timeout=300) 
                
                if os.path.exists(backup_file) and os.path.getsize(backup_file) > 1024:
                    self.progress.emit("✅ Sao lưu dữ liệu thành công!")
                else:
                    self.progress.emit("⚠️ Sao lưu dữ liệu có thể đã bị hủy hoặc rỗng.")

            # 2. APK Backup (Individual Loop)
            if self.backup_apk:
                for i, app in enumerate(self.apps):
                    if not self._is_running: break
                    
                    self.progress.emit(f"📦 Đang trích xuất ({i+1}/{total}): {app.name}...")
                    
                    try:
                        # Get paths
                        out = self.adb.shell(f"pm path {app.package}")
                        paths = []
                        for line in out.splitlines():
                            if line.startswith("package:"):
                                paths.append(line.replace("package:", "").strip())
                        
                        if not paths:
                            fail_count += 1
                            continue 
                        
                        # Determine Destination
                        # Group by app name for cleanliness
                        app_save_dir = os.path.join(batch_folder, f"{app.name}_{app.package}")
                        os.makedirs(app_save_dir, exist_ok=True)
                        
                        if len(paths) == 1:
                            # Single APK
                            src = paths[0]
                            dst = os.path.join(app_save_dir, "base.apk")
                            result = self.adb.pull_file(src, dst)
                            if "error" in result.lower(): raise Exception(result)
                            
                        else:
                            # Split APKs - Pull all parts
                            for src in paths:
                                fname = os.path.basename(src)
                                dst = os.path.join(app_save_dir, fname)
                                result = self.adb.pull_file(src, dst)
                                if "error" in result.lower(): raise Exception(result)
                                
                        # Save metadata
                        with open(os.path.join(app_save_dir, "info.txt"), "w", encoding="utf-8") as f:
                            f.write(f"Name: {app.name}\nPackage: {app.package}\nVersion: {app.version}\nType: Split" if len(paths)>1 else "Type: Single")
                            
                        success_count += 1
                        
                    except Exception as e:
                        print(f"Failed to backup {app.package}: {e}")
                        fail_count += 1

            self.finished.emit(True, f"🎉 Hoàn tất!\n\nThành công: {success_count}\nThất bại: {fail_count}\n\nLưu tại: {batch_folder}")
            
        except Exception as e:
            self.finished.emit(False, str(e))
            
        self._is_running = False


class RestoreThread(QThread):
    """Background thread for restoring system apps"""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, adb_manager, packages: List[str]):
        super().__init__()
        self.adb = adb_manager
        self.packages = packages
        self._is_running = True
        
    def run(self):
        try:
            total = len(self.packages)
            success_count = 0
            
            for i, package in enumerate(self.packages):
                if not self._is_running: break
                
                self.progress.emit(f"Đang phục hồi ({i+1}/{total}): {package}...")
                
                # Command: cmd package install-existing <package>
                res = self.adb.shell(f"cmd package install-existing {package}")
                
                if "installed" in res.lower():
                    success_count += 1
                else:
                    # Fallback for older android
                    res = self.adb.shell(f"pm install-existing {package}")
                    if "installed" in res.lower():
                        success_count += 1
            
            self.finished.emit(True, f"Đã phục hồi {success_count}/{total} ứng dụng!")
            
        except Exception as e:
            self.finished.emit(False, str(e))

    def stop(self):
        self._is_running = False


class AppScanner(QThread):
    """Background thread for scanning apps"""
    
    progress = Signal(int, int)  # current, total
    app_found = Signal(object)  # AppInfo
    finished = Signal(list)  # List[AppInfo]
    error = Signal(str)
    
    def __init__(self, adb_manager, app_type: str = "all"):
        super().__init__()
        self.adb = adb_manager
        self.app_type = app_type  # all, user, system
        self._is_running = True
    
    def run(self):
        """Scan for apps"""
        try:
            apps = []
            
            # 1. Fetch Disabled Packages List (for installed apps)
            disabled_output = self.adb.shell("pm list packages -d")
            disabled_pkgs = set()
            for line in disabled_output.splitlines():
                if line.startswith("package:"):
                    disabled_pkgs.add(line.replace("package:", "").strip())
            
            # 2. Comprehensive Scan OR Specific Scan
            # The user wants a "Scan Once" mechanism. So 'all' should really mean ALL (Installed + Archived).
            
            if self.app_type == "all":
                 # Scan EVERYTHING
                 # Get Currently Installed (for Archive check)
                 installed_out = self.adb.shell("pm list packages")
                 installed_pkgs = set()
                 for line in installed_out.splitlines():
                     line = line.strip()
                     if line.startswith("package:"):
                         installed_pkgs.add(line.replace("package:", "").strip())
                 
                 # Get Full List including uninstalled
                 cmd = "pm list packages -u -f"
                 output = self.adb.shell(cmd)
                 
                 lines = output.strip().split('\n')
                 total = len(lines)
                 
                 for i, line in enumerate(lines):
                    if not self._is_running: break
                    
                    # Periodic UI update for large lists
                    if i % 10 == 0: self.progress.emit(i + 1, total)
                    
                    try:
                        line = line.strip()
                        if not line: continue
                        
                        match = re.match(r'package:(.+)=(.+)', line)
                        if not match: continue
                        path, package = match.groups()
                        package = package.strip()
                        
                        # Determine Status
                        is_installed = package in installed_pkgs
                        is_system = '/system/' in path or '/vendor/' in path or '/product/' in path or '/apex/' in path
                        
                        # 3 Cases:
                        # 1. Installed User App
                        # 2. Installed System App
                        # 3. Uninstalled System App (Archived) -> is_installed=False, is_system=True
                        # 4. Uninstalled User App -> Usually gone completely, but if present, treat as Archived?
                        
                        if is_installed:
                            # It is installed. Check if enabled.
                            is_enabled = package not in disabled_pkgs
                            is_archived = False
                        else:
                            # Not installed aka Archived
                            # Use loose check: if it shows up in -u but not in regular, it's archived.
                            # But only care if it's System? User might want to restore user apps if kept data?
                            # For simplicity and safety, let's treat all non-installed as archived.
                            is_enabled = False # Not active
                            is_archived = True
                            
                        app_info = self._get_app_details_fast(package, path, is_enabled, is_archived)
                        app_info.is_system = is_system # Ensure system flag is correct based on path
                        
                        if app_info:
                            apps.append(app_info)
                            # self.app_found.emit(app_info) # Don't emit individual for bulk loaded list to save UI calls? Or emit for progress?
                            # Emitting 500 signals might freeze UI if not careful. Batching is better but let's stick to emit for live count.
                            self.app_found.emit(app_info)
                            
                    except Exception: continue

            else:
                # Specific legacy modes (if needed, but 'all' covers most)
                # Fallback to simple scan if requested specifically
                if self.app_type == "user": cmd = "pm list packages -3 -f"
                elif self.app_type == "system": cmd = "pm list packages -s -f"
                else: cmd = "pm list packages -f"
                
                output = self.adb.shell(cmd)
                lines = output.strip().split('\n')
                total = len(lines)
                
                for i, line in enumerate(lines):
                    if not self._is_running: break
                    self.progress.emit(i+1, total)
                    try:
                        match = re.match(r'package:(.+)=(.+)', line)
                        if not match: continue
                        path, package = match.groups()
                        is_enabled = package not in disabled_pkgs
                        app_info = self._get_app_details_fast(package, path, is_enabled)
                        if app_info:
                            apps.append(app_info)
                            self.app_found.emit(app_info)
                    except: continue

            self.finished.emit(apps)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def _get_app_details_fast(self, package: str, path: str, is_enabled: bool = True, is_archived: bool = False) -> Optional[AppInfo]:
        """Fast getter for list view"""
        # Heuristics for name
        name = package.split('.')[-1].title()
        is_system = '/system/' in path or '/vendor/' in path
        
        # Fetch Real Size and Date using valid path
        # Using ONE generic command to try to get info: 'stat -c "%s %Y" path'
        # To optimize, we might rely on cached lookup or batch, but for now individual query
        # per item is safer for correctness, though slower.
        # Speed optimization: Check if we have processed this pkg before? No state here.
        
        size = 0
        timestamp = 0
        
        try:
             # Fast stat
             # Check if path is valid on device (it comes from pm list)
             cmd = f"stat -c \"%s %Y\" {path}"
             out = self.adb.shell(cmd).strip()
             # output format: "123456 167890123" (Size Time)
             parts = out.split()
             if len(parts) >= 2:
                 size = int(parts[0])
                 timestamp = int(parts[1])
        except:
             pass

        return AppInfo(
            package=package,
            name=name,
            version="...",
            version_code=0,
            is_system=is_system,
            is_enabled=is_enabled,
            is_archived=is_archived,
            size=size,
            install_time=timestamp,
            update_time=timestamp,
            path=path
        )
    
    def stop(self):
        """Stop scanning"""
        self._is_running = False


class BatchInstallerThread(QThread):
    """
    Background thread for batch installing apps from files/folders
    Target: Restore from Backup
    """
    progress = Signal(str)
    finished = Signal(bool, str) # Success, Summary
    
    def __init__(self, adb_manager, items: List[str]):
        """
        items: List of absolute paths. 
               If path is directory -> Treat as Split APK (install-multiple)
               If path is file -> Treat as Single APK
        """
        super().__init__()
        self.adb = adb_manager
        self.items = items
        self._is_running = True
        
    def run(self):
        try:
            total = len(self.items)
            success = 0
            fail = 0
            
            for i, path in enumerate(self.items):
                if not self._is_running: break
                
                name = os.path.basename(path)
                self.progress.emit(f"🔄 Đang cài đặt ({i+1}/{total}): {name}...")
                
                res = ""
                if os.path.isdir(path):
                    # Split APK Install
                    apks = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.apk')]
                    if not apks:
                        fail += 1
                        continue
                        
                    # Push all
                    remote_paths = []
                    try:
                        for local_apk in apks:
                            fname = os.path.basename(local_apk)
                            remote = f"/data/local/tmp/{fname}"
                            self.adb.push_file(local_apk, remote)
                            remote_paths.append(remote)
                            
                        # Session Install
                        session_out = self.adb.shell("pm install-create -r")
                        session_id = 0
                        match = re.search(r'(\d+)', session_out)
                        if match:
                             session_id = match.group(1)
                        else:
                             raise Exception(f"Failed to create session: {session_out}")
                        
                        for idx, remote in enumerate(remote_paths):
                            size = os.path.getsize(apks[idx])
                            self.adb.shell(f"pm install-write -S {size} {session_id} {idx}.apk {remote}")
                            
                        res = self.adb.shell(f"pm install-commit {session_id}")
                        
                        # Cleanup
                        for remote in remote_paths: self.adb.shell(f"rm {remote}")
                        
                        if "Success" in res:
                            success += 1
                        else:
                            fail += 1
                            
                    except Exception as e:
                        res = str(e)
                        fail += 1
                else:
                    # Single APK
                    res = self.adb.execute(["install", "-r", path])
                    if "Success" in res:
                         success += 1
                    else:
                         fail += 1
            
            self.finished.emit(True, f"✅ Đã khôi phục xong!\nThành công: {success}\nThất bại: {fail}")
            
        except Exception as e:
            self.finished.emit(False, str(e))
        
        self._is_running = False

    def stop(self):
        self._is_running = False
