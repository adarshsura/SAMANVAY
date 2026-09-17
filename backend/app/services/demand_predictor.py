import math
from typing import Dict, Any

def predict_resource_demand(
    disaster_type: str,
    reported_people: int,
    reported_injured: int,
    reported_trapped: int,
    road_accessibility_pct: int = 100
) -> Dict[str, Dict[str, Any]]:
    """
    Predicts minimum and recommended emergency resources based on disaster type,
    casualty numbers, trapped victims, and terrain accessibility.
    """
    demand = {}
    access_multiplier = 1.2 if road_accessibility_pct < 50 else 1.0

    # 1. Ambulances
    if reported_injured > 0:
        amb_min = max(1, math.ceil(reported_injured / 4))
        amb_rec = max(amb_min + 1, math.ceil((reported_injured / 2) * access_multiplier))
    else:
        amb_min = 1
        amb_rec = 2
    demand["Ambulance"] = {"min": amb_min, "recommended": amb_rec, "confidence": 85}

    # 2. Rescue Teams
    if reported_trapped > 0 or disaster_type in ["Building Collapse", "Landslide"]:
        rt_min = max(1, math.ceil(reported_trapped / 15))
        rt_rec = max(rt_min + 1, math.ceil((reported_trapped / 8) * access_multiplier))
    elif disaster_type == "Flood" and reported_people > 20:
        rt_min = 1
        rt_rec = 2
    else:
        rt_min = 0
        rt_rec = 1
    if rt_rec > 0:
        demand["Rescue Team"] = {"min": rt_min, "recommended": rt_rec, "confidence": 80}

    # 3. Rescue Boats (Specialized for Flood)
    if disaster_type == "Flood":
        boat_min = max(1, math.ceil((reported_trapped + (reported_people * 0.2)) / 30))
        boat_rec = max(boat_min + 1, math.ceil(boat_min * 1.5))
        demand["Rescue Boat"] = {"min": boat_min, "recommended": boat_rec, "confidence": 90}

    # 4. Fire Units (Fire & Hazardous Collapse)
    if disaster_type == "Fire":
        fire_min = 2 if reported_people > 30 else 1
        fire_rec = max(fire_min + 1, 3)
        demand["Fire Unit"] = {"min": fire_min, "recommended": fire_rec, "confidence": 92}
    elif disaster_type == "Building Collapse" and reported_trapped > 10:
        demand["Fire Unit"] = {"min": 1, "recommended": 1, "confidence": 70}

    # 5. Medical Teams (On-scene Triage & Stabilization)
    if reported_injured >= 5 or reported_people >= 100:
        med_min = max(1, math.ceil(reported_injured / 25))
        med_rec = max(med_min, math.ceil(reported_injured / 15))
        demand["Medical Team"] = {"min": med_min, "recommended": med_rec, "confidence": 82}

    # 6. Relief Supply Units (Food, Water, Blankets)
    if reported_people >= 20:
        rel_min = max(1, math.ceil(reported_people / 200))
        rel_rec = max(rel_min + 1, math.ceil(reported_people / 100))
        demand["Relief Supply Unit"] = {"min": rel_min, "recommended": rel_rec, "confidence": 78}

    return demand
