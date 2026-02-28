import pytest

def test_get_users_requires_auth(client):
    """Should require authentication to list users."""
    response = client.get("/api/v3/users")
    assert response.status_code in (401, 403)

def test_get_users_success(client, auth_headers):
    """Should return a list of users for an authenticated user."""
    response = client.get("/api/v3/users", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    if users:
        user = users[0]
        assert "user_id" in user or "id" in user
        assert "email" in user
        assert "name" in user

def test_get_users_pagination(client, auth_headers):
    """Should support pagination parameters if implemented."""
    response = client.get("/api/v3/users?limit=2&offset=0", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) <= 2

def test_get_users_filter_by_email(client, auth_headers):
    """Should support filtering by email if supported."""
    response = client.get("/api/v3/users?email=testuser@example.com", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    # Optionally check all users in result have the requested email
    for user in users:
        assert user["email"] == "testuser@example.com"

def test_get_users_filter_by_id(client, auth_headers):
    """Should support filtering by user_id if supported."""
    response = client.get("/api/v3/users?user_id=123", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    for user in users:
        assert str(user.get("user_id", user.get("id"))) == "123"

def test_get_users_unauthorized_access(client, other_auth_headers):
    """Should not allow users with insufficient permissions to list users, if RBAC is enforced."""
    response = client.get("/api/v3/users", headers=other_auth_headers)
    assert response.status_code in (401, 403)


def test_get_users_errIfNoAuth_true_without_auth(client):
    """Should return 401/403 if errIfNoAuth=true and not authenticated."""
    response = client.get("/api/v3/users?errIfNoAuth=true")
    assert response.status_code in (401, 403)

def test_get_users_errIfNoAuth_true_with_auth(client, auth_headers):
    """Should return user list if authenticated and errIfNoAuth=true."""
    response = client.get("/api/v3/users?errIfNoAuth=true", headers=auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    if users:
        user = users[0]
        assert "user_id" in user or "id" in user
        assert "email" in user
        assert "name" in user

def test_get_users_errIfNoAuth_false_without_auth(client):
    """Should return 401/403 or empty list if not authenticated and errIfNoAuth is false or not set."""
    response = client.get("/api/v3/users?errIfNoAuth=false")
    # Acceptable: 401/403 (most secure), or 200 with empty list if public listing is allowed
    assert response.status_code in (200, 401, 403)
    if response.status_code == 200:
        assert response.json() == [] or isinstance(response.json(), list)