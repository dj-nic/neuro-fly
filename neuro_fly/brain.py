"""Adapter for the pinned, separate NeuroHex checkout and its real data."""

from collections import Counter
from dataclasses import dataclass
import importlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import time


REFERENCE_COMMIT = "5d1052b995db12fa1baf8d42f6a94c3f0695817d"
PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = PROJECT_DIR.parent / "neurohex-reference"
GF_IDS = ("VFB_jrmc30my", "VFB_jrmc30mz")


class BrainSetupError(RuntimeError):
    """The pinned source, validated data or Brian2 environment is unavailable."""


class BrainStepError(RuntimeError):
    """The neural model failed or returned an invalid motor output."""


@dataclass(frozen=True)
class ConnectomeInfo:
    neurons: int
    connection_records: int
    directed_edges: int
    groups: dict[str, int]


def _git(reference: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-C", str(reference), *args], capture_output=True,
            text=True, check=False, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BrainSetupError(f"Git could not inspect the reference at {reference}: {exc}") from exc


def check_reference(reference: Path) -> Path:
    """Require the pinned checkout and all files before importing upstream code."""
    root = Path(reference).expanduser().resolve()
    required = [root / "snn_brain.py"] + [
        root / "connectome_data" / name for name in
        ("adjacency_matrix.npy", "neuron_metadata.json", "connection_list.json")
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise BrainSetupError(
            "NeuroHex reference or Connectome data missing: " + ", ".join(missing)
            + ". On Linux/WSL run 'bash scripts/setup.sh', or pass --reference."
        )

    top = _git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        raise BrainSetupError(f"Reference is not a separate Git checkout: {root}")
    head = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    if head.returncode != 0 or head.stdout.strip() != REFERENCE_COMMIT:
        raise BrainSetupError(f"Reference must be at commit {REFERENCE_COMMIT}: {root}")
    dirty = _git(root, "diff", "--quiet", "HEAD", "--", "snn_brain.py")
    if dirty.returncode != 0:
        raise BrainSetupError(f"Reference snn_brain.py is changed or cannot be checked: {root}")
    return root


def validate_connectome(data_dir: Path) -> ConnectomeInfo:
    """Check real-data structure and consistency before upstream can use a fallback.

    This mirrors the project's existing structural checks. It does not by itself
    establish data provenance or licensing.
    """
    try:
        np = importlib.import_module("numpy")
    except ImportError as exc:
        raise BrainSetupError("NumPy is required for Connectome validation") from exc
    try:
        data_dir = Path(data_dir)
        metadata = json.loads((data_dir / "neuron_metadata.json").read_text(encoding="utf-8"))
        connections = json.loads((data_dir / "connection_list.json").read_text(encoding="utf-8"))
        matrix = np.load(data_dir / "adjacency_matrix.npy", allow_pickle=False)
        if not isinstance(metadata, list) or not isinstance(connections, list):
            raise ValueError("metadata and connections must be lists")
        count = len(metadata)
        if count <= 20 or matrix.shape != (count, count):
            raise ValueError("dummy/incomplete data or incompatible matrix shape")
        if matrix.dtype.kind not in "iuf" or not np.isfinite(matrix).all() or (matrix < 0).any():
            raise ValueError("matrix must contain finite nonnegative numbers")
        if [item["index"] for item in metadata] != list(range(count)):
            raise ValueError("neuron indices are not consecutive")
        ids = {item["id"]: item["index"] for item in metadata}
        if len(ids) != count or not all(isinstance(key, str) and key.startswith("VFB_") for key in ids):
            raise ValueError("neuron IDs are missing, duplicated or not VFB IDs")
        if not set(GF_IDS).issubset(ids):
            raise ValueError("both Giant Fiber neurons must be present")
        if any(metadata[ids[gf]]["group"] != "GF" for gf in GF_IDS):
            raise ValueError("Giant Fiber IDs must belong to the GF group")
        groups = Counter(item["group"] for item in metadata)
        if groups["GF"] != 2 or not all(groups[group] for group in ("LC4", "LPLC2", "DN", "TTMn")):
            raise ValueError("required neuron groups are incomplete")
        expected = np.zeros_like(matrix)
        for connection in connections:
            weight = connection["weight"]
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight < 3:
                raise ValueError("connection weight must be finite and at least 3")
            expected[ids[connection["source_id"]], ids[connection["target_id"]]] += weight
        if not np.array_equal(matrix, expected):
            raise ValueError("adjacency matrix and connection list do not match")
        for gf in GF_IDS:
            if not any(matrix[ids[gf], item["index"]] > 0 for item in metadata
                       if item["group"] in ("DN", "TTMn")):
                raise ValueError(f"{gf} has no connection to a motor group")
        return ConnectomeInfo(count, len(connections), int(np.count_nonzero(matrix)), dict(groups))
    except (OSError, EOFError, ValueError, TypeError, KeyError, IndexError, OverflowError, AttributeError) as exc:
        raise BrainSetupError(f"Invalid Connectome data at {data_dir}: {exc}") from exc


class NeuroHexBrainAdapter:
    """Advance NeuroHex by 20 simulated ms and return its escape magnitude."""

    def __init__(self, reference: Path = DEFAULT_REFERENCE, *, cache_dir: Path | None = None) -> None:
        started = time.perf_counter()
        self.reference = check_reference(reference)
        data_dir = self.reference / "connectome_data"
        self.connectome = validate_connectome(data_dir)
        try:
            self.numpy_version = getattr(importlib.import_module("numpy"), "__version__", "unknown")
            brian2 = importlib.import_module("brian2")
            cache = Path(cache_dir) if cache_dir is not None else PROJECT_DIR / "artifacts" / "cache" / "cython"
            cache.mkdir(parents=True, exist_ok=True)
            brian2.prefs.codegen.runtime.cython.cache_dir = str(cache.resolve())
            brian2.prefs.codegen.target = "cython"
            spec = importlib.util.spec_from_file_location("neuro_fly_neurohex_reference", self.reference / "snn_brain.py")
            if spec is None or spec.loader is None:
                raise ImportError("cannot load snn_brain.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._brain = module.NeuroHexBrain(connectome_dir=str(data_dir))
            if self._brain.N != self.connectome.neurons or len(self._brain.metadata) != self.connectome.neurons:
                raise ValueError("loaded network does not match validated Connectome")
            self.backend = str(brian2.prefs.codegen.target)
            self.brian2_version = getattr(brian2, "__version__", "unknown")
        except Exception as exc:
            raise BrainSetupError(f"Cannot initialize the real NeuroHex brain: {exc}") from exc
        self.initialization_s = time.perf_counter() - started
        self.reference_commit = REFERENCE_COMMIT

    def step(self, looming_strength: float) -> float:
        try:
            if isinstance(looming_strength, bool):
                raise ValueError("boolean is not a sensory strength")
            strength = float(looming_strength)
        except (TypeError, ValueError, OverflowError) as exc:
            raise BrainStepError("looming_strength must be finite and in [0, 1]") from exc
        if not math.isfinite(strength) or not 0 <= strength <= 1:
            raise BrainStepError("looming_strength must be finite and in [0, 1]")
        try:
            result = self._brain.step(visual_input=strength, mechanosensory_input=0.0, duration_ms=20.0)
            if isinstance(result["escape_magnitude"], bool):
                raise ValueError("boolean is not a motor magnitude")
            magnitude = float(result["escape_magnitude"])
        except Exception as exc:
            raise BrainStepError(f"NeuroHex step failed: {exc}") from exc
        if not math.isfinite(magnitude) or not 0 <= magnitude <= 1:
            raise BrainStepError("NeuroHex returned escape_magnitude outside [0, 1] or not finite")
        return magnitude
