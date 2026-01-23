from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
import os
import re
from src.data.file_data import FileEntry

class FileWorker(QThread):
    """
    Worker thread to handle ADB file operations.
    Supports operation queueing and detailed file listing.
    """
    # Signals
    listing_ready = Signal(list)     # Returns List[FileEntry]
    storages_ready = Signal(list)    # Returns List[FileEntry]
    usage_ready = Signal(float, float) # Total GB, Used GB
    op_finished = Signal(bool, str)  # Success, Message
    progress = Signal(str)           # Progress message/value
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self._queue = []
        self._running = False
        self._mutex = QMutex()
        
    def list_files(self, path):
        self.run_action("list", path=path)
            
    def list_storages(self):
        self.run_action("list_storages")

    def get_usage(self, path=None):
        self.run_action("get_usage", path=path)

    def create_folder(self, path):
        self.run_action("mkdir", path=path)
        
    def delete_item(self, path):
        self.run_action("delete", path=path)
        
    def rename_item(self, src, dst):
        self.run_action("rename", src=src, dst=dst)
        
    def copy_item(self, src, dst):
        self.run_action("copy", src=src, dst=dst)
        
    def move_item(self, src, dst):
        self.run_action("move", src=src, dst=dst)

    def run_action(self, action, **kwargs):
        self._mutex.lock()
        self._queue.append((action, kwargs))
        self._mutex.unlock()
        
        if not self.isRunning():
            self.start()
        
    def run(self):
        """Execute queued actions one by one"""
        while True:
            self._mutex.lock()
            if not self._queue:
                self._mutex.unlock()
                break
            action, params = self._queue.pop(0)
            self._mutex.unlock()
            
            self._params = params # Legacy support for internal methods
            self._running = True
            
            try:
                if action == "list":
                    self._do_list()
                elif action == "list_storages":
                    self._do_list_storages()
                elif action == "get_usage":
                    self._do_get_usage()
                elif action == "mkdir":
                    self._do_mkdir()
                elif action == "delete":
                    self._do_delete()
                elif action == "rename":
                    self._do_rename()
                elif action == "copy":
                    self._do_copy()
                elif action == "move":
                    self._do_move()
            except Exception as e:
                self.op_finished.emit(False, str(e))
            finally:
                self._running = False
            
    def _do_list_storages(self):
        """
        Detect storages/partitions using 'df' and '/storage' listing.
        More robust than simple ls /storage.
        """
        entries = []
        # 1. Always add Internal Storage (Primary)
        entries.append(FileEntry(name="Hệ thống", path="/storage/emulated/0", is_dir=True, size="Root", date="", permissions=""))

        # 2. Check for SD Card / OTG via 'df'
        # df output: Filesystem 1K-blocks Used Available Use% Mounted on
        df_out = self.adb.shell("df")
        if df_out and "error" not in df_out.lower():
            lines = df_out.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    mount_point = parts[-1] 
                    # Common external storage patterns
                    # /storage/XXXX-XXXX (UUID)
                    # /mnt/media_rw/XXXX-XXXX
                    if mount_point.startswith("/storage/") and mount_point not in ["/storage/emulated", "/storage/self", "/storage/enc_emulated"]:
                         # Check if it's the emulated one we already added
                         if "/emulated/" in mount_point: continue
                         
                         name = f"Thẻ nhớ ({os.path.basename(mount_point)})"
                         entries.append(FileEntry(name=name, path=mount_point, is_dir=True, size="External", date="", permissions=""))
        
        # 3. Fallback: ls /storage if df missed something or failed
        # Only add if not already present
        existing_paths = [e.path for e in entries]
        ls_out = self.adb.shell("ls /storage")
        if ls_out and "No such" not in ls_out and "permission denied" not in ls_out.lower():
            for line in ls_out.split():
                line = line.strip()
                if not line: continue
                path = f"/storage/{line}"
                if line not in ["emulated", "self", "knox-emulated", "enc_emulated", "sdcard0"] and path not in existing_paths:
                     entries.append(FileEntry(name=f"Bộ nhớ ngoài ({line})", path=path, is_dir=True, size="External", date="", permissions=""))

        self.storages_ready.emit(entries)

    def _do_get_usage(self):
        try:
             path = self._params.get("path", "/data")
             if not path: path = "/data"
             
             # df <path>
             out = self.adb.shell(f"df \"{path}\"")
             if out and "error" not in out.lower():
                 lines = out.strip().split('\n')
                 # Last line usually contains the data
                 # Filesystem 1K-blocks Used Available Use% Mounted on
                 # /dev/block/... 123456 1234 122222 1% /data
                 
                 found = False
                 for line in lines:
                     parts = line.split()
                     if len(parts) >= 5:
                         # Heuristic: Check if mount point matches or is root /
                         # Or just take the last valid line that looks like stats
                         try:
                             total_k = int(parts[-5]) # 1k-blocks usually 2nd col, but sometimes different. 
                             # Busybox df: Filesystem 1K-blocks Used Available Use% Mounted on
                             # Android Toybox df: Filesystem 1K-blocks Used Available Use% Mounted on
                             # Standard 'df' output structure is usually consistent at the end.
                             # If we split, 1K-blocks is index 1 usually. 
                             # Let's rely on standard columns if we can find header.
                             
                             # Safer: 1K-blocks is index 1, Used is 2
                             total_k = int(parts[1])
                             used_k = int(parts[2])
                             
                             if total_k > 0:
                                 total_gb = total_k / (1024 * 1024)
                                 used_gb = used_k / (1024 * 1024)
                                 self.usage_ready.emit(total_gb, used_gb)
                                 found = True
                                 break
                         except:
                             continue
                 
                 if found: return

        except Exception as e:
             # print(e)
             pass
        self.usage_ready.emit(0, 0)


    def _do_list(self):
        path = self._params["path"]
        # Use ls -l to get details.
        
        # FIX: Handle spaces in path for the command itself
        cmd = f"ls -l \"{path}\""
        output = self.adb.shell(cmd, log_error=False)
        
        entries = []
        
        # Error handling: If ls -l fails (e.g. Permission denied on the folder itself, or empty), we might get empty output.
        if not output or "No such" in output:
             # Just emit empty list or handle specific errors if needed
             # If it's a "No such file", maybe path is wrong.
             self.listing_ready.emit([]) 
             return

        lines = output.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith("total "): continue
            
            # Skip "ls: ... Permission denied" lines mixed in input
            if "Permission denied" in line or "No such file" in line: continue

            parts = line.split()
            
            # Heuristic Parsing
            # Case A: Toybox/Standard `ls -l`
            # drwxrwx--x 45 system system 4096 2024-05-12 10:00 data
            # Case B: Busybox sometimes differs, but usually similar.
            # Case C: "Permission denied" lines might be skipped above.

            # We need at least perms, user, group ... name
            if len(parts) < 4: continue 
            
            perms = parts[0]
            is_dir = perms.startswith('d') or perms.startswith('l') # Treat links as potential dirs/files based on target? For now mainly dirs.
            
            # Parsing Name and Date
            # Iterate backwards to find the date/time pattern.
            # Time: HH:MM
            # Date: YYYY-MM-DD
            
            name = ""
            size = "0"
            date = ""
            
            # Robust Finder: Look for the time column (HH:MM)
            time_col_idx = -1
            for i, part in enumerate(parts):
                # Simple check for HH:MM format
                if ':' in part and len(part) == 5 and part[0].isdigit() and part[3].isdigit():
                    time_col_idx = i
                    break
            
            if time_col_idx != -1 and time_col_idx > 2:
                # Found time. 
                # date should be at time_col_idx - 1
                date = f"{parts[time_col_idx-1]} {parts[time_col_idx]}"
                # size should be at time_col_idx - 2
                size = parts[time_col_idx-2]
                
                # Name is everything after time
                name_parts = parts[time_col_idx+1:]
                
                # Check for symlink "-> target"
                if "->" in name_parts:
                    arrow_idx = name_parts.index("->")
                    # Just take the name before arrow
                    name = " ".join(name_parts[:arrow_idx])
                else:
                    name = " ".join(name_parts)
            else:
                # Fallback: simple default
                name = parts[-1]
                size = "0" # Unknown
            
            if name in ['.', '..'] or not name: continue
            
            # Form full path
            full_path = f"{path}/{name}".replace('//', '/')
            
            # Size formatting
            size_str = ""
            if not is_dir:
                try:
                    sz = int(size)
                    if sz < 1024: size_str = f"{sz} B"
                    elif sz < 1024*1024: size_str = f"{sz/1024:.1f} KB"
                    elif sz < 1024*1024*1024: size_str = f"{sz/(1024*1024):.1f} MB"
                    else: size_str = f"{sz/(1024*1024*1024):.1f} GB"
                except:
                    size_str = size
            
            entries.append(FileEntry(
                name=name,
                path=full_path,
                is_dir=is_dir,
                size=size_str,
                date=date,
                permissions=perms
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
