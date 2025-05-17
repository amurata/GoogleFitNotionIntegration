#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
天気データを取得してNotionに保存するスクリプト
使い方:
    python update_weather.py           # 前々日（2日前）の天気データを取得しNotionに保存
    python update_weather.py 2023-11-01 # 指定日の天気データを取得しNotionに保存
    python update_weather.py --no-notion # Notionに保存せず、表示のみ
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from weather_notion import get_weather_data, update_notion_database

def save_weather_data(date_obj, update_notion=True):
    """
    指定された日付の天気データを取得し、Notionに保存する

    Args:
        date_obj: datetime.dateオブジェクト
        update_notion: Falseの場合、Notionに保存しない（デフォルトはTrue）

    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse
    """
    try:
        # 天気データを取得
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day

        print(f"日付 {year}年{month}月{day}日 の天気データを取得中...")
        weather_data = get_weather_data(year, month, day)

        # データを表示
        print("\n取得した天気データ:")
        for key, value in weather_data.items():
            print(f"  {key}: {value}")

        # Notionに保存
        if update_notion:
            print("\nNotionにデータを保存中...")
            update_notion_database(weather_data, weather_data["日付"])
            print("Notionへの保存が完了しました。")

        return True

    except Exception as e:
        print(f"エラー: 天気データの処理中に例外が発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(description='天気データを取得してNotionに保存します')
    parser.add_argument('date', nargs='?', help='YYYY-MM-DD形式の日付（省略時は2日前）')
    parser.add_argument('--no-notion', action='store_true', help='Notionに保存しない（表示のみ）')
    args = parser.parse_args()

    # 日付を処理
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    if args.date:
        try:
            date_obj = datetime.strptime(args.date, "%Y-%m-%d").date()

            # 前日の場合は警告
            if date_obj == yesterday:
                print(f"警告: 前日（{yesterday}）の天気データを指定しています。")
                print("気象庁のウェブサイトでは前日のデータがまだ確定していない可能性があります。")
                print("続行しますか？ [y/N]")
                response = input().strip().lower()
                if response != 'y':
                    print("処理を中止しました。")
                    return 0
        except ValueError:
            print(f"エラー: '{args.date}' は有効な日付形式（YYYY-MM-DD）ではありません")
            return 1
    else:
        # 日付が省略された場合は2日前（前々日）の日付を使用
        date_obj = day_before_yesterday
        print(f"日付が指定されていないため、2日前（{date_obj}）のデータを取得します")

    # 天気データを保存
    success = save_weather_data(date_obj, not args.no_notion)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
