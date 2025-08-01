# GitHub統合実装ノート

## 実装概要

GitHub活動データ（Issues、Pull Requests、Direct Commits）をNotionの日記データベースに自動同期するシステムを実装。

## 技術的決定事項

### 1. アーキテクチャパターン

**決定**: weather モジュールと同じ構造を採用
- `src/github/` ディレクトリ構造
- `github_notion.py` メインロジック
- `scripts/utils/update_github.sh` 手動実行スクリプト
- GitHub Actions による自動実行

**理由**: 既存のweatherモジュールとの整合性、メンテナンス性向上

### 2. API戦略の変更

**初期実装**: GitHub Search API使用
**最終実装**: 直接リポジトリAPI呼び出し

**変更理由**:
- Search APIでの403エラー頻発
- レート制限の厳しさ
- ユーザーの要望（「激しく使いたくない」）

**最適化**:
- リポジトリ数を109→10→4に段階的に制限
- `per_page` パラメータで効率化
- `updated` ソートで最新リポジトリを優先

### 3. 情報表示の集約

**課題**: 個別コミット表示で30+行になる問題
**解決策**: リポジトリごとにcommit数と変更行数を集約

```python
# リポジトリごとの集計例
"📝 repo-name:変更行数:+50-10 (5 commits)"
```

### 4. Direct Commits機能

**要件**: PRを経由しないmainブランチへの直接コミットも追跡
**実装ポイント**:
- PRコミットとの重複除外ロジック
- マージコミット除外（parents > 1）
- 変更行数の集計（additions/deletions）

## API効率化対策

### リポジトリ取得最適化
```python
params={
    "per_page": 4,  # 最小限に制限
    "sort": "updated",  # 更新日時順
    "direction": "desc"  # 最新優先
}
```

### Notion Rich Text実装
- Markdownリンクを Notion の `rich_text` 形式に変換
- クリック可能なリンク生成
- リポジトリ名の表示（`owner/repo` → `repo`）

## 自動実行システム

### GitHub Actions設定
- **実行時刻**: JST 24:30 (UTC 15:30) 
- **対象**: 前日のGitHub活動
- **手動実行**: 任意の日付指定可能

### 環境変数管理
- `GITHUB_TOKEN`: 自動提供（GitHub Actions）
- `NOTION_SECRET`: Repository Secrets
- `DATABASE_ID`: Repository Secrets

## トラブルシューティング履歴

### 1. ModuleNotFoundError: 'dotenv'
**解決**: カスタム `load_env_file()` 関数実装
**備考**: requirements.txtには既に存在していた

### 2. 403 Forbidden エラー
**原因**: GitHub Search API制限
**解決**: 直接リポジトリAPI + リポジトリ数制限

### 3. コミット情報過多
**原因**: 個別コミット表示
**解決**: リポジトリ単位での集約表示

## セキュリティ対応

### ハードコーディング排除
- `docs/GithubIntegration.md`: Notion DB ID削除
- `docs/GitHubActionsSetup.md`: 例示IDを汎用表現に変更
- 全体検索で他の機密情報なしを確認

### 認証管理
- GitHub Token: Actions自動提供
- Notion Token: Repository Secrets管理
- 最小権限の原則適用

## パフォーマンス指標

- **実行時間**: 通常1-3分
- **API呼び出し**: 約15-25回/日
- **レート制限**: GitHub 5000回/時（十分な余裕）
- **対象リポジトリ**: 最新4個に最適化

## 今後の拡張可能性

1. **リポジトリ数の動的調整**: アクティビティレベルに応じた自動調整
2. **通知機能**: 失敗時のSlack/Teams連携
3. **履歴保存**: 更新履歴の外部ストレージ保存
4. **Web API化**: HTTPエンドポイント化

## 運用監視項目

- **日次**: GitHub Actions実行ログ確認
- **週次**: Notionデータベース整合性確認
- **月次**: API使用量確認
- **四半期**: 認証トークン更新

## 技術仕様詳細

### Notion Rich Text形式
```python
{
    "type": "text",
    "text": {
        "content": "🎫 repo-name:Issue #123: タイトル",
        "link": {"url": "https://github.com/..."}
    }
}
```

### JST時間処理
```python
JST = datetime.timezone(datetime.timedelta(hours=9))
start_jst = datetime.datetime.combine(date, datetime.time(0, 0), tzinfo=JST)
start_utc = start_jst.astimezone(datetime.timezone.utc)
```

### PR除外ロジック
1. PRコミットSHA収集
2. 直接コミット検索時にSHAセットで除外
3. マージコミット（parents > 1）も除外

## 実装完了日

**開発期間**: 数日間の反復開発
**最終実装**: 2025年8月1日
**状態**: 本番運用準備完了