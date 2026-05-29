# AI Content Bridge 🌉

**China → Global in One Click.**

AI-powered content localization platform that transforms Chinese content into culturally-adapted English posts for X (Twitter), LinkedIn, and Reddit.

```mermaid
graph LR
    A[🇨🇳 Chinese Text] --> B[🔍 Analysis]
    B --> C[🌏 Cultural Localization]
    C --> D[📱 Platform Adaptation]
    D --> E[🚀 X / LinkedIn / Reddit]
```

## Why AI Content Bridge?

Chinese entrepreneurs and creators face a unique challenge: their content is brilliant, but it doesn't resonate globally. Direct translation loses cultural context, humor, and relevance.

**AI Content Bridge** is a 3-step localization pipeline:

1. **Analyze** — Extract core message, audience, and key points from Chinese text
2. **Localize** — Adapt culturally for an international English-speaking audience
3. **Adapt** — Format optimally for each platform (X threads, LinkedIn professional, Reddit community)

## Quick Start

```bash
# Clone & install
git clone https://github.com/guish7423/ai-content-bridge
cd ai-content-bridge
uv sync  # or: pip install -e .

# Start in mock mode (no API key needed)
SOCIAL_API_MOCK=true uv run uvicorn app.main:app --reload

# Open http://localhost:8000
```

## CLI Usage

```bash
# Translate Chinese to English (X/LinkedIn/Reddit)
uv run python -m app.cli "中国的AI创业公司正在快速崛起" --platform x

# Quick mode — just the adapted text
uv run python -m app.cli "中国创业者出海正当时" --quick

# Full pipeline with JSON output
uv run python -m app.cli "Semantic Kernel 是什么？" --all --json
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | — | DeepSeek API key (get at [platform.deepseek.com](https://platform.deepseek.com)) |
| `LLM_API_MOCK` | `true` | Use mock responses for testing |
| `LLM_MODEL` | `deepseek-chat` | Model name |
| `X_API_KEY` | — | X/Twitter API v2 key |
| `X_BEARER_TOKEN` | — | X/Twitter bearer token |
| `LINKEDIN_ACCESS_TOKEN` | — | LinkedIn API access token |
| `LINKEDIN_USER_ID` | — | LinkedIn user URN ID |
| `SOCIAL_API_MOCK` | `true` | Use mock social posting |

## API

```bash
# Full pipeline
curl -X POST http://localhost:8000/bridge \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界", "platforms": ["x", "linkedin"]}'

# Quick mode (one platform, just the text)
curl -X POST http://localhost:8000/quick \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界", "platform": "x"}'

# Publish to social media
curl -X POST http://localhost:8000/publish \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!", "platform": "x"}'

# Health check
curl http://localhost:8000/health
```

## Tech Stack

- **Python 3.12+** — FastAPI + httpx
- **DeepSeek API** — Cost-efficient LLM ($0.07/M input tokens)
- **Jinja2 + HTMX** — Minimal JS web interface
- **Tweepy** — X/Twitter API v2
- **SQLite** — Lightweight data storage

## Roadmap

- [x] Core localization engine (Analyze → Localize → Adapt)
- [x] Web interface (HTMX, dark theme)
- [x] X/Twitter publishing
- [x] LinkedIn publishing
- [ ] Reddit publishing
- [ ] Blog (Ghost/Medium) publishing
- [ ] Batch processing
- [ ] User accounts & API keys
- [ ] Usage analytics dashboard

## Pricing (Planned)

| Plan | Price | Features |
|------|-------|----------|
| Free | $0 | 10 translations/month, mock mode |
| Starter | $19/mo | 100 translations, 1 social account |
| Pro | $49/mo | Unlimited, all platforms, priority |
| Enterprise | Custom | Custom integrations, SLA |

## Why This Exists

Built by a solo developer who saw the gap: Chinese entrepreneurs building world-class products struggle to tell their story globally. Tools like DeepL translate words, but they don't translate culture. AI Content Bridge bridges that gap — for real.

*"中国创业者不需要翻译器，他们需要一个文化翻译官。"*

---

**[🔗 Live Demo](http://localhost:8000)** | Built with ❤️ for the global Chinese creator community
