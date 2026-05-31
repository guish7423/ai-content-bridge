def test_signup_and_login(client):
    resp = client.post("/api/auth/signup", json={
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["plan"] == "free"
    assert "token" in data

    token = data["token"]

    resp = client.get("/api/auth/me", cookies={"token": token})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"

    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_signup_duplicate(client):
    client.post("/api/auth/signup", json={
        "email": "dup@example.com", "password": "pass123",
    })
    resp = client.post("/api/auth/signup", json={
        "email": "dup@example.com", "password": "pass456",
    })
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]


def test_login_wrong_password(client):
    client.post("/api/auth/signup", json={
        "email": "auth@test.com", "password": "correct",
    })
    resp = client.post("/api/auth/login", json={
        "email": "auth@test.com", "password": "wrong",
    })
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_regenerate_api_key(client):
    client.post("/api/auth/signup", json={
        "email": "keytest@test.com", "password": "pass",
    })
    resp = client.post("/api/auth/login", json={
        "email": "keytest@test.com", "password": "pass",
    })
    token = resp.json()["token"]

    resp = client.post("/api/auth/regenerate-key", cookies={"token": token})
    assert resp.status_code == 200
    assert len(resp.json()["api_key"]) > 10


def test_dashboard_requires_auth(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code != 200
