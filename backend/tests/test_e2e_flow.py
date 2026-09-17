import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.database.models import Incident, Resource

client = TestClient(app)

def test_full_disaster_response_lifecycle():
    # Step 1-5: Citizen raises SOS
    sos_res = client.post("/api/sos", json={
        "session_id": "citizen-e2e-demo",
        "latitude": 18.5074,
        "longitude": 73.8077,
        "accuracy": 10.0
    })
    assert sos_res.status_code == 200
    sos_data = sos_res.json()
    inc_id = sos_data["incident_id"]

    # Citizen confirms
    conf_res = client.post(f"/api/sos/{inc_id}/confirm")
    assert conf_res.status_code == 200

    # Step 6-8: Citizen supplies details, AI analyzes, need score computed, demand generated
    details_res = client.post(f"/api/incidents/{inc_id}/details", json={
        "disaster_type": "Flood",
        "answers": {
            "q_flood_trapped": "Yes, unable to leave",
            "q_flood_people": "More than 15",
            "q_flood_water_level": "Chest deep or higher"
        },
        "text_notes": "Water rising rapidly, elderly people with us",
        "reported_people": 35,
        "reported_injured": 6,
        "reported_trapped": 15
    })
    assert details_res.status_code == 200
    details_data = details_res.json()
    assert details_data["need_score"] > 60.0

    # Step 9: Admin logs in and runs optimizer
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    opt_res = client.post("/api/optimization/run", json={"incident_ids": [inc_id]}, headers=headers)
    assert opt_res.status_code == 200
    alloc_data = opt_res.json()
    alloc_id = alloc_data["id"]
    assert len(alloc_data["items"]) > 0

    # Step 10: Admin approves and dispatches
    approve_res = client.post(f"/api/optimization/{alloc_id}/approve", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["success"] is True

    # Step 11: Responder logs in and checks assignment
    resp_login = client.post("/api/auth/login", json={"username": "responder1", "password": "resp123"})
    assert resp_login.status_code == 200
    resp_token = resp_login.json()["access_token"]
    resp_headers = {"Authorization": f"Bearer {resp_token}"}

    assignment_res = client.get("/api/responder/assignment", headers=resp_headers)
    assert assignment_res.status_code == 200

    # Step 12-13: Responder marks EN ROUTE, then ARRIVED
    status_res1 = client.post("/api/responder/status?new_status=EN_ROUTE", headers=resp_headers)
    assert status_res1.status_code == 200

    status_res2 = client.post("/api/responder/status?new_status=ARRIVED", headers=resp_headers)
    assert status_res2.status_code == 200

    # Step 14-15: Responder submits field update
    field_res = client.post(f"/api/responder/field-update?incident_id={inc_id}", json={
        "responder_id": "RESP-01",
        "rescued_count": 8,
        "injured_count": 12,
        "trapped_count": 10,
        "road_status": "West access road inundated, use bypass",
        "text_report": "Rescued 8 individuals. Remaining 10 trapped on second floor."
    }, headers=resp_headers)
    assert field_res.status_code == 200
    assert field_res.json()["new_need_score"] > 0

    # Step 16: Reallocation diff triggered
    realloc_res = client.post("/api/optimization/reallocate?trigger_reason=Casualties+updated+by+field+unit", headers=headers)
    assert realloc_res.status_code == 200
    assert "changes" in realloc_res.json()

    # Step 17-18: Admin closes incident, resources freed
    close_res = client.post(f"/api/incidents/{inc_id}/close", headers=headers)
    assert close_res.status_code == 200
    assert close_res.json()["success"] is True
