import datetime
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Incident, IncidentEvent
from app.services.location_intelligence import calculate_haversine_distance
from app.core.config import settings

def check_duplicate_or_cluster(
    session_id: str,
    lat: float,
    lon: float,
    db: Session
) -> Tuple[Optional[Incident], bool, str]:
    """
    Checks whether this SOS is:
    1. A repeated tap from the same session/device.
    2. A nearby report within the spatial cluster radius (150m) and time window (3 minutes).
    Returns (existing_incident, is_duplicate, match_type).
    """
    cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=settings.SOS_CLUSTER_TIME_WINDOW_SECONDS)

    # 1. Exact session match within recent window
    session_match = db.query(Incident).filter(
        Incident.session_id == session_id,
        Incident.status.in_(["RECEIVED", "VERIFIED", "DISPATCHED", "EN_ROUTE", "ON_SCENE"]),
        Incident.created_at >= cutoff_time
    ).first()

    if session_match:
        return session_match, True, "SESSION_REPEAT"

    # 2. Spatial proximity match within 150m (0.15 km) and time window
    recent_active_incidents = db.query(Incident).filter(
        Incident.status.in_(["RECEIVED", "VERIFIED", "DISPATCHED", "EN_ROUTE", "ON_SCENE"]),
        Incident.created_at >= cutoff_time
    ).all()

    for inc in recent_active_incidents:
        dist_km = calculate_haversine_distance(lat, lon, inc.latitude, inc.longitude)
        dist_meters = dist_km * 1000.0
        if dist_meters <= settings.SOS_CLUSTER_DISTANCE_METERS:
            return inc, True, "SPATIAL_CLUSTER"

    return None, False, "NEW_INCIDENT"

def update_incident_corroboration(incident: Incident, match_type: str, db: Session):
    """
    Updates incident event count, corroboration signals, confidence, and estimated affected count.
    """
    incident.event_count = (incident.event_count or 1) + 1
    
    signals = list(incident.verification_signals or [])
    if match_type == "SESSION_REPEAT":
        if "REPEATED_CITIZEN_TAPS" not in signals:
            signals.append("REPEATED_CITIZEN_TAPS")
        incident.confidence = min(95, (incident.confidence or 70) + 5)
    elif match_type == "SPATIAL_CLUSTER":
        signal_label = f"CLUSTERED_REPORTS_{incident.event_count}"
        signals.append(signal_label)
        # Corroboration increases confidence significantly
        incident.confidence = min(98, (incident.confidence or 70) + 8)
        # Multiple independent reports suggest higher casualty/affected count
        incident.reported_people = max(incident.reported_people, incident.event_count * 2)

    # Update verification status
    if incident.confidence >= 90:
        incident.verification_status = "CONFIRMED"
    elif incident.confidence >= 75:
        incident.verification_status = "CORROBORATED"
    elif incident.confidence >= 60:
        incident.verification_status = "LIKELY"
    else:
        incident.verification_status = "UNVERIFIED"

    incident.verification_signals = signals
    incident.updated_at = datetime.datetime.utcnow()

    # Log event
    event = IncidentEvent(
        incident_id=incident.id,
        event_type="CORROBORATION_UPDATE",
        title=f"SOS Corroborated ({match_type})",
        description=f"Tap event incremented to {incident.event_count}. Confidence now {incident.confidence}%.",
        performed_by="Anti-Prank & Clustering Engine"
    )
    db.add(event)
    db.commit()
