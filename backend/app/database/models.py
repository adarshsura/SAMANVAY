import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="CITIZEN") # ADMIN, RESPONDER, CITIZEN
    organization_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    org_type = Column(String(50), default="EMERGENCY_SERVICES") # NDRF, MUNICIPAL_FIRE, EMS, POLICE, NGO
    contact_phone = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Responder(Base):
    __tablename__ = "responders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    responder_code = Column(String(30), unique=True, nullable=False, index=True) # e.g. RESP-01
    organization = Column(String(100), default="Pune Disaster Response Force")
    role = Column(String(50), default="Paramedic Lead")
    team_unit = Column(String(50), default="Quick Response Unit 3")
    qualification = Column(String(100), default="ALS Trauma & Flood Rescue Specialist")
    current_status = Column(String(30), default="AVAILABLE") # AVAILABLE, ASSIGNED, EN_ROUTE, ON_SCENE, BUSY, OFFLINE
    assigned_resource_id = Column(String(36), nullable=True)
    phone = Column(String(30), nullable=True)
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_active_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resource_code = Column(String(30), unique=True, nullable=False, index=True) # e.g. AMB-07, RESCUE-02
    resource_type = Column(String(50), nullable=False, index=True) # Ambulance, Rescue Team, Rescue Boat, Fire Unit, Medical Team, Relief Supply Unit
    organization_id = Column(String(36), nullable=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, default=4)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    base_latitude = Column(Float, nullable=False)
    base_longitude = Column(Float, nullable=False)
    status = Column(String(30), default="AVAILABLE", index=True) # AVAILABLE, ASSIGNED, EN_ROUTE, ON_SCENE, BUSY, RETURNING, OFFLINE, MAINTENANCE, UNKNOWN
    skills = Column(JSON, default=list) # ["WATER_RESCUE", "EXTRICATION", "TRAUMA", "HAZMAT"]
    current_incident_id = Column(String(36), nullable=True)
    last_seen_at = Column(DateTime, default=datetime.datetime.utcnow)
    battery_level = Column(Integer, default=95) # Percentage
    communication_status = Column(String(20), default="ONLINE") # ONLINE, DEGRADED, OFFLINE
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ResourceStatusHistory(Base):
    __tablename__ = "resource_status_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    resource_id = Column(String(36), ForeignKey("resources.id"), nullable=False)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    note = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(30), unique=True, nullable=False, index=True) # e.g. INC-1047
    session_id = Column(String(100), nullable=True, index=True) # citizen client device session ID
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone_code = Column(String(20), default="Zone B")
    disaster_type = Column(String(50), default="Unknown") # Flood, Building Collapse, Fire, Earthquake, Landslide, Other, Unknown
    description = Column(Text, nullable=True)
    reported_people = Column(Integer, default=1)
    reported_injured = Column(Integer, default=0)
    reported_trapped = Column(Integer, default=0)
    hazard_level = Column(String(30), default="MODERATE") # LOW, MODERATE, HIGH, CRITICAL
    confidence = Column(Integer, default=70) # 0-100
    status = Column(String(30), default="RECEIVED", index=True) # RECEIVED, VERIFIED, DISPATCHED, EN_ROUTE, ON_SCENE, RESOLVED, CLOSED, CANCELLED
    source = Column(String(30), default="CITIZEN_WEB") # CITIZEN_WEB, RESPONDER, SIMULATION
    event_count = Column(Integer, default=1) # Count of duplicate taps/corroborations
    cluster_id = Column(String(36), nullable=True)
    
    # Dynamic Need Score (0-100)
    need_score = Column(Float, default=50.0)
    need_priority = Column(String(20), default="HIGH") # LOW, MODERATE, HIGH, CRITICAL
    need_breakdown = Column(JSON, default=dict) # {medical_severity, people_affected, unmet_demand, accessibility, vulnerability}
    
    # Resource Demand Prediction
    predicted_demand = Column(JSON, default=dict) # {"Ambulance": {"min": 2, "recommended": 3}, ...}
    
    # Location Intelligence
    location_intelligence = Column(JSON, default=dict) # {zone, population_exposure, nearest_hospital_km, road_accessibility_pct, hazard_context}
    
    # Verification System
    verification_status = Column(String(30), default="UNVERIFIED") # UNVERIFIED, LIKELY, CORROBORATED, CONFIRMED, DISMISSED_AFTER_REVIEW
    verification_signals = Column(JSON, default=list) # ["GPS_FIX", "HAZARD_OVERLAY", "CITIZEN_FOLLOWUP"]
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    reports = relationship("IncidentReport", back_populates="incident", cascade="all, delete-orphan")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")
    field_updates = relationship("FieldUpdate", back_populates="incident", cascade="all, delete-orphan")

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False)
    session_id = Column(String(100), nullable=True)
    answers = Column(JSON, default=dict) # adaptive questionnaire answers
    text_notes = Column(Text, nullable=True)
    voice_transcript = Column(Text, nullable=True)
    photo_url = Column(String(255), nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="reports")

