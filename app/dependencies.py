"""Shared FastAPI dependencies — DB session, auth, plan checks."""

from datetime import datetime, timezone

from fastapi import HTTPException, Request, Depends

from app.auth import decode_access_token, get_bearer_token_from_header
from app.models import User, PLANS
from app.models import SessionLocal as get_session


def get_db():
    """Yield a DB session."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


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
            from sqlalchemy import select
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
