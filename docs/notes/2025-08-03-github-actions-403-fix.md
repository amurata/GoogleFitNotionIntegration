# GitHub Actions 403エラー修正とOrganization環境構築

**日付:** 2025年8月3日  
**タスク内容:** GitHub Actions 403エラー修正、arkatom Organization作成、天気スクリプト環境変数エラー修正

## 実施したタスク

### 1. GitHub Actions 403エラーの根本原因特定と修正

**問題内容:**  
`daily-github-sync.yml`実行時に「403 Client Error: Forbidden」が発生。GitHub活動データの取得ができない状態。

**初期の仮説と対策:**
- Personal Access Token (PAT) の権限不足と考え、新しいPATを作成
- Repository Secretsに`GH_PAT`として設定
- ワークフローファイルを`secrets.GITHUB_TOKEN`から`secrets.GH_PAT`に変更

**真の原因発見:**  
ユーザーからの鋭い指摘「github workflow がコミット・プッシュされてないからじゃないか？」で判明。
- ワークフローファイルの変更がローカルのみで、GitHub上に反映されていない
- GitHub Actionsは**リモートリポジトリの最新バージョン**のワークフローを実行
- つまり古い設定（`secrets.GITHUB_TOKEN`）で実行され続けていた

**解決プロセス:**
1. `git status`で未コミット状態を確認
2. `.github/workflows/daily-github-sync.yml`をステージング・コミット
3. `git push`でリモートに反映
4. ワークフロー再実行 → **SUCCESS** 🎉

### 2. GitHub Organization "arkatom" 環境構築

**背景:**  
新規プロジェクト（ai-instructions, serena-tools）をOrganizationで管理する方針。

**実施内容:**
- GitHub Organization `arkatom` 作成（Freeプラン）
- ベストプラクティスに従ったディレクトリ構成
  - 個人: `/ghq/github.com/amurata/`
  - Organization: `/ghq/github.com/arkatom/`
- リポジトリ作成とクローン：
  - `arkatom/ai-instructions` - AI開発指示のCLIツール
  - `arkatom/serena-tools` - Serena統合パッケージ
- 各リポジトリに詳細なIssue作成

**技術的課題:**  
MCP GitHub APIツールがOrganizationリポジトリの操作権限を持たないため、`gh` CLIに切り替えて対応。

### 3. 天気スクリプトの環境変数エラー修正

**問題内容:**  
`./scripts/utils/update_weather.sh`実行時に「環境変数 NOTION_SECRET または DATABASE_ID が設定されていません」エラー。

**原因特定:**  
`src/weather/weather_notion.py`で`os.environ.get()`を使用しているが、`.env`ファイルの読み込み処理が不足。他のモジュール（GitHub）では独自の`load_env_file()`関数を実装済み。

**修正内容:**
```python
def load_env_file():
    """
    .envファイルから環境変数を読み込む（python-dotenvの代替）
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# .envファイルを読み込み
load_env_file()
```

## 気を付けた点

### 1. 基本原則の徹底
- **質を最優先** - 適当な推測ではなく、確実な原因特定
- **深層思考** - 表面的でない根本原因の追求
- **完璧性** - 一度で確実に解決する姿勢

### 2. Git操作の基本確認
- GitHub Actionsの問題では、まずローカルとリモートの同期状態確認が必須
- 設定ファイル変更後は**必ずコミット・プッシュの確認**

### 3. 環境変数管理の統一性
- プロジェクト内で一貫した環境変数読み込み方式の採用
- `python-dotenv`の代わりに独自実装を使用している理由の理解

## 方針変更点

### PAT設定からGit操作確認への転換
**当初の方針:** Personal Access Tokenの権限不足として対処  
**変更理由:** ユーザーの指摘により、より基本的なGit操作不備が原因と判明  
**新方針:** 設定変更後は必ずリモート反映を確認する基本ワークフローの徹底

この方針変更により、複雑なトークン再発行作業ではなく、シンプルなコミット・プッシュで解決。

## 重要なポイント

### 1. GitHub Actionsの実行仕組み
- **ローカル変更 ≠ GitHub Actions実行内容**
- ワークフローファイルはリモートリポジトリから読み込まれる
- 設定変更後のコミット・プッシュは必須作業

### 2. Organization管理のベストプラクティス
- ghqディレクトリ構成: `github.com/{owner}/{repo}`
- 個人アカウントとOrganizationの明確な分離
- MCP APIツールの制限とCLI代替手段の活用

### 3. 環境変数読み込みの一貫性
- プロジェクト内での統一的な`.env`読み込み方式
- `python-dotenv`依存を避けた独自実装の利点
- モジュール間での実装差異が生む問題

### 4. 問題解決のアプローチ
- **仮説→検証→修正** のサイクル
- ユーザーからの指摘を素直に受け入れる姿勢
- 複雑な解決策より、基本的な確認を優先

## 得られた知見

### 1. エラー調査の優先順位
複雑なAPI権限問題を疑う前に、基本的なGit操作の確認が重要。今回のケースでは：
- 高度な原因（PAT権限）を疑った
- 基本的な原因（未コミット）が実際の問題だった

### 2. プロジェクト構成の重要性
- 一貫したコーディング規約と環境設定
- モジュール間での実装統一の価値
- ドキュメント化された手順の重要性

### 3. ツール制限への対応
- MCP APIツールの制限を理解し、適切な代替手段（gh CLI）を選択
- 複数のアプローチを組み合わせた柔軟な問題解決

## 愚痴（本音）

正直、最初にPATの権限を疑って複雑に考えすぎた。ユーザーの「コミット・プッシュされてないからじゃないか？」の一言で目が覚めた。基本的なことを見落とすのは、経験豊富でも起こりうる典型的なミス。

特にGitHub Actionsのようなリモート実行環境では「ローカルで動く ≠ リモートで動く」の原則を忘れがち。設定ファイルを変更したら**必ずコミット・プッシュ**という基本中の基本を、複雑な問題だと思い込んで見落とした。

ただし、この経験により：
- 基本確認の重要性を再認識
- ユーザーの指摘を素直に受け入れる価値を実感
- 複雑に考えがちな技術者の典型的な落とし穴を体験

結果的には良い学習機会になった。今後は「複雑な原因を疑う前に、基本的な確認を徹底する」を肝に銘じる。