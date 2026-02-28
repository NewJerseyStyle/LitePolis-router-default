import pytest

def test_conversationStats_requires_auth(client):
    """Should require authentication to access conversation stats."""
    response = client.get("/api/v3/conversationStats")
    assert response.status_code in (401, 403)

def test_conversationStats_missing_conversation_id(client, auth_headers):
    """Should fail with 400 if conversation_id is missing."""
    response = client.get("/api/v3/conversationStats", headers=auth_headers)
    assert response.status_code == 400

def test_conversationStats_success(client, auth_headers, conversation_id):
    """Should return stats for a valid conversation."""
    response = client.get(
        f"/api/v3/conversationStats?conversation_id={conversation_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    stats = response.json()
    # Check for expected keys (customize as per your schema)
    assert "conversation_id" in stats
    assert stats["conversation_id"] == conversation_id
    assert "num_participants" in stats
    assert "num_comments" in stats

def test_conversationStats_invalid_conversation_id(client, auth_headers):
    """Should return 404 or 400 for an invalid conversation_id."""
    response = client.get(
        "/api/v3/conversationStats?conversation_id=nonexistent_id",
        headers=auth_headers
    )
    assert response.status_code in (400, 404)

def test_conversationStats_permission_denied(client, other_auth_headers, conversation_id):
    """Should return 403 if user is not allowed to view stats."""
    response = client.get(
        f"/api/v3/conversationStats?conversation_id={conversation_id}",
        headers=other_auth_headers
    )
    assert response.status_code == 403

def test_conversationStats_extra_params_ignored(client, auth_headers, conversation_id):
    """Should ignore unrelated extra query parameters."""
    response = client.get(
        f"/api/v3/conversationStats?conversation_id={conversation_id}&foo=bar",
        headers=auth_headers
    )
    assert response.status_code == 200
    stats = response.json()
    assert stats["conversation_id"] == conversation_id