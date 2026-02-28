# LitePolis Router Default

A Polis-compatible API implementation for LitePolis. This module provides the core API endpoints required by the Polis frontend (client-admin, client-participation, client-report).

## Overview

This router implements the `/api/v3/*` endpoints that the original Polis system uses, making LitePolis a drop-in replacement backend for Polis frontends.

## Implemented Endpoints

### Authentication (`/api/v3/auth/*`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/auth/new` | POST | Register new user | ✅ |
| `/auth/login` | POST | User login | ✅ |
| `/auth/deregister` | POST | User logout | ✅ |
| `/auth/pwresettoken` | POST | Request password reset token | ✅ |
| `/auth/password` | POST | Reset password | ✅ |

### Users (`/api/v3/users`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/users` | GET | Get current user info | ✅ |
| `/users` | PUT | Update user info | ✅ |

### Conversations (`/api/v3/conversations/*`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/conversations` | GET | List conversations | ✅ |
| `/conversations` | POST | Create conversation | ✅ |
| `/conversations` | PUT | Update conversation | ✅ |
| `/conversation/close` | POST | Close conversation | ✅ |
| `/conversation/reopen` | POST | Reopen conversation | ✅ |
| `/conversations/preload` | GET | Preload conversation data | ✅ |
| `/conversationStats` | GET | Get conversation statistics | ✅ |

### Participants (`/api/v3/participants/*`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/participants` | GET | Get participants list | ✅ |
| `/participants` | POST | Join conversation (create participant) | ✅ |
| `/participationInit` | GET | Initialize participation session | ✅ |

### Comments (`/api/v3/comments/*`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/comments` | GET | Get comments list | ✅ |
| `/comments` | POST | Create new comment | ✅ |
| `/comments` | PUT | Update comment (moderation) | ✅ |
| `/nextComment` | GET | Get next comment for voting | ✅ |

### Votes (`/api/v3/votes/*`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/votes` | GET | Get votes data | ✅ |
| `/votes` | POST | Submit vote | ✅ |
| `/votes/me` | GET | Get current user's votes | ✅ |

### Invites (`/api/v3/zinvites/*`, `/api/v3/joinWithInvite`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/zinvites/{zid}` | GET | Get conversation invite code | ✅ |
| `/zinvites/{zid}` | POST | Create invite code | ✅ |
| `/joinWithInvite` | POST | Join conversation with invite | ✅ |

### Math/Visualization (`/api/v3/math/*`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/math/pca` | GET | Get PCA visualization data | ⚠️ Stub |
| `/math/pca2` | GET | Get PCA data (v2) | ⚠️ Stub |

### System (`/api/v3/*`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/testConnection` | GET | Health check | ✅ |
| `/testDatabase` | GET | Database connection test | ✅ |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LitePolis Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  run_server.py                 Entry point (FastAPI app)    │
│       │                                                     │
│       └── imports router from litepolis_router_default      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  litepolis_router_default/                                  │
│  └── core.py                   All API endpoints            │
│       ├── Authentication (JWT, cookies)                     │
│       ├── User management                                   │
│       ├── Conversation CRUD                                 │
│       ├── Participant management                            │
│       ├── Comment system                                    │
│       └── Voting system                                     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  litepolis-database-default/    Database layer (SQLite)     │
│       ├── User model                                        │
│       ├── Conversation model                                │
│       ├── Participant model                                 │
│       ├── Comment model                                     │
│       ├── Vote model                                        │
│       └── Zinvite model                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- pip or uv

### Installation

```bash
# Install the package
pip install -e .

# Or with uv
uv pip install -e .
```

### Running the Server

```bash
# Set port (default: 8000)
export LITEPOLIS_PORT=8888

# Start server
python run_server.py

# Server will be available at:
# http://localhost:8888/api/v3/
```

### Testing the API

```bash
# Run unit tests
pytest tests/ -v

# Run E2E API tests (requires server running)
LITEPOLIS_BASE_URL=http://localhost:8888/api/v3 python ../test_e2e_api.py
```

## Authentication

The router supports multiple authentication methods:

1. **Cookie-based**: `token2` and `uid2` cookies set on login
2. **JWT Bearer**: `Authorization: Bearer <token>` header
3. **XID**: External ID for embedded scenarios

### Example: Login and Create Conversation

```python
import requests

# Login
resp = requests.post('http://localhost:8888/api/v3/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})
token = resp.json()['token']

# Create conversation (using cookie)
resp = requests.post('http://localhost:8888/api/v3/conversations', 
    json={'topic': 'My Conversation', 'description': 'Description'},
    cookies={'token2': token}
)
conversation_id = resp.json()['conversation_id']

# Initialize participation
resp = requests.get('http://localhost:8888/api/v3/participationInit',
    params={'conversation_id': conversation_id},
    cookies={'token2': token}
)
```

## API Response Format

### Success Response

```json
{
    "status": "ok",
    "data": { ... }
}
```

### Error Response

```json
{
    "status": "error",
    "error": "polis_err_xxx",
    "message": "Error description"
}
```

### Auth Response (Polis-compatible)

```json
{
    "status": "ok",
    "success": true,
    "token": "jwt_token_here",
    "user_id": 1,
    "data": {"uid": 1, "email": "user@example.com"}
}
```

## Key Concepts

### conversation_id vs zid

- `zid`: Internal numeric ID (database primary key)
- `conversation_id`: External string ID (zinvite code, e.g., "3YUM7S49pdMe")
- API uses `conversation_id` externally, converts to `zid` internally

### Participant (pid)

- `pid` is a unique identifier for a user's participation in a conversation
- Created automatically when user first accesses a conversation
- Stored in JWT for subsequent requests

### Vote Values

- `-1`: Disagree
- `0`: Pass / Skip
- `1`: Agree

### Moderation Status (mod)

- `0`: Pending review
- `1`: Approved
- `-1`: Rejected

## Configuration

The router uses `DEFAULT_CONFIG` for default settings:

```python
DEFAULT_CONFIG = {
    "jwt_secret": "dev-secret-key",
    "jwt_expire_hours": 168,
    # Add more config as needed
}
```

## Known Limitations

1. **Math endpoints** (`/math/pca`, `/math/pca2`) are stubs - return placeholder data
2. **Email notifications** not implemented
3. **OIDC/Social login** not yet implemented

## Contributing

1. Follow existing code patterns
2. Add tests for new endpoints
3. Update this README for API changes
4. Ensure E2E tests pass before submitting

## License

See LICENSE file.

## Related Projects

- [litepolis-database-default](https://github.com/NewJerseyStyle/LitePolis-database-default) - Database layer
- [litepolis-middleware-default](https://github.com/NewJerseyStyle/LitePolis-middleware-default) - Authentication middleware
- [Polis](https://github.com/compdemocracy/polis) - Original Polis system
