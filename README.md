# FitnessAgent

ダイエット・体脂肪削減に特化したAlexaフィットネスエージェント。朝夕6:30にAlexaが自動で発話し、Claude APIが生成した煽りメッセージでモチベーションを維持します。

## フェーズ

| フェーズ | 内容 | 状態 |
|---|---|---|
| Phase 1 | 煽りトーク（Claude生成） + 記録 | ✅ 実装済み |
| Phase 2 | 今日のメニュー提案 | 🔜 次フェーズ |
| Phase 3 | カウントダウン読み上げ | 🔜 将来 |

## アーキテクチャ

```
Alexa (スケジュールトリガー 6:30 AM/PM)
  └─→ Vercel Serverless (api/alexa.py)
       ├─→ Claude API (lib/agent.py) — メッセージ生成
       └─→ Vercel KV / ローカルJSON (lib/storage.py) — 記録
```

## セットアップ

### 1. 環境変数

`.env.example` を `.env` にコピーして設定:

```bash
cp .env.example .env
```

| 変数 | 説明 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API キー |
| `KV_URL` | Vercel KV の Redis URL（省略時はローカルJSON） |
| `ALEXA_SKILL_ID` | Alexa スキルID |
| `TIMEZONE` | タイムゾーン（デフォルト: Asia/Tokyo） |

### 2. Vercel へデプロイ

```bash
npm i -g vercel
vercel --prod
```

### 3. Alexa Skill 設定

1. [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) でスキルを作成
2. エンドポイントを `https://<your-vercel-url>/api/alexa` に設定
3. `data/interaction_model.json` の内容を対話モデルエディタに貼り付けてビルド
4. スキルIDを `.env` の `ALEXA_SKILL_ID` に設定

### 4. Alexa スケジュールトリガー設定

Alexa Developer Console で「スケジュール済みトリガー」を設定:
- **朝**: `cron(30 21 * * ? *)` （UTC 21:30 = JST 06:30）
- **夕方**: `cron(30 9 * * ? *)` （UTC 09:30 = JST 18:30）

## ローカル開発

```bash
pip install -r requirements.txt
python -c "from lib.agent import generate_motivation_message; print(generate_motivation_message('朝', '記録なし'))"
```

## ディレクトリ構成

```
FitnessAgent/
├── api/
│   ├── alexa.py          # Alexa Skill エンドポイント
│   └── health.py         # ヘルスチェック
├── lib/
│   ├── agent.py          # Claude API 連携
│   ├── fitness_data.py   # エクササイズデータ
│   └── storage.py        # 記録の読み書き
├── data/
│   └── interaction_model.json  # Alexa 対話モデル
├── vercel.json
├── requirements.txt
└── .env.example
```
