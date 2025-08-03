# コードスタイルと規約

## Python コーディングスタイル
- **インデント**: スペース4つ
- **文字エンコーディング**: UTF-8
- **文字列**: ダブルクォート `"` を基本使用
- **定数**: 大文字とアンダースコア (例: `GCP_PROJECT`, `DATA_TYPES`)
- **関数名**: snake_case (例: `get_google_fit_data`, `update_notion_page`)
- **クラス名**: PascalCase (例: `GitHubNotionSync`)

## コードパターン
- **エラーハンドリング**: try-exceptブロックでエラーをキャッチし、詳細なログ出力
- **環境変数**: python-dotenvで.envファイルから読み込み
- **日付処理**: datetime, dateutil使用、JST対応
- **API通信**: requestsライブラリ使用、ヘッダー認証
- **Firestore**: google-cloud-firestoreでcredential管理

## ドキュメント
- **関数**: 簡潔な日本語でdocstring記載
- **ログ**: 日本語でユーザーフレンドリーなメッセージ
- **README**: 詳細な手順を日本語で記載

## 型ヒント
- 基本的に型ヒントなし（既存コードスタイルに準拠）