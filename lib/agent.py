"""Gemini API agent for generating fitness motivation messages."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _build_context(trigger_time: str, record_summary: str) -> str:
    tz = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tokyo"))
    now = datetime.now(tz)
    weekday_jp = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    return (
        f"現在の日時: {now.strftime('%Y-%m-%d')}({weekday_jp}) {trigger_time}\n"
        f"ユーザーの最近の記録: {record_summary}"
    )


def generate_motivation_message(
    trigger_time: str,
    record_summary: str,
    phase: int = 1,
) -> str:
    """Generate a motivational fitness message for Alexa to speak.

    Args:
        trigger_time: "朝" or "夕方"
        record_summary: Brief summary of recent workout records
        phase: 1=motivation only, 2=suggest today's menu
    """
    _FALLBACK = {
        "朝": "おはよう！今日も脂肪を燃やすぞ！体を動かしてから一日を始めよう！",
        "夕方": "まだ間に合う！今日の運動、やらずに終わるつもりか！",
    }

    phase1_system = (
        "あなたはユーザーのダイエット・体脂肪削減をサポートする熱血フィットネストレーナーです。"
        "Alexaが読み上げる短いモチベーションメッセージを生成してください。\n"
        "条件:\n"
        "- 30〜60字程度の短さで話しかけてください\n"
        "- 朝ならエネルギッシュに一日を始める煽り、夕方なら「まだ間に合う」「今やらないでいつやる」系の煽り\n"
        "- ダイエット・体脂肪削減にフォーカスした言葉\n"
        "- 体育会系で熱血、でも親しみやすいトーン\n"
        "- 読み上げテキストのみ返してください。前置きや説明は不要です"
    )

    phase2_addition = (
        "\nさらに、今日おすすめの運動メニューを1〜2種類、具体的な回数・時間と共に提案してください。"
        "メニューはダイエット効果が高いものを選び、合計で10〜20分程度に収めてください。"
    )

    prompt = phase1_system + (phase2_addition if phase >= 2 else "")
    context = _build_context(trigger_time, record_summary)

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{prompt}\n\n{context}",
        )
        return response.text.strip()
    except Exception:
        return _FALLBACK.get(trigger_time, _FALLBACK["朝"])
