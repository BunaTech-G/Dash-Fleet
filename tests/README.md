# Pytest Testing Framework - DashFleet

Comprehensive unit and integration tests for the DashFleet fleet monitoring system.

## Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/                    # Unit test modules
│   ├── test_fleet_utils.py  # Tests for fleet_utils (health scoring, formatting)
│   ├── test_db_utils.py     # Tests for database operations
│   ├── test_schemas.py      # Tests for Marshmallow validation
│   └── test_api.py          # Tests for Flask API endpoints
├── integration/             # Integration tests (future)
└── fixtures/                # Reusable test data (future)
```

## Installation

```bash
# Install pytest and dependencies
pip install pytest pytest-cov pytest-flask pytest-mock

# Or using requirements
pip install -r requirements.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/unit/test_fleet_utils.py
```

### Run specific test class
```bash
pytest tests/unit/test_fleet_utils.py::TestHealthScoreCalculation
```

### Run specific test
```bash
pytest tests/unit/test_fleet_utils.py::TestHealthScoreCalculation::test_perfect_health
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage report
```bash
pytest --cov=. --cov-report=html
```

### Run with markers
```bash
pytest -m "unit"  # Run only unit tests
pytest -m "slow" --durations=10  # Show 10 slowest tests
```

### Run in parallel (requires pytest-xdist)
```bash
pytest -n auto  # Use all CPU cores
```

## Test Coverage

### Current Test Suites

**1. tests/unit/test_fleet_utils.py** (36 tests planned)
- Health score calculation (various metric combinations)
- Byte to GiB conversion
- Uptime formatting (HH:MM:SS)

**2. tests/unit/test_db_utils.py** (25 tests planned)
- Database initialization
- Fleet report insertion
- Fleet state retrieval
- Machine expiration logic
- Multi-tenant org scoping
- Report data handling

**3. tests/unit/test_schemas.py** (28 tests planned)
- ReportSchema validation
  - Valid reports
  - Missing fields
  - Type validation
- MetricsSchema validation
  - Percentage bounds (0-100)
  - Required fields
  - Range checking

**4. tests/unit/test_api.py** (15 tests planned)
- Fleet API endpoints
- Authentication and Bearer tokens
- Rate limiting
- Error handling
- Invalid JSON handling

**Total Coverage: 104+ test cases**

## Fixtures (conftest.py)

### `temp_db`
Temporary SQLite database for isolated testing.

```python
@pytest.fixture
def temp_db():
    """Provides temporary database file."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    yield db_file.name
    os.unlink(db_file.name)  # Cleanup
```

### `sample_report`
Mock fleet metric report for testing.

```python
@pytest.fixture
def sample_report():
    """Provides sample fleet report."""
    return {
        "machine_id": "test-machine",
        "report": {
            "cpu_percent": 35.5,
            "ram_percent": 62.1,
            "disk_percent": 45.3,
            "uptime": 86400,
            "timestamp": time.time()
        }
    }
```

### `sample_machine_stats`
Complete machine statistics example.

```python
@pytest.fixture
def sample_machine_stats():
    """Provides complete machine stats."""
    return {
        "cpu_percent": 35.5,
        "ram_percent": 62.1,
        "disk_percent": 45.3,
        "uptime": 86400,
        "timestamp": time.time(),
        "machine_id": "test-machine",
        "client": "192.168.1.100"
    }
```

## Test Examples

### Testing Health Score Calculation

```python
def test_perfect_health(self):
    """Test health score when all metrics are excellent."""
    stats = {
        "cpu_percent": 10.0,
        "ram_percent": 30.0,
        "disk_percent": 40.0,
    }
    result = calculate_health_score(stats)
    assert result["score"] >= 80
    assert result["status"] == "ok"
```

### Testing Database Operations

```python
def test_insert_valid_report(self, temp_db, sample_report):
    """Test inserting a valid fleet report."""
    init_db(temp_db)
    result = insert_fleet_report(
        temp_db,
        sample_report["machine_id"],
        sample_report["report"],
        org_id="test-org"
    )
    assert result is not None
```

### Testing Marshmallow Schemas

```python
def test_missing_machine_id(self):
    """Test validation fails when machine_id is missing."""
    schema = ReportSchema()
    data = {"report": {"cpu_percent": 35.5}}
    
    with pytest.raises(ValidationError) as exc_info:
        schema.load(data)
    
    assert "machine_id" in exc_info.value.messages
```

### Testing API Endpoints

```python
def test_fleet_report_requires_bearer_token(self, client):
    """Test that POST /api/fleet/report requires authentication."""
    data = {"machine_id": "test", "report": {...}}
    response = client.post("/api/fleet/report", json=data)
    
    # Should fail without Bearer token
    assert response.status_code in [401, 403]
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Local Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

pytest --tb=short
if [ $? -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi
```

## Test Categories

### Unit Tests
Fast, isolated tests for individual functions.
- `tests/unit/test_fleet_utils.py` - Utilities (no DB)
- `tests/unit/test_schemas.py` - Validation (no DB)

### Integration Tests (Future)
Tests that exercise multiple components.
- `tests/integration/test_agent_to_api.py` - Agent → API → DB
- `tests/integration/test_dashboard.py` - Dashboard → API

### Performance Tests (Future)
Benchmarks for critical paths.
- Query performance
- Metric collection speed
- Serialization overhead

## Test Markers

### Available Markers

```python
# In test functions
@pytest.mark.unit       # Fast unit tests
@pytest.mark.slow       # Slow tests (skip with -m "not slow")
@pytest.mark.integration # Integration tests
@pytest.mark.db         # Tests requiring database
@pytest.mark.api        # API tests
```

### Usage

```bash
pytest -m "unit and not slow"  # Unit tests only, skip slow
pytest -m "db"                  # Database tests only
```

## Debugging Tests

### Print Debug Output
```python
def test_something(self):
    print("Debug message")  # Shows with -s flag
    pytest.set_trace()      # Drop to pdb debugger
```

### Run with Debug Output
```bash
pytest -s -v --tb=short tests/unit/test_example.py::TestClass::test_method
```

### Interactive Debugging
```bash
pytest --pdb tests/unit/test_example.py  # Drop to pdb on failure
pytest --pdb-trace tests/unit/test_example.py  # Drop to pdb on each test
```

## Reporting

### HTML Coverage Report
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### JUnit XML Report
```bash
pytest --junit-xml=report.xml
```

### Test Report Summary
```bash
pytest --tb=short -v --maxfail=3
```

## Best Practices

1. **Isolation** - Each test should be independent
2. **Clarity** - Test names describe what they test
3. **Fixtures** - Use fixtures for setup/teardown
4. **Mocking** - Mock external dependencies
5. **Coverage** - Aim for >80% code coverage
6. **Speed** - Keep unit tests fast (<100ms each)

## Known Issues & Limitations

1. **Database Tests** - Use temporary files (temp_db fixture)
2. **API Tests** - May require app context setup
3. **Async Operations** - Not yet tested (agent is sync-only)
4. **External APIs** - Not tested (no dependencies on external services)

## Future Improvements

- [ ] Integration tests for agent → API → DB workflow
- [ ] Performance benchmarks
- [ ] UI tests (JavaScript in fleet.html)
- [ ] Load testing with 100+ machines
- [ ] Stress testing rate limits
- [ ] Multi-tenant isolation tests

---

**Last Updated:** 2026-01-02
**Test Framework:** Pytest 7.4+
**Python Version:** 3.11+
