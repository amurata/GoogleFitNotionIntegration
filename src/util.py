import os
import requests
from datetime import datetime

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
