# ENJAPP 開発ガイド

このドキュメントでは、ENJAPPの開発環境のセットアップと開発プロセスについて説明します。

## 開発環境のセットアップ

### 前提条件

- Python 3.8以上
- Git
- Tesseract OCR
- （オプション）CUDA対応のGPU（高速化のため）

### リポジトリのクローンと環境構築

1. リポジトリをクローンします：
   ```bash
   git clone https://github.com/yourusername/monitor_translator.git
   cd monitor_translator
   ```

2. 仮想環境を作成し、有効化します：
   ```bash
   python -m venv venv
   
   # Windowsの場合
   .\venv\Scripts\activate
   
   # Linux/macOSの場合
   source venv/bin/activate
   ```

3. 開発モードでプロジェクトをインストールします：
   ```bash
   pip install -e .
   ```

4. （オプション）GPU対応の依存関係をインストールします：
   ```bash
   pip install -e .[gpu]
   ```

### 開発用設定

開発中は、以下の設定を`.env`ファイルに追加すると便利です：

```
# 開発モード設定
DEBUG=true

# モデルキャッシュを使用（開発中は有効にしておくと便利）
USE_MODEL_CACHE=true

# Tesseractのパス
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## プロジェクト構造

```
monitor_translator/
├── app.py                    # 統合ランチャー
├── setup.py                  # パッケージ設定
├── README.md                 # プロジェクト概要
├── LICENSE                   # MITライセンス
├── CONTRIBUTING.md           # 貢献ガイドライン
├── CHANGELOG.md              # 変更履歴
├── installer.iss             # Inno Setupインストーラ設定
├── build_installer.ps1       # インストーラビルドスクリプト
├── scripts/                  # 補助スクリプト
├── docs/                     # ドキュメント
└── translator_main/          # メインパッケージ
    ├── __init__.py
    ├── .env                  # 環境設定ファイル
    └── translator/           # 翻訳モジュール
        ├── __init__.py
        ├── translator.py     # tkinterベースの翻訳ツール
        ├── gui/              # GUIコンポーネント
        │   ├── __init__.py
        │   └── qt_translator.py  # PyQt5ベースの翻訳ツール
        ├── ocr/              # OCR関連モジュール
        │   └── __init__.py
        └── server_client/    # 翻訳サーバー/クライアント
            ├── __init__.py
            ├── translate_client.py    # 翻訳クライアント
            └── translate_server_run.py  # 翻訳サーバー
```

## 主要コンポーネントの説明

### 1. 統合ランチャー（app.py）

アプリケーションのエントリーポイントです。翻訳サーバーを起動し、その後にモニター翻訳ツールを起動します。

### 2. 翻訳サーバー（translate_server_run.py）

M2M100モデルを使用して翻訳を行うサーバーコンポーネントです。FastAPIを使用してREST APIを提供します。

主な機能：
- モデルのロードとキャッシュ管理
- 翻訳エンドポイントの提供
- GPU/NPUサポート

### 3. 翻訳クライアント（translate_client.py）

翻訳サーバーと通信するクライアントコンポーネントです。サーバーが利用できない場合のフォールバックメカニズムも提供します。

### 4. GUI（qt_translator.py）

PyQt5ベースのユーザーインターフェースです。スクリーンキャプチャ、OCR、翻訳結果の表示を担当します。

## モデルキャッシュの仕組み

ENJAPPでは、Hugging Faceの`transformers`ライブラリを使用してM2M100翻訳モデルをロードします。環境変数`USE_MODEL_CACHE`により、モデルのキャッシュ動作を制御できます：

```python
# translate_server_run.py内の実装
use_cache = os.environ.get("USE_MODEL_CACHE", "true").lower() in ("true", "1", "yes")
if use_cache:
    # キャッシュを使用してモデルをロード
    model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
else:
    # キャッシュを使用せずにモデルをロード
    model = M2M100ForConditionalGeneration.from_pretrained(
        "facebook/m2m100_418M", 
        use_cache=False
    )
```

## インストーラの構築

Windows用インストーラは、Inno Setupを使用して構築されています。`installer.iss`ファイルにインストーラの設定が定義されています。

インストーラの構築手順：

1. PyInstallerでアプリケーションをビルドします：
   ```bash
   python -m PyInstaller enjapp_fixed.spec
   ```

2. Inno Setupでインストーラをビルドします：
   ```bash
   iscc installer.iss
   ```

または、提供されているビルドスクリプトを使用します：
```bash
.\build_installer.ps1
```

### インストーラの自動アンインストール機能

`installer.iss`ファイルには、既存のバージョンを自動的に検出してアンインストールする機能が実装されています：

```pascal
function InitializeSetup(): Boolean;
var
  UninstallString: String;
  ResultCode: Integer;
  UninstallSuccessful: Boolean;
begin
  Result := True;
  
  // レジストリから既存のアンインストーラ情報を取得
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1',
     'UninstallString', UninstallString) then
  begin
    // 既存のバージョンが見つかった場合、ユーザーに確認
    if MsgBox('{#MyAppName}の以前のバージョンが見つかりました...', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 自動的にアンインストールを実行
      UninstallSuccessful := Exec(UninstallString, '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end
  end
end;
```

## テスト

現在、自動テストは実装されていません。将来的には、以下のテスト戦略を検討しています：

1. ユニットテスト：個々のコンポーネントの機能をテスト
2. 統合テスト：コンポーネント間の連携をテスト
3. E2Eテスト：ユーザーの視点からの全体的な機能をテスト

## 今後の開発計画

1. 多言語サポートの拡張
2. UIのカスタマイズオプションの追加
3. ホットキーのカスタマイズ機能
4. 自動テストの実装
5. パフォーマンスの最適化
