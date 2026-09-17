import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Incident, IncidentEvent, IncidentReport
from app.schemas.incident import (
    SosCreateRequest, SosCreateResponse, IncidentDetailsRequest, IncidentItemResponse
)
from app.services.location_intelligence import compute_location_intelligence
from app.services.incident_ai import analyze_incident_data, get_adaptive_questions
from app.services.need_score import calculate_need_score
from app.services.demand_predictor import predict_resource_demand
from app.services.verification import check_duplicate_or_cluster, update_incident_corroboration
from app.api.websocket import manager
from app.core.audit import record_audit_log

router = APIRouter(prefix="", tags=["Citizen SOS"])

@router.post("/sos", response_model=SosCreateResponse)
async def create_sos(payload: SosCreateRequest, db: Session = Depends(get_db)):
    """
    Zero-login citizen emergency endpoint. Immediately captures coordinates,
    checks for duplicate taps or spatial clusters, runs location intelligence,
    and creates or corroborates the incident.
    """
    existing_inc, is_duplicate, match_type = check_duplicate_or_cluster(
        session_id=payload.session_id,
        lat=payload.latitude,
        lon=payload.longitude,
        db=db
    )

    if is_duplicate and existing_inc:
        update_incident_corroboration(existing_inc, match_type, db)
        
        # Broadcast via WebSocket
        await manager.broadcast({
            "type": "INCIDENT_CORROBORATED",
            "incident_id": existing_inc.id,
            "incident_code": existing_inc.code,
            "event_count": existing_inc.event_count,
            "confidence": existing_inc.confidence
        })

        return SosCreateResponse(
            incident_id=existing_inc.id,
            code=existing_inc.code,
            status=existing_inc.status,
            location_captured=True,
            latitude=existing_inc.latitude,
            longitude=existing_inc.longitude,
            is_duplicate=True,
            event_count=existing_inc.event_count,
            message="Your emergency report was linked with an active response cluster."
        )

    # 1. Run Location Intelligence
    loc_intel = compute_location_intelligence(payload.latitude, payload.longitude, db)
    zone_code = loc_intel.get("zone", "Zone B")

    # 2. Initial baseline Need Score & Demand Prediction
    initial_need = calculate_need_score(
        reported_injured=0,
        reported_trapped=0,
        reported_people=1,
        road_accessibility_pct=loc_intel.get("road_accessibility_pct", 85),
        zone_vulnerability_index=loc_intel.get("zone_vulnerability_index", 0.5)
    )

    initial_demand = predict_resource_demand(
        disaster_type="Unknown",
        reported_people=1,
        reported_injured=0,
        reported_trapped=0,
        road_accessibility_pct=loc_intel.get("road_accessibility_pct", 85)
    )

    # Generate distinct human incident code
    inc_code = f"INC-{uuid.uuid4().hex[:4].upper()}"

    new_incident = Incident(
        code=inc_code,
        session_id=payload.session_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        zone_code=zone_code,
        disaster_type="Unknown",
        description="Emergency SOS beacon initiated via citizen web portal.",
        reported_people=1,
        reported_injured=0,
        reported_trapped=0,
        hazard_level="MODERATE",
        confidence=72,
        status="RECEIVED",
        source="CITIZEN_WEB",
        event_count=1,
        need_score=initial_need["need_score"],
        need_priority=initial_need["need_priority"],
        need_breakdown=initial_need["breakdown"],
        predicted_demand=initial_demand,
        location_intelligence=loc_intel,
        verification_status="UNVERIFIED",
        verification_signals=["GPS_RECEIVED"]
    )
    db.add(new_incident)
    db.commit()

    # Timeline event
    event = IncidentEvent(
        incident_id=new_incident.id,
        event_type="SOS_CREATED",
        title="Emergency Beacon Transmitted",
        description=f"GPS coordinates {payload.latitude:.4f}, {payload.longitude:.4f} received in {zone_code}.",
        performed_by="Citizen (Anonymous)"
    )
    db.add(event)
    db.commit()

    # Record Audit Log
    record_audit_log(
        db,
        action="SOS_CREATED",
        entity_type="INCIDENT",
        entity_id=new_incident.id,
        performed_by="Citizen",
        details={"code": inc_code, "zone": zone_code, "lat": payload.latitude, "lon": payload.longitude}
    )

    # Broadcast to Command Center via WebSocket
    await manager.broadcast({
        "type": "NEW_INCIDENT",
        "incident_id": new_incident.id,
        "code": new_incident.code,
        "zone_code": new_incident.zone_code,
        "need_score": new_incident.need_score,
        "need_priority": new_incident.need_priority,
        "latitude": new_incident.latitude,
        "longitude": new_incident.longitude
    })

    return SosCreateResponse(
        incident_id=new_incident.id,
        code=new_incident.code,
        status=new_incident.status,
        location_captured=True,
        latitude=new_incident.latitude,
        longitude=new_incident.longitude,
        is_duplicate=False,
        event_count=1,
        message="Help request sent. Your location has been shared with the response system."
    )

