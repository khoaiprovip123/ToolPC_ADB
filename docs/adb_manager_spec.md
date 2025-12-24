# ADB MANAGER PRO - TÀI LIỆU ĐẶC TẢ KỸ THUẬT

## PHẦN 1: TỔNG QUAN DỰ ÁN

### 1.1 Mục tiêu
Xây dựng ứng dụng desktop quản lý thiết bị Android qua ADB với:
- Giao diện hiện đại, thân thiện
- Tính năng đầy đủ, chuyên sâu cho Xiaomi
- Tự động hóa cao, hỗ trợ multi-device
- Đóng gói standalone, không cần cài đặt

### 1.2 Phạm vi chức năng
**Core Features (MVP):**
1. Kết nối thiết bị (USB/Wireless)
2. Dashboard giám sát real-time
3. Quản lý ứng dụng (enable/disable/uninstall)
4. Cài đặt/Gỡ/Backup APK
5. File Manager (browse/push/pull)
6. Screen Mirroring & Control
7. DNS Configuration
8. Xiaomi Debloat & Optimization

**Advanced Features:**
9. Multi-device management
10. Automation Scripts (record/replay)
11. Cloud Sync (settings/scripts)
12. OTA ROM Downloader
13. Real-time Logcat Viewer
14. Device Profiles & Presets
15. Batch Operations
16. Plugin System

### 1.3 Đối tượng người dùng
- **Primary**: Power users, Android enthusiasts, Xiaomi users
- **Secondary**: Developers, Technical support staff
- **Tertiary**: Enterprises managing device fleets

---

## PHẦN 2: KIẾN TRÚC HỆ THỐNG

### 2.1 Tech Stack

| Layer | Technology | Version | Lý do chọn |
|-------|-----------|---------|-----------|
| UI Framework | PySide6 | 6.6+ | Qt6, modern, cross-platform |
| Language | Python | 3.11+ | Rapid dev, rich ecosystem |
| ADB Interface | subprocess + pure-python-adb | latest | Flexibility + fallback |
| Database | SQLite3 | 3.40+ | Embedded, no server |
| Screen Mirroring | scrcpy | 2.3+ | Low latency, best quality |
| Packaging | PyInstaller + Nuitka | latest | Single exe, performance |
| Logging | loguru | 0.7+ | Better than standard logging |
| Config | pydantic-settings | 2.1+ | Type-safe config |
| HTTP Client | httpx | 0.26+ | For OTA downloads |

### 2.2 Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────┐
│              PRESENTATION LAYER                 │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │Dashboard │ Apps     │ Files    │ Screen   │  │
│  │Widget    │ Widget   │ Widget   │ Widget   │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
│           MainWindow (QMainWindow)              │
└─────────────────────────────────────────────────┘
                       ↓↑
┌─────────────────────────────────────────────────┐
│               BUSINESS LOGIC LAYER              │
│  ┌──────────────────────────────────────────┐   │
│  │      DeviceManager (Orchestrator)        │   │
│  └──────────────────────────────────────────┘   │
│  ┌─────────┬──────────┬──────────┬──────────┐   │
│  │ ADB     │ Xiaomi   │ Script   │ Cloud    │   │
│  │ Manager │ Optimizer│ Engine   │ Sync     │   │
│  └─────────┴──────────┴──────────┴──────────┘   │
└─────────────────────────────────────────────────┘
                       ↓↑
┌─────────────────────────────────────────────────┐
│                 DATA LAYER                      │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │ SQLite   │ Config   │ Logs     │ Cache    │  │
│  │ DB       │ Files    │ Files    │ Files    │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────┘
                       ↓↑
