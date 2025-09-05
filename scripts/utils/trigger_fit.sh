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

# 引数チェック
if [ $# -eq 1 ]; then
    # 1つの引数の場合：単一の日付を処理
    TARGET_DATE=$1
    echo "対象日付: ${TARGET_DATE}"
    
    # 日付を指定してPub/Subメッセージを発行
    echo "Pub/Subトピックを発行: ${TARGET_DATE}"
    gcloud pubsub topics publish fit \
        --message="${TARGET_DATE}" \
        --project=${GCP_PROJECT}
    
elif [ $# -eq 2 ]; then
    # 2つの引数の場合：日付範囲を処理
    START_DATE=$1
    END_DATE=$2
    echo "日付範囲: ${START_DATE} から ${END_DATE}"
    
    # 日付をループで処理
    current_date="$START_DATE"
    # 日付を数値に変換して比較
    while true; do
        echo "処理中: ${current_date}"
        
        # 各日付に対してPub/Subメッセージを発行
        gcloud pubsub topics publish fit \
            --message="${current_date}" \
            --project=${GCP_PROJECT}
        
        # 終了日に達したら終了
        if [ "$current_date" = "$END_DATE" ]; then
            break
        fi
        
        # 次の日付に進む（macOSとLinux両方に対応）
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            current_date=$(date -j -v+1d -f "%Y-%m-%d" "$current_date" +"%Y-%m-%d")
        else
            # Linux
            current_date=$(date -d "$current_date + 1 day" +"%Y-%m-%d")
        fi
        
        # 日付が終了日を超えたらループを終了（安全対策）
        current_num=$(echo "$current_date" | tr -d '-')
        end_num=$(echo "$END_DATE" | tr -d '-')
        if [ "$current_num" -gt "$end_num" ]; then
            echo "警告: 終了日を超えました。処理を終了します。"
            break
        fi
        
        # API制限を避けるため少し待機
        sleep 2
    done
    
else
    # 引数がない場合は通常の自動処理をトリガー
    echo "Pub/Subトピックを発行して処理をトリガー"
    gcloud pubsub topics publish fit \
        --message="trigger" \
        --project=${GCP_PROJECT}
fi

# ログを表示（最新の50件、レベルをINFOに設定）
echo "ログを確認中..."
echo "30秒後にログを取得します..."
sleep 30  # 処理時間を長めに設定

# Cloud Functions Gen2のログを取得（複数の方法を試す）
echo "=== Cloud Functions ログ ==="
gcloud functions logs read GoogleFitNotionIntegration \
    --project=${GCP_PROJECT} \
    --region=asia-northeast1 \
    --limit=50 \
    --min-log-level=info \
    --format="table(time_utc,severity,log)" || true

# Cloud Runのログも念のため確認
echo ""
echo "=== Cloud Run ログ（関数の実行環境）==="
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=googlefitnotionintegration" \
    --project=${GCP_PROJECT} \
    --limit=20 \
    --format="table(timestamp,severity,textPayload)" || true

echo ""
echo "処理完了"