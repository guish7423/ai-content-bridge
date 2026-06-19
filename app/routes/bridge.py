"""Bridge routes — translate, quick, history, publish endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

from app.bridge import process, process_quick, generate_thread, usage
from app.social import publish_content
from app.models import Conversion, PLANS
from app.dependencies import get_db, get_current_user, require_user
from app.services.usage import check_usage_limit, increment_usage

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["bridge"])


# ── Schemas ────────────────────────────────────────────────────────────────

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


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/bridge")
async def bridge_endpoint(
    req: BridgeRequest,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Full pipeline. Free tier: 10/mo, Starter: 100/mo, Pro: unlimited."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    # Check usage limit for authenticated users
    if user and not check_usage_limit(user, db):
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
        db.add(
            Conversion(
                user_id=user.id if user else None,
                original_text=req.text,
                analysis_json=json.dumps(result.analysis, ensure_ascii=False),
                localized_text=result.localized_text,
                platform_results=json.dumps(
                    {k: v.get("content", "") for k, v in result.platform_versions.items()},
                    ensure_ascii=False,
                ),
                usage_json=json.dumps(result.usage),
            )
        )
        db.commit()
    except Exception:
        pass

    # HTMX response
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(
            request, "result.html",
            {
                "original": result.original_text,
                "analysis": result.analysis,
                "localized": result.localized_text,
                "versions": result.platform_versions,
                "usage": result.usage,
                "user": user.to_dict() if user else None,
            },
        )

    return {
        "original_text": result.original_text,
        "analysis": result.analysis,
        "localized_text": result.localized_text,
        "platform_versions": result.platform_versions,
        "usage": result.usage,
    }


@router.post("/quick")
async def quick_endpoint(req: QuickRequest):
    """Quick mode: single platform, returns just text."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    try:
        content = process_quick(req.text, req.platform)
        return {"platform": req.platform, "content": content}
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable. Please check your API key configuration or try again later."
        )


@router.get("/usage")
async def usage_endpoint():
    """Get global LLM API usage stats."""
    return usage.summary()


@router.get("/api/bridge/history")
@router.get("/history")
async def history_endpoint(
    limit: int = 20,
    user=Depends(require_user),
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


@router.post("/publish")
async def publish_endpoint(
    req: PublishRequest,
    user=Depends(require_user),
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
