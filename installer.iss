; Inno Setup Script for Xiaomi ADB Commander v2.5.0
; This script creates a Windows installer with installation path selection

#define MyAppName "Xiaomi ADB Commander"
#define MyAppVersion "2.5.4.1"
#define MyAppPublisher "VanKhoai Dev"
#define MyAppExeName "XiaomiADBCommander.exe"

[Setup]
; App Information
AppId={{A8F5E9D2-3C4B-4E7F-9A1D-6B8C2D5E7F9A}
AppMutex=XiaomiADBCommanderMutex
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
; SetupIconFile=resources\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
CloseApplicationsFilter=adb.exe,XiaomiADBCommander.exe


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
