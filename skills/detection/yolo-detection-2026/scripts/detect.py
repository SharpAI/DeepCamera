#!/usr/bin/env python3
"""
YOLO 2026 Detection Skill — Real-time object detection for SharpAI Aegis.

Communicates via JSON lines over stdin/stdout:
  stdin:  {"event": "frame", "frame_id": N, "camera_id": "...", "frame_path": "...", ...}
  stdout: {"event": "detections", "frame_id": N, "camera_id": "...", "objects": [...]}

Uses env_config.py for automatic hardware detection and model optimization
(TensorRT, ONNX, CoreML, OpenVINO) with PyTorch fallback.

Usage:
  python detect.py --config config.json
  python detect.py --model-size nano --confidence 0.5 --device auto
"""

import sys
import os
import json
import argparse
import signal
import time
from pathlib import Path

# Prevent ultralytics from auto-installing packages (e.g. onnxruntime-gpu on ROCm)
os.environ.setdefault("YOLO_AUTOINSTALL", "0")

# Import env_config — try multiple locations:
# 1. Same directory as detect.py (bundled copy)
# 2. DeepCamera repo: skills/lib/
# 3. Inline fallback (basic PyTorch-only mode)
_script_dir = Path(__file__).resolve().parent
_lib_candidates = [
    _script_dir,                                          # bundled alongside detect.py
    _script_dir.parent.parent.parent.parent / "lib",      # repo: skills/lib/
    _script_dir.parent / "lib",                           # skill-level lib/
]
_env_config_loaded = False
for _lib_path in _lib_candidates:
    if (_lib_path / "env_config.py").exists():
        sys.path.insert(0, str(_lib_path))
        from env_config import HardwareEnv  # noqa: E402
        _env_config_loaded = True
        break

if not _env_config_loaded:
    # Minimal fallback — PyTorch only, no optimization
    import types
    _msg = "[YOLO-2026] WARNING: env_config.py not found, using PyTorch-only fallback"
    print(_msg, file=sys.stderr, flush=True)

    class HardwareEnv:
        def __init__(self):
            self.backend = "cpu"
            self.device = "cpu"
            self.export_format = "none"
            self.gpu_name = ""
            self.gpu_memory_mb = 0
            self.driver_version = ""
            self.framework_ok = False
            self.export_ms = 0.0
            self.load_ms = 0.0

        @staticmethod
        def detect():
            import torch
            env = HardwareEnv()
            if torch.cuda.is_available():
                env.backend = "cuda"; env.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                env.backend = "mps"; env.device = "mps"
            return env

        def load_optimized(self, model_name, use_optimized=True):
            import time
            from ultralytics import YOLO
            t0 = time.perf_counter()
            model = YOLO(f"{model_name}.pt")
            model.to(self.device)
            self.load_ms = (time.perf_counter() - t0) * 1000
            return model, "pytorch"

        def to_dict(self):
            return {"backend": self.backend, "device": self.device}


# Optional temporal tracker — smooths YOLO's per-frame flicker into stable,
# persistent tracks (coasting through missed detections, confirmation to drop
# single-frame false positives). Bundled alongside detect.py; if it's missing we
# fall back to raw per-frame detections so the skill still runs.
try:
    from tracker import MultiObjectTracker
    _TRACKER_AVAILABLE = True
except Exception as _tracker_err:  # pragma: no cover - import guard
    _TRACKER_AVAILABLE = False
    print(f"[YOLO-2026] WARNING: tracker unavailable ({_tracker_err}); raw detections",
          file=sys.stderr, flush=True)


# Model size → ultralytics model name mapping (YOLO26, released Jan 2026)
MODEL_SIZE_MAP = {
    "nano": "yolo26n",
    "small": "yolo26s",
    "medium": "yolo26m",
    "large": "yolo26l",
}

# How often to emit aggregate perf stats (every N frames)
PERF_STATS_INTERVAL = 50


# ───────────────────────────────────────────────────────────────────────────────
# Performance tracker — collects per-frame timings, emits aggregate stats
# ───────────────────────────────────────────────────────────────────────────────

