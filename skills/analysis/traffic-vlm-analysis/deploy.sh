#!/bin/bash
# Deploy script for traffic-vlm-analysis skill.
# No special dependencies — VLM is called over HTTP.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[traffic-vlm-analysis] Deploy check..."
python3 -c "import sys, json, base64, urllib.request, pathlib; print('  stdlib OK')"
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/assets/prompts')
from prompts import get_available_modes
print(f'  prompts OK — {len(get_available_modes())} modes: {get_available_modes()}')
"
echo "[traffic-vlm-analysis] Ready."
