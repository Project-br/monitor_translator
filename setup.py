from setuptools import setup, find_packages

setup(
    name="enjapp",
    version="1.0.1",
    description="A tool for translating text on screen in real-time / 画面上の文章を簡易翻訳ツール",
    author="Borshchnabe, pikkuri",
    author_email="",  # プライバシー保護のため空にしておく
    url="https://github.com/Borshchnabe/enjapp",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        # 画像処理関連
        "opencv-python>=4.5.0",  # 画像処理
        "pytesseract>=0.3.8",    # OCR処理
        "pillow>=8.0.0",         # 画像操作
        "numpy>=1.19.0",         # 数値計算

        # GUI関連
        # tkinter is part of the Python standard library and doesn't need to be installed
        "pynput>=1.7.0",         # キーボード・マウス入力の監視
        "PyQt5>=5.15.0",         # GUI フレームワーク

        # サーバー関連
        "fastapi>=0.68.0",       # APIサーバー
        "uvicorn>=0.15.0",       # ASGIサーバー
        "requests>=2.25.0",      # HTTP通信

        # 翻訳モデル関連
        "torch>=1.9.0",          # 機械学習フレームワーク
        "transformers>=4.11.0",  # 自然言語処理モデル
        "sentencepiece>=0.1.96", # M2M100モデルに必要
        
        # 環境設定
        "python-dotenv>=0.19.0", # 環境変数管理
        
        # ロギング
        "colorlog>=6.0.0",       # カラーロギング
    ],
    extras_require={
        "gpu": ["torch>=1.7.0"],                   # GPU使用時のみ必要
    },
    # パッケージデータの追加
    include_package_data=True,
    # エントリーポイントの設定
    entry_points={
        'console_scripts': [
            'enjapp=app:main',
            'monitor-translator=app:main',  # 後方互換性のために古い名前も維持
        ],
    },
    # パッケージメタデータ
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)