┌─────────────────────────────────────────────────┐
│              EXTERNAL INTERFACES                │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │ ADB      │ Scrcpy   │ Cloud    │ Plugin   │  │
│  │ Binary   │ Binary   │ APIs     │ APIs     │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────┘
```

### 2.3 Cấu trúc thư mục chi tiết

```
adb-manager-pro/
├── src/
│   ├── main.py                          # Entry point
│   │
│   ├── ui/                              # UI Layer
│   │   ├── __init__.py
│   │   ├── main_window.py               # MainWindow class
│   │   ├── components/                  # Reusable components
│   │   │   ├── sidebar.py
│   │   │   ├── statusbar.py
│   │   │   ├── device_selector.py
│   │   │   └── dialogs.py
│   │   ├── widgets/                     # Feature widgets
│   │   │   ├── dashboard.py
│   │   │   ├── app_manager.py
│   │   │   ├── apk_manager.py
│   │   │   ├── file_manager.py
│   │   │   ├── screen_mirror.py
│   │   │   ├── dns_config.py
│   │   │   ├── xiaomi_optimizer.py
│   │   │   ├── script_engine.py
│   │   │   ├── logcat_viewer.py
│   │   │   ├── ota_downloader.py
│   │   │   └── settings.py
│   │   └── styles/                      # QSS Themes
│   │       ├── dark_theme.qss
│   │       ├── light_theme.qss
│   │       └── xiaomi_theme.qss
│   │
│   ├── core/                            # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── adb/
│   │   │   ├── adb_manager.py           # ADB wrapper
│   │   │   ├── device.py                # Device model
│   │   │   └── commands.py              # Command constants
│   │   ├── managers/
│   │   │   ├── device_manager.py        # Multi-device orchestrator
│   │   │   ├── app_manager.py           # App logic
│   │   │   ├── file_manager.py          # File operations
│   │   │   └── package_manager.py       # APK operations
│   │   ├── xiaomi/
│   │   │   ├── optimizer.py             # Xiaomi optimization
│   │   │   ├── bloatware.py             # Bloatware database
│   │   │   ├── tweaks.py                # MIUI tweaks
│   │   │   └── models.py                # Device models database
│   │   ├── automation/
│   │   │   ├── script_engine.py         # Script execution
│   │   │   ├── recorder.py              # Action recorder
│   │   │   └── scheduler.py             # Task scheduler
│   │   ├── cloud/
│   │   │   ├── sync_manager.py          # Cloud sync
│   │   │   ├── providers.py             # Cloud providers
│   │   │   └── encryption.py            # Data encryption
│   │   └── plugins/
│   │       ├── plugin_manager.py        # Plugin system
│   │       └── base_plugin.py           # Plugin interface
│   │
│   ├── models/                          # Data Models
│   │   ├── __init__.py
│   │   ├── device.py
│   │   ├── app.py
│   │   ├── script.py
│   │   └── profile.py
│   │
│   ├── database/                        # Database Layer
│   │   ├── __init__.py
│   │   ├── db_manager.py
│   │   ├── migrations/
│   │   │   ├── 001_initial.sql
│   │   │   ├── 002_add_scripts.sql
│   │   │   └── 003_add_profiles.sql
│   │   └── repositories/
│   │       ├── device_repo.py
│   │       ├── script_repo.py
│   │       └── profile_repo.py
│   │
│   ├── utils/                           # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py                    # Logging setup
│   │   ├── config.py                    # Configuration
│   │   ├── helpers.py                   # Helper functions
│   │   ├── validators.py                # Input validation
│   │   ├── parsers.py                   # Output parsers
│   │   └── decorators.py                # Custom decorators
│   │
│   └── resources/                       # Static Resources
│       ├── adb/                         # ADB binaries
│       │   ├── windows/
│       │   │   ├── adb.exe
│       │   │   ├── AdbWinApi.dll
│       │   │   └── AdbWinUsbApi.dll
│       │   ├── linux/
│       │   │   └── adb
│       │   └── macos/
│       │       └── adb
│       ├── scrcpy/                      # Scrcpy binaries
│       │   ├── windows/
│       │   │   ├── scrcpy.exe
│       │   │   └── scrcpy-server
│       │   └── ...
│       ├── icons/                       # UI Icons
│       │   ├── app_icon.ico
│       │   ├── dashboard.svg
│       │   ├── apps.svg
│       │   └── ...
│       ├── fonts/                       # Custom fonts
│       │   └── Roboto/
│       ├── data/                        # Static data
│       │   ├── xiaomi_bloatware.json
│       │   ├── device_models.json
│       │   └── rom_sources.json
│       └── translations/                # i18n
│           ├── en_US.json
│           └── vi_VN.json
│
├── tests/                               # Unit Tests
│   ├── test_adb_manager.py
│   ├── test_device_manager.py
│   └── test_xiaomi_optimizer.py
│
├── docs/                                # Documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   └── USER_GUIDE.md
│
├── scripts/                             # Build Scripts
│   ├── build_windows.bat
│   ├── build_linux.sh
│   └── setup_dev.py
│
├── requirements.txt                     # Python dependencies
├── requirements-dev.txt                 # Dev dependencies
├── build.spec                           # PyInstaller config
├── .env.example                         # Environment template
├── config.yaml                          # Default config
└── README.md
```

---

## PHẦN 3: CHI TIẾT CHỨC NĂNG

### 3.1 Module 1: Device Connection & Management

#### 3.1.1 Use Cases
**UC-001: Kết nối USB**
- **Actor**: User
- **Precondition**: Device có USB debugging enabled
- **Flow**:
  1. User cắm USB cable
  2. System auto-detect device
  3. System request ADB authorization
  4. User confirm trên device
  5. System hiển thị device info
- **Postcondition**: Device connected, ready for commands

**UC-002: Kết nối Wireless**
- **Actor**: User
- **Precondition**: Device và PC cùng network
- **Flow**:
  1. User nhập IP device hoặc scan network
  2. System attempt connect qua port 5555
  3. System verify connection
  4. System save connection profile
- **Postcondition**: Wireless connection established

**UC-003: Multi-device Management**
- **Actor**: User
- **Precondition**: Multiple devices connected
- **Flow**:
  1. System list all connected devices
  2. User select primary device
  3. System display multi-device dashboard
  4. User can switch between devices
  5. User can batch operations across devices

#### 3.1.2 Technical Specifications

**ADB Commands:**
```bash
# USB Connection
adb devices -l                           # List with details
adb -s <serial> shell                    # Specify device

