# ENJAPPインストーラビルドスクリプト
Write-Host "ENJAPPインストーラビルドスクリプト" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# 必要なディレクトリを作成
if (-not (Test-Path "installer")) {
    New-Item -Path "installer" -ItemType Directory | Out-Null
    Write-Host "installerディレクトリを作成しました" -ForegroundColor Yellow
}

# PyInstallerでアプリをビルド
Write-Host "PyInstallerでアプリケーションをビルドしています..." -ForegroundColor Cyan
pyinstaller "enjapp.spec" --clean

# ビルドが成功したか確認
if (-not (Test-Path "dist\ENJAPP\ENJAPP.exe")) {
    Write-Host "エラー: PyInstallerのビルドに失敗しました。" -ForegroundColor Red
    Read-Host "続行するには何かキーを押してください..."
    exit 1
}

Write-Host "PyInstallerのビルドが完了しました。" -ForegroundColor Green

# Inno Setupでインストーラをビルド
Write-Host "Inno Setupでインストーラをビルドしています..." -ForegroundColor Cyan

# Inno Setupのパスを確認
$innoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoCompiler)) {
    $innoCompiler = "C:\Program Files\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $innoCompiler)) {
        Write-Host "エラー: Inno Setupが見つかりません。" -ForegroundColor Red
        Write-Host "Inno Setup 6をインストールしてください: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
        Read-Host "続行するには何かキーを押してください..."
        exit 1
    }
}

# インストーラをビルド
& $innoCompiler "installer.iss"

Write-Host "インストーラのビルドが完了しました。" -ForegroundColor Green
Write-Host "インストーラは installer フォルダに作成されています。" -ForegroundColor Green
Read-Host "続行するには何かキーを押してください..."
