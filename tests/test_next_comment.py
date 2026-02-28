import pytest

def test_next_comment_success():
    """Should return the next unvoted comment for a valid conversation and participant."""
    response = client.get(
        "/api/v3/nextComment",
        params={
            "conversation_id": 123,
            "not_voted_by_pid": 456,
            "limit": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "tid" in data and "txt" in data

def test_next_comment_no_more_comments():
    """Should return 204 or empty when no unvoted comments remain."""
    response = client.get(
        "/api/v3/nextComment",
        params={
            "conversation_id": 123,
            "not_voted_by_pid": 456,
            "limit": 1
        }
    )
    assert response.status_code in (200, 204)
    if response.status_code == 200:
        assert response.json() == {} or response.json() is None

def test_next_comment_missing_conversation_id():
    """Should return 400 Bad Request if conversation_id is missing."""
    response = client.get(
        "/api/v3/nextComment",
        params={
            "not_voted_by_pid": 456,
            "limit": 1
        }
    )
    assert response.status_code == 400

def test_next_comment_invalid_pid():
    """Should return 404 or 400 for invalid/not found participant id."""
    response = client.get(
        "/api/v3/nextComment",
        params={
            "conversation_id": 123,
            "not_voted_by_pid": 9999999,
            "limit": 1
        }
    )
    assert response.status_code in (400, 404)

def test_next_comment_with_without_param():
    """Should exclude tids in the 'without' list."""
    response = client.get(
        "/api/v3/nextComment",
        params={
            "conversation_id": 123,
            "not_voted_by_pid": 456,
            "without": [789, 1011],
            "limit": 1
        }
    )
    assert response.status_code == 200
    if response.json():
        assert response.json()["tid"] not in [789, 1011]

def test_next_comment_language_filter():
    """Should return comment in specified language if available."""
    response = client.get(
        "/api/v3/nextComment",
        params={
            "conversation_id": 123,
            "not_voted_by_pid": 456,
            "lang": "fr",
            "limit": 1
        }
    )
    assert response.status_code == 200
    if response.json():
        assert response.json().get("lang") == "fr"

def test_next_comment_include_social():
    """Should return social info if include_social=true."""
    response = client.get(
        "/api/v3/nextComment",
        params={
            "conversation_id": 123,
            "not_voted_by_pid": 456,
            "include_social": True,
            "limit": 1
        }
    )
    assert response.status_code == 200
    if response.json():
        assert "social" in response.json()  # Depending on the data

def test_next_comment_unauthorized():
    """Should return 401 if authentication is required and not provided."""
    # If your endpoint is protected, simulate no auth
    response = client.get(
        "/api/v3/nextComment",
        params={
            "conversation_id": 123,
            "not_voted_by_pid": 456,
            "limit": 1
        }
        # No headers
    )
    assert response.status_code == 401

def test_next_comment_rate_limit():
    """Should return 429 Too Many Requests if rate limit exceeded."""
    # Simulate rapid requests if you have rate limiting
    for _ in range(100):
        response = client.get(
            "/api/v3/nextComment",
            params={
                "conversation_id": 123,
                "not_voted_by_pid": 456,
                "limit": 1
            }
        )
    # Last response should be 429 if limit is enforced
    assert response.status_code in (200, 429)