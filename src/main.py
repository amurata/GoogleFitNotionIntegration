import os
import time
import json
import datetime
import functions_framework
from util import create_notion_page, search_notion_page, update_notion_page
from googleapiclient.discovery import build
from google.cloud import firestore
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from constants import OAUTH_SCOPE, DATA_TYPES, ACTIVITY_TYPES

@functions_framework.http
def handler(request):
    try:
        # Firestoreから認証情報を取得
        db = firestore.Client()
        doc_ref = db.collection(u'credentials').document(u'google_fit')
        doc = doc_ref.get()
        if doc.exists:
            cred_dict = doc.to_dict()
            try:
                # 新しい形式での認証情報の取得を試みる
                credentials = Credentials(
                    token=cred_dict['token'],
                    refresh_token=cred_dict['refresh_token'],
                    token_uri=cred_dict['token_uri'],
                    client_id=cred_dict['client_id'],
                    client_secret=cred_dict['client_secret'],
                    scopes=cred_dict['scopes']
                )
            except KeyError:
                # 古い形式の認証情報の場合
                credentials = Credentials.from_authorized_user_info(
                    json.loads(cred_dict['token_info']),
                    OAUTH_SCOPE
                )
        else:
            raise ValueError("Firestoreに認証情報が存在しません。")

        # 必要に応じてトークンを更新
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # 更新された認証情報をFirestoreに保存
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

        fitness_service = build("fitness", "v1", credentials=credentials)
        # Google Fitから昨日のデータを取得
        yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
        start_time = datetime.datetime.combine(yesterday, datetime.time.min)
        end_time = datetime.datetime.combine(yesterday, datetime.time.max)
        start_unix_time_millis = int(time.mktime(start_time.timetuple()) * 1000)
        end_unix_time_millis = int(time.mktime(end_time.timetuple()) * 1000)

        # アクティビティデータの取得
        activity_request_body = {
            "aggregateBy": [
                {"dataTypeName": DATA_TYPES["distance"]},
                {"dataTypeName": DATA_TYPES["steps"]},
                {"dataTypeName": DATA_TYPES["calories"]},
                {"dataTypeName": DATA_TYPES["active_minutes"]},
                {"dataTypeName": DATA_TYPES["heart_rate"]},
                {"dataTypeName": DATA_TYPES["oxygen"]},
                {"dataTypeName": DATA_TYPES["weight"]},
            ],
            "bucketByTime": {
                "durationMillis": end_unix_time_millis - start_unix_time_millis
            },
            "startTimeMillis": start_unix_time_millis,
            "endTimeMillis": end_unix_time_millis,
        }

        dataset = fitness_service.users().dataset().aggregate(userId="me", body=activity_request_body).execute()
        bucket = dataset.get("bucket")[0]

        # 基本データの取得
        distance = round(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[0]['point']]) / 1000, 1)
        steps = sum([point['value'][0]['intVal'] for point in bucket.get("dataset")[1]['point']])
        calories = round(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[2]['point']]), 1)
        active_minutes = int(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[3]['point']]))

        # 追加データの取得
        heart_rate_data = bucket.get("dataset")[4].get('point', [])
        avg_heart_rate = round(sum([point['value'][0]['fpVal'] for point in heart_rate_data]) / len(heart_rate_data), 1) if heart_rate_data else 0

        oxygen_data = bucket.get("dataset")[5].get('point', [])
        avg_oxygen = round(sum([point['value'][0]['fpVal'] for point in oxygen_data]) / len(oxygen_data), 1) if oxygen_data else 0

        weight_data = bucket.get("dataset")[6].get('point', [])
        latest_weight = round(weight_data[-1]['value'][0]['fpVal'], 1) if weight_data else 0

        # 睡眠データの取得（セッションAPI使用）
        sleep_request = fitness_service.users().sessions().list(
            userId="me",
            startTime=start_time.isoformat() + "Z",
            endTime=end_time.isoformat() + "Z",
            activityType=ACTIVITY_TYPES["sleep"]
        ).execute()

        total_sleep_minutes = 0
        if 'session' in sleep_request:
            for session in sleep_request['session']:
                start = int(session['startTimeMillis'])
                end = int(session['endTimeMillis'])
                total_sleep_minutes += (end - start) // (1000 * 60)

        # NotionのデータベースIDと新しいページのタイトルを指定
        database_id = os.getenv("DATABASE_ID")
        formatted_date = yesterday.strftime("%Y/%m/%d")
        page_title = "Google Fit Data " + formatted_date

        # Notionのプロパティを動的に設定
        properties = {
            "移動距離 (km)": {
                "number": distance
            },
            "歩数 (歩)": {
                "number": steps
            },
            "消費カロリー (kcal)": {
                "number": calories
            },
            "強めの運動 (分)": {
                "number": active_minutes
            },
            "平均心拍数 (bpm)": {
                "number": avg_heart_rate
            },
            "酸素飽和度 (%)": {
                "number": avg_oxygen
            },
            "体重 (kg)": {
                "number": latest_weight if latest_weight > 0 else None
            },
            "睡眠時間 (分)": {
                "number": total_sleep_minutes
            },
            "日付": {
                "date": {
                    "start": formatted_date
                }
            }
        }

        # 同じ日付のページを検索
        existing_page = search_notion_page(database_id, formatted_date)

        if existing_page:
            # 既存のページが見つかった場合は更新
            print(f"Updating existing page for date: {formatted_date}")
            res = update_notion_page(existing_page["id"], properties)
        else:
            # 新しいページを作成
            print(f"Creating new page for date: {formatted_date}")
            res = create_notion_page(database_id, page_title, properties)

        return {"status": "success", "message": "Data successfully processed"}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}, 500
