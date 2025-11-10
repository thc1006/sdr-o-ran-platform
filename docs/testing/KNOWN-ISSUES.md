# Known Issues and Limitations

Last Updated: 2025-11-10
Version: 1.0

This document lists all known issues, bugs, and limitations discovered during development and testing of the SDR-O-RAN platform.

---

## Critical Issues

### None Currently

All critical security issues discovered during testing have been fixed as of 2025-11-10.

---

## High Priority Issues

### 1. DRL Trainer Multiprocessing Pickling Error

**Component**: `03-Implementation/ai-ml-pipeline/training/drl_trainer.py`
**Severity**: High
**Status**: Open

**Description**:
When using multiple parallel environments (`--n-envs > 1`), the DRL trainer fails with a pickling error:
```
_pickle.PicklingError: Can't pickle <class '__main__.RICState'>:
it's not the same object as __main__.RICState
```

**Impact**:
- Training is slower without parallel environments
- Cannot utilize multi-core CPU for training acceleration
- Training time increased by ~4x

**Workaround**:
Use `--n-envs 1` flag:
```bash
python3 drl_trainer.py --algorithm PPO --timesteps 10000 --n-envs 1
```

**Root Cause**:
The `RICState` dataclass is not properly serializable for multiprocessing due to its definition location and structure.

**Proposed Fix**:
1. Move `RICState` to a separate module
2. Add `__getstate__` and `__setstate__` methods
3. Use `@dataclass` with frozen=True for immutability

**References**:
- Python multiprocessing documentation
- Stable-Baselines3 VecEnv requirements

---

### 2. xApp Missing Framework Availability Checks

**Component**: `03-Implementation/orchestration/nephio/packages/oran-ric/xapps/traffic-steering-xapp.py`
**Severity**: High
**Status**: Open

**Description**:
The xApp attempts to use `SDLWrapper` without checking if `ricxappframe` is available, causing runtime errors when the framework is not installed.

**Error**:
```
NameError: name 'SDLWrapper' is not defined
```

**Impact**:
- xApp cannot run in standalone mode
- No way to test xApp logic without full O-RAN SC setup
- Development and testing blocked

**Workaround**:
None currently. xApp requires full O-RAN SC environment.

**Proposed Fix**:
Add conditional logic:
```python
if RICXAPP_AVAILABLE:
    self.sdl = SDLWrapper(use_fake_sdl=False)
else:
    self.sdl = MockSDL()  # Implement mock SDL for testing
```

**Location**: Line 134 in `traffic-steering-xapp.py`

---

## Medium Priority Issues

### 3. gRPC Test Field Name Mismatch

**Component**: `03-Implementation/integration/sdr-oran-connector/test_grpc_connection.py`
**Severity**: Medium
**Status**: Open

**Description**:
Test file uses incorrect field name `timing_offset_ns` instead of `timestamp_ns` as defined in the protobuf schema.

**Error**:
```
ValueError: Protocol message IQSampleBatch has no "timing_offset_ns" field.
```

**Impact**:
- One test (2/4) fails unnecessarily
- Test suite appears broken even though code is correct

**Fix**:
Change line 70:
```python
# Before:
timing_offset_ns=125

# After:
timestamp_ns=125
```

**Status**: Easy fix, low priority

---

### 4. Redis SDL Connection Failures Outside Kubernetes

**Component**: `03-Implementation/ai-ml-pipeline/training/drl_trainer.py`
**Severity**: Medium
**Status**: Expected Behavior

**Description**:
DRL Trainer attempts to connect to Redis SDL at `redis-standalone.ricplt.svc.cluster.local:6379`, which only resolves inside a Kubernetes cluster.

**Warning**:
```
WARNING: Could not send RIC control to SDL: Error -3 connecting to
redis-standalone.ricplt.svc.cluster.local:6379.
Temporary failure in name resolution.
```

**Impact**:
- SDL integration cannot be tested outside K8s
- Warnings flood the logs during training
- Model persistence to SDL not validated

**Workaround**:
Training continues successfully in simulation mode without SDL.

**Proposed Fix**:
Add environment variable for Redis host:
```python
REDIS_HOST = os.environ.get("REDIS_HOST", "redis-standalone.ricplt.svc.cluster.local")
```

---

## Low Priority Issues

### 5. Missing shap Library for Explainable AI

**Component**: `03-Implementation/ai-ml-pipeline/training/drl_trainer.py`
**Severity**: Low
**Status**: Optional Dependency

**Description**:
SHAP (SHapley Additive exPlanations) library not installed, disabling XAI features.

**Warning**:
```
Warning: shap not installed for XAI
Run: pip install shap
```

**Impact**:
- Cannot generate model explanations
- Missing interpretability features
- Non-critical for core functionality

**Fix**:
```bash
pip install shap
```

**Note**: SHAP can be slow for large models, so it's intentionally optional.

---

### 6. Commented Out Protobuf Imports

**Component**:
- `03-Implementation/integration/sdr-oran-connector/sdr_grpc_server.py` (lines 33-34)
- `03-Implementation/integration/sdr-oran-connector/oran_grpc_client.py` (lines 30-31)

**Severity**: Low
**Status**: Code Clarity Issue

**Description**:
Protobuf imports are commented out, but code still works due to dynamic import handling.

**Code**:
```python
# import sdr_oran_pb2
# import sdr_oran_pb2_grpc
```

