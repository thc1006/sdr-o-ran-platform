"""
conftest.py for tests/unit/
============================

Adds NTN simulation module paths to sys.path and registers skip
conditions for tests that require optional heavy dependencies
(tensorflow, sionna, httpx, redis, xapp_sdk).

These skips keep the unit-test suite runnable in lightweight CI
environments that do not have GPU-only or proprietary packages.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — make NTN simulation modules importable from repo root
# ---------------------------------------------------------------------------
_REPO = Path(__file__).parent.parent.parent
_NTN  = _REPO / "03-Implementation" / "ntn-simulation"

for _p in [
    _NTN / "rl_power",
    _NTN / "openNTN_integration",
    _NTN / "baseline",
    _NTN / "ml_handover",
    _NTN / "xapps",
    _NTN / "e2_ntn_extension",
    _NTN / "orbit_propagation",
    _REPO / "03-Implementation" / "simulation",
    _REPO / "03-Implementation" / "integration" / "sdr-oran-connector",
    _REPO / "03-Implementation" / "ai-ml-pipeline" / "training",
    _REPO / "03-Implementation" / "sdr-platform" / "api-gateway",
    _REPO / "03-Implementation" / "ric-platform" / "e2-interface",
]:
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
