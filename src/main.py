import os
import time
import json
import datetime
import httplib2
import functions_framework
from util import create_notion_page, search_notion_page, update_notion_page
from googleapiclient.discovery import build
from google.cloud import firestore
from oauth2client.client import GoogleCredentials

@functions_framework.http
def handler(request):
    try:
        # Firestoreから認証情報を取得
        db = firestore.Client()
        doc_ref = db.collection(u'credentials').document(u'google_fit')
        doc = doc_ref.get()
        if doc.exists:
            credentials_dict = doc.to_dict()
            credentials = GoogleCredentials.from_json(json.dumps(credentials_dict))
        else:
            raise ValueError("Firestoreに認証情報が存在しません。")

        http = credentials.authorize(httplib2.Http())
        credentials.refresh(http)  # 認証トークンを更新する。

        # 更新された認証情報をFirestoreに保存
        updated_credentials_dict = json.loads(credentials.to_json())
        doc_ref.set(updated_credentials_dict)

        fitness_service = build("fitness", "v1", http=http)
        # Google Fitから昨日の歩数データを取得
        yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
        start_time = datetime.datetime.combine(yesterday, datetime.time.min)
        end_time = datetime.datetime.combine(yesterday, datetime.time.max)
        start_unix_time_millis = int(time.mktime(start_time.timetuple()) * 1000)
        end_unix_time_millis = int(time.mktime(end_time.timetuple()) * 1000)
        request_body = {
            "aggregateBy": [
                {
                    "dataTypeName": "com.google.distance.delta",  # 移動距離
                },
                {
                    "dataTypeName": "com.google.step_count.delta",  # 歩数
                },
                {
                    "dataTypeName": "com.google.calories.expended",  # 消費カロリー
                },
                {
                    "dataTypeName": "com.google.heart_minutes",  # 強めの運動
                },
            ],
            "bucketByTime": {
                "durationMillis": end_unix_time_millis - start_unix_time_millis
            },
            "startTimeMillis": start_unix_time_millis,
            "endTimeMillis": end_unix_time_millis,
        }

        dataset = fitness_service.users().dataset().aggregate(userId="me", body=request_body).execute()
        bucket = dataset.get("bucket")[0]
        # メートルからキロメートルに変換し、小数点1桁に丸める
        distance = round(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[0]['point']]) / 1000, 1)
        steps = sum([point['value'][0]['intVal'] for point in bucket.get("dataset")[1]['point']])
        # 小数点1桁に丸める
        calories = round(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[2]['point']]), 1)
        active_minutes = int(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[3]['point']]))

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
