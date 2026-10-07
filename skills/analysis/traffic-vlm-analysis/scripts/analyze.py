#!/usr/bin/env python3
"""
Traffic VLM Analysis Skill — City CCTV accident and anomaly detection.

Communicates via JSON lines over stdin/stdout (Aegis frame protocol):
  stdin:  {"event": "frame", "frame_id": N, "camera_id": "...", "frame_path": "...", ...}
  stdout: {"event": "analysis", "frame_id": N, "incident_detected": bool, ...}

Reads config from:
  1. --config <path>   JSON file from Aegis
  2. CLI args          for standalone testing
  3. Env vars          AEGIS_VLM_URL, AEGIS_VLM_MODEL, AEGIS_VLM_API_KEY

Usage (standalone test):
  python analyze.py --mode full_scan --sensitivity medium --vlm-url http://localhost:5405
  echo '{"event":"frame","frame_id":1,"camera_id":"cam1","frame_path":"/tmp/frame.jpg","timestamp":"2026-07-01T10:00:00Z"}' | python analyze.py
"""

import sys
import os
import json
import argparse
import base64
import signal
import time
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Import prompt templates
# ---------------------------------------------------------------------------
_skill_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_skill_dir / "assets" / "prompts"))
from prompts import build as build_prompt, get_available_modes  # noqa: E402

# ---------------------------------------------------------------------------
# YOLO trigger classes — only frames with these objects go to VLM
# (reduces VLM token cost significantly)
# ---------------------------------------------------------------------------
YOLO_TRIGGER_CLASSES = {
    "traffic_accident":    {"car", "truck", "bus", "motorcycle", "bicycle", "person"},
    "crowd_anomaly":       {"person"},
    "suspicious_behavior": {"person", "backpack", "handbag", "suitcase"},
    "wrong_way":           {"car", "truck", "bus", "motorcycle"},
    "road_obstruction":    {"car", "truck", "bus", "motorcycle", "bicycle", "person", "dog", "cat"},
    "fire_smoke":          {"car", "truck", "bus", "motorcycle"},  # fire has no YOLO class; any vehicle can burn
    "full_scan":           {"car", "truck", "bus", "motorcycle", "bicycle", "person", "backpack"},
}


