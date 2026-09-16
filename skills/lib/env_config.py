"""
env_config.py — Shared hardware environment detection and model optimization.

Provides a single entry point for any DeepCamera skill to:
  1. Detect available compute hardware (NVIDIA, AMD, Apple, Intel, CPU)
  2. Auto-export models to the optimal inference format
  3. Load cached optimized models with PyTorch fallback

Usage:
    from lib.env_config import HardwareEnv

    env = HardwareEnv.detect()
    model, fmt = env.load_optimized("yolo26n")
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _log(msg: str):
    """Log to stderr."""
    print(f"[env_config] {msg}", file=sys.stderr, flush=True)


# ─── Backend definitions ────────────────────────────────────────────────────

@dataclass
class BackendSpec:
    """Specification for a compute backend's optimized export."""
    name: str               # "cuda", "rocm", "mps", "intel", "cpu"
    export_format: str      # ultralytics export format string
    model_suffix: str       # file extension/dir to look for cached model
    half: bool = True       # use FP16
    extra_export_args: dict = field(default_factory=dict)
    compute_units: Optional[str] = None  # CoreML compute units: "cpu_and_ne", "all", etc.


BACKEND_SPECS = {
    "cuda": BackendSpec(
        name="cuda",
        export_format="engine",
        model_suffix=".engine",
        half=True,
    ),
    "rocm": BackendSpec(
        name="rocm",
        export_format="pytorch",     # PyTorch + HIP — ultralytics ONNX doesn't support ROCMExecutionProvider
        model_suffix=".pt",
        half=False,
    ),
    "mps": BackendSpec(
        name="mps",
        export_format="onnx",
        model_suffix=".onnx",
        half=False,  # ONNX Runtime handles precision internally
        # ONNX Runtime + CoreMLExecutionProvider bypasses the broken
        # MPSGraphExecutable MLIR pipeline on macOS 26.x while still
        # leveraging GPU/ANE via CoreML under the hood.
    ),
    "intel": BackendSpec(
        name="intel",
        export_format="openvino",
        model_suffix="_openvino_model",
        half=True,
    ),
    "cpu": BackendSpec(
        name="cpu",
        export_format="onnx",
        model_suffix=".onnx",
        half=False,
    ),
}

# ─── ONNX + CoreML EP wrapper ────────────────────────────────────────────────
# Provides an ultralytics-compatible model interface using onnxruntime directly
# with CoreMLExecutionProvider for ~6ms inference on Apple Silicon (vs 21ms when
# ultralytics defaults to CPUExecutionProvider).

class _BoxResult:
    """Minimal replacement for ultralytics Boxes result."""
    __slots__ = ('xyxy', 'conf', 'cls')

    def __init__(self, xyxy, conf, cls):
        self.xyxy = xyxy   # [[x1,y1,x2,y2]]
        self.conf = conf   # [conf]
        self.cls = cls     # [cls_id]


class _DetResult:
    """Minimal replacement for ultralytics Results."""
    __slots__ = ('boxes',)

    def __init__(self, boxes: list):
        self.boxes = boxes


