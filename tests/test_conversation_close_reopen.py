import pytest

def test_close_requires_auth(client):
    """Should require authentication."""
    response = client.post("/api/v3/conversation/close", json={"conversation_id": "someid"})
    assert response.status_code in (401, 403)

def test_close_requires_conversation_id(client, auth_headers):
    """Should fail if conversation_id is missing."""
    response = client.post("/api/v3/conversation/close", headers=auth_headers, json={})
    assert response.status_code == 400
    assert "conversation_id" in response.text

def test_close_valid(client, auth_headers, open_conversation_id):
    """Should close an open conversation."""
    response = client.post(
        "/api/v3/conversation/close",
        headers=auth_headers,
        json={"conversation_id": open_conversation_id}
    )
    assert response.status_code == 200
    # Optionally, fetch the conversation and assert it is now closed

def test_close_already_closed(client, auth_headers, closed_conversation_id):
    """Should be idempotent or return appropriate message if already closed."""
    response = client.post(
        "/api/v3/conversation/close",
        headers=auth_headers,
        json={"conversation_id": closed_conversation_id}
    )
    assert response.status_code in (200, 409)
    # If 200, check for a message indicating already closed

def test_close_nonexistent_conversation(client, auth_headers):
    """Should return 404 or error for nonexistent conversation."""
    response = client.post(
        "/api/v3/conversation/close",
        headers=auth_headers,
        json={"conversation_id": "nonexistentid"}
    )
    assert response.status_code in (404, 400)
    # Optionally, check error message

def test_close_permission_denied(client, other_auth_headers, open_conversation_id):
    """Should return 403 if user is not permitted to close the conversation."""
    response = client.post(
        "/api/v3/conversation/close",
        headers=other_auth_headers,
        json={"conversation_id": open_conversation_id}
    )
    assert response.status_code == 403

def test_reopen_requires_auth(client):
    """Should require authentication."""
    response = client.post("/api/v3/conversation/reopen", json={"conversation_id": "someid"})
    assert response.status_code in (401, 403)

def test_reopen_requires_conversation_id(client, auth_headers):
    """Should fail if conversation_id is missing."""
    response = client.post("/api/v3/conversation/reopen", headers=auth_headers, json={})
    assert response.status_code == 400
    assert "conversation_id" in response.text

def test_reopen_valid(client, auth_headers, closed_conversation_id):
    """Should reopen a closed conversation."""
    response = client.post(
        "/api/v3/conversation/reopen",
        headers=auth_headers,
        json={"conversation_id": closed_conversation_id}
    )
    assert response.status_code == 200
    # Optionally, fetch the conversation and assert it is open now

def test_reopen_already_open(client, auth_headers, open_conversation_id):
    """Should be idempotent or return appropriate message if conversation is already open."""
    response = client.post(
        "/api/v3/conversation/reopen",
        headers=auth_headers,
        json={"conversation_id": open_conversation_id}
    )
    assert response.status_code in (200, 409)
    # If 200, check for a message indicating already open

def test_reopen_nonexistent_conversation(client, auth_headers):
    """Should return 404 or error for nonexistent conversation."""
    response = client.post(
        "/api/v3/conversation/reopen",
        headers=auth_headers,
        json={"conversation_id": "nonexistentid"}
    )
    assert response.status_code in (404, 400)
    # Check error message if desired

def test_reopen_permission_denied(client, other_auth_headers, closed_conversation_id):
    """Should return 403 if user is not permitted to reopen the conversation."""
    response = client.post(
        "/api/v3/conversation/reopen",
        headers=other_auth_headers,
        json={"conversation_id": closed_conversation_id}
    )
    assert response.status_code == 403