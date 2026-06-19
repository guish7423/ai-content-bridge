import os
import pytest
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_bridge.db"
os.environ["SECRET_KEY"] = "test-secret-key-not-default-32char!!"
os.environ["LLM_API_BASE_URL"] = "http://mock"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_API_MOCK"] = "true"
os.environ["APP_URL"] = "http://localhost:8000"

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def pytest_unconfigure():
    db_path = Path("test_bridge.db")
    if db_path.exists():
        db_path.unlink()