class _OnnxCoreMLModel:
    """ONNX Runtime model with CoreML EP, compatible with ultralytics API.

    Supports: model(image_path_or_pil, conf=0.5, verbose=False)
    Returns:  list of _DetResult with .boxes iterable of _BoxResult
    """

    def __init__(self, session, class_names: dict):
        self.session = session
        self.names = class_names
        self._input_name = session.get_inputs()[0].name
        # Expected input shape: [1, 3, H, W]
        shape = session.get_inputs()[0].shape
        self._input_h = shape[2] if isinstance(shape[2], int) else 640
        self._input_w = shape[3] if isinstance(shape[3], int) else 640

    def __call__(self, source, conf: float = 0.25, verbose: bool = True, **kwargs):
        """Run inference on an image path or PIL Image.

        All models use onnx-community HuggingFace format:
          outputs[0] = logits  [1, 300, 80]  (raw, pre-sigmoid)
          outputs[1] = pred_boxes [1, 300, 4] (cx, cy, w, h normalized 0..1)
        """
        import numpy as np
        from PIL import Image

        # Load image
        if isinstance(source, str):
            img = Image.open(source).convert("RGB")
        elif isinstance(source, Image.Image):
            img = source.convert("RGB")
        else:
            img = Image.fromarray(source).convert("RGB")

        orig_w, orig_h = img.size

        # Letterbox resize to input size
        scale = min(self._input_w / orig_w, self._input_h / orig_h)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        img_resized = img.resize((new_w, new_h), Image.BILINEAR)

        # Pad to input size (center)
        pad_x = (self._input_w - new_w) // 2
        pad_y = (self._input_h - new_h) // 2
        canvas = np.full((self._input_h, self._input_w, 3), 114, dtype=np.uint8)
        canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = np.array(img_resized)

        # HWC→CHW, normalize, add batch dim
        blob = canvas.transpose(2, 0, 1).astype(np.float32) / 255.0
        blob = np.expand_dims(blob, 0)

        # Run inference
        outputs = self.session.run(None, {self._input_name: blob})
        logits = outputs[0][0]      # [300, 80] raw class logits
        pred_boxes = outputs[1][0]  # [300, 4]  cx, cy, w, h (normalized 0..1)

        # Sigmoid → class probabilities
        probs = 1.0 / (1.0 + np.exp(-logits))

        # Parse detections
        boxes = []
        for i in range(len(pred_boxes)):
            cls_id = int(np.argmax(probs[i]))
            det_conf = float(probs[i][cls_id])
            if det_conf < conf:
                continue

            # cx,cy,w,h (normalized) → x1,y1,x2,y2 (original image pixels)
            cx, cy, bw, bh = pred_boxes[i]
            px_cx = cx * self._input_w
            px_cy = cy * self._input_h
            px_w = bw * self._input_w
            px_h = bh * self._input_h

            x1 = max(0, min((px_cx - px_w / 2 - pad_x) / scale, orig_w))
            y1 = max(0, min((px_cy - px_h / 2 - pad_y) / scale, orig_h))
            x2 = max(0, min((px_cx + px_w / 2 - pad_x) / scale, orig_w))
            y2 = max(0, min((px_cy + px_h / 2 - pad_y) / scale, orig_h))

            boxes.append(_BoxResult(
                xyxy=np.array([[x1, y1, x2, y2]]),
                conf=np.array([det_conf]),
                cls=np.array([cls_id]),
            ))

        return [_DetResult(boxes)]


# ─── Hardware detection ──────────────────────────────────────────────────────

