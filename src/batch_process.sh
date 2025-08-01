#!/bin/bash

# プロジェクトルートディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 環境変数をロード
echo "環境変数を読み込み中..."
if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  source "$PROJECT_ROOT/.env"
  set +a
  echo "環境変数を読み込みました"
else
  echo "警告: .envファイルが見つかりません ($PROJECT_ROOT/.env)"
fi

# 使い方の表示
function show_usage {
  echo "使い方: $0 [オプション] 開始日 終了日"
  echo "オプション:"
  echo "  -h, --help        このヘルプを表示"
  echo "  -l, --local       ローカルモードで実行 (Cloud Functionを使用しない)"
  echo "  -p, --parallel N  並列処理数 (デフォルト: 3)"
  echo "  --fit-only        バイタルデータのみ更新（天候データ・GitHubは既存のまま保持）"
  echo "  --weather-only    天候データのみ更新（バイタルデータ・GitHubは既存のまま保持）"
  echo "  --github-only     GitHub活動データのみ更新（バイタル・天候データは既存のまま保持）"
  echo "例:"
  echo "  $0 2023-10-01 2023-10-31      # 10月の全日付でバイタル・天候データを更新"
  echo "  $0 -l 2023-01-01 2023-01-31   # 1月の全日付をローカルで更新"
  echo "  $0 -p 5 2023-11-01 2023-11-30 # 11月の全日付を5並列で更新"
  echo "  $0 --fit-only 2023-10-01 2023-10-31    # バイタルデータのみ更新"
  echo "  $0 --weather-only 2023-10-01 2023-10-31 # 天候データのみ更新"
  echo "  $0 --github-only 2023-10-01 2023-10-31  # GitHub活動データのみ更新"
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
PROCESS_FIT=true
PROCESS_WEATHER=true
PROCESS_GITHUB=true

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
    --fit-only)
      PROCESS_FIT=true
      PROCESS_WEATHER=false
      PROCESS_GITHUB=false
      shift
      ;;
    --weather-only)
      PROCESS_FIT=false
      PROCESS_WEATHER=true
      PROCESS_GITHUB=false
      shift
      ;;
    --github-only)
      PROCESS_FIT=false
      PROCESS_WEATHER=false
      PROCESS_GITHUB=true
      shift
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

# 処理内容の表示
echo "処理する日付範囲: $START_DATE から $END_DATE"
echo "並列処理数: $PARALLEL"
if [ -n "$LOCAL_MODE" ]; then
  echo "実行モード: ローカル"
else
  echo "実行モード: Cloud Function"
fi

echo "更新対象:"
if [ "$PROCESS_FIT" = true ]; then
  echo "  - バイタルデータ (Google Fit)"
fi
if [ "$PROCESS_WEATHER" = true ]; then
  echo "  - 天候データ"
fi
if [ "$PROCESS_GITHUB" = true ]; then
  echo "  - GitHub活動データ"
fi
if [ "$PROCESS_FIT" = false ] && [ "$PROCESS_WEATHER" = false ] && [ "$PROCESS_GITHUB" = false ]; then
  echo "エラー: 処理対象が選択されていません"
  exit 1
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
  local date=$1
  echo "処理中: $date"

  local fit_success=true
  local weather_success=true
  local github_success=true
  local any_processed=false

  # バイタルデータ処理
  if [ "$PROCESS_FIT" = true ]; then
    any_processed=true
    echo "  バイタルデータを処理中..."
    if ! bash "$PROJECT_ROOT/scripts/utils/trigger_fit.sh" "$date"; then
      echo "  エラー: バイタルデータの処理に失敗 ($date)"
      fit_success=false
    else
      echo "  バイタルデータ処理完了 ($date)"
    fi
  else
    echo "  バイタルデータはスキップ（既存データを保持）"
  fi

  # 天候データ処理
  if [ "$PROCESS_WEATHER" = true ]; then
    any_processed=true
    echo "  天候データを処理中..."
    if ! bash "$PROJECT_ROOT/scripts/utils/update_weather.sh" "$date"; then
      echo "  エラー: 天候データの処理に失敗 ($date)"
      weather_success=false
    else
      echo "  天候データ処理完了 ($date)"
    fi
  else
    echo "  天候データはスキップ（既存データを保持）"
  fi

  # GitHubデータ処理
  if [ "$PROCESS_GITHUB" = true ]; then
    any_processed=true
    echo "  GitHub活動データを処理中..."
    # YYYY-MM-DD形式をYYYYMMDD形式に変換
    local github_date=$(echo "$date" | sed 's/-//g')
    if ! bash "$PROJECT_ROOT/scripts/utils/update_github.sh" "$github_date"; then
      echo "  エラー: GitHubデータの処理に失敗 ($date)"
      github_success=false
    else
      echo "  GitHubデータ処理完了 ($date)"
    fi
  else
    echo "  GitHubデータはスキップ（既存データを保持）"
  fi

  # 結果判定（実際に処理したデータのみを対象）
  local overall_success=true
  if [ "$PROCESS_FIT" = true ] && [ "$fit_success" = false ]; then
    overall_success=false
  fi
  if [ "$PROCESS_WEATHER" = true ] && [ "$weather_success" = false ]; then
    overall_success=false
  fi
  if [ "$PROCESS_GITHUB" = true ] && [ "$github_success" = false ]; then
    overall_success=false
  fi

  if [ "$overall_success" = true ]; then
    if [ "$any_processed" = true ]; then
      echo "  成功: $date の指定データ処理完了"
    else
      echo "  スキップ: $date は処理対象外"
    fi
    return 0
  else
    echo "  失敗: $date の処理でエラーが発生"
    return 1
  fi
}

