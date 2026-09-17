import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Resource, ResourceStatusHistory
from app.schemas.resource import (
    ResourceItemResponse, ResourceCreateRequest, ResourceStatusUpdateRequest, ResourceHeartbeatRequest
)
from app.core.security import require_roles, get_current_user_optional
from app.core.config import settings
from app.api.websocket import manager
from app.core.audit import record_audit_log

router = APIRouter(prefix="/resources", tags=["Resources"])

@router.get("", response_model=List[ResourceItemResponse])
def list_resources(
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    now = datetime.datetime.utcnow()
    query = db.query(Resource)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    if status:
        query = query.filter(Resource.status == status)

    resources = query.order_by(Resource.resource_code.asc()).all()
    results = []

    for r in resources:
        # Check staleness
        is_stale = False
        status_val = r.status
        comm_status = r.communication_status
        if r.last_seen_at:
            delta_seconds = (now - r.last_seen_at).total_seconds()
            if delta_seconds > settings.RESOURCE_HEARTBEAT_TIMEOUT_SECONDS:
                is_stale = True
                if r.status not in ["OFFLINE", "MAINTENANCE"]:
                    status_val = "UNKNOWN"
                    comm_status = "DEGRADED"

        results.append(ResourceItemResponse(
            id=r.id,
            resource_code=r.resource_code,
            resource_type=r.resource_type,
            name=r.name,
            capacity=r.capacity,
            latitude=r.latitude,
            longitude=r.longitude,
            base_latitude=r.base_latitude,
            base_longitude=r.base_longitude,
            status=status_val,
            skills=r.skills or [],
            current_incident_id=r.current_incident_id,
            last_seen_at=r.last_seen_at,
            battery_level=r.battery_level,
            communication_status=comm_status,
            is_stale=is_stale
        ))

    db.commit()
    return results

@router.post("", response_model=ResourceItemResponse)
def create_resource(
    payload: ResourceCreateRequest,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    existing = db.query(Resource).filter(Resource.resource_code == payload.resource_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Resource {payload.resource_code} already exists")

    new_res = Resource(
        resource_code=payload.resource_code,
        resource_type=payload.resource_type,
        name=payload.name,
        capacity=payload.capacity,
        latitude=payload.latitude,
        longitude=payload.longitude,
        base_latitude=payload.latitude,
        base_longitude=payload.longitude,
        status="AVAILABLE",
        skills=payload.skills or [],
        battery_level=100,
        communication_status="ONLINE"
    )
    db.add(new_res)
    db.commit()

    record_audit_log(
        db,
        action="RESOURCE_CREATED",
        entity_type="RESOURCE",
        entity_id=new_res.id,
        performed_by=current_user.get("username", "Admin"),
        details={"code": new_res.resource_code, "type": new_res.resource_type}
    )

    return ResourceItemResponse(
        id=new_res.id,
        resource_code=new_res.resource_code,
        resource_type=new_res.resource_type,
        name=new_res.name,
        capacity=new_res.capacity,
        latitude=new_res.latitude,
        longitude=new_res.longitude,
        base_latitude=new_res.base_latitude,
        base_longitude=new_res.base_longitude,
        status=new_res.status,
        skills=new_res.skills,
        current_incident_id=None,
        last_seen_at=new_res.last_seen_at,
        battery_level=new_res.battery_level,
        communication_status=new_res.communication_status,
        is_stale=False
    )

@router.patch("/{id}/status")
async def update_resource_status(
    id: str,
    payload: ResourceStatusUpdateRequest,
    current_user: dict = Depends(require_roles(["ADMIN", "RESPONDER"])),
    db: Session = Depends(get_db)
):
    res = db.query(Resource).filter(Resource.id == id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")

    old_status = res.status
    res.status = payload.status
    if payload.latitude and payload.longitude:
        res.latitude = payload.latitude
        res.longitude = payload.longitude
    res.last_seen_at = datetime.datetime.utcnow()

    # Log history
    hist = ResourceStatusHistory(
        resource_id=res.id,
        previous_status=old_status,
        new_status=payload.status,
        latitude=res.latitude,
        longitude=res.longitude,
        note=payload.note
    )
    db.add(hist)
    db.commit()

    await manager.broadcast({
        "type": "RESOURCE_STATUS_CHANGED",
        "resource_id": res.id,
        "resource_code": res.resource_code,
        "status": res.status,
        "latitude": res.latitude,
        "longitude": res.longitude
    })

    return {"success": True, "resource_code": res.resource_code, "status": res.status}

@router.post("/heartbeat")
async def receive_heartbeat(payload: ResourceHeartbeatRequest, db: Session = Depends(get_db)):
    res = db.query(Resource).filter(Resource.id == payload.resource_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")

    res.latitude = payload.latitude
    res.longitude = payload.longitude
    res.last_seen_at = datetime.datetime.utcnow()
    res.communication_status = payload.connectivity_state or "ONLINE"
    if payload.status:
        res.status = payload.status
    if payload.battery_level is not None:
        res.battery_level = payload.battery_level

    db.commit()
    return {"success": True, "message": "Heartbeat registered"}
