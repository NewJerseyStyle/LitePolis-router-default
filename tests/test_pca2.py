import pytest

def create_conversation(client, auth_headers, **kwargs):
    """Helper to create a conversation and return its ID."""
    data = {"is_draft": True, "is_active": True}
    data.update(kwargs)
    response = client.post("/api/v3/conversations", headers=auth_headers, json=data)
    assert response.status_code == 200
    return response.json()["conversation_id"]

def test_pca2_with_new_conversation(client, auth_headers):
    """End-to-end: create a conversation, then call /api/v3/math/pca2."""
    conversation_id = create_conversation(client, auth_headers, topic="PCA Test")
    # Optionally: seed participants or votes if your implementation requires it for PCA
    response = client.get("/api/v3/math/pca2", params={"conversation_id": conversation_id})
    # Expect 200, but actual content may depend on whether extra setup is needed (e.g., enough votes)
    assert response.status_code == 200
    data = response.json()
    # Make assertions based on expected content, e.g. keys present even with 0 votes
    assert "projection" in data or "clusters" in data  # Adjust to your real output

def test_create_and_update_conversation(client, auth_headers):
    """Create, then update a conversation."""
    conversation_id = create_conversation(client, auth_headers, topic="Initial", description="To update")
    update_data = {
        "conversation_id": conversation_id,
        "topic": "Updated Topic",
        "description": "Updated description.",
    }
    response = client.put("/api/v3/conversations", headers=auth_headers, json=update_data)
    assert response.status_code == 200
    # Optionally GET and assert fields are updated

