; Inno Setup Script for Xiaomi ADB Commander v2.4.0
; This script creates a Windows installer with installation path selection

#define MyAppName "Xiaomi ADB Commander"
#define MyAppVersion "2.4.0"
#define MyAppPublisher "VanKhanh Dev"
#define MyAppExeName "XiaomiADBCommander.exe"

[Setup]
; App Information
AppId={{A8F5E9D2-3C4B-4E7F-9A1D-6B8C2D5E7F9A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
; Output Configuration
OutputDir=installer_output
OutputBaseFilename=XiaomiADBCommander_Setup_v{#MyAppVersion}
; SetupIconFile=scripts\icon.ico  ; Commented out - no icon file available
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main Application Files
Source: "dist\XiaomiADBCommander\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Gỡ cài đặt {#MyAppName}"; Filename: "{uninstallexe}"
; Desktop Shortcut (if selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Option to launch app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "Khởi chạy {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
