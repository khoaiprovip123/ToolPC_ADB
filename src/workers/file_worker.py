from PySide6.QtCore import QThread, Signal
import os
from src.data.file_data import FileEntry

class FileWorker(QThread):
    """
    Worker thread to handle ADB file operations.
    Prevents UI freezing during heavy IO or listing.
    """
    # Signals
    listing_ready = Signal(list)     # Returns List[FileEntry]
    op_finished = Signal(bool, str)  # Success, Message
    progress = Signal(str)           # Progress message/value
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self._action = None
        self._params = {}
        
    def list_files(self, path):
        """Queue list command"""
        self._action = "list"
        self._params = {"path": path}
        self.start()
        
    def create_folder(self, path):
        self._action = "mkdir"
        self._params = {"path": path}
        self.start()
        
    def delete_item(self, path):
        self._action = "delete"
        self._params = {"path": path}
        self.start()
        
    def rename_item(self, src, dst):
        self._action = "rename"
        self._params = {"src": src, "dst": dst}
        self.start()
        
    def copy_item(self, src, dst):
        self._action = "copy"
        self._params = {"src": src, "dst": dst}
        self.start()
        
    def move_item(self, src, dst):
        self._action = "move"
        self._params = {"src": src, "dst": dst}
        self.start()
        
    def run(self):
        """Execute queued action"""
        try:
            if self._action == "list":
                self._do_list()
            elif self._action == "mkdir":
                self._do_mkdir()
            elif self._action == "delete":
                self._do_delete()
            elif self._action == "rename":
                self._do_rename()
            elif self._action == "copy":
                self._do_copy()
            elif self._action == "move":
                self._do_move()
        except Exception as e:
            self.op_finished.emit(False, str(e))
            
    def _do_list(self):
        path = self._params["path"]
        # Use ls -1p for simple parsing
        # -1: One entry per line
        # -p: Directories end with /
        cmd = f"ls -1p \"{path}\""
        output = self.adb.shell(cmd, log_error=False) # Suppress error for empty folders
        
        entries = []
        if output and "No such" not in output:
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                is_dir = line.endswith('/')
                name = line[:-1] if is_dir else line
                
                if name in ['.', '..']: continue
                
                full_path = f"{path}/{name}".replace('//', '/')
                
                entries.append(FileEntry(
                    name=name,
                    path=full_path,
                    is_dir=is_dir
                ))
                
        # Sort: Dirs first, then Files
        entries.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        self.listing_ready.emit(entries)
        
    def _do_mkdir(self):
        path = self._params["path"]
        res = self.adb.shell(f"mkdir \"{path}\"")
        if "error" in res.lower():
             self.op_finished.emit(False, f"Lỗi tạo thư mục: {res}")
        else:
             self.op_finished.emit(True, "Đã tạo thư mục")

    def _do_delete(self):
        path = self._params["path"]
        res = self.adb.shell(f"rm -rf \"{path}\"")
        if "error" in res.lower() or "permission denied" in res.lower():
            self.op_finished.emit(False, f"Lỗi xóa: {res}")
        else:
            self.op_finished.emit(True, "Đã xóa thành công")
            
    def _do_rename(self):
        src = self._params["src"]
        dst = self._params["dst"]
        res = self.adb.shell(f"mv \"{src}\" \"{dst}\"")
        if "error" in res.lower():
            self.op_finished.emit(False, f"Lỗi đổi tên: {res}")
        else:
            self.op_finished.emit(True, "Đã đổi tên")

    def _do_copy(self):
        src = self._params["src"]
        dst = self._params["dst"]
        res = self.adb.shell(f"cp -r \"{src}\" \"{dst}\"")
        if "error" in res.lower():
            self.op_finished.emit(False, f"Lỗi sao chép: {res}")
        else:
            self.op_finished.emit(True, "Đã sao chép")

    def _do_move(self):
        src = self._params["src"]
        dst = self._params["dst"]
        res = self.adb.shell(f"mv \"{src}\" \"{dst}\"")
        if "error" in res.lower():
            self.op_finished.emit(False, f"Lỗi di chuyển: {res}")
        else:
            self.op_finished.emit(True, "Đã di chuyển")