# 日付を処理
total=${#DATES[@]}
success=0
error=0

# GNU parallelが使えるか確認
if command -v parallel >/dev/null 2>&1; then
  # 環境変数をexport
  export SCRIPT_DIR PROJECT_ROOT PROCESS_FIT PROCESS_WEATHER PROCESS_GITHUB LOCAL_MODE

  # 関数をexport用ファイルに保存
  cat > /tmp/process_batch_func.sh << 'EOF'
process_batch() {
  local date=$1
  echo "処理中: $date"

  local fit_success=true
  local weather_success=true
  local github_success=true
  local any_processed=false

  # バイタルデータ処理
  if [ "$PROCESS_FIT" = true ]; then
    any_processed=true
    echo "  バイタルデータを処理中..."
    if ! bash "$PROJECT_ROOT/scripts/utils/trigger_fit.sh" "$date"; then
      echo "  エラー: バイタルデータの処理に失敗 ($date)"
      fit_success=false
    else
      echo "  バイタルデータ処理完了 ($date)"
    fi
  else
    echo "  バイタルデータはスキップ（既存データを保持）"
  fi

  # 天候データ処理
  if [ "$PROCESS_WEATHER" = true ]; then
    any_processed=true
    echo "  天候データを処理中..."
    if ! bash "$PROJECT_ROOT/scripts/utils/update_weather.sh" "$date"; then
      echo "  エラー: 天候データの処理に失敗 ($date)"
      weather_success=false
    else
      echo "  天候データ処理完了 ($date)"
    fi
  else
    echo "  天候データはスキップ（既存データを保持）"
  fi

  # GitHubデータ処理
  if [ "$PROCESS_GITHUB" = true ]; then
    any_processed=true
    echo "  GitHub活動データを処理中..."
    # YYYY-MM-DD形式をYYYYMMDD形式に変換
    local github_date=$(echo "$date" | sed 's/-//g')
    if ! bash "$PROJECT_ROOT/scripts/utils/update_github.sh" "$github_date"; then
      echo "  エラー: GitHubデータの処理に失敗 ($date)"
      github_success=false
    else
      echo "  GitHubデータ処理完了 ($date)"
    fi
  else
    echo "  GitHubデータはスキップ（既存データを保持）"
  fi

  # 結果判定（実際に処理したデータのみを対象）
  local overall_success=true
  if [ "$PROCESS_FIT" = true ] && [ "$fit_success" = false ]; then
    overall_success=false
  fi
  if [ "$PROCESS_WEATHER" = true ] && [ "$weather_success" = false ]; then
    overall_success=false
  fi
  if [ "$PROCESS_GITHUB" = true ] && [ "$github_success" = false ]; then
    overall_success=false
  fi

  if [ "$overall_success" = true ]; then
    if [ "$any_processed" = true ]; then
      echo "  成功: $date の指定データ処理完了"
    else
      echo "  スキップ: $date は処理対象外"
    fi
    return 0
  else
    echo "  失敗: $date の処理でエラーが発生"
    return 1
  fi
}
EOF

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

echo
echo "すべての処理が完了しました。"
echo "処理結果:"
echo -n "  - 更新対象: "
first=true
if [ "$PROCESS_FIT" = true ]; then
  echo -n "バイタルデータ"
  first=false
fi
if [ "$PROCESS_WEATHER" = true ]; then
  if [ "$first" = false ]; then echo -n "、"; fi
  echo -n "天候データ"
  first=false
fi
if [ "$PROCESS_GITHUB" = true ]; then
  if [ "$first" = false ]; then echo -n "、"; fi
  echo -n "GitHub活動データ"
fi
echo ""
echo "終了コード: $EXIT_CODE"
exit $EXIT_CODE
