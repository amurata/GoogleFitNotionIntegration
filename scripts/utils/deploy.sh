#!/bin/bash
set -e

# 現在のスクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# プロジェクトのルートディレクトリを取得
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# 環境変数をロード
set -a
source "$PROJECT_ROOT/.env"
set +a

# APIキーの保護に関する重要なメモ
# ==================================
# Google Maps Weather APIはプレビュー版であり、APIキーの保護が必要です。
# 代替として気象庁のデータを使用する場合は、以下の点に注意してください：
#
# 1. 気象庁データの利用ポリシーを確認する
# 2. 適切なキャッシュ期間を設定する
# 3. リクエスト頻度を適切に制限する

echo "Google Cloud Functionsへデプロイしています..."

gcloud functions deploy GoogleFitNotionIntegration \
    --gen2 \
    --runtime python311 \
    --trigger-topic=fit \
    --region=asia-northeast1 \
    --entry-point=handler \
    --timeout=30 \
    --memory=256Mi \
    --set-env-vars=NOTION_SECRET=${NOTION_SECRET},DATABASE_ID=${DATABASE_ID},MAPS_API_KEY=${MAPS_API_KEY},LOCATION_LAT=${LOCATION_LAT},LOCATION_LNG=${LOCATION_LNG} \
    --source="$PROJECT_ROOT/src" \
    --project=${GCP_PROJECT}

echo "デプロイが完了しました。"
