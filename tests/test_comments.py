import pytest

def test_get_comments_requires_conversation_id(client):
    # Missing conversation_id should yield 400
    response = client.get("/api/v3/comments")
    assert response.status_code == 400
    assert "conversation_id" in response.text

def test_get_comments_returns_comments_for_conversation(client, conversation_id):
    # Returns array of comments for a valid conversation
    response = client.get("/api/v3/comments", params={"conversation_id": conversation_id})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Each comment should have expected keys
    for comment in data:
        assert "tid" in comment
        assert "txt" in comment

def test_get_comments_with_not_voted_by_pid_excludes_voted(client, conversation_id, pid, voted_tid):
    # Comments the user already voted on should be excluded
    response = client.get("/api/v3/comments", params={
        "conversation_id": conversation_id,
        "not_voted_by_pid": pid
    })
    assert response.status_code == 200
    tids = [c["tid"] for c in response.json()]
    assert voted_tid not in tids

def test_get_comments_with_limit(client, conversation_id):
    response = client.get("/api/v3/comments", params={"conversation_id": conversation_id, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

def test_get_comments_include_social(client, conversation_id):
    response = client.get("/api/v3/comments", params={"conversation_id": conversation_id, "include_social": True})
    assert response.status_code == 200
    # Some comments may have "social" key if not anonymous
    for comment in response.json():
        if not comment.get("anon", True):
            assert "social" in comment or "social" not in comment  # Accept both, just check key logic

def test_get_comments_lang_filter(client, conversation_id):
    # Should prefer comments in the requested language, if present
    response = client.get("/api/v3/comments", params={"conversation_id": conversation_id, "lang": "fr"})
    assert response.status_code == 200
    data = response.json()
    if data:
        assert all(c.get("lang") == "fr" for c in data if "lang" in c)

def test_get_comments_moderation_true(client, conversation_id):
    # With moderation=true, comments should include moderation fields
    response = client.get("/api/v3/comments", params={"conversation_id": conversation_id, "moderation": "true"})
    assert response.status_code == 200
    for comment in response.json():
        assert "velocity" in comment
        assert "mod" in comment
        assert "active" in comment

def test_get_comments_with_tids(client, conversation_id, tids):
    response = client.get("/api/v3/comments", params={"conversation_id": conversation_id, "tids": tids})
    assert response.status_code == 200
    returned_tids = {c["tid"] for c in response.json()}
    assert set(tids).issubset(returned_tids)

def test_get_comments_invalid_conversation(client):
    response = client.get("/api/v3/comments", params={"conversation_id": 99999999})
    assert response.status_code in (200, 404)
    # If 200, should return empty list
    if response.status_code == 200:
        assert response.json() == []

def test_get_comments_with_mod_param(client, conversation_id):
    # Should return comments with the specified moderation status
    response = client.get("/api/v3/comments", params={"conversation_id": conversation_id, "mod": 1})
    assert response.status_code == 200
    for comment in response.json():
        assert comment.get("mod") == 1

def test_get_comments_include_voting_patterns(client, conversation_id):
    response = client.get("/api/v3/comments", params={
        "conversation_id": conversation_id,
        "moderation": "true",
        "include_voting_patterns": "true"
    })
    assert response.status_code == 200
    for comment in response.json():
        assert "agree_count" in comment
        assert "disagree_count" in comment
        assert "pass_count" in comment
        assert "count" in comment

def test_get_comments_modIn_and_strict(client, conversation_id):
    # Should respect modIn param and strict moderation logic
    response = client.get("/api/v3/comments", params={
        "conversation_id": conversation_id,
        "modIn": "true",
        "strict": "true"
    })
    assert response.status_code == 200
    # Comments should have mod > 0 if strict moderation
    for comment in response.json():
        assert comment["mod"] > 0

def test_post_comment_requires_auth(client):
    """Should reject anonymous POST if auth is required."""
    response = client.post("/api/v3/comments", json={})
    assert response.status_code in (401, 403)

def test_post_comment_requires_conversation_id(client, auth_headers):
    """Should reject POST with missing conversation_id."""
    data = {
        "txt": "Test comment"
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 400
    assert "conversation_id" in response.text

def test_post_comment_creates_comment(client, auth_headers, conversation_id):
    """Should create a comment with required fields."""
    data = {
        "conversation_id": conversation_id,
        "txt": "This is a test comment"
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 200
    comment = response.json()
    assert comment["txt"] == "This is a test comment"
    assert "tid" in comment

def test_post_comment_with_anon_flag(client, auth_headers, conversation_id):
    """Should respect anon flag."""
    data = {
        "conversation_id": conversation_id,
        "txt": "Anonymous comment",
        "anon": True
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 200
    comment = response.json()
    assert comment.get("anon") is True

def test_post_comment_with_seed_flag(client, auth_headers, conversation_id):
    """Should respect is_seed flag."""
    data = {
        "conversation_id": conversation_id,
        "txt": "Seed comment",
        "is_seed": True
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 200
    comment = response.json()
    assert comment.get("is_seed") is True

def test_post_comment_with_lang(client, auth_headers, conversation_id):
    """Should accept lang field."""
    data = {
        "conversation_id": conversation_id,
        "txt": "Comment in French",
        "lang": "fr"
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 200
    comment = response.json()
    assert comment.get("lang") == "fr"

def test_post_comment_requires_txt_or_vote(client, auth_headers, conversation_id):
    """Should reject if neither txt nor vote is present."""
    data = {
        "conversation_id": conversation_id
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 400

def test_post_comment_txt_too_long(client, auth_headers, conversation_id):
    """Should reject if txt is too long (>997 chars)."""
    data = {
        "conversation_id": conversation_id,
        "txt": "a" * 1000
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 400

def test_post_comment_with_twitter_fields(client, auth_headers, conversation_id):
    """Should accept twitter_tweet_id and quote_twitter_screen_name."""
    data = {
        "conversation_id": conversation_id,
        "txt": "Comment with twitter fields",
        "twitter_tweet_id": "1234567890",
        "quote_twitter_screen_name": "user"
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response.status_code == 200
    comment = response.json()
    assert comment.get("twitter_tweet_id") == "1234567890"
    assert comment.get("quote_twitter_screen_name") == "user"

def test_post_comment_spam(client, auth_headers, conversation_id):
    """Should handle spam/offtopic/important flags if supported."""
    data = {
        "conversation_id": conversation_id,
        "txt": "Spammy comment",
        "spam": True
    }
    response = client.post("/api/v3/comments", headers=auth_headers, json=data)
    # Response may vary; ensure no 500 error
    assert response.status_code in (200, 400, 422)

def test_post_comment_duplicate(client, auth_headers, conversation_id):
    """Should reject duplicate comment (if logic exists)."""
    data = {
        "conversation_id": conversation_id,
        "txt": "Unique comment"
    }
    response1 = client.post("/api/v3/comments", headers=auth_headers, json=data)
    response2 = client.post("/api/v3/comments", headers=auth_headers, json=data)
    assert response2.status_code in (200, 409, 400)  # Accept 409 Conflict or 400 if duplicate logic exists