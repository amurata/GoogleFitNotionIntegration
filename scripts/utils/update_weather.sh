#!/bin/bash
# 天気データを取得・更新するスクリプト

# このスクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SRC_DIR="${PROJECT_ROOT}/src"
WEATHER_DIR="${SRC_DIR}/weather"

# 使い方を表示する関数
usage() {
    echo "使い方: $(basename $0) [開始日] [終了日] [オプション]"
    echo ""
    echo "引数:"
    echo "  開始日     - YYYY-MM-DD形式の開始日（省略時は2日前）"
    echo "  終了日     - YYYY-MM-DD形式の終了日（省略時は開始日と同じ）"
    echo ""
    echo "オプション:"
    echo "  --no-notion - Notionに保存せず、表示のみ"
    echo "  --sleep N   - リクエスト間の待機秒数（デフォルト: 2.0秒）"
    echo "  --help      - このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $(basename $0)                      # 2日前の天気データを更新"
    echo "  $(basename $0) 2023-11-01          # 指定日の天気データを更新"
    echo "  $(basename $0) 2023-11-01 2023-11-05 # 指定期間の天気データを更新"
    echo "  $(basename $0) --no-notion          # Notionに保存せず、表示のみ"
    echo "  $(basename $0) 2023-11-01 --sleep 3 # スクレイピング間隔を3秒に設定"
    exit 1
}

# オプション・引数の解析
START_DATE=""
END_DATE=""
NO_NOTION=""
SLEEP_VALUE="2.0"

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            usage
            ;;
        --no-notion)
            NO_NOTION="--no-notion"
            shift
            ;;
        --sleep)
            if [[ $# -gt 1 ]]; then
                SLEEP_VALUE="$2"
                shift 2
            else
                echo "エラー: --sleep オプションには値が必要です"
                usage
            fi
            ;;
        *)
            # 日付と見なす
            if [[ -z "$START_DATE" ]]; then
                START_DATE="$1"
            elif [[ -z "$END_DATE" ]]; then
                END_DATE="$1"
            else
                echo "エラー: 余分な引数 '$1'"
                usage
            fi
            shift
            ;;
    esac
done

# コマンドの構築
COMMAND="cd \"${WEATHER_DIR}\" && python update_weather.py"

if [[ -n "$START_DATE" ]]; then
    COMMAND="${COMMAND} ${START_DATE}"
    
    if [[ -n "$END_DATE" ]]; then
        COMMAND="${COMMAND} ${END_DATE}"
    fi
fi

if [[ -n "$NO_NOTION" ]]; then
    COMMAND="${COMMAND} ${NO_NOTION}"
fi

COMMAND="${COMMAND} --sleep ${SLEEP_VALUE}"

# コマンドの実行
echo "実行コマンド: $COMMAND"
eval "$COMMAND" 
