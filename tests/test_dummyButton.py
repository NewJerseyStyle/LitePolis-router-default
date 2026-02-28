import pytest

def test_dummyButton_get_success(client):
    """GET /api/v3/dummyButton should return 200 and a dummy message."""
    response = client.get("/api/v3/dummyButton?button=addAnotherSiteIdFromSettings")
    assert response.status_code == 200
    data = response.json()
    # The actual implementation just shows an alert "coming soon"
    # So, expect {"message": "coming soon"} or similar
    assert "message" in data
    assert "coming soon" in data["message"].lower()

def test_dummyButton_query_param_required(client):
    """GET /api/v3/dummyButton without button param should return 400 (button required)."""
    response = client.get("/api/v3/dummyButton")
    assert response.status_code == 400

def test_dummyButton_query_param_arbitrary_value(client):
    """GET /api/v3/dummyButton with arbitrary button value should still return dummy message."""
    response = client.get("/api/v3/dummyButton?button=testValue")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "coming soon" in data["message"].lower()

def test_dummyButton_invalid_method(client):
    """PUT /api/v3/dummyButton should return 405 Method Not Allowed."""
    response = client.put("/api/v3/dummyButton?button=addAnotherSiteIdFromSettings")
    assert response.status_code == 405

def test_dummyButton_idempotent_get(client):
    """GET /api/v3/dummyButton should be idempotent (repeatable without side effects)."""
    resp1 = client.get("/api/v3/dummyButton?button=addAnotherSiteIdFromSettings")
    resp2 = client.get("/api/v3/dummyButton?button=addAnotherSiteIdFromSettings")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()