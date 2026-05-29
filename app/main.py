"""AI Content Bridge — API server with auth, billing, and web interface."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.bridge import process, process_quick, generate_thread, usage
from app.social import publish_content, PublishResult
from app.config import settings
from app.models import Conversion, User, PLANS, SessionLocal
from app.auth import (
    hash_password, verify_password, create_access_token, decode_access_token,
    generate_api_key, get_bearer_token_from_header,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="AI Content Bridge",
    description="CN to EN AI content localization platform",
    version="0.2.1",
)
# Global error handler to debug production issues
# Global error handler to debug production issues
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions and return full error info."""
    import traceback
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "traceback": traceback.format_exc().split(chr(10)),
            "type": type(exc).__name__,
        }
    )


# Mount static files
try:
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
except RuntimeError:
    pass

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ── DB Dependency ──────────────────────────────────────────────────────────

def get_db():
    """Yield a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth Dependency ────────────────────────────────────────────────────────

def get_current_user(request: Request, db=Depends(get_db)) -> User | None:
    """Get current user from JWT cookie or Authorization header."""
    user = None

    # Try JWT cookie
    token = request.cookies.get("token")
    if token:
        payload = decode_access_token(token)
        if payload:
            user = db.get(User, int(payload["sub"]))

    # Try Authorization: Bearer header
    if not user:
        auth = request.headers.get("Authorization")
        key = get_bearer_token_from_header(auth)
        if key:
            result = db.execute(select(User).where(User.api_key == key))
            user = result.scalar_one_or_none()

    return user


def require_user(user: User | None = Depends(get_current_user)) -> User:
    """Require an authenticated user. Raises 401 if missing."""
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_plan(plan: str):
    """Dependency factory: require user to have at least this plan level."""
    plan_order = {"free": 0, "starter": 1, "pro": 2}

    def checker(user: User = Depends(require_user)):
        if plan_order.get(user.plan, 0) < plan_order.get(plan, 0):
            raise HTTPException(
                status_code=402,
                detail=f"Upgrade to {plan} plan required. Current plan: {user.plan}",
            )
        return user
    return checker


# ── Schemas ────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BridgeRequest(BaseModel):
    text: str
    platforms: list[str] | None = None


class QuickRequest(BaseModel):
    text: str
    platform: str = "x"


class PublishRequest(BaseModel):
    text: str
    platform: str = "x"
    thread_texts: list[str] | None = None


class CheckoutRequest(BaseModel):
    plan: str = "starter"  # starter or pro
    success_url: str = ""
    cancel_url: str = ""


# ── Usage Check ────────────────────────────────────────────────────────────

def check_usage_limit(user: User, db) -> bool:
    """Check if user has exceeded their monthly translation limit."""
    plan = PLANS.get(user.plan, PLANS["free"])
    limit = plan["translations_per_month"]

    # Reset usage if new month
    now = datetime.now(timezone.utc)
    if user.usage_reset_at and user.usage_reset_at.month != now.month:
        user.monthly_usage = 0
        user.usage_reset_at = now
        db.commit()

    return user.monthly_usage < limit


def increment_usage(user: User, db):
    """Increment user's monthly usage counter."""
    user.monthly_usage = (user.monthly_usage or 0) + 1
    db.commit()


# ── Auth Routes ────────────────────────────────────────────────────────────

