import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import argparse
import statistics
import json
import os
from notion_client import Client

def load_env_file():
    """
    .envファイルから環境変数を読み込む（python-dotenvの代替）
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# .envファイルを読み込み
load_env_file()

def get_weather_emoji(condition):
    """天気状態に応じた絵文字を返す"""
    condition = condition.lower()
    if "快晴" in condition:
        return "☀️☀️"
    elif "晴" in condition:
        return "☀️"
    elif "薄曇" in condition:
        return "⛅️"
    elif "曇" in condition:
        return "☁️"
    elif "雨" in condition:
        return "☔"
    elif "雪" in condition:
        return "❄️"
    return ""

def get_weather_data(year=2025, month=5, day=15):
    """気象庁のウェブサイトから指定された日付の天気データを取得する"""
    url = f'https://www.data.jma.go.jp/stats/etrn/view/hourly_s1.php?prec_no=44&block_no=47662&year={year}&month={month:02d}&day={day:02d}&view=p1'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', class_='data2_s')
    if table is None:
        print(f"警告: {year}年{month}月{day}日 のデータテーブルが見つかりません（データ未公開の可能性）")
        return {
            "日付": f"{year}年{month}月{day}日",
            "天気": "", "気温": "", "湿度": "", "降水量": "", "気圧": "", "日照時間": "",
            "_is_complete": False,
        }
    rows = table.find_all('tr')

    # 結果格納用の変数を初期化
    weather_info = []
    total_sunshine = 0
    humidity_data = []
    sea_level_pressures = []
    temperature_data = []
    precipitation_data = []

    for i, row in enumerate(rows):
        if i > 2:  # ヘッダー行をスキップ
            cells = row.find_all('td')
            if len(cells) >= 15:
                hour = int(cells[0].text.strip())

                # 海面気圧（インデックス2）
                sea_pressure = cells[2].text.strip()
                if sea_pressure != "--" and sea_pressure != "":
                    sea_level_pressures.append((hour, float(sea_pressure)))

                # 降水量（インデックス3）
                precipitation = cells[3].text.strip()
                if precipitation != "--" and precipitation != "":
                    try:
                        precipitation_data.append((hour, float(precipitation)))
                    except ValueError:
                        precipitation_data.append((hour, 0.0))

                # 気温（インデックス4）
                temperature = cells[4].text.strip()
                if temperature != "--" and temperature != "":
                    temperature_data.append((hour, float(temperature)))

                # 湿度（インデックス7）
                humidity = cells[7].text.strip()
                if humidity != "--" and humidity != "":
                    humidity_data.append((hour, int(humidity)))

                # 日照時間（インデックス10）
                sunshine = cells[10].text.strip()
                if sunshine != "--" and sunshine != "":
                    try:
                        total_sunshine += float(sunshine)
                    except ValueError:
                        # 数値に変換できない場合はスキップ
                        pass

                # 天気（インデックス14の画像のalt属性）
                weather_img = cells[14].find('img')
                if weather_img and weather_img.has_attr('alt'):
                    weather_condition = weather_img.get('alt')
                    emoji = get_weather_emoji(weather_condition)
                    weather_info.append(f"{hour}時: {weather_condition}{emoji}")

    # 気圧データを6時間スパンで処理（大気潮に合わせる）
    pressure_spans = []

    # 6時間ごとのスパンの気圧データを収集
    for i in range(1, 25, 6):
        span_pressures = [p[1] for p in sea_level_pressures if i <= p[0] < i+6]
        if span_pressures:
            avg_pressure = statistics.mean(span_pressures)
            min_pressure = min(span_pressures)
            max_pressure = max(span_pressures)
            pressure_spans.append((i, i+5, avg_pressure, min_pressure, max_pressure, span_pressures))

    # 気圧変化のマークを追加
    for i in range(len(pressure_spans)-1):
        current_span = pressure_spans[i]
        next_span = pressure_spans[i+1]

        change_mark = ""

        # 下降判定: 現在のスパンの最大値と次のスパンのすべての値を比較
        if any(current_span[4] - next_value >= 5 for next_value in next_span[5]):
            change_mark = "⤵️💣️"
        # 上昇判定: 現在のスパンの最小値と次のスパンのすべての値を比較
        elif any(next_value - current_span[3] >= 5 for next_value in next_span[5]):
            change_mark = "⤴️⚠️"

        # マークを追加（元のタプルの要素を保持し、マークを最後に追加）
        pressure_spans[i] = (*current_span[:5], change_mark)

    # 最後のスパンの変化マークは空
    if pressure_spans:
        pressure_spans[-1] = (*pressure_spans[-1][:5], "")

    # 気温データを処理
    morning_temps = [t[1] for t in temperature_data if 5 <= t[0] <= 11]
    daytime_temps = [t[1] for t in temperature_data if 12 <= t[0] <= 18]
    evening_temps = [t[1] for t in temperature_data if t[0] >= 19 or t[0] <= 4]

    all_temps = [t[1] for t in temperature_data]
    max_temp = max(all_temps) if all_temps else 0
    min_temp = min(all_temps) if all_temps else 0

    morning_avg = statistics.mean(morning_temps) if morning_temps else 0
    daytime_avg = statistics.mean(daytime_temps) if daytime_temps else 0
    evening_avg = statistics.mean(evening_temps) if evening_temps else 0

    # 湿度データを処理
    morning_humidity = [h[1] for h in humidity_data if 5 <= h[0] <= 11]
    daytime_humidity = [h[1] for h in humidity_data if 12 <= h[0] <= 18]
    evening_humidity = [h[1] for h in humidity_data if h[0] >= 19 or h[0] <= 4]

    all_humidity = [h[1] for h in humidity_data]
    max_humidity = max(all_humidity) if all_humidity else 0
    min_humidity = min(all_humidity) if all_humidity else 0

    morning_hum_avg = statistics.mean(morning_humidity) if morning_humidity else 0
    daytime_hum_avg = statistics.mean(daytime_humidity) if daytime_humidity else 0
    evening_hum_avg = statistics.mean(evening_humidity) if evening_humidity else 0

    # 降水量データを処理
    morning_precip = sum([p[1] for p in precipitation_data if 5 <= p[0] <= 11])
    daytime_precip = sum([p[1] for p in precipitation_data if 12 <= p[0] <= 18])
    evening_precip = sum([p[1] for p in precipitation_data if p[0] >= 19 or p[0] <= 4])

    # 気圧情報を文字列化（6時間スパン版）
    pressure_str = ", ".join([f"{s[0]}-{s[1]}時:平均{s[2]:.1f}hPa{s[5]}" for s in pressure_spans])

    # 気温情報を文字列化
    temp_str = f"朝:平均{morning_avg:.1f}℃, 昼:平均{daytime_avg:.1f}℃, 夜:平均{evening_avg:.1f}℃（最高:{max_temp:.1f}℃, 最低:{min_temp:.1f}℃）"

    # 湿度情報を文字列化
    humidity_str = f"朝:平均{morning_hum_avg:.1f}%, 昼:平均{daytime_hum_avg:.1f}%, 夜:平均{evening_hum_avg:.1f}%（最高:{max_humidity}%, 最低:{min_humidity}%）"

    # 降水量情報を文字列化
    precip_str = f"朝:{morning_precip:.1f}mm, 昼:{daytime_precip:.1f}mm, 夜:{evening_precip:.1f}mm"

    # 天気情報を文字列化
    weather_str = ", ".join(weather_info)

    result = {
        "日付": f"{year}年{month}月{day}日",
        "天気": weather_str,
        "気温": temp_str,
        "湿度": humidity_str,
        "降水量": precip_str,
        "気圧": pressure_str,
        "日照時間": f"{total_sunshine:.1f}時間"
    }

    # データの完全性を示すフラグを追加
    # 天気情報（imgのalt属性）が空の場合はデータ未公開と判断
    result["_is_complete"] = len(weather_info) > 0

    return result

def update_notion_database(weather_data, date_str):
    """Notionデータベースに天気データを追加/更新する"""
    try:
        # Notion APIトークンを取得
        notion_token = os.environ.get("NOTION_SECRET")
        database_id = os.environ.get("DATABASE_ID")

        if not notion_token or not database_id:
            print("エラー: 環境変数 NOTION_SECRET または DATABASE_ID が設定されていません。")
            return False

        # Notion クライアントを初期化
        notion = Client(auth=notion_token)

        # 日付をISO形式に変換
        date_obj = datetime.strptime(date_str, "%Y年%m月%d日")
        iso_date = date_obj.strftime("%Y-%m-%d")

        # データベースを検索して同じ日付のページがあるか確認
        query_result = notion.databases.query(
            database_id=database_id,
            filter={
                "property": "日付",
                "date": {
                    "equals": iso_date
                }
            }
        )

        # 複数のエントリーがある場合、「振り返り」チェックが入っていないエントリーを優先選択
        target_page = None
        if query_result["results"]:
            # 「振り返り」チェックが入っていないエントリーを探す
            for page in query_result["results"]:
                page_id = page["id"]
                
                # ページの詳細情報を取得（すべてのプロパティを含む）
                page_details = notion.pages.retrieve(page_id=page_id)
                
                # 「振り返り」プロパティが存在し、チェックされているか確認
                if "振り返り" in page_details["properties"]:
                    is_reflection_checked = page_details["properties"]["振り返り"].get("checkbox", False)
                    if not is_reflection_checked:  # チェックが入っていない場合
                        target_page = page
                        break
                else:
                    # 「振り返り」プロパティが存在しない場合も更新対象とする
                    target_page = page
                    break
            
            # 「振り返り」チェックが入っていないエントリーが見つからない場合
            if target_page is None:
                print(f"注意: {date_str} のすべてのエントリーで「振り返り」チェックが入っているため更新をスキップします。")
                return True
        
        # ページのプロパティを作成
        properties = {
            "日付": {
                "date": {
                    "start": iso_date
                }
            },
            "天気": {
                "rich_text": [
                    {
                        "text": {
                            "content": weather_data["天気"]
                        }
                    }
                ]
            },
            "気温": {
                "rich_text": [
                    {
                        "text": {
                            "content": weather_data["気温"]
                        }
                    }
                ]
            },
            "湿度": {
                "rich_text": [
                    {
                        "text": {
                            "content": weather_data["湿度"]
                        }
                    }
                ]
            },
            "降水量": {
                "rich_text": [
                    {
                        "text": {
                            "content": weather_data["降水量"]
                        }
                    }
                ]
            },
            "気圧": {
                "rich_text": [
                    {
                        "text": {
                            "content": weather_data["気圧"]
                        }
                    }
                ]
            },
            "日照時間": {
                "rich_text": [
                    {
                        "text": {
                            "content": weather_data["日照時間"]
                        }
                    }
                ]
            }
        }

        # 既存のページがある場合は更新、なければ新規作成
        if target_page:
            page_id = target_page["id"]
            notion.pages.update(page_id=page_id, properties=properties)
            print(f"Notionページを更新しました: {date_str}")
        else:
            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            print(f"Notionに新しいページを作成しました: {date_str}")

        return True

    except Exception as e:
        print(f"Notionデータベース更新エラー: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='気象庁ウェブサイトから天気データを取得してNotionに保存します')
    parser.add_argument('--year', type=int, help='年 (例: 2025)')
    parser.add_argument('--month', type=int, help='月 (例: 5)')
    parser.add_argument('--day', type=int, help='日 (例: 15)')
    parser.add_argument('--notion', action='store_true', help='Notionにも保存する')

    args = parser.parse_args()

    now = datetime.now()
    year = args.year if args.year else now.year
    month = args.month if args.month else now.month
    day = args.day if args.day else now.day

    weather_data = get_weather_data(year, month, day)

    # データを表示
    print(f"{year}年{month}月{day}日の天気データ:")
    for key, value in weather_data.items():
        print(f"{key}: {value}")

    # Notionに保存
    if args.notion:
        update_notion_database(weather_data, weather_data["日付"])
        print("Notionへの保存が完了しました。")

    return 0

if __name__ == "__main__":
    main()
