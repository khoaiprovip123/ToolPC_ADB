import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("."))

from src.core.adb.adb_manager import ADBManager

def debug_adb():
    print("Initializing ADB Manager...")
    adb = ADBManager()
    print(f"ADB Path: {adb.adb_path}")
    
    print("\nChecking devices...")
    devices = adb.get_devices()
    print(f"Devices found: {devices}")
    
    if not devices:
        print("No devices found. Please connect a device.")
        return
        
    serial, status = devices[0]
    print(f"\nSelecting device: {serial}")
    adb.select_device(serial)
    
    print("\nFetching detailed system info...")
    try:
        info = adb.get_detailed_system_info()
        print("Info retrieved:")
        for k, v in info.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error fetching info: {e}")

if __name__ == "__main__":
    debug_adb()
