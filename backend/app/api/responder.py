import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import (
    Responder, Resource, Incident, IncidentEvent, FieldUpdate, AllocationItem, RoadAccessibility
)
from app.schemas.incident import FieldUpdateRequest
from app.core.security import require_roles, get_current_user
from app.core.audit import record_audit_log
from app.api.websocket import manager
from app.services.need_score import calculate_need_score
from app.services.demand_predictor import predict_resource_demand

router = APIRouter(prefix="/responder", tags=["Responder Operations"])

@router.get("/me")
def get_responder_profile(
    current_user: dict = Depends(require_roles(["RESPONDER", "ADMIN"])),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    responder = db.query(Responder).filter(Responder.user_id == user_id).first()
    if not responder:
        # Fallback to first responder for convenience
        responder = db.query(Responder).first()
    if not responder:
        raise HTTPException(status_code=404, detail="Responder profile not found")

    assigned_resource = None
    if responder.assigned_resource_id:
        assigned_resource = db.query(Resource).filter(Resource.id == responder.assigned_resource_id).first()
    elif responder.responder_code == "RESP-01":
        assigned_resource = db.query(Resource).filter(Resource.resource_code == "AMB-01").first()
    elif responder.responder_code == "RESP-02":
        assigned_resource = db.query(Resource).filter(Resource.resource_code == "RESCUE-01").first()

    return {
        "id": responder.id,
        "name": responder.name,
        "responder_code": responder.responder_code,
        "organization": responder.organization,
        "role": responder.role,
        "team_unit": responder.team_unit,
        "qualification": responder.qualification,
        "current_status": responder.current_status,
        "phone": responder.phone,
        "assigned_resource": {
            "id": assigned_resource.id,
            "resource_code": assigned_resource.resource_code,
            "resource_type": assigned_resource.resource_type,
            "name": assigned_resource.name,
            "status": assigned_resource.status,
            "current_incident_id": assigned_resource.current_incident_id
        } if assigned_resource else None
    }

@router.get("/assignment")
def get_responder_assignment(
    current_user: dict = Depends(require_roles(["RESPONDER", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """Fetches the current active emergency dispatch assignment for this responder."""
    user_id = current_user.get("sub")
    responder = db.query(Responder).filter(Responder.user_id == user_id).first()
    if not responder:
        responder = db.query(Responder).first()

    # Find resource
    res = None
    if responder.assigned_resource_id:
        res = db.query(Resource).filter(Resource.id == responder.assigned_resource_id).first()
    if not res:
        res_code = "AMB-01" if responder.responder_code == "RESP-01" else "RESCUE-01"
        res = db.query(Resource).filter(Resource.resource_code == res_code).first()

    if not res or not res.current_incident_id:
        # Check latest allocated incident for demo friendliness
        alloc_item = db.query(AllocationItem).filter(
            AllocationItem.resource_id == (res.id if res else "")
        ).order_by(AllocationItem.created_at.desc()).first()
        if alloc_item:
            inc = db.query(Incident).filter(Incident.id == alloc_item.incident_id).first()
            if inc and inc.status != "CLOSED":
                return {
                    "has_assignment": True,
                    "assignment_id": alloc_item.id,
                    "incident": inc,
                    "resource": res,
                    "estimated_eta_minutes": alloc_item.estimated_eta_minutes,
                    "distance_km": alloc_item.distance_km,
                    "instructions": alloc_item.reason,
                    "task_status": alloc_item.status
                }

        return {"has_assignment": False, "message": "No active emergency mission assigned. On standby."}

    inc = db.query(Incident).filter(Incident.id == res.current_incident_id).first()
    return {
        "has_assignment": True,
        "incident": inc,
        "resource": res,
        "estimated_eta_minutes": 8.5,
        "distance_km": 2.8,
        "instructions": f"Proceed urgently to {inc.code} in {inc.zone_code}. Provide immediate triage and victim evacuation.",
        "task_status": res.status
    }

@router.post("/status")
async def update_responder_workflow_status(
    new_status: str, # ACCEPTED, REJECTED, EN_ROUTE, ARRIVED, ON_SCENE, COMPLETED, AVAILABLE
    current_user: dict = Depends(require_roles(["RESPONDER", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Updates the responder and their assigned vehicle's operational state machine.
    """
    user_id = current_user.get("sub")
    responder = db.query(Responder).filter(Responder.user_id == user_id).first()
    if not responder:
        responder = db.query(Responder).first()

    now = datetime.datetime.utcnow()
    responder.current_status = new_status
    responder.last_active_at = now

    # Map to resource status
    resource_status_map = {
        "ACCEPTED": "ASSIGNED",
        "EN_ROUTE": "EN_ROUTE",
        "ARRIVED": "ON_SCENE",
        "ON_SCENE": "ON_SCENE",
        "COMPLETED": "AVAILABLE",
        "AVAILABLE": "AVAILABLE",
        "REJECTED": "AVAILABLE"
    }

    res = None
    if responder.assigned_resource_id:
        res = db.query(Resource).filter(Resource.id == responder.assigned_resource_id).first()
    if not res:
        res_code = "AMB-01" if responder.responder_code == "RESP-01" else "RESCUE-01"
        res = db.query(Resource).filter(Resource.resource_code == res_code).first()

    if res:
        res.status = resource_status_map.get(new_status, res.status)
        res.last_seen_at = now
        if new_status in ["COMPLETED", "REJECTED"]:
            res.current_incident_id = None

    db.commit()

    await manager.broadcast({
        "type": "RESPONDER_STATUS_CHANGED",
        "responder_name": responder.name,
        "responder_code": responder.responder_code,
        "new_status": new_status,
        "resource_code": res.resource_code if res else None
    })

    return {"success": True, "responder_status": new_status, "resource_status": res.status if res else None}

@router.post("/field-update")
async def submit_field_update(
    incident_id: str,
    payload: FieldUpdateRequest,
    current_user: dict = Depends(require_roles(["RESPONDER", "ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Field Update from on-scene responder. Updates rescued, injured, trapped,
    road conditions, and triggers backend re-scoring.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    user_id = current_user.get("sub")
    responder = db.query(Responder).filter(Responder.user_id == user_id).first()
    resp_name = responder.name if responder else "Responder Unit"

    field_update = FieldUpdate(
        incident_id=incident.id,
        responder_id=payload.responder_id or (responder.id if responder else "RESP-01"),
        responder_name=resp_name,
        rescued_count=payload.rescued_count or 0,
        injured_count=payload.injured_count or 0,
        trapped_count=payload.trapped_count or 0,
        road_status=payload.road_status,
        extra_resources_needed=payload.extra_resources_needed,
        text_report=payload.text_report,
        audio_transcript=payload.audio_transcript,
        photo_url=payload.photo_url
    )
    db.add(field_update)

    # Adjust incident numbers based on on-scene confirmation
    if payload.injured_count:
        incident.reported_injured = max(incident.reported_injured, payload.injured_count)
    if payload.trapped_count:
        incident.reported_trapped = max(incident.reported_trapped, payload.trapped_count)

    # If responder verified, boost confidence to CONFIRMED
    incident.confidence = 96
    incident.verification_status = "CONFIRMED"
    if "ON_SCENE_RESPONDER_VERIFIED" not in (incident.verification_signals or []):
        signals = list(incident.verification_signals or [])
        signals.append("ON_SCENE_RESPONDER_VERIFIED")
        incident.verification_signals = signals

    # Re-evaluate Need Score
    loc_intel = incident.location_intelligence or {}
    road_acc = loc_intel.get("road_accessibility_pct", 75)
    if payload.road_status and "blocked" in payload.road_status.lower():
        road_acc = 20

    need_res = calculate_need_score(
        reported_injured=incident.reported_injured,
        reported_trapped=incident.reported_trapped,
        reported_people=incident.reported_people,
        road_accessibility_pct=road_acc,
        zone_vulnerability_index=loc_intel.get("zone_vulnerability_index", 0.6)
    )
    incident.need_score = need_res["need_score"]
    incident.need_priority = need_res["need_priority"]
    incident.need_breakdown = need_res["breakdown"]

    # Recompute demand
    incident.predicted_demand = predict_resource_demand(
        disaster_type=incident.disaster_type,
        reported_people=incident.reported_people,
        reported_injured=incident.reported_injured,
        reported_trapped=incident.reported_trapped,
        road_accessibility_pct=road_acc
    )
    incident.updated_at = datetime.datetime.utcnow()

    # Timeline event
    ev = IncidentEvent(
        incident_id=incident.id,
        event_type="FIELD_UPDATE",
        title=f"On-Scene Field Update by {resp_name}",
        description=(
            f"Rescued: {payload.rescued_count}, Injured: {payload.injured_count}, "
            f"Trapped: {payload.trapped_count}. Report: {payload.text_report or 'Standard update'}"
        ),
        performed_by=resp_name
    )
    db.add(ev)
    db.commit()

    record_audit_log(
        db,
        action="FIELD_UPDATE_SUBMITTED",
        entity_type="INCIDENT",
        entity_id=incident.id,
        performed_by=resp_name,
        details={
            "rescued": payload.rescued_count,
            "injured": payload.injured_count,
            "trapped": payload.trapped_count,
            "road_status": payload.road_status
        }
    )

    await manager.broadcast({
        "type": "NEW_FIELD_UPDATE",
        "incident_id": incident.id,
        "incident_code": incident.code,
        "responder_name": resp_name,
        "rescued_count": payload.rescued_count,
        "injured_count": payload.injured_count,
        "trapped_count": payload.trapped_count,
        "need_score": incident.need_score
    })

    return {
        "success": True,
        "message": "Field update recorded. Incident metrics and Need Score updated.",
        "new_need_score": incident.need_score
    }
