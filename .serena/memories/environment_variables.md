# 環境変数設定

## 必須環境変数（.envファイル）

```bash
# Google Cloud Project ID
GCP_PROJECT=your-project-id

# Notion API Secret Token
NOTION_SECRET=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Notion Database ID
DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Maps API Key（天候情報取得用）
MAPS_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 位置情報（天候情報取得用）
LOCATION_LAT=35.6812  # デフォルト：東京駅
LOCATION_LNG=139.7671

# GitHub Personal Access Token
# repo スコープが必要（手動実行時）
# GitHub Actionsでは自動提供
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Cloud Function URL（デプロイ後に設定）
CLOUD_FUNCTION_URL=https://asia-northeast1-your-project.cloudfunctions.net/your-function-name
```

## 設定方法
1. `.env.example`をコピーして`.env`を作成
2. 各APIキー・トークンを取得して設定
3. **重要**: `.env`ファイルは絶対にGitにコミットしない（.gitignoreに登録済み）

## 認証情報の管理
- Google認証: Firestoreで管理（`scripts/utils/auth.py`で設定）
- Notion/GitHub: 環境変数で管理
- ローテーション: 3ヶ月ごとに`scripts/utils/rotate_credentials.py`実行推奨