; ENJAPPインストーラスクリプト
; Inno Setup用

#define MyAppName "ENJAPP"
#define MyAppVersion "1.0.1"
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
SetupIconFile=translator_main\translator\resources\icon.ico

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
; 変更履歴ファイル
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
; ログファイルは含めない（初回実行時に自動生成される）

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
// 既存のインストールを検出して自動的にアンインストールする
function InitializeSetup(): Boolean;
var
  UninstallString: String;
  ResultCode: Integer;
  UninstallSuccessful: Boolean;
begin
  // デフォルトでは続行
  Result := True;
  
  // レジストリから既存のアンインストーラ情報を取得
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1',
     'UninstallString', UninstallString) then
  begin
    // 既存のインストールが見つかった場合、ユーザーに確認
    if MsgBox('{#MyAppName}の以前のバージョンが見つかりました。' + #13#10 +
              'インストールを続行する前に、既存のバージョンをアンインストールする必要があります。' + #13#10 + #13#10 +
              '既存のバージョンをアンインストールしますか？',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // アンインストーラに /SILENT パラメータを追加して、サイレントモードで実行
      UninstallString := RemoveQuotes(UninstallString);
      UninstallSuccessful := Exec(UninstallString, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      
      // アンインストールが成功したかどうかを確認
      if not UninstallSuccessful then
      begin
        MsgBox('既存のバージョンのアンインストールに失敗しました。' + #13#10 +
               'インストールを続行できません。', mbError, MB_OK);
        Result := False;
      end
      else
      begin
        // アンインストール後、少し待機してファイルの削除が完了するのを待つ
        Sleep(1000);
      end;
    end
    else
    begin
      // ユーザーがアンインストールをキャンセルした場合
      Result := False;
    end;
  end;
end;

// Tesseract-OCRのインストール確認
function CheckTesseractInstalled(): Boolean;
var
  TesseractPath, TesseractPath32: String;
begin
  // 64ビット版のパスをチェック
  TesseractPath := ExpandConstant('{pf64}\Tesseract-OCR\tesseract.exe');
  // 32ビット版のパスをチェック
  TesseractPath32 := ExpandConstant('{pf32}\Tesseract-OCR\tesseract.exe');
  
  // いずれかのパスにファイルが存在すればOK
  Result := FileExists(TesseractPath) or FileExists(TesseractPath32);
  
  // Program Files以外の一般的なインストール先もチェック
  if not Result then
  begin
    TesseractPath := ExpandConstant('{commonpf}\Tesseract-OCR\tesseract.exe');
    Result := FileExists(TesseractPath);
  end;
end;

// インストール後の処理
procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Tesseract-OCRがインストールされているか確認
    if not CheckTesseractInstalled() then
    begin
      if MsgBox('Tesseract-OCRがインストールされていません。' + #13#10 +
             'ENJAPPを使用するには、Tesseract-OCRをインストールしてください。' + #13#10 +
             '以下の手順でインストールできます:' + #13#10 +
             '1. https://github.com/UB-Mannheim/tesseract/wiki にアクセス' + #13#10 +
             '2. "tesseract-ocr-w64-setup-v5.x.x.exe" (64ビット版)をダウンロード' + #13#10 +
             '3. ダウンロードしたファイルを実行してインストール' + #13#10 + #13#10 +
             '今すぐTesseract-OCRのダウンロードページを開きますか？', 
             mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://github.com/UB-Mannheim/tesseract/wiki', '', '', SW_SHOW, ewNoWait, ErrorCode);
      end;
    end;
  end;
end;
