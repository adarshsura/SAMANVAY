import re
from typing import Dict, Any, List, Optional

DISASTER_QUESTIONS = {
    "Flood": [
        {
            "id": "q_flood_trapped",
            "question": "Are you trapped?",
            "options": ["Yes, unable to leave", "Partially, moving slowly", "No, on safe ground"]
        },
        {
            "id": "q_flood_people",
            "question": "How many people are with you?",
            "options": ["Just myself (1)", "2 to 5 people", "6 to 15 people", "More than 15"]
        },
        {
            "id": "q_flood_water_level",
            "question": "What is the water level around you?",
            "options": ["Ankle / Knee deep", "Waist deep", "Chest deep or higher", "Submerged ground floor"]
        },
        {
            "id": "q_flood_safe_upper",
            "question": "Can you move to a safe higher floor or roof?",
            "options": ["Yes, on roof/upper floor", "No higher floor available", "Water is rising towards us"]
        }
    ],
    "Building Collapse": [
        {
            "id": "q_col_location",
            "question": "Are you inside or outside the structure?",
            "options": ["Trapped under debris", "Inside damaged building", "Outside / On the street"]
        },
        {
            "id": "q_col_floors",
            "question": "Approximate number of floors of the structure?",
            "options": ["1 to 2 floors", "3 to 5 floors", "6 floors or higher"]
        },
        {
            "id": "q_col_trapped_count",
            "question": "How many people may be trapped?",
            "options": ["1 to 3", "4 to 10", "10 to 30", "Dozens / Unknown"]
        },
        {
            "id": "q_col_hazards",
            "question": "Any visible fire, smoke, or gas leak smell?",
            "options": ["Heavy smoke / Fire", "Strong gas smell", "None visible"]
        },
        {
            "id": "q_col_sounds",
            "question": "Can you hear people calling or tapping inside?",
            "options": ["Yes, clear voices/tapping", "Faint sounds", "No sounds heard"]
        }
    ],
    "Fire": [
        {
            "id": "q_fire_trapped",
            "question": "Are people trapped inside?",
            "options": ["Yes, confirmed trapped", "Likely inside", "Everyone evacuated"]
        },
        {
            "id": "q_fire_building",
            "question": "What type of building is on fire?",
            "options": ["Residential apartment", "Commercial / Market", "Factory / Industrial warehouse"]
        },
        {
            "id": "q_fire_severity",
            "question": "Fire and smoke severity?",
            "options": ["Flames through roof / windows", "Heavy suffocating black smoke", "Contained room fire"]
        },
        {
            "id": "q_fire_hazmat",
            "question": "Are there hazardous materials, gas cylinders, or chemicals?",
            "options": ["LPG cylinders / Chemicals present", "Standard building contents", "Unsure"]
        }
    ],
    "Earthquake": [
        {
            "id": "q_eq_damage",
            "question": "What is the extent of building damage?",
            "options": ["Total structural collapse", "Major cracks / partial fall", "Minor non-structural cracks"]
        },
        {
            "id": "q_eq_trapped",
            "question": "Are there people trapped or injured?",
            "options": ["Multiple severe injuries & trapped", "Minor injuries only", "No known trapped victims"]
        },
        {
            "id": "q_eq_gas_fire",
            "question": "Any fires or gas pipe ruptures?",
            "options": ["Yes, active fire or ruptured gas line", "Power lines down", "No immediate secondary hazard"]
        },
        {
            "id": "q_eq_roads",
            "question": "Is the road accessible for heavy emergency vehicles?",
            "options": ["Road blocked by rubble / cracks", "Partially passable for bikes/foot", "Road is clear"]
        }
    ]
}

def get_adaptive_questions(disaster_type: str) -> List[Dict[str, Any]]:
    return DISASTER_QUESTIONS.get(disaster_type, DISASTER_QUESTIONS["Flood"])

