# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FitnessAgent** は Alexa スキルとして動作する体脂肪削減特化フィットネスエージェント。Alexa のスケジュールトリガー（朝夕 6:30）で自動発話し、Gemini API が生成した煽りメッセージでモチベーションを維持する。Vercel Serverless（Python）にデプロイ。

## Architecture

```
Alexa (スケジュールトリガー JST 6:30 AM/PM)
  └─→ Vercel Serverless: api/alexa.py (FastAPI + ask-sdk)
       ├─→ lib/agent.py  — Gemini API でメッセージ生成
       ├─→ lib/storage.py — Vercel KV(Redis) or /tmp JSON
       └─→ lib/fitness_data.py — 運動種目定義（Phase 2 用）
```

- `api/alexa.py` は FastAPI アプリと Alexa SDK を同居させ、`WebserviceSkillHandler` でリクエストを処理する。
- `lib/agent.py` は `GEMINI_API_KEY` で Gemini 2.0 Flash を呼び出す。`ANTHROPIC_API_KEY` は**使用していない**（README 記載は古い）。
- `lib/storage.py` は `KV_URL` 環境変数があれば Redis、なければ `/tmp/fitness_records.json` にフォールバック。
- `api/health.py` は独立した FastAPI アプリとして `/api/health` を提供する。

## Environment Variables

| 変数 | 説明 |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API キー（必須） |
| `KV_URL` | Vercel KV の Redis URL（省略時はローカル JSON） |
| `ALEXA_SKILL_ID` | Alexa スキル ID（署名検証に使用） |
| `TIMEZONE` | デフォルト `Asia/Tokyo` |

## Development Commands

```bash
# 依存関係インストール
pip install -r requirements.txt

# ローカルでメッセージ生成テスト
python -c "from lib.agent import generate_motivation_message; print(generate_motivation_message('朝', '記録なし'))"

# FastAPI ローカル起動（alexa エンドポイント）
uvicorn api.alexa:app --reload

# Vercel デプロイ
vercel --prod
```

## Vercel Deployment Notes

- `vercel.json` で `api/*.py` を `@vercel/python` でビルド。
- 各 `.py` ファイルが独立した Serverless Function になるため、`api/alexa.py` と `api/health.py` はそれぞれ独自の `FastAPI()` インスタンスを持つ。
- `sys.path.insert(0, ...)` で `lib/` を import できるようにしている。

## Alexa Intents

| Intent | 発話例 |
|---|---|
| `LaunchRequest` | スキル起動（スケジュールトリガー含む） |
| `WorkoutDoneIntent` | 「やった」 |
| `WorkoutSkipIntent` | 「まだ」「やってない」 |
| `StatusIntent` | 「記録を教えて」 |

対話モデル定義は `data/interaction_model.json`。

## Phase Roadmap

- **Phase 1** ✅ 煽りトーク + 記録
- **Phase 2** 🔜 今日のメニュー提案（`lib/fitness_data.py` の `get_exercises_for_day()` を使用）
- **Phase 3** 🔜 カウントダウン読み上げ
