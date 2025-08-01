# AI開発アシスタント 行動指示

## 🚨 基本原則（必須）
すべてのタスク・コマンド・ツール実行前に必ず読み込み
- [基本ルール](./instructions/base.md) - 絶対厳守事項
- [深層思考](./instructions/deep-think.md)
- [memory](./instructions/memory.md)

## プロジェクト固有のアーキテクチャ・ルール・ドキュメント
- [プロジェクトドキュメント索引](./docs/README.md)

## 📋 場面別必須参照ファイル

### 実行環境
- [コマンド実行](./instructions/command.md) - シェル、実行ルール

### Git・コミット関連
- [Gitルール](./instructions/git.md) - GitHub操作、Issue、ブランチ戦略
- [コミット規約](./instructions/commit-rules.md) - コミットメッセージ形式
- [PRルール](./instructions/pr-rules.md) - プルリクエスト作成規約

### 開発プロセス
- [開発スタイル](./instructions/develop.md) - Issue駆動、TDD、スクラム
- [TDDルール](./instructions/KentBeck-tdd-rules.md) - テスト駆動開発
- [スクラム開発](./instructions/scrum.md) - スプリント管理

### 用語・表記統一
- [ドメイン用語集](./instructions/domain-terms.md) - 統一表記確認
- [用語更新ワークフロー](./instructions/domain-term-workflow.md) - 新用語提案

### 調査・検索
- [検索パターン集](./instructions/search-patterns.md) - Git検索コマンド
- [トラブルシューティング](./instructions/troubleshooting.md) - 問題解決手順

### 記録・管理
- [ノート・日誌](./instructions/note.md) - 作業記録の書き方

## 🔄 実行フロー
1. 基本ルール読み込み → 絶対厳守事項の確認
2. 場面に応じた専用ファイル読み込み → 具体的な実行ルール確認
  - 例：実装時 → プロジェクトドキュメント索引 を参照
3. 参照確認の明示 → `✅️:{filename.md}` で表示
4. 実行 → ルールに従って作業実行

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Google Fit to Notion Integration system that automatically syncs health/fitness data from Google Fit, weather data from Google Maps Platform Weather API, and GitHub activity data (closed issues and merged PRs) to a Notion database. The system runs on Google Cloud Platform using Cloud Functions/Run and Firestore for credential storage.

## Key Commands

### Development Setup
```bash
# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Authenticate with Google and save credentials to Firestore
python scripts/utils/auth.py
```

### Deployment
```bash
# Deploy to Google Cloud Functions
./scripts/utils/deploy.sh
```

### Manual Triggers
```bash
# Trigger Google Fit data sync for a specific date (or today if no date provided)
./scripts/utils/trigger_fit.sh [YYYY-MM-DD]

# Update weather data for a specific date (or 2 days ago if no date provided)
./scripts/utils/update_weather.sh [YYYY-MM-DD]

# Update GitHub activity data for a specific date (or yesterday if no date provided)
./scripts/utils/update_github.sh [YYYYMMDD]

# Batch process multiple days (supports --fit-only, --weather-only, --github-only options)
bash src/batch_process.sh 2025-04-01 2025-04-10

# Automated daily execution via GitHub Actions
# Runs daily at JST 24:30, processing previous day's GitHub activity
```

## Architecture

### Core Components
- **src/main.py**: Main Cloud Function handler for Google Fit data sync
- **src/util.py**: Utilities for Google Fit API and Notion API interactions
- **src/weather/weather_notion.py**: Weather data retrieval and Notion update
- **src/weather/update_weather.py**: Standalone weather data fetcher
- **src/github/github_notion.py**: GitHub activity data sync to Notion
- **scripts/utils/auth.py**: Google OAuth authentication and Firestore credential storage

### Data Flow
1. Cloud Scheduler triggers PubSub topic
2. Cloud Function fetches data from Google Fit API
3. Weather data is fetched from Google Maps Weather API
4. GitHub activity data is fetched from GitHub API
5. Data is formatted and saved to Notion database
6. Credentials are managed via Firestore

### External Dependencies
- Google Fit API for health data
- Google Maps Platform Weather API for weather data
- GitHub API for activity data (issues and pull requests)
- Notion API for database updates
- Google Cloud Firestore for credential storage
- Google Cloud Functions/Run for serverless execution

## Important Considerations

### Notion Database Properties
The Notion database must have these exact property names (including units):
- 日付 (Date type)
- 移動距離 (km) (Number)
- 歩数 (歩) (Number)
- 消費カロリー (kcal) (Number)
- 強めの運動 (分) (Number)
- 平均心拍数 (bpm) (Number)
- 酸素飽和度 (%) (Number)
- 体重 (kg) (Number)
- 睡眠時間 (分) (Number)
- 天気 (Text)
- 気温 (Text)
- 湿度 (Text)
- 降水量 (Text)
- 気圧 (Text)
- 日照時間 (Text)
- Github (Text)
- 振り返り (Checkbox)

### Environment Variables
Required in `.env`:
- `GCP_PROJECT`: Google Cloud project ID
- `NOTION_SECRET`: Notion API secret token
- `DATABASE_ID`: Notion database ID
- `MAPS_API_KEY`: Google Maps API key
- `LOCATION_LAT`: Latitude for weather data
- `LOCATION_LNG`: Longitude for weather data
- `GITHUB_TOKEN`: GitHub Personal Access Token (repo scope required for manual execution, auto-provided in GitHub Actions)

### Python Version
The project uses Python 3.9 as specified in the Dockerfile and Cloud Functions runtime.

### Security Notes
- Never commit `.env` file or credentials
- Use Firestore for secure credential storage
- Rotate credentials every 3 months using `scripts/utils/rotate_credentials.py`
- Audit credentials using `scripts/utils/audit_credentials.py`
