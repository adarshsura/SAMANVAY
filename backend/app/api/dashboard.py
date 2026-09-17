from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import (
    Incident, Resource, Zone, Hospital, Shelter, RoadAccessibility, Allocation
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    active_incidents = db.query(Incident).filter(
        Incident.status.in_(["RECEIVED", "VERIFIED", "DISPATCHED", "EN_ROUTE", "ON_SCENE"])
    ).all()

    critical_count = sum(1 for inc in active_incidents if inc.need_score >= 75.0 or inc.need_priority == "CRITICAL")

    resources = db.query(Resource).all()
    available_res = [r for r in resources if r.status == "AVAILABLE"]
    deployed_res = [r for r in resources if r.status in ["ASSIGNED", "EN_ROUTE", "ON_SCENE"]]

    latest_alloc = db.query(Allocation).filter(
        Allocation.is_active == True,
        Allocation.status.in_(["RECOMMENDED", "APPROVED"])
    ).order_by(Allocation.created_at.desc()).first()

    avg_eta = 0.0
    unmet = 0
    if latest_alloc:
        unmet = latest_alloc.unmet_demand_count
        if latest_alloc.items:
            avg_eta = round(latest_alloc.total_eta_minutes / len(latest_alloc.items), 1)

    return {
        "active_incidents": len(active_incidents),
        "critical_incidents": critical_count,
        "available_resources": len(available_res),
        "deployed_resources": len(deployed_res),
        "total_resources": len(resources),
        "unmet_demand": unmet,
        "average_response_eta_min": avg_eta
    }

@router.get("/infrastructure")
def get_infrastructure_overlay(db: Session = Depends(get_db)):
    zones = db.query(Zone).all()
    hospitals = db.query(Hospital).all()
    shelters = db.query(Shelter).all()
    roads = db.query(RoadAccessibility).all()

    return {
        "zones": [
            {
                "id": z.id,
                "code": z.code,
                "name": z.name,
                "population": z.population,
                "vulnerability_index": z.vulnerability_index,
                "latitude": z.center_latitude,
                "longitude": z.center_longitude,
                "radius_km": z.radius_km
            }
            for z in zones
        ],
        "hospitals": [
            {
                "id": h.id,
                "name": h.name,
                "zone_code": h.zone_code,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "total_beds": h.total_beds,
                "available_beds": h.available_beds,
                "icu_available": h.icu_available,
                "trauma_capable": h.trauma_capable,
                "contact_phone": h.contact_phone
            }
            for h in hospitals
        ],
        "shelters": [
            {
                "id": s.id,
                "name": s.name,
                "zone_code": s.zone_code,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "capacity": s.capacity,
                "current_occupancy": s.current_occupancy
            }
            for s in shelters
        ],
        "roads": [
            {
                "id": r.id,
                "name": r.road_name,
                "zone_code": r.zone_code,
                "from_lat": r.from_latitude,
                "from_lon": r.from_longitude,
                "to_lat": r.to_latitude,
                "to_lon": r.to_longitude,
                "accessibility_pct": r.accessibility_percentage,
                "is_blocked": r.is_blocked,
                "block_reason": r.block_reason
            }
            for r in roads
        ]
    }
