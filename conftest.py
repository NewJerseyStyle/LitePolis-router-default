import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from litepolis_router_default import router

# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v3")
testclient = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database before each test."""
    from litepolis_database_default import DatabaseActor
    # Delete all users to start fresh
    users = DatabaseActor.list_users(page=1, page_size=1000)
    for user in users:
        try:
            DatabaseActor.delete_user(user.id)
        except:
            pass
    yield


@pytest.fixture
def client(valid_email, valid_password):
    """Test client fixture with auto-created test user."""
    # Create test user first
    testclient.post("/api/v3/auth/new", json={
        "email": valid_email,
        "password": valid_password
    })
    return testclient


@pytest.fixture
def valid_email():
    """Valid test email."""
    return "test@example.com"


@pytest.fixture
def valid_password():
    """Valid test password."""
    return "TestPassword123!"


@pytest.fixture
def other_email():
    """Another test email."""
    return "other@example.com"


@pytest.fixture
def other_password():
    """Another test password."""
    return "OtherPassword123!"


@pytest.fixture
def test_user(client, valid_email, valid_password):
    """Create a test user and return credentials."""
    response = client.post("/api/v3/auth/new", json={
        "email": valid_email,
        "password": valid_password
    })
    return {"email": valid_email, "password": valid_password}


@pytest.fixture
def auth_headers(client, valid_email, valid_password, test_user):
    """Get authentication headers for a user."""
    response = client.post("/api/v3/auth/login", json={
        "email": valid_email,
        "password": valid_password
    })

    data = response.json()
    token = data.get("token", "test-token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(client, other_email, other_password):
    """Get authentication headers for another user."""
    # Create other user
    client.post("/api/v3/auth/new", json={
        "email": other_email,
        "password": other_password
    })
    response = client.post("/api/v3/auth/login", json={
        "email": other_email,
        "password": other_password
    })

    data = response.json()
    token = data.get("token", "test-token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def conversation_id(client, auth_headers):
    """Create a test conversation and return its ID."""
    response = client.post(
        "/api/v3/conversations",
        headers=auth_headers,
        json={
            "topic": "Test Conversation",
            "description": "A test conversation",
            "is_active": True,
            "is_draft": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    return data["data"]["conversation_id"]
