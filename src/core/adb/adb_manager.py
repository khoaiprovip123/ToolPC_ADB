import subprocess
import os
import re
import platform
from pathlib import Path
from enum import Enum, auto
import sys

class DeviceStatus(Enum):
    ONLINE = auto()
    OFFLINE = auto()
    UNAUTHORIZED = auto()
    BOOTLOADER = auto()
    RECOVERY = auto()
    SIDELOAD = auto()
    UNKNOWN = auto()


class ADBManager:
    def __init__(self):
        # Determine ADB Path
        self.adb_path = "adb" # Default to PATH
        
        # Check bundled resources (PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
            possible_bundled = [
                base_path / "assets" / "platform-tools" / "adb.exe",
                base_path / "resources" / "platform-tools" / "adb.exe",
            ]
            for p in possible_bundled:
                if p.exists():
                    self.adb_path = str(p)
                    break
        
        # Check local resources and common paths if not found in bundle or as fallback
        if self.adb_path == "adb":
            root = Path(__file__).parent.parent.parent.parent
            possible_paths = [
                root / "resources" / "platform-tools" / "adb.exe",
                root / "resources" / "adb" / "windows" / "adb.exe",
                root / "assets" / "platform-tools" / "adb.exe",
                root / "scripts" / "adb.exe",
            ]
            
            for p in possible_paths:
                if p.exists():
                    self.adb_path = str(p)
                    break
        
        # Log resolution
        print(f"ADBManager: Initialized with adb_path={self.adb_path}")
            
        self.current_device = None
        
    def select_device(self, serial):
        self.current_device = serial
        
    def get_devices(self):
        """Get list of connected ADB devices: [(serial, status), ...]"""
        devices = []
        try:
            out = self.execute("devices")
            lines = out.strip().split('\n')[1:] # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    state_str = parts[1]
                    
                    status = DeviceStatus.UNKNOWN
                    if state_str == 'device':
                        status = DeviceStatus.ONLINE
                    elif state_str == 'offline':
                        status = DeviceStatus.OFFLINE
                    elif state_str == 'unauthorized':
                        status = DeviceStatus.UNAUTHORIZED
                    elif state_str == 'sideloade':
                        status = DeviceStatus.SIDELOAD
                    elif state_str == 'recovery':
                        status = DeviceStatus.RECOVERY
                        
                    devices.append((serial, status))
        except Exception as e:
            print(f"ADBManager: Error getting devices: {e}")
            pass
        return devices

    def get_fastboot_devices(self):
        """Get list of fastboot devices serials"""
        devices = []
        try:
            # Fastboot uses same adb path? usually fastboot.exe in same folder
            fastboot_path = self.adb_path.replace("adb.exe", "fastboot.exe").replace("adb", "fastboot")
            
            # If default adb used, try default fastboot
            if "platform-tools" not in fastboot_path and "adb" == self.adb_path:
                 fastboot_path = "fastboot"
                 
            cmd = f'"{fastboot_path}" devices'
            
            # Execute manually since self.execute uses adb_path
            creation_flags = 0x08000000 if os.name == 'nt' else 0
            out = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT, 
                creationflags=creation_flags, encoding='utf-8', errors='replace'
            ).strip()
            
            lines = out.split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'fastboot':
                    devices.append(parts[0])
        except:
             pass
        return devices

    def check_connection(self):
        """Auto-select first device if none selected"""
        if self.current_device: return True
        devices = self.get_devices()
        if devices:
            self.current_device = devices[0][0]
            return True
        return False

    def execute(self, command):
        """Execute ADB command (host side)"""
        if isinstance(command, list):
            cmd_list = [self.adb_path] + [str(arg) for arg in command]
        else:
            cmd_list = f'"{self.adb_path}" {command}'
            
        try:
            # Use shell=True for string command
            use_shell = isinstance(command, str)
            return subprocess.check_output(
                cmd_list, 
                shell=use_shell,
                stderr=subprocess.STDOUT, 
                creationflags=0x08000000 if os.name == 'nt' else 0,
                encoding='utf-8',
                errors='replace'
            ).strip()
        except subprocess.CalledProcessError as e:
            return e.output.strip()
        except Exception as e:
            return f"Error: {e}"

    def shell(self, command, *args, **kwargs):
        """Execute ADB Shell command"""
        if not self.current_device:
            return "Error: No device connected"
        return self.execute(f"-s {self.current_device} shell {command}")
        
    def run_adb(self, args):
        """Run raw adb command with args list"""
        return self.execute(args)

    def connect_wireless(self, ip, port=5555):
        res = self.execute(f"connect {ip}:{port}")
        if "connected to" in res:
            self.current_device = f"{ip}:{port}"
            return True
        return False

    def enable_wireless_adb(self):
        if not self.current_device: return False
        res = self.execute(f"-s {self.current_device} tcpip 5555")
        return "restarting in TCP mode port: 5555" in res or not res.strip()
        
    def reboot(self, mode=""):
        """Reboot device. Mode: 'bootloader', 'recovery', or empty for normal."""
        return self.execute(f"-s {self.current_device} reboot {mode}".strip())
        
    def toggle_screen(self):
        """Toggle screen power (Power Button)"""
        return self.shell("input keyevent 26")
        
    def is_online(self):
        return self.current_device is not None
        
    def get_detailed_system_info(self):
        """Fetch detailed device info (aggregated)"""
        info = {}
        if not self.is_online(): return info
        
        try:
            # 1. Props
            props = self.shell("getprop")
            for line in props.split('\n'):
                if ': [' in line:
                    parts = line.split(': [')
                    if len(parts) >= 2:
                        key = parts[0].strip('[] ')
                        val = parts[1].strip('[] ')
                    
                        if key == 'ro.product.model': info['model'] = val
                        elif key == 'ro.product.name': info['device_name'] = val
                        elif key == 'ro.product.board': info['board'] = val
                        elif key == 'ro.build.id': info['build_id'] = val
                        elif key == 'ro.build.version.release': info['android_version'] = val
                        elif key == 'ro.build.version.security_patch': info['security_patch'] = val
                        elif key == 'ro.product.manufacturer': info['manufacturer'] = val
                        elif key == 'ro.miui.ui.version.name': info['os_version'] = f"HyperOS {val}" if "816" in val or "1.0" in val else f"MIUI {val}"
                        elif key == 'ro.kernel.version': info['kernel'] = val
            
            # Friendly Name & SoC
            brand = info.get('manufacturer', 'Xiaomi')
            model = info.get('model', 'Device')
            info['device_friendly_name'] = f"{brand} {model}"
            
            # SoC Logic (Simple mapping)
            board = info.get('board', '').lower()
            if board == 'lisa': info['soc_name'] = 'Snapdragon 778G'
            elif board == 'taro': info['soc_name'] = 'Snapdragon 8 Gen 1'
            elif board == 'kalama': info['soc_name'] = 'Snapdragon 8 Gen 2'
            elif board == 'pineapple': info['soc_name'] = 'Snapdragon 8 Gen 3'
            elif board == 'alioth': info['soc_name'] = 'Snapdragon 870'
            elif board == 'vayu': info['soc_name'] = 'Snapdragon 860'
            elif board == 'courbet': info['soc_name'] = 'Snapdragon 732G'
            elif board == 'sweet': info['soc_name'] = 'Snapdragon 732G'
            else: info['soc_name'] = board
            
            # 2. Battery
            batt = self.get_battery_info()
            info.update(batt)
            info['battery_level'] = batt.get('level', 0)

            # 3. Storage
            store = self.get_storage_info()
            info.update(store)
            # Format storage
            total_gb = store.get('total', 0) / (1024**3)
            info['storage_total'] = f"{total_gb:.0f}GB"
            
            # 4. Memory/RAM
            mem = self.get_memory_info()
            info.update(mem)
            
        except Exception as e: 
            print(f"Error getting system info: {e}")
            pass
        return info

    def get_memory_info(self):
        """Get RAM info from /proc/meminfo (Python parsing)"""
        info = {'ram_total': '0GB', 'ram_free': '0GB'}
        try:
            # Read file directly without grep to avoid pipe issues on Windows
            out = self.shell("cat /proc/meminfo")
            total = 0
            free = 0
            available = 0
            
            for line in out.split('\n'):
                parts = line.split(':')
                if len(parts) < 2: continue
                
                key = parts[0].strip()
                val_str = parts[1].strip().split(' ')[0] # 'MemTotal: 12345 kB'
                if not val_str.isdigit(): continue
                val = int(val_str) # kB
                
                if key == 'MemTotal': total = val
                elif key == 'MemFree': free = val
                elif key == 'MemAvailable': available = val
            
            # Convert to GB
            if total > 0:
                # Round to nearest standard RAM size (4, 6, 8, 12, 16)
                total_gb_real = total / (1024 * 1024)
                standard_sizes = [4, 6, 8, 12, 16, 24, 32]
                closest = min(standard_sizes, key=lambda x: abs(x - total_gb_real))
                info['ram_total'] = f"{closest}GB"
                
            info['ram_raw_total'] = total
            info['ram_raw_free'] = available if available > 0 else free
            
        except: pass
        return info

    def get_storage_info(self):
        """Get storage usage: {'total': bytes, 'used': bytes, 'free': bytes}"""
        info = {'total': 0, 'used': 0, 'free': 0}
        if not self.is_online(): return info
        try:
            # df returns 1K blocks
            out = self.shell("df /data")
            lines = out.strip().split('\n')
            # Look for the line mounted on /data (or contains /data)
            # Some devices output multiple lines or wrapping
            target_line = None
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                     if "/data" in line:
                         target_line = line
                         break
                     elif "/storage" in line and not target_line:
                         target_line = line
            
            # Fallback: if no specific match, take the first non-header line
            if not target_line and len(lines) > 1 and "Filesystem" not in lines[-1]:
                 # Check last line (often the result) or second line
                 # Debug output showed data on line 1 (index 1)
                 if "Filesystem" in lines[0] and len(lines) >= 2:
                     target_line = lines[1]

            if target_line:
                 parts = target_line.split()
                 nums = [x for x in parts if x.isdigit()]
                 if len(nums) >= 3:
                     try:
                         # parts logic varies if filesystem name is long. 
                         # Reliable way: last part is mount, 2nd last is %, 3rd last is Avail, 4th last is Used, 5th last is Total (1K-blocks)
                         # Filesystem 1K-blocks Used Available Use% Mounted on
                         
                         # Reverse indexing is safer against long filesystem paths with spaces (though rare for block devices)
                         # But parts are split by space.
                         
                         # Let's try standard index first
                         t = int(parts[1]) * 1024
                         u = int(parts[2]) * 1024
                         a = int(parts[3]) * 1024
                         
                         info['total'] = t
                         info['used'] = u
                         info['free'] = a
                     except:
                         pass
        except: pass
        return info
        
    def screenshot(self, filename="screenshot.png"):
        self.shell(f"screencap -p /sdcard/{filename}")
        self.execute(f"-s {self.current_device} pull /sdcard/{filename} .")
        self.shell(f"rm /sdcard/{filename}")
        
    def shutdown(self):
        return self.shell("reboot -p")
        
    def fastboot_reboot(self):
        return self.execute("reboot") # fastboot command
        
    def fastboot_reboot_recovery(self):
        # fastboot oem reboot-recovery or generic
        return self.execute("oem reboot-recovery")
        
    def fastboot_reboot_fastbootd(self):
        return self.execute("reboot fastboot")
        
    def fastboot_reboot_edl(self):
        return self.execute("oem edl")

    def get_battery_info(self):
        """Get dumpsys battery info as dict"""
        info = {}
        if not self.is_online(): return info
        
        try:
            cmd = "dumpsys battery"
            output = self.shell(cmd)
            
            if "Error" in output or not output: return info
            
            # Parse basic fields
            for line in output.split('\n'):
                line = line.strip()
                if ': ' in line:
                    key, val = line.split(': ', 1)
                    if key == 'level': info['level'] = int(val)
                    elif key == 'status': 
                        info['status_code'] = int(val)
                        status_map = {1: "Unknown", 2: "Charging", 3: "Discharging", 4: "Not charging", 5: "Full"}
                        info['status'] = status_map.get(int(val), "Unknown")
                    elif key == 'health': info['health'] = int(val)
                    elif key == 'voltage': info['voltage'] = int(val)
                    elif key == 'temperature': info['temperature'] = int(val)
                    elif key == 'technology': info['technology'] = val
                    elif key == 'Charge counter': 
                        # Xiaomi specific: 394600000 -> 3946 mAh
                        try:
                            c = int(val)
                            # Heuristic: If > 10M, assume it needs scaling
                            # User case: 394,600,000 uAh / 100,000 = 3946 mAh
                            if c > 10000000:
                                info['charge_full'] = int(c / 100000)
                            else:
                                info['charge_full'] = int(c / 1000) # Normal uAh
                        except: pass

            # Design Capacity Lookup (Xiaomi)
            design_map = {
                "lisa": 4250, "renoir": 4250, "courbet": 4250, "2107119DC": 4250, # Mi 11 Lite Series
                "sweet": 5020, "vayu": 5160, "alioth": 4520, "munch": 4500,
                "marble": 5000, "mondrian": 5160, "fuxi": 4500, "nuwa": 4820,
                "socrates": 6000, "ishtar": 5000
            }
            
            # Try to find match
            # We need model or board. We can assume get_detailed_system_info called props, 
            # OR we check adb shell getprop quickly.
            # But making another shell call here might slow things down.
            # Let's do a quick lazy check if 'charge_full' is present but design is missing
            if 'charge_full' in info:
                # We have real capacity, need design to calc health
                try:
                   board = self.shell("getprop ro.product.board").strip()
                   cap = design_map.get(board)
                   if not cap:
                       model = self.shell("getprop ro.product.model").strip()
                       cap = design_map.get(model)
                   
                   if cap:
                       info['charge_full_design'] = cap
                except: pass
                
        except Exception as e:
            print(f"Error getting battery info: {e}")
        return info

    def get_battery_health(self):
        """Get advanced health info from kernel files"""
        info = self.get_battery_info()
        
        # Try to read kernel nodes for more accurate capacity
        # Charge Full (uc)
        try:
            # Common paths
            paths = [
                "/sys/class/power_supply/battery/charge_full",
                "/sys/class/power_supply/bms/charge_full",
                "/sys/class/power_supply/battery/charge_full_design", # For design
            ]
            
            # Read real capacity
            real_cap = self.shell("cat /sys/class/power_supply/battery/charge_full")
            if real_cap.isdigit():
                info['charge_full'] = int(real_cap) / 1000 # Usually in uAh
                
            # Read design capacity
            design_cap = self.shell("cat /sys/class/power_supply/battery/charge_full_design")
            if design_cap.isdigit():
                info['charge_full_design'] = int(design_cap) / 1000
            else:
                # Fallback
                info['charge_full_design'] = 4500 # Default fallback
                
        except:
             pass
             
        # Normalize voltage and temp
        if 'voltage' in info and info['voltage'] > 100:
            info['voltage'] = info['voltage'] / 1000.0 # mV to V
            
        if 'temperature' in info and info['temperature'] > 100:
             info['temperature'] = info['temperature'] / 10.0 # 300 -> 30.0
             
        return info

    def push_file(self, local, remote):
        """Push file to device"""
        result = self.execute(["push", local, remote])
        return result

    def pull_file(self, remote, local):
        """Pull file from device"""
        result = self.execute(["pull", remote, local])
        return result

    # Cleaner Methods
    def clean_app_cache(self):
        return self.shell("pm trim-caches 32G")
        
    def clean_obsolete_dex(self):
        return self.shell("cmd package prune-dex-opt")
        
    def clean_messenger_data(self):
         # Example for Telegram
         return self.shell("rm -rf /sdcard/Telegram/Telegram\ Video/* /sdcard/Telegram/Telegram\ Images/*")

    def fix_connection(self):
        """Kill-server and Start-server to fix connection issues"""
        try:
            self.execute("kill-server")
            import time
            time.sleep(1)
            out = self.execute("start-server")
            return f"Đã khởi động lại ADB:\n{out}\n\nVui lòng thử kết nối lại."
        except Exception as e:
            return f"Lỗi khi sửa kết nối: {e}"

    # ================== Control Utils ==================
    def set_brightness(self, val):
        return self.shell(f"settings put system screen_brightness {val}")
        
    def set_volume(self, val):
        # STREAM_MUSIC
        return self.shell(f"media volume --stream 3 --set {val}")
        
    def toggle_show_taps(self, enable: bool):
        val = 1 if enable else 0
        return self.shell(f"settings put system show_touches {val}")
        
    def toggle_layout_bounds(self, enable: bool):
        val = "true" if enable else "false"
        return self.shell(f"setprop debug.layout {val}; service call activity 1599295570") 
