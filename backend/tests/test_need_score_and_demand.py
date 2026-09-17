import pytest
from app.services.need_score import calculate_need_score
from app.services.demand_predictor import predict_resource_demand

def test_need_score_calculation_explainability():
    """Verify Need Score produces bounded 0-100 values with explainable component breakdown."""
    result = calculate_need_score(
        reported_injured=15,
        reported_trapped=20,
        reported_people=120,
        road_accessibility_pct=40,
        zone_vulnerability_index=0.85
    )
    score = result["need_score"]
    assert 0.0 <= score <= 100.0
    assert result["need_priority"] in ["CRITICAL", "HIGH"]
    breakdown = result["breakdown"]
    assert "medical_severity" in breakdown
    assert "people_affected" in breakdown
    assert "accessibility" in breakdown
    assert "vulnerability" in breakdown
    assert "unmet_demand" in breakdown

def test_custom_weights_affect_score():
    """Verify admin-configured weights genuinely alter the final Need Score."""
    # Extreme weight on medical
    res_medical_heavy = calculate_need_score(
        reported_injured=50,
        reported_trapped=10,
        reported_people=5,
        road_accessibility_pct=100,
        zone_vulnerability_index=0.1,
        custom_weights={
            "medical_severity": 0.80,
            "people_affected": 0.05,
            "unmet_demand": 0.05,
            "accessibility": 0.05,
            "vulnerability": 0.05
        }
    )
    # Extreme weight on people affected
    res_people_heavy = calculate_need_score(
        reported_injured=50,
        reported_trapped=10,
        reported_people=5,
        road_accessibility_pct=100,
        zone_vulnerability_index=0.1,
        custom_weights={
            "medical_severity": 0.05,
            "people_affected": 0.80,
            "unmet_demand": 0.05,
            "accessibility": 0.05,
            "vulnerability": 0.05
        }
    )
    assert res_medical_heavy["need_score"] > res_people_heavy["need_score"]

def test_demand_prediction_flood():
    """Verify flood scenario demands specialized rescue boats, ambulances, and relief trucks."""
    demand = predict_resource_demand(
        disaster_type="Flood",
        reported_people=300,
        reported_injured=25,
        reported_trapped=40,
        road_accessibility_pct=35
    )
    assert "Rescue Boat" in demand
    assert demand["Rescue Boat"]["min"] >= 1
    assert "Ambulance" in demand
    assert demand["Ambulance"]["min"] >= 4
    assert "Relief Supply Unit" in demand

def test_demand_prediction_fire():
    """Verify fire scenario demands fire units, ambulances, and medical teams."""
    demand = predict_resource_demand(
        disaster_type="Fire",
        reported_people=80,
        reported_injured=12,
        reported_trapped=5,
        road_accessibility_pct=85
    )
    assert "Fire Unit" in demand
    assert demand["Fire Unit"]["min"] >= 2
    assert "Ambulance" in demand
