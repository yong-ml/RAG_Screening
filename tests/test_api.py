def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "AI Resume Screening API is running"
    assert "version" in data

def test_get_history_empty(client):
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    assert response.json() == []

def test_system_status(client):
    response = client.get("/api/v1/db-status")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "sqlite_stats" in data

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_system_state(client):
    response = client.get("/api/v1/state")
    assert response.status_code == 200
    data = response.json()
    assert "has_job_description" in data
    assert "resume_count" in data
