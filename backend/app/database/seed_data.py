import datetime
from sqlalchemy.orm import Session
from app.database.models import (
    User, Responder, Resource, Zone, Hospital, Shelter, RoadAccessibility, Incident, IncidentEvent
)
from app.core.security import hash_password

def seed_all_data(db: Session):
    # Check if already seeded
    if db.query(User).filter(User.username == "admin").first():
        return

    print("[SEED] Starting database seeding for SAMANVAY AI...")

    # 1. Users
    admin_user = User(
        username="admin",
        email="command.center@raahat.gov.in",
        hashed_password=hash_password("admin123"),
        role="ADMIN",
        is_active=True
    )
    resp1_user = User(
        username="responder1",
        email="pravin.jadhav@raahat.gov.in",
        hashed_password=hash_password("resp123"),
        role="RESPONDER",
        is_active=True
    )
    resp2_user = User(
        username="responder2",
        email="sunita.rao@raahat.gov.in",
        hashed_password=hash_password("resp123"),
        role="RESPONDER",
        is_active=True
    )
    db.add_all([admin_user, resp1_user, resp2_user])
    db.commit()

    # 2. Responders
    r1 = Responder(
        user_id=resp1_user.id,
        name="Pravin Jadhav",
        responder_code="RESP-01",
        organization="Pune EMS Unit",
        role="Paramedic Lead",
        team_unit="ALS Squad Alpha",
        qualification="Advanced Life Support, Trauma Triage",
        phone="+91 98230 11223",
        current_status="AVAILABLE",
        last_latitude=18.5204,
        last_longitude=73.8567
    )
    r2 = Responder(
        user_id=resp2_user.id,
        name="Sunita Rao",
        responder_code="RESP-02",
        organization="National Disaster Response Force (NDRF)",
        role="Rescue Commander",
        team_unit="Water Rescue Battalion 5",
        qualification="Swift Water Rescue, Collapsed Structure Specialist",
        phone="+91 98230 44556",
        current_status="AVAILABLE",
        last_latitude=18.5089,
        last_longitude=73.8077
    )
    db.add_all([r1, r2])
    db.commit()

    # 3. Zones
    zones_data = [
        {"code": "Zone A", "name": "Shivajinagar Central", "pop": 65000, "vuln": 0.45, "lat": 18.5314, "lon": 73.8446},
        {"code": "Zone B", "name": "Kothrud / Riverside Basin", "pop": 85000, "vuln": 0.85, "lat": 18.5074, "lon": 73.8077},
        {"code": "Zone C", "name": "Hadapsar Industrial Belt", "pop": 92000, "vuln": 0.65, "lat": 18.5089, "lon": 73.9260},
        {"code": "Zone D", "name": "Swargate Transit Corridor", "pop": 58000, "vuln": 0.50, "lat": 18.5018, "lon": 73.8636},
        {"code": "Zone E", "name": "Aundh / Baner Tech Corridor", "pop": 72000, "vuln": 0.35, "lat": 18.5590, "lon": 73.7868},
    ]
    for zd in zones_data:
        z = Zone(
            code=zd["code"],
            name=zd["name"],
            population=zd["pop"],
            vulnerability_index=zd["vuln"],
            center_latitude=zd["lat"],
            center_longitude=zd["lon"],
            radius_km=4.5
        )
        db.add(z)
    db.commit()

    # 4. Hospitals
    hospitals_data = [
        {"name": "Sassoon General Hospital (Govt Apex)", "zone": "Zone A", "lat": 18.5256, "lon": 73.8742, "beds": 450, "avail": 72, "icu": 14, "trauma": True, "phone": "+91 20 2612 8000"},
        {"name": "Deenanath Mangeshkar Hospital", "zone": "Zone B", "lat": 18.5012, "lon": 73.8322, "beds": 350, "avail": 48, "icu": 10, "trauma": True, "phone": "+91 20 4015 1000"},
        {"name": "Sahyadri Super Speciality Hospital", "zone": "Zone B", "lat": 18.5134, "lon": 73.8340, "beds": 220, "avail": 31, "icu": 6, "trauma": True, "phone": "+91 20 6721 3000"},
        {"name": "Noble Hospital Hadapsar", "zone": "Zone C", "lat": 18.5034, "lon": 73.9298, "beds": 280, "avail": 54, "icu": 8, "trauma": True, "phone": "+91 20 6628 5000"},
        {"name": "Ruby Hall Clinic Wanowrie", "zone": "Zone D", "lat": 18.4902, "lon": 73.8967, "beds": 180, "avail": 29, "icu": 5, "trauma": True, "phone": "+91 20 6645 5100"},
    ]
    for hd in hospitals_data:
        h = Hospital(
            name=hd["name"],
            zone_code=hd["zone"],
            latitude=hd["lat"],
            longitude=hd["lon"],
            total_beds=hd["beds"],
            available_beds=hd["avail"],
            icu_available=hd["icu"],
            trauma_capable=hd["trauma"],
            contact_phone=hd["phone"]
        )
        db.add(h)
    db.commit()

    # 5. Shelters
    shelters_data = [
        {"name": "Shivajinagar Municipal Relief Center", "zone": "Zone A", "lat": 18.5300, "lon": 73.8500, "cap": 600, "occ": 110},
        {"name": "Kothrud Community Sports Hall", "zone": "Zone B", "lat": 18.5045, "lon": 73.8150, "cap": 800, "occ": 180},
        {"name": "Hadapsar Magarpatta Relief Center", "zone": "Zone C", "lat": 18.5150, "lon": 73.9350, "cap": 750, "occ": 95},
        {"name": "Swargate Multipurpose Shelter", "zone": "Zone D", "lat": 18.4990, "lon": 73.8610, "cap": 500, "occ": 70},
        {"name": "Balewadi High Capacity Relief Camp", "zone": "Zone E", "lat": 18.5720, "lon": 73.7710, "cap": 1200, "occ": 210},
    ]
    for sd in shelters_data:
        s = Shelter(
            name=sd["name"],
            zone_code=sd["zone"],
            latitude=sd["lat"],
            longitude=sd["lon"],
            capacity=sd["cap"],
            current_occupancy=sd["occ"]
        )
        db.add(s)
    db.commit()

    # 6. Road Accessibility Data
    roads_data = [
        {"name": "Karve Road Arterial", "zone": "Zone B", "flat": 18.5080, "flon": 73.8250, "tlat": 18.5020, "tlon": 73.8050, "pct": 85, "blocked": False},
        {"name": "Mutha Riverbank Road", "zone": "Zone B", "flat": 18.5150, "flon": 73.8350, "tlat": 18.5050, "tlon": 73.8150, "pct": 42, "blocked": False, "reason": "Waterlogging 1.5ft"},
        {"name": "Hadapsar Bypass Express", "zone": "Zone C", "flat": 18.5100, "flon": 73.9150, "tlat": 18.5050, "tlon": 73.9400, "pct": 95, "blocked": False},
        {"name": "Shivajinagar FC Road", "zone": "Zone A", "flat": 18.5280, "flon": 73.8400, "tlat": 18.5350, "tlon": 73.8460, "pct": 90, "blocked": False},
        {"name": "Swargate Junction Underpass", "zone": "Zone D", "flat": 18.5010, "flon": 73.8620, "tlat": 18.5030, "tlon": 73.8650, "pct": 75, "blocked": False},
    ]
    for rd in roads_data:
        r = RoadAccessibility(
            road_name=rd["name"],
            zone_code=rd["zone"],
            from_latitude=rd["flat"],
            from_longitude=rd["flon"],
            to_latitude=rd["tlat"],
            to_longitude=rd["tlon"],
            accessibility_percentage=rd["pct"],
            is_blocked=rd["blocked"],
            block_reason=rd.get("reason")
        )
        db.add(r)
    db.commit()

    # 7. Resources (29 Specialized Units)
    # 10 Ambulances
    amb_coords = [
        (18.5260, 73.8730), (18.5020, 73.8330), (18.5140, 73.8350), (18.5040, 73.9280), (18.4910, 73.8950),
        (18.5320, 73.8460), (18.5090, 73.8110), (18.5580, 73.7880), (18.5010, 73.8640), (18.5180, 73.8520)
    ]
    for i, (lat, lon) in enumerate(amb_coords, start=1):
        res = Resource(
            resource_code=f"AMB-{i:02d}",
            resource_type="Ambulance",
            name=f"Advanced Life Support Ambulance {i:02d}",
            capacity=2 if i % 2 == 1 else 4,
            latitude=lat,
            longitude=lon,
            base_latitude=lat,
            base_longitude=lon,
            status="AVAILABLE",
            skills=["TRAUMA_CARE", "OXYGEN_SUPPORT", "CRITICAL_TRANSPORT"],
            battery_level=90 + (i % 10),
            communication_status="ONLINE"
        )
        db.add(res)

    # 5 Rescue Teams
    rescue_coords = [
        (18.5100, 73.8120), (18.5290, 73.8430), (18.5070, 73.9210), (18.5005, 73.8625), (18.5610, 73.7890)
    ]
    for i, (lat, lon) in enumerate(rescue_coords, start=1):
        res = Resource(
            resource_code=f"RESCUE-{i:02d}",
            resource_type="Rescue Team",
            name=f"Specialized SAR Unit {i:02d}",
            capacity=6,
            latitude=lat,
            longitude=lon,
            base_latitude=lat,
            base_longitude=lon,
            status="AVAILABLE",
            skills=["COLLAPSED_STRUCTURE", "HIGH_ANGLE", "SEARCH_LOCATE", "EXTRICATION"],
            battery_level=85 + (i * 2),
            communication_status="ONLINE"
        )
        db.add(res)

    # 3 Rescue Boats
    boat_coords = [
        (18.5120, 73.8200), (18.5050, 73.8100), (18.5180, 73.8300)
    ]
    for i, (lat, lon) in enumerate(boat_coords, start=1):
        res = Resource(
            resource_code=f"BOAT-{i:02d}",
            resource_type="Rescue Boat",
            name=f"Inflatable Swiftwater Boat {i:02d}",
            capacity=8,
            latitude=lat,
            longitude=lon,
            base_latitude=lat,
            base_longitude=lon,
            status="AVAILABLE",
            skills=["WATER_RESCUE", "FLOOD_EVACUATION", "SHALLAW_DRAFT"],
            battery_level=92,
            communication_status="ONLINE"
        )
        db.add(res)

    # 4 Medical Teams
    med_coords = [
        (18.5250, 73.8700), (18.5030, 73.8300), (18.5050, 73.9250), (18.5570, 73.7900)
    ]
    for i, (lat, lon) in enumerate(med_coords, start=1):
        res = Resource(
            resource_code=f"MED-{i:02d}",
            resource_type="Medical Team",
            name=f"Mobile Triage & Surgical Team {i:02d}",
            capacity=10,
            latitude=lat,
            longitude=lon,
            base_latitude=lat,
            base_longitude=lon,
            status="AVAILABLE",
            skills=["TRIAGE", "EMERGENCY_SURGERY", "MEDICATION_DISPENSE"],
            battery_level=88,
            communication_status="ONLINE"
        )
        db.add(res)

    # 2 Fire Units
    fire_coords = [(18.5300, 73.8480), (18.5060, 73.8640)]
    for i, (lat, lon) in enumerate(fire_coords, start=1):
        res = Resource(
            resource_code=f"FIRE-{i:02d}",
            resource_type="Fire Unit",
            name=f"Heavy Water Tender & Foam Unit {i:02d}",
            capacity=5,
            latitude=lat,
            longitude=lon,
            base_latitude=lat,
            base_longitude=lon,
            status="AVAILABLE",
            skills=["FIRE_SUPPRESSION", "HAZMAT_CONTROL", "STRUCTURAL_STABILIZATION"],
            battery_level=96,
            communication_status="ONLINE"
        )
        db.add(res)

    # 5 Relief Supply Units
    relief_coords = [
        (18.5280, 73.8520), (18.5060, 73.8180), (18.5110, 73.9310), (18.4980, 73.8600), (18.5630, 73.7850)
    ]
    for i, (lat, lon) in enumerate(relief_coords, start=1):
        res = Resource(
            resource_code=f"RELIEF-{i:02d}",
            resource_type="Relief Supply Unit",
            name=f"Rapid Relief & Ration Truck {i:02d}",
            capacity=500,
            latitude=lat,
            longitude=lon,
            base_latitude=lat,
            base_longitude=lon,
            status="AVAILABLE",
            skills=["RATION_DISTRIBUTION", "POTABLE_WATER", "BLANKETS_TENTS"],
            battery_level=89,
            communication_status="ONLINE"
        )
        db.add(res)
    db.commit()

    # 8. Seed Sample Incident for the Hackathon Flood Scenario (INC-1047 in Zone B)
    inc_1047 = Incident(
        code="INC-1047",
        session_id="seed-session-zone-b-riverside",
        latitude=18.5074,
        longitude=73.8077,
        zone_code="Zone B",
        disaster_type="Flood",
        description="Severe river overflow near Mutha bank residential societies. Rapidly rising flood waters, people trapped on upper balconies.",
        reported_people=600,
        reported_injured=65,
        reported_trapped=120,
        hazard_level="CRITICAL",
        confidence=88,
        status="RECEIVED",
        source="CITIZEN_WEB",
        event_count=12,
        need_score=94.2,
        need_priority="CRITICAL",
        need_breakdown={
            "medical_severity": 85.0,
            "people_affected": 95.0,
            "unmet_demand": 92.0,
            "accessibility": 58.0,
            "vulnerability": 85.0,
            "weights_used": {
                "medical": 0.30,
                "people": 0.25,
                "demand": 0.20,
                "accessibility": 0.15,
                "vulnerability": 0.10
            }
        },
        predicted_demand={
            "Ambulance": {"min": 4, "recommended": 6},
            "Rescue Team": {"min": 2, "recommended": 3},
            "Rescue Boat": {"min": 2, "recommended": 3},
            "Medical Team": {"min": 1, "recommended": 2},
            "Relief Supply Unit": {"min": 2, "recommended": 4}
        },
        location_intelligence={
            "zone": "Zone B",
            "zone_name": "Kothrud / Riverside Basin",
            "population_exposure": "HIGH",
            "nearest_hospital": {"name": "Sahyadri Super Speciality Hospital", "distance_km": 2.1},
            "nearest_shelter": {"name": "Kothrud Community Sports Hall", "distance_km": 0.8},
            "nearest_ambulance_km": 1.2,
            "nearest_rescue_team_km": 0.6,
            "road_accessibility_pct": 42,
            "hazard_context": "Severe River Overbank Flooding (Mutha River)"
        },
        verification_status="CORROBORATED",
        verification_signals=["GPS_RECEIVED", "MULTIPLE_CITIZEN_TAPS_12", "HAZARD_RIVER_OVERFLOW"]
    )
    db.add(inc_1047)
    db.commit()

    ev1 = IncidentEvent(
        incident_id=inc_1047.id,
        event_type="SOS_CREATED",
        title="Initial Emergency SOS Triggered",
        description="First emergency beacon triggered from Riverside Society, Zone B.",
        performed_by="Citizen (Anonymous)"
    )
    ev2 = IncidentEvent(
        incident_id=inc_1047.id,
        event_type="CORROBORATION",
        title="12 Corroborating Reports Clustered",
        description="12 reports received within 150m. Affected estimate revised to 600.",
        performed_by="System Clustering Engine"
    )
    db.add_all([ev1, ev2])
    db.commit()

    print("[SEED] Seeding completed successfully: 3 users, 29 resources, 5 zones, 5 hospitals, 5 shelters, 1 critical incident.")
