@echo off
chcp 65001 > nul
echo ENJAPPインストーラビルドスクリプト
echo ======================================   

REM 必要なディレクトリを作成
if not exist "installer" mkdir installer

REM PyInstallerでアプリをビルド
echo PyInstallerでアプリケーションをビルドしています...
pyinstaller "モニター翻訳ツール.spec" --clean

REM ビルドが成功したか確認
if not exist "dist\ENJAPP\ENJAPP.exe" (
    echo エラー: PyInstallerのビルドに失敗しました。
    pause
    exit /b 1
)

echo PyInstallerのビルドが完了しました。

REM Inno Setupでインストーラをビルド
echo Inno Setupでインストーラをビルドしています...
echo Inno Setupがインストールされていることを確認してください。

REM Inno Setupのパスを確認
set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_COMPILER%" (
    set "INNO_COMPILER=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist "%INNO_COMPILER%" (
    echo エラー: Inno Setupが見つかりません。
    echo Inno Setup 6をインストールしてください: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM インストーラをビルド
"%INNO_COMPILER%" installer.iss

echo インストーラのビルドが完了しました。
echo インストーラは installer フォルダに作成されています。
pause
