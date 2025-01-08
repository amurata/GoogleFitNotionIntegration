# Google Fit API Scopes
OAUTH_SCOPE = [
    "https://www.googleapis.com/auth/fitness.activity.read",  # 歩数、距離、カロリー
    "https://www.googleapis.com/auth/fitness.body.read",      # 体重
    "https://www.googleapis.com/auth/fitness.heart_rate.read", # 心拍数
    "https://www.googleapis.com/auth/fitness.oxygen_saturation.read", # 酸素飽和度
    "https://www.googleapis.com/auth/fitness.sleep.read",     # 睡眠データ
]

# Google Fit Data Types
DATA_TYPES = {
    "distance": "com.google.distance.delta",
    "steps": "com.google.step_count.delta",
    "calories": "com.google.calories.expended",
    "active_minutes": "com.google.heart_minutes",
    "heart_rate": "com.google.heart_rate.bpm",
    "oxygen": "com.google.oxygen_saturation",
    "weight": "com.google.weight",
}

# Activity Types
ACTIVITY_TYPES = {
    "sleep": 72,  # SLEEP activity type
}
