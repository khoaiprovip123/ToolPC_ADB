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
                    # Secure install execution
                    res = self.adb.execute(["install", "-r", path])
                    
                    if "Success" in res:
                        continue
                    else:
                        self.finished.emit(False, f"Lỗi khi cài {os.path.basename(path)}: {res}")
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
    """Background thread for backing up apps"""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, adb_manager, apps: List[AppInfo], dest_folder: str, mode: str = "apk"):
        super().__init__()
        self.adb = adb_manager
        self.apps = apps
        self.dest_folder = dest_folder
        self.mode = mode # 'apk' or 'data'
        self._is_running = True
        
    def run(self):
        try:
            total = len(self.apps)
            success_count = 0
            
            if self.mode == "data":
                # ADB Backup Mode (.ab file)
                packages = [app.package for app in self.apps]
                pkg_str = " ".join(packages)
                timestamp = int(time.time())
                
                # Single backup file for all (or loop?)
                # 'adb backup' for multiple packages creates one .ab file
                backup_file = os.path.join(self.dest_folder, f"backup_{timestamp}.ab")
                
                self.progress.emit("⚠️ Đang chờ xác nhận TRÊN ĐIỆN THOẠI...\nVui lòng mở khóa và nhấn 'Back up my data'!")
                
                # Command: adb backup -apk -shared -all -f file.ab (for all)
                # For specific: adb backup -apk -shared -f file.ab pkg1 pkg2
                # Including -shared to try and get external data (images)
                
                cmd_list = ["backup", "-apk", "-shared", "-f", backup_file] + packages
                res = self.adb.execute(cmd_list, timeout=300) # Long timeout for user interaction
                
                if "error" not in res.lower():
                    self.finished.emit(True, f"Đã gửi lệnh Backup Data!\nFile: {os.path.basename(backup_file)}\n\nLưu ý: Kiểm tra file .ab có dung lượng > 0KB không.")
                else:
                    self.finished.emit(False, f"Lỗi: {res}")
                return

            # APK Mode (Default)
            for i, app in enumerate(self.apps):
                if not self._is_running: break
                
                self.progress.emit(f"Đang sao lưu ({i+1}/{total}): {app.name}...")
                
                # Get paths
                out = self.adb.shell(f"pm path {app.package}")
                paths = []
                for line in out.splitlines():
                    if line.startswith("package:"):
                        paths.append(line.replace("package:", "").strip())
                
                if not paths:
                    continue # Skip if no path found
                
                if len(paths) == 1:
                    src = paths[0]
                    dst_name = f"{app.package}_{app.version_code}.apk" if app.version_code else f"{app.package}.apk"
                    dst = os.path.join(self.dest_folder, dst_name)
                    self.adb.pull_file(src, dst)
                else:
                    # Split APKs
                    save_dir = os.path.join(self.dest_folder, f"{app.package}_backup")
                    os.makedirs(save_dir, exist_ok=True)
                    
                    for src in paths:
                        fname = os.path.basename(src)
                        dst = os.path.join(save_dir, fname)
                        self.adb.pull_file(src, dst)
                        
                success_count += 1
            
            self.finished.emit(True, f"Đã sao lưu hoàn tất {success_count}/{total} ứng dụng!")
            
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
