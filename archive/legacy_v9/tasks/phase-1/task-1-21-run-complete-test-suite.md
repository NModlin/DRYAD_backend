# Task 1-21: Run Complete Test Suite

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 4  
**Estimated Hours:** 4 hours  
**Priority:** CRITICAL  
**Dependencies:** All previous test tasks

---

## 🎯 OBJECTIVE

Execute complete test suite, verify all tests pass, achieve >85% coverage, and establish CI/CD test automation.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Run all unit tests
- Run all integration tests
- Run all API tests
- Generate coverage report
- Verify coverage targets met
- Document test results

### Technical Requirements
- pytest test runner
- pytest-cov for coverage
- pytest-xdist for parallel execution
- CI/CD integration

### Performance Requirements
- Full test suite: <5 minutes
- Parallel execution enabled
- Coverage report: <1 minute

---

## 🔧 IMPLEMENTATION

**File:** `scripts/run_tests.sh`

```bash
#!/bin/bash
# Complete Test Suite Runner

set -e

echo "🧪 Running DRYAD.AI Complete Test Suite"
echo "========================================"

# Set test environment
export ENVIRONMENT=test
export DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/dryad_test

# Clean previous coverage
rm -rf htmlcov .coverage coverage.json

# Run tests with coverage
echo "📊 Running tests with coverage..."
pytest \
    --cov=app \
    --cov-report=html \
    --cov-report=json \
    --cov-report=term-missing \
    --cov-fail-under=85 \
    -v \
    -n auto \
    --tb=short

# Check coverage
echo ""
echo "📈 Coverage Summary:"
coverage report --skip-covered

# Generate badge
echo ""
echo "✅ Test suite complete!"
echo "📁 HTML coverage report: htmlcov/index.html"
```

**File:** `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: dryad_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/dryad_test
          REDIS_URL: redis://localhost:6379
        run: |
          pytest \
            --cov=app \
            --cov-report=xml \
            --cov-fail-under=85 \
            -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --strict-markers
    --tb=short
    --cov-branch
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    security: Security tests
```

---

## ✅ DEFINITION OF DONE

- [ ] All tests passing
- [ ] Coverage >85%
- [ ] CI/CD pipeline configured
- [ ] Test results documented
- [ ] No flaky tests
- [ ] Performance targets met

---

## 📊 SUCCESS METRICS

- Test pass rate: 100%
- Coverage: >85%
- Test execution: <5 minutes
- CI/CD: Automated

---

**Estimated Completion:** 4 hours  
**Status:** NOT STARTED

