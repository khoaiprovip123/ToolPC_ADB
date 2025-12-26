from PySide6.QtCore import QThread, Signal

class DebloatWorker(QThread):
    """Background worker for debloating"""
    progress = Signal(str)
    finished = Signal()
    
    def __init__(self, adb, packages):
        super().__init__()
        self.adb = adb
        self.packages = packages
        self._is_running = True
        
    def run(self):
        for package in self.packages:
            if not self._is_running:
                break
            
            try:
                self.progress.emit(f"Đang xử lý: {package}...")
                # Uninstall for user 0 (safe removal - Archive)
                result = self.adb.shell(f"pm uninstall --user 0 {package}")
                
                if "success" in result.lower():
                    self.progress.emit(f"✅ Đã gỡ: {package}")
                elif "not installed" in result.lower():
                    self.progress.emit(f"👌 Đã gỡ trước đó: {package}")
                else:
                    # Try disable if uninstall fails (rarely needed if uninstall failed, but sometimes meaningful)
                    # But on HyperOS, disable is often more restricted than uninstall.
                    
                    # Check if System app
                    # If uninstall failed, it might be a protected system app that CANNOT be uninstalled or disabled without root.
                    
                    try:
                        res_disable = self.adb.shell(f"pm disable-user --user 0 {package}")
                        if "new state" in res_disable.lower() or "disabled" in res_disable.lower():
                             self.progress.emit(f"⚠️ Đã tắt: {package}")
                        else:
                             # Check for specific security error
                             if "SecurityException" in res_disable:
                                 self.progress.emit(f"🔒 App hệ thống được bảo vệ: {package}")
                             else:
                                 self.progress.emit(f"❌ Không thể gỡ/tắt: {package}")
                    except Exception as e_dis:
                         if "SecurityException" in str(e_dis):
                             self.progress.emit(f"🔒 App hệ thống được bảo vệ: {package}")
                         else:
                             self.progress.emit(f"❌ Lỗi khi tắt: {package}")
                    
            except Exception as e:
                self.progress.emit(f"❌ Lỗi {package}: {e}")
                
        self.finished.emit()
        
    def stop(self):
        self._is_running = False
