# Xiaomi ADB Commander

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
- 🔄 **Auto-Update**: Automatic update checking and installation from GitHub releases

## 📋 Requirements

- Python 3.11+
- Windows 10/11, Linux, or macOS
- ADB Platform Tools (included in releases)
- 4GB RAM minimum, 8GB recommended

## 🔧 Installation

### From Release (Recommended)
1. Download latest release from [Releases](https://github.com/khoaiprovip123/ToolPC_ADB/releases)
2. Extract ZIP file
3. Run `ADBManager.exe`

### From Source
```bash
# Clone repository
git clone https://github.com/khoaiprovip123/ToolPC_ADB.git
cd ToolPC_ADB

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
- [Awesome ADB Guide](docs/reference/AWESOME_ADB_GUIDE.md) :books:
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

- Issues: [GitHub Issues](https://github.com/khoaiprovip123/ToolPC_ADB/issues)

## 🌟 Star History

If you find this tool useful, please consider giving it a star! ⭐

---

Made with ❤️ by [Van Khoai]
