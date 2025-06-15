import os
import json
import functions_framework
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.cloud import firestore
from src.util import get_google_fit_data, update_notion_page
from src.constants import OAUTH_SCOPE

# 環境変数の取得
GCP_PROJECT = os.getenv("GCP_PROJECT")

def get_credentials():
    """Firestoreから認証情報を取得し、必要に応じて更新する"""
    try:
        print("Firestoreから認証情報を取得中...")
        db = firestore.Client()
        doc_ref = db.collection(u'credentials').document(u'google_fit')
        doc = doc_ref.get()
        
        if not doc.exists:
            print("Firestoreに認証情報が見つかりません。scripts/utils/auth.pyを実行してください。")
            return None
        
        cred_dict = doc.to_dict()
        print("認証情報を取得しました")
        
        credentials = Credentials(
            token=cred_dict['token'],
            refresh_token=cred_dict['refresh_token'],
            token_uri=cred_dict['token_uri'],
            client_id=cred_dict['client_id'],
            client_secret=cred_dict['client_secret'],
            scopes=cred_dict['scopes']
        )
        
        # トークンが期限切れかどうかチェック
        if credentials.expired and credentials.refresh_token:
            print("トークンが期限切れです。更新中...")
            credentials.refresh(Request())
            # 更新されたトークンをFirestoreに保存
            save_credentials_to_firestore(credentials)
            print("トークンを更新しました")
        
        return credentials
        
    except Exception as e:
        print(f"認証情報の取得中にエラーが発生しました: {str(e)}")
        return None

def save_credentials_to_firestore(credentials):
    """認証情報をFirestoreに保存"""
    try:
        db = firestore.Client()
        doc_ref = db.collection(u'credentials').document(u'google_fit')
        cred_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(cred_dict)
        print("認証情報をFirestoreに保存しました")
    except Exception as e:
        print(f"Firestore保存中にエラーが発生しました: {str(e)}")

def process_data_for_date(target_date):
    """指定された日付のGoogle Fitデータを取得してNotionに記録する"""
    try:
        print(f"Processing data for date: {target_date}")
        
        # 認証情報を取得
        credentials = get_credentials()
        if not credentials:
            raise ValueError("認証情報が取得できません。scripts/utils/auth.pyを実行してください。")

        # Google Fitからデータを取得
        print("Fetching Google Fit data...")
        fit_data = get_google_fit_data(credentials, target_date)
        print("Retrieved Google Fit data:", json.dumps(fit_data, indent=2))

        # Notionのプロパティを更新
        database_id = os.getenv("DATABASE_ID")
        formatted_date = target_date.strftime("%Y-%m-%d")
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
        res = update_notion_page(database_id, properties, target_date)
        print("Notion API response:", json.dumps(res, indent=2))

        return {
            "status": "success",
            "message": f"Successfully updated Google Fit data for {formatted_date}",
            "details": {
                "date": formatted_date,
                "fit_data": fit_data
            }
        }

    except Exception as e:
        print(f"Error processing Google Fit data: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to process Google Fit data: {str(e)}"
        }

def process_yesterday_data():
    """昨日のデータを処理する"""
    yesterday = datetime.now().date() - timedelta(days=1)
    return process_data_for_date(yesterday)

def trigger_today():
    """今日のデータを処理する"""
    today = datetime.now().date()
    return process_data_for_date(today)

@functions_framework.cloud_event
def handler(cloud_event):
    """Cloud Functionsのエントリーポイント（Pub/Subトリガー）"""
    try:
        # Pub/Subメッセージからデータを取得
        import base64
        
        if cloud_event.data and 'message' in cloud_event.data:
            message_data = cloud_event.data['message'].get('data', '')
            if message_data:
                # Base64デコード
                decoded_data = base64.b64decode(message_data).decode('utf-8')
                print(f"Received message: {decoded_data}")
                
                # 日付文字列をパース
                try:
                    target_date = datetime.strptime(decoded_data, "%Y-%m-%d").date()
                    result = process_data_for_date(target_date)
                except ValueError:
                    print(f"Invalid date format: {decoded_data}")
                    result = process_yesterday_data()
            else:
                print("No message data, processing yesterday's data")
                result = process_yesterday_data()
        else:
            print("No message in cloud event, processing yesterday's data")
            result = process_yesterday_data()
        
        print("Processing result:", json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        print(f"Error in handler: {str(e)}")
        return {
            "status": "error",
            "message": f"Handler error: {str(e)}"
        }

@functions_framework.http
def http_handler(request):
    """HTTPトリガー用のエントリーポイント"""
    try:
        if request.method == 'GET':
            return {
                "status": "ok",
                "message": "Health check passed"
            }
        
        if request.method == 'POST':
            request_json = request.get_json()
            date_str = request_json.get('message', '') if request_json else ''
            
            if date_str:
                try:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    result = process_data_for_date(target_date)
                except ValueError:
                    result = process_yesterday_data()
            else:
                result = process_yesterday_data()
            
            return result
        
        return {
            "status": "error",
            "message": "Only GET and POST methods are allowed"
        }, 405
        
    except Exception as e:
        print(f"Error in http_handler: {str(e)}")
        return {
            "status": "error",
            "message": f"HTTP handler error: {str(e)}"
        }, 500
