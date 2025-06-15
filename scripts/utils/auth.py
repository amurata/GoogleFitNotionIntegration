import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.cloud import firestore

# プロジェクトルートへのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.constants import OAUTH_SCOPE

def oauth2():
    """
    PKCEを使用した安全な認証フローでGoogleFit APIのアクセストークンを取得

    注意: この関数を実行するには、Google Cloud Consoleから
    OAuth 2.0クライアントIDの認証情報をダウンロードし、
    'client_secret.json'として保存する必要があります。
    """
    # OAuth 2.0クライアント設定ファイル
    client_secret_file = 'client_secret.json'

    if not os.path.exists(client_secret_file):
        print(f"エラー: {client_secret_file} が見つかりません。")
        print("Google Cloud Consoleから OAuth 2.0 クライアントIDの認証情報をダウンロードし、")
        print(f"'{client_secret_file}' として保存してください。")
        return None

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_file,
        scopes=OAUTH_SCOPE,
        # PKCEはInstalledAppFlowで自動的に有効化される
    )

    credentials = flow.run_local_server(port=0)
    print("認証が完了しました。")
    return credentials

def save_credentials_to_firestore(credentials):
    """
    現在の認証情報をFirestoreに保存します。
    """
    try:
        print("Firestoreに認証情報を保存中...")
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
        print("認証情報が正常にFirestoreに保存されました。")
        return True
    except Exception as e:
        print(f"Firestore保存中にエラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    print("Google Fit API認証フローを開始します...")
    credentials = oauth2()

    if credentials and credentials.valid:
        if save_credentials_to_firestore(credentials):
            print("認証情報の取得・保存が完了しました。")
        else:
            print("認証情報の保存に失敗しました。")
    else:
        print("認証情報の取得に失敗しました。")
