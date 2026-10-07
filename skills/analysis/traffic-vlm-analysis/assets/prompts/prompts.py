"""
Traffic VLM prompt templates.

Each prompt is a system message instructing the VLM to return a specific JSON schema.
The `build()` function assembles the final system + user messages for a given mode.
"""

# ---------------------------------------------------------------------------
# Shared JSON schema instruction (appended to every system prompt)
# ---------------------------------------------------------------------------
_SCHEMA = """
Respond ONLY with a valid JSON object. No markdown, no extra text.
Schema:
{
  "incident_detected": <bool>,
  "incident_type": <one of: "traffic_accident"|"crowd_anomaly"|"suspicious_behavior"|"wrong_way"|"road_obstruction"|"fire_smoke"|"other"|null>,
  "severity": <"low"|"medium"|"high"|"critical"|null>,
  "confidence": <float 0.0-1.0>,
  "description": <string, 1-3 sentences, factual>,
  "objects": <list of detected relevant objects, e.g. ["car","truck","person"]>,
  "suggested_action": <string or null>
}
If no incident is detected, set incident_detected=false and all other fields to null.
"""

# ---------------------------------------------------------------------------
# Sensitivity preambles
# ---------------------------------------------------------------------------
_SENSITIVITY = {
    "low": (
        "Report ONLY clear, confirmed incidents that are already happening. "
        "Do not flag near-misses, ambiguous situations, or normal traffic congestion."
    ),
    "medium": (
        "Report confirmed incidents AND developing situations (near-misses, vehicles slowing abnormally, "
        "crowds beginning to gather). Use your judgment on ambiguous cases."
    ),
    "high": (
        "Report any unusual pattern, near-miss, potential precursor to an incident, "
        "or behavior that deviates from normal traffic flow. Err on the side of flagging."
    ),
}

# ---------------------------------------------------------------------------
# Mode-specific system prompts
# ---------------------------------------------------------------------------
_MODE_PROMPTS = {
    "traffic_accident": """You are a traffic accident detection AI monitoring a city CCTV camera.
Analyze the frame for:
- Vehicle collisions (rear-end, side-impact, head-on)
- Overturned or heavily damaged vehicles
- Vehicles stopped in unusual positions after impact
- Post-crash debris on the road
- Pedestrians injured or struck by vehicles
- Motorcycles or bicycles involved in crashes
Ignore: normal traffic stops, parked cars, minor fender-benders with no safety impact.""",

    "crowd_anomaly": """You are a crowd safety AI monitoring a city CCTV camera.
Analyze the frame for:
- Stampedes or crowds moving in panic
- Abnormally dense crowd concentration (crush risk)
- Sudden crowd dispersal (possible fight or threat nearby)
- People falling or being trampled
- Blocked emergency access routes
- Crowd gathering around an incident
Ignore: normal pedestrian traffic, bus stops, markets with expected density.""",

    "suspicious_behavior": """You are a public safety AI monitoring a city CCTV camera.
Analyze the frame for:
- Individuals loitering in restricted or unusual areas for extended periods
- Abandoned bags, packages, or objects left unattended
- Erratic or aggressive movement between individuals
- Individuals surveilling or photographing infrastructure suspiciously
- Groups confronting or surrounding another person
- Individuals climbing fences, walls, or restricted structures
Ignore: people waiting normally, street vendors, delivery personnel.""",

    "wrong_way": """You are a wrong-way vehicle detection AI monitoring a city CCTV camera.
Analyze the frame for:
- Vehicles driving against the flow of traffic
- Vehicles entering one-way streets in the wrong direction
- Vehicles reversing on highways or main roads
- Vehicles driving on sidewalks or pedestrian areas
Use lane markings, traffic signals, and the direction of other vehicles as reference.
Ignore: emergency vehicles, reversing in parking areas.""",

    "road_obstruction": """You are a road obstruction detection AI monitoring a city CCTV camera.
Analyze the frame for:
- Vehicles stopped and blocking one or more lanes
- Fallen cargo, debris, or objects on the road
- Construction equipment or materials blocking traffic
- Broken-down vehicles in live traffic lanes
- Flooding or road damage blocking passage
- Pedestrians or animals on the road in dangerous positions
Ignore: normal traffic queues, vehicles stopped at red lights.""",

    "fire_smoke": """You are a fire and smoke detection AI monitoring a city CCTV camera.
Analyze the frame for:
- Visible flames from vehicles, buildings, or roadside objects
- Smoke plumes (black, grey, or white) from any source
- Burning debris on the road
- Smoke rising from underground (manhole fires)
- Vehicles on fire or smoldering
Report even small fires or initial smoke as they can escalate rapidly.""",

    "full_scan": """You are a comprehensive city traffic and public safety AI monitoring a CCTV camera.
In a single pass, analyze the frame for ANY of the following:
1. TRAFFIC ACCIDENTS — collisions, overturned vehicles, injured pedestrians
2. CROWD ANOMALIES — stampedes, dangerous density, panic dispersal
3. SUSPICIOUS BEHAVIOR — loitering, abandoned objects, confrontations
4. WRONG-WAY VEHICLES — driving against traffic or on restricted areas
5. ROAD OBSTRUCTIONS — blocked lanes, debris, breakdowns
6. FIRE & SMOKE — flames or smoke from any source
Report the MOST SEVERE incident if multiple are present.
Classify the incident_type accurately based on the primary threat.""",
}


def build(
    mode: str,
    sensitivity: str,
    camera_location: str = "",
    language: str = "english",
) -> tuple[str, str]:
    """
    Build (system_prompt, user_message) for a given analysis mode.

    Returns:
        system_prompt: Full system instruction with schema
        user_message:  Frame-specific user turn
    """
    base = _MODE_PROMPTS.get(mode, _MODE_PROMPTS["full_scan"])
    sens = _SENSITIVITY.get(sensitivity, _SENSITIVITY["medium"])

    location_ctx = f"\nCamera location: {camera_location}" if camera_location else ""

    lang_instruction = ""
    if language == "burmese":
        lang_instruction = "\nWrite the 'description' and 'suggested_action' fields in Burmese (Myanmar language)."
    elif language == "both":
        lang_instruction = "\nWrite the 'description' field as: English description first, then '|' separator, then Burmese translation."

    system_prompt = f"{base}\n\nSensitivity level: {sens}{location_ctx}{lang_instruction}\n\n{_SCHEMA}"

    user_message = "Analyze this camera frame and return the JSON response."

    return system_prompt, user_message


def get_available_modes() -> list[str]:
    return list(_MODE_PROMPTS.keys())
