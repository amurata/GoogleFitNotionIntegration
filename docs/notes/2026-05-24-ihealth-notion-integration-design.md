# iHealth × Notion 統合（新 private リポ）設計書

作成日: 2026-05-24 / ステータス: ドラフト（要確認事項あり）

## 0. この文書の位置づけ

新しい private リポジトリ（健康 + 天気 + GitHub を Notion へ日次集約）を
「GoogleFit リポとほぼ同じ実装」で立ち上げるための設計書。
クラウド実行環境の制約上、リポ作成・push・`arkatom/ihealth-relay` の参照は
このセッションからは行えないため、まず設計を固めてから実装ディレクトリを起こす。

## 1. 背景・現状

### 1.1 GoogleFitNotionIntegration（現リポ）
3系統のデータを Notion DB に日次同期している。

| 系統 | 実装 | 実行基盤 | 重さ |
|---|---|---|---|
| 健康（歩数/距離/カロリー/心拍/SpO2/体重/睡眠） | `src/main.py`, `src/util.py` | **GCP Cloud Functions + Firestore + PubSub + OAuth** | 重い・壊れやすい |
| 天気（気象庁スクレイピング） | `src/weather/update_weather.py` | **GitHub Actions cron**（JST15:00） | 軽い |
| GitHub活動（Issue/PR/直接コミット） | `src/github/github_notion.py` | **GitHub Actions cron**（JST24:30） | 軽い |

- Notion 書き込みパターン（共通・実証済み）:
  `日付` プロパティでページを query → 該当プロパティだけ PATCH。
  **ページは事前に存在している前提**（Notion 習慣トラッカー側で日次ページが作られる）。
- weather / github は `requests` 直叩きの自己完結スクリプト + Actions secrets
  （`NOTION_SECRET`, `DATABASE_ID`, `GH_PAT`）。GCP 不要。
- 健康のみ GCP/Firestore/OAuth に依存しており、運用コスト・障害点が突出している。

### 1.2 arkatom/ihealth-relay（既存・public）
- iHealth のデータを取得し、**直接 Notion に書き込む**リレー。
- 設定により SQLite 等への書き出しも可能。
- **macOS の launchd で定期実行**（= ユーザーの Mac 上でローカル稼働）。
- HTTP エンドポイントは持たない（バッチ型）。

### 1.3 重複・課題
- Notion の健康プロパティ（体重/心拍/SpO2/睡眠）を **Google Fit と iHealth が二重に**
  埋めうる構造。
- Google Fit 系は GCP 依存で重い。iHealth 系はローカル launchd 依存で可搬性が低い。

## 2. 目的（新 private リポ）

1. 健康データの取得元を **iHealth に一本化**し、Google Fit/GCP パイプラインを廃止。
2. 健康 + 天気 + GitHub を **GitHub Actions に統一**したクラウド日次同期に集約。
3. ローカル launchd 依存を解消（または役割を明確に分離）。
4. GoogleFit リポの「Actions + `requests` で Notion プロパティ更新」パターンを踏襲。

## 3. 最重要の決定ポイント（要確認）

**iHealth のデータをクラウド（GitHub Actions ランナー）から取得できるか？**

ihealth-relay が iHealth の**クラウド API**（REST/OAuth）からデータを引いているなら、
同じ認証情報を Actions secrets に置けばクラウドで完結できる（→ 案A）。
ローカルでしか取得できない（端末ペアリング/ローカルエクスポート依存）場合は、
健康取得はローカルに残す必要がある（→ 案B）。

### 案A: クラウド完全集約（推奨・iHealth がクラウド取得可能な場合）
- 新リポが Actions で iHealth API → Notion を実行。launchd 廃止。Google Fit 廃止。
- 単一リポ・単一実行基盤。重複も二重実行もなくなる。

### 案B: 健康はローカル維持 + 新リポは天気/GitHub（iHealth がローカル専用の場合）
- ihealth-relay（launchd）が健康 → Notion を継続。
- 新リポは天気 + GitHub を Actions で担当（Google Fit 健康分は廃止）。
- もしくは ihealth-relay が SQLite 等を**クラウド到達可能な場所**（例: 同 Notion DB、
  Google Sheets、クラウド DB）に書き、新リポがそれを読む案も可。

→ **要確認#1: ihealth-relay の iHealth 取得はクラウド API か、ローカル専用か。**

## 4. 推奨アーキテクチャ（案A 前提）

