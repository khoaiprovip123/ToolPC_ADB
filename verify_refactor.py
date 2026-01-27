import sys
import os
from pathlib import Path

# Add src to python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def verify_adb_manager():
    print("Testing ADBManager...")
    try:
        from src.core.adb.adb_manager import ADBManager
        adb = ADBManager()
        # Mocking shell to avoid actual ADB calls or relying on connected devices
        # But for now, let's just see if the method runs without crashing (it has try/except blocks)
        info = adb.get_detailed_system_info()
        print("ADBManager.get_detailed_system_info() returned:", info.keys())
        print("ADBManager test PASS")
    except Exception as e:
        print(f"ADBManager test FAIL: {e}")
        import traceback
        traceback.print_exc()

def verify_ui_init():
    print("Testing UI Initialization...")
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        # Create app
        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
            
        # Instantiate Window (triggers usage of ThemeManager styles)
        window = MainWindow()
        print("MainWindow instantiated successfully.")
        print("UI test PASS")
    except Exception as e:
        print(f"UI test FAIL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_adb_manager()
    print("-" * 20)
    verify_ui_init()
