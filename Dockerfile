FROM python:3.12-slim
# AI Content Bridge - production image

WORKDIR /app


# Install system deps for native packages (bcrypt etc.)
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*
# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (includes static/ and templates/)
COPY app/ app/
# Remove marketing/ from .dockerignore or remove this line

EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
