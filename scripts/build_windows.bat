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
