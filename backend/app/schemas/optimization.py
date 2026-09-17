from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AllocationItemResponse(BaseModel):
    id: str
    resource_id: str
    resource_code: str
    resource_type: str
    incident_id: str
    incident_code: str
    estimated_eta_minutes: float
    distance_km: float
    reason: str
    status: str

class AllocationResponse(BaseModel):
    id: str
    allocation_code: str
    status: str
    optimization_score: float
    total_eta_minutes: float
    unmet_demand_count: int
    is_active: bool
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    items: List[AllocationItemResponse] = []
    created_at: datetime

class OptimizationRunRequest(BaseModel):
    incident_ids: Optional[List[str]] = None
    force_recalculate: bool = False

class ReallocationChangeItem(BaseModel):
    resource_id: str
    resource_code: str
    resource_type: str
    old_incident_id: Optional[str] = None
    old_incident_code: Optional[str] = None
    new_incident_id: str
    new_incident_code: str
    old_eta_minutes: Optional[float] = None
    new_eta_minutes: float
    reason: str

class ReallocationPlanResponse(BaseModel):
    reallocation_id: str
    trigger_reason: str
    affected_incidents: List[str]
    changes: List[ReallocationChangeItem]
    old_plan_summary: Dict[str, Any]
    new_plan_summary: Dict[str, Any]
    requires_approval: bool = True
    generated_at: datetime

class AllocationApprovalRequest(BaseModel):
    approved_by: Optional[str] = "Command Center Admin"
    notes: Optional[str] = None
    modified_items: Optional[List[Dict[str, Any]]] = None

class BaselineComparisonMetrics(BaseModel):
    average_eta_minutes: float
    total_travel_distance_km: float
    unmet_demand_count: int
    critical_incidents_covered_percentage: float
    resource_utilization_percentage: float

class BaselineComparisonResponse(BaseModel):
    scenario: str
    incident_count: int
    resource_count: int
    baseline_greedy: BaselineComparisonMetrics
    samanvay_milp: BaselineComparisonMetrics
    raahat_milp: Optional[BaselineComparisonMetrics] = None
    improvement_summary: Dict[str, str]
