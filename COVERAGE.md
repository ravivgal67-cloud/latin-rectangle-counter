# Code Coverage Report

## Overview

Current overall coverage: **94%** 🎉 (improved from 83% → 85% → 94%)

## Coverage by Module

### Core Module (92-100%)
- ✅ `core/counter.py`: **100%** - All counting logic fully tested
- ✅ `core/formatting.py`: **100%** - All formatting functions tested
- ✅ `core/permutation.py`: **100%** - All permutation operations tested
- ✅ `core/validation.py`: **100%** - All validation logic fully tested
- ✅ `core/latin_rectangle.py`: **100%** - All rectangle operations fully tested
- ⚠️ `core/progress.py`: **92%** - Progress tracking mostly tested (4 lines missing)

### Cache Module (96%)
- ✅ `cache/cache_manager.py`: **96%** - Cache operations well tested (3 lines missing)

### Web Module (83%)
- ✅ `web/app.py`: **83%** ⬆️ - Most endpoints tested (32 lines missing)
  - Tested: `/api/count`, `/api/cache`, `/api/progress`, `/api/cache/results`, `/api/count/stream`
  - Tested: Error handlers, frontend routes, streaming endpoint
  - Remaining: Some error paths and edge cases in streaming

## Running Coverage

### Quick Start
```bash
# Run tests with coverage (configured by default)
pytest

# View HTML report
./view_coverage.sh
# or manually:
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Custom Coverage Commands
```bash
# Run with terminal report
pytest --cov-report=term-missing

# Generate only HTML report
pytest --cov-report=html --no-cov-on-fail

# Check specific module
pytest --cov=core tests/test_counter.py
```

## Coverage Configuration

Coverage is configured in:
- `pytest.ini` - pytest-cov integration
- `.coveragerc` - detailed coverage settings

### What's Excluded
- Test files (`*/tests/*`)
- Virtual environment (`*/venv/*`)
- Cache files (`*/__pycache__/*`)
- Abstract methods and type checking blocks

## Improving Coverage

### Priority Areas
1. **Web streaming endpoint** (`/api/count/stream`) - 0% coverage
   - Add tests for Server-Sent Events
   - Test streaming progress updates
   
2. **Error handlers** in `web/app.py`
   - Test 400/500 error responses
   - Test exception handling

3. **Edge cases** in validation and progress tracking
   - Cover remaining validation branches
   - Test progress callback edge cases

### Non-Critical
- Static file serving (framework-level functionality)
- Frontend route (`/`) - integration test territory
- Some error paths that are difficult to trigger in unit tests

## Coverage Goals

- **Current**: 94% 🎉
- **Target**: ✅ Exceeded! (was 90%+)
- **Core modules**: ✅ Achieved! 5 of 6 modules at 100%
- **Web module**: ✅ Achieved! 83% (exceeded 75% target)

## Notes

- Property-based tests (using Hypothesis) provide excellent coverage across many input combinations
- High coverage in core modules reflects the mathematical nature of the code
- Web module coverage is lower due to integration-heavy code (streaming, SSE, etc.)