@app.post("/api/auth/signup")
async def signup(req: SignupRequest, db=Depends(get_db)):
    """Create a new account (free plan)."""
    existing = db.execute(select(User).where(User.email == req.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        name=req.name,
        api_key=generate_api_key(),
        plan="free",
        monthly_usage=0,
        usage_reset_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return {
        "token": token,
        "user": user.to_dict(),
        "message": "Account created! You're on the Free plan (10 translations/mo).",
    }


@app.post("/api/auth/login")
async def login(req: LoginRequest, db=Depends(get_db)):
    """Log in and get a JWT token."""
    result = db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(user.id, user.email)
    return {
        "token": token,
        "user": user.to_dict(),
    }


@app.get("/api/auth/me")
async def get_profile(user: User = Depends(require_user)):
    """Get current user profile and usage info."""
    plan = PLANS.get(user.plan, PLANS["free"])
    return {
        **user.to_dict(),
        "plan_details": plan,
        "usage_remaining": max(0, plan["translations_per_month"] - (user.monthly_usage or 0)),
    }


@app.post("/api/auth/regenerate-key")
async def regenerate_key(user: User = Depends(require_user), db=Depends(get_db)):
    """Generate a new API key."""
    user.api_key = generate_api_key()
    db.commit()
    return {"api_key": user.api_key}


@app.post("/api/auth/change-plan")
async def change_plan(
    plan: str,
    user: User = Depends(require_user),
    db=Depends(get_db),
):
    """Change user's plan (admin use only now; Stripe handles upgrade)."""
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Options: {list(PLANS.keys())}")
    user.plan = plan
    user.monthly_usage = 0
    user.usage_reset_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Plan changed to {plan}", "plan": plan}


# ── Stripe Routes ──────────────────────────────────────────────────────────

@app.post("/api/stripe/create-checkout")
async def create_checkout(req: CheckoutRequest, user: User = Depends(require_user)):
    """Create a Stripe Checkout session for subscription."""
    if req.plan not in ("starter", "pro"):
        raise HTTPException(status_code=400, detail="Invalid plan")

    # Graceful mode: if Stripe not configured, inform user
    if not settings.stripe_api_key or settings.stripe_api_key == "sk_test_dummy":
        return {
            "url": "/pricing?stripe=coming-soon",
            "message": "Stripe payments coming soon. Your account is on Free plan for now.",
        }

    stripe.api_key = settings.stripe_api_key
    price_ids = {
        "starter": os.getenv("STRIPE_STARTER_PRICE_ID", ""),
        "pro": os.getenv("STRIPE_PRO_PRICE_ID", ""),
    }
    price_id = price_ids.get(req.plan)
    if not price_id:
        raise HTTPException(status_code=500, detail="Stripe price ID not configured")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=user.email,
            client_reference_id=str(user.id),
            success_url=req.success_url or os.getenv("STRIPE_SUCCESS_URL", f"{settings.app_url}/dashboard?upgrade=success"),
            cancel_url=req.cancel_url or os.getenv("STRIPE_CANCEL_URL", f"{settings.app_url}/pricing"),
            metadata={"user_id": str(user.id), "plan": req.plan},
        )
        return {"url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


async def stripe_webhook(request: Request, db=Depends(get_db)):
    """Handle Stripe webhook events — gracefully skip if not configured."""
    if not settings.stripe_api_key or settings.stripe_api_key == "sk_test_dummy":
        return {"status": "skipped", "message": "Stripe not configured"}
    import stripe
    stripe.api_key = settings.stripe_api_key
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})
    if event_type == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")
        plan = data.get("metadata", {}).get("plan", "starter")
        if user_id:
            user = db.get(User, int(user_id))
            if user:
                user.plan = plan
                user.stripe_customer_id = customer_id
                user.stripe_subscription_id = subscription_id
                user.monthly_usage = 0
                user.usage_reset_at = datetime.now(timezone.utc)
                db.commit()
    elif event_type == "customer.subscription.updated":
        customer_id = data.get("customer")
        status = data.get("status")
        items = data.get("items", {}).get("data", [])
        result = db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()
        if user and status == "active":
            for item in items:
                price_id = item.get("price", {}).get("id", "")
                if price_id == os.getenv("STRIPE_STARTER_PRICE_ID"):
                    user.plan = "starter"
                elif price_id == os.getenv("STRIPE_PRO_PRICE_ID"):
                    user.plan = "pro"
            db.commit()
        elif user and status in ("canceled", "incomplete_expired"):
            user.plan = "free"
            user.stripe_subscription_id = None
            db.commit()
    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        result = db.execute(select(User).where(User.stripe_customer_id == customer_id))
        user = result.scalar_one_or_none()
        if user:
            user.plan = "free"
            user.stripe_subscription_id = None
            db.commit()
    return {"status": "ok"}


async def billing_portal(user: User = Depends(require_user)):
    """Redirect to Stripe Billing Portal — gracefully handle missing config."""
    if not settings.stripe_api_key or settings.stripe_api_key == "sk_test_dummy":
        return {"url": "/pricing", "message": "Stripe billing portal coming soon."}
    if not user.stripe_customer_id:
        return {"url": "/pricing"}
    import stripe
    stripe.api_key = settings.stripe_api_key
    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{settings.app_url}/dashboard",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


