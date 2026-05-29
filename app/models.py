"""AI Content Bridge — SQLite models for history, users, and subscriptions."""

import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

Base = declarative_base()


class Conversion(Base):
    """Stores a content bridge conversion."""
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # Link to User
    original_text = Column(Text, nullable=False)
    analysis_json = Column(Text, default="{}")
    localized_text = Column(Text, default="")
    platform_results = Column(Text, default="{}")
    usage_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "original_text": self.original_text[:200],
            "localized_text": self.localized_text[:200],
            "platforms": list(json.loads(self.platform_results or "{}").keys()),
            "cost_usd": json.loads(self.usage_json or "{}").get("cost_usd", 0),
            "tokens": json.loads(self.usage_json or "{}").get("tokens", 0),
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


class User(Base):
    """User account with auth and subscription info."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), default="")
    api_key = Column(String(64), unique=True, nullable=True, index=True)
    plan = Column(String(50), default="free")  # free, starter, pro
    monthly_usage = Column(Integer, default=0)  # translations used this month
    usage_reset_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "plan": self.plan,
            "api_key": self.api_key,
            "monthly_usage": self.monthly_usage,
            "is_active": self.is_active,
            "stripe_customer_id": self.stripe_customer_id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


# ── Pricing Plans ────────────────────────────────────────────────────────────

PLANS = {
    "free": {
        "name": "Free",
        "price_cents": 0,
        "translations_per_month": 10,
        "social_accounts": 0,
        "stripe_price_id": None,
    },
    "starter": {
        "name": "Starter",
        "price_cents": 1999,  # $19.99/month
        "translations_per_month": 100,
        "social_accounts": 1,
        "stripe_price_id": None,  # Set via env STRIPE_STARTER_PRICE_ID
    },
    "pro": {
        "name": "Pro",
        "price_cents": 4999,  # $49.99/month
        "translations_per_month": 10000,
        "social_accounts": 3,
        "stripe_price_id": None,  # Set via env STRIPE_PRO_PRICE_ID
    },
}


engine = create_engine(settings.database_url, echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
