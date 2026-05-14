"""Claude API agent for generating fitness motivation messages."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
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
    context = _build_context(trigger_time, record_summary)

    phase1_instruction = (
        "あなたはユーザーのダイエット・体脂肪削減をサポートする熱血フィットネストレーナーです。"
        "Alexaが読み上げる短いモチベーションメッセージを生成してください。\n"
        "条件:\n"
        "- 30〜60字程度の短さで話しかけてください\n"
        "- 朝ならエネルギッシュに一日を始める煽り、夕方なら「まだ間に合う」「今やらないでいつやる」系の煽り\n"
        "- ダイエット・体脂肪削減にフォーカスした言葉\n"
        "- 体育会系で熱血、でも親しみやすいトーン\n"
        "- SSMLタグは不要、読み上げテキストのみ返してください"
    )

    phase2_addition = (
        "\nさらに、今日おすすめの運動メニューを1〜2種類、具体的な回数・時間と共に提案してください。"
        "メニューはダイエット効果が高いものを選び、合計で10〜20分程度に収めてください。"
    )

    instruction = phase1_instruction + (phase2_addition if phase >= 2 else "")

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=instruction,
        messages=[
            {
                "role": "user",
                "content": context,
            }
        ],
    )
    return response.content[0].text.strip()
