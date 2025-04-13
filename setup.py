from setuptools import setup, find_packages

setup(
    name="monitor_translator",
    version="0.1.0",
    description="A tool for translating text on screen in real-time",
    author="s-take",
    author_email="shumpeitake@gmail.com",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        # 画像処理関連
        "opencv-python",  # 画像処理
        "pytesseract",    # OCR処理
        "pillow",         # 画像操作
        "numpy",          # 数値計算

        # GUI関連
        # tkinter is part of the Python standard library and doesn't need to be installed
        "pynput",         # キーボード・マウス入力の監視

        # サーバー関連
        "fastapi",        # APIサーバー
        "uvicorn",        # ASGIサーバー
        "requests",       # HTTP通信

        # 翻訳モデル関連
        "torch",          # 機械学習フレームワーク
        "transformers",   # 自然言語処理モデル
        "sentencepiece",  # M2M100モデルに必要
        
        # 環境設定
        "python-dotenv",  # 環境変数管理
    ],
    extras_require={
        "gpu": ["torch>=1.7.0"],                   # GPU使用時のみ必要
    },
    entry_points={
        "console_scripts": [
            "monitor-translator=translator_main.app:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)