class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False)
    event_type = Column(String(50), nullable=False) # SOS_CREATED, DUPLICATE_TAP, DETAILS_ADDED, DISPATCHED, RESPONDER_ARRIVED, FIELD_UPDATE, CLOSED
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    performed_by = Column(String(100), default="System")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="events")

class Zone(Base):
    __tablename__ = "zones"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(20), unique=True, nullable=False) # Zone A, Zone B, Zone C, Zone D, Zone E
    name = Column(String(100), nullable=False)
    population = Column(Integer, default=50000)
    vulnerability_index = Column(Float, default=0.5) # 0.0 - 1.0
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_km = Column(Float, default=4.0)

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    zone_code = Column(String(20), default="Zone B")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    total_beds = Column(Integer, default=300)
    available_beds = Column(Integer, default=45)
    icu_available = Column(Integer, default=8)
    trauma_capable = Column(Boolean, default=True)
    contact_phone = Column(String(30), default="+91 20 2612 0000")

class Shelter(Base):
    __tablename__ = "shelters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    zone_code = Column(String(20), default="Zone B")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, default=500)
    current_occupancy = Column(Integer, default=120)
    food_water_supply_days = Column(Integer, default=5)
    contact_phone = Column(String(30), default="+91 20 2553 1111")

class RoadAccessibility(Base):
    __tablename__ = "road_accessibility"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    road_name = Column(String(100), nullable=False)
    zone_code = Column(String(20), nullable=False)
    from_latitude = Column(Float, nullable=False)
    from_longitude = Column(Float, nullable=False)
    to_latitude = Column(Float, nullable=False)
    to_longitude = Column(Float, nullable=False)
    accessibility_percentage = Column(Integer, default=100) # 0 = blocked, 100 = open
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    allocation_code = Column(String(30), unique=True, nullable=False) # e.g. ALC-2026-001
    status = Column(String(30), default="RECOMMENDED") # RECOMMENDED, APPROVED, MODIFIED, REJECTED, SUPERSEDED
    optimization_score = Column(Float, default=0.0)
    total_eta_minutes = Column(Float, default=0.0)
    unmet_demand_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), default="OR-Tools Optimizer")
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    items = relationship("AllocationItem", back_populates="allocation", cascade="all, delete-orphan")

class AllocationItem(Base):
    __tablename__ = "allocation_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    allocation_id = Column(String(36), ForeignKey("allocations.id"), nullable=False)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False)
    resource_id = Column(String(36), ForeignKey("resources.id"), nullable=False)
    estimated_eta_minutes = Column(Float, default=10.0)
    distance_km = Column(Float, default=3.5)
    reason = Column(Text, nullable=False) # Explainable reason
    status = Column(String(30), default="RECOMMENDED") # RECOMMENDED, DISPATCHED, ACCEPTED, EN_ROUTE, ON_SCENE, COMPLETED, REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    allocation = relationship("Allocation", back_populates="items")
    incident = relationship("Incident")
    resource = relationship("Resource")

class FieldUpdate(Base):
    __tablename__ = "field_updates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False)
    responder_id = Column(String(36), nullable=False)
    responder_name = Column(String(100), default="Responder")
    rescued_count = Column(Integer, default=0)
    injured_count = Column(Integer, default=0)
    trapped_count = Column(Integer, default=0)
    road_status = Column(String(100), nullable=True)
    extra_resources_needed = Column(String(255), nullable=True)
    text_report = Column(Text, nullable=True)
    audio_transcript = Column(Text, nullable=True)
    photo_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="field_updates")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action = Column(String(50), nullable=False) # SOS_CREATED, ALLOCATION_APPROVED, REALLOCATION_TRIGGERED, STATUS_CHANGED
    entity_type = Column(String(50), nullable=False) # INCIDENT, RESOURCE, ALLOCATION, USER
    entity_id = Column(String(36), nullable=False)
    performed_by = Column(String(100), nullable=False) # citizen, admin, responder
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scenario_name = Column(String(100), nullable=False)
    status = Column(String(30), default="RUNNING") # RUNNING, COMPLETED, RESET
    initial_conditions = Column(JSON, default=dict)
    injected_events = Column(JSON, default=list)
    performance_metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
