import subprocess
from fastapi.testclient import TestClient
from app import fastapi_app

client = TestClient(fastapi_app)

def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "incident-triage-agent"

def test_dotenv_not_tracked_in_git():
    result = subprocess.run(
        ["git", "ls-files", ".env"],
        capture_output=True,
        text=True
    )
    # Output must be empty meaning .env is ignored and not tracked
    assert result.stdout.strip() == ""
