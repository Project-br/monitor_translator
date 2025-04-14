@echo off
REM Tesseract-OCRのインストール確認スクリプト

set TESSERACT_PATH="C:\Program Files\Tesseract-OCR\tesseract.exe"

if exist %TESSERACT_PATH% (
    echo Tesseract-OCRは正しくインストールされています。
) else (
    echo Tesseract-OCRがインストールされていないか、パスが異なります。
    echo 翻訳ツールを使用するには、Tesseract-OCRをインストールしてください。
    echo https://github.com/UB-Mannheim/tesseract/wiki からダウンロードできます。
    pause
)
