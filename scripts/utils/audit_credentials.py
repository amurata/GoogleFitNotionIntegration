#!/usr/bin/env python3
import os
import sys
import json
import datetime
from google.cloud import firestore

# プロジェクトルートへのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def audit_credentials():
    """
    Firestoreに保存された認証情報を監査し、セキュリティリスクがないか確認します。
    
    以下をチェックします：
    1. Firestoreドキュメントの存在確認
    2. トークンの最終更新日時
    3. リフレッシュトークンの存在
    4. 必須フィールドの確認
    """
    print("Firestoreの認証情報を監査中...")
    
    try:
        # Firestoreクライアントを初期化
        db = firestore.Client()
        doc_ref = db.collection(u'credentials').document(u'google_fit')
        doc = doc_ref.get()
        
        # 1. ドキュメントの存在確認
        if not doc.exists:
            print("エラー: Firestoreに認証情報が見つかりません。")
            print("scripts/utils/auth.pyを実行して認証情報を作成してください。")
            return False
        
        cred_dict = doc.to_dict()
        
        # 2. 必須フィールドの確認
        required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes']
        missing_fields = [field for field in required_fields if field not in cred_dict]
        
        if missing_fields:
            print(f"警告: 認証情報に以下のフィールドが欠けています: {', '.join(missing_fields)}")
            return False
        
        # 3. 更新日時の確認
        if 'updated_at' in cred_dict and cred_dict['updated_at']:
            last_update = cred_dict['updated_at']
            # Firestoreのタイムスタンプをdatetimeに変換
            if hasattr(last_update, 'timestamp'):
                last_update = datetime.datetime.fromtimestamp(last_update.timestamp())
            
            # 現在の日時
            now = datetime.datetime.now()
            
            # 経過日数を計算
            days_since_update = (now - last_update).days
            
            # 90日以上経過していれば警告
            if days_since_update > 90:
                print(f"警告: 認証情報が最後に更新されてから{days_since_update}日経過しています")
                print("セキュリティのため、定期的に認証情報を更新することをお勧めします")
                print("更新するには: python scripts/utils/auth.py")
            else:
                print(f"OK: 認証情報は{days_since_update}日前に更新されています")
        else:
            print("警告: 更新日時の情報がありません")
        
        # 4. リフレッシュトークンの確認
        if cred_dict.get('refresh_token'):
            print("リフレッシュトークン: 存在します")
        else:
            print("警告: リフレッシュトークンが見つかりません")
            return False
        
        # 5. スコープの確認
        if cred_dict.get('scopes'):
            print(f"認証スコープ: {', '.join(cred_dict['scopes'])}")
        else:
            print("警告: 認証スコープの情報がありません")
        
        print("Firestore認証情報の監査が完了しました")
        return True
        
    except Exception as e:
        print(f"エラー: Firestore認証情報の監査中にエラーが発生しました: {str(e)}")
        return False

def main():
    """メイン実行関数"""
    success = audit_credentials()
    if success:
        print("監査完了: Firestore認証情報は有効です")
    else:
        print("監査完了: Firestore認証情報に問題があります")
        sys.exit(1)

if __name__ == "__main__":
    main() 
