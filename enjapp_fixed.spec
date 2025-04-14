# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['e:\\develop\\monitor_translator\\app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'), 
        # translation_logs.jsonは含めない（初回実行時に自動生成される）
        # ('translation_logs.json', '.'),
        # Tesseract関連ファイルを含める
        ('C:\\Program Files\\Tesseract-OCR\\tessdata', 'tessdata'),
        # 必要なアイコンやリソースファイル
        ('translator_main/translator/resources', 'translator_main/translator/resources'),
        # 翻訳サーバー関連のファイル（モデルは除く）
        ('translator_main/translator/server_client/translate_client.py', 'translator_main/translator/server_client'),
        ('translator_main/translator/server_client/translate_server_run.py', 'translator_main/translator/server_client'),
        # モデルディレクトリ構造だけを含める（中身は含めない）
        ('translator_main/translator/server_client/model', 'translator_main/translator/server_client/model'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'translator_main.translator.server_client.translate_server_run',
        'translator_main.translator.server_client.translate_client',
        'argparse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ENJAPP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # コンソールウィンドウを非表示に変更
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='translator_main/translator/resources/icon.ico' if os.path.exists('translator_main/translator/resources/icon.ico') else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ENJAPP',
)
