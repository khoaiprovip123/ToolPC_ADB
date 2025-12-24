
from PySide6.QtCore import QObject, Signal

class LogManager(QObject):
    """
    Central Logging Singleton.
    Emits signals when a log is added so UI components can react (e.g., NotificationCenter).
    """
    _instance = None
    
    # Signal(Title, Message, Type/Level)
    # Type: info, success, error, warning
    log_signal = Signal(str, str, str)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            # Must call QObject init if we were creating it normally, 
            # but for singletons inheriting QObject, it's tricky with __new__.
            # We initialize signals by ensuring proper PySide object creation or just composition.
            # Best practice for PySide singletons is usually a class attribute or global instance.
        return cls._instance

    def __init__(self):
        # Prevent re-init
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Setup log file path and ensure directory exists"""
        try:
            from pathlib import Path
            import sys
            
            # Determine base path
            if hasattr(sys, '_MEIPASS'):
                base_dir = Path(sys.executable).parent
            else:
                # src/core/log_manager.py -> ... -> root
                base_dir = Path(__file__).parent.parent.parent
            
            self.log_dir = base_dir / "logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "app_log.txt"
            
            # Write session start separator
            from datetime import datetime
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"SESSION START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*50}\n")
        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LogManager()
        return cls._instance

    @classmethod
    def log(cls, title: str, message: str, level: str = "info"):
        """Static helper to send logs easily and write to file"""
        inst = cls.get_instance()
        inst.log_signal.emit(title, message, level)
        inst._write_to_file(title, message, level)

    def _write_to_file(self, title: str, message: str, level: str):
        """Write log entry to file"""
        try:
             if not hasattr(self, 'log_file'): return
             
             from datetime import datetime
             timestamp = datetime.now().strftime('%H:%M:%S')
             log_entry = f"[{timestamp}] [{level.upper()}] [{title}] {message}\n"
             
             with open(self.log_file, "a", encoding="utf-8") as f:
                 f.write(log_entry)
        except:
             pass
