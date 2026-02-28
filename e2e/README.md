## Testing

### E2E Tests

E2E tests verify full API functionality:

```bash
# Start server first
LITEPOLIS_PORT=8888 python run_server.py &

# Run E2E tests
LITEPOLIS_BASE_URL=http://localhost:8888/api/v3 python test_e2e_api.py
```

### E2E Test Results (2026-02-28)

```
==================================================
LitePolis E2E API Test Suite
==================================================
Results: 18/18 passed

✓ Backend connection
✓ User registration
✓ Duplicate email rejection (409 status)
✓ User login
✓ Cookie token2 set
✓ Cookie uid2 set
✓ Invalid password rejection
✓ Get user info
✓ Create conversation
✓ Conversation ID returned
✓ List conversations
✓ Participation init
✓ Create comment
✓ Get comments
✓ Create vote (agree)
✓ Logout
✓ Anonymous participation init
✓ Anonymous pc cookie set
```
