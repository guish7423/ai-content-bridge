"""Social media API clients — X/Twitter + LinkedIn.

Mock mode by default. Enable with SOCIAL_API_MOCK=false and real API keys.
"""

import json
import os
from dataclasses import dataclass, field

from app.config import settings


class SocialAPIError(Exception):
    """Raised on social API failures after retries."""
    pass


@dataclass
class PublishResult:
    """Result of a social media publish operation."""
    platform: str
    success: bool
    post_id: str | None = None
    url: str | None = None
    error: str | None = None


# ─── X / Twitter Client ──────────────────────────────────────────────────────


class XClient:
    """X/Twitter API v2 client for posting tweets/threads."""

    def __init__(self):
        self.api_key = settings.x_api_key or ""
        self.api_key_secret = settings.x_api_key_secret or ""
        self.access_token = settings.x_access_token or ""
        self.access_token_secret = settings.x_access_token_secret or ""
        self.bearer_token = settings.x_bearer_token or ""
        self.mock = os.environ.get("SOCIAL_API_MOCK", "true").lower() in ("true", "1")

    def _is_configured(self) -> bool:
        return bool(self.bearer_token or (self.api_key and self.access_token))

    def post_tweet(self, text: str) -> PublishResult:
        """Post a single tweet."""
        if self.mock:
            return PublishResult(
                platform="x",
                success=True,
                post_id="mock_tweet_001",
                url="https://x.com/status/mock_tweet_001",
            )

        if not self._is_configured():
            return PublishResult(
                platform="x", success=False,
                error="X API not configured. Set X_BEARER_TOKEN or X_API_KEY + X_ACCESS_TOKEN",
            )

        try:
            import tweepy

            if self.bearer_token:
                client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_key_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                )
            else:
                client = tweepy.Client(
                    consumer_key=self.api_key,
                    consumer_secret=self.api_key_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                )

            response = client.create_tweet(text=text)
            tweet_id = response.data["id"]
            return PublishResult(
                platform="x",
                success=True,
                post_id=tweet_id,
                url=f"https://x.com/status/{tweet_id}",
            )
        except Exception as e:
            return PublishResult(
                platform="x", success=False, error=str(e),
            )

    def post_thread(self, tweets: list[str]) -> list[PublishResult]:
        """Post a thread (multiple tweets in sequence)."""
        results = []
        last_id = None
        for text in tweets:
            if last_id:
                text = text  # Could add reply logic here
            result = self.post_tweet(text)
            results.append(result)
            if result.success:
                last_id = result.post_id
            else:
                break  # Stop thread on failure
        return results


# ─── LinkedIn Client ─────────────────────────────────────────────────────────


class LinkedInClient:
    """LinkedIn API v2 client for sharing posts."""

    def __init__(self):
        self.access_token = settings.linkedin_access_token or ""
        self.user_id = settings.linkedin_user_id or ""
        self.mock = os.environ.get("SOCIAL_API_MOCK", "true").lower() in ("true", "1")

    def _is_configured(self) -> bool:
        return bool(self.access_token and self.user_id)

    def share_post(self, text: str, description: str = "") -> PublishResult:
        """Share a post on LinkedIn."""
        if self.mock:
            return PublishResult(
                platform="linkedin",
                success=True,
                post_id="mock_li_001",
                url="https://linkedin.com/feed/update/mock_li_001",
            )

        if not self._is_configured():
            return PublishResult(
                platform="linkedin", success=False,
                error="LinkedIn API not configured. Set LINKEDIN_ACCESS_TOKEN + LINKEDIN_USER_ID",
            )

        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }

            body = {
                "author": f"urn:li:person:{self.user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
                },
            }

            resp = httpx.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=body,
                timeout=30,
            )
            resp.raise_for_status()
            post_id = resp.headers.get("X-RestLi-Id", "unknown")
            return PublishResult(
                platform="linkedin",
                success=True,
                post_id=post_id,
                url=f"https://linkedin.com/feed/update/{post_id}",
            )
        except Exception as e:
            return PublishResult(
                platform="linkedin", success=False, error=str(e),
            )


# ─── Publish orchestration ───────────────────────────────────────────────────


def publish_content(
    platform: str,
    text: str,
    thread_texts: list[str] | None = None,
) -> PublishResult:
    """Publish bridge output to a social platform.

    Args:
        platform: "x", "linkedin", or "reddit"
        text: Main post text
        thread_texts: For X threads (list of tweet texts)

    Returns:
        PublishResult
    """
    platform = platform.lower()

    if platform == "x":
        client = XClient()
        if thread_texts:
            results = client.post_thread(thread_texts)
            if results:
                return results[0]  # Return first tweet result
        return client.post_tweet(text)

    elif platform == "linkedin":
        client = LinkedInClient()
        return client.share_post(text)

    elif platform == "reddit":
        return PublishResult(
            platform="reddit", success=False,
            error="Reddit publish not yet implemented. Use the bridge to generate content, then post manually.",
        )

    else:
        return PublishResult(
            platform=platform, success=False,
            error=f"Unknown platform: {platform}",
        )
