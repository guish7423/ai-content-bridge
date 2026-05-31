def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "AI Content Bridge"


def test_landing_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI Content Bridge" in resp.text


def test_pricing_page(client):
    resp = client.get("/pricing")
    assert resp.status_code == 200
    assert "Free" in resp.text
    assert "Starter" in resp.text
    assert "Pro" in resp.text


def test_login_page(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_signup_page(client):
    resp = client.get("/signup")
    assert resp.status_code == 200