# Wireless Connection
adb tcpip 5555                           # Enable wireless
adb connect <ip>:5555                    # Connect
adb disconnect <ip>:5555                 # Disconnect

# Device Info
adb shell getprop ro.product.model       # Model
adb shell getprop ro.build.version.release  # Android version
adb shell getprop ro.product.manufacturer   # Manufacturer
adb shell getprop ro.serialno            # Serial number
```

**Data Model:**
```python
@dataclass
class Device:
    serial: str
    model: str
    manufacturer: str
    android_version: str
    connection_type: Literal['usb', 'wireless']
    ip_address: Optional[str]
    status: Literal['online', 'offline', 'unauthorized']
    last_connected: datetime
    profile_id: Optional[int]
```

---

### 3.2 Module 2: Dashboard (Real-time Monitoring)

#### 3.2.1 Metrics Display

**Primary Metrics:**
1. **Device Overview**
   - Model, Android version, MIUI version
   - Serial number, IMEI
   - Connection status, uptime

2. **Battery Status**
   - Current level (%)
   - Status (charging/discharging/full)
   - Health, temperature
   - Voltage, current
   - Technology (Li-ion/Li-poly)

3. **Storage**
   - Internal: Used/Total
   - SD Card: Used/Total
   - App data breakdown
   - Cache size

4. **Memory (RAM)**
   - Available/Total
   - Used percentage
   - Cached memory
   - Top memory consumers

5. **CPU**
   - Current frequency
   - Governor mode
   - Temperature
   - Per-core usage

6. **Network**
   - Active connection (WiFi/Mobile)
   - IP address, MAC
   - Download/Upload speed
   - Data usage (today/total)

**ADB Commands:**
```bash
# Battery
adb shell dumpsys battery

# Storage
adb shell df /data
adb shell df /sdcard

# Memory
adb shell cat /proc/meminfo
adb shell dumpsys meminfo

# CPU
adb shell cat /proc/cpuinfo
adb shell cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq
adb shell dumpsys thermal

