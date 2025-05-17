#!/bin/bash

# 使い方の表示
function show_usage {
  echo "使い方: $0 [オプション] 開始日 終了日"
  echo "オプション:"
  echo "  -h, --help        このヘルプを表示"
  echo "  -l, --local       ローカルモードで実行 (Cloud Functionを使用しない)"
  echo "  -p, --parallel N  並列処理数 (デフォルト: 3)"
  echo "例:"
  echo "  $0 2023-10-01 2023-10-31      # 10月の全日付をCloud Functionで処理"
  echo "  $0 -l 2023-01-01 2023-01-31   # 1月の全日付をローカルで処理"
  echo "  $0 -p 5 2023-11-01 2023-11-30 # 11月の全日付を5並列で処理"
  exit 1
}

# 日付を検証する関数
function validate_date {
  local date_str=$1
  # Python を使用して日付を検証
  python3 -c "from datetime import datetime; datetime.strptime('$date_str', '%Y-%m-%d')" 2>/dev/null
  return $?
}

# 日付を加算する関数
function add_days {
  local date_str=$1
  local days=$2

  # Python を使用して日付を加算
  python3 -c "from datetime import datetime, timedelta; print((datetime.strptime('$date_str', '%Y-%m-%d') + timedelta(days=$days)).strftime('%Y-%m-%d'))"
}

# 日付の比較関数
function compare_dates {
  local date1=$1
  local date2=$2

  # Python を使用して日付を比較
  # 戻り値: date1 <= date2 なら 0、そうでなければ 1
  python3 -c "from datetime import datetime; exit(0 if datetime.strptime('$date1', '%Y-%m-%d') <= datetime.strptime('$date2', '%Y-%m-%d') else 1)"
  return $?
}

# パラメータの初期値
LOCAL_MODE=""
PARALLEL=3

# 引数の解析
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_usage
      ;;
    -l|--local)
      LOCAL_MODE="--local"
      shift
      ;;
    -p|--parallel)
      PARALLEL="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

# 引数の検証
if [ $# -ne 2 ]; then
  echo "エラー: 開始日と終了日を指定してください"
  show_usage
fi

START_DATE="$1"
END_DATE="$2"

# 日付形式の検証
if ! validate_date "$START_DATE"; then
  echo "エラー: 無効な開始日 '$START_DATE' (YYYY-MM-DD形式で指定)"
  exit 1
fi

if ! validate_date "$END_DATE"; then
  echo "エラー: 無効な終了日 '$END_DATE' (YYYY-MM-DD形式で指定)"
  exit 1
fi

# 日付の順序を検証
if ! compare_dates "$START_DATE" "$END_DATE"; then
  echo "エラー: 開始日は終了日より前である必要があります"
  exit 1
fi

# 日付リストの生成
echo "処理する日付範囲: $START_DATE から $END_DATE"
echo "並列処理数: $PARALLEL"
if [ -n "$LOCAL_MODE" ]; then
  echo "実行モード: ローカル"
else
  echo "実行モード: Cloud Function"
fi

echo "処理を開始します..."
echo

# 日付のリストを生成
DATES=()
CURRENT_DATE="$START_DATE"
while compare_dates "$CURRENT_DATE" "$END_DATE"; do
  DATES+=("$CURRENT_DATE")
  CURRENT_DATE=$(add_days "$CURRENT_DATE" 1)
done

# 並列処理関数
function process_batch {
  local batch=("$@")
  echo "処理するバッチ: ${batch[*]}"
  python3 "$(dirname "$0")/trigger_date.py" $LOCAL_MODE "${batch[@]}"
  return $?
}

# 日付を処理
total=${#DATES[@]}
success=0
error=0

# GNU parallelが使えるか確認
if command -v parallel >/dev/null 2>&1; then
  # export関数をfishシェルでも動作するように修正
  echo "process_batch() { echo \"処理するバッチ: \$@\"; python3 \"$(dirname "$0")/trigger_date.py\" $LOCAL_MODE \"\$@\"; return \$?; }" > /tmp/process_batch_func.sh
  source /tmp/process_batch_func.sh
  export -f process_batch

  # GNU parallelを使用
  printf "%s\n" "${DATES[@]}" | parallel --progress -j "$PARALLEL" process_batch
  EXIT_CODE=$?

  # 一時ファイルを削除
  rm -f /tmp/process_batch_func.sh
else
  # 通常の逐次処理
  echo "注意: GNU parallelがインストールされていません。シーケンシャル処理に戻ります。"

  for date in "${DATES[@]}"; do
    if process_batch "$date"; then
      ((success++))
    else
      ((error++))
    fi
    echo "進捗: $((success + error))/$total 完了 (成功: $success, エラー: $error)"
  done

  EXIT_CODE=$([[ $error -eq 0 ]] && echo 0 || echo 1)
fi

echo "すべての処理が完了しました。終了コード: $EXIT_CODE"
exit $EXIT_CODE
