#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
天気データを取得してNotionに保存するスクリプト
使い方:
    python update_weather.py                      # 前々日（2日前）の天気データを取得しNotionに保存
    python update_weather.py 2023-11-01           # 指定日の天気データを取得しNotionに保存
    python update_weather.py 2023-11-01 2023-11-05 # 指定期間の天気データを取得しNotionに保存
    python update_weather.py --no-notion          # Notionに保存せず、表示のみ
"""

import os
import sys
import argparse
import time
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

def process_date_range(start_date, end_date, update_notion=True, sleep_seconds=2):
    """
    指定された日付範囲の天気データを取得し、Notionに保存する

    Args:
        start_date: 開始日（datetime.dateオブジェクト）
        end_date: 終了日（datetime.dateオブジェクト）
        update_notion: Falseの場合、Notionに保存しない（デフォルトはTrue）
        sleep_seconds: リクエスト間の待機秒数（スクレイピングのマナー）

    Returns:
        bool: すべて成功した場合はTrue、一部でも失敗した場合はFalse
    """
    all_success = True
    current_date = start_date
    
    while current_date <= end_date:
        success = save_weather_data(current_date, update_notion)
        if not success:
            all_success = False
            print(f"警告: {current_date} のデータ処理に失敗しました")
        
        # 次の日付に進む前に待機（スクレイピングのマナー）
        if current_date < end_date:
            print(f"次のリクエストまで {sleep_seconds} 秒待機しています...")
            time.sleep(sleep_seconds)
        
        current_date += timedelta(days=1)
    
    return all_success

def main():
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(description='天気データを取得してNotionに保存します')
    parser.add_argument('start_date', nargs='?', help='開始日 YYYY-MM-DD形式（省略時は2日前）')
    parser.add_argument('end_date', nargs='?', help='終了日 YYYY-MM-DD形式（省略時は開始日と同じ）')
    parser.add_argument('--no-notion', action='store_true', help='Notionに保存しない（表示のみ）')
    parser.add_argument('--sleep', type=float, default=2.0, help='リクエスト間の待機秒数（デフォルト: 2.0秒）')
    parser.add_argument('-y', '--yes', action='store_true', help='すべての確認プロンプトを自動承認')
    args = parser.parse_args()

    # 日付を処理
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    start_date = None
    end_date = None

    # 開始日の処理
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            
            # 前日の場合は警告
            if start_date == yesterday:
                print(f"警告: 前日（{yesterday}）の天気データを指定しています。")
                print("気象庁のウェブサイトでは前日のデータがまだ確定していない可能性があります。")
                if not args.yes:
                    print("続行しますか？ [y/N]")
                    response = input().strip().lower()
                    if response != 'y':
                        print("処理を中止しました。")
                        return 0
                else:
                    print("--yes フラグが指定されているため、自動的に続行します。")
        except ValueError:
            print(f"エラー: '{args.start_date}' は有効な日付形式（YYYY-MM-DD）ではありません")
            return 1
    else:
        # 日付が省略された場合は2日前（前々日）の日付を使用
        start_date = day_before_yesterday
        print(f"開始日が指定されていないため、2日前（{start_date}）のデータを取得します")

    # 終了日の処理
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
            if end_date < start_date:
                print(f"エラー: 終了日（{end_date}）が開始日（{start_date}）より前になっています")
                return 1
        except ValueError:
            print(f"エラー: '{args.end_date}' は有効な日付形式（YYYY-MM-DD）ではありません")
            return 1
    else:
        # 終了日が省略された場合は開始日と同じにする
        end_date = start_date

    # 日付範囲を表示
    if start_date == end_date:
        print(f"日付 {start_date} のデータを処理します")
    else:
        print(f"日付範囲 {start_date} から {end_date} までのデータを処理します")
        if (end_date - start_date).days > 30:
            print(f"警告: 処理する日数が多いです（{(end_date - start_date).days + 1}日間）")
            if not args.yes:
                print("続行しますか？ [y/N]")
                response = input().strip().lower()
                if response != 'y':
                    print("処理を中止しました。")
                    return 0
            else:
                print("--yes フラグが指定されているため、自動的に続行します。")

    # 天気データを保存
    success = process_date_range(start_date, end_date, not args.no_notion, args.sleep)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
