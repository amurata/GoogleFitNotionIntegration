#!/bin/bash

# 現在のスクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# プロジェクトのルートディレクトリを取得
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# 環境変数をロード
echo "環境変数を読み込み中..."
set -a
source "$PROJECT_ROOT/.env"
set +a

# 引数がある場合は指定された日付のデータを取得
if [ $# -eq 1 ]; then
    TARGET_DATE=$1
    echo "対象日付: ${TARGET_DATE}"
    # 日付を指定してPub/Subメッセージを発行
    gcloud pubsub topics publish fit \
        --message="${TARGET_DATE}" \
        --project=${GCP_PROJECT}
else
    # 引数がない場合は通常の自動処理をトリガー
    echo "Pub/Subトピックを発行して処理をトリガー"
    gcloud pubsub topics publish fit \
        --message="trigger" \
        --project=${GCP_PROJECT}
fi

# ログを表示（最新の10件）
# echo "ログを確認中..."
# sleep 5
# gcloud functions logs read GoogleFitNotionIntegration \
#     --project=${GCP_PROJECT} \
#     --region=asia-northeast1 \
#     --limit=10
