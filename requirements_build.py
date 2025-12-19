# ============================================
# requirements.txt
# ============================================
PySide6>=6.6.0
PySide6-Addons>=6.6.0
pyqtgraph>=0.13.3
psutil>=5.9.6
loguru>=0.7.2
pydantic>=2.5.0
pydantic-settings>=2.1.0
httpx>=0.26.0
aiofiles>=23.2.1
python-dotenv>=1.0.0


# ============================================
# requirements-dev.txt  
# ============================================
pytest>=7.4.3
pytest-qt>=4.2.0
pytest-cov>=4.1.0
black>=23.12.0
flake8>=6.1.0
mypy>=1.7.0
pyinstaller>=6.3.0
nuitka>=1.9.0


# ============================================
# build.spec (PyInstaller Configuration)
# ============================================
# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Get paths
src_dir = Path('src')
resources_dir = src_dir / 'resources'

# Analysis
a = Analysis(
    ['src/main.py'],
    pathex=[str(src_dir)],
    binaries=[
        # ADB binaries (Windows)
        (str(resources_dir / 'adb' / 'windows' / 'adb.exe'), 'adb'),
        (str(resources_dir / 'adb' / 'windows' / 'AdbWinApi.dll'), 'adb'),
        (str(resources_dir / 'adb' / 'windows' / 'AdbWinUsbApi.dll'), 'adb'),
        
        # Scrcpy binaries (Windows)
        (str(resources_dir / 'scrcpy' / 'windows' / 'scrcpy.exe'), 'scrcpy'),
        (str(resources_dir / 'scrcpy' / 'windows' / 'scrcpy-server'), 'scrcpy'),
    ],
    datas=[
        # Icons and resources
        (str(resources_dir / 'icons'), 'icons'),
        (str(resources_dir / 'fonts'), 'fonts'),
        (str(resources_dir / 'data'), 'data'),
        (str(resources_dir / 'translations'), 'translations'),
        
        # Stylesheets
        (str(src_dir / 'ui' / 'styles'), 'ui/styles'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pyqtgraph',
        'psutil',
        'loguru',
        'pydantic',
        'httpx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'numpy.distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ADBManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(resources_dir / 'icons' / 'app_icon.ico'),
    version='version_info.txt',  # See version_info.txt below
)

# COLLECT
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ADBManager'
)


# ============================================
# version_info.txt (Windows version info)
# ============================================
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 0, 0, 0),
    prodvers=(2, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'ADB Manager Pro - Android Device Manager'),
        StringStruct(u'FileVersion', u'2.0.0.0'),
        StringStruct(u'InternalName', u'ADBManager'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024'),
        StringStruct(u'OriginalFilename', u'ADBManager.exe'),
        StringStruct(u'ProductName', u'ADB Manager Pro'),
        StringStruct(u'ProductVersion', u'2.0.0.0')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)


# ============================================
# config.yaml (Default configuration)
# ============================================
app:
  name: "ADB Manager Pro"
  version: "2.0.0"
  theme: "dark"  # dark, light, xiaomi
  language: "en"  # en, vi

adb:
  path: null  # Auto-detect if null
  timeout: 30
  retry: 3

ui:
  window:
    width: 1400
    height: 900
    remember_position: true
  
  dashboard:
    refresh_interval: 2  # seconds
    chart_points: 60
  
  app_manager:
    show_system: false
    sort_by: "name"  # name, size, package
  
device:
  auto_connect: true
  remember_devices: true
  wireless_port: 5555

features:
  screen_mirror:
    bitrate: 8000000
    max_size: 1920
    framerate: 60
  
  backup:
    directory: "./backups"
    auto_organize: true
  
  scripts:
    directory: "./scripts"
    auto_load: true
  
cloud:
  enabled: false
  provider: null  # gdrive, dropbox, onedrive
  sync_interval: 3600  # seconds

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "./logs/adb_manager.log"
  max_size: 10485760  # 10 MB
  backup_count: 5


# ============================================
# .env.example (Environment variables template)
# ============================================
# ADB Configuration
ADB_PATH=
ADB_TIMEOUT=30

