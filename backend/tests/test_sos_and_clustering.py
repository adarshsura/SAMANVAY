import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.database.models import Incident

client = TestClient(app)

def test_citizen_sos_creation_zero_login():
    """Verify citizen can trigger SOS without credentials and receive Incident ID and code."""
    payload = {
        "session_id": "test-session-citizen-01",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "accuracy": 12.5
    }
    response = client.post("/api/sos", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    assert data["code"].startswith("INC-")
    assert data["location_captured"] is True
    assert data["is_duplicate"] is False
    assert data["event_count"] == 1

def test_duplicate_sos_prevention_same_session():
    """Verify repeated tap from the same session is merged and does not create duplicate incidents."""
    session_id = "test-session-repeat-tap-02"
    payload = {
        "session_id": session_id,
        "latitude": 18.5210,
        "longitude": 73.8570
    }
    # First tap
    res1 = client.post("/api/sos", json=payload)
    assert res1.status_code == 200
    inc_id1 = res1.json()["incident_id"]

    # Second tap within 3 minutes
    res2 = client.post("/api/sos", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["incident_id"] == inc_id1
    assert data2["is_duplicate"] is True
    assert data2["event_count"] >= 2

def test_spatial_clustering_within_150_meters():
    """Verify independent reports within 150m cluster together into a single incident with higher confidence."""
    # Base location (approx 50m offset: 0.0004 deg is ~45m)
    payload_a = {
        "session_id": "citizen-device-alpha",
        "latitude": 18.5300,
        "longitude": 73.8440
    }
    res_a = client.post("/api/sos", json=payload_a)
    assert res_a.status_code == 200
    inc_id = res_a.json()["incident_id"]

    payload_b = {
        "session_id": "citizen-device-beta",
        "latitude": 18.5303, # ~35m away
        "longitude": 73.8442
    }
    res_b = client.post("/api/sos", json=payload_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["incident_id"] == inc_id
    assert data_b["is_duplicate"] is True
    assert data_b["event_count"] >= 2
