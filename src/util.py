import os
import requests
from datetime import datetime, time as dt_time, timedelta
from googleapiclient.discovery import build
import time
from constants import DATA_TYPES, ACTIVITY_TYPES
from activity_types import get_english_name
import json
from google.cloud import firestore
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

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
    複数のエントリーがある場合、「振り返り」チェックが入っていないエントリーを優先的に返す
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
    
    if not results:
        return None
    
    # 複数のエントリーがある場合、「振り返り」チェックが入っていないエントリーを優先選択
    for page in results:
        page_id = page["id"]
        
        # ページの詳細情報を取得して「振り返り」プロパティを確認
        try:
            page_details_response = requests.get(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=headers
            )
            if page_details_response.ok:
                page_details = page_details_response.json()
                
                # 「振り返り」プロパティが存在し、チェックされているか確認
                if "振り返り" in page_details["properties"]:
                    is_reflection_checked = page_details["properties"]["振り返り"].get("checkbox", False)
                    if not is_reflection_checked:  # チェックが入っていない場合
                        return page
                else:
                    # 「振り返り」プロパティが存在しない場合も優先対象とする
                    return page
        except Exception as e:
            print(f"Warning: Failed to check reflection property for page {page_id}: {str(e)}")
            # エラーが発生した場合はそのページを返す
            return page
    
    # すべてのエントリーで「振り返り」チェックが入っている場合、最初のエントリーを返す
    print(f"Warning: All entries for date {iso_date} have reflection checkbox checked.")
    return results[0]

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
    """
    Google Fitからデータを取得する
    """
    fitness_service = build("fitness", "v1", credentials=credentials)
    start_time = datetime.combine(date, dt_time.min)
    end_time = datetime.combine(date, dt_time.max)
    start_unix_time_millis = int(time.mktime(start_time.timetuple()) * 1000)
    end_unix_time_millis = int(time.mktime(end_time.timetuple()) * 1000)
    
    # 変数初期化
    resting_heart_rate = 0
    latest_body_fat = 0

    activity_request_body = {
        "aggregateBy": [
            {"dataTypeName": DATA_TYPES["distance"]},
            {"dataTypeName": DATA_TYPES["steps"]},
            {"dataTypeName": DATA_TYPES["calories"]},
            {"dataTypeName": DATA_TYPES["active_minutes"]},  # Heart Points
            {"dataTypeName": DATA_TYPES["heart_rate"]},
            {"dataTypeName": DATA_TYPES["oxygen"]},
            {"dataTypeName": DATA_TYPES["weight"]},
            {"dataTypeName": DATA_TYPES["body_fat"]},  # 体脂肪率
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
    # Heart Points を計算（活動強度の指標）
    try:
        heart_points_data = bucket.get("dataset")[3].get('point', [])
        if heart_points_data:
            active_minutes = int(sum([point['value'][0]['fpVal'] for point in heart_points_data]))
            # デバッグログ（高強度活動の記録）
            if active_minutes > 180:  # 3時間以上の活動をログ
                print(f"High activity detected: {active_minutes} Heart Points - Great workout!")
        else:
            active_minutes = 0
    except (KeyError, IndexError, TypeError) as e:
        print(f"Warning: Failed to get Heart Points data: {e}")
        active_minutes = 0
    
    # Move Minutes は利用できない場合があるため、代替値を使用
    move_minutes = 0  # Move Minutesが利用できない環境のため0に設定
    
    heart_rate_data = bucket.get("dataset")[4].get('point', [])
    if heart_rate_data:
        heart_rates = [point['value'][0]['fpVal'] for point in heart_rate_data]
        avg_heart_rate = round(sum(heart_rates) / len(heart_rates), 1)
        max_heart_rate = round(max(heart_rates), 1)
        min_heart_rate = round(min(heart_rates), 1)
        
        # 安静時心拍数を推定（下位10%の心拍数の平均）
        sorted_rates = sorted(heart_rates)
        resting_count = max(1, len(sorted_rates) // 10)  # 最低1つは使用
        resting_heart_rate = round(sum(sorted_rates[:resting_count]) / resting_count, 1)
    else:
        avg_heart_rate = max_heart_rate = min_heart_rate = resting_heart_rate = 0

    oxygen_data = bucket.get("dataset")[5].get('point', [])
    avg_oxygen = round(sum([point['value'][0]['fpVal'] for point in oxygen_data]) / len(oxygen_data), 1) if oxygen_data else 0

    weight_data = bucket.get("dataset")[6].get('point', [])
    latest_weight = round(weight_data[-1]['value'][0]['fpVal'], 1) if weight_data else 0
    
    # 体脂肪率データ
    try:
        body_fat_data = bucket.get("dataset")[7].get('point', [])
        latest_body_fat = round(body_fat_data[-1]['value'][0]['fpVal'], 1) if body_fat_data else 0
    except (KeyError, IndexError, TypeError):
        latest_body_fat = 0  # 体脂肪率データが無い場合

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
    
    # マインドフルネス（瞑想）セッションを取得
    meditation_request = fitness_service.users().sessions().list(
        userId="me",
        startTime=start_time.isoformat() + "Z",
        endTime=end_time.isoformat() + "Z",
        activityType=ACTIVITY_TYPES["meditation"]
    ).execute()
    
    meditation_sessions = 0
    total_meditation_minutes = 0
    if 'session' in meditation_request:
        meditation_sessions = len(meditation_request['session'])
        for session in meditation_request['session']:
            start = int(session['startTimeMillis'])
            end = int(session['endTimeMillis'])
            total_meditation_minutes += (end - start) // (1000 * 60)
    
    # 全アクティビティセッションを取得（重複除去付き）
    all_sessions = fitness_service.users().sessions().list(
        userId="me",
        startTime=start_time.isoformat() + "Z",
        endTime=end_time.isoformat() + "Z"
    ).execute()
    
    activity_summary = {}
    processed_times = []  # 重複チェック用
    
    if 'session' in all_sessions:
        for session in all_sessions['session']:
            activity_type = session.get('activityType', 0)
            app_name = session.get('application', {}).get('name', 'Unknown')
            start_ms = int(session['startTimeMillis'])
            end_ms = int(session['endTimeMillis'])
            duration_min = (end_ms - start_ms) // (1000 * 60)
            
            # 重複チェック（同じ時間帯のアクティビティはスキップ）
            is_duplicate = False
            for processed_start, processed_end in processed_times:
                # 時間の重なりをチェック
                if not (end_ms <= processed_start or start_ms >= processed_end):
                    # 優先度: AutoSleep > AppleWatch > その他
                    # 優先度: Strava > Nike Run Club > その他
                    if ('AutoSleep' in app_name or 'Strava' in app_name):
                        # 高優先度アプリのデータを保持
                        continue
                    else:
                        is_duplicate = True
                        break
            
            if not is_duplicate and duration_min > 0:
                processed_times.append((start_ms, end_ms))
                
                # アクティビティタイプ名を取得（英語名で統一）
                activity_name = get_english_name(activity_type)
                
                if activity_name not in activity_summary:
                    activity_summary[activity_name] = 0
                activity_summary[activity_name] += duration_min

    return {
        "distance": distance,
        "steps": steps,
        "calories": calories,
        "active_minutes": active_minutes,  # Heart Points（活動強度）
        "move_minutes": move_minutes,  # Move Minutes（実際の活動時間）
        "avg_heart_rate": avg_heart_rate,
        "max_heart_rate": max_heart_rate,
        "min_heart_rate": min_heart_rate,
        "resting_heart_rate": resting_heart_rate,  # 安静時心拍数（疲労回復指標）
        "avg_oxygen": avg_oxygen,
        "latest_weight": latest_weight,
        "latest_body_fat": latest_body_fat,  # 体脂肪率
        "total_sleep_minutes": total_sleep_minutes,
        "meditation_sessions": meditation_sessions,
        "total_meditation_minutes": total_meditation_minutes,
        "activity_summary": activity_summary  # アクティビティ種類別時間
    }

def update_notion_page_with_date(database_id, properties, target_date):
    """
    指定された日付のNotionページを検索し、「振り返り」チェックが入っていないエントリーを優先的に更新する
    """
    # 日付をISO形式に変換
    formatted_date = target_date.strftime("%Y-%m-%d")
    
    # 既存のページを検索
    page = search_notion_page(database_id, formatted_date)
    
    if page:
        # 既存のページを更新
        page_id = page["id"]
        print(f"既存のページを更新します: {formatted_date}")
        return update_notion_page(page_id, properties)
    else:
        # 新しいページを作成
        title = f"Health Data - {formatted_date}"
        print(f"新しいページを作成します: {formatted_date}")
        return create_notion_page(database_id, title, properties)


def get_credentials_from_firestore(collection_name='credentials', document_name='google_fit'):
    """
    Firestoreから認証情報を取得し、必要に応じて更新する
    
    Args:
        collection_name: Firestoreのコレクション名
        document_name: Firestoreのドキュメント名
        
    Returns:
        Credentials: Google認証情報オブジェクト、または None
    """
    try:
        print(f"Firestoreから認証情報を取得中... (collection: {collection_name}, doc: {document_name})")
        db = firestore.Client()
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()

        if not doc.exists:
            print(f"Firestoreに認証情報が見つかりません。")
            return None

        cred_dict = doc.to_dict()
        print("認証情報を取得しました")

        # Credentialsオブジェクトを作成
        credentials = Credentials(
            token=cred_dict.get('token'),
            refresh_token=cred_dict.get('refresh_token'),
            token_uri=cred_dict.get('token_uri'),
            client_id=cred_dict.get('client_id'),
            client_secret=cred_dict.get('client_secret'),
            scopes=cred_dict.get('scopes')
        )

        # トークンが期限切れかどうかチェック
        if credentials.expired and credentials.refresh_token:
            print("トークンが期限切れです。更新中...")
            credentials.refresh(Request())
            # 更新されたトークンをFirestoreに保存
            save_credentials_to_firestore(credentials, collection_name, document_name)
            print("トークンを更新しました")

        return credentials

    except Exception as e:
        print(f"認証情報の取得中にエラーが発生しました: {str(e)}")
        return None


def save_credentials_to_firestore(credentials, collection_name='credentials', document_name='google_fit'):
    """
    認証情報をFirestoreに保存
    
    Args:
        credentials: 保存する認証情報
        collection_name: Firestoreのコレクション名
        document_name: Firestoreのドキュメント名
        
    Returns:
        bool: 保存の成否
    """
    try:
        db = firestore.Client()
        doc_ref = db.collection(collection_name).document(document_name)
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
        print(f"認証情報をFirestoreに保存しました (collection: {collection_name}, doc: {document_name})")
        return True
    except Exception as e:
        print(f"Firestore保存中にエラーが発生しました: {str(e)}")
        return False


