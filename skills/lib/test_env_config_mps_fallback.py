#!/usr/bin/env python3
"""
Regression test for SharpAI/DeepCamera#207: load_optimized() crashed with
"No module named 'ultralytics'" on mps machines where framework_ok is False
(the CoreML execution-provider check failed), because the final fallback
branch unconditionally did `from ultralytics import YOLO` — but mps installs
deliberately never ship torch/ultralytics (see requirements_mps.txt).

Run:  python -m pytest skills/lib/test_env_config_mps_fallback.py -v
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_config import HardwareEnv  # noqa: E402


def _mps_env(framework_ok=False):
    return HardwareEnv(
        backend="mps",
        device="mps",
        export_format="onnx",
        framework_ok=framework_ok,
    )


class TestMpsFrameworkMissingFallback:
    """load_optimized() when framework_ok is False on mps (Brian's exact case)."""

    def test_uses_onnx_coreml_when_prebuilt_model_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        onnx_path = tmp_path / "yolo26n.onnx"
        onnx_path.write_bytes(b"fake-onnx")

        env = _mps_env(framework_ok=False)
        sentinel = object()
        with mock.patch.object(env, "_load_onnx_coreml", return_value=sentinel) as m:
            model, fmt = env.load_optimized("yolo26n", use_optimized=True)

        m.assert_called_once_with("yolo26n.onnx")
        assert model is sentinel
        assert fmt == "onnx"

    def test_never_imports_ultralytics_when_framework_missing(self, tmp_path, monkeypatch):
        """The historical bug: this path must not need ultralytics at all."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "yolo26n.onnx").write_bytes(b"fake-onnx")

        env = _mps_env(framework_ok=False)
        with mock.patch.object(env, "_load_onnx_coreml", return_value=object()):
            with mock.patch.dict(sys.modules, {"ultralytics": None}):
                # If the code path tried `import ultralytics` here, this would
                # raise ImportError since sys.modules["ultralytics"] is None.
                env.load_optimized("yolo26n", use_optimized=True)

    def test_raises_clear_error_when_no_prebuilt_model_and_no_framework(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        env = _mps_env(framework_ok=False)
        with pytest.raises(RuntimeError, match="torch/ultralytics"):
            env.load_optimized("yolo26n", use_optimized=True)
