# 推奨コマンド集

## 開発環境セットアップ
```bash
# 仮想環境作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集して必要な値を設定
```

## 認証・デプロイ
```bash
# Google認証とFirestore保存（初回セットアップ）
python scripts/utils/auth.py

# Cloud Functionsへデプロイ
./scripts/utils/deploy.sh
```

## データ同期実行
```bash
# Google Fitデータ同期（特定日付または当日）
./scripts/utils/trigger_fit.sh [YYYY-MM-DD]

# 天気データ更新（特定日付または2日前）
./scripts/utils/update_weather.sh [YYYY-MM-DD]

# GitHub活動データ更新（特定日付または昨日）
./scripts/utils/update_github.sh [YYYYMMDD]

# バッチ処理（複数日をまとめて処理）
bash src/batch_process.sh 2025-04-01 2025-04-10
bash src/batch_process.sh --fit-only 2025-04-01 2025-04-10
bash src/batch_process.sh --weather-only 2025-04-01 2025-04-10
```

## メンテナンス・監査
```bash
# 認証情報の監査
python scripts/utils/audit_credentials.py

# 認証情報のローテーション（3ヶ月ごと推奨）
python scripts/utils/rotate_credentials.py
```

## Git操作
```bash
# ステータス確認
git status

# 変更の追加とコミット
git add .
git commit -m "feat: 機能追加"

# リモートへプッシュ
git push origin main
```

## システムユーティリティ（Darwin/macOS）
```bash
# ファイル検索
find . -name "*.py" -type f

# ディレクトリ表示
ls -la

# プロセス確認
ps aux | grep python

# ログ確認（GCPコンソールで確認推奨）
gcloud functions logs read
```

## テスト・品質チェック
現在、このプロジェクトには専用のテスト・リンティング・フォーマットツールは設定されていません。
必要に応じて以下を追加可能：
- pytest（テスト）
- black（フォーマット）
- flake8/pylint（リンティング）