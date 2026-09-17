import datetime
from typing import Dict, Any, Optional
from app.core.config import settings

def calculate_need_score(
    reported_injured: int,
    reported_trapped: int,
    reported_people: int,
    road_accessibility_pct: int,
    zone_vulnerability_index: float,
    assigned_resources_count: int = 0,
    required_resources_count: int = 4,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Computes an explainable Need Score (0-100) using configurable weights.
    Returns the final score, priority level, and full component breakdown.
    """
    weights = custom_weights or {
        "medical_severity": settings.WEIGHT_MEDICAL_SEVERITY,
        "people_affected": settings.WEIGHT_PEOPLE_AFFECTED,
        "unmet_demand": settings.WEIGHT_UNMET_DEMAND,
        "accessibility": settings.WEIGHT_ACCESSIBILITY,
        "vulnerability": settings.WEIGHT_VULNERABILITY
    }

    # Component 1: Medical Severity (0 - 100)
    # Injured and trapped count have heavy influence
    med_score = min(100.0, (reported_injured * 5.0) + (reported_trapped * 4.0))
    if reported_injured == 0 and reported_trapped == 0:
        med_score = 15.0

    # Component 2: People Affected (0 - 100)
    # Scaled response
    if reported_people <= 5:
        people_score = reported_people * 6.0
    elif reported_people <= 50:
        people_score = 30.0 + (reported_people - 5) * 1.0
    else:
        people_score = min(100.0, 75.0 + (reported_people - 50) * 0.05)

    # Component 3: Unmet Demand (0 - 100)
    if required_resources_count <= 0:
        unmet_score = 0.0
    else:
        unmet_ratio = max(0.0, (required_resources_count - assigned_resources_count) / required_resources_count)
        unmet_score = unmet_ratio * 100.0

    # Component 4: Accessibility Inaccessibility Penalty (0 - 100)
    # Low accessibility -> High need
    inaccessibility_score = max(0.0, min(100.0, 100.0 - float(road_accessibility_pct)))

    # Component 5: Vulnerability (0 - 100)
    vulnerability_score = max(0.0, min(100.0, float(zone_vulnerability_index) * 100.0))

    # Calculate weighted total
    final_score = (
        (med_score * weights["medical_severity"]) +
        (people_score * weights["people_affected"]) +
        (unmet_score * weights["unmet_demand"]) +
        (inaccessibility_score * weights["accessibility"]) +
        (vulnerability_score * weights["vulnerability"])
    )
    final_score = round(max(5.0, min(100.0, final_score)), 1)

    # Assign priority label
    if final_score >= 80.0:
        priority = "CRITICAL"
    elif final_score >= 60.0:
        priority = "HIGH"
    elif final_score >= 40.0:
        priority = "MODERATE"
    else:
        priority = "LOW"

    return {
        "need_score": final_score,
        "need_priority": priority,
        "calculation_timestamp": datetime.datetime.utcnow().isoformat(),
        "breakdown": {
            "medical_severity": round(med_score, 1),
            "people_affected": round(people_score, 1),
            "unmet_demand": round(unmet_score, 1),
            "accessibility": round(inaccessibility_score, 1),
            "vulnerability": round(vulnerability_score, 1),
            "weights_used": weights
        }
    }