# Network
adb shell ip addr
adb shell dumpsys connectivity
```

#### 3.2.2 Real-time Charts
- Line chart: CPU usage (last 60s, update every 1s)
- Area chart: Memory usage (last 5min, update every 5s)
- Bar chart: Network speed (last 30s, update every 1s)
- Gauge: Battery level, temperature

**Chart Library**: Use `pyqtgraph` for high-performance real-time plotting

---

### 3.3 Module 3: App Manager

#### 3.3.1 Features

**Display:**
- List all packages (system/user filter)
- Show: Icon, Name, Package, Version, Size, Status
- Sort by: Name, Size, Install date
- Search & filter

**Operations:**
- Enable/Disable app
- Force stop
- Clear cache
- Clear data
- Uninstall (user apps)
- Disable bloatware (system apps)
- Backup APK
- View app info
- Open app settings on device

**Batch Operations:**
- Select multiple apps
- Bulk enable/disable
- Bulk uninstall
- Bulk backup

#### 3.3.2 ADB Commands

```bash
# List packages
adb shell pm list packages -f           # All with path
adb shell pm list packages -s           # System only
adb shell pm list packages -3           # User only
adb shell pm list packages -e           # Enabled only
adb shell pm list packages -d           # Disabled only

# App info
adb shell dumpsys package <pkg>         # Full info
adb shell pm dump <pkg>                 # Alternative

# Operations
adb shell pm enable <pkg>               # Enable
adb shell pm disable-user <pkg>         # Disable
adb shell am force-stop <pkg>           # Force stop
adb shell pm clear <pkg>                # Clear data
adb uninstall <pkg>                     # Uninstall
adb shell pm uninstall -k --user 0 <pkg>  # Uninstall for user 0

# Backup APK
adb shell pm path <pkg>                 # Get APK path
adb pull /data/app/<pkg>/base.apk      # Pull APK
```

---

### 3.4 Module 4: APK Manager

#### 3.4.1 Features

**Install:**
- Single APK install
- Batch install (folder)
- Install queue with progress
- Auto-retry on failure
- Install options: -r (replace), -t (test APK), -d (downgrade)

**Uninstall:**
- Single/Batch uninstall
- Keep data option (-k flag)

**Backup:**
- Backup installed APK to PC
- Backup with data (requires root)
- Auto-organize: /backups/{package}/{version}/

**APK Info:**
- Parse APK manifest
- Show: Package, Version, Permissions, Min SDK, Target SDK
- Icon extraction

#### 3.4.2 Implementation

```python
class APKManager:
    def install_apk(self, apk_path: str, options: list = ['-r']):
        """
        Install APK with options
        -r: Replace existing
        -t: Allow test APKs
        -d: Allow downgrade
        -g: Grant all permissions
        """
        
    def install_batch(self, apk_list: List[str]):
        """Install multiple APKs with queue"""
        
    def backup_apk(self, package: str, output_dir: str):
        """Backup APK from device"""
        
    def parse_apk_info(self, apk_path: str) -> APKInfo:
        """Extract info from APK (use aapt)"""
```

---

### 3.5 Module 5: File Manager

#### 3.5.1 Features

**Browse:**
- Two-pane: Device | PC
- Navigate device filesystem
- Show file size, date, permissions
- Icons by file type
- Quick access: DCIM, Download, Documents, Movies

**Operations:**
- Push file/folder to device
- Pull file/folder from device
- Delete file/folder
- Rename
- Create folder
- Change permissions (chmod)
- Drag & drop support

**Advanced:**
- Sync folder (bi-directional)
- Batch operations
- Progress indicator for large transfers
- Resume on failure

#### 3.5.2 ADB Commands

```bash
# List files
adb shell ls -la /sdcard/

# Push/Pull
adb push local_path device_path
adb pull device_path local_path

# Operations
adb shell rm -rf /sdcard/path           # Delete
adb shell mv /old/path /new/path        # Move/Rename
adb shell mkdir /sdcard/newfolder       # Create folder
adb shell chmod 777 /sdcard/file        # Change permissions
```

---

### 3.6 Module 6: Screen Mirroring

#### 3.6.1 Approach: Integrate Scrcpy

**Scrcpy Advantages:**
- Low latency (30-60ms)
- High quality (H.264)
- Touch control
- Keyboard input
- Copy/paste sync
- Screen recording
- No root required

**Integration:**
```python
class ScreenMirror:
    def __init__(self, device_serial: str):
        self.scrcpy_path = get_scrcpy_binary()
        self.device = device_serial
        
    def start_mirror(self, 
                     bitrate: int = 8000000,
                     max_size: int = 1920,
                     framerate: int = 60):
        """
        Start scrcpy with options
        """
        cmd = [
            self.scrcpy_path,
            '--serial', self.device,
            '--bit-rate', str(bitrate),
            '--max-size', str(max_size),
            '--max-fps', str(framerate),
            '--stay-awake',
            '--turn-screen-off',  # Optional
        ]
        subprocess.Popen(cmd)
        
    def screenshot(self, output_path: str):
        """Take screenshot"""
        self.adb.shell(f'screencap -p > {output_path}')
        
    def record_screen(self, output_path: str, duration: int):
        """Record screen"""
        cmd = f'screenrecord --time-limit {duration} /sdcard/record.mp4'
        self.adb.shell(cmd)
        self.adb.pull('/sdcard/record.mp4', output_path)
