"""AI Content Bridge — core prompt chain.

Translates Chinese content into platform-optimized English versions.
Pipeline: Analyze → Localize → Adapt → Polish
"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Literal

from app.config import settings

Platform = Literal["x", "linkedin", "reddit", "blog"]

# ── Cost tracking ─────────────────────────────────────────────────────────────

@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0

    def record(self, prompt_t: int, completion_t: int, model: str):
        self.prompt_tokens += prompt_t
        self.completion_tokens += completion_t
        self.total_tokens += prompt_t + completion_t
        self.calls += 1
        # Multi-model pricing per million tokens
        model_lower = model.lower()
        if 'llama' in model_lower or 'nvidia' in model_lower:
            # Llama 3.1 8B: $0.10 in + $0.10 out
            cost = (prompt_t + completion_t) * 0.10 / 1_000_000
        elif 'deepseek' in model_lower or 'flash' in model_lower:
            cost = prompt_t * 0.07 / 1_000_000 + completion_t * 0.28 / 1_000_000
        elif 'pro' in model_lower:
            cost = prompt_t * 0.14 / 1_000_000 + completion_t * 0.56 / 1_000_000
        else:
            cost = (prompt_t + completion_t) * 0.15 / 1_000_000
        self.cost_usd += cost

    def summary(self) -> dict:
        return {
            "calls": self.calls,
            "tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 4),
        }

usage = Usage()

# ── LLM Call ──────────────────────────────────────────────────────────────────

def _is_mock() -> bool:
    return os.environ.get("LLM_API_MOCK", str(settings.llm_api_mock)).lower() in ("true", "1")

def _parse_json_from_text(text: str) -> dict:
    """Extract JSON from LLM response text (for APIs without native JSON mode)."""
    # Try direct parse first
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    # Try to extract JSON block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Fallback: return as result
    return {"result": text}
def call_llm(prompt: str, system: str = "", json_mode: bool = True) -> dict:
    """Sync LLM call with retry."""
    if _is_mock():
        return json.loads(os.environ.get("LLM_MOCK_RESPONSE", settings.llm_mock_response))

    import httpx

    body = {
        "model": settings.llm_model,
        "messages": [],
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    if system:
        body["messages"].append({"role": "system", "content": system})
    body["messages"].append({"role": "user", "content": prompt})
    if json_mode and settings.supports_json_mode:
        body["response_format"] = {"type": "json_object"}

    last_err = None
    for attempt in range(3):
        try:
            resp = httpx.post(
                f"{settings.llm_api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            usage.record(
                data.get("usage", {}).get("prompt_tokens", 0),
                data.get("usage", {}).get("completion_tokens", 0),
                data.get("model", settings.llm_model),
            )
            content = data["choices"][0]["message"]["content"]
            if json_mode:
                return _parse_json_from_text(content)
            return {"result": content}
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(2.0 * (2 ** attempt))
    raise RuntimeError(f"LLM call failed: {last_err}")

# ── SYSTEM PROMPTS (the secret sauce) ─────────────────────────────────────────

ANALYZER_SYSTEM = """You are a bilingual content analyst and marketing strategist. Given Chinese text, extract and analyze:

core_message: The single most important point in one compelling sentence (English)
target_audience: Who this is for (English, specific — e.g., "solopreneurs running Shopify stores")
key_points: 3-5 actionable bullet points (English)
tone: Professional / Casual / Humorous / Urgent / Inspirational
cultural_context: Chinese-specific references needing localization
emotional_triggers: What emotions does this appeal to (trust, FOMO, ambition, etc.)
unique_selling_point: What makes this different (1 sentence)

Respond in JSON format."""

LOCALIZER_SYSTEM = """You are a senior copywriter specializing in cultural transcreation. NOT translation — transcreation.

