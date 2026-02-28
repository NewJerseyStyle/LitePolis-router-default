import pytest

def test_correlationMatrix_requires_report_id(client):
    """GET /api/v3/math/correlationMatrix without report_id should return 400."""
    response = client.get("/api/v3/math/correlationMatrix")
    assert response.status_code == 400

def test_correlationMatrix_invalid_report_id(client):
    """GET /api/v3/math/correlationMatrix with invalid report_id should return 404 or 400."""
    response = client.get("/api/v3/math/correlationMatrix?report_id=99999999")
    assert response.status_code in (400, 404)

def test_correlationMatrix_valid(client):
    """GET /api/v3/math/correlationMatrix with valid report_id should return a correlation matrix."""
    # Substitute with a valid report_id from your test fixtures or database
    valid_report_id = 1
    response = client.get(f"/api/v3/math/correlationMatrix?report_id={valid_report_id}")
    assert response.status_code == 200
    result = response.json()
    # The actual key may be 'data', 'correlation', etc. Adjust as needed.
    assert any(k in result for k in ["data", "correlation", "matrix"])
    # If the key is known, for instance 'data', you can do:
    # matrix = result["data"]
    # assert isinstance(matrix, list)
    # assert all(isinstance(row, list) for row in matrix)

def test_correlationMatrix_with_math_tick(client):
    """GET /api/v3/math/correlationMatrix with math_tick should still succeed."""
    valid_report_id = 1
    response = client.get(f"/api/v3/math/correlationMatrix?report_id={valid_report_id}&math_tick=0")
    assert response.status_code == 200
    result = response.json()
    assert any(k in result for k in ["data", "correlation", "matrix"])

def test_correlationMatrix_invalid_method(client):
    """POST on /api/v3/math/correlationMatrix should return 405."""
    response = client.post("/api/v3/math/correlationMatrix")
    assert response.status_code == 405