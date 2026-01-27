from PySide6.QtCore import QThread, Signal
from typing import List, Optional
import os
import re
import shutil
import time
from src.data.app_data import AppInfo

class InstallerThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)
    
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
                self.progress.emit("Pushing files...")
                remote_paths = []
                for local_path in self.paths:
                    fname = os.path.basename(local_path)
                    remote = f"/data/local/tmp/{fname}"
                    self.adb.push_file(local_path, remote)
                    remote_paths.append(remote)
                
                self.progress.emit("Installing Split APKs...")
                session_out = self.adb.shell("pm install-create -r") 
                session_id = 0
                match = re.search(r'(\d+)', session_out)
                if match: session_id = match.group(1)
                else: raise Exception(f"Failed to create session: {session_out}")
                
                total = len(remote_paths)
                for i, remote in enumerate(remote_paths):
                    self.progress.emit(f"Writing apk {i+1}/{total}...")
                    size = os.path.getsize(self.paths[i])
                    self.adb.shell(f"pm install-write -S {size} {session_id} {i}.apk {remote}")
                
                self.progress.emit("Committing...")
                res = self.adb.shell(f"pm install-commit {session_id}")
                
                for remote in remote_paths: self.adb.shell(f"rm {remote}")
                    
                if "Success" in res: self.finished.emit(True, "Success!")
                else: self.finished.emit(False, f"Error: {res}")
            
            else:
                for path in self.paths:
                    self.progress.emit(f"Installing {os.path.basename(path)}...")
                    try:
                        res = self.adb.execute(["install", "-r", "-d", "-g", path])
                    except Exception as ie: res = str(ie)
                    
                    if "Success" not in res:
                         self.finished.emit(False, f"Install Failed: {res}")
                         return
                self.finished.emit(True, "Success!")
                
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            for path in self.cleanup_paths:
                try:
                    if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
                    elif os.path.isfile(path): os.remove(path)
                except: pass

class BackupThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)
    
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
            success = 0
            fail = 0
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_folder = os.path.join(self.dest_folder, f"Backup_{timestamp}")
            os.makedirs(batch_folder, exist_ok=True)
            
            if self.backup_data:
                self.progress.emit("Backing up data (Check phone)...")
                packages = [app.package for app in self.apps]
                backup_file = os.path.join(batch_folder, "FullData.ab")
                cmd = ["backup", "-f", backup_file, "-noapk", "-obb", "-shared"] + packages
                self.adb.execute(cmd, timeout=300)
                if os.path.exists(backup_file): self.progress.emit("Data backup done.")
            
            if self.backup_apk:
                for i, app in enumerate(self.apps):
                    if not self._is_running: break
                    self.progress.emit(f"Extracting ({i+1}/{total}): {app.name}...")
                    try:
                        out = self.adb.shell(f"pm path {app.package}")
                        paths = [l.replace("package:", "").strip() for l in out.splitlines() if l.startswith("package:")]
                        if not paths: raise Exception("No path found")
                        
                        app_dir = os.path.join(batch_folder, f"{app.name}_{app.package}")
                        os.makedirs(app_dir, exist_ok=True)
                        
                        for src in paths:
                            dst = os.path.join(app_dir, os.path.basename(src) if len(paths)>1 else "base.apk")
                            self.adb.pull_file(src, dst)
                        success += 1
                    except: fail += 1
            
            self.finished.emit(True, f"Backup Complete.\nSuccess: {success}, Failed: {fail}\nSaved to: {batch_folder}")
        except Exception as e:
            self.finished.emit(False, str(e))
        self._is_running = False

class RestoreThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)
    def __init__(self, adb_manager, packages):
        super().__init__()
        self.adb = adb_manager
        self.packages = packages
        self._is_running = True
    def run(self):
        try:
             count = 0
             for pkg in self.packages:
                 if not self._is_running: break
                 self.progress.emit(f"Restoring {pkg}...")
                 self.adb.shell(f"cmd package install-existing {pkg}")
                 count += 1
             self.finished.emit(True, f"Restored {count} apps.")
        except Exception as e: self.finished.emit(False, str(e))
    def stop(self): self._is_running = False

class AppScanner(QThread):
    progress = Signal(int, int)
    app_found = Signal(object)
    finished = Signal(list)
    error = Signal(str)
    def __init__(self, adb_manager, app_type="all"):
        super().__init__()
        self.adb = adb_manager
        self._is_running = True
    def run(self):
        try:
            print("[AppScanner] Starting...")
            disabled = set()
            
            # Check for disabled packages
            try:
                for line in self.adb.shell("pm list packages -d").splitlines():
                    if line.startswith("package:"): disabled.add(line[8:].strip())
                print(f"[AppScanner] Found {len(disabled)} disabled packages")
            except: pass
            
            # Note: We no longer need to check suspended packages
            # because we now use 'pm uninstall -k --user 0' which is tracked by pm list packages
            
            installed = set()
            try:
                 for line in self.adb.shell("pm list packages").splitlines():
                    if line.startswith("package:"): installed.add(line[8:].strip())
            except: pass
            
            output = self.adb.shell("pm list packages -u -f")
            if not output: 
                self.finished.emit([])
                return
            
            lines = output.strip().split('\n')
            result = []
            for i, line in enumerate(lines):
                if not self._is_running: break
                if i % 50 == 0: self.progress.emit(i, len(lines))
                
                line = line.strip()
                if not line.startswith("package:"): continue
                
                content = line[8:]
                split_idx = content.rfind('=')
                if split_idx == -1:
                    path = ""
                    pkg = content
                else:
                    path = content[:split_idx]
                    pkg = content[split_idx+1:]
                
                is_inst = pkg in installed
                is_sys = '/system/' in path or '/vendor/' in path or '/product/' in path or '/apex/' in path or '/odm/' in path
                is_en = pkg not in disabled if is_inst else False
                is_arch = not is_inst
                
                result.append(AppInfo(pkg, pkg.split('.')[-1].title(), "", 0, is_sys, is_en, is_arch, 0, 0, 0, path))
                
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    def stop(self): self._is_running = False

class SmartAppActionThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, adb_manager, apps: List[AppInfo], mode: str):
        super().__init__()
        self.adb = adb_manager
        self.apps = apps
        self.mode = mode
        self._is_running = True

    def run(self):
        print(f"DEBUG: SmartAppActionThread.run started. Mode={self.mode}, Apps={[a.package for a in self.apps]}")
        try:
            total = len(self.apps)
            success_count = 0
            failed = []
            
            for i, app in enumerate(self.apps):
                if not self._is_running: break
                self.progress.emit(f"Handling ({i+1}/{total}): {app.name}...")
                
                result_msg = ""
                is_ok = False
                
                if self.mode == "uninstall":
                    # Method 1: Standard Uninstall
                    res = self.adb.shell(f"pm uninstall {app.package}")
                    if "Success" in res: is_ok = True
                    else:
                        # Method 2: Uninstall User (Keep Data/System)
                        res = self.adb.shell(f"pm uninstall -k --user 0 {app.package}")
                        if "Success" in res: is_ok = True
                
                elif self.mode == "disable":
                    # AGGRESSIVE CASCADE for Xiaomi/HyperOS stubborn apps
                    is_system = app.is_system if hasattr(app, 'is_system') else False
                    
                    if is_system:
                        # System apps: Try disable first, then uninstall, then aggressive methods
                        methods = [
                            (f"pm disable-user --user 0 {app.package}", "Disable User", ["disabled", "new state"]),
                            (f"pm uninstall -k --user 0 {app.package}", "Uninstall User", ["Success", "uninstalled"]),
                            (f"pm disable {app.package}", "Disable (Root)", ["disabled", "new state"]),
                            (f"pm hide {app.package}", "Hide", ["true", "hidden"]),
                            (f"pm clear {app.package}", "Clear Data", ["Success"]),
                            (f"am force-stop {app.package}", "Force Stop", [""])  # force-stop doesn't output success
                        ]
                    else:
                        # User apps: Prioritize uninstall
                        methods = [
                            (f"pm uninstall {app.package}", "Uninstall", ["Success"]),
                            (f"pm uninstall -k --user 0 {app.package}", "Uninstall User", ["Success", "uninstalled"]),
                            (f"pm disable-user --user 0 {app.package}", "Disable User", ["disabled", "new state"])
                        ]
                    
                    for cmd, label, success_keywords in methods:
                        try:
                            print(f"DEBUG: Trying {label}: {cmd}")
                            res = self.adb.shell(cmd, check=False, log_error=False)  # Don't log errors for cascade attempts
                            print(f"DEBUG: {label} response: {res[:150]}")
                            
                            # Check for success - look for any success keyword in response
                            res_lower = res.lower()
                            if any(keyword.lower() in res_lower for keyword in success_keywords if keyword):
                                is_ok = True
                                result_msg = f"Success via {label}"
                                print(f"DEBUG: ✓ {label} succeeded")
                                break
                            
                            # For force-stop, if no error then consider success
                            if label == "Force Stop" and "error" not in res_lower and "exception" not in res_lower:
                                is_ok = True
                                result_msg = f"Success via {label}"
                                print(f"DEBUG: ✓ {label} succeeded (no error)")
                                break
                                 
                            result_msg = res
                            print(f"DEBUG: ✗ {label} did not succeed, trying next method...")
                            
                        except Exception as e:
                            error_str = str(e)
                            print(f"DEBUG: ✗ {label} raised exception: {error_str[:100]}")
                            result_msg = error_str
                            continue
                
                elif self.mode == "enable":
                    self.adb.shell(f"cmd package unsuspend --user 0 {app.package}")
                    res = self.adb.shell(f"pm enable {app.package}")
                    if "enabled" in res.lower() or "new state" in res.lower(): is_ok = True
                    else:
                        res = self.adb.shell(f"cmd package install-existing {app.package}")
                        if "installed" in res.lower(): is_ok = True

                if is_ok: success_count += 1
                else: failed.append(f"{app.name}: {result_msg.strip()}")

            summary = f"Success: {success_count}/{total}"
            if failed: summary += "\nFailed: " + ", ".join(failed[:2])
            
            self.finished.emit(success_count > 0, summary)
            
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def stop(self): self._is_running = False