@dataclass
class HardwareEnv:
    """Detected hardware environment with model optimization capabilities."""

    backend: str = "cpu"              # "cuda" | "rocm" | "mps" | "intel" | "cpu"
    device: str = "cpu"               # torch device string
    export_format: str = "onnx"       # optimal export format
    compute_units: str = "all"        # CoreML compute units (Apple only)
    gpu_name: str = ""                # human-readable GPU name
    gpu_memory_mb: int = 0            # GPU memory in MB
    driver_version: str = ""          # GPU driver version
    framework_ok: bool = False        # True if optimized runtime is importable
    detection_details: dict = field(default_factory=dict)  # raw detection info

    # Timing (populated by export/load)
    export_ms: float = 0.0
    load_ms: float = 0.0

    @staticmethod
    def detect() -> "HardwareEnv":
        """Probe the system and return a populated HardwareEnv."""
        env = HardwareEnv()

        # Try each backend in priority order
        if env._try_cuda():
            pass
        elif env._try_rocm():
            pass
        elif env._try_mps():
            pass
        elif env._try_intel():
            pass
        else:
            env._fallback_cpu()

        # Set export format and compute units from backend spec
        spec = BACKEND_SPECS.get(env.backend, BACKEND_SPECS["cpu"])
        env.export_format = spec.export_format
        if spec.compute_units:
            env.compute_units = spec.compute_units

        # Check if optimized runtime is available
        env.framework_ok = env._check_framework()

        _log(f"Detected: backend={env.backend}, device={env.device}, "
             f"gpu={env.gpu_name or 'none'}, "
             f"format={env.export_format}, "
             f"framework_ok={env.framework_ok}")

        return env

    def _try_cuda(self) -> bool:
        """Detect NVIDIA GPU via nvidia-smi (with Windows path search) and WMI fallback."""
        nvidia_smi = shutil.which("nvidia-smi")

        # Windows: check well-known paths if not on PATH
        if not nvidia_smi and platform.system() == "Windows":
            for candidate in [
                Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
                / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
                Path(os.environ.get("WINDIR", r"C:\Windows"))
                / "System32" / "nvidia-smi.exe",
            ]:
                if candidate.is_file():
                    nvidia_smi = str(candidate)
                    _log(f"Found nvidia-smi at {nvidia_smi}")
                    break

        if nvidia_smi:
            try:
                result = subprocess.run(
                    [nvidia_smi, "--query-gpu=name,memory.total,driver_version",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    line = result.stdout.strip().split("\n")[0]
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        self.backend = "cuda"
                        self.device = "cuda"
                        self.gpu_name = parts[0]
                        self.gpu_memory_mb = int(float(parts[1]))
                        self.driver_version = parts[2]
                        self.detection_details["nvidia_smi"] = line
                        _log(f"NVIDIA GPU: {self.gpu_name} ({self.gpu_memory_mb}MB, driver {self.driver_version})")
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
                _log(f"nvidia-smi probe failed: {e}")

        # Windows WMI fallback: detect NVIDIA GPU even without nvidia-smi on PATH
        if platform.system() == "Windows":
            return self._try_cuda_wmi()

        return False

    def _try_cuda_wmi(self) -> bool:
        """Windows-only: detect NVIDIA GPU via WMI (wmic)."""
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get",
                 "Name,AdapterRAM,DriverVersion", "/format:csv"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return False

            for line in result.stdout.strip().split("\n"):
                if "NVIDIA" in line.upper():
                    parts = [p.strip() for p in line.split(",")]
                    # CSV format: Node,AdapterRAM,DriverVersion,Name
                    if len(parts) >= 4:
                        self.backend = "cuda"
                        self.device = "cuda"
                        self.gpu_name = parts[3]
                        try:
                            self.gpu_memory_mb = int(int(parts[1]) / (1024 * 1024))
                        except (ValueError, IndexError):
                            pass
                        self.driver_version = parts[2] if len(parts) > 2 else ""
                        self.detection_details["wmi"] = line
                        _log(f"NVIDIA GPU (WMI): {self.gpu_name} ({self.gpu_memory_mb}MB)")
                        return True
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
            _log(f"WMI probe failed: {e}")
        return False

    def _try_rocm(self) -> bool:
        """Detect AMD GPU via amd-smi (preferred) or rocm-smi."""
        has_amd_smi = shutil.which("amd-smi") is not None
        has_rocm_smi = shutil.which("rocm-smi") is not None
        has_rocm_dir = Path("/opt/rocm").is_dir()

        if not (has_amd_smi or has_rocm_smi or has_rocm_dir):
            return False

        self.backend = "rocm"
        # ROCm exposes as CUDA in PyTorch — but only if PyTorch-ROCm is installed
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
                _log("PyTorch CUDA/ROCm not available, using CPU for PyTorch fallback")
        except ImportError:
            self.device = "cpu"

        # Strategy 1: amd-smi static --json (ROCm 6.3+/7.x, richest output)
        if has_amd_smi:
            try:
                result = subprocess.run(
                    ["amd-smi", "static", "--json"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    import json as _json
                    data = _json.loads(result.stdout)
                    # amd-smi may return {"gpu_data": [...]} or a bare list
                    gpu_list = data.get("gpu_data", data) if isinstance(data, dict) else data
                    if isinstance(gpu_list, list) and len(gpu_list) > 0:
                        # Pick GPU with most VRAM (discrete > iGPU)
                        def _vram_mb(g):
                            vram = g.get("vram", {}).get("size", {})
                            if isinstance(vram, dict):
                                return int(vram.get("value", 0))
                            return 0

                        best_gpu = max(gpu_list, key=_vram_mb)
                        best_idx = gpu_list.index(best_gpu)
                        asic = best_gpu.get("asic", {})
                        vram = best_gpu.get("vram", {}).get("size", {})

                        self.gpu_name = asic.get("market_name", "AMD GPU")
                        self.gpu_memory_mb = int(vram.get("value", 0)) if isinstance(vram, dict) else 0
                        self.detection_details["amd_smi"] = {
                            "gpu_index": best_idx,
                            "gfx_version": asic.get("target_graphics_version", ""),
                            "total_gpus": len(gpu_list),
                        }

                        # Pin to discrete GPU if multiple GPUs present
                        if len(gpu_list) > 1:
                            os.environ["HIP_VISIBLE_DEVICES"] = str(best_idx)
                            os.environ["ROCR_VISIBLE_DEVICES"] = str(best_idx)
                            _log(f"Multi-GPU: pinned to GPU {best_idx} ({self.gpu_name})")
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, Exception) as e:
                _log(f"amd-smi probe failed: {e}")

        # Strategy 2: rocm-smi fallback (legacy ROCm <6.3)
        if not self.gpu_name and has_rocm_smi:
            try:
                result = subprocess.run(
                    ["rocm-smi", "--showproductname", "--csv"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        self.gpu_name = lines[1].split(",")[0].strip()
                self.detection_details["rocm_smi"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            try:
                result = subprocess.run(
                    ["rocm-smi", "--showmeminfo", "vram", "--csv"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n")[1:]:
                        parts = line.split(",")
                        if len(parts) >= 2:
                            try:
                                self.gpu_memory_mb = int(float(parts[0].strip()) / (1024 * 1024))
                            except ValueError:
                                pass
                            break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        _log(f"AMD ROCm GPU: {self.gpu_name or 'detected'} ({self.gpu_memory_mb}MB)")
        return True

    def _try_mps(self) -> bool:
        """Detect Apple Silicon via uname + sysctl."""
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            return False

        self.backend = "mps"
        self.device = "mps"

        # Get chip name
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                self.gpu_name = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.gpu_name = "Apple Silicon"

        # Get total memory (shared with GPU on Apple Silicon)
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                self.gpu_memory_mb = int(int(result.stdout.strip()) / (1024 * 1024))
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass

        _log(f"Apple Silicon: {self.gpu_name} ({self.gpu_memory_mb}MB unified)")
        return True

    def _try_intel(self) -> bool:
        """Detect Intel OpenVINO-capable hardware."""
        # Check for OpenVINO installation
        has_openvino = False
        try:
            import openvino  # noqa: F401
            has_openvino = True
        except ImportError:
            # Check for system install
            has_openvino = Path("/opt/intel/openvino").is_dir()

        if not has_openvino:
            # Check CPU flags for Intel-specific features (AVX-512, AMX)
            try:
                if platform.system() == "Linux":
                    with open("/proc/cpuinfo") as f:
                        cpuinfo = f.read()
                    if "GenuineIntel" in cpuinfo:
                        self.backend = "intel"
                        self.device = "cpu"
                        self.gpu_name = "Intel CPU"
                        _log("Intel CPU detected (no OpenVINO installed)")
                        return True
            except FileNotFoundError:
                pass
            return False

        self.backend = "intel"
        self.device = "cpu"  # OpenVINO handles device selection internally
        self.gpu_name = "Intel (OpenVINO)"

        # Check for Intel GPU / NPU
        try:
            from openvino.runtime import Core
            core = Core()
            devices = core.available_devices
            self.detection_details["openvino_devices"] = devices
            if "GPU" in devices:
                self.gpu_name = "Intel GPU (OpenVINO)"
            if "NPU" in devices:
                self.gpu_name = "Intel NPU (OpenVINO)"
            _log(f"OpenVINO devices: {devices}")
        except Exception:
            pass

        _log(f"Intel: {self.gpu_name}")
        return True

    def _fallback_cpu(self):
        """CPU-only fallback."""
        self.backend = "cpu"
        self.device = "cpu"
        self.gpu_name = ""

        # Report CPU info
        try:
            self.detection_details["cpu"] = platform.processor() or "unknown"
        except Exception:
            pass

        _log("No GPU detected, using CPU backend")

    def _check_rocm_runtime(self):
        """Verify onnxruntime has ROCm provider, not just CPU."""
        import onnxruntime
        providers = onnxruntime.get_available_providers()
        if "ROCmExecutionProvider" in providers or "MIGraphXExecutionProvider" in providers:
            _log(f"onnxruntime ROCm providers: {providers}")
            return True
        _log(f"onnxruntime providers: {providers} — ROCmExecutionProvider not found")
        _log("Fix: pip uninstall onnxruntime && pip install onnxruntime-rocm")
        raise ImportError("ROCmExecutionProvider not available")

    def _check_mps_runtime(self):
        """Verify onnxruntime has CoreML provider for Apple GPU/ANE acceleration.

        ONNX Runtime + CoreMLExecutionProvider bypasses the broken
        MPSGraphExecutable MLIR pipeline (macOS 26.x) while still routing
        inference through CoreML to leverage GPU and Neural Engine.
        """
        import onnxruntime
        providers = onnxruntime.get_available_providers()
        if "CoreMLExecutionProvider" in providers:
            _log(f"onnxruntime CoreML provider available: {providers}")
            return True
        _log(f"onnxruntime providers: {providers} — CoreMLExecutionProvider not found")
        _log("Fix: pip install onnxruntime  (arm64 macOS wheel includes CoreML EP)")
        raise ImportError("CoreMLExecutionProvider not available")

    def _check_framework(self) -> bool:
        """Check if the optimized inference runtime is importable and compatible."""
        checks = {
            "cuda": lambda: __import__("tensorrt"),
            "rocm": lambda: self._check_rocm_runtime(),
            "mps": lambda: self._check_mps_runtime(),
            "intel": lambda: __import__("openvino"),
            "cpu": lambda: __import__("onnxruntime"),
        }

        check = checks.get(self.backend)
        if not check:
            return False
        try:
            check()
            return True
        except ImportError:
            _log(f"Optimized runtime not installed for {self.backend}, "
                 f"will use PyTorch fallback")
            return False

    # ─── Model export & loading ──────────────────────────────────────────

    def get_optimized_path(self, model_name: str) -> Path:
        """Get the expected path for the optimized model."""
        spec = BACKEND_SPECS.get(self.backend, BACKEND_SPECS["cpu"])
        return Path(f"{model_name}{spec.model_suffix}")

    def export_model(self, model, model_name: str) -> Optional[Path]:
        """Export PyTorch model to optimal format. Returns path or None."""
        if not self.framework_ok:
            _log(f"Skipping export — {self.backend} runtime not available")
            return None

        spec = BACKEND_SPECS.get(self.backend, BACKEND_SPECS["cpu"])
        optimized_path = self.get_optimized_path(model_name)

        # Already exported
        if optimized_path.exists():
            _log(f"Cached model found: {optimized_path}")
            return optimized_path

        # Guard: numpy 2.x breaks coremltools PyTorch→MIL converter
        # (TypeError: only 0-dimensional arrays can be converted to Python scalars)
        if spec.export_format == "coreml":
            try:
                import numpy as np
                np_major = int(np.__version__.split('.')[0])
                if np_major >= 2:
                    _log(f"numpy {np.__version__} detected — CoreML export "
                         f"requires numpy<2.0.0 (coremltools incompatibility)")
                    _log("Fix: pip install 'numpy>=1.24,<2.0'")
                    return None
            except Exception:
                pass  # If numpy check fails, try export anyway

        try:
            _log(f"Exporting {model_name}.pt → {spec.export_format} "
                 f"(one-time, may take 30-120s)...")
            t0 = time.perf_counter()

            export_kwargs = {
                "format": spec.export_format,
                "half": spec.half,
            }
            export_kwargs.update(spec.extra_export_args)

            exported = model.export(**export_kwargs)
            self.export_ms = (time.perf_counter() - t0) * 1000

            exported_path = Path(exported)
            if exported_path.exists():
                _log(f"Export complete: {exported_path} ({self.export_ms:.0f}ms)")
                return exported_path

            _log(f"Export returned {exported} but path not found")
        except Exception as e:
            _log(f"Export failed ({spec.export_format}): {e}")

        return None

    def _load_coreml_with_compute_units(self, model_path: str):
        """
        Load a CoreML model via YOLO with specific compute_units.

        Monkey-patches coremltools.MLModel to inject compute_units
        (e.g. CPU_AND_NE for Neural Engine) since ultralytics doesn't
        expose this parameter. Patch is scoped and immediately restored.
        """
        from ultralytics import YOLO

        # Map string config → coremltools enum
        _COMPUTE_UNIT_MAP = {
            "all": "ALL",
            "cpu_only": "CPU_ONLY",
            "cpu_and_gpu": "CPU_AND_GPU",
            "cpu_and_ne": "CPU_AND_NE",
        }

        ct_enum_name = _COMPUTE_UNIT_MAP.get(self.compute_units)
        if not ct_enum_name:
            _log(f"Unknown compute_units '{self.compute_units}', using default")
            return YOLO(model_path)

        try:
            import coremltools as ct
            target_units = getattr(ct.ComputeUnit, ct_enum_name, None)
            if target_units is None:
                _log(f"coremltools.ComputeUnit.{ct_enum_name} not available")
                return YOLO(model_path)

            # Temporarily patch MLModel to inject compute_units
            _OrigMLModel = ct.models.MLModel

            class _PatchedMLModel(_OrigMLModel):
                def __init__(self, *args, **kwargs):
                    kwargs.setdefault('compute_units', target_units)
                    super().__init__(*args, **kwargs)

            ct.models.MLModel = _PatchedMLModel
            try:
                model = YOLO(model_path)
            finally:
                ct.models.MLModel = _OrigMLModel  # Always restore

            _log(f"CoreML model loaded with compute_units={ct_enum_name} "
                 f"(Neural Engine preferred)")
            return model

        except ImportError:
            _log("coremltools not available, loading without compute_units")
            return YOLO(model_path)

    # ── ONNX model download from HuggingFace ──────────────────────────

    # Maps model base name → onnx-community HuggingFace repo
    _ONNX_HF_REPOS = {
        "yolo26n": "onnx-community/yolo26n-ONNX",
        "yolo26s": "onnx-community/yolo26s-ONNX",
        "yolo26m": "onnx-community/yolo26m-ONNX",
        "yolo26l": "onnx-community/yolo26l-ONNX",
    }

    def _download_onnx_from_hf(self, model_name: str, dest_path: Path) -> bool:
        """Download pre-built ONNX model from onnx-community on HuggingFace.

        Uses urllib (no extra dependencies). Downloads to dest_path.
        Returns True on success, False on failure.
        """
        repo = self._ONNX_HF_REPOS.get(model_name)
        if not repo:
            _log(f"No HuggingFace repo for {model_name}")
            return False

        url = f"https://huggingface.co/{repo}/resolve/main/onnx/model.onnx"
        names_url = None  # class names not available on HF, use bundled nano names

        _log(f"Downloading {model_name}.onnx from {repo}...")
        try:
            import urllib.request
            import shutil

            # Download ONNX model
            tmp_path = str(dest_path) + ".download"
            with urllib.request.urlopen(url) as resp, open(tmp_path, 'wb') as f:
                shutil.copyfileobj(resp, f)

            # Rename to final path
            Path(tmp_path).rename(dest_path)
            size_mb = dest_path.stat().st_size / 1e6
            _log(f"Downloaded {model_name}.onnx ({size_mb:.1f} MB)")

            # Create class names JSON if missing (COCO 80 — same for all YOLO models)
            names_path = Path(str(dest_path).replace('.onnx', '_names.json'))
            if not names_path.exists():
                # Try copying from nano (which is shipped in the repo)
                nano_names = dest_path.parent / "yolo26n_names.json"
                if nano_names.exists():
                    shutil.copy2(str(nano_names), str(names_path))
                    _log(f"Copied class names from yolo26n_names.json")
                else:
                    # Generate default COCO names
                    import json
                    coco_names = {str(i): f"class_{i}" for i in range(80)}
                    with open(str(names_path), 'w') as f:
                        json.dump(coco_names, f)
                    _log("Generated default class names")

            return True
        except Exception as e:
            _log(f"HuggingFace download failed: {e}")
            # Clean up partial download
            for p in [str(dest_path) + ".download", str(dest_path)]:
                try:
                    Path(p).unlink(missing_ok=True)
                except Exception:
                    pass
            return False

    def _load_onnx_coreml(self, onnx_path: str):
        """Load ONNX model with CoreMLExecutionProvider for fast GPU/ANE inference.

        Returns an OnnxCoreMLModel wrapper that is compatible with the
        ultralytics model(frame_path, conf=...) call pattern.
        """
        import onnxruntime as ort

        providers = ['CoreMLExecutionProvider', 'CPUExecutionProvider']
        session = ort.InferenceSession(onnx_path, providers=providers)
        active = session.get_providers()
        _log(f"ONNX+CoreML session: {active}")

        # Load class names from companion JSON (avoids torch/ultralytics dep)
        import json
        names_path = onnx_path.replace('.onnx', '_names.json')
        try:
            with open(names_path) as f:
                raw = json.load(f)
            # JSON keys are strings; convert to int-keyed dict
            class_names = {int(k): v for k, v in raw.items()}
            _log(f"Loaded {len(class_names)} class names from {Path(names_path).name}")
        except FileNotFoundError:
            # Fallback: try loading from .pt if JSON doesn't exist
            try:
                from ultralytics import YOLO
                pt_path = onnx_path.replace('.onnx', '.pt')
                pt_model = YOLO(pt_path)
                class_names = pt_model.names
                _log(f"Loaded class names from {Path(pt_path).name} (fallback)")
            except Exception:
                # Last resort: use COCO 80-class defaults
                _log("WARNING: No class names found, using generic labels")
                class_names = {i: f"class_{i}" for i in range(80)}

        return _OnnxCoreMLModel(session, class_names)

    def load_optimized(self, model_name: str, use_optimized: bool = True):
        """
        Load the best available model for this hardware.

        Returns:
            (model, format_str) — the YOLO model and its format name
        """
        t0 = time.perf_counter()

        if use_optimized and self.framework_ok:
            # Try loading from cache first (no export needed)
            optimized_path = self.get_optimized_path(model_name)
            if optimized_path.exists():
                try:
                    # MPS: use ONNX Runtime + CoreML EP for fast inference
                    if self.backend == "mps":
                        model = self._load_onnx_coreml(str(optimized_path))
                    else:
                        from ultralytics import YOLO
                        model = YOLO(str(optimized_path))
                    self.load_ms = (time.perf_counter() - t0) * 1000
                    _log(f"Loaded {self.export_format} model ({self.load_ms:.0f}ms)")
                    return model, self.export_format
                except Exception as e:
                    _log(f"Failed to load cached model: {e}")

            # Try downloading pre-built ONNX from HuggingFace (no torch needed)
            if self.export_format == "onnx" and self._download_onnx_from_hf(model_name, optimized_path):
                try:
                    if self.backend == "mps":
                        model = self._load_onnx_coreml(str(optimized_path))
                    else:
                        from ultralytics import YOLO
                        model = YOLO(str(optimized_path))
                    self.load_ms = (time.perf_counter() - t0) * 1000
                    _log(f"Loaded HuggingFace ONNX model ({self.load_ms:.0f}ms)")
                    return model, self.export_format
                except Exception as e:
                    _log(f"Failed to load HF-downloaded model: {e}")

            # Try exporting then loading
            from ultralytics import YOLO
            pt_model = YOLO(f"{model_name}.pt")
            exported = self.export_model(pt_model, model_name)
            if exported:
                try:
                    # MPS: use ONNX Runtime + CoreML EP for fast inference
                    if self.backend == "mps":
                        model = self._load_onnx_coreml(str(exported))
                    else:
                        from ultralytics import YOLO
                        model = YOLO(str(exported))
                    self.load_ms = (time.perf_counter() - t0) * 1000
                    _log(f"Loaded freshly exported {self.export_format} model ({self.load_ms:.0f}ms)")
                    return model, self.export_format
                except Exception as e:
                    _log(f"Failed to load exported model: {e}")

            # Fallback: use the PT model we already loaded
            _log("Falling back to PyTorch model")
            fallback_device = self.device
            if fallback_device == "cuda":
                try:
                    import torch
                    if not torch.cuda.is_available():
                        fallback_device = "cpu"
                        _log("torch.cuda not available, falling back to CPU")
                except ImportError:
                    fallback_device = "cpu"
            pt_model.to(fallback_device)
            self.device = fallback_device
            self.load_ms = (time.perf_counter() - t0) * 1000
            return pt_model, "pytorch"

        # No optimization requested or framework missing.
        # mps ships without torch/ultralytics (see requirements_mps.txt) — the
        # pre-built .onnx is still usable via plain CPUExecutionProvider even
        # when the CoreML EP check that sets framework_ok failed, so try that
        # before assuming ultralytics is importable (SharpAI/DeepCamera#207:
        # this branch used to crash with "No module named 'ultralytics'" on
        # every mps machine where framework_ok was False).
        if self.backend == "mps":
            optimized_path = self.get_optimized_path(model_name)
            if optimized_path.exists():
                model = self._load_onnx_coreml(str(optimized_path))
                self.load_ms = (time.perf_counter() - t0) * 1000
                _log(f"Loaded {self.export_format} model via ONNX CPU fallback ({self.load_ms:.0f}ms)")
                return model, self.export_format
            raise RuntimeError(
                f"No optimized runtime available for mps and no pre-built "
                f"{optimized_path} found — cannot load {model_name} without "
                f"torch/ultralytics, which are not installed for mps."
            )

        from ultralytics import YOLO
        model = YOLO(f"{model_name}.pt")
        fallback_device = self.device
        if fallback_device == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    fallback_device = "cpu"
                    _log("torch.cuda not available, falling back to CPU")
            except ImportError:
                fallback_device = "cpu"
        model.to(fallback_device)
        self.device = fallback_device
        self.load_ms = (time.perf_counter() - t0) * 1000
        return model, "pytorch"

    def to_dict(self) -> dict:
        """Serialize environment info for JSON output."""
        d = {
            "backend": self.backend,
            "device": self.device,
            "export_format": self.export_format,
            "gpu_name": self.gpu_name,
            "gpu_memory_mb": self.gpu_memory_mb,
            "driver_version": self.driver_version,
            "framework_ok": self.framework_ok,
            "export_ms": round(self.export_ms, 1),
            "load_ms": round(self.load_ms, 1),
        }
        if self.backend == "mps":
            d["compute_units"] = self.compute_units
        return d


# ─── CLI: run standalone for diagnostics ─────────────────────────────────────

if __name__ == "__main__":
    env = HardwareEnv.detect()
    print(json.dumps(env.to_dict(), indent=2))