@router.post("/sos/{id}/confirm")
async def confirm_sos(id: str, db: Session = Depends(get_db)):
    """Second-step confirmation from citizen UI."""
    incident = db.query(Incident).filter(Incident.id == id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "RECEIVED"
    if "USER_CONFIRMED" not in (incident.verification_signals or []):
        signals = list(incident.verification_signals or [])
        signals.append("USER_CONFIRMED")
        incident.verification_signals = signals
        incident.confidence = min(95, incident.confidence + 5)

    ev = IncidentEvent(
        incident_id=incident.id,
        event_type="SOS_CONFIRMED",
        title="Citizen Confirmed Emergency",
        description="Two-step intentional confirmation verified by citizen.",
        performed_by="Citizen"
    )
    db.add(ev)
    db.commit()

    return {"success": True, "message": "SOS confirmed and verified."}

@router.get("/incidents/{id}/questions")
def get_incident_questions(id: str, disaster_type: str = "Flood", db: Session = Depends(get_db)):
    """Returns skippable, adaptive questions tailored to the disaster type."""
    questions = get_adaptive_questions(disaster_type)
    return {"disaster_type": disaster_type, "questions": questions}

@router.post("/incidents/{id}/details")
async def add_incident_details(id: str, payload: IncidentDetailsRequest, db: Session = Depends(get_db)):
    """
    Step 4 Optional Information: citizen provides answers, text notes, voice transcript, or photo.
    Re-runs AI incident analysis, updates Need Score and resource demand predictions.
    """
    incident = db.query(Incident).filter(Incident.id == id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Record report entry
    report = IncidentReport(
        incident_id=incident.id,
        session_id=payload.session_id,
        answers=payload.answers or {},
        text_notes=payload.text_notes,
        voice_transcript=payload.voice_transcript,
        photo_url=payload.photo_url
    )
    db.add(report)

    # Run AI Analysis
    ai_result = analyze_incident_data(
        disaster_type=payload.disaster_type or incident.disaster_type,
        answers=payload.answers,
        text_notes=payload.text_notes,
        voice_transcript=payload.voice_transcript,
        location_intel=incident.location_intelligence or {}
    )

    # Update incident fields
    incident.disaster_type = ai_result["disaster_type"]
    if payload.reported_people:
        incident.reported_people = payload.reported_people
    elif ai_result.get("estimated_people_mid"):
        incident.reported_people = max(incident.reported_people, ai_result["estimated_people_mid"])

    if payload.reported_injured:
        incident.reported_injured = payload.reported_injured
    else:
        incident.reported_injured = max(incident.reported_injured, ai_result["estimated_injured"])

    if payload.reported_trapped:
        incident.reported_trapped = payload.reported_trapped
    else:
        incident.reported_trapped = max(incident.reported_trapped, ai_result["estimated_trapped"])

    incident.hazard_level = ai_result["hazard_level"]
    incident.confidence = max(incident.confidence, ai_result["confidence"])
    if payload.text_notes:
        incident.description = f"{incident.description or ''} | Note: {payload.text_notes}".strip(" | ")

    # Recompute Need Score with updated inputs
    loc_intel = incident.location_intelligence or {}
    updated_need = calculate_need_score(
        reported_injured=incident.reported_injured,
        reported_trapped=incident.reported_trapped,
        reported_people=incident.reported_people,
        road_accessibility_pct=loc_intel.get("road_accessibility_pct", 80),
        zone_vulnerability_index=loc_intel.get("zone_vulnerability_index", 0.5)
    )
    incident.need_score = updated_need["need_score"]
    incident.need_priority = updated_need["need_priority"]
    incident.need_breakdown = updated_need["breakdown"]

    # Recompute Predicted Resource Demand
    updated_demand = predict_resource_demand(
        disaster_type=incident.disaster_type,
        reported_people=incident.reported_people,
        reported_injured=incident.reported_injured,
        reported_trapped=incident.reported_trapped,
        road_accessibility_pct=loc_intel.get("road_accessibility_pct", 80)
    )
    incident.predicted_demand = updated_demand
    incident.updated_at = datetime.datetime.utcnow()

    # Timeline event
    ev = IncidentEvent(
        incident_id=incident.id,
        event_type="DETAILS_ADDED",
        title="Incident Intelligence Enhanced",
        description=ai_result["explanation"],
        performed_by="AI Decision Engine"
    )
    db.add(ev)
    db.commit()

    # Broadcast updated intelligence
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "incident_id": incident.id,
        "disaster_type": incident.disaster_type,
        "need_score": incident.need_score,
        "need_priority": incident.need_priority,
        "predicted_demand": incident.predicted_demand
    })

    return {
        "success": True,
        "incident_id": incident.id,
        "disaster_type": incident.disaster_type,
        "need_score": incident.need_score,
        "need_priority": incident.need_priority,
        "explanation": ai_result["explanation"]
    }

