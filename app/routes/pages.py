"""Page routes — HTML pages served by Jinja2 templates."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models import PLANS
from app.dependencies import get_current_user, require_user

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(get_current_user)):
    """Landing page with the bridge tool."""
    from app.config import settings

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "platforms": ["x", "linkedin", "reddit"],
            "user": user.to_dict() if user else None,
            "mock_mode": settings.llm_api_mock or not settings.llm_api_key,
        },
    )


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing page."""
    return templates.TemplateResponse(request, "pricing.html", {"plans": PLANS})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user=Depends(require_user)):
    """User dashboard."""
    from app.services.usage import usage_remaining

    plan = PLANS.get(user.plan, PLANS["free"])
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user.to_dict(),
            "plan_details": plan,
            "usage_remaining": usage_remaining(user),
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(request, "login.html", {})


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page."""
    return templates.TemplateResponse(request, "signup.html", {})
