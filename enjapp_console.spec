# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['e:\\develop\\monitor_translator\\app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'), 
        ('translation_logs.json', '.'),
        # Tesseract関連ファイルを含める
        ('C:\\Program Files\\Tesseract-OCR\\tessdata', 'tessdata'),
        # 必要なアイコンやリソースファイル
        ('translator_main/translator/resources', 'translator_main/translator/resources'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
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
    name='ENJAPP_Console',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # コンソールウィンドウを表示する
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
    name='ENJAPP_Console',
)
