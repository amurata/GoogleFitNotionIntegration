FROM python:3.9-slim

WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 環境変数を設定
ENV PORT=8080

# Cloud Runはヘルスチェックを行うため、起動時にレスポンスを返せるようにGunicornを使用
CMD exec gunicorn --worker-class uvicorn.workers.UvicornWorker --workers 1 --threads 8 --timeout 0 --bind :$PORT src.app:app 
