# GitHub リポジトリ設定ガイド

このドキュメントでは、ENJAPPプロジェクトをGitHubで公開するための設定手順について説明します。

## リポジトリの作成

1. GitHubにログインし、新しいリポジトリを作成します。
   - リポジトリ名: `monitor_translator` または `enjapp`
   - 説明: 「画面上の文章を簡易翻訳するツール」
   - 公開設定: Public
   - READMEの初期化: チェックを外す（既存のREADMEを使用するため）
   - ライセンス: MIT（既存のLICENSEファイルを使用するため、選択不要）

2. ローカルリポジトリを設定し、GitHubにプッシュします：
   ```bash
   # リポジトリの初期化（まだ行っていない場合）
   git init
   
   # リモートリポジトリの追加
   git remote add origin https://github.com/Borshchnabe/enjapp.git
   
   # 全ファイルをステージング
   git add .
   
   # 初回コミット
   git commit -m "Initial commit"
   
   # mainブランチにプッシュ
   git push -u origin main
   ```

## リポジトリの設定

### 1. Issue テンプレートの設定

`/.github/ISSUE_TEMPLATE/` ディレクトリを作成し、以下のテンプレートを追加します：

#### バグ報告テンプレート

ファイル名: `bug_report.md`
```markdown
---
name: バグ報告
about: アプリケーションの問題を報告する
title: '[BUG] '
labels: bug
assignees: ''
---

## バグの説明
バグについての明確で簡潔な説明を記入してください。

## 再現手順
バグを再現するための手順:
1. '...' に移動
2. '....' をクリック
3. '....' までスクロール
4. エラーを確認

## 期待される動作
何が起こるべきだったのかについての明確で簡潔な説明。

## スクリーンショット
可能であれば、問題を説明するためのスクリーンショットを追加してください。

## 環境情報
 - OS: [例: Windows 10]
 - バージョン: [例: 1.0.1]
 - Python バージョン: [例: 3.8.5]
 - その他の関連情報

## 追加情報
ここに問題に関するその他の情報を追加してください。
```

#### 機能リクエストテンプレート

ファイル名: `feature_request.md`
```markdown
---
name: 機能リクエスト
about: このプロジェクトのアイデアを提案する
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## 機能リクエストは問題に関連していますか？
問題が何であるかについての明確で簡潔な説明。例: 私はいつも [...] のときにフラストレーションを感じます

## 希望するソリューションの説明
何が起こってほしいのかについての明確で簡潔な説明。

## 検討した代替案
検討した代替ソリューションや機能についての明確で簡潔な説明。

## 追加情報
ここに機能リクエストに関するその他の情報やスクリーンショットを追加してください。
```

### 2. Pull Request テンプレートの設定

ファイル名: `/.github/PULL_REQUEST_TEMPLATE.md`
```markdown
## 変更内容
この PR で何が変更されたのかを簡潔に説明してください。

## 関連する Issue
この PR が解決する Issue 番号を記載してください。例: #123

## 変更の種類
- [ ] バグ修正
- [ ] 新機能
- [ ] コードスタイルの更新（フォーマット、変数名など）
- [ ] リファクタリング（機能変更なし）
- [ ] ビルド関連の変更
- [ ] CI関連の変更
- [ ] ドキュメントの更新
- [ ] その他（詳細を記載）

## チェックリスト
- [ ] コードをセルフレビューしました
- [ ] コメントを追加/更新しました（特に理解しにくいコードの場合）
- [ ] ドキュメントを更新しました（必要な場合）
- [ ] 変更によって新しい警告が発生していません
- [ ] テストを追加/更新しました（該当する場合）
- [ ] 既存のテストがすべて通過します

## スクリーンショット（該当する場合）

## その他の情報
```

### 3. リポジトリの設定

GitHubリポジトリの「Settings」タブで以下の設定を行います：

#### 一般設定
- リポジトリ名: `enjapp` または `monitor_translator`
- 説明: 「画面上の文章を簡易翻訳するツール」
- トピック: `translation`, `ocr`, `screen-capture`, `python`, `m2m100`
- 機能: Issues, Wiki, Discussions を有効化

#### ブランチ保護
- `main` ブランチを保護するルールを設定
- マージ前にレビューを必須にする（オプション）
- ステータスチェックを必須にする（オプション）

#### コラボレーター
- 共同開発者（Borshchnabe, pikkuri）を追加

### 4. GitHub Actions の設定（オプション）

基本的なCI/CDパイプラインを設定するために、`.github/workflows/` ディレクトリを作成し、以下のワークフローファイルを追加します：

