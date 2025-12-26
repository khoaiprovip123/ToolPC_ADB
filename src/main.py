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
sys.path.append(str(root_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.core.adb.adb_manager import ADBManager
from src.ui.main_window import MainWindow


def main():
    """Main entry point"""
    # Create Win32 Mutex to prevent multiple instances and support installer lock
    mutex_name = "XiaomiADBCommanderMutex"
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
    icon_path = root_dir / 'resources' / 'icon.ico'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    adb = ADBManager()
    window = MainWindow(adb)
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        print(f"CRASH: {e}")