```

#### 3.6.2 Features
- One-click mirroring
- Adjustable quality/bitrate
- Screenshot button
- Screen recording (with timer)
- Touch control toggle
- Fullscreen mode
- Picture-in-Picture (floating window)

---

### 3.7 Module 7: DNS Configuration

#### 3.7.1 Features

**Private DNS:**
- Quick select: Google, Cloudflare, AdGuard, Quad9
- Custom hostname
- Auto-detect & test connection
- Fallback on failure

**Custom DNS:**
- Set DNS1, DNS2
- Per-network configuration
- IPv4/IPv6 support

#### 3.7.2 Commands

```bash
# Private DNS (Android 9+)
adb shell settings put global private_dns_mode hostname
adb shell settings put global private_dns_specifier dns.google

# Legacy DNS (requires root)
adb shell setprop net.dns1 8.8.8.8
adb shell setprop net.dns2 8.8.4.4
```

---

### 3.8 Module 8: Xiaomi Optimizer (Debloat & Tweaks)

#### 3.8.1 Bloatware Database

**Categories:**
1. **Safe to Remove** (100+ packages)
   - Analytics: com.miui.analytics, com.miui.msa.global
   - Ads: com.xiaomi.joyose
   - Redundant: GetApps, Mi Browser, Mi Video, Mi Music
   - Cloud: Mi Cloud, Mi Drive (if not used)

2. **Caution** (affects features)
   - Mi Account (affects sync)
   - Mi Unlock (affects bootloader)
   - Gallery (if prefer Google Photos)

3. **Critical** (DO NOT remove)
   - Settings, Phone, Messages, Contacts
   - System UI, Launcher

**Full list**: See `resources/data/xiaomi_bloatware.json`

#### 3.8.2 MIUI Tweaks

```python
XIAOMI_TWEAKS = {
    'performance': {
        'unlock_performance': [
            'pm disable com.miui.powerkeeper',
            'settings put global force_fsg_nav_bar 1',
        ],
        'reduce_animations': [
            'settings put global window_animation_scale 0.5',
            'settings put global transition_animation_scale 0.5',
            'settings put global animator_duration_scale 0.5',
        ],
    },
    'battery': {
        'aggressive_doze': [
            'dumpsys deviceidle enable',
            'dumpsys deviceidle force-idle',
        ],
        'optimize_apps': [
            'cmd package bg-dexopt-job',
        ],
    },
    'privacy': {
        'disable_analytics': [
            'pm disable com.miui.analytics',
            'settings put global msa_enabled 0',
        ],
        'disable_ads': [
            'pm disable com.xiaomi.joyose',
            'settings put secure ad_id ""',
        ],
    },
    'ui': {
        'enable_gestures': [
            'settings put global force_fsg_nav_bar 1',
        ],
        'dark_mode': [
            'cmd uimode night yes',
        ],
    }
}
```

#### 3.8.3 Device-specific Optimization

**Per-model profiles:**
```json
{
  "Mi 11": {
    "safe_bloat": [...],
    "recommended_tweaks": ["performance", "battery"],
    "warnings": ["May affect camera features"]
  },
  "Poco F3": {
    "safe_bloat": [...],
    "recommended_tweaks": ["performance"],
    "warnings": []
  }
}
```

---

### 3.9 Module 9: Automation Scripts

#### 3.9.1 Features

**Script Engine:**
- Define scripts in YAML/JSON
- Variables support
- Conditional execution
- Error handling
- Logging

**Recorder:**
- Record user actions
- Generate script automatically
- Edit recorded script

**Scheduler:**
- Schedule scripts (cron-like)
- Run on device connect/disconnect
- Run on battery level
- Run daily/weekly

#### 3.9.2 Script Format

```yaml
# example_script.yaml
name: "Daily Optimization"
description: "Clear cache and optimize apps"
version: "1.0"

