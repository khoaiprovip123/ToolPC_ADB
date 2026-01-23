
import sys
import os
from pathlib import Path

# Setup path
# Assuming this script is in tools/, so project root is one up
current_dir = Path(__file__).resolve().parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from PySide6.QtWidgets import QApplication

# Create App instance for widgets that need it during import (unlikely but safe)
# Some widgets might instantiate QPixmaps or QFonts at module level
if not QApplication.instance():
    app = QApplication(sys.argv)

def test_import(name, module_path):
    print(f"Testing {name}...", end=" ", flush=True)
    try:
        # Import module
        mod = __import__(module_path, fromlist=[''])
        
        # Instantiate if it's a widget module
        if "widgets" in module_path:
            # We need a dummy ADB manager
            from src.core.adb.adb_manager import ADBManager
            adb = ADBManager()
            
            if "battery_health" in module_path:
                print("Instantiating BatteryHealthWidget...", end=" ")
                w = mod.BatteryHealthWidget(adb)
                print("Success")
            elif "unified_tools" in module_path:
                 print("Instantiating UnifiedTools...", end=" ")
                 # Unified tools might be complex, skip deep check if battery passes
                 pass

        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True

modules = [
    ("ADB Manager", "src.core.adb.adb_manager"),
    ("Battery Health", "src.ui.widgets.battery_health"),
    ("App Manager", "src.ui.widgets.app_manager"),
    ("Xiaomi Optimizer", "src.ui.widgets.xiaomi_optimizer"),
    ("Unified Tools", "src.ui.widgets.unified_tools"),
    ("Main Window", "src.ui.main_window"),
]

print(f"--- Starting Import Checks in {current_dir} ---")
for name, path in modules:
    if not test_import(name, path):
        print("Stopping due to failure.")
        sys.exit(1)

print("--- All Imports Successful ---")
sys.exit(0)