@router.get("/incidents/track/{code_or_id}")
def track_incident(code_or_id: str, db: Session = Depends(get_db)):
    """Zero-login tracking endpoint for citizens."""
    incident = db.query(Incident).filter(
        (Incident.code == code_or_id) | (Incident.id == code_or_id) | (Incident.session_id == code_or_id)
    ).first()
    if not incident:
        raise HTTPException(status_code=404, detail="No active incident found for this reference.")

    # Fetch latest events
    events = db.query(IncidentEvent).filter(
        IncidentEvent.incident_id == incident.id
    ).order_by(IncidentEvent.created_at.desc()).limit(10).all()

    return {
        "id": incident.id,
        "code": incident.code,
        "status": incident.status,
        "disaster_type": incident.disaster_type,
        "zone_code": incident.zone_code,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
        "need_priority": incident.need_priority,
        "events": [
            {"title": e.title, "description": e.description, "time": e.created_at.isoformat()}
            for e in events
        ]
    }

@router.post("/incidents/{id}/cancel")
async def cancel_sos(id: str, db: Session = Depends(get_db)):
    """Allows citizen to cancel within accidental tap protection window."""
    incident = db.query(Incident).filter(Incident.id == id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "CANCELLED"
    incident.updated_at = datetime.datetime.utcnow()

    ev = IncidentEvent(
        incident_id=incident.id,
        event_type="CANCELLED_BY_USER",
        title="Citizen Cancelled Request",
        description="Emergency marked cancelled (accidental tap reported).",
        performed_by="Citizen"
    )
    db.add(ev)
    db.commit()

    record_audit_log(db, "INCIDENT_CANCELLED", "INCIDENT", incident.id, "Citizen", {"reason": "Accidental tap"})

    await manager.broadcast({
        "type": "INCIDENT_CANCELLED",
        "incident_id": incident.id,
        "code": incident.code
    })

    return {"success": True, "message": "Emergency SOS cancelled."}
