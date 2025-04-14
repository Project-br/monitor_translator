# ENJAPPインストーラビルドスクリプト（PowerShell版）
Write-Host "ENJAPPインストーラビルドスクリプト" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# 必要なディレクトリを作成
if (-not (Test-Path "installer")) {
    New-Item -Path "installer" -ItemType Directory | Out-Null
    Write-Host "installerディレクトリを作成しました" -ForegroundColor Yellow
}

# モデルファイルを一時的に移動（ビルド時に含めないため）
Write-Host "ビルド準備: モデルファイルを一時的に移動しています..." -ForegroundColor Cyan
& python prepare_for_build.py

# PyInstallerでアプリをビルド
Write-Host "PyInstallerでアプリケーションをビルドしています..." -ForegroundColor Cyan
& pyinstaller "enjapp_fixed.spec" --clean

# ビルドが成功したか確認
if (-not (Test-Path "dist\ENJAPP\ENJAPP.exe")) {
    Write-Host "エラー: PyInstallerのビルドに失敗しました。" -ForegroundColor Red
    
    # モデルファイルを元に戻す
    Write-Host "モデルファイルを元に戻しています..." -ForegroundColor Cyan
    & python prepare_for_build.py --restore
    
    Read-Host "続行するには何かキーを押してください..."
    exit 1
}

Write-Host "PyInstallerのビルドが完了しました。" -ForegroundColor Green

# Inno Setupでインストーラをビルド
Write-Host "Inno Setupでインストーラをビルドしています..." -ForegroundColor Cyan
Write-Host "Inno Setupがインストールされていることを確認してください。" -ForegroundColor Yellow

# Inno Setupのパスを確認
$innoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoCompiler)) {
    $innoCompiler = "C:\Program Files\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $innoCompiler)) {
    Write-Host "エラー: Inno Setupが見つかりません。" -ForegroundColor Red
    Write-Host "Inno Setup 6をインストールしてください: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    
    # モデルファイルを元に戻す
    Write-Host "モデルファイルを元に戻しています..." -ForegroundColor Cyan
    & python prepare_for_build.py --restore
    
    Read-Host "続行するには何かキーを押してください..."
    exit 1
}

# インストーラをビルド
& $innoCompiler "installer.iss"

# モデルファイルを元に戻す
Write-Host "モデルファイルを元に戻しています..." -ForegroundColor Cyan
& python prepare_for_build.py --restore

Write-Host "インストーラのビルドが完了しました。" -ForegroundColor Green
Write-Host "インストーラは installer フォルダに作成されています。" -ForegroundColor Green
Read-Host "続行するには何かキーを押してください..."
