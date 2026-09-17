import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Incident, IncidentEvent, IncidentReport, Resource, AllocationItem
from app.schemas.incident import (
    IncidentItemResponse, IncidentVerificationRequest, IncidentEventResponse
)
from app.core.security import require_roles, get_current_user_optional
from app.core.audit import record_audit_log
from app.api.websocket import manager

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("", response_model=List[IncidentItemResponse])
def list_incidents(
    status: Optional[str] = None,
    disaster_type: Optional[str] = None,
    zone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    else:
        # Default active filter excludes CANCELLED unless asked
        query = query.filter(Incident.status != "CANCELLED")
    if disaster_type:
        query = query.filter(Incident.disaster_type == disaster_type)
    if zone:
        query = query.filter(Incident.zone_code == zone)

    incidents = query.order_by(Incident.need_score.desc(), Incident.created_at.desc()).all()
    return incidents

@router.get("/{id}")
def get_incident_detail(id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events = db.query(IncidentEvent).filter(
        IncidentEvent.incident_id == incident.id
    ).order_by(IncidentEvent.created_at.desc()).all()

    reports = db.query(IncidentReport).filter(
        IncidentReport.incident_id == incident.id
    ).order_by(IncidentReport.submitted_at.desc()).all()

    # Find active allocated resources
    allocated_items = db.query(AllocationItem).filter(
        AllocationItem.incident_id == incident.id
    ).all()

    assigned_resources = []
    for item in allocated_items:
        res = db.query(Resource).filter(Resource.id == item.resource_id).first()
        if res:
            assigned_resources.append({
                "resource_code": res.resource_code,
                "resource_type": res.resource_type,
                "name": res.name,
                "status": res.status,
                "eta_minutes": item.estimated_eta_minutes
            })

    return {
        "incident": incident,
        "events": events,
        "reports": reports,
        "assigned_resources": assigned_resources
    }

@router.post("/{id}/verify")
async def verify_incident(
    id: str,
    payload: IncidentVerificationRequest,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    incident = db.query(Incident).filter(Incident.id == id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_status = incident.verification_status
    incident.verification_status = payload.verification_status
    if payload.confidence is not None:
        incident.confidence = payload.confidence
    elif payload.verification_status == "CONFIRMED":
        incident.confidence = 98

    incident.updated_at = datetime.datetime.utcnow()

    # Timeline event
    ev = IncidentEvent(
        incident_id=incident.id,
        event_type="VERIFICATION_STATUS_CHANGED",
        title=f"Verification Updated: {payload.verification_status}",
        description=payload.notes or f"Status changed from {old_status} to {payload.verification_status}.",
        performed_by=current_user.get("username", "Admin")
    )
    db.add(ev)
    db.commit()

    record_audit_log(
        db,
        action="INCIDENT_VERIFIED",
        entity_type="INCIDENT",
        entity_id=incident.id,
        performed_by=current_user.get("username", "Admin"),
        details={"old_status": old_status, "new_status": payload.verification_status}
    )

    await manager.broadcast({
        "type": "VERIFICATION_CHANGED",
        "incident_id": incident.id,
        "verification_status": incident.verification_status,
        "confidence": incident.confidence
    })

    return {"success": True, "verification_status": incident.verification_status}

@router.post("/{id}/close")
async def close_incident(
    id: str,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Closes an incident and frees up any assigned resources back to AVAILABLE."""
    incident = db.query(Incident).filter(Incident.id == id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "CLOSED"
    incident.updated_at = datetime.datetime.utcnow()

    # Free resources assigned to this incident
    resources = db.query(Resource).filter(Resource.current_incident_id == incident.id).all()
    freed_codes = []
    for r in resources:
        r.status = "AVAILABLE"
        r.current_incident_id = None
        freed_codes.append(r.resource_code)

    ev = IncidentEvent(
        incident_id=incident.id,
        event_type="INCIDENT_CLOSED",
        title="Incident Operations Closed",
        description=f"Incident closed by {current_user.get('username')}. Freed resources: {', '.join(freed_codes) if freed_codes else 'None'}.",
        performed_by=current_user.get("username", "Admin")
    )
    db.add(ev)
    db.commit()

    record_audit_log(
        db,
        action="INCIDENT_CLOSED",
        entity_type="INCIDENT",
        entity_id=incident.id,
        performed_by=current_user.get("username", "Admin"),
        details={"freed_resources": freed_codes}
    )

    await manager.broadcast({
        "type": "INCIDENT_CLOSED",
        "incident_id": incident.id,
        "freed_resources": freed_codes
    })

    return {"success": True, "message": f"Incident {incident.code} closed. Freed resources: {freed_codes}"}
