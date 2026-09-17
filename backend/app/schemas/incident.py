from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SosCreateRequest(BaseModel):
    session_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: Optional[str] = None

class SosCreateResponse(BaseModel):
    incident_id: str
    code: str
    status: str
    location_captured: bool
    latitude: float
    longitude: float
    is_duplicate: bool
    event_count: int
    message: str

class IncidentDetailsRequest(BaseModel):
    session_id: Optional[str] = None
    disaster_type: Optional[str] = None
    answers: Optional[Dict[str, Any]] = None
    text_notes: Optional[str] = None
    voice_transcript: Optional[str] = None
    photo_url: Optional[str] = None
    reported_people: Optional[int] = None
    reported_injured: Optional[int] = None
    reported_trapped: Optional[int] = None

class IncidentVerificationRequest(BaseModel):
    verification_status: str # UNVERIFIED, LIKELY, CORROBORATED, CONFIRMED, DISMISSED_AFTER_REVIEW
    confidence: Optional[int] = None
    notes: Optional[str] = None

class IncidentEventResponse(BaseModel):
    id: str
    event_type: str
    title: str
    description: Optional[str] = None
    performed_by: str
    created_at: datetime

class IncidentItemResponse(BaseModel):
    id: str
    code: str
    session_id: Optional[str] = None
    latitude: float
    longitude: float
    zone_code: str
    disaster_type: str
    description: Optional[str] = None
    reported_people: int
    reported_injured: int
    reported_trapped: int
    hazard_level: str
    confidence: int
    status: str
    source: str
    event_count: int
    need_score: float
    need_priority: str
    need_breakdown: Optional[Dict[str, Any]] = None
    predicted_demand: Optional[Dict[str, Any]] = None
    location_intelligence: Optional[Dict[str, Any]] = None
    verification_status: str
    verification_signals: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

class FieldUpdateRequest(BaseModel):
    responder_id: str
    rescued_count: Optional[int] = 0
    injured_count: Optional[int] = 0
    trapped_count: Optional[int] = 0
    road_status: Optional[str] = None
    extra_resources_needed: Optional[str] = None
    text_report: Optional[str] = None
    audio_transcript: Optional[str] = None
    photo_url: Optional[str] = None
