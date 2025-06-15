#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
特定の日付でGoogleFitとNotion連携をトリガーするスクリプト
使い方:
    python trigger_date.py 2023-11-01
    python trigger_date.py 2023-11-01 2023-11-02 2023-11-03  # 複数日指定も可能
"""

import sys
import os
import requests
import json
from datetime import datetime
import argparse
import traceback

# Cloud Function（またはローカルのprocess_data_for_date）を呼び出すか選択
USE_CLOUD_FUNCTION = True  # Trueの場合はCloud Functionを呼び出し、Falseの場合はローカル関数を呼び出す

def call_cloud_function(date_str):
    """
    Cloud Functionを呼び出して特定の日付のデータを処理する

    Args:
        date_str: YYYY-MM-DD形式の日付文字列
    """
    # Cloud FunctionのURLを環境変数から取得
    function_url = os.getenv("CLOUD_FUNCTION_URL")

    if not function_url:
        print("エラー: 環境変数「CLOUD_FUNCTION_URL」が設定されていません")
        print("例: export CLOUD_FUNCTION_URL=https://asia-northeast1-your-project.cloudfunctions.net/your-function-name")
        return False

    # リクエストヘッダーとボディの準備
    headers = {
        "Content-Type": "application/json"
    }

    # Cloud Functionsで処理する日付を指定
    body = {
        "message": date_str
    }

    try:
        # Cloud Functionを呼び出し
        print(f"日付 {date_str} のデータを処理中...")
        response = requests.post(function_url, headers=headers, json=body)

        if response.status_code == 200:
            result = response.json()
            print(f"成功: {date_str} のデータを処理しました")
            print(f"詳細: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"エラー: HTTPステータスコード {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False

    except Exception as e:
        print(f"エラー: Cloud Function呼び出し中に例外が発生しました: {str(e)}")
        return False

def process_date_locally(date_str):
    """
    ローカルでデータを処理する（Cloud Function未使用時）

    Args:
        date_str: YYYY-MM-DD形式の日付文字列
    """
    try:
        # main.pyをインポート（同じディレクトリにある前提）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.append(script_dir)

        try:
            from main import process_data_for_date
        except ImportError as e:
            print(f"エラー: main.pyモジュールのインポートに失敗しました: {str(e)}")
            print(f"現在のディレクトリ: {os.getcwd()}")
            print(f"スクリプトのディレクトリ: {script_dir}")
            print(f"Pythonパス: {sys.path}")
            return False

        # 日付文字列をdatetime.dateオブジェクトに変換
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # データ処理を実行
        print(f"日付 {date_str} のデータをローカルで処理中...")
        result = process_data_for_date(date_obj)

        print(f"成功: {date_str} のデータを処理しました")
        return True

    except Exception as e:
        print(f"エラー: ローカル処理中に例外が発生しました: {str(e)}")
        print("詳細なエラー情報:")
        traceback.print_exc()
        return False

def validate_date(date_str):
    """
    日付形式を検証する

    Args:
        date_str: 検証する日付文字列

    Returns:
        bool: 有効な日付形式ならTrue、そうでなければFalse
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def main():
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(description='特定の日付でGoogleFitとNotion連携をトリガーします')
    parser.add_argument('dates', nargs='+', help='YYYY-MM-DD形式の日付（複数指定可能）')
    parser.add_argument('--local', action='store_true', help='ローカル処理を使用（Cloud Functionを使用しない）')
    args = parser.parse_args()

    # コマンドライン引数でローカル処理が指定された場合
    global USE_CLOUD_FUNCTION
    if args.local:
        USE_CLOUD_FUNCTION = False

    success_count = 0
    error_count = 0

    # 各日付を処理
    for date_str in args.dates:
        if not validate_date(date_str):
            print(f"エラー: '{date_str}' は有効な日付形式（YYYY-MM-DD）ではありません")
            error_count += 1
            continue

        if USE_CLOUD_FUNCTION:
            success = call_cloud_function(date_str)
        else:
            success = process_date_locally(date_str)

        if success:
            success_count += 1
        else:
            error_count += 1

    # 結果サマリーを表示
    print(f"\n処理結果: 成功 {success_count}件, エラー {error_count}件")

    # 終了コードを設定（エラーがあれば1、なければ0）
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
