# src/main.py
"""
Application Entry Point
"""

import sys
import os
import ctypes
from pathlib import Path

# Add src to python path
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))  # Force local priority

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import PySide6.QtSvg # Required for SVG icons
from src.core.adb.adb_manager import ADBManager
from src.ui.main_window import MainWindow
from src.ui.theme_manager import ThemeManager
from src.core.resource_utils import get_resource_path


def main():
    """Main entry point"""
    # Create Win32 Mutex to prevent multiple instances and support installer lock
    mutex_name = "XiaomiADBCommanderMutex_v4"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()
    
    if last_error == 183: # ERROR_ALREADY_EXISTS
        print("Another instance is already running.")
        # Optional: Bring existing window to front here
        sys.exit(0)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Xiaomi ADB Commander")
    app.setOrganizationName("VanKhoai")
    
    # Keep mutex reference alive
    app._app_mutex = mutex
    
    # Set app icon
    icon_path = get_resource_path('resources', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    adb = ADBManager()
    
    # Apply Global Theme
    current_theme = ThemeManager.get_theme()
    # ThemeManager.set_theme("light") # Default is light in class
    # Apply stylesheet to QApplication to ensure all top-level windows (Dialogs) inherit it
    app.setStyleSheet(ThemeManager.get_main_window_style())
    
    window = MainWindow(adb)
    window.show()

    # Run event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    import sys
    import traceback
    from datetime import datetime
    
    # Configure Loguru for global crash logging
    try:
        from loguru import logger
        import os
        os.makedirs("logs", exist_ok=True)
        # Add a dedicated crash log file that rotates
        logger.add("logs/crash_{time:YYYY-MM-DD}.log", rotation="10 MB", retention="10 days", level="ERROR", backtrace=True, diagnose=True)
    except ImportError:
        logger = None

    def global_exception_handler(exctype, value, tb):
        """Handle unhandled exceptions in the Qt Event Loop and main thread."""
        if logger:
            # loguru will beautifully format the backtrace
            logger.opt(exception=(exctype, value, tb)).critical("UNHANDLED EXCEPTION")
            
        # Fallback to plain text log for easy reading
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(f"--- Crash Report {timestamp} ---\n")
            f.write("".join(traceback.format_exception(exctype, value, tb)))
            f.write("\n--------------------------------\n")
            f.write("Please send this file to the developer to help fix the issue.\n")
            
        # Still print to stderr
        sys.__excepthook__(exctype, value, tb)

    # Attach the global exception hook
    sys.excepthook = global_exception_handler

    try:
        main()
    except Exception as e:
        # Catch any synchronous error in main()
        global_exception_handler(type(e), e, e.__traceback__)
        sys.exit(1)
