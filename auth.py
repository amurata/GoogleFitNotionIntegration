import argparse
import os
import json
from google.cloud import firestore
from oauth2client.client import flow_from_clientsecrets

OAUTH_SCOPE = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.location.read",
    "https://www.googleapis.com/auth/fitness.nutrition.read",
    "https://www.googleapis.com/auth/fitness.oxygen_saturation.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
]

def oauth2():
    """取得した認証情報をFirestoreに格納し、GoogleFitAPIのアクセスに必要なトークンを発行する。
    """
    flow = flow_from_clientsecrets(
        # API有効化時に取得したOAuth用のJSONファイルを指定
        "./key.json",
        # スコープを指定
        scope=OAUTH_SCOPE,
        # ユーザーの認証後の、トークン受け取り方法を指定
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )

    authorize_url = flow.step1_get_authorize_url()
    print("下記URLをブラウザで起動してください。")
    print(authorize_url)

    code = input("Codeを入力してください: ").strip()
    credentials = flow.step2_exchange(code)

    # Firestoreに認証情報を格納
    db = firestore.Client()
    doc_ref = db.collection(u'credentials').document(u'google_fit')
    doc_ref.set(json.loads(credentials.to_json()))

oauth2()

