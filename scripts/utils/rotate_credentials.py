#!/usr/bin/env python3
import os
import sys
import json
import datetime
from google.cloud import firestore
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# プロジェクトルートへのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.constants import OAUTH_SCOPE

def rotate_credentials():
    """
    Firestoreに保存された認証情報をローテーション（更新）します。
    
    手順：
    1. 現在のFirestore認証情報を確認
    2. 新しい認証フローを実行
    3. 新しい認証情報をFirestoreに保存
    4. 古い認証情報をバックアップ
    """
    print("認証情報のローテーションを開始します...")
    
    try:
        # Firestoreクライアントを初期化
        db = firestore.Client()
        doc_ref = db.collection(u'credentials').document(u'google_fit')
        
        # 1. 現在の認証情報を確認・バックアップ
        doc = doc_ref.get()
        if doc.exists:
            old_cred_dict = doc.to_dict()
            print("現在の認証情報を確認しました")
            
            # バックアップを作成
            backup_ref = db.collection(u'credentials_backup').document(f'google_fit_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}')
            backup_ref.set(old_cred_dict)
            print("古い認証情報をバックアップしました")
        else:
            print("現在の認証情報が見つかりません。新規作成します。")
        
        # 2. 新しい認証フローを実行
        print("新しい認証フローを開始します...")
        
        # OAuth 2.0クライアント設定ファイル
        client_secret_file = 'client_secret.json'
        
        if not os.path.exists(client_secret_file):
            print(f"エラー: {client_secret_file} が見つかりません。")
            print("Google Cloud Consoleから OAuth 2.0 クライアントIDの認証情報をダウンロードし、")
            print(f"'{client_secret_file}' として保存してください。")
            return False
        
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_file,
            scopes=OAUTH_SCOPE
        )
        
        credentials = flow.run_local_server(port=0)
        print("新しい認証が完了しました")
        
        # 3. 新しい認証情報をFirestoreに保存
        new_cred_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'rotated_at': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.set(new_cred_dict)
        print("新しい認証情報をFirestoreに保存しました")
        
        # 4. 認証情報をテスト
        print("新しい認証情報をテスト中...")
        if test_credentials(credentials):
            print("認証情報のテストが成功しました")
            print("認証情報のローテーションが完了しました")
            return True
        else:
            print("警告: 認証情報のテストに失敗しました")
            return False
            
    except Exception as e:
        print(f"エラー: 認証情報のローテーション中にエラーが発生しました: {str(e)}")
        return False

def test_credentials(credentials):
    """認証情報をテストして有効性を確認"""
    try:
        # トークンが期限切れの場合は更新
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        
        # 簡単なAPIリクエストでテスト
        import requests
        headers = {'Authorization': f'Bearer {credentials.token}'}
        response = requests.get(
            'https://www.googleapis.com/fitness/v1/users/me/dataSources',
            headers=headers
        )
        
        if response.status_code == 200:
            print("Google Fit APIへのアクセスが成功しました")
            return True
        else:
            print(f"Google Fit APIへのアクセスに失敗しました: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"認証情報のテスト中にエラーが発生しました: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    print("Google Fit認証情報のローテーションツール")
    print("注意: このツールは既存の認証情報を新しいものに置き換えます")
    
    # 確認プロンプト
    confirm = input("続行しますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("ローテーションをキャンセルしました")
        return
    
    success = rotate_credentials()
    if success:
        print("認証情報のローテーションが正常に完了しました")
    else:
        print("認証情報のローテーションに失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()