# Cloud Sync (optional)
GDRIVE_CLIENT_ID=
GDRIVE_CLIENT_SECRET=
DROPBOX_API_KEY=

# Update Check
UPDATE_CHECK_URL=https://api.github.com/repos/yourname/adb-manager/releases/latest

# Logging
LOG_LEVEL=INFO


# ============================================
# setup.py (For development installation)
# ============================================
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="adb-manager-pro",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Comprehensive Android device manager via ADB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourname/adb-manager",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "PySide6>=6.6.0",
        "pyqtgraph>=0.13.3",
        "psutil>=5.9.6",
        "loguru>=0.7.2",
        "pydantic>=2.5.0",
        "httpx>=0.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-qt>=4.2.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "adb-manager=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.qss", "*.json", "*.ico", "*.png"],
    },
)


# ============================================
# scripts/build_windows.bat (Build script)
# ============================================
@echo off
echo ========================================
echo Building ADB Manager Pro for Windows
echo ========================================

:: Clean previous builds
echo Cleaning previous builds...
rmdir /s /q build dist 2>nul

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: Download ADB platform tools if not exists
if not exist "src\resources\adb\windows\adb.exe" (
    echo Downloading ADB platform tools...
    mkdir src\resources\adb\windows
    :: Add download logic here
    echo Please manually download platform-tools and extract to src/resources/adb/windows/
    pause
)

:: Build with PyInstaller
echo Building executable...
pyinstaller build.spec

:: Check if build succeeded
if exist "dist\ADBManager\ADBManager.exe" (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo Output: dist\ADBManager\ADBManager.exe
    echo ========================================
    
    :: Create installer (optional - requires NSIS)
    echo.
    echo Create installer? (Y/N)
    choice /C YN /M "Create installer"
    if errorlevel 2 goto :end
    
    :: Run NSIS to create installer
    if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
        "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
    ) else (
        echo NSIS not found. Skipping installer creation.
    )
) else (
    echo.
    echo ========================================
    echo Build failed! Check errors above.
    echo ========================================
)

:end
pause


# ============================================
# scripts/setup_dev.py (Development setup)
# ============================================
#!/usr/bin/env python3
"""
Development environment setup script
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run command with description"""
    print(f"\n{'='*50}")
    print(f"{description}")
    print(f"{'='*50}")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error: {description} failed")
        sys.exit(1)

def main():
    """Setup development environment"""
    print("Setting up ADB Manager Pro development environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11+ required")
        sys.exit(1)
    
    # Create virtual environment
    if not Path("venv").exists():
        run_command(
            f"{sys.executable} -m venv venv",
            "Creating virtual environment"
        )
    
    # Activate venv (platform-specific)
    if sys.platform == "win32":
        activate = "venv\\Scripts\\activate.bat"
        pip = "venv\\Scripts\\pip.exe"
    else:
        activate = "source venv/bin/activate"
        pip = "venv/bin/pip"
    
    # Upgrade pip
    run_command(
        f"{pip} install --upgrade pip",
        "Upgrading pip"
    )
    
    # Install requirements
    run_command(
        f"{pip} install -r requirements.txt",
        "Installing dependencies"
    )
    
    # Install dev requirements
    run_command(
        f"{pip} install -r requirements-dev.txt",
        "Installing development dependencies"
    )
    
    # Create necessary directories
    dirs = [
        "src/resources/adb/windows",
        "src/resources/adb/linux",
        "src/resources/adb/macos",
        "src/resources/scrcpy/windows",
        "src/resources/icons",
        "src/resources/fonts",
        "src/resources/data",
        "backups",
        "scripts",
        "logs",
    ]
    
    print("\nCreating directory structure...")
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}")
    
    # Copy example files
    if not Path(".env").exists() and Path(".env.example").exists():
        import shutil
        shutil.copy(".env.example", ".env")
        print("\n  ✓ Created .env from .env.example")
    
    print("\n" + "="*50)
    print("Setup complete!")
    print("="*50)
    print("\nNext steps:")
    print("  1. Activate virtual environment:")
    print(f"     {activate}")
    print("  2. Download ADB platform tools:")
    print("     https://developer.android.com/studio/releases/platform-tools")
    print("  3. Extract to src/resources/adb/windows/")
    print("  4. Run application:")
    print("     python src/main.py")
    print("\nHappy coding! 🚀")

