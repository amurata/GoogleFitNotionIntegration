# Google Fit Notion Integration

GoogleFitNotionIntegrationは、Google Fitから取得した運動履歴を自動的にNotionデータベースに同期させるシステムです。
Cloud Scheduler, PubSub, そしてCloud Functionsを活用して、定期的にデータを収集・加工し、あなたの健康管理と運動の進捗をNotionで簡単に追跡できるようにします。
この統合により、運動習慣の可視化と分析が手間なく行えるようになり、健康管理の質を向上させることができます。
Google Fitの豊富な運動データと天気データを活用して、より豊かな健康管理ライフスタイルを実現しましょう。

## アーキテクチャ
![GoogleFitNotionIntegration Architecture](./docs/architecture.png)

## 取得可能なデータ

### Google Fitデータ
以下のデータはGoogle Fitで収集されている場合に取得可能です。Apple HealthからGoogle Fitへの連携設定や、各種測定アプリの利用が前提となります。

#### アクティビティデータ
- 移動距離 (km) - iPhone本体やApple Watchのワークアウトアプリなどで記録
- 歩数 (歩) - iPhone本体やApple Watchで自動記録
- 消費カロリー (kcal) - iPhone本体やApple Watchで自動記録
- 強めの運動時間 (分) - Apple Watchのワークアウトアプリなどで記録

#### バイタルデータ
- 平均心拍数 (bpm) - Apple WatchとHeartWatchなどの専用アプリが必要
- 酸素飽和度 (%) - Apple WatchとHeartWatchなどの専用アプリが必要
- 体重 (kg) - スマート体重計と専用アプリが必要

#### 睡眠データ
- 睡眠時間 (分) - 睡眠追跡アプリが必要

**注意**: データが取得できるかどうかは、使用しているデバイス、アプリ、およびApple HealthからGoogle Fitへの連携設定に依存します。すべてのデータがすべてのユーザーで利用できるとは限りません。

### 天気データ
Google Maps Platform Weather APIを使用して、指定された位置情報の天気データを取得します。以下のデータが含まれます：

- 天気 - 朝（6-12時）、昼（12-18時）、夜（18-24時）の各時間帯の天気状況
- 気温 - 各時間帯の平均気温
- 湿度 - 各時間帯の平均湿度
- 降水量 - 各時間帯の総降水量
- 気圧 - 各時間帯の平均気圧
- 日照時間 - 日の出から日の入りまでの時間（分）

各時間帯のデータは「朝：晴れ、昼：曇り、夜：雨」のようにフォーマットされます。

## Notionデータベースの設定
このシステムを使用するには、Notionデータベースに特定のプロパティを設定する必要があります。以下のプロパティ名を正確に設定してください：

| プロパティ名 | タイプ | 説明 |
|------------|------|-----|
| 日付 | 日付 | データの日付（必須） |
| 移動距離 (km) | 数値 | その日の移動距離 |
| 歩数 (歩) | 数値 | その日の歩数 |
| 消費カロリー (kcal) | 数値 | その日の消費カロリー |
| 強めの運動 (分) | 数値 | 強度の高い運動の時間 |
| 平均心拍数 (bpm) | 数値 | その日の平均心拍数 |
| 酸素飽和度 (%) | 数値 | その日の平均酸素飽和度 |
| 体重 (kg) | 数値 | その日の体重 |
| 睡眠時間 (分) | 数値 | その日の睡眠時間 |
| 天気 | テキスト | 朝・昼・夜の天気状況 |
| 気温 | テキスト | 朝・昼・夜の平均気温 |
| 湿度 | テキスト | 朝・昼・夜の平均湿度 |
| 降水量 | テキスト | 朝・昼・夜の降水量 |
| 気圧 | テキスト | 朝・昼・夜の平均気圧 |
| 日照時間 | テキスト | 日の出から日の入りまでの時間（分） |
| 振り返り | チェックボックス | データ更新をスキップ |

**重要**: プロパティ名は上記と完全に一致している必要があります。特に単位の表記（括弧と単位）まで同じにしてください。

### Notionテンプレート

日記やヘルスデータの記録には、Notionの習慣トラッカーテンプレートを活用すると便利です。以下のリンクから様々な習慣トラッカーテンプレートを入手できます：

