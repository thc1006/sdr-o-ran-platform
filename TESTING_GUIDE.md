# Testing Guide - SDR-O-RAN Platform

Quick reference for running tests and understanding the test infrastructure.

## Quick Start

### Run All Tests
```bash
cd /home/gnb/thc1006/sdr-o-ran-platform
source venv/bin/activate
pytest tests/ -v --cov=03-Implementation --cov-report=html
```

### View Coverage Report
```bash
# Open in browser
firefox htmlcov/index.html
# or
google-chrome htmlcov/index.html
```

## Test Organization

```
tests/
├── conftest.py                      # Global fixtures and configuration
├── __init__.py
├── unit/                            # Unit tests (isolated components)
│   ├── test_grpc_services.py       # gRPC server/client (23 tests)
│   ├── test_drl_trainer.py         # DRL training pipeline (26 tests)
│   └── test_api_gateway.py         # FastAPI endpoints (31 tests)
├── integration/                     # Integration tests (multi-component)
│   └── test_grpc_integration.py    # gRPC client-server (17 tests)
└── infrastructure/                  # Infrastructure/deployment tests
    ├── test_cicd_config.py         # CI/CD configuration
    ├── test_dev_tools.py           # Development tools
    ├── test_k8s_cluster.py         # Kubernetes cluster
    └── test_core_services.py       # Core services (Redis, Prometheus)
```

## Running Specific Tests

### By Directory
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Infrastructure tests only
pytest tests/infrastructure/ -v
```

### By Marker
```bash
# gRPC tests only
pytest -m grpc -v

# DRL tests only
pytest -m drl -v

# API tests only
pytest -m api -v

# Exclude slow tests
pytest -m "not slow" -v

# Unit tests only (marker)
pytest -m unit -v

# Integration tests only (marker)
pytest -m integration -v
```

### By File
```bash
# Specific test file
pytest tests/unit/test_grpc_services.py -v

# Specific test class
pytest tests/unit/test_grpc_services.py::TestIQSampleGenerator -v

# Specific test case
pytest tests/unit/test_grpc_services.py::TestIQSampleGenerator::test_generate_batch -v
```

### By Pattern
```bash
# All tests with "grpc" in the name
pytest -k grpc -v

# All tests with "statistics" in the name
pytest -k statistics -v

# Exclude tests with "slow" in the name
pytest -k "not slow" -v
```

## Coverage Options

### Basic Coverage
```bash
# Simple coverage report
pytest --cov=03-Implementation

# With missing lines
pytest --cov=03-Implementation --cov-report=term-missing

# HTML report
pytest --cov=03-Implementation --cov-report=html

# XML report (for CI/CD)
pytest --cov=03-Implementation --cov-report=xml
```

### Module-Specific Coverage
```bash
# gRPC modules only
pytest tests/unit/test_grpc_services.py --cov=03-Implementation/integration/sdr-oran-connector

# DRL modules only
pytest tests/unit/test_drl_trainer.py --cov=03-Implementation/ai-ml-pipeline/training

# API modules only
pytest tests/unit/test_api_gateway.py --cov=03-Implementation/sdr-platform/api-gateway
```

### Coverage Thresholds
```bash
# Fail if coverage below 40%
pytest --cov=03-Implementation --cov-fail-under=40

# Show only uncovered lines
pytest --cov=03-Implementation --cov-report=term:skip-covered
```

## Test Markers Reference

Configured in `pytest.ini`:

- `@pytest.mark.unit` - Unit tests (isolated component testing)
- `@pytest.mark.integration` - Integration tests (multi-component)
- `@pytest.mark.grpc` - gRPC service tests
- `@pytest.mark.drl` - Deep reinforcement learning tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.slow` - Slow-running tests (>1 second)
- `@pytest.mark.requires_hardware` - Tests requiring actual hardware
- `@pytest.mark.requires_k8s` - Tests requiring Kubernetes cluster

## Fixtures Reference

Defined in `tests/conftest.py`:

### Session Fixtures
- `project_root` - Path to project root directory

### Function Fixtures
- `mock_redis` - Mock Redis client for SDL operations
- `mock_grpc_context` - Mock gRPC server context
- `sample_ric_state` - Sample RIC state data for testing

### API Testing Fixtures (in test_api_gateway.py)
- `client` - FastAPI TestClient
- `auth_token` - JWT authentication token
- `auth_headers` - Authorization headers with token

## Common Test Patterns

