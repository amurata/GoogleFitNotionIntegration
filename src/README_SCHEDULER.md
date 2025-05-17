# Google Fit & Notion 連携スケジューラ

## 概要

このドキュメントでは、Google Fitデータと天気データをNotionデータベースに連携する自動実行の設定方法について説明します。

## 1. Cloud Schedulerで定期実行する方法

Cloud Schedulerを使用して、定期的（例: 毎日）にデータを更新するための設定手順です。

### 前提条件

- Google Cloudプロジェクトがセットアップされていること
- Cloud Functionsにwebhook_handler関数がデプロイされていること
- 必要な権限（Cloud Schedulerの設定権限）があること

### 設定手順

1. **Google Cloudコンソールにログイン**
   - [Google Cloudコンソール](https://console.cloud.google.com/)にアクセス

2. **Cloud Scheduler画面へ移動**
   - 左側のナビゲーションメニューから「Cloud Scheduler」を選択
   - または検索バーで「Cloud Scheduler」を検索

3. **新しいジョブの作成**
   - 「ジョブを作成」または「CREATE JOB」ボタンをクリック

4. **ジョブの詳細入力**
   - 名前: `daily-google-fit-notion-sync` （わかりやすい名前）
   - 説明: `毎日Google FitとNotionデータを同期` （任意）
   - 頻度: [Cron式](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)で指定
     - 例: 毎日朝6時に実行 → `0 6 * * *`
     - 例: 毎日21時に実行 → `0 21 * * *`
   - タイムゾーン: `Asia/Tokyo` を選択

5. **ターゲットの設定**
   - ターゲットタイプ: `HTTP` を選択
   - URL: デプロイしたCloud FunctionのURL（例: `https://us-central1-your-project-id.cloudfunctions.net/webhook_handler`）
   - HTTP メソッド: `POST` を選択
   - リクエストヘッダー:
     - 「ヘッダーを追加」をクリック
     - キー: `Content-Type` 値: `application/json`
     - キー: `X-API-Key` 値: `あなたのAPIキー`
   - 本文:
     ```json
     {"message": "trigger"}
     ```

6. **認証の設定（オプション）**
   - 必要に応じて認証方法を選択（なしやOAuthなど）

7. **「作成」ボタンをクリック**

8. **完了！**
   - これで設定した時間に毎日自動的にデータが同期されます

## 2. 特定の日付でデータを処理する方法

特定の日付や複数の日付を一括で処理したい場合に使用するスクリプトの使い方です。

### 単一の日付を処理する

```bash
# 環境変数の設定
export CLOUD_FUNCTION_URL="https://us-central1-your-project-id.cloudfunctions.net/webhook_handler"
export WEBHOOK_API_KEY="your-api-key"

# 特定の日付を処理
python src/trigger_date.py 2023-11-15
```

### 複数の日付を処理する

```bash
# 複数の日付を一度に処理
python src/trigger_date.py 2023-11-01 2023-11-02 2023-11-03
```

### ローカルで処理する場合（Cloud Function不使用）

```bash
# ローカルモードで処理
python src/trigger_date.py --local 2023-11-15
```

## 3. 日付範囲を一括処理する

```bash
# 10月分を一括処理
./src/batch_process.sh 2023-10-01 2023-10-31

# 並列処理数を増やして高速化
./src/batch_process.sh -p 5 2023-10-01 2023-10-31

# ローカルモードで処理
./src/batch_process.sh -l 2023-10-01 2023-10-31
```

## 4. トラブルシューティング

問題が発生した場合は、以下を確認してください:

1. **環境変数の設定**
   - `CLOUD_FUNCTION_URL`と`WEBHOOK_API_KEY`が正しく設定されているか
   - `echo $CLOUD_FUNCTION_URL`と`echo $WEBHOOK_API_KEY`で確認

2. **Cloud Function**
   - デプロイされたCloud Functionが正常に動作するか
   - ログを確認（Google Cloudコンソールから）

3. **API認証**
   - APIキーが正しいか
   - 必要な権限が付与されているか

4. **ネットワーク接続**
   - インターネット接続が正常か
   - VPNやファイアウォールの制限がないか

5. **エラーメッセージ**
   - エラーメッセージを確認し、具体的な問題を特定

## 5. 高度な使い方

### Cloud Schedulerの高度な設定

- 複数のスケジュールを設定する（例：毎日午前と午後）
- 失敗時の再試行ポリシーを設定する
- 一時的に無効化する（テスト中など）

### バッチ処理の最適化

- 並列処理数を調整して最適なパフォーマンスを見つける
- 大量のデータを処理する場合は、小さな日付範囲に分割する

## 6. セキュリティ上の注意

- API キーを公開リポジトリにコミットしない
- 環境変数を使用してシークレット情報を管理する
- 必要最小限の権限を付与する
