# プロジェクト概要

## 目的
Google Fit Notion Integration - Google Fit、天気、GitHubのデータをNotionデータベースに自動同期するシステム

## 主な機能
1. **Google Fitデータの同期**: 歩数、移動距離、消費カロリー、心拍数、睡眠時間など
2. **天気データの取得**: Google Maps Platform Weather APIから朝・昼・夜の天気情報
3. **GitHub活動の記録**: クローズしたIssueとマージしたPRを日次で記録
4. **自動実行**: GitHub Actionsで毎日JST 24:30に前日分を自動同期

## テクノロジースタック
- **言語**: Python 3.9 (Cloud Functions runtime)
- **クラウド**: Google Cloud Platform (Cloud Functions/Run, Firestore, PubSub)
- **API**: Google Fit API, Notion API, Google Maps Weather API, GitHub API
- **認証**: OAuth 2.0 (Google), Firestore for credential storage
- **CI/CD**: GitHub Actions for daily sync

## 依存関係
- functions_framework (Cloud Functions)
- google-api-python-client, google-cloud-firestore
- notion-client
- beautifulsoup4 (天気データ処理)
- requests, python-dotenv