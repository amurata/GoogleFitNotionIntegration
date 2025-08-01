#!/bin/bash
# GitHub活動データを取得・Notionに同期するスクリプト

# このスクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SRC_DIR="${PROJECT_ROOT}/src"
GITHUB_DIR="${SRC_DIR}/github"

# .envファイルを読み込む
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    export $(cat "${PROJECT_ROOT}/.env" | grep -v '^#' | xargs)
fi

# 使い方を表示する関数
usage() {
    echo "使い方: $(basename $0) [日付引数]"
    echo ""
    echo "日付引数:"
    echo "  YYYYMMDD           - 単一日付の処理"
    echo "  YYYYMMDD-YYYYMMDD  - 日付範囲の処理"
    echo "  (省略時)           - 昨日の日付を処理"
    echo ""
    echo "例:"
    echo "  $(basename $0)                  # 昨日のGitHub活動を同期"
    echo "  $(basename $0) 20250731         # 2025年7月31日のGitHub活動を同期"
    echo "  $(basename $0) 20250701-20250731 # 2025年7月1日から31日までのGitHub活動を同期"
    exit 1
}

# 引数の解析
if [[ $# -gt 1 ]]; then
    echo "エラー: 引数が多すぎます"
    usage
fi

# 日付引数の設定
DATE_ARG=""
if [[ $# -eq 0 ]]; then
    # 引数なしの場合は昨日の日付を使用
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        DATE_ARG=$(date -v-1d +%Y%m%d)
    else
        # Linux
        DATE_ARG=$(date -d "yesterday" +%Y%m%d)
    fi
    echo "昨日（${DATE_ARG}）のGitHub活動を同期します"
elif [[ "$1" == "--help" || "$1" == "-h" ]]; then
    usage
else
    DATE_ARG="$1"
    # 日付形式の簡易検証
    if ! [[ "$DATE_ARG" =~ ^[0-9]{8}(-[0-9]{8})?$ ]]; then
        echo "エラー: 無効な日付形式です。YYYYMMDD または YYYYMMDD-YYYYMMDD の形式で指定してください。"
        usage
    fi
fi

# 必要な環境変数のチェック
if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "エラー: GITHUB_TOKEN が設定されていません"
    echo ".envファイルに GITHUB_TOKEN を設定してください"
    exit 1
fi

if [[ -z "$NOTION_SECRET" ]]; then
    echo "エラー: NOTION_SECRET が設定されていません"
    echo ".envファイルに NOTION_SECRET を設定してください"
    exit 1
fi

if [[ -z "$DATABASE_ID" ]]; then
    echo "エラー: DATABASE_ID が設定されていません"
    echo ".envファイルに DATABASE_ID を設定してください"
    exit 1
fi

# Pythonスクリプトの実行
echo "GitHub活動データの同期を開始します..."
echo "対象期間: $DATE_ARG"

# コマンドの構築と実行
COMMAND="cd \"${GITHUB_DIR}\" && source \"${PROJECT_ROOT}/venv/bin/activate\" && python github_notion.py ${DATE_ARG}"

echo "実行コマンド: $COMMAND"
eval "$COMMAND"

# 終了コードをそのまま返す
exit $?