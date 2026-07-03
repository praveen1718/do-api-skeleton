"""End-to-end-ish tests via FastAPI's TestClient (no network needed)."""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app


@pytest.fixture(autouse=True)
def reset_service():
    """Each test gets a clean in-memory store."""
    routes._service = None
    yield
    routes._service = None


@pytest.fixture
def client():
    return TestClient(app)


def _record(rid: str, value: float):
    return {
        "id": rid,
        "source": "sensor-a",
        "timestamp": datetime.now(UTC).isoformat(),
        "value": value,
        "metadata": {"unit": "c"},
    }


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_and_results(client):
    payload = {"records": [_record("1", 10.0), _record("2", 20.0)]}
    r = client.post("/api/v1/ingest", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] == 2
    assert body["rejected"] == 0
    assert "request_id" in body

    r2 = client.get("/api/v1/results")
    res = r2.json()
    assert res["count"] == 2
    assert res["sum"] == 30.0
    assert res["mean"] == 15.0
    assert res["min"] == 10.0
    assert res["max"] == 20.0


def test_duplicate_ids_rejected(client):
    payload = {"records": [_record("dup", 1.0), _record("dup", 2.0)]}
    r = client.post("/api/v1/ingest", json=payload)
    assert r.json() == {"accepted": 1, "rejected": 1, "request_id": r.json()["request_id"]}


def test_invalid_payload_returns_422(client):
    # Missing required 'records'
    r = client.post("/api/v1/ingest", json={})
    assert r.status_code == 422
    assert r.json()["error"] == "validation_error"


def test_empty_records_rejected(client):
    r = client.post("/api/v1/ingest", json={"records": []})
    assert r.status_code == 422


def test_results_empty(client):
    r = client.get("/api/v1/results")
    assert r.json()["count"] == 0
