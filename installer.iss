; ENJAPPインストーラスクリプト
; Inno Setup用

#define MyAppName "ENJAPP"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company Name"
#define MyAppURL "https://yourcompany.com/"
#define MyAppExeName "ENJAPP.exe"

[Setup]
; アプリケーション情報
AppId={{E1234567-89AB-CDEF-0123-456789ABCDEF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; インストール先ディレクトリ
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 管理者権限が必要
PrivilegesRequired=admin

; 出力設定
OutputDir=installer
OutputBaseFilename={#MyAppName}_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
; アイコン設定
SetupIconFile=dist\ENJAPP\translator_main\translator\resources\icon.ico

; インターフェース設定
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; PyInstallerでビルドされたファイルをすべて含める
Source: "dist\ENJAPP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 設定ファイル
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "translation_logs.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

; Tesseract-OCRのインストールチェック用スクリプト
Source: "check_tesseract.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; インストール後に実行するかどうか
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Tesseract-OCRの確認
Filename: "{app}\check_tesseract.bat"; Description: "Tesseract-OCRの確認"; Flags: runhidden

[Code]
// インストール前の確認
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

// Tesseract-OCRのインストール確認
function CheckTesseractInstalled(): Boolean;
var
  TesseractPath: String;
begin
  TesseractPath := ExpandConstant('{pf}\Tesseract-OCR\tesseract.exe');
  Result := FileExists(TesseractPath);
end;

// インストール後の処理
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Tesseract-OCRがインストールされているか確認
    if not CheckTesseractInstalled() then
    begin
      MsgBox('Tesseract-OCRがインストールされていません。' + #13#10 +
             'ENJAPPを使用するには、Tesseract-OCRをインストールしてください。' + #13#10 +
             'https://github.com/UB-Mannheim/tesseract/wiki からダウンロードできます。', mbInformation, MB_OK);
    end;
  end;
end;
