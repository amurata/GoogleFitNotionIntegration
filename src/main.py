import os
import json
from datetime import datetime, timedelta
import functions_framework
from util import create_notion_page, search_notion_page, update_notion_page, get_google_fit_data
from google.cloud import firestore
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from constants import OAUTH_SCOPE

# 環境変数の取得
WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY")
GCP_PROJECT = os.getenv("GCP_PROJECT")

@functions_framework.http
def webhook_handler(request):
    """
    NotionのWebhookリクエストを受け取り、Pub/Subメッセージを発行する
    """
    print("Received request:", request.method)
    print("Headers:", dict(request.headers))

    # ヘルスチェック用のGETリクエスト対応
    if request.method == 'GET':
        return {
            "status": "ok",
            "message": "Health check passed"
        }

    try:
        # POSTリクエストの処理
        if request.method != 'POST':
            return {
                "status": "error",
                "message": "Only POST method is allowed"
            }, 405

        # APIキーの検証
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        print("All headers:", dict(request.headers))
        print("API Key from headers:", api_key)
        print("Expected API Key:", WEBHOOK_API_KEY)

        if not api_key or api_key != WEBHOOK_API_KEY:
            print("Error: Invalid API key")
            print("Received:", api_key)
            print("Expected:", WEBHOOK_API_KEY)
            return {
                "status": "error",
                "message": "Unauthorized",
                "details": {
                    "received_key": api_key,
                    "expected_key": WEBHOOK_API_KEY
                }
            }, 401

        # リクエストボディの取得
        try:
            request_json = request.get_json()
            print("Request body:", json.dumps(request_json, indent=2))
        except Exception as e:
            print("Error parsing JSON:", str(e))
            print("Raw request data:", request.get_data())
            return {
                "status": "error",
                "message": "Invalid JSON payload"
            }, 400

        # プロパティの取得
        properties = request_json.get('properties', {})
        page_id = request_json.get('pageId')

        print("Properties:", json.dumps(properties, indent=2))
        print("Page ID:", page_id)

        if not page_id:
            print("Page ID not found in request")
            return {
                "status": "error",
                "message": "Page ID is required"
            }, 400

        # 日付プロパティの取得
        date_prop = properties.get('日付', {}).get('date', {}).get('start')
        if not date_prop:
            print("Date property not found in:", properties)
            return {
                "status": "error",
                "message": "Date property is required"
            }, 400

        print("Date property:", date_prop)

        # 日付文字列をdatetimeオブジェクトに変換
        try:
            target_date = datetime.strptime(date_prop, "%Y-%m-%d").date()
        except ValueError:
            try:
                target_date = datetime.strptime(date_prop, "%Y/%m/%d").date()
            except ValueError:
                print("Invalid date format:", date_prop)
                return {
                    "status": "error",
                    "message": "Invalid date format"
                }, 400

        print("Target date:", target_date)

        # Firestoreから認証情報を取得
        try:
            db = firestore.Client()
            doc_ref = db.collection(u'credentials').document(u'google_fit')
            doc = doc_ref.get()
            if doc.exists:
                cred_dict = doc.to_dict()
                try:
                    credentials = Credentials(
                        token=cred_dict['token'],
                        refresh_token=cred_dict['refresh_token'],
                        token_uri=cred_dict['token_uri'],
                        client_id=cred_dict['client_id'],
                        client_secret=cred_dict['client_secret'],
                        scopes=cred_dict['scopes']
                    )
                except KeyError:
                    credentials = Credentials.from_authorized_user_info(
                        json.loads(cred_dict['token_info']),
                        OAUTH_SCOPE
                    )
            else:
                raise ValueError("Firestoreに認証情報が存在しません。")

            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                updated_cred_dict = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }
                doc_ref.set(updated_cred_dict)

            # Google Fitからデータを取得
            print("Fetching Google Fit data for date:", target_date)
            fit_data = get_google_fit_data(credentials, target_date)
            print("Retrieved Google Fit data:", json.dumps(fit_data, indent=2))

            # Notionのプロパティを更新
            database_id = os.getenv("DATABASE_ID")
            formatted_date = target_date.strftime("%Y/%m/%d")
            print("Formatted date:", formatted_date)

            properties = {
                "移動距離 (km)": {"number": fit_data["distance"]},
                "歩数 (歩)": {"number": fit_data["steps"]},
                "消費カロリー (kcal)": {"number": fit_data["calories"]},
                "強めの運動 (分)": {"number": fit_data["active_minutes"]},
                "平均心拍数 (bpm)": {"number": fit_data["avg_heart_rate"]},
                "酸素飽和度 (%)": {"number": fit_data["avg_oxygen"]},
                "体重 (kg)": {"number": fit_data["latest_weight"] if fit_data["latest_weight"] > 0 else None},
                "睡眠時間 (分)": {"number": fit_data["total_sleep_minutes"]},
                "日付": {"date": {"start": formatted_date}}
            }

            print("Updating Notion properties:", json.dumps(properties, indent=2))

            # ページを更新
            print("Updating Notion page:", page_id)
            res = update_notion_page(page_id, properties)
            print("Notion API response:", json.dumps(res, indent=2))

            return {
                "status": "success",
                "message": f"Successfully updated Google Fit data for {formatted_date}",
                "details": {
                    "page_id": page_id,
                    "date": formatted_date
                }
            }

        except Exception as e:
            print(f"Error processing Google Fit data: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process Google Fit data: {str(e)}"
            }, 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            "status": "error",
            "message": "Internal server error"
        }, 500

