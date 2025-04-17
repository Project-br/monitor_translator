# ENJAPPインストーラビルドスクリプト（シンプル版）
Write-Host "ENJAPPインストーラビルドスクリプト" -ForegroundColor Green

# 必要なディレクトリを作成
if (-not (Test-Path "installer")) {
    New-Item -Path "installer" -ItemType Directory | Out-Null
}

# PyInstallerでアプリをビルド
Write-Host "PyInstallerでアプリケーションをビルドしています..." -ForegroundColor Cyan
pyinstaller "モニター翻訳ツール.spec" --clean

# Inno Setupでインストーラをビルド
Write-Host "Inno Setupでインストーラをビルドしています..." -ForegroundColor Cyan

# Inno Setupのパスを確認
$innoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoCompiler)) {
    $innoCompiler = "C:\Program Files\Inno Setup 6\ISCC.exe"
}

# インストーラをビルド
& $innoCompiler "installer.iss"

Write-Host "インストーラのビルドが完了しました。" -ForegroundColor Green
Write-Host "インストーラは installer フォルダに作成されています。" -ForegroundColor Green
Read-Host "続行するには何かキーを押してください..."
