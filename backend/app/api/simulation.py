from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database.session import get_db
from app.services.simulation_engine import start_simulation, inject_simulation_event, reset_simulation_state
from app.core.security import require_roles
from app.api.websocket import manager

router = APIRouter(prefix="/simulation", tags=["Disaster Simulation"])

@router.post("/start")
async def api_start_simulation(
    scenario_name: str = Body("Flood Escalation Scenario", embed=True),
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    res = start_simulation(scenario_name, db)
    await manager.broadcast({"type": "SIMULATION_STARTED", "scenario": scenario_name})
    return res

@router.post("/event")
async def api_inject_simulation_event(
    event_type: str = Body(..., embed=True), # INJECT_INCIDENT, BLOCK_ROAD, DISABLE_RESOURCE, SURGE_CASUALTIES
    payload: Dict[str, Any] = Body(default={}, embed=True),
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    res = inject_simulation_event(event_type, payload, db)
    await manager.broadcast({"type": "SIMULATION_EVENT", "event_type": event_type, "result": res})
    return res

@router.post("/reset")
async def api_reset_simulation(
    current_user: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    res = reset_simulation_state(db)
    await manager.broadcast({"type": "SIMULATION_RESET"})
    return res
