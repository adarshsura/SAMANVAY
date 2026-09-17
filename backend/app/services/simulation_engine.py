import datetime
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database.models import (
    Incident, Resource, RoadAccessibility, IncidentEvent, Allocation, AllocationItem, SimulationRun
)
from app.services.location_intelligence import compute_location_intelligence
from app.services.incident_ai import analyze_incident_data
from app.services.need_score import calculate_need_score
from app.services.demand_predictor import predict_resource_demand
from app.services.optimizer import solve_resource_allocation
from app.services.reallocation import compute_dynamic_reallocation
from app.database.seed_data import seed_all_data

def start_simulation(scenario_name: str, db: Session) -> Dict[str, Any]:
    run = SimulationRun(
        scenario_name=scenario_name,
        status="RUNNING",
        initial_conditions={"started_at": datetime.datetime.utcnow().isoformat(), "scenario": scenario_name},
        injected_events=[]
    )
    db.add(run)
    db.commit()
    return {"simulation_id": run.id, "scenario": scenario_name, "status": "RUNNING"}

def inject_simulation_event(
    event_type: str, # INJECT_INCIDENT, BLOCK_ROAD, DISABLE_RESOURCE, SURGE_CASUALTIES
    payload: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    Executes a simulation event and immediately impacts real state.
    """
    now = datetime.datetime.utcnow()

    if event_type == "INJECT_INCIDENT":
        zone_code = payload.get("zone_code", "Zone C")
        lat = payload.get("latitude", 18.5089)
        lon = payload.get("longitude", 73.9260)
        disaster_type = payload.get("disaster_type", "Flood")
        people = payload.get("reported_people", 150)
        injured = payload.get("reported_injured", 40)
        trapped = payload.get("reported_trapped", 25)

        loc_intel = compute_location_intelligence(lat, lon, db)
        need_res = calculate_need_score(
            reported_injured=injured,
            reported_trapped=trapped,
            reported_people=people,
            road_accessibility_pct=loc_intel.get("road_accessibility_pct", 80),
            zone_vulnerability_index=loc_intel.get("zone_vulnerability_index", 0.6)
        )
        demands = predict_resource_demand(
            disaster_type=disaster_type,
            reported_people=people,
            reported_injured=injured,
            reported_trapped=trapped,
            road_accessibility_pct=loc_intel.get("road_accessibility_pct", 80)
        )

        code = f"INC-SIM-{uuid.uuid4().hex[:4].upper()}"
        inc = Incident(
            code=code,
            session_id=f"sim-{code.lower()}",
            latitude=lat,
            longitude=lon,
            zone_code=zone_code,
            disaster_type=disaster_type,
            description=payload.get("description", f"Simulated high-priority {disaster_type} escalation in {zone_code}."),
            reported_people=people,
            reported_injured=injured,
            reported_trapped=trapped,
            hazard_level="CRITICAL",
            confidence=90,
            status="RECEIVED",
            source="SIMULATION",
            need_score=need_res["need_score"],
            need_priority=need_res["need_priority"],
            need_breakdown=need_res["breakdown"],
            predicted_demand=demands,
            location_intelligence=loc_intel,
            verification_status="CONFIRMED",
            verification_signals=["SIMULATION_CONTROL_CENTER"]
        )
        db.add(inc)
        db.commit()

        ev = IncidentEvent(
            incident_id=inc.id,
            event_type="SIMULATION_INJECTION",
            title="Simulated Incident Injected",
            description=f"Injected {disaster_type} with {injured} critical casualties in {zone_code}.",
            performed_by="Disaster Simulation Engine"
        )
        db.add(ev)
        db.commit()

        return {
            "success": True,
            "event_type": event_type,
            "incident_id": inc.id,
            "incident_code": inc.code,
            "need_score": inc.need_score,
            "message": f"Injected incident {code} in {zone_code}"
        }

    elif event_type == "BLOCK_ROAD":
        zone_code = payload.get("zone_code", "Zone B")
        road = db.query(RoadAccessibility).filter(RoadAccessibility.zone_code == zone_code).first()
        if road:
            road.is_blocked = True
            road.accessibility_percentage = 15
            road.block_reason = payload.get("reason", "Water level 4ft - Inundated arterial link")
            road.updated_at = now
            db.commit()
            return {
                "success": True,
                "event_type": event_type,
                "road_name": road.road_name,
                "accessibility_pct": road.accessibility_percentage,
                "message": f"Blocked road {road.road_name} in {zone_code}"
            }
        return {"success": False, "message": f"No roads registered in {zone_code}"}

    elif event_type == "DISABLE_RESOURCE":
        res_code = payload.get("resource_code", "AMB-07")
        res = db.query(Resource).filter(Resource.resource_code == res_code).first()
        if res:
            res.status = "MAINTENANCE"
            res.communication_status = "DEGRADED"
            res.updated_at = now
            db.commit()
            return {
                "success": True,
                "event_type": event_type,
                "resource_code": res_code,
                "new_status": "MAINTENANCE",
                "message": f"Resource {res_code} marked unavailable due to mechanical failure."
            }
        return {"success": False, "message": f"Resource {res_code} not found"}

    elif event_type == "SURGE_CASUALTIES":
        inc_code = payload.get("incident_code", "INC-1047")
        inc = db.query(Incident).filter(Incident.code == inc_code).first()
        if inc:
            inc.reported_injured += payload.get("added_injured", 40)
            inc.reported_trapped += payload.get("added_trapped", 20)
            inc.reported_people += payload.get("added_people", 100)

            # Recompute need score and demand
            loc_intel = inc.location_intelligence or {}
            need_res = calculate_need_score(
                reported_injured=inc.reported_injured,
                reported_trapped=inc.reported_trapped,
                reported_people=inc.reported_people,
                road_accessibility_pct=loc_intel.get("road_accessibility_pct", 50),
                zone_vulnerability_index=loc_intel.get("zone_vulnerability_index", 0.8)
            )
            demands = predict_resource_demand(
                disaster_type=inc.disaster_type,
                reported_people=inc.reported_people,
                reported_injured=inc.reported_injured,
                reported_trapped=inc.reported_trapped,
                road_accessibility_pct=loc_intel.get("road_accessibility_pct", 50)
            )
            inc.need_score = need_res["need_score"]
            inc.need_priority = need_res["need_priority"]
            inc.need_breakdown = need_res["breakdown"]
            inc.predicted_demand = demands
            inc.updated_at = now
            db.commit()

            return {
                "success": True,
                "event_type": event_type,
                "incident_code": inc_code,
                "new_injured": inc.reported_injured,
                "new_need_score": inc.need_score,
                "message": f"Surged casualties for {inc_code}. Need score revised to {inc.need_score}."
            }
        return {"success": False, "message": f"Incident {inc_code} not found"}

    return {"success": False, "message": f"Unknown event type {event_type}"}

def reset_simulation_state(db: Session) -> Dict[str, Any]:
    """
    Cleans up all incidents, allocations, field updates, and resets seed state.
    """
    db.query(AllocationItem).delete()
    db.query(Allocation).delete()
    db.query(IncidentEvent).delete()
    db.query(Incident).delete()
    db.query(Resource).delete()
    db.query(RoadAccessibility).delete()
    db.query(Hospital).delete()
    db.query(Shelter).delete()
    db.query(SimulationRun).delete()
    db.commit()

    # Re-seed fresh baseline
    seed_all_data(db)
    return {"success": True, "message": "Simulation state successfully reset to initial clean baseline."}
