# プロジェクト構造

## ディレクトリ構成

```
.
├── src/                       # メインソースコード
│   ├── main.py               # Cloud Function メインハンドラー
│   ├── util.py               # Google Fit/Notion ユーティリティ
│   ├── constants.py          # 定数定義
│   ├── trigger_date.py       # 日付指定バッチトリガー
│   ├── batch_process.sh      # バッチ処理シェルスクリプト
│   ├── weather/              # 天気関連モジュール
│   │   ├── weather_notion.py # 天気データ取得・Notion更新
│   │   └── update_weather.py # 天気データ取得・保存
│   └── github/               # GitHub関連モジュール
│       └── github_notion.py  # GitHub活動データ同期
│
├── scripts/utils/            # ユーティリティスクリプト
│   ├── auth.py              # Google認証・Firestore保存
│   ├── deploy.sh            # GCP デプロイスクリプト
│   ├── trigger_fit.sh       # Google Fitデータ手動トリガー
│   ├── update_weather.sh    # 天気データ更新スクリプト
│   ├── update_github.sh     # GitHub活動更新スクリプト
│   ├── audit_credentials.py # 認証情報監査
│   └── rotate_credentials.py # 認証ローテーション
│
├── docs/                     # ドキュメント
│   ├── architecture.png     # アーキテクチャ図
│   ├── GitHubActionsSetup.md # GitHub Actions設定ガイド
│   └── notes/               # 実装ノート
│
├── instructions/            # AI開発アシスタント用指示
│   └── *.md                # 各種開発ルール・規約
│
├── .env.example             # 環境変数テンプレート
├── requirements.txt         # Python依存関係（ルート）
└── src/requirements.txt     # Cloud Functions用依存関係
```

## 主要コンポーネント
- **main.py**: PubSubトリガーを受けてGoogle Fitデータを処理
- **util.py**: Google Fit API、Notion API共通処理
- **weather_notion.py**: 天気データ取得とNotion更新
- **github_notion.py**: GitHub APIからデータ取得、Notion同期（クラスベース実装）