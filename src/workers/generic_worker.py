from PySide6.QtCore import QThread, Signal

class GenericShellWorker(QThread):
    """
    Worker chung để chạy các lệnh shell đơn giản hoặc danh sách các lệnh shell trong nền.
    """
    finished = Signal(bool, str)  # success, message
    progress = Signal(str)        # thông báo tiến trình

    def __init__(self, adb_manager, commands, title="Task"):
        super().__init__()
        self.adb = adb_manager
        self.commands = commands if isinstance(commands, list) else [commands]
        self.title = title

    def run(self):
        success_count = 0
        total = len(self.commands)
        
        try:
            for i, cmd in enumerate(self.commands):
                if self.isInterruptionRequested():
                    self.finished.emit(False, "Đã bị hủy bởi người dùng.")
                    return
                
                self.progress.emit(f"Đang xử lý {i+1}/{total}...")
                res = self.adb.shell(cmd, check=False)
                
                if "error" not in res.lower() and "failed" not in res.lower():
                    success_count += 1
            
            msg = f"Hoàn thành {success_count}/{total} tác vụ '{self.title}'."
            self.finished.emit(success_count > 0, msg)
            
        except Exception as e:
            self.finished.emit(False, f"Lỗi: {str(e)}")
