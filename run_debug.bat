@echo off
cd dist\ENJAPP
echo ENJAPPデバッグ実行
echo ==================
echo.
ENJAPP.exe
echo.
echo 終了コード: %ERRORLEVEL%
pause
