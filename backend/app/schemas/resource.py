from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ResourceItemResponse(BaseModel):
    id: str
    resource_code: str
    resource_type: str
    name: str
    capacity: int
    latitude: float
    longitude: float
    base_latitude: float
    base_longitude: float
    status: str
    skills: List[str]
    current_incident_id: Optional[str] = None
    last_seen_at: datetime
    battery_level: int
    communication_status: str
    is_stale: bool = False

class ResourceCreateRequest(BaseModel):
    resource_code: str
    resource_type: str
    name: str
    capacity: int = 4
    latitude: float
    longitude: float
    skills: Optional[List[str]] = None

class ResourceStatusUpdateRequest(BaseModel):
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    note: Optional[str] = None

class ResourceHeartbeatRequest(BaseModel):
    resource_id: str
    latitude: float
    longitude: float
    status: Optional[str] = None
    battery_level: Optional[int] = None
    connectivity_state: Optional[str] = "ONLINE"
