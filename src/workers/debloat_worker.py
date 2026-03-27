from PySide6.QtCore import QThread, Signal

class DebloatWorker(QThread):
    """Background worker for debloating"""
    progress = Signal(str)
    finished = Signal()
    
    def __init__(self, adb, packages):
        super().__init__()
        self.adb = adb
        self.packages = packages
        
    def run(self):
        for package in self.packages:
            if self.isInterruptionRequested():
                break
            
            try:
                self.progress.emit(f"Đang xử lý: {package}...")
                result = self.adb.shell(f"pm uninstall --user 0 {package}")
                
                if "success" in result.lower():
                    self.progress.emit(f"✅ Đã gỡ: {package}")
                elif "not installed" in result.lower():
                    self.progress.emit(f"👌 Đã gỡ trước đó: {package}")
                else:
                    try:
                        res_disable = self.adb.shell(f"pm disable-user --user 0 {package}")
                        if "new state" in res_disable.lower() or "disabled" in res_disable.lower():
                            self.progress.emit(f"⚠️ Đã tắt: {package}")
                        elif "SecurityException" in res_disable:
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
