"""Tests para el API FastAPI."""

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_analyze_endpoint() -> None:
    payload = {
        "source": """begin
    for i 🡨 1 to n do
    begin
        suma 🡨 suma + i
    end
end""",
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "worst_case" in body["summary"]
    assert "pattern_summary" in body["annotations"]


def test_analyze_file_endpoint() -> None:
    content = """begin
    while (n > 0) do
    begin
        n 🡨 n - 1
    end
end"""
    files = {
        "file": (
            "algoritmo.txt",
            content.encode("utf-8"),
            "text/plain",
        )
    }
    response = client.post("/api/analyze-file", files=files)
    assert response.status_code == 200
    body = response.json()
    assert "worst_case" in body["summary"]
    assert "pattern_summary" in body["annotations"]
