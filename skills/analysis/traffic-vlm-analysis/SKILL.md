---
name: traffic-vlm-analysis
description: "Traffic & public safety VLM analysis — accident, anomaly, and crowd detection using vision-language models"
version: 1.0.0
category: analysis
runtime: python
entry: scripts/analyze.py
install: pip

requirements:
  python: ">=3.9"
  platforms: ["linux", "macos", "windows"]

parameters:
  - name: analysis_mode
    label: "Analysis Mode"
    type: select
    options:
      - "traffic_accident"
      - "crowd_anomaly"
      - "suspicious_behavior"
      - "wrong_way"
      - "road_obstruction"
      - "fire_smoke"
      - "full_scan"
    default: "full_scan"
    description: "Focus the VLM on a specific threat type, or run all checks at once"
    group: Analysis

  - name: sensitivity
    label: "Sensitivity"
    type: select
    options: ["low", "medium", "high"]
    default: "medium"
    description: "low = only obvious incidents | high = flag edge cases and near-misses"
    group: Analysis

  - name: fps
    label: "Processing FPS"
    type: select
    options: [0.1, 0.2, 0.5, 1, 2]
    default: 0.5
    description: "Frames per second sent to VLM — VLM is slower than YOLO, keep low"
    group: Performance

  - name: min_confidence
    label: "Min Confidence to Report"
    type: number
    min: 0.1
    max: 1.0
    default: 0.6
    description: "Suppress incidents below this confidence score"
    group: Analysis

  - name: yolo_prefilter
    label: "YOLO Pre-filter"
    type: boolean
    default: true
    description: "Only send frames to VLM when YOLO detects relevant objects (saves VLM tokens)"
    group: Performance

  - name: camera_location
    label: "Camera Location Description"
    type: string
    default: ""
    description: "e.g. 'Intersection of Main St and 5th Ave, downtown' — injected into VLM prompt for context"
    group: Analysis

  - name: language
    label: "Report Language"
    type: select
    options: ["english", "burmese", "both"]
    default: "english"
    description: "Language for incident descriptions in VLM output"
    group: Analysis

capabilities:
  live_detection:
    script: scripts/analyze.py
    description: "Real-time VLM scene analysis for traffic and public safety"
---

# Traffic VLM Analysis

Real-time traffic and public safety scene analysis using Vision-Language Models (VLMs). Runs on top of the Aegis camera frame pipeline and outputs structured incident events.

## What It Detects

| Mode | Examples |
|------|---------|
| `traffic_accident` | Collisions, overturned vehicles, post-crash debris |
| `crowd_anomaly` | Stampedes, unusually dense crowds, dispersal events |
| `suspicious_behavior` | Loitering, package abandonment, erratic movement |
| `wrong_way` | Vehicles driving against traffic |
| `road_obstruction` | Stopped vehicles blocking lanes, fallen objects |
| `fire_smoke` | Visible flames, smoke plumes from vehicles or structures |
| `full_scan` | All of the above in one pass |

## Sensitivity Levels

| Level | Behavior |
|-------|---------|
| `low` | Only clear, confirmed incidents (fewer false positives) |
| `medium` | Balanced — flags near-misses and developing situations |
| `high` | Flags edge cases, unusual patterns, and potential precursors |

## VLM Compatibility

Works with any OpenAI-compatible vision endpoint:
- **Local:** Qwen-VL, LLaVA, DeepSeek-VL, SmolVLM (via llama-server or Ollama)
- **Cloud:** GPT-4o Vision, Claude Sonnet (vision), Gemini Pro Vision

## Protocol

### Aegis → Skill (stdin)
```jsonl
{"event": "frame", "frame_id": 42, "camera_id": "cam_001", "frame_path": "/tmp/frame.jpg", "timestamp": "2026-07-01T10:30:00Z", "width": 1920, "height": 1080}
```

### Skill → Aegis (stdout)
```jsonl
{"event": "ready", "model": "qwen-vl", "mode": "full_scan", "sensitivity": "medium", "fps": 0.5}

{"event": "analysis", "frame_id": 42, "camera_id": "cam_001", "timestamp": "...",
 "incident_detected": true,
 "incident_type": "traffic_accident",
 "severity": "high",
 "confidence": 0.91,
 "description": "Two-vehicle collision detected at intersection. One vehicle has crossed the center line. Airbags may have deployed.",
 "objects": ["car", "truck"],
 "suggested_action": "Dispatch emergency services",
 "skipped_reason": null}

{"event": "analysis", "frame_id": 43, "camera_id": "cam_001", "timestamp": "...",
 "incident_detected": false, "skipped_reason": "no_trigger_objects"}

{"event": "error", "message": "VLM endpoint unreachable", "retriable": true}
```

### Stop Command
```jsonl
{"command": "stop"}
```
