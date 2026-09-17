import pytest
from app.database.session import SessionLocal
from app.services.reallocation import compute_dynamic_reallocation

def test_dynamic_reallocation_diff():
    """Verify dynamic reallocation computes delta without silent overrides."""
    db = SessionLocal()
    try:
        diff = compute_dynamic_reallocation("Road to Zone B blocked and +40 critical casualties in Zone C", db)
        assert "reallocation_id" in diff
        assert "changes" in diff
        assert "old_plan_summary" in diff
        assert "new_plan_summary" in diff
        assert diff["requires_approval"] is True
    finally:
        db.close()
