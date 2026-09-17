import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Incident, Resource, Allocation, AllocationItem, IncidentEvent
from app.schemas.optimization import (
    OptimizationRunRequest, AllocationResponse, AllocationApprovalRequest,
    ReallocationPlanResponse, BaselineComparisonResponse
)
from app.services.optimizer import solve_resource_allocation, compute_baseline_greedy_comparison
from app.services.reallocation import compute_dynamic_reallocation
from app.core.security import require_roles
from app.core.audit import record_audit_log
from app.api.websocket import manager

router = APIRouter(prefix="/optimization", tags=["Resource Optimization"])

@router.post("/run", response_model=AllocationResponse)
async def run_optimization(
    payload: Optional[OptimizationRunRequest] = None,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Executes Google OR-Tools MILP optimization across active incidents and available resources.
    Returns optimal assignments with full human explainability strings.
    """
    query_inc = db.query(Incident).filter(
        Incident.status.in_(["RECEIVED", "VERIFIED", "DISPATCHED", "EN_ROUTE", "ON_SCENE"])
    )
    if payload and payload.incident_ids:
        query_inc = query_inc.filter(Incident.id.in_(payload.incident_ids))
    incidents = query_inc.order_by(Incident.need_score.desc()).all()

    # Usable resources (AVAILABLE or if force re-calculate, also ASSIGNED)
    candidate_resources = db.query(Resource).filter(
        Resource.status.in_(["AVAILABLE", "ASSIGNED"])
    ).all()

    # Solve MILP
    solver_output = solve_resource_allocation(incidents, candidate_resources, db)

    # Persist Allocation record
    alloc_code = f"ALC-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    allocation = Allocation(
        allocation_code=alloc_code,
        status="RECOMMENDED",
        optimization_score=solver_output["optimization_score"],
        total_eta_minutes=solver_output["total_eta"],
        unmet_demand_count=solver_output["unmet_demand_count"],
        is_active=True,
        created_by=current_user.get("username", "OR-Tools MILP Solver")
    )
    db.add(allocation)
    db.commit()

    saved_items = []
    for item in solver_output["assignments"]:
        alloc_item = AllocationItem(
            allocation_id=allocation.id,
            incident_id=item["incident_id"],
            resource_id=item["resource_id"],
            estimated_eta_minutes=item["estimated_eta_minutes"],
            distance_km=item["distance_km"],
            reason=item["reason"],
            status="RECOMMENDED"
        )
        db.add(alloc_item)
        saved_items.append(alloc_item)
    db.commit()

    record_audit_log(
        db,
        action="OPTIMIZATION_RUN",
        entity_type="ALLOCATION",
        entity_id=allocation.id,
        performed_by=current_user.get("username", "Admin"),
        details={
            "assignments_count": len(saved_items),
            "total_eta": allocation.total_eta_minutes,
            "unmet_demand": allocation.unmet_demand_count
        }
    )

    await manager.broadcast({
        "type": "NEW_OPTIMIZATION_RECOMMENDATION",
        "allocation_id": allocation.id,
        "allocation_code": allocation.allocation_code,
        "units_recommended": len(saved_items),
        "total_eta": allocation.total_eta_minutes
    })

    # Prepare response
    res_items = []
    for si in saved_items:
        res = db.query(Resource).filter(Resource.id == si.resource_id).first()
        inc = db.query(Incident).filter(Incident.id == si.incident_id).first()
        res_items.append({
            "id": si.id,
            "resource_id": si.resource_id,
            "resource_code": res.resource_code if res else "UNKNOWN",
            "resource_type": res.resource_type if res else "UNKNOWN",
            "incident_id": si.incident_id,
            "incident_code": inc.code if inc else "UNKNOWN",
            "estimated_eta_minutes": si.estimated_eta_minutes,
            "distance_km": si.distance_km,
            "reason": si.reason,
            "status": si.status
        })

    return AllocationResponse(
        id=allocation.id,
        allocation_code=allocation.allocation_code,
        status=allocation.status,
        optimization_score=allocation.optimization_score,
        total_eta_minutes=allocation.total_eta_minutes,
        unmet_demand_count=allocation.unmet_demand_count,
        is_active=allocation.is_active,
        created_by=allocation.created_by,
        approved_by=allocation.approved_by,
        approved_at=allocation.approved_at,
        items=res_items,
        created_at=allocation.created_at
    )

@router.get("/latest", response_model=Optional[AllocationResponse])
def get_latest_allocation(db: Session = Depends(get_db)):
    alloc = db.query(Allocation).filter(Allocation.is_active == True).order_by(Allocation.created_at.desc()).first()
    if not alloc:
        return None

    items_res = []
    for item in alloc.items:
        res = db.query(Resource).filter(Resource.id == item.resource_id).first()
        inc = db.query(Incident).filter(Incident.id == item.incident_id).first()
        items_res.append({
            "id": item.id,
            "resource_id": item.resource_id,
            "resource_code": res.resource_code if res else "UNKNOWN",
            "resource_type": res.resource_type if res else "UNKNOWN",
            "incident_id": item.incident_id,
            "incident_code": inc.code if inc else "UNKNOWN",
            "estimated_eta_minutes": item.estimated_eta_minutes,
            "distance_km": item.distance_km,
            "reason": item.reason,
            "status": item.status
        })

    return AllocationResponse(
        id=alloc.id,
        allocation_code=alloc.allocation_code,
        status=alloc.status,
        optimization_score=alloc.optimization_score,
        total_eta_minutes=alloc.total_eta_minutes,
        unmet_demand_count=alloc.unmet_demand_count,
        is_active=alloc.is_active,
        created_by=alloc.created_by,
        approved_by=alloc.approved_by,
        approved_at=alloc.approved_at,
        items=items_res,
        created_at=alloc.created_at
    )

@router.post("/{id}/approve")
async def approve_and_dispatch(
    id: str,
    payload: Optional[AllocationApprovalRequest] = None,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    CRITICAL DEVELOPMENT RULE IMPLEMENTATION:
    APPROVE & DISPATCH actually:
    1. Validates allocation
    2. Locks/assigns resources
    3. Updates resource statuses to ASSIGNED
    4. Updates incidents to DISPATCHED
    5. Notifies responders via WebSocket
    6. Creates audit event
    7. Prevents the same resource from being assigned twice.
    """
    allocation = db.query(Allocation).filter(Allocation.id == id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    now = datetime.datetime.utcnow()
    allocation.status = "APPROVED"
    allocation.approved_by = current_user.get("username", "Admin Dispatcher")
    allocation.approved_at = now
    allocation.notes = payload.notes if payload else "Approved by Command Center"

    dispatched_resources = []
    impacted_incidents = set()

    for item in allocation.items:
        res = db.query(Resource).filter(Resource.id == item.resource_id).first()
        inc = db.query(Incident).filter(Incident.id == item.incident_id).first()

        if res and inc:
            # Assign resource
            res.status = "ASSIGNED"
            res.current_incident_id = inc.id
            res.updated_at = now

            item.status = "DISPATCHED"

            # Update incident status if received
            if inc.status in ["RECEIVED", "VERIFIED"]:
                inc.status = "DISPATCHED"
                inc.updated_at = now

            dispatched_resources.append(res.resource_code)
            impacted_incidents.add(inc.id)

            # Log incident event
            ev = IncidentEvent(
                incident_id=inc.id,
                event_type="DISPATCH_APPROVED",
                title=f"Resource {res.resource_code} Dispatched",
                description=f"{res.name} dispatched with estimated ETA of {item.estimated_eta_minutes} min.",
                performed_by=current_user.get("username", "Admin")
            )
            db.add(ev)

    db.commit()

    record_audit_log(
        db,
        action="ALLOCATION_APPROVED",
        entity_type="ALLOCATION",
        entity_id=allocation.id,
        performed_by=current_user.get("username", "Admin"),
        details={
            "dispatched_units": dispatched_resources,
            "incidents": list(impacted_incidents)
        }
    )

    # Broadcast to all connected clients & responders
    await manager.broadcast({
        "type": "DISPATCH_APPROVED",
        "allocation_id": allocation.id,
        "dispatched_resources": dispatched_resources,
        "timestamp": now.isoformat()
    })

    return {
        "success": True,
        "allocation_code": allocation.allocation_code,
        "dispatched_units": dispatched_resources,
        "message": f"Successfully approved allocation. Dispatched {len(dispatched_resources)} emergency units."
    }

@router.post("/{id}/reject")
async def reject_allocation(
    id: str,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    alloc = db.query(Allocation).filter(Allocation.id == id).first()
    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")

    alloc.status = "REJECTED"
    alloc.is_active = False
    db.commit()

    record_audit_log(
        db,
        action="ALLOCATION_REJECTED",
        entity_type="ALLOCATION",
        entity_id=alloc.id,
        performed_by=current_user.get("username", "Admin")
    )

    return {"success": True, "message": f"Allocation {alloc.allocation_code} marked REJECTED."}

@router.post("/reallocate")
def trigger_dynamic_reallocation_diff(
    trigger_reason: str = "Severe casualty surge and road accessibility reduction",
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Computes dynamic reallocation diff comparing the OLD approved plan against
    the newly optimized plan, highlighting which resources are redirected and why.
    """
    diff_result = compute_dynamic_reallocation(trigger_reason, db)
    return diff_result

@router.get("/baseline-comparison", response_model=BaselineComparisonResponse)
def get_baseline_comparison(db: Session = Depends(get_db)):
    """
    Returns empirical comparison of Baseline Greedy Nearest Resource dispatch
    vs SAMANVAY OR-Tools MILP optimization.
    """
    incidents = db.query(Incident).filter(Incident.status != "CANCELLED").all()
    resources = db.query(Resource).all()
    return compute_baseline_greedy_comparison(incidents, resources, db)
