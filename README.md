# ENJAPP - 画面上の文章を簡易翻訳ツール

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Shift + Alt + Z キーを押しながら、マウスを移動させるだけで四角い範囲を指定して英語の文章を読み取り、ローカル翻訳サーバーによる日本語訳を出力します。<br>
起動時に出現する小さいウィンドウ上で翻訳前の文章と翻訳後の文章が提示されるようになっています。

## 主な機能

- **画面キャプチャでテキスト検出**: OpenCVを使用して画面上のテキスト領域を指定して検出します
- **OCRによるテキスト抽出**: Tesseract OCRを使用して検出された領域からテキストを抽出します
- **サーバー・クライアント翻訳**: 専用の翻訳サーバーを使用してテキストを翻訳します
- **統合ランチャー**: 翻訳サーバーとモニターアプリケーションを一括で起動・管理します

## 必要条件

- Python 3.6以上
- Windows 10/11（他のOSでも動作する可能性がありますが、未テスト）
- Tesseract OCRエンジン

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/monitor_translator.git
cd monitor_translator
```

### 2. 仮想環境の作成と有効化

```bash
python -m venv venv
```

Windowsの場合:
```bash
.\venv\Scripts\activate
```

Linux/macOSの場合:
```bash
source venv/bin/activate
```

### 3. プロジェクトのインストール。GPUで翻訳サーバーを動かして高速化したい場合はCUDAとtorchを反映させます。（正直なくてもいい）

1. 基本インストール

```bash
pip install -e .
```

2. GPUサポート付きでインストール

```bash
pip install -e .[gpu]
```

### 4. Tesseract OCRのインストール

1. [Tesseract-OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki) からインストーラーをダウンロード
2. インストール時に、追加言語として日本語を選択
3. インストール後、環境変数を設定するか、`.env`ファイルを作成して以下のように指定:

```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### 5. GPUチェック（必要な人だけ）

CUDAが使える状態かどうかを確認する。(Trueと出ていればOK)

```bash
python .\test\Cuda_checker.py
```

### 6. translator_main\.env ファイルの準備

面倒であれば、.env.exampleの.exampleを削除すれば使えます。<br>
GPUを使う場合は、USE_GPUにて True , 1, yes のいずれかを代入しておいてください。

## 使用方法

### 統合ランチャーを使用する方法（推奨）

1. 以下のコマンドを実行して、翻訳サーバーとモニターアプリケーションを一括で起動:

```bash
python app.py
```

これにより、翻訳サーバーが別プロセスで起動され、その後にモニター翻訳ツールが起動します。<br>
初回の起動時だけ、モデルのダウンロードが必要なので、少し待ってください。<br>
２回目以降はローカル上にモデルがあるのでそれを使う形になります。

### コンポーネントを個別に実行する方法

1. 翻訳サーバーを起動:

```bash
python -m monitor_translator.server_client.translate_server_run
```

2. 別のターミナルでモニター翻訳ツールを起動:

```bash
python -m monitor_translator.translator
```

### 操作方法

1. プログラムが開始すると、「お手軽翻訳ツール」というウィンドウが表示されます。
2. 英語が書かれている画面を表示します。
3. Shift + Alt + Z キーを同時入力したタイミングのマウスの位置を始点として、離した瞬間のマウスの位置を終点とする対角線の四角形の範囲で文字をキャプチャします。
4. 終了するには、「お手軽翻訳ツール」ウィンドウを閉じればいいです。或いは実行ターミナル上で Ctrl + c

## 環境設定

以下の環境変数を`.env`ファイルで設定することができます:

```
# Default language settings
DEFAULT_OCR_LANGUAGE="jpn+eng"
DEFAULT_TARGET_LANGUAGE="en-US"
# Path settings
# Windows default path for Tesseract
TESSERACT_PATH="C:\Program Files\Tesseract-OCR\tesseract.exe"
# Translate Server Use GPU
USE_GPU = false
# Translate Server Use NPU
USE_NPU = false
# Use Hugging Face model cache (true/false)
USE_MODEL_CACHE = true
```

## トラブルシューティング

### 翻訳サーバーが起動しない場合

- 必要なライブラリがすべてインストールされているか確認してください
- ポート11451が他のアプリケーションで使用されていないか確認してください
- ファイアウォール設定を確認してください(ローカル上なら気にしなくても良いはず)

### テキスト検出の精度が低い場合

- Tesseract OCRが正しくインストールされているか確認してください
- 適切な言語パックがインストールされているか確認してください

## 貢献

バグ報告や機能リクエストは、Issueを通じてお知らせください。プルリクエストも歓迎します。

## 作者

- [Borshchnabe](https://github.com/Borshchnabe)
- [pikkuri](https://github.com/pikkuri)

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。
