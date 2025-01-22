#!/bin/bash

# 環境変数を読み込む
echo "Read .env"
set -a
source .env
set +a

# 引数がある場合は指定された日付のデータを取得
if [ $# -eq 1 ]; then
    TARGET_DATE=$1
    echo "Target date: ${TARGET_DATE}"
    # 日付を指定してPub/Subメッセージを発行
    gcloud pubsub topics publish fit \
        --message="${TARGET_DATE}" \
        --project=${GCP_PROJECT}
else
    # 引数がない場合は通常の自動処理をトリガー
    echo "Publish pubsub topic to trigger fit"
    gcloud pubsub topics publish fit \
        --message="trigger" \
        --project=${GCP_PROJECT}
fi

# ログを表示（最新の10件）
echo "Checking logs..."
sleep 5
gcloud functions logs read GoogleFitNotionIntegration \
    --project=${GCP_PROJECT} \
    --region=asia-northeast1 \
    --limit=10
