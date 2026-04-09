[Setup]
AppName=V-Pack Monitor
AppVersion=1.5.0
AppPublisher=VDT - Vu Duc Thang
AppPublisherURL=https://github.com/thangvd2
AppSupportURL=https://github.com/thangvd2/V-Pack-Monitor
DefaultDirName={sd}\V-Pack Monitor
DefaultGroupName=V-Pack Monitor
OutputDir=.\installer
OutputBaseFilename=V-Pack_Setup_v1.5.0
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
SetupIconFile=compiler:SetupClassicIcon.ico

[Files]
Source: "dist\V-Pack-Monitor.exe"; DestDir: "{app}"; Flags: ignoreversion
; Tạo thư mục trống cho recordings
Source: "README.md"; DestDir: "{app}\recordings"; Flags: skipifsourcedoesntexist

[Icons]
Name: "{group}\V-Pack Monitor"; Filename: "{app}\V-Pack-Monitor.exe"
Name: "{commondesktop}\V-Pack Monitor"; Filename: "{app}\V-Pack-Monitor.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài Màn hình chính"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "http://localhost:8001"; Flags: shellexec runasoriginaluser postinstall nowait; Description: "Mở V-Pack Monitor (Cổng 8001)"
Filename: "{app}\V-Pack-Monitor.exe"; Description: "Khởi động Server V-Pack"; Flags: nowait postinstall skipifsilent