[Notion公式：習慣トラッカーテンプレート集](https://www.notion.com/ja/templates/category/habit-tracking)

これらのテンプレートを使用して、Google Fitからのデータを記録するための日記ページを作成し、健康習慣の可視化と継続をサポートすることができます。

## プロジェクト構造
```
.
├── src/
│   ├── main.py          # メインの実行ファイル（Google Fitデータ処理）
│   ├── constants.py     # 定数定義（APIスコープ、データタイプ）
│   ├── util.py          # ユーティリティ関数
│   ├── webhook.py       # Notionウェブフック処理
│   ├── trigger_date.py  # 特定日付のデータ処理トリガー
│   ├── weather/         # 天気データ処理モジュール
│   │   ├── __init__.py  # パッケージ初期化ファイル
│   │   ├── weather_notion.py # 天気データ取得・Notion更新機能
│   │   └── update_weather.py # 天気データ取得・保存スクリプト
│   └── requirements.txt # 依存パッケージ

├── scripts/
│   ├── utils/
│   │   ├── auth.py      # 認証設定スクリプト
│   │   ├── deploy.sh    # デプロイスクリプト
│   │   ├── setup.sh     # セットアップスクリプト
│   │   └── trigger_fit.sh # 手動トリガースクリプト
│   └── archive/         # 使用されていないスクリプト（参考用）
├── docs/
│   ├── architecture.png # アーキテクチャ図
│   ├── diagram.py       # 図生成スクリプト
│   └── icon/            # アイコン画像
├── .env.example         # 環境変数のサンプルファイル
└── LICENSE              # MITライセンス
```

## セットアップ方法

### 1. 必要な認証情報の準備
1. Google Cloud Platformで新しいプロジェクトを作成
2. Google Fit APIを有効化
3. OAuth 2.0クライアントIDを作成し、認証情報を`key.json`としてプロジェクトのルートディレクトリに保存
   - `key.json`はGCP認証情報ファイルで、Google APIへのアクセスに使用されます
   - 秘密情報を含むため、リポジトリには追加しないでください
4. Notionでインテグレーションを作成し、シークレットトークンを取得
5. Notionでデータベースを作成し、インテグレーションと共有
   - 上記の「Notionデータベースの設定」セクションに記載されたプロパティを正確に設定してください

### 2. 環境変数の設定
`.env.example`ファイルを`.env`にコピーし、必要な情報を入力します：
```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の情報を設定します：
```
GCP_PROJECT=your-project-id
NOTION_SECRET=your-notion-secret
DATABASE_ID=your-database-id
WEBHOOK_API_KEY=your-webhook-api-key
MAPS_API_KEY=your-maps-api-key
LOCATION_LAT=your-latitude
LOCATION_LNG=your-longitude
```

### 3. 認証の設定
```bash
cd scripts/utils
python auth.py
```
ブラウザが開き、Google認証が要求されます。認証後、トークンがFirestoreに保存されます。

### 4. デプロイ
```bash
cd scripts/utils
./setup.sh   # 初回セットアップ
./deploy.sh  # Cloud Functionsへのデプロイ
```

### 5. トリガーする
Pub/Subトピック "fit" にメッセージを送信してCloud Functionsをトリガーするには、以下のスクリプトを使用します：

#### ディレクトリに移動して実行する方法
```bash
cd scripts/utils
./trigger_fit.sh  # 当日のデータを処理
```

#### 特定の日付を指定する場合
```bash
cd scripts/utils
./trigger_fit.sh 2025-04-20  # 2025年4月20日のデータを処理
```

#### 連続した日付を指定する場合
```bash
cd scripts/utils
for i in $(seq 1 28); do d=$(printf "%02d" $i); ./trigger_fit.sh 2025-04-$d; sleep 2; done
```

```fish
cd scripts/utils
for i in (seq 1 28); set d (printf "%02d" $i); ./trigger_fit.sh 2025-04-$d; sleep 2; end
```

#### プロジェクトルートから実行する方法
```bash
./scripts/utils/trigger_fit.sh  # 当日のデータを処理
./scripts/utils/trigger_fit.sh 2025-04-20  # 特定の日付のデータを処理
```

### 6. 天気データの取得方法
以下のコマンドを使用して、気象庁のウェブサイトからデータを取得し、Notionデータベースに保存します。

#### 2日前（前々日）の天気データを取得
```bash
./scripts/utils/update_weather.sh
```

#### 特定の日付の天気データを取得
```bash
./scripts/utils/update_weather.sh 2025-04-20  # 2025年4月20日の天気データを取得
```

#### 天気データを表示のみ（Notionに保存しない）
```bash
cd src/weather
python update_weather.py --no-notion 2025-04-20
```

#### 連続した日付の天気データを取得
```bash
for i in {1..28}; do d=$(printf "%02d" $i); ./scripts/utils/update_weather.sh 2025-04-$d; sleep 2; done
```

```fish
for i in (seq 1 30); set d (printf "%02d" $i); ./scripts/utils/update_weather.sh 2025-04-$d; sleep 2; end
```

**注意**: 前日の天気データを取得しようとすると、気象庁のウェブサイトではまだデータが確定していない可能性があるため、警告が表示されます。

### 3. Weather APIの有効化
Google Cloud Platformで次の手順を実行します：
1. Google Maps PlatformのWeather APIを有効化
2. APIキーを作成し、制限を設定（サーバーキーとして使用するため、適切なIP制限を設定することをお勧めします）
3. 作成したAPIキーを`MAPS_API_KEY`環境変数に設定

## 使用しているAPIスコープ
- fitness.activity.read: アクティビティデータの取得
- fitness.body.read: 体重データの取得
- fitness.heart_rate.read: 心拍数データの取得
- fitness.oxygen_saturation.read: 酸素飽和度の取得
- fitness.sleep.read: 睡眠データの取得

### 使用している外部API
- Google Fit API: 運動・健康データの取得（2024年後半にサービス終了予定）
- Google Maps Platform Weather API: 天気データの取得
- Notion API: データの保存と管理

## 注意事項
- Google Fit APIは2024年後半にサービス終了予定です
- Weather APIはプレビュー段階のサービスです
- データの取得頻度はCloud Schedulerの設定に依存します
- 体重データは記録がある場合のみ保存されます
- すべてのデータは日次で集計されます
- Apple HealthからGoogle Fitへのデータ連携が適切に設定されていることを確認してください
- 一部のデータはデバイスやアプリに依存し、利用できない場合があります
- 天気データは指定された位置情報に基づいて取得されます

## トラブルシューティング
エラーが発生した場合は、GCPコンソールのCloud Functionsログで詳細を確認できます。
主な確認ポイント：
1. 認証情報の有効期限
2. Notionデータベースの権限設定
3. APIの利用制限
4. Notionデータベースのプロパティ名が正確に設定されているか
5. Google Fitに適切なデータが連携されているか

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](./LICENSE)ファイルを参照してください。

## 謝辞
このプロジェクトは[tatsuiman/GoogleFitNotionIntegration](https://github.com/tatsuiman/GoogleFitNotionIntegration)を参考に作成しました。

## 機能

- 気象庁のウェブサイトから天気データをスクレイピング
- 指定された日付または日付範囲のデータを取得
- Notionデータベースに天気データを保存
- 「振り返り」プロパティがチェックされているエントリーは更新をスキップ

## 更新履歴

### 最新の変更点

- **日付範囲指定機能**: 一度に複数日のデータを取得できるようになりました（2秒間隔で順次取得）
- **「振り返り」スキップ機能**: Notionの「振り返り」プロパティがチェックされているエントリーは更新しないようになりました
- **Cloud Run対応**: FastAPIでAPIを実装し、Cloud Runにデプロイ可能になりました

## 使い方

### コマンドライン

```bash
# 前々日（2日前）の天気データを取得
python src/weather/update_weather.py

# 指定日の天気データを取得
python src/weather/update_weather.py 2023-11-01

# 指定期間の天気データを取得（日付範囲指定）
python src/weather/update_weather.py 2023-11-01 2023-11-05

# Notionに保存せず、表示のみ
python src/weather/update_weather.py --no-notion

# スクレイピング間隔を指定（デフォルト: 2秒）
python src/weather/update_weather.py 2023-11-01 2023-11-05 --sleep 3.0
```

### APIサーバー

```bash
# ローカルでAPIサーバーを起動
python src/app.py
```

APIエンドポイント:

- `GET /api/v1/health` - ヘルスチェック
- `GET /api/v1/update-weather?start_date=2023-11-01&end_date=2023-11-05` - 日付範囲の天気データを取得（GET）
- `POST /api/v1/update-weather` - 日付範囲の天気データを取得（POST、JSONリクエスト）

POSTリクエストの例:

```json
{
  "start_date": "2023-11-01",
  "end_date": "2023-11-05",
  "update_notion": true,
  "sleep_seconds": 2.0
}
```

## 環境変数

必要な環境変数:

- `NOTION_SECRET` - NotionのAPIシークレットキー
- `DATABASE_ID` - Notionデータベースのプライマリキー

## Cloud Runへのデプロイ

```bash
# Dockerイメージのビルド
docker build -t weather-notion-api .

# ローカルでの実行（テスト用）
docker run -p 8080:8080 -e NOTION_SECRET=your_secret -e DATABASE_ID=your_db_id weather-notion-api

# Google Cloud Run へのデプロイ
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/weather-notion-api
gcloud run deploy weather-notion-api --image gcr.io/YOUR_PROJECT_ID/weather-notion-api --platform managed
```

### CloudRunのデプロイ時の注意点

1. 環境変数 `NOTION_SECRET` と `DATABASE_ID` をCloud Runの環境変数として設定
2. 必要に応じてタイムアウト設定を調整（長期間のデータ取得には長いタイムアウトが必要）
3. メモリ割り当てを適切に設定（最小256MB推奨）

## Notionデータベース設定

必要なプロパティ：
- `日付`: 日付型
- `天気`: リッチテキスト型
- `気温`: リッチテキスト型
- `湿度`: リッチテキスト型
- `降水量`: リッチテキスト型
- `気圧`: リッチテキスト型
- `日照時間`: リッチテキスト型
- `振り返り`: チェックボックス型（チェックが入っているとデータ更新をスキップ）
