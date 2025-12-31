# Task 1-22: Fix Failing Tests

**Phase:** 1 - Foundation & Beta Readiness  
**Week:** 4  
**Estimated Hours:** 8 hours  
**Priority:** CRITICAL  
**Dependencies:** Task 1-21 (Run Complete Test Suite)

---

## 🎯 OBJECTIVE

Identify and fix all failing tests, resolve flaky tests, and ensure 100% test pass rate.

---

## 📋 REQUIREMENTS

### Functional Requirements
- Identify all failing tests
- Categorize failures by type
- Fix implementation issues
- Fix test issues
- Eliminate flaky tests
- Verify all tests pass

### Technical Requirements
- Test debugging tools
- Logging and diagnostics
- Test isolation
- Proper cleanup

### Performance Requirements
- All tests passing: 100%
- Flaky tests: 0
- Test stability: 100%

---

## 🔧 IMPLEMENTATION APPROACH

### Step 1: Identify Failures

```bash
# Run tests and capture failures
pytest --tb=long --maxfail=0 > test_results.txt 2>&1

# Analyze failures
python scripts/analyze_test_failures.py
```

**File:** `scripts/analyze_test_failures.py`

```python
"""
Test Failure Analysis
Categorize and prioritize test failures.
"""

from __future__ import annotations

import re
from pathlib import Path
from collections import Counter


class TestFailureAnalyzer:
    """Analyze test failures."""
    
    def __init__(self, results_file: str = "test_results.txt"):
        self.results_file = Path(results_file)
        self.failures = []
    
    def parse_failures(self) -> list[dict]:
        """Parse test failure output."""
        content = self.results_file.read_text()
        
        # Extract FAILED tests
        failed_pattern = r"FAILED (.*?) - (.*)"
        matches = re.findall(failed_pattern, content)
        
        for test_path, error in matches:
            self.failures.append({
                'test': test_path,
                'error': error,
                'category': self._categorize_error(error),
            })
        
        return self.failures
    
    def _categorize_error(self, error: str) -> str:
        """Categorize error type."""
        if "AssertionError" in error:
            return "assertion"
        elif "AttributeError" in error:
            return "attribute"
        elif "TypeError" in error:
            return "type"
        elif "asyncio" in error.lower():
            return "async"
        elif "database" in error.lower():
            return "database"
        else:
            return "other"
    
    def generate_report(self) -> str:
        """Generate failure analysis report."""
        categories = Counter(f['category'] for f in self.failures)
        
        report = f"""
# Test Failure Analysis

**Total Failures:** {len(self.failures)}

## Failures by Category
"""
        for category, count in categories.most_common():
            report += f"- {category}: {count}\n"
        
        report += "\n## Detailed Failures\n"
        for failure in self.failures:
            report += f"\n### {failure['test']}\n"
            report += f"- Category: {failure['category']}\n"
            report += f"- Error: {failure['error']}\n"
        
        return report


if __name__ == '__main__':
    analyzer = TestFailureAnalyzer()
    failures = analyzer.parse_failures()
    report = analyzer.generate_report()
    
    Path('test_failure_report.md').write_text(report)
    print(f"Found {len(failures)} failures")
```

### Step 2: Fix Common Issues

**Async Test Issues:**
```python
# ❌ Wrong
def test_async_function():
    result = async_function()  # Returns coroutine

# ✅ Correct
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
```

**Database Cleanup Issues:**
```python
# ✅ Proper cleanup
@pytest.fixture
async def db_session():
    async with async_session() as session:
        yield session
        await session.rollback()  # Clean up
```

**Flaky Test Fixes:**
```python
# ❌ Flaky - timing dependent
def test_with_sleep():
    time.sleep(0.1)
    assert condition

# ✅ Stable - proper waiting
async def test_with_wait():
    await asyncio.wait_for(condition_met(), timeout=5.0)
```

### Step 3: Verify Fixes

```bash
# Run tests multiple times to verify stability
for i in {1..10}; do
    echo "Run $i"
    pytest || exit 1
done
```

---

## ✅ DEFINITION OF DONE

- [ ] All test failures identified
- [ ] All failures categorized
- [ ] All tests fixed
- [ ] 100% pass rate achieved
- [ ] No flaky tests
- [ ] Fixes documented

---

## 📊 SUCCESS METRICS

- Test pass rate: 100%
- Flaky tests: 0
- Test stability: 10/10 runs pass

---

**Estimated Completion:** 8 hours  
**Status:** NOT STARTED

