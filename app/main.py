"""AI Content Bridge — API server with web interface."""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.bridge import process, process_quick, generate_thread, usage
from app.social import publish_content, PublishResult
from app.config import settings
from app.models import Conversion, SessionLocal

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="AI Content Bridge",
    description="CN to EN AI content localization platform",
    version="0.1.0",
)

# Mount static files (ok if dir missing at first)
try:
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
except RuntimeError:
    pass

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ── Schemas ──────────────────────────────────────────────────────────────────

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


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "app": "AI Content Bridge"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page with the bridge tool."""
    return templates.TemplateResponse(request, "index.html",
        {"platforms": ["x", "linkedin", "reddit"]},
    )


@app.post("/bridge")
async def bridge_endpoint(req: BridgeRequest, request: Request):
    """Full pipeline. Returns HTML for HTMX, JSON for API calls."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    platforms = req.platforms or ["x", "linkedin", "reddit"]
    valid = {"x", "linkedin", "reddit", "blog"}
    for p in platforms:
        if p not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {p}")
    result = process(req.text, platforms)

    # Add thread posts for X if content exceeds 280 chars
    for p in platforms:
        content = result.platform_versions.get(p, {}).get("content", "")
        if p == "x" and content:
            thread = generate_thread(content)
            if thread:
                result.platform_versions[p]["thread_posts"] = thread

    # Save to history (non-critical)
    try:
        db = SessionLocal()
        db.add(Conversion(
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
    finally:
        try:
            db.close()
        except Exception:
            pass

    # HTMX request -> return HTML fragment
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(request, "result.html",
            {
                "original": result.original_text,
                "analysis": result.analysis,
                "localized": result.localized_text,
                "versions": result.platform_versions,
                "usage": result.usage,
            },
        )

    # API call -> return JSON
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
    """Get LLM API usage stats."""
    return usage.summary()


@app.get("/history")
async def history_endpoint(limit: int = 20):
    """Get recent content bridge history."""
    try:
        db = SessionLocal()
        rows = db.query(Conversion).order_by(Conversion.created_at.desc()).limit(limit).all()
        return [r.to_dict() for r in rows]
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        try:
            db.close()
        except Exception:
            pass


@app.post("/publish")
async def publish_endpoint(req: PublishRequest):
    """Publish bridge output to a social platform."""
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