variables:
  cache_threshold: 500  # MB

steps:
  - name: "Check storage"
    action: "shell"
    command: "df /data"
    save_output: "storage_info"
    
  - name: "Clear cache if needed"
    condition: "storage_info.available < 2000"
    action: "batch_shell"
    commands:
      - "pm trim-caches 500M"
      - "cmd package bg-dexopt-job"
      
  - name: "Restart launcher"
    action: "shell"
    command: "am force-stop com.miui.home"
    
  - name: "Notify user"
    action: "notification"
    title: "Optimization Complete"
    message: "Cache cleared and apps optimized"
```

---

### 3.10 Module 10: Cloud Sync

#### 3.10.1 Features

**Sync Data:**
- Device profiles
- Scripts library
- App lists (favorites)
- Settings/preferences
- Backup metadata

**Providers:**
- Google Drive
- Dropbox
- OneDrive
- Self-hosted (WebDAV)

**Security:**
- End-to-end encryption (AES-256)
- Password/Key protection
- Auto-sync toggle

#### 3.10.2 Implementation

```python
class CloudSyncManager:
    def __init__(self, provider: CloudProvider):
        self.provider = provider
        self.crypto = CryptoHandler()
        
    def sync_up(self, data: dict):
        """Upload to cloud"""
        encrypted = self.crypto.encrypt(json.dumps(data))
        self.provider.upload('adb_manager/data.enc', encrypted)
        
    def sync_down(self) -> dict:
        """Download from cloud"""
        encrypted = self.provider.download('adb_manager/data.enc')
        return json.loads(self.crypto.decrypt(encrypted))
```

---

### 3.11 Module 11: Logcat Viewer

#### 3.11.1 Features

**Display:**
- Real-time log streaming
- Syntax highlighting
- Log level filter (V/D/I/W/E/F)
- Tag filter
- PID filter
- Search & highlight

**Export:**
- Save to file
- Copy selected
- Share logs

**Advanced:**
- Regex filter
- Custom color schemes
- Bookmarks
- Auto-scroll toggle

#### 3.11.2 Implementation

```bash
# Logcat command
adb logcat -v time                       # With timestamp
adb logcat *:E                           # Error only
adb logcat -s TAG                        # Specific tag
adb logcat | grep "pattern"              # Filter
```

---

### 3.12 Module 12: OTA ROM Downloader

#### 3.12.1 Features

**ROM Sources:**
- Official Xiaomi CDN
- XiaomiROM.com
- Xiaomi.eu (custom ROMs)

**Functions:**
- Browse available ROMs for model
- Download ROM package
- Verify MD5/SHA256
- Extract firmware
- Flash via Fastboot (guide)

#### 3.12.2 ROM Database

```json
{
  "device_code": "venus",
  "model": "Mi 11",
  "roms": [
    {
      "version": "MIUI 14.0.5.0",
      "android": "13",
      "region": "Global",
      "size": "3.5 GB",
      "url": "https://...",
      "md5": "abc123...",
      "changelog": "Bug fixes..."
    }
  ]
}
```

---

## PHẦN 4: DATABASE SCHEMA

```sql
-- devices table
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial TEXT UNIQUE NOT NULL,
    model TEXT,
    manufacturer TEXT,
    android_version TEXT,
    last_connected DATETIME,
    profile_id INTEGER,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

-- profiles table
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    config JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- scripts table
CREATE TABLE scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    language TEXT DEFAULT 'yaml',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- script_runs table
CREATE TABLE script_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER,
    device_serial TEXT,
    status TEXT,
    output TEXT,
    started_at DATETIME,
    finished_at DATETIME,
    FOREIGN KEY (script_id) REFERENCES scripts(id)
);

-- app_lists table (favorites, blacklists)
CREATE TABLE app_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,  -- 'favorites', 'blacklist', 'custom'
    packages JSON
);

-- backups table
CREATE TABLE backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_serial TEXT,
    backup_type TEXT,  -- 'apk', 'data', 'full'
    package TEXT,
    file_path TEXT,
    size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- logs table
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT,
    module TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## PHẦN 5: UI/UX DESIGN

### 5.1 Color Palette (Dark Theme)

