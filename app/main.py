"""AI Content Bridge — API server with auth, billing, and web interface."""

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="AI Content Bridge",
    description="CN to EN AI content localization platform",
    version="0.4.0",
)


# ── Global Exception Handler ───────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions — return detail in debug mode, safe message in production."""
    if settings.debug:
        import traceback

        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "traceback": traceback.format_exc().split("\n"),
                "type": type(exc).__name__,
            },
        )
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# ── Static files ───────────────────────────────────────────────────────────

try:
    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="static",
    )
except RuntimeError:
    pass

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ── CORS ───────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────

# Health check (before other routes)
@app.get("/health")
async def health():
    return {"status": "ok", "app": "AI Content Bridge", "version": "0.4.0"}


# CrossWave landing page
@app.get("/crosswave", response_class=HTMLResponse)
async def crosswave_landing():
    """CrossWave company landing page."""
    html = (BASE_DIR / "static" / "crosswave" / "index.html").read_text()
    return HTMLResponse(content=html)


# Waitlist
@app.post("/api/waitlist")
async def waitlist(request: Request):
    """Capture waitlist email."""
    try:
        data = await request.json()
        email = data.get("email", "")
        if not email or "@" not in email:
            return {"status": "error", "message": "Invalid email"}
        from datetime import datetime, timezone

        waitlist_file = BASE_DIR.parent / "waitlist.csv"
        with open(str(waitlist_file), "a") as f:
            f.write(f"{email},{datetime.now(timezone.utc).isoformat()}\n")
        return {"status": "ok", "message": "You're on the list!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Mount route modules
from app.models import init_db

init_db()  # Ensure tables exist
from app.routes.auth import router as auth_router
from app.routes.bridge import router as bridge_router
from app.routes.billing import router as billing_router
from app.routes.pages import router as pages_router

app.include_router(auth_router)
app.include_router(bridge_router)
app.include_router(billing_router)
app.include_router(pages_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
