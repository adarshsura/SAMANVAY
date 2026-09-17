import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database.models import Zone, Hospital, Shelter, Resource, RoadAccessibility, Incident

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in kilometers using the Haversine formula."""
    R = 6371.0 # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def compute_location_intelligence(lat: float, lon: float, db: Session) -> Dict[str, Any]:
    # 1. Determine zone
    zones = db.query(Zone).all()
    assigned_zone = None
    min_dist_to_zone = float("inf")

    for z in zones:
        dist = calculate_haversine_distance(lat, lon, z.center_latitude, z.center_longitude)
        if dist < min_dist_to_zone:
            min_dist_to_zone = dist
            assigned_zone = z

    zone_code = assigned_zone.code if assigned_zone else "Zone B"
    zone_name = assigned_zone.name if assigned_zone else "Kothrud / Riverside Basin"
    zone_vuln = assigned_zone.vulnerability_index if assigned_zone else 0.85
    zone_pop = assigned_zone.population if assigned_zone else 85000

    # Population exposure
    if zone_pop > 80000 or zone_vuln > 0.7:
        pop_exposure = "HIGH"
    elif zone_pop > 50000 or zone_vuln > 0.4:
        pop_exposure = "MODERATE"
    else:
        pop_exposure = "LOW"

    # 2. Nearest Hospital
    hospitals = db.query(Hospital).all()
    nearest_hospital_data = None
    min_hosp_dist = float("inf")
    for h in hospitals:
        dist = calculate_haversine_distance(lat, lon, h.latitude, h.longitude)
        if dist < min_hosp_dist:
            min_hosp_dist = dist
            nearest_hospital_data = {
                "id": h.id,
                "name": h.name,
                "distance_km": dist,
                "available_beds": h.available_beds,
                "trauma_capable": h.trauma_capable
            }

    # 3. Nearest Shelter
    shelters = db.query(Shelter).all()
    nearest_shelter_data = None
    min_shelter_dist = float("inf")
    for s in shelters:
        dist = calculate_haversine_distance(lat, lon, s.latitude, s.longitude)
        if dist < min_shelter_dist:
            min_shelter_dist = dist
            nearest_shelter_data = {
                "id": s.id,
                "name": s.name,
                "distance_km": dist,
                "capacity": s.capacity,
                "current_occupancy": s.current_occupancy
            }

    # 4. Nearest Resources
    resources = db.query(Resource).filter(Resource.status.in_(["AVAILABLE", "ASSIGNED"])).all()
    nearest_amb_dist = 999.0
    nearest_rescue_dist = 999.0
    nearest_boat_dist = 999.0
    nearest_fire_dist = 999.0

    for r in resources:
        dist = calculate_haversine_distance(lat, lon, r.latitude, r.longitude)
        if r.resource_type == "Ambulance" and dist < nearest_amb_dist:
            nearest_amb_dist = dist
        elif r.resource_type == "Rescue Team" and dist < nearest_rescue_dist:
            nearest_rescue_dist = dist
        elif r.resource_type == "Rescue Boat" and dist < nearest_boat_dist:
            nearest_boat_dist = dist
        elif r.resource_type == "Fire Unit" and dist < nearest_fire_dist:
            nearest_fire_dist = dist

    # 5. Road accessibility in this zone
    roads = db.query(RoadAccessibility).filter(RoadAccessibility.zone_code == zone_code).all()
    if roads:
        avg_access = sum(r.accessibility_percentage for r in roads) / len(roads)
        blocked_count = sum(1 for r in roads if r.is_blocked)
    else:
        avg_access = 85.0
        blocked_count = 0

    road_access_pct = max(10, int(avg_access - (blocked_count * 25)))

    # 6. Hazard context based on zone characteristics
    hazard_contexts = {
        "Zone A": "Dense Urban Core - High Pedestrian & Traffic Congestion",
        "Zone B": "Severe River Overbank Flooding (Mutha River Basin)",
        "Zone C": "Heavy Industrial Area - Chemical & Factory Vulnerability",
        "Zone D": "Transit Transport Hub - Major Underpass Vulnerability",
        "Zone E": "High-Rise Residential & Commercial Technology Parks"
    }
    hazard_context = hazard_contexts.get(zone_code, "Mixed Urban Terrain with Seasonal Hazard Exposure")

    # 7. Nearby active incidents
    active_incidents = db.query(Incident).filter(
        Incident.status.in_(["RECEIVED", "VERIFIED", "DISPATCHED", "EN_ROUTE", "ON_SCENE"])
    ).all()
    nearby_incidents_count = 0
    for inc in active_incidents:
        if calculate_haversine_distance(lat, lon, inc.latitude, inc.longitude) <= 2.0:
            nearby_incidents_count += 1

    return {
        "zone": zone_code,
        "zone_name": zone_name,
        "population_exposure": pop_exposure,
        "zone_vulnerability_index": zone_vuln,
        "nearest_hospital": nearest_hospital_data,
        "nearest_shelter": nearest_shelter_data,
        "nearest_ambulance_km": round(nearest_amb_dist, 1) if nearest_amb_dist < 900 else None,
        "nearest_rescue_team_km": round(nearest_rescue_dist, 1) if nearest_rescue_dist < 900 else None,
        "nearest_rescue_boat_km": round(nearest_boat_dist, 1) if nearest_boat_dist < 900 else None,
        "nearest_fire_unit_km": round(nearest_fire_dist, 1) if nearest_fire_dist < 900 else None,
        "road_accessibility_pct": road_access_pct,
        "hazard_context": hazard_context,
        "nearby_active_incidents_count": nearby_incidents_count,
        "is_estimated": True
    }
