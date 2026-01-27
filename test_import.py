
import sys
import os
from pathlib import Path

current_dir = Path.cwd()
sys.path.append(str(current_dir))

print(f"Path: {sys.path}")
try:
    print("Attempting import...")
    from src.core.adb.adb_manager import ADBManager, DeviceState
    print(f"Imported: {ADBManager}, {DeviceState}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
