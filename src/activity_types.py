"""
Google Fit アクティビティタイプの日本語マッピング
Activity Types from Google Fit API with Japanese translations
"""

# Google Fit Activity Types mapping
# https://developers.google.com/fit/rest/v1/reference/activity-types
ACTIVITY_TYPES = {
    # 基本動作 (Basic Movements)
    0: {"en": "In vehicle", "ja": "車両移動"},
    1: {"en": "Biking", "ja": "サイクリング"},
    2: {"en": "On foot", "ja": "徒歩"},
    3: {"en": "Still", "ja": "静止"},
    4: {"en": "Unknown", "ja": "不明"},
    5: {"en": "Tilting", "ja": "傾き"},
    
    # ウォーキング/ランニング (Walking/Running)
    7: {"en": "Walking", "ja": "ウォーキング"},
    8: {"en": "Running", "ja": "ランニング"},
    56: {"en": "Jogging", "ja": "ジョギング"},
    93: {"en": "Walking (fitness)", "ja": "フィットネスウォーク"},
    94: {"en": "Nordic walking", "ja": "ノルディックウォーキング"},
    95: {"en": "Walking (treadmill)", "ja": "トレッドミル（ウォーキング）"},
    116: {"en": "Walking (stroller)", "ja": "ベビーカーウォーキング"},
    
    # エアロビクス/フィットネス (Aerobics/Fitness)
    9: {"en": "Aerobics", "ja": "エアロビクス"},
    10: {"en": "Badminton", "ja": "バドミントン"},
    11: {"en": "Baseball", "ja": "野球"},
    12: {"en": "Basketball", "ja": "バスケットボール"},
    13: {"en": "Biathlon", "ja": "バイアスロン"},
    
    # サイクリング種別 (Cycling Types)
    14: {"en": "Handbiking", "ja": "ハンドサイクリング"},
    15: {"en": "Mountain biking", "ja": "マウンテンバイク"},
    16: {"en": "Road biking", "ja": "ロードバイク"},
    17: {"en": "Spinning", "ja": "スピニング"},
    18: {"en": "Stationary biking", "ja": "エアロバイク"},
    19: {"en": "Utility biking", "ja": "実用サイクリング"},
    
    # 格闘技/武道 (Martial Arts)
    20: {"en": "Boxing", "ja": "ボクシング"},
    21: {"en": "Calisthenics", "ja": "自重トレーニング"},
    
    # チームスポーツ (Team Sports)
    22: {"en": "Circuit training", "ja": "サーキットトレーニング"},
    23: {"en": "Cricket", "ja": "クリケット"},
    24: {"en": "Dancing", "ja": "ダンス"},
    25: {"en": "Elliptical", "ja": "エリプティカル"},
    26: {"en": "Fencing", "ja": "フェンシング"},
    27: {"en": "Football (American)", "ja": "アメフト"},
    28: {"en": "Football (Australian)", "ja": "オージーフットボール"},
    29: {"en": "Football (Soccer)", "ja": "サッカー"},
    30: {"en": "Frisbee", "ja": "フリスビー"},
    31: {"en": "Gardening", "ja": "ガーデニング"},
    32: {"en": "Golf", "ja": "ゴルフ"},
    33: {"en": "Gymnastics", "ja": "体操"},
    34: {"en": "Handball", "ja": "ハンドボール"},
    35: {"en": "Hiking", "ja": "ハイキング"},
    36: {"en": "Hockey", "ja": "ホッケー"},
    37: {"en": "Horseback riding", "ja": "乗馬"},
    38: {"en": "Housework", "ja": "家事"},
    39: {"en": "Jumping rope", "ja": "縄跳び"},
    40: {"en": "Kayaking", "ja": "カヤック"},
    41: {"en": "Kettlebell training", "ja": "ケトルベル"},
    42: {"en": "Kickboxing", "ja": "キックボクシング"},
    43: {"en": "Kitesurfing", "ja": "カイトサーフィン"},
    44: {"en": "Martial arts", "ja": "格闘技"},
    45: {"en": "Meditation", "ja": "瞑想"},
    46: {"en": "Mixed martial arts", "ja": "総合格闘技"},
    47: {"en": "P90X exercises", "ja": "P90Xエクササイズ"},
    48: {"en": "Paragliding", "ja": "パラグライダー"},
    49: {"en": "Pilates", "ja": "ピラティス"},
    50: {"en": "Polo", "ja": "ポロ"},
    51: {"en": "Racquetball", "ja": "ラケットボール"},
    52: {"en": "Rock climbing", "ja": "ロッククライミング"},
    53: {"en": "Rowing", "ja": "ローイング"},
    54: {"en": "Rowing machine", "ja": "ローイングマシン"},
    55: {"en": "Rugby", "ja": "ラグビー"},
    57: {"en": "Sand volleyball", "ja": "ビーチバレー"},
    58: {"en": "Sailing", "ja": "セーリング"},
    59: {"en": "Scuba diving", "ja": "スキューバダイビング"},
    60: {"en": "Skateboarding", "ja": "スケートボード"},
    61: {"en": "Skating", "ja": "スケート"},
    62: {"en": "Skiing", "ja": "スキー"},
    63: {"en": "Skiing (cross-country)", "ja": "クロスカントリースキー"},
    64: {"en": "Skiing (downhill)", "ja": "ダウンヒルスキー"},
    65: {"en": "Snowboarding", "ja": "スノーボード"},
    66: {"en": "Snowmobile", "ja": "スノーモービル"},
    67: {"en": "Snowshoeing", "ja": "スノーシュー"},
    68: {"en": "Squash", "ja": "スカッシュ"},
    69: {"en": "Stair climbing", "ja": "階段昇降"},
    70: {"en": "Stair climbing machine", "ja": "ステアクライマー"},
    71: {"en": "Stand-up paddleboarding", "ja": "スタンドアップパドルボード"},
    72: {"en": "Sleeping", "ja": "睡眠"},
    73: {"en": "Surfing", "ja": "サーフィン"},
    74: {"en": "Swimming", "ja": "水泳"},
    75: {"en": "Swimming (pool)", "ja": "プール水泳"},
    76: {"en": "Swimming (open water)", "ja": "オープンウォータースイミング"},
    77: {"en": "Table tennis", "ja": "卓球"},
    78: {"en": "Team sports", "ja": "チームスポーツ"},
    79: {"en": "Tennis", "ja": "テニス"},
    80: {"en": "Strength training", "ja": "筋力トレーニング"},
    81: {"en": "Treadmill", "ja": "トレッドミル"},
    82: {"en": "Volleyball", "ja": "バレーボール"},
    83: {"en": "Wakeboarding", "ja": "ウェイクボード"},
    84: {"en": "Water polo", "ja": "水球"},
    85: {"en": "Weightlifting", "ja": "ウェイトリフティング"},
    86: {"en": "Wheelchair", "ja": "車椅子"},
    87: {"en": "Windsurfing", "ja": "ウィンドサーフィン"},
    88: {"en": "Yoga", "ja": "ヨガ"},
    89: {"en": "Zumba", "ja": "ズンバ"},
    
    # 追加のアクティビティ (Additional Activities)
    90: {"en": "Curling", "ja": "カーリング"},
    91: {"en": "Crossfit", "ja": "クロスフィット"},
    92: {"en": "Elevator", "ja": "エレベーター"},
    96: {"en": "Running (treadmill)", "ja": "トレッドミル（ランニング）"},
    97: {"en": "Ice skating", "ja": "アイススケート"},
    98: {"en": "Indoor skating", "ja": "インドアスケート"},
    99: {"en": "Cross skating", "ja": "クロススケート"},
    100: {"en": "Inline skating", "ja": "インラインスケート"},
    101: {"en": "High intensity interval training", "ja": "HIIT"},
    102: {"en": "Interval training", "ja": "インターバルトレーニング"},
    103: {"en": "Light sleep", "ja": "浅い睡眠"},
    104: {"en": "Deep sleep", "ja": "深い睡眠"},
    105: {"en": "REM sleep", "ja": "レム睡眠"},
    106: {"en": "Awake during sleep cycle", "ja": "睡眠中の覚醒"},
    107: {"en": "Archery", "ja": "アーチェリー"},
    108: {"en": "Other", "ja": "その他"},
    109: {"en": "Light sleep", "ja": "浅い睡眠"},
    110: {"en": "Deep sleep", "ja": "深い睡眠"},
    111: {"en": "REM sleep", "ja": "レム睡眠"},
    112: {"en": "Awake", "ja": "覚醒"},
    113: {"en": "Downhill skiing", "ja": "ダウンヒルスキー"},
    114: {"en": "Cross-country skiing", "ja": "クロスカントリースキー"},
    115: {"en": "Kite skiing", "ja": "カイトスキー"},
    117: {"en": "Roller skiing", "ja": "ローラースキー"},
    118: {"en": "Sledding", "ja": "そり"},
    119: {"en": "HIIT", "ja": "HIIT"},
    120: {"en": "Guided breathing", "ja": "呼吸法"},
}


def get_activity_name(activity_type: int, lang: str = "ja") -> str:
    """
    アクティビティタイプIDから名前を取得
    
    Args:
        activity_type: Google Fit activity type ID
        lang: 言語 ("ja" for Japanese, "en" for English)
    
    Returns:
        Activity name in specified language
    """
    if activity_type in ACTIVITY_TYPES:
        return ACTIVITY_TYPES[activity_type].get(lang, f"Activity Type {activity_type}")
    else:
        return f"その他 (Type {activity_type})" if lang == "ja" else f"Other (Type {activity_type})"


def get_japanese_name(activity_type: int) -> str:
    """アクティビティタイプIDから日本語名を取得"""
    return get_activity_name(activity_type, "ja")


def get_english_name(activity_type: int) -> str:
    """アクティビティタイプIDから英語名を取得"""
    return get_activity_name(activity_type, "en")