# Google Fit Notion Integration

GoogleFitNotionIntegrationは、Google Fitから取得した運動履歴を自動的にNotionデータベースに同期させるシステムです。
Cloud Scheduler, PubSub, そしてCloud Functionsを活用して、定期的にデータを収集・加工し、あなたの健康管理と運動の進捗をNotionで簡単に追跡できるようにします。
この統合により、運動習慣の可視化と分析が手間なく行えるようになり、健康管理の質を向上させることができます。
Google Fitの豊富な運動データを活用して、より豊かな健康管理ライフスタイルを実現しましょう。

## アーキテクチャ
![GoogleFitNotionIntegration Architecture](./docs/architecture.png)

## 取得可能なデータ
以下のデータはGoogle Fitで収集されている場合に取得可能です。Apple HealthからGoogle Fitへの連携設定や、各種測定アプリの利用が前提となります。

### アクティビティデータ
- 移動距離 (km) - iPhone本体やApple Watchのワークアウトアプリなどで記録
- 歩数 (歩) - iPhone本体やApple Watchで自動記録
- 消費カロリー (kcal) - iPhone本体やApple Watchで自動記録
- 強めの運動時間 (分) - Apple Watchのワークアウトアプリなどで記録

### バイタルデータ
- 平均心拍数 (bpm) - Apple WatchとHeartWatchなどの専用アプリが必要
- 酸素飽和度 (%) - Apple WatchとHeartWatchなどの専用アプリが必要
- 体重 (kg) - スマート体重計と専用アプリが必要

### 睡眠データ
- 睡眠時間 (分) - 睡眠追跡アプリが必要

**注意**: データが取得できるかどうかは、使用しているデバイス、アプリ、およびApple HealthからGoogle Fitへの連携設定に依存します。すべてのデータがすべてのユーザーで利用できるとは限りません。

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

**重要**: プロパティ名は上記と完全に一致している必要があります。特に単位の表記（括弧と単位）まで同じにしてください。

### Notionテンプレート

日記やヘルスデータの記録には、Notionの習慣トラッカーテンプレートを活用すると便利です。以下のリンクから様々な習慣トラッカーテンプレートを入手できます：

[Notion公式：習慣トラッカーテンプレート集](https://www.notion.com/ja/templates/category/habit-tracking)

これらのテンプレートを使用して、Google Fitからのデータを記録するための日記ページを作成し、健康習慣の可視化と継続をサポートすることができます。

## プロジェクト構造
```
.
├── src/
│   ├── main.py          # メインの実行ファイル
│   ├── constants.py     # 定数定義（APIスコープ、データタイプ）
│   ├── util.py          # ユーティリティ関数
│   ├── webhook.py       # Notionウェブフック処理
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
for i in (seq 1 28); set d (printf "%02d" $i); ./trigger_fit.sh 2025-03-$d; sleep 2; end
```

#### プロジェクトルートから実行する方法
```bash
./scripts/utils/trigger_fit.sh  # 当日のデータを処理
./scripts/utils/trigger_fit.sh 2025-04-20  # 特定の日付のデータを処理
```

## 使用しているAPIスコープ
- fitness.activity.read: アクティビティデータの取得
- fitness.body.read: 体重データの取得
- fitness.heart_rate.read: 心拍数データの取得
- fitness.oxygen_saturation.read: 酸素飽和度の取得
- fitness.sleep.read: 睡眠データの取得

## 注意事項
- Google Fit APIは2024年後半にサービス終了予定です
- データの取得頻度はCloud Schedulerの設定に依存します
- 体重データは記録がある場合のみ保存されます
- すべてのデータは日次で集計されます
- Apple HealthからGoogle Fitへのデータ連携が適切に設定されていることを確認してください
- 一部のデータはデバイスやアプリに依存し、利用できない場合があります

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
