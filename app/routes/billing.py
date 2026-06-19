"""Billing routes — Stripe checkout, webhook, billing portal."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.dependencies import get_db, require_user
from app.services.billing import (
    create_checkout_session,
    create_billing_portal_url,
    get_stripe_event,
    stripe_available,
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
)

router = APIRouter(prefix="/api/stripe", tags=["billing"])


# ── Schemas ────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str = "starter"  # starter or pro
    success_url: str = ""
    cancel_url: str = ""


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/create-checkout")
async def create_checkout(
    req: CheckoutRequest,
    user=Depends(require_user),
):
    """Create a Stripe Checkout session for subscription."""
    if req.plan not in ("starter", "pro"):
        raise HTTPException(status_code=400, detail="Invalid plan")

    try:
        result = await create_checkout_session(
            plan=req.plan,
            customer_email=user.email,
            user_id=user.id,
            success_url=req.success_url or None,
            cancel_url=req.cancel_url or None,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request, db=Depends(get_db)):
    """Handle Stripe webhook events."""
    if not stripe_available():
        return {"status": "skipped", "message": "Stripe not configured"}

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = get_stripe_event(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    handlers = {
        "checkout.session.completed": handle_checkout_completed,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(event, db)

    return {"status": "ok"}


@router.get("/billing-portal")
async def billing_portal(user=Depends(require_user)):
    """Redirect to Stripe Billing Portal — gracefully handle missing config."""
    if not stripe_available():
        return {"url": "/pricing", "message": "Stripe billing portal coming soon."}

    if not user.stripe_customer_id:
        return {"url": "/pricing"}

    try:
        url = await create_billing_portal_url(user.stripe_customer_id)
        if url:
            return {"url": url}
        return {"url": "/pricing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
