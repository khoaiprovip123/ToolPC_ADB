# src/core/adb/adb_manager.py
"""
ADB Manager - Core wrapper for ADB commands
Handles device connection, command execution, and output parsing
"""

import subprocess
import os
import re
import time
import json
import sys
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from src.core.log_manager import LogManager


class ConnectionType(Enum):
    USB = "usb"
    WIRELESS = "wireless"


class DeviceStatus(Enum):
    ONLINE = "device"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    BOOTLOADER = "bootloader"
    RECOVERY = "recovery"


@dataclass
class DeviceInfo:
    """Device information model"""
    serial: str
    model: str
    manufacturer: str
    android_version: str
    sdk_version: int
    build_id: str
    connection_type: ConnectionType
    status: DeviceStatus
    ip_address: Optional[str] = None
    
    # Extended info
    miui_version: Optional[str] = None
    hyperos_version: Optional[str] = None
    battery_level: Optional[int] = None
    storage_used: Optional[int] = None
    storage_total: Optional[int] = None
    ram_available: Optional[int] = None
    ram_total: Optional[int] = None


class ADBManager:
    """
    Main ADB Manager class
    Provides high-level interface to ADB functionality
    """
    
    import sys
    
    def __init__(self, adb_path: Optional[str] = None):
        """
        Initialize ADB Manager
        
        Args:
            adb_path: Path to ADB binary. If None, will auto-detect
        """
        self.adb_path = adb_path or self._find_adb()
        self.current_device: Optional[str] = None
        self.logger = LogManager()
        
        # Load SoC Database
        self.soc_mappings = {}
        try:
            # Handle PyInstaller _MEIPASS
            if hasattr(sys, '_MEIPASS'):
                base_dir = Path(sys._MEIPASS)
            else:
                # src/core/adb/adb_manager.py -> ... -> root
                base_dir = Path(__file__).parent.parent.parent.parent
            
            db_path = base_dir / "src" / "data" / "soc_database.json"
            
            if db_path.exists():
                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.soc_mappings = data.get("mappings", {})
                    self.device_mappings = data.get("devices", {})   
            else:
                print(f"SoC Database not found at: {db_path}")
        except Exception as e:
            print(f"Failed to load SoC database: {e}")
        
        # Auto-install check
        if self.adb_path == "adb" and not self._check_adb_command():
             print("ADB not found in PATH. Attempting to download...")
             self.download_adb()
             
        self._verify_adb()
    
    def get_fastboot_system_info(self) -> Dict:
        """
        Get limited system info in Fastboot mode
        """
        info = {}
        try:
            # 1. Check if device is in fastboot
            devices = self.get_fastboot_devices()
            if not devices:
                return {}
                
            serial = devices[0]
            info["build_id"] = serial
            
            # 2. Get Product/Codename
            # fastboot getvar product -> product: lisa
            product_out = self.fastboot_command("getvar product")
            codename = "Unknown"
            
            if "product:" in product_out:
                # Output format usually: "product: lisa\nfinished. total time: ..."
                for line in product_out.split('\n'):
                    if line.startswith("product:"):
                        codename = line.split(":")[1].strip()
                        break
            
            info["board"] = codename
            info["device_name"] = codename
            
            # 3. Resolve Model Name from Database
            if hasattr(self, 'device_mappings') and codename in self.device_mappings:
                info["model"] = self.device_mappings[codename]
            else:
                info["model"] = f"Xiaomi Device ({codename})"
                
            # 4. Resolve SoC from Database
            if hasattr(self, 'soc_mappings') and codename in self.soc_mappings:
                info["soc_name"] = self.soc_mappings[codename]
            else:
                info["soc_name"] = "Fastboot Mode"
                
            info["os_version"] = "Fastboot Mode"
            info["android_version"] = "N/A"
            info["security_patch"] = "N/A"
            
            return info
            
        except Exception as e:
            print(f"Fastboot Info Error: {e}")
            return {}

    def _check_adb_command(self) -> bool:
        try:
            subprocess.run(["adb", "version"], capture_output=True, check=True)
            return True
        except:
            return False

    def _find_adb(self) -> str:
        """
        Find ADB binary in system or bundled resources
        """
        # 1. Check bundled resources (PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            bundled_adb = Path(sys._MEIPASS) / 'resources' / 'adb' / 'windows' / 'adb.exe'
            if bundled_adb.exists():
                return str(bundled_adb)
                
        # 2. Check local dev environment
        # src/core/adb/adb_manager.py -> ... -> root
        root_dir = Path(__file__).parent.parent.parent.parent
        dev_paths = [
            root_dir / 'resources' / 'adb' / 'windows' / 'adb.exe',
            root_dir / 'scripts' / 'adb.exe',
        ]
        
        for path in dev_paths:
            if path.exists():
                return str(path)
        
        # 3. Check system PATH
        try:
            cmd = ['where', 'adb'] if os.name == 'nt' else ['which', 'adb']
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        
        # Fallback
        return "adb"
    
    def download_adb(self) -> bool:
        """Download and extract ADB platform tools"""
        import urllib.request
        import zipfile
        import shutil
        
        try:
            # Define paths
            resources_dir = Path(__file__).parent.parent.parent.parent / 'resources' / 'adb' / 'windows'
            resources_dir.mkdir(parents=True, exist_ok=True)
            
            zip_path = resources_dir / "platform-tools.zip"
            adb_exe = resources_dir / "adb.exe"
            
            # URL for Windows platform tools
            url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
            
            # Download
            print(f"Downloading ADB from {url}...")
            urllib.request.urlretrieve(url, zip_path)
            
            # Extract
            print("Extracting ADB...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(resources_dir)
            
            # Move files from platform-tools folder to adb/windows if needed
            extracted_folder = resources_dir / "platform-tools"
            if extracted_folder.exists():
                for item in extracted_folder.iterdir():
                    shutil.move(str(item), str(resources_dir))
                shutil.rmtree(extracted_folder)
            
            # Cleanup zip
            if zip_path.exists():
                os.remove(zip_path)
                
            if adb_exe.exists():
                self.adb_path = str(adb_exe)
                print(f"ADB installed to {self.adb_path}")
                return True
            else:
                print("ADB executable not found after extraction.")
                return False
                
        except Exception as e:
            print(f"Failed to download/install ADB: {e}")
            return False

    def fix_connection(self) -> str:
        """
        Attempt to fix ADB connection issues
        Returns: Status message
        """
        log = []
        try:
            log.append("Stopping ADB server...")
            self.execute("kill-server", check=False)
            time.sleep(1)
            
            log.append("Starting ADB server...")
            self.execute("start-server", check=False)
            time.sleep(2)
            
            log.append("Checking devices...")
            devices = self.get_devices()
            
            if devices:
                return "\n".join(log) + f"\nSuccess: Found {len(devices)} device(s)."
            else:
                return "\n".join(log) + "\nWarning: No devices found after reset. Check USB cable/drivers."
                
        except Exception as e:
            return "\n".join(log) + f"\nError: {str(e)}"

    def _verify_adb(self):
        """Verify ADB is working"""
        try:
            result = self.execute("version", timeout=5)
            if "Android Debug Bridge version" not in result:
                # Try simple adb command if version check fails but command runs
                pass
        except Exception as e:
            # Don't crash if ADB check fails, just warn
            print(f"ADB verification warning: {str(e)}")
    
    def execute(self, command: str, timeout: int = 30, check: bool = True) -> str:
        """
        Execute ADB command
        """
        full_cmd = f'"{self.adb_path}" {command}' if os.path.isabs(self.adb_path) else f'{self.adb_path} {command}'
        
        try:
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            if check and result.returncode != 0:
                raise RuntimeError(
                    f"ADB command failed: {command}\n"
                    f"Error: {result.stderr}"
                )
            
            output = result.stdout.strip()
            
            # Log specific high-level commands
            if command.startswith("install ") and "Success" in output:
                LogManager.log("Cài đặt APK", f"Đã cài đặt thành công: {command.split()[-1]}", "success")
                
            return output
            
        except subprocess.TimeoutExpired:
            err_msg = f"Command timed out after {timeout}s: {command}"
            LogManager.log("ADB Timeout", err_msg, "error")
            raise TimeoutError(err_msg)
        except Exception as e:
            err_msg = str(e)
            # Filter noise
            if "dumpsys" not in command and "getprop" not in command:
                 LogManager.log("ADB Error", f"Cmd: {command}\n{err_msg}", "error")
            
            if check:
                raise RuntimeError(f"Failed to execute: {command}\nError: {err_msg}")
            return ""
    
    def shell(self, command: str, timeout: int = 30, check: bool = True) -> str:
        """
        Execute shell command on device
        """
        device_arg = f"-s {self.current_device}" if self.current_device else ""
        # Quote the command to prevent shell interpretation by host OS
        # Escape double quotes inside the command
        safe_command = command.replace('"', '\\"')
        return self.execute(f'{device_arg} shell "{safe_command}"', timeout=timeout, check=check)
    
    # ==================== Device Management ====================
    
    def get_devices(self) -> List[Tuple[str, DeviceStatus]]:
        """
        Get list of connected devices
        """
        output = self.execute("devices")
        devices = []
        
        for line in output.split('\n')[1:]:  # Skip header
            if '\t' in line:
                parts = line.split('\t')
                serial = parts[0].strip()
                status_str = parts[1].strip()
                
                # Map status string to enum
                status_map = {
                    'device': DeviceStatus.ONLINE,
                    'offline': DeviceStatus.OFFLINE,
                    'unauthorized': DeviceStatus.UNAUTHORIZED,
                    'bootloader': DeviceStatus.BOOTLOADER,
                    'recovery': DeviceStatus.RECOVERY,
                }
                status = status_map.get(status_str, DeviceStatus.OFFLINE)
                
                devices.append((serial, status))
        
        return devices
    
    def select_device(self, serial: str):
        """Set current device for operations"""
        self.current_device = serial
    
    def get_device_info(self) -> DeviceInfo:
        """
        Get comprehensive device information
        """
        if not self.current_device:
            raise RuntimeError("No device selected")
        
        # Basic properties
        props = self._get_device_properties()
        
        # Battery info
        battery = self.get_battery_info()
        
        # Storage info
        storage = self.get_storage_info()
        
        # Memory info
        memory = self.get_memory_info()
        
        # Determine connection type
        conn_type = (ConnectionType.WIRELESS 
                    if ':' in self.current_device 
                    else ConnectionType.USB)
        
        return DeviceInfo(
            serial=self.current_device,
            model=props.get('ro.product.model', 'Unknown'),
            manufacturer=props.get('ro.product.manufacturer', 'Unknown'),
            android_version=props.get('ro.build.version.release', 'Unknown'),
            sdk_version=int(props.get('ro.build.version.sdk', '0')),
            build_id=props.get('ro.build.id', 'Unknown'),
            connection_type=conn_type,
            status=DeviceStatus.ONLINE,
            ip_address=self._get_device_ip(),
            miui_version=props.get('ro.miui.ui.version.name', None),
            hyperos_version=props.get('ro.mi.os.version.name', None),
            battery_level=battery.get('level'),
            storage_used=storage.get('used'),
            storage_total=storage.get('total'),
            ram_available=memory.get('available'),
            ram_total=memory.get('total'),
        )
    
    def get_detailed_system_info(self) -> Dict:
        """
        Get detailed system specifications
        Returns format: {model, board, soc, ram, ...}
        """
        # Try primary logic (ADB)
        try:
            if not self.get_devices():
                 # No adb devices, maybe fastboot?
                 fb_info = self.get_fastboot_system_info()
                 return fb_info if fb_info else {}
                 
            # If devices exist but unexpected error
            props = self._get_device_properties()
            if not props:
                return {}
                
            def safe_shell(cmd):
                try: return self.shell(cmd).strip()
                except: return ""

            # Kernel Version
            kernel = safe_shell("uname -r")
            if "Unknown" in kernel or not kernel:
                proc_ver = safe_shell("cat /proc/version")
                if proc_ver:
                    parts = proc_ver.split()
                    if len(parts) > 2:
                        kernel = parts[2]

            # Baseband
            baseband = props.get("gsm.version.baseband", "Unknown")
            
            # CPU / SoC
            board = props.get("ro.board.platform", props.get("ro.product.board", "Unknown")).strip()
            soc_man = self.shell("getprop ro.soc.manufacturer").strip().title()
            soc_model = self.shell("getprop ro.soc.model").strip().upper()
            
            # Hardware field from cpuinfo
            hardware = ""
            try:
                cpu_out = self.shell("cat /proc/cpuinfo")
                for line in cpu_out.split('\n'):
                    if "Hardware" in line:
                         hardware = line.split(":")[1].strip()
                         break
            except:
                pass
                
            # Resolve Commercial Name using Database
            resolved_soc = self._resolve_soc_name(board, soc_model, hardware)
            if not resolved_soc:
                 # Fallback logic
                 if soc_man:
                     resolved_soc = f"{soc_man} {soc_model if soc_model else board}"
                 else:
                     resolved_soc = board.upper()

            # CPU Details
            cpu_info = self.get_cpu_info()
            cpu_cores = safe_shell("cat /proc/cpuinfo | grep processor | wc -l")
            
            # RAM Extended
            mem_info = self.get_memory_info()
            
            # Battery Level
            battery_level = 0
            try:
                dumpsys_batt = self.shell("dumpsys battery | grep level")
                if "level:" in dumpsys_batt:
                    battery_level = int(dumpsys_batt.split(":")[1].strip())
            except:
                pass

            # Storage Info
            storage_used = "0GB"
            storage_total = "0GB"
            storage_percent = 0
            try:
                df = self.shell("df -h /data")
                lines = df.split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        storage_total = parts[1]
                        storage_used = parts[2]
                        storage_percent = int(parts[4].replace('%', ''))
            except:
                pass

            # Security Patch, Screen, OS Version
            security_patch = props.get("ro.build.version.security_patch", "Unknown")
            
            wm_size_out = safe_shell("wm size")
            wm_size = "Unknown"
            if "Physical size:" in wm_size_out:
                wm_size = wm_size_out.split("Physical size:")[1].strip()

            wm_density_out = safe_shell("wm density")
            wm_density = "Unknown"
            if "Physical density:" in wm_density_out:
                wm_density = wm_density_out.split("Physical density:")[1].strip()
            
            hyperos = props.get("ro.mi.os.version.name")
            miui = props.get("ro.miui.ui.version.name")
            build_disp = props.get("ro.build.display.id", "Unknown")
            
            if hyperos:
                os_ver = f"HyperOS {hyperos}"
            elif miui:
                os_ver = f"MIUI {miui}"
            else:
                os_ver = build_disp
                
            # CODENAME / PRODUCT
            # ro.product.name or ro.build.product often holds the codename
            device_codename = props.get("ro.product.name", props.get("ro.build.product", "Unknown"))

            return {
                "model": props.get("ro.product.model", "Unknown"),
                "device_name": device_codename, # Codename
                "manufacturer": props.get("ro.product.manufacturer", "Unknown"),
                "brand": props.get("ro.product.brand", "Unknown"),
                "board": board,
                "soc_manufacturer": soc_man,
                "soc_model": soc_model,
                "soc_name": resolved_soc,
                "os_version": os_ver,
                "android_version": props.get("ro.build.version.release", "Unknown"),
                "sdk_version": props.get("ro.build.version.sdk", props.get("ro.build.version.sdk_int", "Unknown")),
                "security_patch": security_patch,
                "kernel": kernel,
                "baseband": baseband,
                "cpu_cores": cpu_cores,
                "cpu_freq": f"{max(cpu_info.get('frequencies', [0]))} MHz" if cpu_info.get('frequencies') else "Unknown",
                "ram_total": f"{mem_info.get('total', 0) / 1024:.1f} GB",
                "ram_percent": int(mem_info.get('used', 0) / mem_info.get('total', 1) * 100) if mem_info.get('total') else 0,
                "battery_level": battery_level,
                "storage_used": storage_used,
                "storage_total": storage_total,
                "storage_percent": storage_percent,
                "build_id": props.get("ro.build.id", "Unknown"),
                "wm_size": wm_size,
                "wm_density": wm_density,
            }
        except Exception as e:
            # Logic failed, maybe fastboot fallback?
            fb = self.get_fastboot_system_info()
            if fb: return fb
            
            print(f"Error getting system info: {e}")
            return {}

    def _get_device_properties(self) -> Dict[str, str]:
        """Get device properties via getprop"""
        output = self.shell("getprop")
        props = {}
        
        for line in output.split('\n'):
            match = re.match(r'\[(.*?)\]: \[(.*?)\]', line)
            if match:
                key, value = match.groups()
                props[key] = value
        
        return props
    
    def _get_device_ip(self) -> Optional[str]:
        """Get device IP address"""
        try:
            output = self.shell("ip addr show wlan0")
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', output)
            return match.group(1) if match else None
        except:
            return None
    
    # ==================== Connection Management ====================
    
    def connect_wireless(self, ip: str, port: int = 5555) -> bool:
        """
        Connect to device via TCP/IP
        """
        try:
            result = self.execute(f"connect {ip}:{port}", timeout=10)
            return "connected" in result.lower()
        except Exception:
            return False
    
    
    def get_language_region_status(self) -> Dict[str, str]:
        """Get current language and region settings"""
        props = self._get_device_properties()
        return {
            "Active Locale (persist.sys.locale)": props.get("persist.sys.locale", "Not Set"),
            "Factory Locale (ro.product.locale)": props.get("ro.product.locale", "Unknown"),
            "Region (persist.sys.country)": props.get("persist.sys.country", "Unknown"),
            "MIUI Region (ro.miui.region)": props.get("ro.miui.region", "Unknown"),
            "Time Format (system)": self.shell("settings get system time_12_24").strip(),
            "Timezone (persist.sys.timezone)": props.get("persist.sys.timezone", "Unknown"),
        }
    
    def disconnect_wireless(self, ip: str, port: int = 5555) -> bool:
        """Disconnect wireless connection"""
        try:
            result = self.execute(f"disconnect {ip}:{port}", timeout=5)
            return "disconnected" in result.lower()
        except Exception:
            return False
    
    def enable_wireless_adb(self, port: int = 5555) -> bool:
        """
        Enable wireless ADB on USB-connected device
        """
        try:
            self.shell(f"setprop service.adb.tcp.port {port}")
            self.shell("stop adbd")
            self.shell("start adbd")
            time.sleep(2)
            return True
        except Exception:
            return False
    
    def set_system_setting(self, namespace: str, key: str, value: str) -> bool:
        """
        Set system setting via settings put
        Args:
            namespace: system, secure, or global
            key: setting key
            value: setting value
        """
        try:
            # Quote value if it contains spaces
            if " " in value:
                value = f'"{value}"'
            self.shell(f"settings put {namespace} {key} {value}")
            return True
        except Exception as e:
            LogManager.log("ADB Error", f"Failed to set setting: {e}", "error")
            return False

    def set_prop(self, key: str, value: str) -> bool:
        """Set system property"""
        try:
            self.shell(f"setprop {key} {value}")
            return True
        except Exception:
            return False

    def grant_permission(self, package: str, permission: str) -> bool:
        """Grant permission to package"""
        try:
            result = self.shell(f"pm grant {package} {permission}")
            return "error" not in result.lower()
        except:
            return False

    def get_battery_info(self) -> Dict:
        """
        Get battery information
        """
        output = self.shell("dumpsys battery")
        info = {
            'level': None,
            'status': None,
            'health': None,
            'temperature': None,
            'voltage': None,
            'technology': None,
        }
        
        for line in output.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'level' in key:
                    info['level'] = int(value)
                elif 'status' in key:
                    info['status'] = value
                elif 'health' in key:
                    info['health'] = value
                elif 'temperature' in key:
                    info['temperature'] = int(value) / 10  # Convert to Celsius
                elif 'voltage' in key:
                    info['voltage'] = int(value) / 1000  # Convert to V
                elif 'technology' in key:
                    info['technology'] = value
        
        return info
    
    def get_storage_info(self) -> Dict:
        """
        Get storage information
        """
        info = {'total': 0, 'used': 0, 'free': 0}
        try:
            output = self.shell("df /data")
            lines = output.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 4:
                    # df output is usually in 1K blocks
                    info['total'] = int(parts[1]) * 1024
                    info['used'] = int(parts[2]) * 1024
                    info['free'] = int(parts[3]) * 1024
        except:
            pass
        return info

    def get_memory_info(self) -> Dict:
        """
        Get memory (RAM) information
        
        Returns:
            Dict with keys: total, available, cached (in MB)
        """
        output = self.shell("cat /proc/meminfo")
        info = {'total': 0, 'available': 0, 'cached': 0}
        
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().split()[0]  # Get number only
                
                try:
                    value_kb = int(value)
                    if 'MemTotal' in key:
                        info['total'] = value_kb // 1024
                    elif 'MemAvailable' in key:
                        info['available'] = value_kb // 1024
                    elif 'Cached' in key:
                        info['cached'] = value_kb // 1024
                except:
                    pass
        
        # Round total to nearest standard size (4GB, 6GB, 8GB, 12GB etc)
        # to look nicer on UI
        standard_sizes = [
            1024, 2048, 3072, 4096, 6144, 8192, 10240, 
            12288, 16384, 18432, 24576, 32768
        ]
        
        current_mb = info['total']
        for size in standard_sizes:
            if size >= current_mb:
                # Only upgrade if it's within reasonable range (e.g. > 80% of target)
                # To avoid mapping a weird 5GB virtual setup to 6GB?
                # But for physical devices, simply finding the next bucket is usually correct.
                info['total'] = size
                break
                
        return info
    
    def get_cpu_info(self) -> Dict:
        """
        Get CPU information
        """
        info = {'cores': 0, 'frequencies': []}
        try:
            # Count cores
            output = self.shell("cat /proc/cpuinfo")
            info['cores'] = output.count("processor")
            
            # Get max frequencies
            # Requires root usually to read scaling_max_freq for all, but try anyway
            freqs = []
            for i in range(info['cores']):
                try:
                    freq = self.shell(f"cat /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_max_freq").strip()
                    if freq.isdigit():
                        freqs.append(int(freq) // 1000) # Convert to MHz
                except:
                    pass
            info['frequencies'] = freqs
        except:
            pass
        return info
        
    def _resolve_soc_name(self, board, soc_model, hardware):
        """Map internal board codenames/models to commercial SoC names"""
        board = board.lower().strip()
        soc_model = soc_model.upper().strip()
        hardware = hardware.lower().strip()
        
        # Priority 1: Direct SoC Model mapping (SMxxxx)
        if soc_model:
             if soc_model.lower() in self.soc_mappings:
                 return self.soc_mappings[soc_model.lower()]
             # Try without suffix maybe? No, json has exact keys.
             
        # Priority 2: Board Codename mapping (lisa, alioth)
        if board in self.soc_mappings:
            return self.soc_mappings[board]
            
        # Priority 3: Hardware string (qcom, mt67xx)
        if hardware in self.soc_mappings:
            return self.soc_mappings[hardware]
            
        # Partial matches for Hardware
        if hardware:
            if "mt" in hardware or "dimensity" in hardware:
                 return f"MediaTek {hardware.title()}"
            if "sm" in hardware or "sd" in hardware:
                 return f"Snapdragon {hardware.upper()}"
        
        # Fallback
        if soc_model:
            return f"Snapdragon {soc_model}" if "SM" in soc_model else soc_model
            
        return None

    # ==================== Fastboot & Power ====================

    def reboot(self, mode: str = "normal"):
        """
        Reboot device
        Args:
            mode: 'normal', 'bootloader', 'recovery', 'fastbootd', 'edl'
        """
        cmd = "reboot"
        if mode == "bootloader":
            cmd += " bootloader"
        elif mode == "recovery":
            cmd += " recovery"
        elif mode == "fastbootd":
            cmd += " fastboot"
        elif mode == "edl":
            self.shell("reboot edl") # Some devices support this via shell
            return
            
        LogManager.log("Reboot", f"Đang khởi động lại ({mode})...", "info")
        self.execute(cmd, check=False)

    def shutdown(self):
        """Shutdown device"""
        LogManager.log("Shutdown", "Đang tắt nguồn thiết bị...", "info")
        self.shell("reboot -p", check=False)

    def fastboot_command(self, command: str) -> str:
        """Execute fastboot command"""
        # Assume fastboot is in the same dir as adb or in PATH
        fastboot_path = self.adb_path.replace("adb.exe", "fastboot.exe").replace("adb", "fastboot")
        if not os.path.exists(fastboot_path):
            fastboot_path = "fastboot"
            
        try:
            result = subprocess.run(
                f'"{fastboot_path}" {command}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() + result.stderr.strip()
        except Exception as e:
            return str(e)
    
    def get_fastboot_devices(self) -> List[str]:
        """Get devices in fastboot mode"""
        output = self.fastboot_command("devices")
        devices = []
        for line in output.split('\n'):
            if 'fastboot' in line:
                devices.append(line.split()[0])
        return devices

    def fastboot_reboot(self):
        """Reboot from Fastboot to System"""
        return self.fastboot_command("reboot")
        
    def fastboot_bootloader(self):
        """Reboot from Fastboot to Bootloader"""
        return self.fastboot_command("reboot-bootloader")
        
    def fastboot_reboot_recovery(self):
        """Reboot from Fastboot to Recovery"""
        # Try standard command first, then some oem fallbacks if needed
        return self.fastboot_command("reboot recovery")
        
    def fastboot_reboot_fastbootd(self):
        """Reboot from Fastboot to FastbootD"""
        return self.fastboot_command("reboot fastboot")
        
    def fastboot_reboot_edl(self):
        """Reboot from Fastboot to EDL"""
        return self.fastboot_command("oem edl")


    def fastboot_unlock_frp(self) -> str:
        """
        Unlock FRP (Factory Reset Protection)
        Uses 'fastboot erase frp' and 'fastboot erase config'
        """
        log = []
        
        # 0. Check connection
        devices = self.get_fastboot_devices()
        if not devices:
            return "❌ Lỗi: Không tìm thấy thiết bị Fastboot!"
            
        log.append(f"📱 Tìm thấy thiết bị: {devices[0]}")
        
        # 1. Erase FRP
        log.append("▶️ Thực thi: fastboot erase frp")
        res_frp = self.fastboot_command("erase frp")
        log.append(res_frp if res_frp else "OK")
        
        # 2. Erase Config (Xiaomi workaround)
        log.append("▶️ Thực thi: fastboot erase config")
        res_config = self.fastboot_command("erase config")
        log.append(res_config if res_config else "OK")
        
        log.append("\n✅ Đã gửi lệnh mở khóa FRP.")
        return "\n".join(log)

    def get_battery_health(self) -> Dict:
        """
        Refactored implementation of get_battery_health
        Using known device database for Design Capacity to avoid parsing errors.
        """
        
        # Database of Design Capacities (mAh)
        # Add more as discovered
        KNOWN_CAPACITIES = {
            "lisa": 4250,      # Mi 11 Lite 5G NE
            "renoir": 4250,    # Mi 11 Lite 5G
            "courbet": 4250,   # Mi 11 Lite 4G
            "alioth": 4520,    # Poco F3 / K40
            "munch": 4500,     # Poco F4 / K40S
            "marble": 5000,    # Poco F5
            "mondrian": 5160,  # Poco F5 Pro
            "haydn": 4520,     # Mi 11i / K40 Pro
            "star": 4600,      # Mi 11 Ultra
            "venus": 4600,     # Mi 11
            "thyme": 4600,     # Mi 10S
            "umi": 4780,       # Mi 10
            "cmi": 4780,       # Mi 10 Pro
            "cas": 4500,       # Mi 10 Ultra
            "apollo": 5000,    # Mi 10T / Pro
            "vayu": 5160,      # Poco X3 Pro
            "surya": 5160,     # Poco X3 NFC
            "sweet": 5020,     # Redmi Note 10 Pro
            "mojito": 5000,    # Redmi Note 10
            "sunny": 5000,     # Redmi Note 10S
            "pissarro": 4500,  # Redmi Note 11 Pro+
            "veux": 5000,      # Redmi Note 11 Pro 5G
            "fleur": 5000,     # Redmi Note 11S
            "spes": 5000,      # Redmi Note 11
            "ruby": 5000,      # Redmi Note 12 Pro / + / Discovery
            "tapas": 5000,     # Redmi Note 12
            "garnet": 5100,    # Redmi Note 13 Pro 5G
            "zircon": 5000,    # Redmi Note 13 Pro+
            "gold": 5000,      # Redmi Note 13
            # Tablets
            "nabu": 8720,      # Pad 5
            "pipa": 8840,      # Pad 6
            "yudi": 10000,     # Pad 6 Pro/Max
        }

        info = {
            "charge_full": 0,         # Real Full Capacity
            "charge_full_design": 0,  # Design Capacity
            "charge_current": 0,      # Current Charge stored
            "cycle_count": 0,
            "health_percent": 0,
            "technology": "Unknown",
            "wear_level_percent": 0,
            "status": "Unknown",
            "level": 0,
            "scale": 100,
            "voltage": 0,
            "temperature": 0,
            "debug_log": "",
            "is_estimated": False
        }
        
        log = []
        
        def safe_int(val, default=0):
            try: return int(float(val)) # float handles strings like '390.10'
            except: return default
            
        def clean_capacity(val):
             # Logic to normalize uAh/tens-uAh to mAh
             if val > 20000: 
                 if val > 1000000: # e.g. 4000000 -> 4000
                     val //= 1000
                 elif val > 100000: # e.g. 400000 -> 4000
                     val //= 100
                 else: # e.g. 40000 -> 4000
                     val //= 10
             return val

        try:
            # 0. Identify Device
            codename = "unknown"
            try:
                codename = self.shell("getprop ro.product.name").strip()
                if not codename: codename = self.shell("getprop ro.build.product").strip()
            except: pass
            
            # --- Method 1: Dumpsys Battery (Basics) ---
            dumpsys = self.shell("dumpsys battery")
            log.append(f"--- Dumpsys Battery ---\n{dumpsys}")
            
            for line in dumpsys.split('\n'):
                if ':' not in line: continue
                k, v = [x.strip() for x in line.split(':', 1)]
                
                if k == "status":
                    status_map = {"1": "Unknown", "2": "Charging", "3": "Discharging", "4": "Not charging", "5": "Full"}
                    info["status"] = status_map.get(v, v)
                elif k == "level": info["level"] = safe_int(v)
                elif k == "scale": info["scale"] = safe_int(v, 100)
                elif k == "voltage": info["voltage"] = safe_int(v) / 1000.0 # to Volts
                elif k == "temperature": info["temperature"] = safe_int(v) / 10.0
                elif k == "technology": info["technology"] = v
            
            # Extract Charge Counter
            match_cc = re.search(r"Charge counter: (\d+)", dumpsys)
            if match_cc:
                # Charge counter is usually in uAh
                cc = safe_int(match_cc.group(1))
                info["charge_current"] = clean_capacity(cc)

            # --- Method 2: Dumpsys Batterystats (Design Capacity) ---
            try:
                stats = self.shell("dumpsys batterystats")
                match_cap = re.search(r"Capacity: (\d+)", stats)
                if match_cap:
                    info["charge_full_design"] = safe_int(match_cap.group(1))
                    log.append(f"Found Design Capacity in stats: {info['charge_full_design']}")
            except Exception as e:
                log.append(f"Batterystats Error: {e}")

            # --- Method 3: SysFS Scan (Real Capacity) ---
            log.append("\n--- SysFS Scan ---")
            paths = [
                "/sys/class/power_supply/battery/",
                "/sys/class/power_supply/bms/", 
                "/sys/class/power_supply/main/"
            ]
            
            node_map = {
                "charge_full": ["charge_full", "energy_full", "batt_capacity_mah"], 
                "charge_full_design": ["charge_full_design", "energy_full_design", "batt_capacity_design_mah"],
                "cycle_count": ["cycle_count", "batt_cycle_count"]
            }
            
            for path in paths:
                for key, filenames in node_map.items():
                    if info[key] > 0 and key != 'cycle_count': continue # Keep scanning cycles if needed
                    
                    for fname in filenames:
                        val_str = self.shell(f"cat {path}{fname}", check=False).strip()
                        if val_str and val_str[0].isdigit():
                            log.append(f"Read {path}{fname} => {val_str}")
                            raw_val = safe_int(val_str)
                            
                            if key in ["charge_full", "charge_full_design"]:
                                val_cleaned = clean_capacity(raw_val)
                                if info[key] == 0: info[key] = val_cleaned
                            else:
                                info[key] = raw_val
            
            # --- Method 4: Logic Estimation & Calculation ---
            
            # Fallback 1: Use KNOWN database for Design Capacity
            # This is authoritative if available
            short_code = codename.split('_')[0] # handle 'lisa_global' etc
            if short_code in KNOWN_CAPACITIES:
                info["charge_full_design"] = KNOWN_CAPACITIES[short_code]
                log.append(f"Using Database Design Capacity for {short_code}: {info['charge_full_design']}")
            
            # Fallback 2: getprop
            if info["charge_full_design"] == 0:
                prop = self.shell("getprop ro.boot.battery.capacity").strip()
                if prop.isdigit(): info["charge_full_design"] = clean_capacity(safe_int(prop))

            # Fallback 3: Real Capacity Estimation
            # If we know Current Charge (mAh) and Level (%)
            if info["charge_full"] == 0 and info["charge_current"] > 0 and info["level"] > 0:
                # e.g. 2000 mAh at 50% -> 4000 mAh total
                est = int(info["charge_current"] / (info["level"] / 100.0))
                info["charge_full"] = est
                info["is_estimated"] = True
                log.append(f"Estimated Full Capacity: {est}")

            # --- SANITY CHECK: Real vs Design ---
            # If Real is much larger than Design, it's likely a scaling issue (uAh vs mAh)
            # e.g. Design 4250, Real 391100 -> needs /100 -> 3911
            cf = info["charge_full"]
            cfd = info["charge_full_design"]
            
            if cfd > 0 and cf > cfd * 1.5:
                log.append(f"Detected huge mismatch: Real {cf} vs Design {cfd}. Attempting rescale.")
                # Try simple divisors
                if cf > 1000000 and (cf / 1000) < (cfd * 1.2):
                    info["charge_full"] = int(cf / 1000)
                    log.append(f"Rescaled by 1000 -> {info['charge_full']}")
                elif (cf / 100) < (cfd * 1.2):
                    info["charge_full"] = int(cf / 100)
                    log.append(f"Rescaled by 100 -> {info['charge_full']}")
                elif (cf / 10) < (cfd * 1.2):
                    info["charge_full"] = int(cf / 10)
                    log.append(f"Rescaled by 10 -> {info['charge_full']}")
                else:
                    log.append("Could not auto-rescale safely.")

            # Calculate Health
            if info["charge_full"] > 0 and info["charge_full_design"] > 0:
                health = (info["charge_full"] / info["charge_full_design"]) * 100
                info["health_percent"] = round(health, 1) # Decimal for precision
                info["wear_level_percent"] = max(0, 100 - health) # Don't round yet for cleaner display? 
                # UI expects ints mostly but float is fine
                info["health_percent"] = int(health)
                info["wear_level_percent"] = max(0, 100 - int(health))
            
            info["debug_log"] = "\n".join(log)
            
        except Exception as e:
            print(f"Battery Health Error: {e}")
            info["debug_log"] += f"\nCritical Error: {e}"
            
        return info



    # ==================== Xiaomi Optimization ====================

    def disable_package(self, package_name: str) -> bool:
        """Disable a package"""
        try:
            result = self.shell(f"pm disable-user --user 0 {package_name}")
            success = "disabled" in result.lower() or "new state" in result.lower()
            if success:
                LogManager.log("Disable App", f"Đã tắt ứng dụng: {package_name}", "success")
            return success
        except:
            return False

    def enable_package(self, package_name: str) -> bool:
        """Enable a package"""
        try:
            result = self.shell(f"pm enable {package_name}")
            success = "enabled" in result.lower() or "new state" in result.lower()
            if success:
                LogManager.log("Enable App", f"Đã bật ứng dụng: {package_name}", "success")
            return success
        except:
            return False

    def uninstall_package(self, package_name: str) -> bool:
        """Uninstall a package for user 0"""
        try:
            result = self.shell(f"pm uninstall --user 0 {package_name}")
            success = "success" in result.lower()
            if success:
                LogManager.log("Uninstall App", f"Đã gỡ bỏ: {package_name}", "success")
            return success
        except:
            return False

    def set_system_property(self, key: str, value: str):
        """Set a system property (might require root or specific permissions)"""
        self.shell(f"setprop {key} {value}")

    def optimize_animations(self, scale: float = 0.5):
        """Set animation scales"""
        self.shell(f"settings put global window_animation_scale {scale}")
        self.shell(f"settings put global transition_animation_scale {scale}")
        self.shell(f"settings put global animator_duration_scale {scale}")

    def apply_smart_blur(self) -> str:
        """
        Auto-configure Control Center Blur based on device specs.
        """
        try:
            # Check RAM
            mem = self.get_memory_info()
            total_ram_mb = mem.get('total', 0)
            
            # Threshold: 6GB = 6144MB
            # If > 6GB, use Max settings. Else use Balanced.
            if total_ram_mb >= 6000:
                mode = "Max Performance (v:1,c:3,g:3)"
                val = "v:1,c:3,g:3"
                desc = "Đã kích hoạt Blur mức cao nhất cho máy cấu hình mạnh."
            else:
                mode = "Balanced (v:1,c:2,g:2)"
                val = "v:1,c:2,g:2"
                desc = "Đã kích hoạt Blur mức tối ưu cho máy cấu hình trung bình."
                
            self.shell(f"settings put global deviceLevelList {val}")
            
            LogManager.log("Smart Blur", f"Applied {mode}", "success")
            return f"{desc}\n(Mode: {mode})"
            
        except Exception as e:
            return f"Lỗi: {e}"

    def disable_msa(self) -> bool:
        """Disable MIUI System Ads"""
        return self.disable_package("com.miui.msa.global")

    def disable_analytics(self) -> bool:
        """Disable MIUI Analytics"""
        return self.disable_package("com.miui.analytics")

    # ==================== System Cleaner ====================

    def clean_app_cache(self) -> str:
        """
        Clean app caches using trim-caches.
        Frees up space by deleting non-essential cache files.
        """
        try:
            # 256G is a target free space, forcing Android to trim caches to reach it.
            # It won't delete data, just caches.
            result = self.shell("pm trim-caches 256g")
            msg = "✅ Đã gửi lệnh dọn dẹp Cache"
            LogManager.log("Cleaner", msg, "success")
            return msg
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def clean_obsolete_dex(self) -> str:
        """
        Prune obsolete dex files (prune-dex-opt).
        Removes odex files for apps that no longer exist or are updated.
        """
        try:
            # check=False prevents raising exception on failure
            result = self.shell("cmd package prune-dex-opt", check=False)
            msg = "✅ Đã dọn dẹp Dex lỗi thời"
            LogManager.log("Cleaner", msg, "success")
            return msg
        except Exception as e:
            # Just ignore if failed, likely not supported or permission denied
            return f"⚠️ Bỏ qua Dex Opt"

    def clean_messenger_data(self) -> str:
        """
        Clean Telegram/Nekogram cache.
        Warning: This deletes cache folders.
        """
        try:
            targets = [
                "/sdcard/Telegram/Telegram Images",
                "/sdcard/Telegram/Telegram Video",
                "/sdcard/Telegram/Telegram Audio",
                "/sdcard/Telegram/Telegram Documents",
                "/sdcard/Android/data/org.telegram.messenger/cache",
                "/sdcard/Android/data/tw.nekomimi.nekogram/cache"
            ]
            
            count = 0
            for path in targets:
                # Check if exists first to avoid scary errors? rm -rf is silent usually.
                self.shell(f"rm -rf \"{path}\"")
                count += 1
                
            msg = f"✅ Đã dọn dẹp {count} thư mục rác Telegram"
            LogManager.log("Cleaner", msg, "success")
            return msg
        except Exception as e:
            return f"❌ Lỗi: {e}"

    # ==================== Advanced Optimization ====================

    def optimize_notifications(self, packages: str) -> str:
        """
        Add packages to Doze whitelist for instant notifications.
        Args:
            packages: Comma separated package names
        """
        try:
            pkg_list = [p.strip() for p in packages.split(',')]
            count = 0
            for pkg in pkg_list:
                if not pkg: continue
                # dumpsys deviceidle whitelist +com.package
                self.shell(f"dumpsys deviceidle whitelist +{pkg}")
                count += 1
            msg = f"✅ Đã thêm {count} ứng dụng vào Whitelist (Tối ưu thông báo)"
            LogManager.log("Optimization", msg, "success")
            return msg
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def compile_apps(self, mode: str, timeout: int = 900) -> str:
        """
        Compile apps using 'cmd package compile'.
        Modes:
        - speed: Max performance
        - quicken: Battery/Storage balance
        - speed-profile: Daily use (based on usage)
        - verify: Fast install / First boot
        - everything: Full optimization (slowest)
        """
        try:
            # -a means all apps
            # -f means force
            cmd = f"cmd package compile -m {mode} -a"
            # This can take a long time, so we might want to run it in background or just return 'started'
            # But here we wait for result usually.
            result = self.shell(cmd, timeout=timeout)
            if "Success" in result or "Success" in result: # Sometimes output varies
                msg = f"✅ Tối ưu hóa (Mode: {mode}) hoàn tất!"
                LogManager.log("Compilation", msg, "success")
                return msg
            return f"⚠️ Kết quả: {result}"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    # ==================== File Transfer ====================
    
    def push_file(self, local_path: str, remote_path: str) -> bool:
        """Push file to device"""
        try:
            # Use quotes for paths to handle spaces
            self.execute(f"push \"{local_path}\" \"{remote_path}\"")
            LogManager.log("Push File", f"Đã gửi file: {os.path.basename(local_path)}", "success")
            return True
        except Exception:
            return False

    def pull_file(self, remote_path: str, local_path: str) -> bool:
        """Pull file from device"""
        try:
            self.execute(f"pull \"{remote_path}\" \"{local_path}\"")
            LogManager.log("Pull File", f"Đã lấy file: {os.path.basename(remote_path)}", "success")
            return True
        except Exception:
            return False

    # ==================== Quick Controls ====================

    def set_brightness(self, level: int):
        """Set screen brightness (0-255)"""
        # Ensure range
        level = max(0, min(255, level))
        self.shell(f"settings put system screen_brightness {level}", check=False)

    def set_volume(self, level: int):
        """Set media volume (0-15 typically)"""
        # Using cmd media_session if available
        self.shell(f"cmd media_session volume --stream 3 --set {level}", check=False)

    def toggle_show_taps(self, enable: bool):
        """Toggle 'Show Taps' visual feedback"""
        val = "1" if enable else "0"
        self.shell(f"settings put system show_touches {val}", check=False)

    def toggle_layout_bounds(self, enable: bool):
        """Toggle 'Show Layout Bounds'"""
        val = "true" if enable else "false"
        self.shell(f"setprop debug.layout {val}", check=False)
        # Force refresh (poke service)
    def set_language_vietnamese(self) -> str:
        """
        Force set system language to Vietnamese via ADB properties.
        Requires reboot to take effect.
        """
        try:
            # Set properties
            self.shell("setprop persist.sys.language vi")
            self.shell("setprop persist.sys.country VN")
            self.shell("setprop persist.sys.locale vi-VN")
            
            # Additional for some Xiaomi ROMs
            # self.shell("setprop ro.product.locale vi-VN") # Usually RO
            self.shell("setprop persist.sys.timezone Asia/Ho_Chi_Minh")
            
            return "Đã gửi lệnh. Vui lòng KHỞI ĐỘNG LẠI máy để áp dụng."
        except Exception as e:
            return f"Lỗi: {e}"

    def skip_setup_wizard(self) -> str:
        """
        Skip Android Setup Wizard (Bypass FRP/Account Login after reset).
        """
        try:
            # 1. Mark setup as complete
            self.shell("settings put secure user_setup_complete 1")
            self.shell("settings put global device_provisioned 1")
            
            # 2. Try to disable setup wizard packages (Google & Xiaomi)
            # This prevents it from popping up again
            self.shell("pm disable-user --user 0 com.google.android.setupwizard")
            self.shell("pm disable-user --user 0 com.android.provision")
            self.shell("pm disable-user --user 0 com.miui.provision")
            
            # 3. Force go to Home Screen
            self.shell("am start -c android.intent.category.HOME -a android.intent.action.MAIN")
            
            return "✅ Đã bỏ qua Setup Wizard! (Nếu chưa vào được màn hình chính, hãy khởi động lại)"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def disable_miui_ota(self) -> str:
        """Disable MIUI System Updater"""
        try:
            pkgs = ["com.android.updater", "com.miui.updater", "com.miui.android.qt"]
            count = 0
            for p in pkgs:
                 if self.disable_package(p): count += 1
            return f"✅ Đã chặn cập nhật hệ thống ({count} packages disabled)"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def set_refresh_rate(self, hz_value: int) -> str:
        """Force specific Refresh Rate (Hz) or Reset"""
        try:
            if hz_value > 0:
                self.shell(f"settings put system user_refresh_rate {hz_value}")
                self.shell(f"settings put system peak_refresh_rate {hz_value}")
                self.shell(f"settings put system min_refresh_rate {hz_value}")
                return f"✅ Đã ép xung màn hình {hz_value}Hz"
            else:
                # Reset to auto/default
                self.shell("settings put system user_refresh_rate 0") 
                self.shell("settings delete system peak_refresh_rate")
                self.shell("settings delete system min_refresh_rate")
                return "✅ Đã đặt lại tần số quét (Auto)"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def force_dark_mode(self, enable: bool) -> str:
        """Force System-wide Dark Mode"""
        try:
            # 1. Standard Settings
            val = "2" if enable else "1" # 2: Yes, 1: No
            self.shell(f"settings put secure ui_night_mode {val}")
            
            # 2. Command Line Interface (More effective on A10+)
            mode = "yes" if enable else "no"
            self.shell(f"cmd uimode night {mode}")
            
            # 3. Developer Option Force Dark
            self.shell("setprop debug.hwui.force_dark true" if enable else "setprop debug.hwui.force_dark false")
            
            return "✅ Đã gửi lệnh Dark Mode. (Có thể cần khởi động lại ứng dụng hoặc máy để áp dụng)"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def hide_navigation_bar(self, hide: bool) -> str:
        """Hide/Show Navigation Bar (Switch to Gestures)"""
        try:
            if hide:
                # 1. Enable Full Screen Gestures (Xiaomi Legacy)
                self.shell("settings put global force_fsg_nav_bar 1")
                
                # 2. Standard Android Gestures
                self.shell("settings put secure navigation_mode 2")
                
                # 3. Hide Gesture Line/Indicator (HyperOS/MIUI)
                self.shell("settings put global hide_gesture_line 1")
                self.shell("settings put system hide_gesture_line 1") # Try system table too
                
                return "✅ Đã ẩn thanh điều hướng & Vạch kẻ (Full Screen)"
            else:
                # Show 3-Buttons
                self.shell("settings put global force_fsg_nav_bar 0")
                self.shell("settings put secure navigation_mode 0")
                self.shell("settings put global hide_gesture_line 0")
                return "✅ Đã hiện lại 3 phím điều hướng"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def show_refresh_rate_overlay(self, show: bool) -> str:
        """Show/Hide Refresh Rate FPS overlay"""
        try:
            val = "1" if show else "0"
            
            # 1. Developer Options Setting
            # Ensure Dev Options is "seen" as enabled for this to take effect
            self.shell("settings put global development_settings_enabled 1")
            
            self.shell(f"settings put system show_refresh_rate_overlay {val}")
            self.shell(f"settings put global show_refresh_rate_overlay {val}")
            self.shell(f"settings put secure show_refresh_rate_overlay {val}")
            
            # 2. SurfaceFlinger Service Call (Root/ADB magic)
            # Codes change every Android version:
            # A11: 1008
            # A12/A13: 1034
            # A14 (HyperOS): 1042 or 1035
            codes = [1008, 1034, 1035, 1042] 
            
            for code in codes:
                try:
                    self.shell(f"service call SurfaceFlinger {code} i32 {val}")
                except:
                    pass

            return "✅ Đã kích hoạt Show FPS (Hỗ trợ cả Android 14/HyperOS)" if show else "✅ Đã tắt FPS Monitor"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def open_developer_options(self) -> str:
        """Open Developer Options Screen"""
        try:
            self.shell("am start -a com.android.settings.APPLICATION_DEVELOPMENT_SETTINGS")
            return "✅ Đã mở Cài đặt cho nhà phát triển"
        except Exception as e:
            return f"❌ Lỗi: {e}"

    def set_display_density(self, dpi: int) -> str:
        """Set Display Density (DPI)"""
        try:
            if dpi <= 0:
                self.shell("wm density reset")
                return "✅ Đã đặt lại DPI gốc"
            else:
                self.shell(f"wm density {dpi}")
                return f"✅ Đã đổi DPI sang {dpi}"
        except Exception as e:
            return f"❌ Lỗi: {e}"
            
    def toggle_layout_bounds(self, enable: bool):
        """Toggle 'Show Layout Bounds'"""
        val = "true" if enable else "false"
        self.shell(f"setprop debug.layout {val}", check=False)
        # Force refresh (poke service)
        self.shell("service call activity 1599295570", check=False)
