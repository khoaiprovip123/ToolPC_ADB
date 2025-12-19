
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

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LogManager()
        return cls._instance

    @classmethod
    def log(cls, title: str, message: str, level: str = "info"):
        """Static helper to send logs easily"""
        inst = cls.get_instance()
        inst.log_signal.emit(title, message, level)
