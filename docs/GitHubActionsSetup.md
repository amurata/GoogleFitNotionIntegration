# GitHub Actions 自動実行セットアップガイド

## 概要

毎日JST 24:30（翌日00:30）に前日のGitHub活動データを自動でNotionに同期するGitHub Actionsワークフローのセットアップ手順です。

## 🔧 必要な設定

### 1. Repository Secretsの設定

GitHubリポジトリのSettings → Secrets and variables → Actionsで以下を設定：

| Secret名 | 説明 | 取得方法 |
|---------|------|---------|
| `NOTION_SECRET` | Notion Integration トークン | [Notion Integrations](https://www.notion.so/my-integrations)で作成 |
| `DATABASE_ID` | NotionデータベースID | NotionデータベースURLから抽出 |

**注意:** `GITHUB_TOKEN`は自動で提供されるため設定不要です。

#### DATABASE_IDの取得方法
NotionデータベースのURLから32文字のIDを抽出：
```
https://www.notion.so/workspace/YOUR_DATABASE_ID_HERE?v=...
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                この部分がDATABASE_ID
```

### 2. 失敗時メール通知の設定

1. **GitHub Settings → Notifications**にアクセス
2. **Actions**セクションで以下を設定：
   - ✅ "Send notifications for failed workflows only"
   - ✅ "Email notifications"
3. メールアドレスを確認・設定

## 📅 実行スケジュール

- **定期実行**: 毎日JST 24:30（UTC 15:30）
- **処理対象**: 前日のGitHub活動（Issue、PR、Direct Commits）
- **例**: 8/1 00:30に7/31のデータを処理

## 🚀 手動実行

緊急時や特定日付を処理したい場合：

1. **Actions**タブ → **Daily GitHub Activity Sync**
2. **Run workflow**ボタンをクリック
3. 日付を指定（省略時は昨日）
4. **Run workflow**で実行

## 📊 実行状況の確認

### 成功時
- ✅ 緑色のチェックマーク
- ログに"GitHub活動データの同期が正常に完了しました"

### 失敗時
- ❌ 赤色のXマーク
- 設定したメールアドレスに通知
- ログでエラー詳細を確認可能

## 🔍 トラブルシューティング

### よくある問題

#### 1. Notion API エラー
```
エラー: 403 Forbidden
```
**解決策**: 
- NOTION_SECRETが正しく設定されているか確認
- NotionデータベースがIntegrationと共有されているか確認

#### 2. GitHub API エラー
```
エラー: 403 Client Error: Forbidden
```
**解決策**:
- GITHUB_TOKENは自動設定のため、通常発生しない
- リポジトリの権限設定を確認

#### 3. 日付フォーマット エラー
```
エラー: 日付パースエラー
```
**解決策**:
- 手動実行時の日付はYYYYMMDD形式で入力
- 例: 20250731

### ログの確認方法

1. **Actions**タブ → 該当のワークフロー実行をクリック
2. **sync-github-activity**ジョブをクリック
3. 各ステップのログを展開して詳細確認

## 📈 監視・メンテナンス

### 定期確認項目

- **週次**: Actions実行履歴の確認
- **月次**: Notionデータベースでのデータ整合性確認
- **四半期**: NOTION_SECRETの更新（セキュリティ強化）

### パフォーマンス情報

- **実行時間**: 通常1-3分
- **API呼び出し**: 約15-25回/日
- **GitHubレート制限**: 5000回/時（十分な余裕）

## 🔒 セキュリティ

- **Secrets**: GitHubの暗号化されたSecrets機能で安全に保管
- **トークン**: 最小権限の原則に従った設定
- **ログ**: 機密情報はマスクされて表示

## 📞 サポート

問題が発生した場合：

1. **Actions**ログでエラー詳細を確認
2. Notion/GitHubの認証情報を再確認
3. 手動実行でテスト
4. 必要に応じてSecrets再設定

---

**注意**: このワークフローは個人のリポジトリでのみ動作します。他者のリポジトリアクセスには別途権限設定が必要です。