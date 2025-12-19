# src/main.py
"""
Application Entry Point
"""

import sys
import os
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
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("ADB Manager Pro")
    app.setOrganizationName("YourOrg")
    
    # Set app icon
    icon_path = root_dir / 'src' / 'resources' / 'icons' / 'app_icon.ico'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    adb = ADBManager()
    window = MainWindow(adb)
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
