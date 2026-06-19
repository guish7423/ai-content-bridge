"""Auth routes — signup, login, logout, profile, API key management."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    generate_api_key,
)
from app.models import User, PLANS
from app.dependencies import get_db, require_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码至少 8 个字符")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Helpers ────────────────────────────────────────────────────────────────

def _set_auth_cookie(redirect: "RedirectResponse", token: str) -> "RedirectResponse":
    """Set secure auth cookie with consistent settings."""
    redirect.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800,  # 7 days
        path="/",
    )
    return redirect


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/signup")
async def signup(req: SignupRequest, db=Depends(get_db)):
    """Create a new account (free plan)."""
    existing = db.execute(
        select(User).where(User.email == req.email)
    ).scalar_one_or_none()
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


@router.post("/login")
async def login(req: LoginRequest, db=Depends(get_db)):
    """Log in and get a JWT token."""
    result = db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(user.id, user.email)
    return {"token": token, "user": user.to_dict()}


@router.get("/me")
async def get_profile(user: User = Depends(require_user)):
    """Get current user profile and usage info."""
    plan = PLANS.get(user.plan, PLANS["free"])
    from app.services.usage import usage_remaining

    return {
        **user.to_dict(),
        "plan_details": plan,
        "usage_remaining": usage_remaining(user),
    }


@router.post("/regenerate-key")
async def regenerate_key(
    user: User = Depends(require_user), db=Depends(get_db)
):
    """Generate a new API key."""
    user.api_key = generate_api_key()
    db.commit()
    return {"api_key": user.api_key}


@router.post("/change-plan")
async def change_plan(
    plan: str,
    user: User = Depends(require_user),
    db=Depends(get_db),
):
    """Change user's plan (admin use only; Stripe handles upgrades)."""
    if plan not in PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan. Options: {list(PLANS.keys())}",
        )
    user.plan = plan
    user.monthly_usage = 0
    user.usage_reset_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": f"Plan changed to {plan}", "plan": plan}


# ── HTMX Form Endpoints ────────────────────────────────────────────────────

@router.post("/login-form")
async def login_form(req: LoginRequest, db=Depends(get_db)):
    """Login form endpoint for HTMX — returns redirect with cookie."""
    result = login(req, db)
    token = result["token"]
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(
        key="token", value=token, httponly=True, secure=True,
        samesite="lax", max_age=604800, path="/",
    )
    return redirect


@router.post("/signup-form")
async def signup_form(req: SignupRequest, db=Depends(get_db)):
    """Signup form endpoint for HTMX — returns redirect with cookie."""
    result = signup(req, db)
    token = result["token"]
    redirect = RedirectResponse(url="/dashboard", status_code=302)
    redirect.set_cookie(
        key="token", value=token, httponly=True, secure=True,
        samesite="lax", max_age=604800, path="/",
    )
    return redirect


@router.post("/logout")
async def logout():
    """Logout — clear token cookie."""
    redirect = RedirectResponse(url="/", status_code=302)
    redirect.delete_cookie("token", path="/")
    return redirect
