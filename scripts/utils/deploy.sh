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

gcloud functions deploy GoogleFitNotionIntegration \
    --gen2 \
    --runtime python39 \
    --trigger-topic=fit \
    --region=asia-northeast1 \
    --entry-point=handler \
    --timeout=30 \
    --memory=256Mi \
    --set-env-vars=NOTION_SECRET=${NOTION_SECRET},DATABASE_ID=${DATABASE_ID} \
    --source="$PROJECT_ROOT/src" \
    --project=${GCP_PROJECT}
