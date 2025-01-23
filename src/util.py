import os
import requests
from datetime import datetime, time as dt_time
from googleapiclient.discovery import build
import time
from constants import DATA_TYPES, ACTIVITY_TYPES

def convert_date_format(date_str, to_iso=True):
    """
    日付フォーマットを変換する
    to_iso=True: YYYY/MM/DD → YYYY-MM-DD
    to_iso=False: YYYY-MM-DD → YYYY/MM/DD
    """
    if to_iso:
        # YYYY/MM/DD → YYYY-MM-DD
        return date_str.replace('/', '-')
    else:
        # YYYY-MM-DD → YYYY/MM/DD
        return date_str.replace('-', '/')

def search_notion_page(database_id, date):
    """
    指定された日付のページをNotionデータベースから検索する
    """
    notion_secret = os.getenv("NOTION_SECRET")
    if not notion_secret:
        raise ValueError("NOTION_SECRET environment variable is not set")

    headers = {
        "Authorization": f"Bearer {notion_secret}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    # 日付をISO形式に変換
    iso_date = convert_date_format(date, to_iso=True)

    data = {
        "filter": {
            "property": "日付",
            "date": {
                "equals": iso_date
            }
        }
    }

    print(f"Search request data: {data}")  # デバッグ用
    response = requests.post(url, headers=headers, json=data)
    if not response.ok:
        print(f"Notion API error: {response.status_code} - {response.text}")
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[0] if results else None

def update_notion_page(page_id, properties):
    """
    既存のNotionページを更新する
    """
    notion_secret = os.getenv("NOTION_SECRET")
    if not notion_secret:
        raise ValueError("NOTION_SECRET environment variable is not set")

    headers = {
        "Authorization": f"Bearer {notion_secret}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = f"https://api.notion.com/v1/pages/{page_id}"

    # 日付プロパティの形式を変換
    if "日付" in properties and "date" in properties["日付"]:
        date_str = properties["日付"]["date"]["start"]
        properties["日付"]["date"]["start"] = convert_date_format(date_str, to_iso=True)

    data = {
        "properties": properties
    }

    print(f"Update request data: {data}")  # デバッグ用
    response = requests.patch(url, headers=headers, json=data)
    if not response.ok:
        print(f"Notion API error: {response.status_code} - {response.text}")
    response.raise_for_status()
    return response.json()

def create_notion_page(database_id, title, properties):
    """
    Notionのデータベースに新しいページを作成する
    """
    notion_secret = os.getenv("NOTION_SECRET")
    if not notion_secret:
        raise ValueError("NOTION_SECRET environment variable is not set")

    headers = {
        "Authorization": f"Bearer {notion_secret}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    url = "https://api.notion.com/v1/pages"

    # 日付プロパティの形式を変換
    if "日付" in properties and "date" in properties["日付"]:
        date_str = properties["日付"]["date"]["start"]
        properties["日付"]["date"]["start"] = convert_date_format(date_str, to_iso=True)

    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            **properties
        }
    }

    print(f"Create request data: {data}")  # デバッグ用
    response = requests.post(url, headers=headers, json=data)
    if not response.ok:
        print(f"Notion API error: {response.status_code} - {response.text}")
    response.raise_for_status()
    return response.json()

def get_google_fit_data(credentials, date):
    fitness_service = build("fitness", "v1", credentials=credentials)
    start_time = datetime.combine(date, dt_time.min)
    end_time = datetime.combine(date, dt_time.max)
    start_unix_time_millis = int(time.mktime(start_time.timetuple()) * 1000)
    end_unix_time_millis = int(time.mktime(end_time.timetuple()) * 1000)

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

    distance = round(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[0]['point']]) / 1000, 1)
    steps = sum([point['value'][0]['intVal'] for point in bucket.get("dataset")[1]['point']])
    calories = round(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[2]['point']]), 1)
    active_minutes = int(sum([point['value'][0]['fpVal'] for point in bucket.get("dataset")[3]['point']]))

    heart_rate_data = bucket.get("dataset")[4].get('point', [])
    avg_heart_rate = round(sum([point['value'][0]['fpVal'] for point in heart_rate_data]) / len(heart_rate_data), 1) if heart_rate_data else 0

    oxygen_data = bucket.get("dataset")[5].get('point', [])
    avg_oxygen = round(sum([point['value'][0]['fpVal'] for point in oxygen_data]) / len(oxygen_data), 1) if oxygen_data else 0

    weight_data = bucket.get("dataset")[6].get('point', [])
    latest_weight = round(weight_data[-1]['value'][0]['fpVal'], 1) if weight_data else 0

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

    return {
        "distance": distance,
        "steps": steps,
        "calories": calories,
        "active_minutes": active_minutes,
        "avg_heart_rate": avg_heart_rate,
        "avg_oxygen": avg_oxygen,
        "latest_weight": latest_weight,
        "total_sleep_minutes": total_sleep_minutes
    }