# ── Public Routes ──────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "app": "AI Content Bridge", "version": "0.2.0"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User | None = Depends(get_current_user)):
    """Landing page with the bridge tool."""
    return templates.TemplateResponse(request, "index.html", {
        "platforms": ["x", "linkedin", "reddit"],
        "user": user.to_dict() if user else None,
    })


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    return templates.TemplateResponse(request, "pricing.html", {
        "plans": PLANS,
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: User = Depends(require_user)):
    """User dashboard."""
    plan = PLANS.get(user.plan, PLANS["free"])
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user.to_dict(),
        "plan_details": plan,
        "usage_remaining": max(0, plan["translations_per_month"] - (user.monthly_usage or 0)),
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(request, "login.html", {})


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page."""
    return templates.TemplateResponse(request, "signup.html", {})


# ── API Routes ─────────────────────────────────────────────────────────────

@app.post("/bridge")
async def bridge_endpoint(
    req: BridgeRequest,
    request: Request,
    user: User | None = Depends(get_current_user),
    db=Depends(get_db),
):
    """Full pipeline. Free tier: 10/mo, Starter: 100/mo, Pro: unlimited."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    # Check usage limit for authenticated users
    if user:
        if not check_usage_limit(user, db):
            plan = PLANS.get(user.plan, PLANS["free"])
            raise HTTPException(
                status_code=429,
                detail=f"Monthly limit reached ({plan['translations_per_month']}/mo). Upgrade to continue.",
            )

    platforms = req.platforms or ["x", "linkedin", "reddit"]
    valid = {"x", "linkedin", "reddit", "blog"}
    for p in platforms:
        if p not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {p}")

    result = process(req.text, platforms)

    # Generate thread for X if needed
    for p in platforms:
        content = result.platform_versions.get(p, {}).get("content", "")
        if p == "x" and content:
            thread = generate_thread(content)
            if thread:
                result.platform_versions[p]["thread_posts"] = thread

    # Track usage
    if user:
        increment_usage(user, db)

    # Save to history
    try:
        db.add(Conversion(
            user_id=user.id if user else None,
            original_text=req.text,
            analysis_json=json.dumps(result.analysis, ensure_ascii=False),
            localized_text=result.localized_text,
            platform_results=json.dumps(
                {k: v.get("content", "") for k, v in result.platform_versions.items()},
                ensure_ascii=False,
            ),
            usage_json=json.dumps(result.usage),
        ))
        db.commit()
    except Exception:
        pass

    # HTMX response
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(request, "result.html", {
            "original": result.original_text,
            "analysis": result.analysis,
            "localized": result.localized_text,
            "versions": result.platform_versions,
            "usage": result.usage,
            "user": user.to_dict() if user else None,
        })

    return {
        "original_text": result.original_text,
        "analysis": result.analysis,
        "localized_text": result.localized_text,
        "platform_versions": result.platform_versions,
        "usage": result.usage,
    }


@app.post("/quick")
async def quick_endpoint(req: QuickRequest):
    """Quick mode: single platform, returns just text."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    content = process_quick(req.text, req.platform)
    return {"platform": req.platform, "content": content}


@app.get("/usage")
async def usage_endpoint():
    """Get global LLM API usage stats."""
    return usage.summary()


@app.get("/api/bridge/history")
@app.get("/history")
async def history_endpoint(
    limit: int = 20,
    user: User = Depends(require_user),
    db=Depends(get_db),
):
    """Get user's bridge history."""
    rows = (
        db.query(Conversion)
        .filter(Conversion.user_id == user.id)
        .order_by(Conversion.created_at.desc())
        .limit(limit)
        .all()
    )
    return [r.to_dict() for r in rows]

@app.post("/publish")
async def publish_endpoint(
    req: PublishRequest,
    user: User = Depends(require_user),
):
    """Publish bridge output to a social platform (Starter plan+)."""
    if user.plan == "free":
        raise HTTPException(
            status_code=402,
            detail="Social publishing requires Starter plan ($19/mo). Upgrade in dashboard.",
        )

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    result = publish_content(req.platform, req.text, req.thread_texts)
    return {
        "platform": result.platform,
        "success": result.success,
        "post_id": result.post_id,
        "url": result.url,
        "error": result.error,
    }


# ── Auth Token Redirect (for HTMX / spa-like flow) ─────────────────────────

@app.post("/api/auth/login-form")
async def login_form(
    req: LoginRequest,
    request: Request,
    db=Depends(get_db),
):
    """Login form endpoint for HTMX — returns redirect with cookie."""
    result = await login(req, db)
    token = result["token"]
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(key="token", value=token, httponly=True, max_age=604800, samesite="lax")
    return redirect


@app.post("/api/auth/signup-form")
async def signup_form(
    req: SignupRequest,
    request: Request,
    db=Depends(get_db),
):
    """Signup form endpoint for HTMX — returns redirect with cookie."""
    result = await signup(req, db)
    token = result["token"]
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(key="token", value=token, httponly=True, max_age=604800, samesite="lax")
    return redirect


@app.post("/api/auth/logout")
async def logout():
    """Logout — clear token cookie."""
    redirect = RedirectResponse(url="/", status_code=302)
    redirect.delete_cookie("token")
    return redirect


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
