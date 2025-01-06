import os
import requests

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

    data = {
        "filter": {
            "property": "日付",
            "date": {
                "equals": date
            }
        }
    }

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

    data = {
        "properties": properties
    }

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

    print(f"Request data: {properties}")
    response = requests.post(url, headers=headers, json=data)
    if not response.ok:
        print(f"Notion API error: {response.status_code} - {response.text}")
    response.raise_for_status()
    return response.json()
