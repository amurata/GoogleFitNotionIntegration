from google.cloud import firestore
from google_auth_oauthlib.flow import InstalledAppFlow
from constants import OAUTH_SCOPE

# 認証情報を取得するためには、以下のコマンドを実行する必要がある
# PYTHONPATH=src python auth.py

def oauth2():
    """PKCEを使用した安全な認証フローでGoogleFit APIのアクセストークンを取得"""
    flow = InstalledAppFlow.from_client_secrets_file(
        "./key.json",
        scopes=OAUTH_SCOPE,
        # PKCEはInstalledAppFlowで自動的に有効化される
    )

    credentials = flow.run_local_server(port=0)

    # 認証情報を安全に保存
    db = firestore.Client()
    doc_ref = db.collection(u'credentials').document(u'google_fit')

    encrypted_credentials = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP
    }

    doc_ref.set(encrypted_credentials)
    print("認証が完了し、認証情報が安全に保存されました。")

if __name__ == "__main__":
    oauth2()
