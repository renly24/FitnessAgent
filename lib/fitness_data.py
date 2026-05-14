"""Fitness exercise definitions focused on fat loss / diet."""

from dataclasses import dataclass


@dataclass
class Exercise:
    name: str
    description: str
    duration_sec: int
    calories_approx: int
    category: str  # "cardio" | "strength" | "hiit"


EXERCISES: list[Exercise] = [
    Exercise("バーピー", "全身を使う有酸素＋筋力運動", 30, 8, "hiit"),
    Exercise("ジャンピングジャック", "全身有酸素運動", 30, 5, "cardio"),
    Exercise("マウンテンクライマー", "体幹＋有酸素", 30, 7, "hiit"),
    Exercise("スクワット", "下半身筋トレ＋代謝アップ", 30, 5, "strength"),
    Exercise("腹筋クランチ", "腹部強化", 30, 4, "strength"),
    Exercise("プッシュアップ", "上半身筋トレ", 30, 5, "strength"),
    Exercise("ハイニー", "その場で高膝ランニング", 30, 6, "cardio"),
    Exercise("プランク", "体幹強化", 30, 3, "strength"),
    Exercise("ランジ", "下半身強化＋バランス", 30, 5, "strength"),
    Exercise("ジャンプスクワット", "下半身HIIT", 30, 8, "hiit"),
]

DEFAULT_WORKOUT_PHASES = [
    {"phase": "ウォームアップ", "duration_sec": 60, "note": "その場足踏み・肩回し"},
    {"phase": "メインセット", "sets": 3, "rest_sec": 20},
    {"phase": "クールダウン", "duration_sec": 60, "note": "深呼吸・軽いストレッチ"},
]


def get_exercises_for_day(weekday: int) -> list[Exercise]:
    """Return recommended exercises for a given weekday (0=Mon, 6=Sun)."""
    if weekday in (0, 3):  # 月・木: HIIT メイン
        categories = ["hiit", "cardio"]
    elif weekday in (1, 4):  # 火・金: 筋トレ メイン
        categories = ["strength", "hiit"]
    elif weekday == 5:  # 土: 全身
        categories = ["cardio", "strength", "hiit"]
    else:  # 水・日: 軽め有酸素
        categories = ["cardio"]

    return [e for e in EXERCISES if e.category in categories]