def analyze_incident_data(
    disaster_type: Optional[str],
    answers: Optional[Dict[str, Any]],
    text_notes: Optional[str],
    voice_transcript: Optional[str],
    location_intel: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synthesizes citizen answers, free-text/speech transcripts, and location intelligence.
    Returns deterministic, explainable estimates (never hallucinating exact precision).
    """
    combined_text = f"{text_notes or ''} {voice_transcript or ''}".lower()
    
    # 1. Disaster classification refinement
    detected_type = disaster_type or "Unknown"
    if detected_type == "Unknown" or not detected_type:
        if any(w in combined_text for w in ["water", "flood", "drown", "submerged", "river", "boat"]):
            detected_type = "Flood"
        elif any(w in combined_text for w in ["fire", "smoke", "flame", "burn", "cylinder", "blast"]):
            detected_type = "Fire"
        elif any(w in combined_text for w in ["collapse", "rubble", "building fell", "crushed", "debris"]):
            detected_type = "Building Collapse"
        elif any(w in combined_text for w in ["quake", "shake", "earthquake", "tremor"]):
            detected_type = "Earthquake"
        else:
            detected_type = "Unknown"

    # 2. Extract people, injured, trapped from text/answers
    est_people_min = 1
    est_people_max = 5
    est_injured = 0
    est_trapped = 0

    if answers:
        # Check people
        p_ans = str(answers.get("q_flood_people", "") or answers.get("q_col_trapped_count", ""))
        if "More than 15" in p_ans or "Dozens" in p_ans:
            est_people_min, est_people_max = 20, 50
        elif "6 to 15" in p_ans or "10 to 30" in p_ans:
            est_people_min, est_people_max = 10, 25
        elif "2 to 5" in p_ans or "4 to 10" in p_ans:
            est_people_min, est_people_max = 4, 8

        # Check trapped
        t_ans = str(answers.get("q_flood_trapped", "") or answers.get("q_col_location", "") or answers.get("q_fire_trapped", ""))
        if "Yes" in t_ans or "Trapped under" in t_ans or "confirmed" in t_ans:
            est_trapped = max(1, est_people_min)

    # Keyword number extraction from free text
    numbers_in_text = re.findall(r'(\d+)\s*(?:people|persons|injured|trapped|casualties)?', combined_text)
    if numbers_in_text:
        parsed_nums = [int(n) for n in numbers_in_text if int(n) < 5000]
        if parsed_nums:
            max_num = max(parsed_nums)
            est_people_min = max(est_people_min, int(max_num * 0.8))
            est_people_max = max(est_people_max, int(max_num * 1.2))
            if "injured" in combined_text or "hurt" in combined_text:
                est_injured = max(est_injured, int(max_num * 0.4))
            if "trapped" in combined_text or "stuck" in combined_text:
                est_trapped = max(est_trapped, int(max_num * 0.6))

    # 3. Urgency and Hazard calculation
    if detected_type in ["Building Collapse", "Fire"] and (est_trapped > 0 or "heavy smoke" in combined_text):
        hazard_level = "CRITICAL"
        urgency = "CRITICAL"
    elif detected_type == "Flood" and (est_trapped > 10 or location_intel.get("road_accessibility_pct", 100) < 50):
        hazard_level = "CRITICAL"
        urgency = "CRITICAL"
    elif est_injured > 5 or est_trapped > 0:
        hazard_level = "HIGH"
        urgency = "HIGH"
    elif est_people_max > 10:
        hazard_level = "MODERATE"
        urgency = "MODERATE"
    else:
        hazard_level = "MODERATE"
        urgency = "MODERATE"

    # 4. Confidence assessment
    confidence = 65
    if answers and len(answers) >= 2:
        confidence += 15
    if text_notes or voice_transcript:
        confidence += 10
    if location_intel.get("population_exposure") == "HIGH":
        confidence += 5
    confidence = min(95, max(45, confidence))

    # 5. Human-readable explanation (strictly adhering to "estimated vs confirmed")
    explanation_parts = [
        f"Disaster classified as {detected_type} (Confidence: {confidence}%).",
        f"Estimated population affected: {est_people_min}–{est_people_max}.",
        f"Reported/Estimated trapped: {est_trapped}, injured: {est_injured}.",
        f"Road accessibility in sector: {location_intel.get('road_accessibility_pct', 80)}%."
    ]
    if location_intel.get("nearest_hospital"):
        hosp = location_intel["nearest_hospital"]
        explanation_parts.append(f"Nearest trauma apex: {hosp['name']} ({hosp['distance_km']} km).")

    return {
        "disaster_type": detected_type,
        "estimated_people_range": f"{est_people_min}–{est_people_max}",
        "estimated_people_mid": int((est_people_min + est_people_max) / 2),
        "estimated_injured": est_injured,
        "estimated_trapped": est_trapped,
        "hazard_level": hazard_level,
        "urgency": urgency,
        "confidence": confidence,
        "explanation": " ".join(explanation_parts)
    }
