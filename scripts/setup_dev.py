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
