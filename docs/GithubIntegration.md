# GitHub → Notion 日記進捗同期システム設計ドキュメント

## 1. 目的

指定日付または日付範囲の日本時間（Asia/Tokyo）において、**自分がオーナー／管理する GitHub リポジトリ**の以下を取得し、Notion の日記エントリー（対象データベースの行）の `Github` テキストプロパティに**上書き**で反映することで、その日の進捗を自動記録する。

* 閉じられた Issue（🎫）
* マージされた PR（🔀）

出力例（Notion 日記内の `Github` プロパティに入る内容。日付見出しは不要）：

```
- 🎫 Issue #42: [バグ修正の件](https://github.com/owner/repo/issues/42)
- 🔀 PR #87: [機能追加をマージ済み](https://github.com/owner/repo/pull/87)
```

該当がなければ：

```
- 該当なし
```

## 2. 要件整理

### 2.1 機能要件

1. 自分がオーナーの GitHub リポジトリ（`affiliation=owner`）のみを対象とし、以下を取得する。

   * 日本時間（JST / Asia/Tokyo）で指定日付（00:00〜23:59:59）に閉じられた Issue（PR でないもの）。
   * 同じく指定日付にマージされた PR（merged\_at を厳密に確認）。
2. 取得した項目を Markdown リストに整形し、絵文字で区別する。

   * Issue: 🎫
   * PR: 🔀
3. 指定日付／範囲ごとに Notion データベース（ID: 環境変数 `NOTION_DB_ID` で指定）をクエリし、`日付` プロパティ（Date 型）と一致するページを見つけて、`Github` プロパティ（テキスト）を上書き更新する。
4. 日付指定は CLI 引数で単一（`YYYYMMDD`）または範囲（`YYYYMMDD-YYYYMMDD`）を受け取り、各日ごとに処理する。
5. 冪等性：同一日を再実行しても上書きされるだけで問題ない（重複防止は上書き方式で担保）。
6. 実行は CLI ベース（将来 Web API 化は拡張として保留）。
7. 定期実行は前日分を日本時間 24:30 頃に走らせる想定（例: 8/1 00:30 JST に 7/31 を処理）。
8. 通知は不要（成功時は何もしない。失敗時のログは呼び出し元で確認する／将来の拡張でメール通知追加可能）。

### 2.2 非機能要件

* 認証情報（トークン）を環境変数またはシークレットで管理し、コードに直書きしない。
* 日本時間基準での「その日」の判定を正確に行う（JST→UTCの変換を含む）。
* エラー時は例外を投げて失敗を明示し、呼び出し元（手動実行や CI）で再試行/ログ取得可能にする。
* フォーマットは人がそのまま読めてリンクも機能する Markdown 形式。

## 3. 実装コンポーネント

### 3.1 環境変数（必須）

* `GITHUB_TOKEN`: Personal Access Token。スコープは `repo`（自分がオーナーのプライベート・パブリック両方を読めるようになる）。
* `NOTION_TOKEN`: Notion Integration トークン。対象 DB にアクセス権を与えておく。
* `NOTION_DB_ID`: Notion データベース ID（32文字の英数字）

### 3.2 CLI スクリプト（Python）

* 入力: 1つの引数（例: `20250731` または `20250701-20250731`）

* 処理の流れ（日付ごとに）：

  1. 指定日の JST 範囲（00:00〜23:59:59）を UTC に変換。
  2. GitHub から自分がオーナーのリポジトリ一覧を取得（`/user/repos?affiliation=owner` をページネーション）。
  3. 各リポジトリについて：

     * 閉じた Issue（PR ではない）を取得し、`closed_at` が該当 UTC 範囲内のものを選別。
     * Search API で `is:pr is:merged merged:YYYY-MM-DD` を使い PR を列挙し、詳細を取りに行って `merged_at` を該当 UTC 範囲内のものだけ採用。
  4. 取得した Issue/PR を絵文字付き Markdown リストに整形。
  5. Notion DB をクエリして `日付` がその日と等しいページを取得。
  6. そのページの `Github` プロパティを上書きし、整形済みテキストをセット。

* フォーマット例（該当があるとき）：

  ```
  - 🎫 Issue #123: [タイトル](https://github.com/owner/repo/issues/123)
  - 🔀 PR #456: [機能名](https://github.com/owner/repo/pull/456)
  ```

  該当がないとき：

  ```
  - 該当なし
  ```

