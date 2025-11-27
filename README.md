# Latin Rectangle Counter

A web-based application that counts positive (even) and negative (odd) normalized Latin rectangles for specified dimensions.

## Project Structure

```
.
├── core/           # Core counting engine (generators, counters, sign computation)
├── cache/          # Cache layer for storing computed results (SQLite)
├── web/            # Web interface layer (Flask API and frontend)
├── tests/          # Test suite (unit tests and property-based tests)
├── requirements.txt
└── README.md
```

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage report:
```bash
pytest --cov=core --cov=cache --cov=web --cov-report=term-missing --cov-report=html
```

Or simply run `pytest` (coverage is configured by default in `pytest.ini`).

View detailed HTML coverage report:
```bash
open htmlcov/index.html  # On macOS
# or
xdg-open htmlcov/index.html  # On Linux
```

Current coverage: **94%** overall 🎉 (improved from 83% → 85% → 94%)
- `core/`: Excellent coverage (92-100%) - 5 modules at 100%!
- `cache/`: 96% coverage
- `web/`: 83% coverage - all major endpoints tested!

See [COVERAGE.md](COVERAGE.md) for detailed coverage report.

## Running the Application

```bash
python -m flask --app web.app run
```

Or alternatively:
```bash
flask --app web.app run
```