### Testing gRPC Services
```python
def test_my_grpc_function(mock_grpc_context):
    servicer = IQStreamServicer()
    request = Mock()
    request.station_id = "test-station"

    response = servicer.MyFunction(request, mock_grpc_context)

    assert response.success == True
```

### Testing DRL Components
```python
@patch('drl_trainer.redis.Redis')
def test_ric_environment(mock_redis_class, sample_ric_state):
    mock_redis = Mock()
    mock_redis_class.return_value = mock_redis

    env = RICEnvironment(redis_host="localhost")
    obs, info = env.reset()

    assert obs.shape == (11,)
```

### Testing API Endpoints
```python
def test_api_endpoint(client, auth_headers):
    response = client.post(
        "/api/v1/endpoint",
        json={"key": "value"},
        headers=auth_headers
    )

    assert response.status_code == 200
    assert "expected_field" in response.json()
```

## Debugging Tests

### Verbose Output
```bash
# Show print statements
pytest -v -s

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x

# Show full traceback
pytest --tb=long
```

### Debugging Specific Tests
```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start
pytest --trace

# Show all output (including passed tests)
pytest -v -s --tb=short
```

### Coverage Debugging
```bash
# Show which tests cover which lines
pytest --cov=03-Implementation --cov-report=annotate

# Generate coverage data only
pytest --cov=03-Implementation --no-cov-on-fail
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run tests
  run: |
    source venv/bin/activate
    pytest tests/ --cov=03-Implementation --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

### GitLab CI
```yaml
test:
  script:
    - source venv/bin/activate
    - pytest tests/ --cov=03-Implementation --cov-report=xml
  coverage: '/^TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Performance

### Test Execution Times
- **gRPC tests:** ~0.32s (40 tests)
- **Expected full suite:** ~5-10s (128 tests)

### Optimization Tips
```bash
# Parallel execution (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Run only failed tests from last run
pytest --lf

# Run failed first, then others
pytest --ff
```

## Troubleshooting

### Import Errors
```bash
# Ensure all paths are configured
export PYTHONPATH=/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation:$PYTHONPATH

# Or reinstall in development mode
pip install -e .
```

### Missing Dependencies
```bash
# Install all test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx redis torch numpy
```

### Redis Connection Errors
```bash
# Use mock Redis (default in tests)
# Set environment variable if needed
export REDIS_HOST=localhost
```

## Test Development Guidelines

### Writing New Tests

1. **Choose the right test type:**
   - Unit test: Testing a single function/class in isolation
   - Integration test: Testing multiple components together
   - Infrastructure test: Testing deployment/configuration

2. **Use appropriate markers:**
   ```python
   @pytest.mark.unit
   @pytest.mark.grpc
   def test_my_function():
       pass
   ```

3. **Follow naming conventions:**
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test functions: `test_*`

4. **Use fixtures for setup:**
   ```python
   def test_with_fixture(mock_redis, sample_ric_state):
       # Test code here
       pass
   ```

5. **Assert meaningful conditions:**
   ```python
   # Good
   assert response.status_code == 200
   assert "expected_key" in response.json()

   # Bad (too generic)
   assert response
   ```

### Test Quality Checklist

- [ ] Test name clearly describes what is being tested
- [ ] Test has a single, clear purpose
- [ ] Test uses appropriate fixtures
- [ ] Test has proper markers
- [ ] Test includes assertions
- [ ] Test handles both success and failure cases
- [ ] Test is fast (<1s for unit tests)
- [ ] Test is isolated (no external dependencies)
- [ ] Test is deterministic (always same result)
- [ ] Test cleans up after itself

## Coverage Goals

### Current Status
- **gRPC Connector:** 44.37%
- **DRL Trainer:** Tests created (pending torch install)
- **API Gateway:** Tests created (pending httpx install)

### Target Coverage by Module
- Critical modules (gRPC, DRL): 60%+
- API endpoints: 70%+
- Utilities: 50%+
- Generated code: Excluded
- Overall project: 40%+

## Resources

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)

### Configuration Files
- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage configuration
- `tests/conftest.py` - Global fixtures

### Reports
- `htmlcov/index.html` - HTML coverage report
- `coverage.xml` - XML coverage report (for CI/CD)
- `TEST_COVERAGE_REPORT.md` - Detailed coverage analysis

---

**Last Updated:** 2025-11-17
**Test Framework:** pytest 7.4.3
**Coverage Tool:** pytest-cov 4.1.0