**Impact**:
- Confusing for code reviewers
- Unclear why code works with commented imports
- Poor code maintainability

**Proposed Fix**:
Either uncomment the imports or add explanation comment.

---

## Hardware Limitations

### 7. No USRP Hardware Available

**Severity**: N/A (Expected Limitation)
**Status**: Hardware Not Purchased

**Description**:
All SDR functionality is simulated. USRP X310 hardware ($7,500) not available for testing.

**Impact**:
- Cannot test real signal processing
- Cannot validate performance claims
- Cannot test with actual satellites
- All USRP operations are mocked

**Components Affected**:
- VITA 49.2 receiver
- GNU Radio flowgraphs
- Signal quality metrics
- Real-time processing

**Workaround**:
Use simulation mode. See SIMULATION-ALTERNATIVES.md for alternatives.

---

### 8. O-RAN SC Framework Not Installed

**Severity**: N/A (Expected Limitation)
**Status**: Complex External Dependency

**Description**:
`ricxappframe` and O-RAN Software Community Near-RT RIC not installed.

**Impact**:
- xApp cannot run in production mode
- E2 interface untested
- RMR messaging untested
- SDL integration partial

**Requirements**:
- O-RAN SC Near-RT RIC platform
- RMR (RIC Message Router)
- SDL (Shared Data Layer)
- E2 termination

**Installation Complexity**: High (requires multi-day setup)

**Workaround**:
Use simulation frameworks. See SIMULATION-ALTERNATIVES.md.

---

## Performance Issues

### None Currently

Performance has not been benchmarked with real hardware. Simulated performance is acceptable for development.

---

## Security Issues (Fixed)

### ~~9. Hardcoded SECRET_KEY~~ (FIXED 2025-11-10)

**Status**: FIXED
**Component**: `sdr_api_server.py`

**Previous Issue**:
```python
SECRET_KEY = "your-secret-key-change-in-production"
```

**Fix Applied**:
- SECRET_KEY now loaded from `SDR_API_SECRET_KEY` environment variable
- Auto-generates secure random key if not set (with warning)
- Production deployments must set environment variable

---

### ~~10. Hardcoded Admin Password~~ (FIXED 2025-11-10)

**Status**: FIXED
**Component**: `sdr_api_server.py`

**Previous Issue**:
```python
"hashed_password": pwd_context.hash("secret")
```

**Fix Applied**:
- Admin credentials now loaded from environment variables:
  - `SDR_ADMIN_USERNAME` (default: "admin")
  - `SDR_ADMIN_PASSWORD` (default: "secret")
  - `SDR_ADMIN_EMAIL`
- Warns if default credentials are used
- Production deployments must set environment variables

---

### ~~11. Missing Input Validation~~ (FIXED 2025-11-10)

**Status**: FIXED
**Component**: `sdr_api_server.py`

**Fix Applied**:
- Added regex pattern validation for all string inputs
- Added length limits (min/max)
- Added format validation for endpoints
- Prevents injection attacks

**Validation Added**:
- `station_id`: `^[a-zA-Z0-9_-]{1,64}$`
- `usrp_device`: `^usrp-[0-9]{3}$`
- `frequency_band`: `^(C|Ku|Ka)$`
- `modulation_scheme`: `^(QPSK|8PSK|16APSK|32APSK)$`
- `oran_endpoint`: `^[a-zA-Z0-9.-]+:[0-9]{1,5}$`

---

## Documentation Issues

### None Currently

Documentation has been updated to reflect actual implementation status.

---

## Test Coverage Issues

### 12. Low Unit Test Coverage

**Severity**: Medium
**Status**: Open

**Current Coverage**: ~15-20%
**Target Coverage**: 60-80%

**Missing Tests**:
- DRL environment reward function
- Quantum crypto edge cases
- gRPC error handling
- xApp decision logic
- VITA 49.2 packet parsing

**Impact**:
- Reduced confidence in code correctness
- Harder to detect regressions
- Difficult to refactor safely

**Proposed Action**:
Create comprehensive test suite following TDD principles.

---

## Integration Issues

### 13. No End-to-End Integration Tests

**Severity**: Medium
**Status**: Open

**Description**:
Individual components tested, but no tests verify complete data flow from SDR → gRPC → RIC → xApp → Control.

**Missing Test Scenarios**:
1. IQ samples from VITA 49.2 → gRPC → O-RAN
2. DRL model training → SDL → xApp loading
3. E2 KPM indication → xApp decision → E2 control
4. Full OAuth2 flow → API call → USRP control

**Impact**:
- Integration bugs may not be discovered until deployment
- Unclear if components actually work together
- No confidence in end-to-end functionality

**Proposed Action**:
Create integration test suite with mocked external dependencies.

---

## Reporting Issues

If you discover new issues:

1. Check if the issue is already listed above
2. Create a GitHub issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or error messages

3. For security issues, contact: thc1006@ieee.org (do not post publicly)

---

## Issue Resolution Process

1. **Critical**: Fix immediately, block releases
2. **High**: Fix before next release
3. **Medium**: Fix in next 2-3 releases
4. **Low**: Fix when convenient, or mark as "won't fix"

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-10 | Initial known issues document |

---

**Maintainer**: Hsiu-Chi Tsai (thc1006@ieee.org)
**Last Reviewed**: 2025-11-10
