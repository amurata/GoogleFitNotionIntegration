# Google Fit Notion Integration

GoogleFitNotionIntegrationは、Google Fitから取得した運動履歴を自動的にNotionデータベースに同期させるシステムです。
Cloud Scheduler, PubSub, そしてCloud Functionsを活用して、定期的にデータを収集・加工し、あなたの健康管理と運動の進捗をNotionで簡単に追跡できるようにします。
この統合により、運動習慣の可視化と分析が手間なく行えるようになり、健康管理の質を向上させることができます。
Google Fitの豊富な運動データを活用して、より豊かな健康管理ライフスタイルを実現しましょう。

## アーキテクチャ
![GoogleFitNotionIntegration Architecture](./docs/architecture.png)

## 取得可能なデータ

### アクティビティデータ
- 移動距離 (km)
- 歩数 (歩)
- 消費カロリー (kcal)
- 強めの運動時間 (分)

### バイタルデータ
- 平均心拍数 (bpm)
- 酸素飽和度 (%)
- 体重 (kg)

### 睡眠データ
- 睡眠時間 (分)

## プロジェクト構造
```
.
├── src/
│   ├── main.py          # メインの実行ファイル
│   ├── constants.py     # 定数定義（APIスコープ、データタイプ）
│   ├── util.py          # ユーティリティ関数
│   └── requirements.txt # 依存パッケージ
├── auth.py              # 認証設定スクリプト
├── deploy.sh            # デプロイスクリプト
└── setup.sh            # セットアップスクリプト
```

## セットアップ方法

### 1. 必要な認証情報の準備
1. Google Cloud Platformで新しいプロジェクトを作成
2. Google Fit APIを有効化
3. OAuth 2.0クライアントIDを作成し、認証情報をkey.jsonとして保存
4. Notionでインテグレーションを作成し、シークレットトークンを取得
5. Notionでデータベースを作成し、インテグレーションと共有

### 2. 認証の設定
```bash
python auth.py
```
ブラウザが開き、Google認証が要求されます。認証後、トークンがFirestoreに保存されます。

### 3. 環境変数の設定
```bash
export NOTION_SECRET=secret_xxxxxxxxxx
export DATABASE_ID=xxxxxxxxxxxx
export GCP_PROJECT=xxxxxxx
```

### 4. デプロイ
```bash
./setup.sh   # 初回セットアップ
./deploy.sh  # Cloud Functionsへのデプロイ
```

### 5. トリガーする
Pub/Subトピック "fit" にメッセージを送信してCloud Functionsをトリガーする
```bash
./trigger_fit.sh
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

## トラブルシューティング
エラーが発生した場合は、GCPコンソールのCloud Functionsログで詳細を確認できます。
主な確認ポイント：
1. 認証情報の有効期限
2. Notionデータベースの権限設定
3. APIの利用制限
