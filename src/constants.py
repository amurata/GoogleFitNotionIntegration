# Google Fit API Scopes
OAUTH_SCOPE = [
    "https://www.googleapis.com/auth/fitness.activity.read",  # 歩数、距離、カロリー
    "https://www.googleapis.com/auth/fitness.body.read",      # 体重
    "https://www.googleapis.com/auth/fitness.heart_rate.read", # 心拍数
    "https://www.googleapis.com/auth/fitness.oxygen_saturation.read", # 酸素飽和度
    "https://www.googleapis.com/auth/fitness.sleep.read",     # 睡眠データ
    "https://www.googleapis.com/auth/fitness.location.read",  # 位置情報（距離計算に必要）
]

# Google Fit Data Types
DATA_TYPES = {
    "distance": "com.google.distance.delta",
    "steps": "com.google.step_count.delta",
    "calories": "com.google.calories.expended",
    "active_minutes": "com.google.heart_minutes",  # Heart Points（活動強度の指標）
    # "move_minutes": "com.google.move_minutes",  # Move Minutes（利用できない場合がある）
    "heart_rate": "com.google.heart_rate.bpm",
    "oxygen": "com.google.oxygen_saturation",
    "weight": "com.google.weight",
    "body_fat": "com.google.body.fat.percentage",  # 体脂肪率
}

# Activity Types
ACTIVITY_TYPES = {
    "sleep": 72,  # SLEEP activity type
    "meditation": 45,  # MEDITATION activity type
    "running": 8,  # RUNNING activity type
    "walking": 7,  # WALKING activity type
    "cycling": 1,  # BIKING activity type
    "strength_training": 80,  # STRENGTH_TRAINING activity type
}
