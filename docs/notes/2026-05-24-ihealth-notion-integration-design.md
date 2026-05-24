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

## 3. 決定済み: iHealth 取得はローカル専用

**確定（2026-05-24）: iHealth のデータ取得はローカル専用**（launchd / Mac 上でのみ可能）。
クラウド（GitHub Actions ランナー）から iHealth を直接叩くことはできない。

これにより、当初検討した「クラウド完全集約（健康も Actions 化）」案は**不採用**。
健康取得はローカル launchd に残し、天気・GitHub はクラウド Actions で動かす
**混在実行のモノレポ**を採用する（次節）。重い Google Fit/GCP パイプラインは廃止し、
健康データ源は iHealth に一本化して重複を解消する。

## 4. 採用アーキテクチャ（混在実行モノレポ）

健康はローカル launchd、天気・GitHub はクラウド Actions。実行基盤は分かれるが、
コードと設定は 1 つの private リポに集約し、共通の Notion 書き込み層を共有する。

```
[ローカル / Mac launchd]                Notion DB（既存・日次ページ）
┌─────────────────────────┐ iHealth   ┌──────────────────────┐
│ health/ihealth_notion.py ├─(local)─► │ 日付 でページ検索       │
└─────────────────────────┘           │   → 体重/心拍/SpO2/    │
                                       │     睡眠… を PATCH      │
[クラウド / GitHub Actions cron]        │                        │
┌─────────────────────────┐ 気象庁    │   → 天気… を PATCH      │
│ daily-weather-sync.yml   ├─────────► │                        │
│ daily-github-sync.yml    │ GitHub    │   → Github を PATCH     │
└─────────────────────────┘ API       └──────────────────────┘
        共通: src/notion_client.py（日付検索 + プロパティ PATCH）を全系統で共有
```

- weather / github: 現リポの実装をそのまま移植 + Actions ワークフロー移植。
- health: `health/ihealth_notion.py` を新規。**launchd で定期実行**（plist 雛形を同梱）。
  iHealth 取得部は ihealth-relay のロジックを移植（このセッションからは
  ihealth-relay を読めないため、実装はスケルトン + TODO とし、ローカルで肉付け）。
- 共通 `notion_client.py`（`日付` 検索 + プロパティ PATCH）を 1 本化し重複削減。
- Google Fit/GCP（Firestore/PubSub/OAuth）パイプラインは廃止。

### 別案（参考）: 2 リポ構成
新リポは天気・GitHub（Actions）のみとし、健康は ihealth-relay を据え置く形も可。
統合度は下がるが移行が最小。→ 要確認#5 で選択。

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

## 8. 移行・カットオーバー手順（モノレポ案）

1. 新 private リポ作成（ユーザーが実施）。本設計の `src/` を配置。
2. weather / github を現リポからコピーし、共通 `notion_client.py` にリファクタ。
3. `health/ihealth_notion.py` を実装（ihealth-relay の iHealth 取得ロジックを
   ローカルで移植）。launchd plist を設定。
4. weather/github: Actions secrets 設定 → `workflow_dispatch` で過去日を手動実行し検証。
   health: launchd でローカル実行し検証。
5. 健康プロパティが iHealth 由来で正しく入ることを確認。
6. **Google Fit パイプライン停止**（GCP Cloud Functions / スケジューラ無効化）。
7. 旧 ihealth-relay は新リポへ移植後に停止（モノレポ案）／2 リポ案なら据え置き。
8. 現リポ（GoogleFitNotionIntegration）は weather/github を新リポへ移したらアーカイブ検討。

## 9. 未確定事項（実装着手前に確定したい）

- ~~**#1** iHealth 取得はクラウド API か／ローカル専用か~~ → **確定: ローカル専用**。
- **#2** iHealth で取れる項目の正確な範囲（体重/心拍/SpO2/睡眠以外に歩数・距離・カロリーは？）。
- **#4** Google Fit パイプラインは完全廃止でよいか（段階移行の要否）。
- **#5** 構成の選択: モノレポ統合（health を private リポへ移植）か、2 リポ構成
  （ihealth-relay 据え置き + 新リポは天気/GitHub のみ）か。
- **#6** 新リポ名・配置（例: `ihealth-notion-integration`）。

## 10. このセッションでの進め方

- 上記 #1〜#3 が分かれば本設計を確定版に更新。
- 合意後、このブランチ上に `staging/ihealth-notion-integration/` を作って
  weather/github の移植 + 共通 notion_client + health スケルトンを実装し、
  ユーザーが pull → 新 private リポへ push する運用とする。
