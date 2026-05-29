"""AI Content Bridge — configuration with auto-detect."""

import json
import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    """Settings with auto-detect. Priority: LLM_API_KEY > NVIDIA_API_KEY > Ollama > mock."""

    # --- LLM Backend (auto-detected) ---
    llm_api_key: str = ""
    llm_api_base_url: str = ""
    llm_model: str = ""
    supports_json_mode: bool = False

    def __post_init__(self):
        """Auto-detect best available LLM backend."""
        # 1) Explicit LLM_API_KEY (DeepSeek, OpenAI, etc.)
        key = os.getenv("LLM_API_KEY", "")
        if key:
            self.llm_api_key = key
            self.llm_api_base_url = os.getenv(
                "LLM_API_BASE_URL", "https://api.deepseek.com/v1"
            )
            self.llm_model = os.getenv("LLM_MODEL", "deepseek-chat")
            self.supports_json_mode = True
            return

        # 2) NVIDIA API key (available in env)
        nvidia = os.getenv("NVIDIA_API_KEY", "")
        if nvidia:
            self.llm_api_key = nvidia
            self.llm_api_base_url = "https://integrate.api.nvidia.com/v1"
            self.llm_model = "meta/llama-3.1-8b-instruct"
            self.supports_json_mode = False
            return

        # 3) Volcengine (火山引擎)
        volc = os.getenv("VOLC_ENGINE_API_KEY", "")
        if volc:
            self.llm_api_key = volc
            self.llm_api_base_url = (
                "https://ark.cn-beijing.volces.com/api/coding/v3"
            )
            self.llm_model = "doubao-seed-2.0-code"
            self.supports_json_mode = False
            return

        # 4) Ollama local
        self.llm_api_key = "ollama"
        self.llm_api_base_url = "http://localhost:11434/v1"
        self.llm_model = "qwen2.5:3b"
        self.supports_json_mode = False

    # Mock mode for testing
    llm_api_mock: bool = field(
        default_factory=lambda: os.getenv("LLM_API_MOCK", "false").lower()
        in ("true", "1")
    )
    llm_mock_response: str = field(
        default_factory=lambda: os.getenv(
            "LLM_MOCK_RESPONSE",
            json.dumps({
                "result": "mock",
                "content": "Looking to expand your AI startup globally? Localize your content for Western markets.",
                "localized_text": "AI-powered localization for Chinese entrepreneurs going global.",
                "hashtags": ["AI", "Startup", "Global"],
                "notes": "Adapted for English-speaking audience",
                "changes_made": ["Cultural reference update"],
                "core_message": "AI-powered cross-cultural localization",
                "target_audience": "Chinese entrepreneurs expanding globally",
                "key_points": ["Cultural adaptation", "Native English output"],
                "tone": "Professional",
                "unique_selling_point": "One-click CN to EN localization"
            })
        )
    )

    # App
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() in ("true", "1")
    )
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    )
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "sqlite:///./content_bridge.db"
        )
    )

    # Social API keys (for actual posting)
    x_api_key: str = field(default_factory=lambda: os.getenv("X_API_KEY", ""))
    x_api_key_secret: str = field(
        default_factory=lambda: os.getenv("X_API_KEY_SECRET", "")
    )
    x_access_token: str = field(
        default_factory=lambda: os.getenv("X_ACCESS_TOKEN", "")
    )
    x_access_token_secret: str = field(
        default_factory=lambda: os.getenv("X_ACCESS_TOKEN_SECRET", "")
    )
    x_bearer_token: str = field(
        default_factory=lambda: os.getenv("X_BEARER_TOKEN", "")
    )
    linkedin_access_token: str = field(
        default_factory=lambda: os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    )
    linkedin_user_id: str = field(
        default_factory=lambda: os.getenv("LINKEDIN_USER_ID", "")
    )
    reddit_client_id: str = field(
        default_factory=lambda: os.getenv("REDDIT_CLIENT_ID", "")
    )
    reddit_secret: str = field(default_factory=lambda: os.getenv("REDDIT_SECRET", ""))
    reddit_username: str = field(
        default_factory=lambda: os.getenv("REDDIT_USERNAME", "")
    )


settings = Settings()
