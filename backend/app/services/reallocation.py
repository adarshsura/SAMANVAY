import datetime
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database.models import Incident, Resource, Allocation, AllocationItem, AuditLog
from app.services.optimizer import solve_resource_allocation

def compute_dynamic_reallocation(
    trigger_reason: str,
    db: Session,
    priority_incident_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates system delta, re-runs OR-Tools MILP optimization, and constructs
    a clear diff between the current active plan and the recommended new plan.
    """
    # 1. Fetch current active allocation
    active_allocation = db.query(Allocation).filter(
        Allocation.is_active == True,
        Allocation.status == "APPROVED"
    ).order_by(Allocation.created_at.desc()).first()

    old_plan_by_resource: Dict[str, Dict[str, Any]] = {}
    if active_allocation:
        for item in active_allocation.items:
            res = db.query(Resource).filter(Resource.id == item.resource_id).first()
            inc = db.query(Incident).filter(Incident.id == item.incident_id).first()
            if res and inc:
                old_plan_by_resource[res.id] = {
                    "resource_code": res.resource_code,
                    "resource_type": res.resource_type,
                    "incident_id": inc.id,
                    "incident_code": inc.code,
                    "eta_minutes": item.estimated_eta_minutes
                }

    # 2. Fetch all active incidents needing response
    active_incidents = db.query(Incident).filter(
        Incident.status.in_(["RECEIVED", "VERIFIED", "DISPATCHED", "EN_ROUTE", "ON_SCENE"])
    ).order_by(Incident.need_score.desc()).all()

    # 3. Fetch all usable resources (AVAILABLE or currently ASSIGNED if reallocatable)
    candidate_resources = db.query(Resource).filter(
        Resource.status.in_(["AVAILABLE", "ASSIGNED", "EN_ROUTE"])
    ).all()

    # 4. Run optimization
    new_opt_result = solve_resource_allocation(active_incidents, candidate_resources, db)
    new_assignments = new_opt_result.get("assignments", [])

    # 5. Detect changes (Diff)
    changes: List[Dict[str, Any]] = []
    affected_incidents_set = set()

    for new_item in new_assignments:
        res_id = new_item["resource_id"]
        new_inc_id = new_item["incident_id"]
        affected_incidents_set.add(new_item["incident_code"])

        old_assignment = old_plan_by_resource.get(res_id)
        if not old_assignment:
            # New assignment
            changes.append({
                "resource_id": res_id,
                "resource_code": new_item["resource_code"],
                "resource_type": new_item["resource_type"],
                "old_incident_id": None,
                "old_incident_code": "None (Standby)",
                "new_incident_id": new_inc_id,
                "new_incident_code": new_item["incident_code"],
                "old_eta_minutes": None,
                "new_eta_minutes": new_item["estimated_eta_minutes"],
                "reason": f"Dispatched to {new_item['incident_code']} due to {trigger_reason}"
            })
        elif old_assignment["incident_id"] != new_inc_id:
            # Resource redirected!
            affected_incidents_set.add(old_assignment["incident_code"])
            changes.append({
                "resource_id": res_id,
                "resource_code": new_item["resource_code"],
                "resource_type": new_item["resource_type"],
                "old_incident_id": old_assignment["incident_id"],
                "old_incident_code": old_assignment["incident_code"],
                "new_incident_id": new_inc_id,
                "new_incident_code": new_item["incident_code"],
                "old_eta_minutes": old_assignment["eta_minutes"],
                "new_eta_minutes": new_item["estimated_eta_minutes"],
                "reason": f"Redirected from {old_assignment['incident_code']} to higher-criticality {new_item['incident_code']}: {trigger_reason}"
            })

    # Summary structures
    old_plan_summary = {
        "active_allocation_code": active_allocation.allocation_code if active_allocation else "None",
        "total_units_deployed": len(old_plan_by_resource),
        "status": active_allocation.status if active_allocation else "STANDBY"
    }

    new_plan_summary = {
        "total_recommended_units": len(new_assignments),
        "total_eta_minutes": new_opt_result.get("total_eta", 0.0),
        "unmet_demand_count": new_opt_result.get("unmet_demand_count", 0),
        "optimization_score": new_opt_result.get("optimization_score", 0.0)
    }

    realloc_id = f"REALLOC-{uuid.uuid4().hex[:8].upper()}"

    return {
        "reallocation_id": realloc_id,
        "trigger_reason": trigger_reason,
        "affected_incidents": list(affected_incidents_set),
        "changes": changes,
        "new_assignments": new_assignments,
        "old_plan_summary": old_plan_summary,
        "new_plan_summary": new_plan_summary,
        "requires_approval": True,
        "generated_at": datetime.datetime.utcnow().isoformat()
    }
