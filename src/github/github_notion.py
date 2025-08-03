#!/usr/bin/env python3
"""
GitHub活動データ（Issue、PR）をNotionの日記データベースに同期するスクリプト

環境変数:
    GITHUB_TOKEN: GitHub Personal Access Token（repo スコープ）
    NOTION_SECRET: Notion Integration トークン
    DATABASE_ID: Notion データベース ID
    GCP_PROJECT: Google Cloud プロジェクト ID（Firestore用）
"""

import os
import sys
import datetime
import json
import logging
import re
from typing import List, Dict, Optional, Tuple

import requests

# 親ディレクトリのモジュールをインポート可能にする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .envファイルから環境変数を手動で読み込む
def load_env_file():
    """
    .envファイルから環境変数を読み込む（python-dotenvの代替）
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

# 日本時間タイムゾーン
JST = datetime.timezone(datetime.timedelta(hours=9))

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GitHubNotionSync:
    """GitHub活動データをNotionに同期するクラス"""

    def __init__(self):
        """初期化処理"""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.notion_token = os.getenv('NOTION_SECRET')
        self.database_id = os.getenv('DATABASE_ID')
        self.gcp_project = os.getenv('GCP_PROJECT')

        if not all([self.github_token, self.notion_token, self.database_id]):
            logger.error("必要な環境変数が設定されていません: GITHUB_TOKEN, NOTION_SECRET, DATABASE_ID")
            sys.exit(1)

        # GitHubのAPIヘッダー
        self.github_headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }

        # NotionのAPIヘッダー
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def parse_date_range(self, arg: str) -> List[datetime.date]:
        """
        日付引数をパースして日付リストを返す

        Args:
            arg: "YYYYMMDD" または "YYYYMMDD-YYYYMMDD" 形式の文字列

        Returns:
            日付のリスト
        """
        try:
            if "-" in arg:
                start_str, end_str = arg.split("-", 1)
                start = datetime.datetime.strptime(start_str, "%Y%m%d").date()
                end = datetime.datetime.strptime(end_str, "%Y%m%d").date()
            else:
                start = datetime.datetime.strptime(arg, "%Y%m%d").date()
                end = start

            if end < start:
                raise ValueError("日付範囲の開始が終了より後です。")

            dates = []
            current = start
            while current <= end:
                dates.append(current)
                current += datetime.timedelta(days=1)

            return dates
        except Exception as e:
            logger.error(f"日付パースエラー: {e}")
            raise

    def get_owned_repos(self) -> List[Dict]:
        """
        自分がオーナーのリポジトリ一覧を取得（最新4個のみ）

        Returns:
            リポジトリ情報のリスト（更新日時順、最新4個）
        """
        try:
            resp = requests.get(
                "https://api.github.com/user/repos",
                headers=self.github_headers,
                params={
                    "per_page": 4,  # 4個に制限（実際の活発なリポジトリ数に合わせて最適化）
                    "page": 1,
                    "affiliation": "owner",
                    "sort": "updated",  # 更新日時順
                    "direction": "desc"  # 降順（最新が先）
                }
            )
            resp.raise_for_status()
            repos = resp.json()

            logger.info(f"取得したリポジトリ数: {len(repos)} (最新4個に制限、API効率化)")
            for repo in repos:
                logger.info(f"  - {repo['full_name']} (updated: {repo['updated_at']})")

            return repos

        except Exception as e:
            logger.error(f"リポジトリ取得エラー: {e}")
            raise

    def fetch_issues_for_date(self, date: datetime.date, repos: List[Dict]) -> List[Dict]:
        """
        指定日（JST）にクローズされたIssueを取得

        Args:
            date: 対象日付
            repos: リポジトリ一覧

        Returns:
            Issue情報のリスト
        """
        # JST時間範囲をUTCに変換
        start_jst = datetime.datetime.combine(date, datetime.time(0, 0), tzinfo=JST)
        end_jst = datetime.datetime.combine(date, datetime.time(23, 59, 59, 999999), tzinfo=JST)
        start_utc = start_jst.astimezone(datetime.timezone.utc)
        end_utc = end_jst.astimezone(datetime.timezone.utc)

        items = []

        for repo in repos:
            owner = repo["owner"]["login"]
            name = repo["name"]
            page = 1

            while True:
                try:
                    resp = requests.get(
                        f"https://api.github.com/repos/{owner}/{name}/issues",
                        headers=self.github_headers,
                        params={
                            "state": "closed",
                            "per_page": 100,
                            "page": page,
                            "since": start_utc.isoformat()
                        }
                    )
                    resp.raise_for_status()
                    batch = resp.json()

                    if not batch:
                        break

                    for issue in batch:
                        # PRではないことを確認
                        if "pull_request" in issue:
                            continue

                        closed_at = issue.get("closed_at")
                        if not closed_at:
                            continue

                        # closed_atをパースして時間範囲を確認
                        closed_dt = datetime.datetime.fromisoformat(closed_at.rstrip("Z")).replace(tzinfo=datetime.timezone.utc)

                        if start_utc <= closed_dt <= end_utc:
                            items.append({
                                "type": "issue",
                                "repo": f"{owner}/{name}",
                                "number": issue["number"],
                                "title": issue["title"],
                                "url": issue["html_url"]
                            })

                    page += 1

                except Exception as e:
                    logger.warning(f"Issue取得スキップ ({owner}/{name}): {e}")
                    # エラーでも処理を継続（プライベートリポジトリなど）
                    continue

        logger.info(f"{date} のIssue数: {len(items)}")
        return items

    def fetch_prs_for_date(self, date: datetime.date, repos: List[Dict]) -> List[Dict]:
        """
        指定日（JST）にマージされたPRを取得

        Args:
            date: 対象日付
            repos: リポジトリ一覧

        Returns:
            PR情報のリスト
        """
        # JST時間範囲をUTCに変換
        start_jst = datetime.datetime.combine(date, datetime.time(0, 0), tzinfo=JST)
        end_jst = datetime.datetime.combine(date, datetime.time(23, 59, 59, 999999), tzinfo=JST)
        start_utc = start_jst.astimezone(datetime.timezone.utc)
        end_utc = end_jst.astimezone(datetime.timezone.utc)

        results = []

        for repo in repos:
            owner = repo["owner"]["login"]
            name = repo["name"]

            # リポジトリのPRを直接取得（Search APIの代替）
            try:
                resp = requests.get(
                    f"https://api.github.com/repos/{owner}/{name}/pulls",
                    headers=self.github_headers,
                    params={
                        "state": "closed",
                        "per_page": 50,  # 各リポジトリ最大9550個
                        "sort": "updated",
                        "direction": "desc"
                    }
                )
                resp.raise_for_status()
                prs = resp.json()

                for pr in prs:
                    # マージされたPRのみ処理
                    if not pr.get("merged_at"):
                        continue

                    # merged_atをパースして時間範囲を確認
                    merged_at = pr["merged_at"]
                    merged_dt = datetime.datetime.fromisoformat(merged_at.rstrip("Z")).replace(tzinfo=datetime.timezone.utc)

                    if start_utc <= merged_dt <= end_utc:
                        results.append({
                            "type": "pr",
                            "repo": f"{owner}/{name}",
                            "number": pr["number"],
                            "title": pr["title"],
                            "url": pr["html_url"]
                        })
                        logger.info(f"  マッチしたPR: {owner}/{name}#{pr['number']} - {pr['title']}")

            except Exception as e:
                logger.warning(f"PR取得スキップ ({owner}/{name}): {e}")
                # エラーでも処理を継続（プライベートリポジトリなど）
                continue

        logger.info(f"{date} のPR数: {len(results)}")
        return results

    def fetch_direct_commits_for_date(self, date: datetime.date, repos: List[Dict], pr_commits: set) -> List[Dict]:
        """
        指定日（JST）のmainブランチへの直接コミットを取得（リポジトリごとに集計）

        Args:
            date: 対象日付
            repos: リポジトリ一覧
            pr_commits: PRに含まれるコミットSHA集合（重複除外用）

        Returns:
            リポジトリごとの集計情報リスト
        """
        # JST時間範囲をISO形式に変換
        start_jst = datetime.datetime.combine(date, datetime.time(0, 0), tzinfo=JST)
        end_jst = datetime.datetime.combine(date, datetime.time(23, 59, 59, 999999), tzinfo=JST)

        results = []

        for repo in repos:
            owner = repo["owner"]["login"]
            name = repo["name"]
            repo_key = f"{owner}/{name}"

            try:
                # mainブランチのコミットを取得
                resp = requests.get(
                    f"https://api.github.com/repos/{owner}/{name}/commits",
                    headers=self.github_headers,
                    params={
                        "sha": repo.get("default_branch", "main"),
                        "since": start_jst.isoformat(),
                        "until": end_jst.isoformat(),
                        "per_page": 100  # 各リポジトリ最大100コミット
                    }
                )
                resp.raise_for_status()
                commits = resp.json()

                # このリポジトリの直接コミットを集計
                total_additions = 0
                total_deletions = 0
                direct_commit_count = 0

                for commit in commits:
                    sha = commit["sha"]

                    # PRに含まれるコミットは除外
                    if sha in pr_commits:
                        continue

                    # マージコミットを除外（親が2つ以上）
                    if len(commit.get("parents", [])) > 1:
                        continue

                    # コミット詳細を取得して変更行数を確認
                    detail_resp = requests.get(
                        f"https://api.github.com/repos/{owner}/{name}/commits/{sha}",
                        headers=self.github_headers
                    )
                    detail_resp.raise_for_status()
                    detail = detail_resp.json()

                    stats = detail.get("stats", {})
                    total_additions += stats.get("additions", 0)
                    total_deletions += stats.get("deletions", 0)
                    direct_commit_count += 1

                # このリポジトリに直接コミットがあれば結果に追加
                if direct_commit_count > 0:
                    results.append({
                        "type": "commit",
                        "repo": repo_key,
                        "commit_count": direct_commit_count,
                        "additions": total_additions,
                        "deletions": total_deletions,
                        "url": f"https://github.com/{repo_key}/commits/{repo.get('default_branch', 'main')}"
                    })
                    logger.info(f"  {repo_key}: {direct_commit_count} commits, +{total_additions}-{total_deletions}")

            except Exception as e:
                logger.warning(f"コミット取得スキップ ({owner}/{name}): {e}")
                continue

        logger.info(f"{date} の直接コミットがあるリポジトリ数: {len(results)}")
        return results

    def get_pr_commit_shas(self, prs: List[Dict], repos: List[Dict]) -> set:
        """
        PRに含まれるコミットのSHAを収集

        Args:
            prs: PR情報リスト
            repos: リポジトリ一覧

        Returns:
            コミットSHAのセット
        """
        commit_shas = set()

        # リポジトリ情報を辞書に変換（検索効率化）
        repo_dict = {f"{r['owner']['login']}/{r['name']}": r for r in repos}

        for pr in prs:
            repo_key = pr["repo"]
            pr_number = pr["number"]

            if repo_key not in repo_dict:
                continue

            owner, name = repo_key.split("/")

            try:
                # PRのコミット一覧を取得
                resp = requests.get(
                    f"https://api.github.com/repos/{owner}/{name}/pulls/{pr_number}/commits",
                    headers=self.github_headers,
                    params={"per_page": 100}
                )
                resp.raise_for_status()
                commits = resp.json()

                # コミットSHAを収集
                for commit in commits:
                    commit_shas.add(commit["sha"])

            except Exception as e:
                logger.warning(f"PRコミット取得スキップ ({repo_key}#{pr_number}): {e}")
                continue

        logger.info(f"PR関連コミット数: {len(commit_shas)}")
        return commit_shas

    def build_markdown(self, items: List[Dict]) -> str:
        """
        GitHub活動データをMarkdown形式に整形

        Args:
            items: Issue/PR情報のリスト

        Returns:
            Markdown形式の文字列
        """
        if not items:
            return "- 該当なし"

        lines = []
        for item in items:
            if item["type"] == "issue":
                lines.append(f"- 🎫 Issue #{item['number']}: [{item['title']}]({item['url']})")
            elif item["type"] == "pr":
                lines.append(f"- 🔀 PR #{item['number']}: [{item['title']}]({item['url']})")
            else:  # commit
                lines.append(f"- 📝 変更行数:+{item['additions']}-{item['deletions']} ({item['commit_count']} commits) [{item['repo'].split('/')[1]}]({item['url']})")

        return "\n".join(lines)

    def build_notion_rich_text(self, items: List[Dict]) -> List[Dict]:
        """
        GitHub活動データをNotionのrich_text形式に変換

        Args:
            items: Issue/PR情報のリスト

        Returns:
            Notionのrich_text配列
        """
        if not items:
            return [{"type": "text", "text": {"content": "該当なし"}}]

        rich_text = []

        for i, item in enumerate(items):
            # リポジトリ名を抽出（"owner/repo" -> "repo"）
            repo_name = item["repo"].split("/")[1]

            # 全体のテキストを構築（リポジトリ名:Issue/PR #番号: タイトル）
            if item["type"] == "issue":
                full_text = f"🎫 {repo_name}:Issue #{item['number']}: {item['title']}"
            elif item["type"] == "pr":
                full_text = f"🔀 {repo_name}:PR #{item['number']}: {item['title']}"
            else:  # commit
                full_text = f"📝 {repo_name}:変更行数:+{item['additions']}-{item['deletions']} ({item['commit_count']} commits)"

            # 全体をリンク付きテキストとして追加
            rich_text.append({
                "type": "text",
                "text": {
                    "content": full_text,
                    "link": {"url": item["url"]}
                }
            })

            # 最後のアイテム以外は改行を追加
            if i < len(items) - 1:
                rich_text.append({
                    "type": "text",
                    "text": {"content": "\n"}
                })

        return rich_text

    def find_notion_page(self, date: datetime.date) -> Optional[Dict]:
        """
        指定日付のNotionページを検索

        Args:
            date: 対象日付

        Returns:
            ページ情報またはNone
        """
        formatted_date = date.strftime("%Y-%m-%d")

        payload = {
            "filter": {
                "property": "日付",
                "date": {"equals": formatted_date}
            },
            "page_size": 1
        }

        try:
            resp = requests.post(
                f"https://api.notion.com/v1/databases/{self.database_id}/query",
                headers=self.notion_headers,
                json=payload
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

            if not results:
                logger.warning(f"{formatted_date} に対応するNotionページが見つかりません")
                return None

            return results[0]

        except Exception as e:
            logger.error(f"Notionページ検索エラー: {e}")
            raise

    def update_notion_page(self, page_id: str, rich_text: List[Dict]) -> Dict:
        """
        NotionページのGithubプロパティを更新

        Args:
            page_id: ページID
            rich_text: Notionのrich_text配列

        Returns:
            更新結果
        """
        payload = {
            "properties": {
                "Github": {
                    "rich_text": rich_text
                }
            }
        }

        try:
            resp = requests.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=self.notion_headers,
                json=payload
            )
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            logger.error(f"Notionページ更新エラー: {e}")
            raise

    def sync_date(self, date: datetime.date) -> bool:
        """
        指定日付のGitHub活動をNotionに同期

        Args:
            date: 対象日付

        Returns:
            成功時True、失敗時False
        """
        try:
            logger.info(f"処理開始: {date}")

            # リポジトリ一覧を1回だけ取得（API効率化）
            repos = self.get_owned_repos()

            # GitHub活動データを取得
            issues = self.fetch_issues_for_date(date, repos)
            prs = self.fetch_prs_for_date(date, repos)

            # PRに含まれるコミットSHAを収集（重複除外用）
            pr_commits = self.get_pr_commit_shas(prs, repos)

            # 直接コミットを取得
            direct_commits = self.fetch_direct_commits_for_date(date, repos, pr_commits)

            # 全アイテムを統合
            all_items = issues + prs + direct_commits

            # ログ用のMarkdown形式に整形
            markdown = self.build_markdown(all_items)
            logger.info(f"生成されたMarkdown:\n{markdown}")

            # Notion用のrich_text形式に変換
            rich_text = self.build_notion_rich_text(all_items)
            logger.info(f"Notionリッチテキスト要素数: {len(rich_text)}")

            # Notionページを検索
            page = self.find_notion_page(date)
            if not page:
                logger.warning(f"{date} のNotionページが見つからないためスキップします")
                return False

            # Notionページを更新（リッチテキスト形式で）
            page_id = page["id"]
            self.update_notion_page(page_id, rich_text)
            logger.info(f"✅ {date} の同期が完了しました（リンク付きフォーマットで更新）")

            return True

        except Exception as e:
            logger.error(f"❌ {date} の処理中にエラーが発生しました: {e}")
            return False

    def run(self, date_arg: str):
        """
        メイン実行処理

        Args:
            date_arg: 日付引数（"YYYYMMDD" または "YYYYMMDD-YYYYMMDD"）
        """
        try:
            dates = self.parse_date_range(date_arg)
            success_count = 0

            for date in dates:
                if self.sync_date(date):
                    success_count += 1

            logger.info(f"処理完了: {success_count}/{len(dates)} 件成功")

            if success_count < len(dates):
                sys.exit(1)

        except Exception as e:
            logger.error(f"実行エラー: {e}")
            sys.exit(1)


def main():
    """メイン関数"""
    if len(sys.argv) != 2:
        print("使い方: python github_notion.py YYYYMMDD または YYYYMMDD-YYYYMMDD")
        print("例: python github_notion.py 20250731")
        print("例: python github_notion.py 20250701-20250731")
        sys.exit(1)

    date_arg = sys.argv[1]
    sync = GitHubNotionSync()
    sync.run(date_arg)


if __name__ == "__main__":
    main()