```css
/* Primary Colors */
--bg-primary: #1e1e1e;
--bg-secondary: #252526;
--bg-tertiary: #2d2d30;

/* Accent Colors */
--accent-orange: #ff6b35;  /* Xiaomi Orange */
--accent-blue: #4A9EFF;
--accent-green: #4ECB71;
--accent-red: #F04747;
--accent-yellow: #FAA819;

/* Text Colors */
--text-primary: #CCCCCC;
--text-secondary: #858585;
--text-tertiary: #505050;

/* Border Colors */
--border-color: #3e3e42;
--border-hover: #505050;
```

### 5.2 Typography

```css
--font-family: 'Segoe UI', 'Roboto', sans-serif;
--font-size-small: 12px;
--font-size-normal: 14px;
--font-size-large: 16px;
--font-size-title: 20px;
```

### 5.3 Component Styles

**Buttons:**
```python
PRIMARY_BUTTON = """
    QPushButton {
        background-color: #ff6b35;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #ff7f50;
    }
    QPushButton:pressed {
        background-color: #e55a2b;
    }
    QPushButton:disabled {
        background-color: #3e3e42;
        color: #858585;
    }
"""
```

---

## PHẦN 6: TESTING STRATEGY

### 6.1 Unit Tests
- Test ADB command wrappers
- Test parsers (battery, storage, etc.)
- Test data models

### 6.2 Integration Tests
- Test device connection flow
- Test app operations
- Test file transfers

### 6.3 UI Tests
- Test widget interactions
- Test theme switching
- Test responsive layout

### 6.4 Device Tests
**Test Matrix:**
| Device | Android | MIUI | USB | Wireless |
|--------|---------|------|-----|----------|
| Mi 11 | 13 | 14 | ✓ | ✓ |
| Poco F3 | 12 | 13 | ✓ | ✓ |
| Redmi Note 10 | 11 | 12.5 | ✓ | ✓ |

---

## PHẦN 7: DEPLOYMENT

### 7.1 Build Process

**Windows:**
```bash
# Install dependencies
pip install -r requirements.txt

# Build with PyInstaller
pyinstaller build.spec

# Output: dist/ADBManager.exe (~60MB)
```

**Linux:**
```bash
python3 -m pip install -r requirements.txt
pyinstaller build_linux.spec
# Output: dist/adbmanager
```

### 7.2 Distribution
- GitHub Releases
- Auto-update mechanism (check version on startup)
- Installer option (NSIS for Windows)

### 7.3 System Requirements
- **OS**: Windows 10+, Linux (Ubuntu 20.04+), macOS 11+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 200MB for app, 5GB for ROM downloads
- **Network**: For wireless ADB and cloud sync

---

## PHẦN 8: ROADMAP

**Version 1.0 (MVP)**
- Core ADB functions
- Dashboard, App Manager, File Manager
- Xiaomi Debloat
- Basic UI

**Version 1.5**
- Screen Mirroring
- Script Engine
- Multi-device support
- Improved UI

**Version 2.0**
- Cloud Sync
- Plugin System
- OTA Downloader
- Logcat Viewer
- Advanced automation

**Version 2.5**
- Mobile app (remote control)
- Web dashboard
- Enterprise features (fleet management)
- AI-powered optimization suggestions

---

## PHẦN 9: KẾT LUẬN

Dự án ADB Manager Pro là một công cụ toàn diện, hiện đại cho quản lý thiết bị Android, đặc biệt tối ưu cho dòng Xiaomi. Với kiến trúc mở rộng tốt, UI/UX chuyên nghiệp, và tính năng phong phú, công cụ này sẽ đáp ứng nhu cầu từ người dùng cơ bản đến advanced users.

**Điểm mạnh:**
- Tự động hóa cao
- Tích hợp sâu với Xiaomi/MIUI
- Không cần root
- Đóng gói standalone
- Mở rộng qua plugin

**Thách thức:**
- ADB command stability across Android versions
- Performance với multi-device
- UI responsiveness khi streaming screen
- Cross-platform compatibility

**Khuyến nghị:**
1. Phát triển theo MVP approach
2. Test kỹ trên nhiều devices
3. Thu thập feedback sớm
4. Build community (GitHub, Discord)
5. Document tốt (user guide, API docs)