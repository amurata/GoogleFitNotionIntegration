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

# 必要なサービスを有効化
gcloud services enable fitness.googleapis.com

# PubSubトピックが存在しない場合は作成
if ! gcloud pubsub topics describe fit --project=${GCP_PROJECT} > /dev/null 2>&1; then
  gcloud pubsub topics create fit --project=${GCP_PROJECT}
fi

# Cloud Schedulerジョブを作成
gcloud scheduler jobs create pubsub fit_job \
  --schedule="00 04 * * *" \
  --topic=fit \
  --message-body="trigger" \
  --time-zone="Asia/Tokyo" \
  --location="asia-northeast1" \
  --project=${GCP_PROJECT}
