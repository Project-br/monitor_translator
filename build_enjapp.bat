@echo off
echo ENJAPP Installer Build Script
echo ==============================

REM Create installer directory if it doesn't exist
if not exist "installer" mkdir installer

REM Build application with PyInstaller
echo Building application with PyInstaller...
pyinstaller enjapp.spec --clean

REM Check if build was successful
if not exist "dist\ENJAPP\ENJAPP.exe" (
    echo Error: PyInstaller build failed.
    pause
    exit /b 1
)

echo PyInstaller build completed.

REM Build installer with Inno Setup
echo Building installer with Inno Setup...

REM Check Inno Setup path
set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_COMPILER%" (
    set "INNO_COMPILER=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist "%INNO_COMPILER%" (
    echo Error: Inno Setup not found.
    echo Please install Inno Setup 6: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM Build installer
"%INNO_COMPILER%" installer.iss

echo Installer build completed.
echo Installer is located in the installer folder.
pause