if __name__ == "__main__":
    main()


# ============================================
# README.md (Project documentation)
# ============================================
# ADB Manager Pro

A comprehensive, modern desktop application for managing Android devices via ADB (Android Debug Bridge). Optimized for Xiaomi devices with specialized debloat and MIUI optimization features.

## 🚀 Features

### Core Features
- ✅ **Device Connection**: USB and Wireless (TCP/IP) support
- 📊 **Real-time Dashboard**: CPU, RAM, Battery, Storage, Network monitoring
- 📱 **App Manager**: Install, uninstall, enable/disable, backup apps
- 📦 **APK Manager**: Batch install, backup, parse APK info
- 📁 **File Manager**: Browse, push/pull files with drag & drop
- 🖥️ **Screen Mirroring**: Real-time display and control via Scrcpy
- 🌐 **DNS Configuration**: Private DNS and custom DNS servers

### Xiaomi Specific
- 🤖 **Debloat Tool**: Remove 100+ MIUI bloatware safely
- ⚡ **MIUI Tweaks**: Performance, battery, privacy optimizations
- 🔧 **Device Profiles**: Pre-configured settings for popular models

### Advanced Features
- 📝 **Script Engine**: Record, edit, and run automation scripts
- 🔄 **Multi-Device**: Manage multiple devices simultaneously
- ☁️ **Cloud Sync**: Backup settings to Google Drive/Dropbox
- 📋 **Logcat Viewer**: Real-time log monitoring with filters
- 💾 **OTA Downloader**: Download and flash MIUI ROMs
- 🔌 **Plugin System**: Extend functionality with plugins

## 📋 Requirements

- Python 3.11+
- Windows 10/11, Linux, or macOS
- ADB Platform Tools (included in releases)
- 4GB RAM minimum, 8GB recommended

## 🔧 Installation

### From Release (Recommended)
1. Download latest release from [Releases](https://github.com/yourname/adb-manager/releases)
2. Extract ZIP file
3. Run `ADBManager.exe`

### From Source
```bash
# Clone repository
git clone https://github.com/yourname/adb-manager.git
cd adb-manager

# Run setup script
python scripts/setup_dev.py

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Run application
python src/main.py
```

## 🎯 Quick Start

1. **Enable USB Debugging** on your Android device:
   - Settings → About Phone → Tap "Build Number" 7 times
   - Settings → Developer Options → Enable "USB Debugging"

2. **Connect Device**:
   - USB: Plug in device and accept authorization prompt
   - Wireless: Enable wireless debugging and enter IP address

3. **Start Managing**:
   - View device info in Dashboard
   - Manage apps in App Manager
   - Optimize Xiaomi devices in Xiaomi Optimizer

## 📖 Documentation

- [User Guide](docs/USER_GUIDE.md)
- [API Documentation](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](docs/CONTRIBUTING.md)

## 🛠️ Development

### Build from Source
```bash
# Install build tools
pip install pyinstaller

# Build executable
pyinstaller build.spec

# Output: dist/ADBManager/
```

### Run Tests
```bash
pytest tests/
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## ⚠️ Disclaimer

- **Backup your data** before using debloat features
- Removing system apps may cause instability
- Use at your own risk
- Not affiliated with Xiaomi or Google

## 🙏 Credits

- **ADB**: Android Debug Bridge by Google
- **Scrcpy**: Screen mirroring by Genymobile
- **PySide6**: Qt for Python
- **Community**: Thanks to all contributors!

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yourname/adb-manager/issues)
- Discord: [Join Server](https://discord.gg/yourserver)
- Email: your.email@example.com

## 🌟 Star History

If you find this tool useful, please consider giving it a star! ⭐

---

Made with ❤️ by [Your Name]
