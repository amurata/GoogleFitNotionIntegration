#!/bin/bash
# 天気データを取得・更新するスクリプト

# このスクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SRC_DIR="${PROJECT_ROOT}/src"
WEATHER_DIR="${SRC_DIR}/weather"

# 引数を確認
if [ $# -eq 0 ]; then
    # 引数がない場合は2日前（前々日）のデータを更新
    cd "${WEATHER_DIR}" && python update_weather.py
else
    # 日付指定がある場合
    cd "${WEATHER_DIR}" && python update_weather.py "$1"
fi 