def get_credentials():
    """Firestoreから認証情報を取得し、必要に応じて更新する"""
    try:
        db = firestore.Client()
        doc_ref = db.collection(u'credentials').document(u'google_fit')
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Firestoreに認証情報が存在しません。")

        cred_dict = doc.to_dict()
        try:
            credentials = Credentials(
                token=cred_dict['token'],
                refresh_token=cred_dict['refresh_token'],
                token_uri=cred_dict['token_uri'],
                client_id=cred_dict['client_id'],
                client_secret=cred_dict['client_secret'],
                scopes=cred_dict['scopes']
            )
        except KeyError:
            credentials = Credentials.from_authorized_user_info(
                json.loads(cred_dict['token_info']),
                OAUTH_SCOPE
            )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            updated_cred_dict = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            doc_ref.set(updated_cred_dict)

        return credentials
    except Exception as e:
        print(f"認証情報の取得に失敗: {str(e)}")
        raise

def process_data_for_date(target_date):
    """指定された日付のデータを処理する"""
    try:
        credentials = get_credentials()
        fit_data = get_google_fit_data(credentials, target_date)
        formatted_date = target_date.strftime("%Y/%m/%d")
        page_title = "Google Fit Data " + formatted_date

        # Notionのページを検索
        page = search_notion_page(os.getenv("DATABASE_ID"), formatted_date)

        if page:  # ページが存在する場合は更新
            page_id = page["id"]
            print(f"Updating existing Notion page for {formatted_date}")

            properties = {
                "移動距離 (km)": {"number": fit_data["distance"]},
                "歩数 (歩)": {"number": fit_data["steps"]},
                "消費カロリー (kcal)": {"number": fit_data["calories"]},
                "強めの運動 (分)": {"number": fit_data["active_minutes"]},
                "平均心拍数 (bpm)": {"number": fit_data["avg_heart_rate"]},
                "酸素飽和度 (%)": {"number": fit_data["avg_oxygen"]},
                "体重 (kg)": {"number": fit_data["latest_weight"] if fit_data["latest_weight"] > 0 else None},
                "睡眠時間 (分)": {"number": fit_data["total_sleep_minutes"]},
                "日付": {"date": {"start": formatted_date}}
            }

            res = update_notion_page(page_id, properties)
            print(f"Successfully updated Notion page for {formatted_date}")
            return res
        else:  # ページが存在しない場合は新規作成
            print(f"Creating new Notion page for {formatted_date}")

            properties = {
                "移動距離 (km)": {"number": fit_data["distance"]},
                "歩数 (歩)": {"number": fit_data["steps"]},
                "消費カロリー (kcal)": {"number": fit_data["calories"]},
                "強めの運動 (分)": {"number": fit_data["active_minutes"]},
                "平均心拍数 (bpm)": {"number": fit_data["avg_heart_rate"]},
                "酸素飽和度 (%)": {"number": fit_data["avg_oxygen"]},
                "体重 (kg)": {"number": fit_data["latest_weight"] if fit_data["latest_weight"] > 0 else None},
                "睡眠時間 (分)": {"number": fit_data["total_sleep_minutes"]},
                "日付": {"date": {"start": formatted_date}}
            }

            res = create_notion_page(os.getenv("DATABASE_ID"), formatted_date, properties)
            print(f"Successfully created Notion page for {formatted_date}")
            return res

    except Exception as e:
        print(f"Error processing data for {target_date}: {str(e)}")
        raise

def process_yesterday_data():
    """昨日のデータを処理する"""
    yesterday = (datetime.now() - timedelta(days=1)).date()
    return process_data_for_date(yesterday)

def trigger_today():
    """今日のデータを処理する"""
    today = datetime.now().date()
    return process_data_for_date(today)

@functions_framework.cloud_event
def handler(cloud_event):
    """Pub/Subメッセージを処理するハンドラー"""
    try:
        import base64
        message = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        print(f"Received message: {message}")

        if message == "trigger":
            return process_yesterday_data()
        else:
            try:
                target_date = datetime.strptime(message, '%Y-%m-%d').date()
                return process_data_for_date(target_date)
            except ValueError:
                print(f"Invalid date format: {message}")
                return process_yesterday_data()

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}, 500
