import pytest
from app.database.session import SessionLocal
from app.database.models import Incident, Resource
from app.services.optimizer import solve_resource_allocation, compute_baseline_greedy_comparison

def test_ortools_milp_solver_constraints():
    """Verify OR-Tools MILP assigns resources without double-booking and respects capability matching."""
    db = SessionLocal()
    try:
        incidents = db.query(Incident).filter(Incident.status != "CANCELLED").all()
        resources = db.query(Resource).filter(Resource.status == "AVAILABLE").all()

        result = solve_resource_allocation(incidents, resources, db)
        assert result["status"] in ["OPTIMAL", "FEASIBLE"]
        assignments = result["assignments"]
        assert len(assignments) > 0

        # Verify no resource is assigned more than once
        assigned_res_ids = [a["resource_id"] for a in assignments]
        assert len(assigned_res_ids) == len(set(assigned_res_ids)), "A resource was assigned more than once!"

        # Verify reason/explainability string exists for each assignment
        for a in assignments:
            assert "Incident criticality" in a["reason"]
            assert "ETA:" in a["reason"]
            assert "Capability: MATCH" in a["reason"]
            assert a["estimated_eta_minutes"] > 0
    finally:
        db.close()

def test_baseline_comparison_generation():
    """Verify baseline comparison returns valid empirical comparison metrics."""
    db = SessionLocal()
    try:
        incidents = db.query(Incident).filter(Incident.status != "CANCELLED").all()
        resources = db.query(Resource).all()
        comp = compute_baseline_greedy_comparison(incidents, resources, db)

        assert "baseline_greedy" in comp
        assert "samanvay_milp" in comp
        assert "raahat_milp" in comp
        assert "improvement_summary" in comp
        assert comp["samanvay_milp"]["critical_incidents_covered_percentage"] >= comp["baseline_greedy"]["critical_incidents_covered_percentage"]
    finally:
        db.close()
