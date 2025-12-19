import sys
import os
sys.path.append(os.getcwd())
from src.core.adb.adb_manager import ADBManager

def scan_battery():
    adb = ADBManager()
    print("--- Battery Debug Scan ---")
    
    # List power supplies
    try:
        supplies = adb.shell("ls /sys/class/power_supply/").split()
        print(f"Supplies found: {supplies}")
        
        candidates = [
            "charge_full", 
            "charge_full_design", 
            "energy_full", 
            "energy_full_design",
            "capacity",
            "capacity_level",
            "status",
            "health",
            "charge_counter"
        ]
        
        for supply in supplies:
            print(f"\n[Scanning {supply}]")
            base = f"/sys/class/power_supply/{supply}"
            
            for node in candidates:
                try:
                    val = adb.shell(f"cat {base}/{node}").strip()
                    print(f"  {node}: {val}")
                except:
                    pass
                    
            # Try to list all files just in case
            # ls = adb.shell(f"ls {base}")
            # print(f"  All files: {ls.replace('\n', ' ')}")
            
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Dumpsys Battery ---")
    try:
        print(adb.shell("dumpsys battery"))
    except: pass

if __name__ == "__main__":
    scan_battery()
