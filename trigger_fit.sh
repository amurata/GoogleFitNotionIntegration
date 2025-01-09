#!/bin/bash

# 環境変数を読み込む
echo "Read .env"
set -a
source .env
set +a


# Google Fit データ取得をトリガーするスクリプト
echo "Publish pubsub topic to trigger fit"
gcloud pubsub topics publish fit --message="trigger" --project=${GCP_PROJECT}

# ログを表示（最新の10件）
echo "Checking logs..."
sleep 5  # ログが更新されるまで少し待機
gcloud functions logs read GoogleFitNotionIntegration \
    --project=${GCP_PROJECT} \
    --region=asia-northeast1 \
    --limit=10