ファイル名: `python-app.yml`
```yaml
name: Python Application

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python 3.8
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest
        pip install -e .
    - name: Lint with flake8
      run: |
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero treats all errors as warnings
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    - name: Test with pytest
      run: |
        pytest
```

## リリースの管理

### 1. リリースの作成

1. GitHubリポジトリの「Releases」セクションに移動します。
2. 「Draft a new release」ボタンをクリックします。
3. タグバージョンを入力します（例: `v1.0.1`）。
4. リリースタイトルを入力します（例: 「ENJAPP v1.0.1」）。
5. リリースノートを記入します（CHANGELOG.mdの内容を参照）。
6. ビルド済みのインストーラファイル（`ENJAPP_Setup.exe`）をアップロードします。
7. 「Publish release」ボタンをクリックします。

### 2. リリースの自動化（オプション）

GitHub Actionsを使用して、タグプッシュ時に自動的にリリースを作成するワークフローを設定できます：

ファイル名: `.github/workflows/release.yml`
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python 3.8
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    - name: Build with PyInstaller
      run: |
        python -m PyInstaller enjapp_fixed.spec
    - name: Build Installer
      run: |
        iscc installer.iss
    - name: Create Release
      id: create_release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: ENJAPP ${{ github.ref }}
        draft: false
        prerelease: false
    - name: Upload Release Asset
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: ${{ steps.create_release.outputs.upload_url }}
        asset_path: ./Output/ENJAPP_Setup.exe
        asset_name: ENJAPP_Setup.exe
        asset_content_type: application/octet-stream
```

## コミュニティガイドライン

### 1. 行動規範の設定

ファイル名: `CODE_OF_CONDUCT.md`
```markdown
# 行動規範

## 私たちの約束

オープンで歓迎的な環境を育むために、私たちは貢献者およびメンテナーとして、年齢、体型、障害、民族性、性自認および性別表現、経験レベル、国籍、個人の外見、人種、宗教、または性的同一性および指向に関係なく、私たちのプロジェクトおよびコミュニティへの参加を、誰にとっても嫌がらせのない体験にすることを誓います。

## 私たちの標準

前向きな環境を作り出すことに貢献する行動の例：

* 友好的かつ包括的な言葉を使う
* 異なる視点や経験を尊重する
* 建設的な批判を素直に受け入れる
* コミュニティにとって何が最善かに焦点を当てる
* 他のコミュニティメンバーに共感を示す

参加者による容認できない行動の例：

* 性的な言葉や画像の使用、および不適切な性的注目または誘い
* トローリング、侮辱的/軽蔑的なコメント、個人的または政治的攻撃
* 公的または私的な嫌がらせ
* 明示的な許可なく、他者の個人情報（物理的または電子的アドレスなど）を公開する
* 職業上不適切と合理的に考えられるその他の行為

## 私たちの責任

プロジェクトメンテナーは、許容される行動の基準を明確にする責任があります。また、何かしらの許容できない行動に対応して、適切かつ公平な是正措置をとることが期待されています。

プロジェクトメンテナーは、この行動規範に沿わないコメント、コミット、コード、Wiki編集、Issueなどの貢献を削除、編集、または拒否する権利と責任を持ちます。また、不適切、脅迫的、攻撃的、または有害と見なされる他の行動に対して、一時的または永久的に貢献者を追放する権利と責任を持ちます。

## 適用範囲

この行動規範は、個人がプロジェクトやそのコミュニティを代表するとき、プロジェクト内および公共空間の両方に適用されます。プロジェクトまたはコミュニティを代表する例としては、公式プロジェクトのEメールアドレスの使用、公式ソーシャルメディアアカウントを通じての投稿、オンラインまたはオフラインのイベントでの代表者としての行動などがあります。プロジェクトの表現は、プロジェクトメンテナーによってさらに定義され明確化される場合があります。

## 執行

虐待、嫌がらせ、またはその他の容認できない行動の事例は、プロジェクトチーム（[メールアドレスを挿入]）に連絡することで報告できます。すべての苦情は、レビューおよび調査され、状況に対して必要かつ適切と判断される対応がとられます。プロジェクトチームは、事象の報告者に関する守秘義務があります。具体的な執行ポリシーの詳細が別途投稿される場合があります。

この行動規範に誠意をもって従わない、または執行しないプロジェクトメンテナーは、プロジェクトをリードする他のメンバーの決定により、一時的または永久的な影響を受ける場合があります。
```

## まとめ

以上の設定を行うことで、ENJAPPプロジェクトはGitHub上で適切に管理され、コミュニティの参加を促進することができます。リポジトリの設定は、プロジェクトの成長に合わせて随時更新することをお勧めします。
