import os
import time
import json
import datetime
import functions_framework
from util import create_notion_page, search_notion_page, update_notion_page, get_google_fit_data
from googleapiclient.discovery import build
from google.cloud import firestore
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from constants import OAUTH_SCOPE, DATA_TYPES, ACTIVITY_TYPES

@functions_framework.http
def handler(request):
    if request.path == '/trigger_today':
        return trigger_today()
    else:
        return process_yesterday_data()

def process_yesterday_data():
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

        yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
        fit_data = get_google_fit_data(credentials, yesterday)

        database_id = os.getenv("DATABASE_ID")
        formatted_date = yesterday.strftime("%Y/%m/%d")
        page_title = "Google Fit Data " + formatted_date

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

        existing_page = search_notion_page(database_id, formatted_date)

        if existing_page:
            print(f"Updating existing page for date: {formatted_date}")
            res = update_notion_page(existing_page["id"], properties)
        else:
            print(f"Creating new page for date: {formatted_date}")
            res = create_notion_page(database_id, page_title, properties)

        return {"status": "success", "message": "Yesterday's data successfully processed"}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

def trigger_today():
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

        today = datetime.datetime.now().date()
        fit_data = get_google_fit_data(credentials, today)

        database_id = os.getenv("DATABASE_ID")
        formatted_date = today.strftime("%Y/%m/%d")
        page_title = "Google Fit Data " + formatted_date

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

        existing_page = search_notion_page(database_id, formatted_date)

        if existing_page:
            print(f"Updating existing page for date: {formatted_date}")
            res = update_notion_page(existing_page["id"], properties)
        else:
            print(f"Creating new page for date: {formatted_date}")
            res = create_notion_page(database_id, page_title, properties)

        return {"status": "success", "message": "Today's data successfully processed"}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}, 500
