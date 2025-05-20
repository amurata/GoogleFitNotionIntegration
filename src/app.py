#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
天気データ更新用のFastAPIアプリケーション
Cloud Run上で動作させるためのAPIサーバー
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 天気更新モジュールをインポート
from weather.update_weather import save_weather_data
from weather.weather_notion import get_weather_data, update_notion_database

app = FastAPI(
    title="天気データNotion更新API",
    description="気象庁のデータを取得してNotionデータベースを更新するAPIです",
    version="1.0.0"
)

class WeatherUpdateRequest(BaseModel):
    start_date: str = Field(..., description="開始日（YYYY-MM-DD形式）")
    end_date: Optional[str] = Field(None, description="終了日（YYYY-MM-DD形式、指定しない場合は開始日と同じ）")
    update_notion: bool = Field(True, description="Notionデータベースを更新するかどうか")
    sleep_seconds: float = Field(2.0, description="リクエスト間の待機時間（秒）")

class WeatherResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {
        "message": "天気データNotion更新APIサーバーが稼働中です",
        "endpoints": [
            "/api/v1/update-weather - 天気データを取得してNotionに保存",
            "/api/v1/health - ヘルスチェック"
        ]
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def process_date_range(start_date_str: str, end_date_str: Optional[str] = None, update_notion: bool = True, sleep_seconds: float = 2.0):
    """バックグラウンドで日付範囲の処理を行う"""
    try:
        # 日付文字列をパース
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else start_date
        
        if end_date < start_date:
            print(f"エラー: 終了日（{end_date}）が開始日（{start_date}）より前になっています")
            return
        
        # 日付範囲を処理
        current_date = start_date
        while current_date <= end_date:
            print(f"日付 {current_date} の天気データを処理中...")
            success = save_weather_data(current_date, update_notion)
            
            if not success:
                print(f"警告: {current_date} のデータ処理に失敗しました")
            
            # 次の日付に進む前に待機（スクレイピングのマナー）
            if current_date < end_date:
                print(f"次のリクエストまで {sleep_seconds} 秒待機しています...")
                time.sleep(sleep_seconds)
            
            current_date += timedelta(days=1)
        
        print("すべての日付の処理が完了しました")
    
    except Exception as e:
        print(f"バックグラウンド処理中にエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

@app.post("/api/v1/update-weather", response_model=WeatherResponse)
async def update_weather(request: WeatherUpdateRequest, background_tasks: BackgroundTasks):
    try:
        # リクエストの検証
        try:
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date() if request.end_date else start_date
        except ValueError:
            raise HTTPException(status_code=400, detail="無効な日付形式です。YYYY-MM-DD形式で指定してください。")
        
        if end_date < start_date:
            raise HTTPException(status_code=400, detail=f"終了日（{end_date}）が開始日（{start_date}）より前になっています")
        
        # 処理日数の確認
        days_count = (end_date - start_date).days + 1
        if days_count > 60:
            raise HTTPException(status_code=400, detail=f"一度に処理できる日数は最大60日です（リクエスト: {days_count}日）")
            
        # 環境変数のチェック
        if request.update_notion and (not os.environ.get("NOTION_SECRET") or not os.environ.get("DATABASE_ID")):
            raise HTTPException(status_code=500, detail="環境変数 NOTION_SECRET または DATABASE_ID が設定されていません")
        
        # バックグラウンドタスクとして処理を開始
        background_tasks.add_task(
            process_date_range,
            request.start_date,
            request.end_date,
            request.update_notion,
            request.sleep_seconds
        )
        
        return WeatherResponse(
            success=True,
            message=f"{start_date} から {end_date} までの天気データ処理をバックグラウンドで開始しました",
            details={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_count": days_count,
                "update_notion": request.update_notion
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内部エラーが発生しました: {str(e)}")

@app.get("/api/v1/update-weather", response_model=WeatherResponse)
async def update_weather_get(
    background_tasks: BackgroundTasks,
    start_date: str = Query(..., description="開始日（YYYY-MM-DD形式）"),
    end_date: Optional[str] = Query(None, description="終了日（YYYY-MM-DD形式、指定しない場合は開始日と同じ）"),
    update_notion: bool = Query(True, description="Notionデータベースを更新するかどうか"),
    sleep_seconds: float = Query(2.0, description="リクエスト間の待機時間（秒）")
):
    # POSTエンドポイントに処理を委譲
    request = WeatherUpdateRequest(
        start_date=start_date,
        end_date=end_date,
        update_notion=update_notion,
        sleep_seconds=sleep_seconds
    )
    return await update_weather(request, background_tasks)

if __name__ == "__main__":
    # ローカルでの開発用サーバー起動
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 
