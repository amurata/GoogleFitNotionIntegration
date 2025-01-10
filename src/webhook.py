import os
import functions_framework
from google.cloud import pubsub_v1
import json

# 環境変数の取得
WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY")
GCP_PROJECT = os.getenv("GCP_PROJECT")

# 環境変数のバリデーション
if not WEBHOOK_API_KEY:
    raise ValueError("WEBHOOK_API_KEY environment variable is not set")
if not GCP_PROJECT:
    raise ValueError("GCP_PROJECT environment variable is not set")

@functions_framework.http
def webhook_handler(request):
    """
    Webhookリクエストを受け取り、Pub/Subメッセージを発行する

    Args:
        request: Cloud Functions request object

    Returns:
        dict: Response with status and message

    Raises:
        ValueError: Invalid request parameters
    """
    try:
        # リクエストメソッドの確認
        if request.method != 'POST':
            return {
                "status": "error",
                "message": "Only POST method is allowed"
            }, 405

        # APIキーの検証
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            print("Error: Missing API key")
            return {
                "status": "error",
                "message": "Missing API key"
            }, 401

        if api_key != WEBHOOK_API_KEY:
            print("Error: Invalid API key")
            return {
                "status": "error",
                "message": "Invalid API key"
            }, 401

        # クエリパラメータからモードを取得（today or yesterday）
        mode = request.args.get("mode", "yesterday")
        if mode not in ["today", "yesterday"]:
            print(f"Error: Invalid mode: {mode}")
            return {
                "status": "error",
                "message": "Invalid mode. Must be 'today' or 'yesterday'"
            }, 400

        # Pub/Subクライアントの初期化
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GCP_PROJECT, "fit")

        # モードに応じてメッセージを設定
        message = "trigger_today" if mode == "today" else "trigger"

        print(f"Publishing message '{message}' to topic 'fit'")

        # メッセージをパブリッシュ
        try:
            future = publisher.publish(topic_path, message.encode("utf-8"))
            message_id = future.result()  # 送信完了を待つ
            print(f"Published message with ID: {message_id}")
        except Exception as e:
            print(f"Error publishing message: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to publish message to Pub/Sub"
            }, 500

        return {
            "status": "success",
            "message": f"Successfully triggered Google Fit data fetch for {mode}",
            "details": {
                "mode": mode,
                "message_id": message_id
            }
        }

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            "status": "error",
            "message": "Internal server error"
        }, 500