```
GitHub Actions (cron, JST)            Notion DB（既存・日次ページ）
┌─────────────────────────┐          ┌──────────────────────┐
│ daily-health-sync.yml    │ iHealth  │ 日付 でページ検索       │
│   └ health/ihealth_notion├─API────► │   → 体重/心拍/SpO2/    │
│ daily-weather-sync.yml   │          │     睡眠/歩数… を PATCH │
│   └ weather/...          │ 気象庁   │   → 天気… を PATCH      │
│ daily-github-sync.yml    │ GitHub   │   → Github を PATCH     │
│   └ github/github_notion │ API      └──────────────────────┘
└─────────────────────────┘
```

- 各系統は独立スクリプト + 独立ワークフロー（現リポの github/weather をそのまま移植）。
- 健康だけ新規 `health/ihealth_notion.py` を起こす（ihealth-relay のロジックを移植/再実装）。
- 共通の Notion クライアント util（`日付` 検索 + プロパティ PATCH）を 1 本に切り出すと
  3 系統で共有でき、重複コードが減る。

## 5. リポ構成（案）

```
ihealth-notion-integration/        # 新 private リポ
├── src/
│   ├── notion_client.py           # 共通: 日付ページ検索 + プロパティ PATCH
│   ├── health/
│   │   └── ihealth_notion.py      # iHealth 取得 → Notion（体重/心拍/SpO2/睡眠/歩数…）
│   ├── weather/                   # 現リポから移植
│   │   └── update_weather.py
│   └── github/                    # 現リポから移植
│       └── github_notion.py
├── .github/workflows/
│   ├── daily-health-sync.yml
│   ├── daily-weather-sync.yml
│   └── daily-github-sync.yml
├── requirements.txt               # requests, beautifulsoup4, (iHealth SDK 等)
├── .env.example
└── README.md
```

## 6. Notion プロパティ対応（既存スキーマ流用）

| プロパティ | 型 | 供給元（新） | 備考 |
|---|---|---|---|
| 日付 | Date | （ページキー） | 検索キー。既存ページ前提 |
| 体重 (kg) | Number | iHealth | 旧 Google Fit から移行 |
| 平均心拍数 (bpm) | Number | iHealth | 同上 |
| 酸素飽和度 (%) | Number | iHealth | 同上 |
| 睡眠時間 (分) | Number | iHealth | 同上 |
| 歩数 (歩) / 移動距離 (km) / 消費カロリー (kcal) / 強めの運動 (分) | Number | iHealth?（要確認#2） | iHealth で取れる項目を確認 |
| 天気/気温/湿度/降水量/気圧/日照時間 | Text | 気象庁 | 現リポ流用 |
| Github | Text | GitHub API | 現リポ流用 |
| 振り返り | Checkbox | （スキップ制御） | 現挙動を踏襲 |

→ **要確認#2: iHealth で実際に取得できる項目**（体重・心拍・SpO2・睡眠以外に
歩数/距離/カロリー等も取れるか。取れない項目の扱い）。

## 7. Secrets / 環境変数

- `NOTION_SECRET`, `DATABASE_ID`（現リポと共通）
- `GH_PAT`（GitHub 同期用）
- iHealth 認証情報（案A の場合。client id/secret/refresh token 等。**要確認#3**）

## 8. 移行・カットオーバー手順（案A）

1. 新 private リポ作成（ユーザーが実施）。本設計の `src/` を配置。
2. weather / github を現リポからコピーし、共通 `notion_client.py` にリファクタ。
3. `health/ihealth_notion.py` を実装（ihealth-relay のロジック移植）。
4. Actions secrets 設定 → `workflow_dispatch` で過去日を手動実行し検証。
5. 健康プロパティが iHealth 由来で正しく入ることを確認。
6. **Google Fit パイプライン停止**（GCP Cloud Functions / スケジューラ無効化）。
7. ihealth-relay の launchd を停止（案A）または役割整理（案B）。
8. 現リポ（GoogleFitNotionIntegration）は weather/github を新リポへ移したらアーカイブ検討。

## 9. 未確定事項（実装着手前に確定したい）

- **#1** iHealth 取得はクラウド API か／ローカル専用か（案A/B の分岐）。
- **#2** iHealth で取れる項目の正確な範囲。
- **#3** iHealth 認証方式（Actions secrets に置ける形か）。
- **#4** Google Fit パイプラインは完全廃止でよいか（段階移行の要否）。
- **#5** ihealth-relay は廃止か併存か（public→private への移設可否含む）。
- **#6** 新リポ名・配置（例: `ihealth-notion-integration`）。

## 10. このセッションでの進め方

- 上記 #1〜#3 が分かれば本設計を確定版に更新。
- 合意後、このブランチ上に `staging/ihealth-notion-integration/` を作って
  weather/github の移植 + 共通 notion_client + health スケルトンを実装し、
  ユーザーが pull → 新 private リポへ push する運用とする。
