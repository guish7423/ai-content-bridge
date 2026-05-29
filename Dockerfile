FROM python:3.12-slim

WORKDIR /app

# Install just Python deps (no build tools needed for pure Python packages)
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx pydantic aiosqlite 'sqlalchemy[asyncio]' jinja2 python-multipart

# App code (has static/ and templates/ subdirs)
COPY app/ app/
COPY marketing/ marketing/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
