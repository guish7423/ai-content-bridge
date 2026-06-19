"""Billing service — Stripe checkout, webhook handling, plan management."""

import os
from datetime import datetime, timezone

from app.config import settings


def stripe_available() -> bool:
    """Check if Stripe is properly configured."""
    return bool(settings.stripe_api_key) and settings.stripe_api_key != "sk_test_dummy"


def get_price_id(plan: str) -> str | None:
    """Get Stripe price ID for a plan."""
    price_ids = {
        "starter": os.getenv("STRIPE_STARTER_PRICE_ID", ""),
        "pro": os.getenv("STRIPE_PRO_PRICE_ID", ""),
    }
    return price_ids.get(plan)


async def create_checkout_session(
    plan: str,
    customer_email: str,
    user_id: int,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict:
    """Create a Stripe Checkout session for subscription.

    Returns dict with 'url' and 'session_id'.
    If Stripe is not configured, returns a graceful message.
    """
    import stripe

    if not stripe_available():
        return {
            "url": "/pricing?stripe=coming-soon",
            "message": "Stripe payments coming soon. Your account is on Free plan for now.",
        }

    # Use price_id from PLANS dict (loaded from env at startup)
    from app.models import PLANS
    plan_config = PLANS.get(plan)
    price_id = plan_config["stripe_price_id"] if plan_config else None
    if not price_id:
        raise ValueError(f"Stripe price ID not configured for plan: {plan}")

    stripe.api_key = settings.stripe_api_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=customer_email,
        client_reference_id=str(user_id),
        success_url=success_url
        or os.getenv("STRIPE_SUCCESS_URL", f"{settings.app_url}/dashboard?upgrade=success"),
        cancel_url=cancel_url
        or os.getenv("STRIPE_CANCEL_URL", f"{settings.app_url}/pricing"),
        metadata={"user_id": str(user_id), "plan": plan},
    )
    return {"url": session.url, "session_id": session.id}


def get_stripe_event(payload: bytes, sig_header: str):
    """Construct and verify a Stripe webhook event."""
    import stripe

    stripe.api_key = settings.stripe_api_key
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.stripe_webhook_secret
    )


async def handle_checkout_completed(event_data: dict, db) -> None:
    """Handle checkout.session.completed webhook event."""
    from app.models import User

    data = event_data.get("object", {})
    event_id = event_data.get("id", "")
    user_id = data.get("metadata", {}).get("user_id")
    subscription_id = data.get("subscription")
    customer_id = data.get("customer")
    plan = data.get("metadata", {}).get("plan", "starter")

    # Idempotency check — skip if already processed
    if event_id:
        existing = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if existing and existing.stripe_subscription_id == subscription_id and existing.plan == plan:
            return

    if user_id:
        user = db.get(User, int(user_id))
        if user:
            user.plan = plan
            user.stripe_customer_id = customer_id
            user.stripe_subscription_id = subscription_id
            user.monthly_usage = 0
            user.usage_reset_at = datetime.now(timezone.utc)
            db.commit()


async def handle_subscription_updated(event_data: dict, db) -> None:
    """Handle customer.subscription.updated webhook event."""
    from app.models import User

    data = event_data.get("object", {})
    customer_id = data.get("customer")
    status = data.get("status")
    items = data.get("items", {}).get("data", [])

    if not customer_id:
        return

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        return

    if status == "active":
        for item in items:
            price_id = item.get("price", {}).get("id", "")
            configured_ids = {
                os.getenv("STRIPE_STARTER_PRICE_ID", ""): "starter",
                os.getenv("STRIPE_PRO_PRICE_ID", ""): "pro",
            }
            if price_id in configured_ids:
                user.plan = configured_ids[price_id]
        db.commit()
    elif status in ("canceled", "incomplete_expired"):
        user.plan = "free"
        user.stripe_subscription_id = None
        db.commit()


async def handle_subscription_deleted(event_data: dict, db) -> None:
    """Handle customer.subscription.deleted webhook event."""
    from app.models import User

    customer_id = event_data.get("object", {}).get("customer")
    if not customer_id:
        return

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        user.plan = "free"
        user.stripe_subscription_id = None
        # Reset usage to prevent immediately hitting free tier limit
        from app.models import PLANS
        if user.monthly_usage and user.monthly_usage > PLANS["free"]["translations_per_month"]:
            user.monthly_usage = 0
            user.usage_reset_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        db.commit()


async def create_billing_portal_url(customer_id: str) -> str | None:
    """Create a Stripe Billing Portal session URL."""
    import stripe

    if not stripe_available() or not customer_id:
        return None

    stripe.api_key = settings.stripe_api_key
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.app_url}/dashboard",
    )
    return session.url
