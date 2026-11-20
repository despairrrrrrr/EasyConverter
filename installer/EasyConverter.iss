#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif

[Setup]
AppId={{B3D8190B-91BE-4DD5-9A18-971A5BDAA80E}
AppName=EasyConverter
AppVersion={#AppVersion}
AppVerName=EasyConverter {#AppVersion}
AppPublisher=EasyConverter
AppPublisherURL=https://github.com/despairrrrrrr/EasyConverter
AppSupportURL=https://github.com/despairrrrrrr/EasyConverter/issues
AppUpdatesURL=https://github.com/despairrrrrrr/EasyConverter/releases
DefaultDirName={localappdata}\Programs\EasyConverter
DefaultGroupName=EasyConverter
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\releases
OutputBaseFilename=EasyConverterSetup-{#AppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\EasyConverter.exe
LicenseFile=..\LICENSE
Compression=lzma2/normal
SolidCompression=yes
DiskSpanning=no
WizardStyle=modern
WizardResizable=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
VersionInfoVersion={#AppVersion}.0
VersionInfoDescription=EasyConverter Setup
VersionInfoProductName=EasyConverter
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\EasyConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\EasyConverter"; Filename: "{app}\EasyConverter.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\EasyConverter"; Filename: "{app}\EasyConverter.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\EasyConverter.exe"; Description: "{cm:LaunchProgram,EasyConverter}"; Flags: nowait postinstall skipifsilent
