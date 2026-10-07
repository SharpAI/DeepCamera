#!/usr/bin/env python3
"""
Standalone prompt tester — sends a real image to a VLM and prints the result.

Usage:
  python test_prompts.py --image /path/to/frame.jpg --mode traffic_accident
  python test_prompts.py --image /tmp/cam.jpg --mode full_scan --sensitivity high --language burmese
  python test_prompts.py --image /tmp/cam.jpg --all-modes   # run every mode and compare
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "assets" / "prompts"))
from prompts import build as build_prompt, get_available_modes


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--mode", default="full_scan", choices=get_available_modes())
    p.add_argument("--all-modes", action="store_true")
    p.add_argument("--sensitivity", default="medium", choices=["low", "medium", "high"])
    p.add_argument("--language", default="english", choices=["english", "burmese", "both"])
    p.add_argument("--camera-location", default="")
    p.add_argument("--vlm-url", default="http://localhost:5405")
    p.add_argument("--vlm-model", default="qwen-vl")
    p.add_argument("--vlm-api-key", default="none")
    p.add_argument("--timeout", type=int, default=30)
    return p.parse_args()


def run_mode(args, mode: str):
    import sys, os
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from analyze import call_vlm

    system_prompt, user_message = build_prompt(
        mode, args.sensitivity, args.camera_location, args.language
    )

    print(f"\n{'='*60}")
    print(f"MODE: {mode} | sensitivity: {args.sensitivity} | language: {args.language}")
    if args.camera_location:
        print(f"LOCATION: {args.camera_location}")
    print(f"{'='*60}")
    print("SYSTEM PROMPT:")
    print(system_prompt[:800] + "…" if len(system_prompt) > 800 else system_prompt)
    print(f"\n{'─'*60}")

    try:
        result = call_vlm(
            args.image, system_prompt, user_message,
            args.vlm_url, args.vlm_model, args.vlm_api_key, args.timeout
        )
        print("VLM RESPONSE:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    args = parse_args()
    if not Path(args.image).exists():
        print(f"Image not found: {args.image}")
        sys.exit(1)

    modes = get_available_modes() if args.all_modes else [args.mode]
    for mode in modes:
        run_mode(args, mode)


if __name__ == "__main__":
    main()