class PerfTracker:
    """Tracks timing for each pipeline stage and emits periodic statistics."""

    def __init__(self, interval: int = PERF_STATS_INTERVAL):
        self.interval = interval
        self.frame_count = 0
        self.total_frames = 0
        self.error_count = 0

        # One-time timings (ms)
        self.model_load_ms = 0.0
        self.export_ms = 0.0

        # Per-frame accumulators (ms)
        self._timings: dict[str, list[float]] = {
            "file_read":    [],
            "inference":    [],
            "postprocess":  [],
            "emit":         [],
            "total":        [],
        }

    def record(self, stage: str, duration_ms: float):
        if stage in self._timings:
            self._timings[stage].append(duration_ms)

    def record_frame(self):
        self.frame_count += 1
        self.total_frames += 1
        if self.frame_count >= self.interval:
            self.emit_stats()
            self.frame_count = 0

    def emit_stats(self):
        stats = {
            "event": "perf_stats",
            "total_frames": self.total_frames,
            "window_size": len(self._timings["total"]) or 1,
            "errors": self.error_count,
            "model_load_ms": round(self.model_load_ms, 1),
            "timings_ms": {},
        }
        if self.export_ms > 0:
            stats["export_ms"] = round(self.export_ms, 1)

        for stage, values in self._timings.items():
            if not values:
                continue
            sorted_v = sorted(values)
            n = len(sorted_v)
            stats["timings_ms"][stage] = {
                "avg": round(sum(sorted_v) / n, 2),
                "min": round(sorted_v[0], 2),
                "max": round(sorted_v[-1], 2),
                "p50": round(sorted_v[n // 2], 2),
                "p95": round(sorted_v[int(n * 0.95)], 2),
                "p99": round(sorted_v[int(n * 0.99)], 2),
            }
        emit(stats)
        for key in self._timings:
            self._timings[key].clear()

    def emit_final(self):
        if self._timings["total"]:
            self.emit_stats()


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="YOLO 2026 Detection Skill")
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    parser.add_argument("--model-size", type=str, default="nano",
                        choices=["nano", "small", "medium", "large"])
    parser.add_argument("--confidence", type=float, default=0.8)
    parser.add_argument("--classes", type=str, default="person,car,dog,cat")
    parser.add_argument("--device", type=str, default="auto",
                        choices=["auto", "cpu", "cuda", "mps", "rocm"])
    parser.add_argument("--fps", type=float, default=5)
    return parser.parse_args()


def load_config(args):
    """Load config from JSON file, CLI args, or AEGIS_SKILL_PARAMS env var."""
    import os

    env_params = os.environ.get("AEGIS_SKILL_PARAMS")
    if env_params:
        try:
            return json.loads(env_params)
        except json.JSONDecodeError:
            pass

    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

    return {
        "model_size": args.model_size,
        "confidence": args.confidence,
        "classes": args.classes.split(","),
        "device": args.device,
        "fps": args.fps,
    }


def emit(event: dict):
    print(json.dumps(event), flush=True)


def log(msg: str):
    print(f"[YOLO-2026] {msg}", file=sys.stderr, flush=True)


# ───────────────────────────────────────────────────────────────────────────────
# Main loop
# ───────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    config = load_config(args)

    model_size = config.get("model_size", "nano")
    confidence = config.get("confidence", 0.8)
    fps = config.get("fps", 5)
    use_optimized = config.get("use_optimized", config.get("use_coreml", True))
    if isinstance(use_optimized, str):
        use_optimized = use_optimized.lower() in ("true", "1", "yes")

    model_name = MODEL_SIZE_MAP.get(model_size, "yolo26n")

    target_classes = config.get("classes", ["person", "car", "dog", "cat"])
    if isinstance(target_classes, str):
        target_classes = [c.strip() for c in target_classes.split(",")]

    # ── Temporal tracking config ──
    tracking_enabled = config.get("tracking", True)
    if isinstance(tracking_enabled, str):
        tracking_enabled = tracking_enabled.lower() in ("true", "1", "yes")
    tracking_enabled = bool(tracking_enabled) and _TRACKER_AVAILABLE
    try:
        track_max_age = int(config.get("track_max_age", 15))
    except (TypeError, ValueError):
        track_max_age = 15
    try:
        track_min_hits = int(config.get("track_min_hits", 3))
    except (TypeError, ValueError):
        track_min_hits = 3
    trackers = {}  # camera_id → MultiObjectTracker (one per camera)

    # ── Hardware detection & optimized model loading ──
    emit({"event": "progress", "stage": "init", "message": "Detecting compute hardware..."})
    env = HardwareEnv.detect()
    perf = PerfTracker(interval=PERF_STATS_INTERVAL)

    gpu_msg = f"{env.gpu_name} ({env.backend})" if env.gpu_name else env.backend
    emit({"event": "progress", "stage": "init", "message": f"Hardware: {gpu_msg}"})

    try:
        emit({"event": "progress", "stage": "model", "message": f"Loading {model_name} model ({env.export_format} format)..."})
        model, model_format = env.load_optimized(model_name, use_optimized=use_optimized)
        perf.model_load_ms = env.load_ms
        perf.export_ms = env.export_ms

        if env.export_ms > 0:
            emit({"event": "progress", "stage": "model", "message": f"Model optimized in {env.export_ms:.0f}ms"})

        ready_event = {
            "event": "ready",
            "model": f"yolo2026{model_size[0]}",
            "model_size": model_size,
            "device": env.device,
            "backend": env.backend,
            "format": model_format,
            "gpu": env.gpu_name,
            "classes": len(model.names),
            "fps": fps,
            "model_load_ms": round(env.load_ms, 1),
            "available_sizes": list(MODEL_SIZE_MAP.keys()),
        }
        if hasattr(env, 'compute_units') and env.backend == "mps":
            ready_event["compute_units"] = env.compute_units
        emit(ready_event)
    except Exception as e:
        emit({"event": "error", "message": f"Failed to load model: {e}", "retriable": False})
        sys.exit(1)

    # Graceful shutdown — exit immediately with code 0.
    # The stdin read loop blocks, so setting a flag doesn't work;
    # we must exit in the signal handler to avoid being killed (code null).
    def handle_signal(signum, frame):
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        log(f"Received {sig_name}, shutting down gracefully")
        perf.emit_final()
        sys.exit(0)
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Main loop: read frames from stdin, output detections to stdout
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

        if msg.get("event") == "frame":
            t_frame_start = time.perf_counter()

            frame_path = msg.get("frame_path")
            frame_id = msg.get("frame_id")
            camera_id = msg.get("camera_id", "unknown")
            timestamp = msg.get("timestamp", "")

            t0 = time.perf_counter()
            if not frame_path or not Path(frame_path).exists():
                emit({
                    "event": "error",
                    "frame_id": frame_id,
                    "message": f"Frame not found: {frame_path}",
                    "retriable": True,
                })
                perf.error_count += 1
                continue
            perf.record("file_read", (time.perf_counter() - t0) * 1000)

            try:
                t0 = time.perf_counter()
                results = model(frame_path, conf=confidence, verbose=False)
                perf.record("inference", (time.perf_counter() - t0) * 1000)

                t0 = time.perf_counter()
                objects = []
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        cls_name = model.names[cls_id]
                        if cls_name in target_classes or not target_classes:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            objects.append({
                                "class": cls_name,
                                "confidence": round(float(box.conf[0]), 3),
                                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            })
                perf.record("postprocess", (time.perf_counter() - t0) * 1000)

                # ── Temporal tracking: turn the raw per-frame boxes into smooth,
                # persistent tracks (kills flicker). One tracker per camera. The
                # original image + dims come from the YOLO result we already have,
                # so there's no extra decode. Falls back to raw boxes on any error.
                if tracking_enabled and results:
                    try:
                        r0 = results[0]
                        oh, ow = (r0.orig_shape if getattr(r0, "orig_shape", None)
                                  else (0, 0))
                        if ow and oh:
                            tk = trackers.get(camera_id)
                            if tk is None:
                                tk = MultiObjectTracker(max_age=track_max_age,
                                                        n_init=track_min_hits)
                                trackers[camera_id] = tk
                            objects = tk.update(objects, int(ow), int(oh),
                                                getattr(r0, "orig_img", None))
                    except Exception as track_err:
                        log(f"tracker error (using raw detections): {track_err}")

                t0 = time.perf_counter()
                emit({
                    "event": "detections",
                    "frame_id": frame_id,
                    "camera_id": camera_id,
                    "timestamp": timestamp,
                    "objects": objects,
                })
                perf.record("emit", (time.perf_counter() - t0) * 1000)

            except Exception as e:
                emit({
                    "event": "error",
                    "frame_id": frame_id,
                    "message": f"Inference error: {e}",
                    "retriable": True,
                })
                perf.error_count += 1
                continue

            perf.record("total", (time.perf_counter() - t_frame_start) * 1000)
            perf.record_frame()

    perf.emit_final()


if __name__ == "__main__":
    main()