Rules:
1. Replace Chinese-specific references with universal equivalents
2. Adapt idioms and cultural references for international audiences
3. Make it FEEL native English — like originally written in English
4. Add context where needed ("similar to a cross between Shopify and ChatGPT")
5. Enhance persuasive power: stronger verbs, clearer benefits, emotional hooks
6. Preserve accuracy but improve narrative flow
7. Output 2-3x longer — expand benefits, use cases, social proof

Output JSON with: localized_text (full transcreated version), changes_made, cultural_notes"""

PLATFORM_SYSTEM = """You are a social media content strategist. Adapt content for the specified platform.

For X/Twitter:
- Max 280 chars per post. For longer content, use thread format numbered 1/N
- Strong hook in first line, clear value proposition
- 2-3 relevant hashtags. Conversational, punchy tone

For LinkedIn:
- Professional but warm tone, 800-1500 chars
- Open with a short personal story or insight
- 2-4 bullet points for key takeaways
- 3-5 hashtags, end with an engagement question

For Reddit:
- Conversational, helpful tone (no hard sell)
- Provide value first, be transparent about affiliation
- 200-500 chars

CRITICAL: Respond ONLY with the post content. No JSON. No markdown. No labels. Just the text."""

# ── Core Pipeline ─────────────────────────────────────────────────────────────

@dataclass
class BridgeResult:
    """Complete output from the content bridge pipeline."""
    original_text: str
    analysis: dict
    localized_text: str
    platform_versions: dict[str, dict]  # platform -> {content, hashtags, notes}
    usage: dict

def process(text: str, platforms: list[Platform] | None = None) -> BridgeResult:
    """Run the full CN→EN content bridge pipeline.

    Args:
        text: Chinese input text
        platforms: Target platforms (default: all)

    Returns:
        BridgeResult with analysis, localization, and platform versions
    """
    if platforms is None:
        platforms = ["x", "linkedin", "reddit"]

    # Step 1: Analyze
    analysis = call_llm(
        prompt=f"Analyze this Chinese text:\n\n{text}",
        system=ANALYZER_SYSTEM,
    )

    # Step 2: Localize
    localized = call_llm(
        prompt=f"Localize this content for international audience:\n\n{text}\n\nAnalysis: {json.dumps(analysis, ensure_ascii=False)}",
        system=LOCALIZER_SYSTEM,
    )
    localized_text = localized.get("localized_text", localized.get("result", ""))

    # Step 3: Adapt per platform
    platform_versions = {}
    for platform in platforms:
        # Use plain text mode for non-JSON backends (NVIDIA, Ollama, etc.)
        use_json = settings.supports_json_mode
        result = call_llm(
            prompt=f"Adapt for {platform}:\n\nLocalized content:\n{localized_text}",
            system=PLATFORM_SYSTEM + f"\n\nTarget platform: {platform}",
            json_mode=use_json,
        )
        content = result.get("content", result.get("result", ""))
        platform_versions[platform] = {
            "content": content,
            "hashtags": [],
            "notes": "",
        }

    return BridgeResult(
        original_text=text,
        analysis=analysis,
        localized_text=localized_text,
        platform_versions=platform_versions,
        usage=usage.summary(),
    )


def process_quick(text: str, platform: Platform = "x") -> str:
    """Quick mode - single platform, no analysis output.
    Returns just the adapted content string.
    """
    result = call_llm(
        prompt=f"""Convert this Chinese text into a {platform} post in English.
Keep the tone natural. Output ONLY the post content, no JSON.

Text: {text}""",
        system="You are a bilingual content creator.",
        json_mode=False,
    )
    return result.get("result", result.get("content", ""))


def generate_thread(content: str, max_chars: int = 280) -> list[str]:
    """Split long text into X thread posts."""
    if len(content) <= max_chars:
        return []
    import re
    sentences = re.split(r'(?<=[.!?])\s+', content)
    posts, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 5 <= max_chars:
            current = (current + " " + s).strip() if current else s
        else:
            if current:
                posts.append(current)
            current = s
    if current:
        posts.append(current)
    return posts if len(posts) > 1 else []
