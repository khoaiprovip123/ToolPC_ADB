
from PySide6.QtCore import QObject, Signal
import logging
import logging.handlers

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
        # Simple singleton pattern without interfering with QObject initialization
        if cls._instance is None:
            # Create instance without calling __init__ yet
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-init
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Setup log file with rotation: 5 files x 5MB max."""
        try:
            from pathlib import Path
            import sys
            import os
            
            # Determine base path
            if hasattr(sys, '_MEIPASS'):
                base_dir = Path(sys.executable).parent
            else:
                # src/core/log_manager.py -> ... -> root
                base_dir = Path(__file__).parent.parent.parent
            
            self.log_dir = base_dir / "logs"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "app_log.txt"
            
            # Ensure file has restricted permissions (rw-------)
            if not self.log_file.exists():
                self.log_file.touch()
                try:
                    os.chmod(self.log_file, 0o600)
                except Exception:
                    pass
            
            # Setup RotatingFileHandler: 5MB per file, keep 5 backups
            self._file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=5,
                encoding='utf-8'
            )
            self._file_handler.setFormatter(
                logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
            )
            self._logger = logging.getLogger('XiaomiADB')
            self._logger.setLevel(logging.DEBUG)
            # Avoid duplicate handlers on re-init
            if not self._logger.handlers:
                self._logger.addHandler(self._file_handler)
            
            # Write session start separator
            self._logger.info(f"{'='*50}")
            self._logger.info(f"SESSION START")
            self._logger.info(f"{'='*50}")
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
        """Write log entry to file via RotatingFileHandler, filtering sensitive info."""
        try:
            if not hasattr(self, '_logger'):
                return
            # Filter out environment variable values like GEMINI_API_KEY
            if "GEMINI_API_KEY" in message or "GEMINI_API_KEY" in title:
                title = title.replace("GEMINI_API_KEY", "[REDACTED]")
                message = message.replace("GEMINI_API_KEY", "[REDACTED]")
            log_entry = f"[{level.upper()}] [{title}] {message}"
            self._logger.info(log_entry)
        except Exception as e:
            print(f"[LogManager] Không thể ghi log ra file: {e}")
