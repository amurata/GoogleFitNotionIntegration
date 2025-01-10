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
    NotionのWebhookリクエストを受け取り、Pub/Subメッセージを発行する

    Args:
        request: Cloud Functions request object

    Returns:
        dict: Response with status and message
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
        if not api_key or api_key != WEBHOOK_API_KEY:
            print("Error: Invalid API key")
            return {
                "status": "error",
                "message": "Unauthorized"
            }, 401

        # リクエストボディの取得
        try:
            request_json = request.get_json()
        except Exception:
            print("Error: Invalid JSON")
            return {
                "status": "error",
                "message": "Invalid JSON payload"
            }, 400

        # プロパティの取得
        properties = request_json.get('properties', {})

        # ボタンのプロパティから取得モードを判断
        # デフォルトは today とする
        mode = "today"

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

if __name__ == "__main__":
    # ローカルでのテスト用
    functions_framework.start()