### 3.3 GitHub Actions（将来の定期実行への拡張／テンプレート）

予定：前日分を JST 24:30（= 翌日 15:30 UTC）に走らせる。
サンプル workflow（リポジトリ内に `sync.py` を置く前提）：

```yaml
name: Daily GitHub→Notion Sync

on:
  schedule:
    - cron: '30 15 * * *'  # 毎日 15:30 UTC = 前日 JST 24:30 頃

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: チェックアウト
        uses: actions/checkout@v4

      - name: Python セットアップ
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: 依存インストール
        run: pip install requests python-dateutil

      - name: 前日分を実行
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # repo スコープの PAT
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DB_ID: '16fde731d2cf8115b5b9dda21c6e57cc'
        run: |
          # 日本時間で前日を YYYYMMDD 形式に (例: date コマンドを使う環境なら)
          python sync.py $(date -d '9 hours ago -1 day' +'%Y%m%d')
```

> ※現時点では CLI 実行が主目的なのでこの Actions はオプション。必要になったら Secrets を GitHub 上で設定して有効化する。

## 4. 具体的な Python 実装例（sync.py）

```python
import os
import sys
import datetime
import requests

# タイムゾーン：日本時間
JST = datetime.timezone(datetime.timedelta(hours=9))

# 環境変数取得
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

if not (GITHUB_TOKEN and NOTION_TOKEN and NOTION_DB_ID):
    print("環境変数 GITHUB_TOKEN, NOTION_TOKEN, NOTION_DB_ID を設定してください。")
    sys.exit(1)

HEADERS_GH = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def parse_date_range(arg: str):
    # YYYYMMDD または YYYYMMDD-YYYYMMDD
    if "-" in arg:
        start_str, end_str = arg.split("-", 1)
        start = datetime.datetime.strptime(start_str, "%Y%m%d").date()
        end = datetime.datetime.strptime(end_str, "%Y%m%d").date()
    else:
        start = datetime.datetime.strptime(arg, "%Y%m%d").date()
        end = start
    if end < start:
        raise ValueError("日付範囲の開始が終了より後です。")
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += datetime.timedelta(days=1)
    return days


def get_owned_repos():
    # 自分がオーナーのリポジトリ一覧を取得
    repos = []
    page = 1
    while True:
        resp = requests.get(
            "https://api.github.com/user/repos",
            headers=HEADERS_GH,
            params={"per_page": 100, "page": page, "affiliation": "owner"},  # オーナーだけ
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def fetch_issues_for_date(date: datetime.date):
    # その日（JST）の closed issue（PR ではない）を集める
    start_jst = datetime.datetime.combine(date, datetime.time(0, 0), tzinfo=JST)
    end_jst = datetime.datetime.combine(date, datetime.time(23, 59, 59), tzinfo=JST)
    start_utc = start_jst.astimezone(datetime.timezone.utc)
    end_utc = end_jst.astimezone(datetime.timezone.utc)

    items = []
    for repo in get_owned_repos():
        owner = repo["owner"]["login"]
        name = repo["name"]
        page = 1
        while True:
            resp = requests.get(
                f"https://api.github.com/repos/{owner}/{name}/issues",
                headers=HEADERS_GH,
                params={"state": "closed", "per_page": 100, "page": page, "since": start_utc.isoformat()},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            for issue in batch:
                if "pull_request" in issue:
                    continue  # PR ではない
                closed_at = issue.get("closed_at")
                if not closed_at:
                    continue
                closed_dt = datetime.datetime.fromisoformat(closed_at.rstrip("Z")).replace(tzinfo=datetime.timezone.utc)
                if start_utc <= closed_dt <= end_utc:
                    items.append({
                        "type": "issue",
                        "repo": f"{owner}/{name}",
                        "number": issue["number"],
                        "title": issue["title"],
                        "url": issue["html_url"],
                    })
            page += 1
    return items


def fetch_prs_for_date(date: datetime.date):
    # その日（JST）に merged された PR を収集
    start_jst = datetime.datetime.combine(date, datetime.time(0, 0), tzinfo=JST)
    end_jst = datetime.datetime.combine(date, datetime.time(23, 59, 59), tzinfo=JST)
    start_utc = start_jst.astimezone(datetime.timezone.utc)
    end_utc = end_jst.astimezone(datetime.timezone.utc)

    results = []
    for repo in get_owned_repos():
        owner = repo["owner"]["login"]
        name = repo["name"]
        date_str = date.strftime("%Y-%m-%d")
        query = f"repo:{owner}/{name} is:pr is:merged merged:{date_str}"
        resp = requests.get(
            "https://api.github.com/search/issues",
            headers=HEADERS_GH,
            params={"q": query, "per_page": 100},
        )
        resp.raise_for_status()
        for pr in resp.json().get("items", []):
            # 詳細取得して merged_at を確認
            pr_meta_url = pr["pull_request"]["url"]
            detail = requests.get(pr_meta_url, headers=HEADERS_GH)
            detail.raise_for_status()
            pr_data = detail.json()
            merged_at = pr_data.get("merged_at")
            if not merged_at:
                continue
            merged_dt = datetime.datetime.fromisoformat(merged_at.rstrip("Z")).replace(tzinfo=datetime.timezone.utc)
            if start_utc <= merged_dt <= end_utc:
                results.append({
                    "type": "pr",
                    "repo": f"{owner}/{name}",
                    "number": pr_data["number"],
                    "title": pr_data["title"],
                    "url": pr_data["html_url"],
                })
    return results


def build_markdown(items: list):
    if not items:
        return "- 該当なし"
    lines = []
    for it in items:
        if it["type"] == "issue":
            lines.append(f"- 🎫 Issue #{it['number']}: [{it['title']}]({it['url']})")
        else:
            lines.append(f"- 🔀 PR #{it['number']}: [{it['title']}]({it['url']})")
    return "\n".join(lines)


def find_notion_page(date: datetime.date):
    # 日付プロパティが一致するページを検索
    formatted = date.strftime("%Y-%m-%d")
    payload = {
        "filter": {
            "property": "日付",
            "date": {"equals": formatted}
        },
        "page_size": 1,
    }
    resp = requests.post(f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query", headers=HEADERS_NOTION, json=payload)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None
    return results[0]


def update_notion(page_id: str, text: str):
    payload = {
        "properties": {
            "Github": {
                "rich_text": [
                    {"type": "text", "text": {"content": text}}
                ]
            }
        }
    }
    resp = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=HEADERS_NOTION, json=payload)
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) != 2:
        print("使い方: python sync.py 20250731 または 20250701-20250731")
        sys.exit(1)
    try:
        dates = parse_date_range(sys.argv[1])
    except Exception as e:
        print(f"日付パース失敗: {e}")
        sys.exit(1)

    for date in dates:
        try:
            issues = fetch_issues_for_date(date)
            prs = fetch_prs_for_date(date)
            all_items = issues + prs
            md = build_markdown(all_items)
            page = find_notion_page(date)
            if not page:
                print(f"[警告] {date} に対応する Notion ページが見つかりません。")
                continue
            page_id = page["id"]
            update_notion(page_id, md)
            print(f"[成功] {date} を更新しました。内容:\n{md}")
        except Exception as e:
            print(f"[エラー] {date} の処理に失敗しました: {e}")
            raise

if __name__ == "__main__":
    main()
```

