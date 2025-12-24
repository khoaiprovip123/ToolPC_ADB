import os
import sys
import shutil
import subprocess
from pathlib import Path

def run_build():
    print("🚀 Starting Build Process for Xiaomi ADB Commander...")
    
    # 1. Clean previous build
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
        
    # 2. Define Assets
    sep = ";" if os.name == 'nt' else ":"
    
    assets = [
        f"src/data/soc_database.json{sep}src/data",
        f"resources/adb{sep}resources/adb",
        f"scripts{sep}resources/scrcpy",
        f"resources/icons{sep}resources/icons",
        f"resources/logo.png{sep}resources",
    ]
    
    # 3. Check for Icon
    icon_arg = []
    if os.path.exists("scripts/icon.ico"):
         icon_arg = ["--icon", "scripts/icon.ico"]
    elif os.path.exists("resources/icon.ico"):
         icon_arg = ["--icon", "resources/icon.ico"]
    
    # 4. PyInstaller Arguments - CHANGED TO ONEDIR
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",  # FOLDER-BASED DISTRIBUTION (not --onefile)
        "--windowed",
        "--name", "XiaomiADBCommander",
        "--hidden-import", "PySide6",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
    ]
    
    # Add data
    for asset in assets:
        cmd.extend(["--add-data", asset])
        
    # Add icon
    cmd.extend(icon_arg)
    
    # Add script
    cmd.append("src/main.py")
    
    print(f"📦 Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ Build Success! Output is in 'dist/XiaomiADBCommander' folder.")
        print(f"Path: {os.path.abspath('dist/XiaomiADBCommander')}")
        return True
    else:
        print("\n❌ Build Failed!")
        return False

if __name__ == "__main__":
    # Check PyInstaller
    try:
        subprocess.run(["pyinstaller", "--version"], capture_output=True, check=True)
    except:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    run_build()
