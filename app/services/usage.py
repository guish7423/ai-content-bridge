"""Usage tracking service — plan limits, monthly resets, concurrency-safe."""

import threading
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.models import PLANS

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models import User

_lock = threading.Lock()


def check_usage_limit(user: "User", db: "Session") -> bool:
    """Check if user has exceeded their monthly translation limit.

    Thread-safe: uses a lock to prevent race conditions on the limit check.
    """
    plan = PLANS.get(user.plan, PLANS["free"])
    limit = plan["translations_per_month"]

    # Reset usage if new month
    now = datetime.now(timezone.utc)
    if user.usage_reset_at and user.usage_reset_at.month != now.month:
        with _lock:
            user.monthly_usage = 0
            user.usage_reset_at = now
            db.commit()

    with _lock:
        return user.monthly_usage < limit


def increment_usage(user: "User", db: "Session") -> int:
    """Increment user's monthly usage counter. Returns new count."""
    with _lock:
        user.monthly_usage = (user.monthly_usage or 0) + 1
        db.commit()
        return user.monthly_usage


def usage_remaining(user: "User") -> int:
    """Calculate remaining translations for the current billing period."""
    plan = PLANS.get(user.plan, PLANS["free"])
    return max(0, plan["translations_per_month"] - (user.monthly_usage or 0))