## 5. 実行例（手動）

```bash
GITHUB_TOKEN=... NOTION_TOKEN=... NOTION_DB_ID=16fde731d2cf8115b5b9dda21c6e57cc python sync.py 20250801
```

これは日本時間 2025-08-01 日記の進捗を更新する。
（内部では 2025-08-01 JST の Issue/PR を取る）

## 6. 将来の拡張案

* GitHub Actions 化：前日分を自動実行して失敗時メール通知（現状は CLI だが、必要なら workflow を追加）
* 更新前後の差分保持（履歴保存）
* 再実行履歴ログを外部にストア（監査用ファイル or S3 等）
* Web API 化：`?range=YYYYMMDD-YYYYMMDD` で HTTP 叩けるエンドポイントにする
* 通知追加：失敗時にメール／Slack／Teams でアラート

## 7. 注意点

* GitHub API レート制限：自分のオーナーリポジトリのみを絞っているので通常は問題ないが、多数のリポジトリを持っている場合は間隔を空けるかキャッシュを検討。
* Notion の `日付` プロパティがカスタムフォーマット（表示形式）と内部比較用の ISO 日付が一致するように確認。
* `Github` プロパティを上書きするため、過去内容を残したい場合は事前に複製／バックアップするか、履歴保存ロジックを追加する。