def emit(obj: dict):
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def log(msg: str):
    print(f"[traffic-vlm] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# VLM client
# ---------------------------------------------------------------------------

def call_vlm(
    frame_path: str,
    system_prompt: str,
    user_message: str,
    vlm_url: str,
    vlm_model: str,
    api_key: str,
    timeout: int = 30,
) -> dict:
    """Call VLM with a base64-encoded frame. Returns parsed JSON dict."""
    with open(frame_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    payload = {
        "model": vlm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 512,
        "temperature": 0.1,
    }

    endpoint = vlm_url.rstrip("/")
    if not endpoint.endswith("/v1"):
        endpoint += "/v1"
    url = f"{endpoint}/chat/completions"

    data = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read())

    content = body["choices"][0]["message"]["content"]
    # Strip markdown code fences if the VLM ignores json_object format
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(content)


# ---------------------------------------------------------------------------
# Frame throttle
# ---------------------------------------------------------------------------

class FrameThrottle:
    """Allows at most `fps` frames per second through to VLM."""

    def __init__(self, fps: float):
        self.interval = 1.0 / fps if fps > 0 else float("inf")
        self._last = 0.0

    def should_process(self) -> bool:
        now = time.monotonic()
        if now - self._last >= self.interval:
            self._last = now
            return True
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Traffic VLM Analysis Skill")
    p.add_argument("--config", help="JSON config file from Aegis")
    p.add_argument("--mode", default="full_scan", choices=get_available_modes())
    p.add_argument("--sensitivity", default="medium", choices=["low", "medium", "high"])
    p.add_argument("--fps", type=float, default=0.5)
    p.add_argument("--min-confidence", type=float, default=0.6)
    p.add_argument("--yolo-prefilter", action="store_true", default=True)
    p.add_argument("--no-yolo-prefilter", dest="yolo_prefilter", action="store_false")
    p.add_argument("--camera-location", default="")
    p.add_argument("--language", default="english", choices=["english", "burmese", "both"])
    p.add_argument("--vlm-url", default=os.environ.get("AEGIS_VLM_URL", "http://localhost:5405"))
    p.add_argument("--vlm-model", default=os.environ.get("AEGIS_VLM_MODEL", "qwen-vl"))
    p.add_argument("--vlm-api-key", default=os.environ.get("AEGIS_VLM_API_KEY", "none"))
    p.add_argument("--vlm-timeout", type=int, default=30)
    return p.parse_args()


def load_config(args) -> dict:
    cfg = {
        "mode":            args.mode,
        "sensitivity":     args.sensitivity,
        "fps":             args.fps,
        "min_confidence":  args.min_confidence,
        "yolo_prefilter":  args.yolo_prefilter,
        "camera_location": args.camera_location,
        "language":        args.language,
        "vlm_url":         args.vlm_url,
        "vlm_model":       args.vlm_model,
        "vlm_api_key":     args.vlm_api_key,
        "vlm_timeout":     args.vlm_timeout,
    }

    if args.config:
        try:
            with open(args.config) as f:
                file_cfg = json.load(f)
            # Aegis injects skill params under "skill_params" or flat
            params = file_cfg.get("skill_params", file_cfg)
            cfg.update({k: v for k, v in params.items() if k in cfg})
            # Platform params
            cfg["vlm_url"]     = file_cfg.get("vlm_url",     cfg["vlm_url"])
            cfg["vlm_model"]   = file_cfg.get("vlm_model",   cfg["vlm_model"])
            cfg["vlm_api_key"] = file_cfg.get("vlm_api_key", cfg["vlm_api_key"])
        except Exception as e:
            log(f"Warning: could not load config file: {e}")

    # Env var overrides (highest priority)
    if os.environ.get("AEGIS_VLM_URL"):
        cfg["vlm_url"] = os.environ["AEGIS_VLM_URL"]
    if os.environ.get("AEGIS_VLM_MODEL"):
        cfg["vlm_model"] = os.environ["AEGIS_VLM_MODEL"]
    if os.environ.get("AEGIS_VLM_API_KEY"):
        cfg["vlm_api_key"] = os.environ["AEGIS_VLM_API_KEY"]

    return cfg


def main():
    args = parse_args()
    cfg = load_config(args)

    mode        = cfg["mode"]
    sensitivity = cfg["sensitivity"]
    fps         = float(cfg["fps"])
    min_conf    = float(cfg["min_confidence"])
    prefilter   = bool(cfg["yolo_prefilter"])
    cam_loc     = cfg["camera_location"]
    language    = cfg["language"]
    vlm_url     = cfg["vlm_url"]
    vlm_model   = cfg["vlm_model"]
    vlm_api_key = cfg["vlm_api_key"]
    vlm_timeout = int(cfg["vlm_timeout"])

    trigger_classes = YOLO_TRIGGER_CLASSES.get(mode, set())
    system_prompt, user_message = build_prompt(mode, sensitivity, cam_loc, language)
    throttle = FrameThrottle(fps)

    # Stats
    frames_received = 0
    frames_analyzed = 0
    frames_skipped_throttle = 0
    frames_skipped_prefilter = 0
    incidents_detected = 0
    errors = 0

    emit({
        "event":       "ready",
        "model":       vlm_model,
        "mode":        mode,
        "sensitivity": sensitivity,
        "fps":         fps,
        "min_confidence": min_conf,
        "yolo_prefilter": prefilter,
        "language":    language,
        "camera_location": cam_loc or None,
    })

    def handle_signal(signum, _frame):
        log(f"Received signal {signum}, shutting down")
        emit({
            "event": "stats",
            "frames_received": frames_received,
            "frames_analyzed": frames_analyzed,
            "frames_skipped_throttle": frames_skipped_throttle,
            "frames_skipped_prefilter": frames_skipped_prefilter,
            "incidents_detected": incidents_detected,
            "errors": errors,
        })
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if msg.get("command") == "stop":
            break

        if msg.get("event") != "frame":
            continue

        frames_received += 1
        frame_id  = msg.get("frame_id")
        camera_id = msg.get("camera_id", "unknown")
        timestamp = msg.get("timestamp", "")
        frame_path = msg.get("frame_path", "")

        # --- Throttle check ---
        if not throttle.should_process():
            frames_skipped_throttle += 1
            continue

        # --- Frame existence check ---
        if not frame_path or not Path(frame_path).exists():
            emit({"event": "error", "frame_id": frame_id, "message": f"Frame not found: {frame_path}", "retriable": True})
            errors += 1
            continue

        # --- YOLO pre-filter check ---
        if prefilter:
            yolo_objects = set(msg.get("yolo_objects", []))  # populated if YOLO skill runs first
            if yolo_objects and trigger_classes and yolo_objects.isdisjoint(trigger_classes):
                frames_skipped_prefilter += 1
                emit({
                    "event": "analysis",
                    "frame_id": frame_id,
                    "camera_id": camera_id,
                    "timestamp": timestamp,
                    "incident_detected": False,
                    "skipped_reason": "no_trigger_objects",
                })
                continue

        # --- VLM call ---
        t0 = time.monotonic()
        try:
            result = call_vlm(
                frame_path, system_prompt, user_message,
                vlm_url, vlm_model, vlm_api_key, vlm_timeout,
            )
        except urllib.error.URLError as e:
            emit({"event": "error", "frame_id": frame_id, "message": f"VLM unreachable: {e}", "retriable": True})
            errors += 1
            continue
        except json.JSONDecodeError as e:
            emit({"event": "error", "frame_id": frame_id, "message": f"VLM returned non-JSON: {e}", "retriable": True})
            errors += 1
            continue
        except Exception as e:
            emit({"event": "error", "frame_id": frame_id, "message": str(e), "retriable": True})
            errors += 1
            continue

        frames_analyzed += 1
        vlm_ms = round((time.monotonic() - t0) * 1000, 1)

        # Validate and sanitise result
        incident_detected = bool(result.get("incident_detected", False))
        confidence = float(result.get("confidence") or 0.0)

        # Apply confidence gate
        if incident_detected and confidence < min_conf:
            incident_detected = False

        if incident_detected:
            incidents_detected += 1

        emit({
            "event":            "analysis",
            "frame_id":         frame_id,
            "camera_id":        camera_id,
            "timestamp":        timestamp,
            "incident_detected": incident_detected,
            "incident_type":    result.get("incident_type") if incident_detected else None,
            "severity":         result.get("severity") if incident_detected else None,
            "confidence":       round(confidence, 3),
            "description":      result.get("description") if incident_detected else None,
            "objects":          result.get("objects") or [],
            "suggested_action": result.get("suggested_action") if incident_detected else None,
            "skipped_reason":   None,
            "vlm_ms":           vlm_ms,
        })

    emit({
        "event": "stats",
        "frames_received":         frames_received,
        "frames_analyzed":         frames_analyzed,
        "frames_skipped_throttle": frames_skipped_throttle,
        "frames_skipped_prefilter": frames_skipped_prefilter,
        "incidents_detected":      incidents_detected,
        "errors":                  errors,
    })


if __name__ == "__main__":
    main()
