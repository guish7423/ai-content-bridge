def test_bridge_mock(client):
    client.post("/api/auth/signup", json={
        "email": "bridge@test.com", "password": "pass",
    })
    resp = client.post("/api/auth/login", json={
        "email": "bridge@test.com", "password": "pass",
    })
    token = resp.json()["token"]

    resp = client.post("/bridge", json={
        "text": "Hello world, this is a test message.",
        "platforms": ["x", "linkedin"],
    }, cookies={"token": token})
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis" in data
    assert "localized_text" in data
    assert "platform_versions" in data


def test_bridge_requires_text(client):
    resp = client.post("/bridge", json={"text": ""})
    assert resp.status_code == 400


def test_quick_endpoint(client):
    resp = client.post("/quick", json={
        "text": "Quick test message",
        "platform": "x",
    })
    assert resp.status_code == 200
    assert "content" in resp.json()


def test_bridge_history(client):
    resp = client.post("/api/auth/signup", json={
        "email": "history@test.com", "password": "pass",
    })
    token = resp.json()["token"]

    client.post("/bridge", json={
        "text": "History test post", "platforms": ["blog"],
    }, cookies={"token": token})

    resp = client.get("/api/bridge/history", cookies={"token": token})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
