# Helper Scripts

This directory contains utility scripts for development, testing, and monitoring.

## Cache Management Scripts

### `generate_cache.py`
Generates optimized smart derangement cache files with pre-computed indices to eliminate initialization bottlenecks.

**Usage:**
```bash
# Generate all caches (n=2 through n=8)
python scripts/generate_cache.py

# Generate cache for specific n
python scripts/generate_cache.py --n 8

# Force regeneration with verification and benchmarking
python scripts/generate_cache.py --n 8 --force --verify --benchmark
```

**Options:**
- `--n N`: Generate cache for specific n (default: 2-8)
- `--force`: Force regeneration even if cache exists
- `--verify`: Verify cache integrity after generation
- `--benchmark`: Benchmark loading performance

**Purpose:** Pre-compute and store database indices and multi-prefix indices to speed up parallel process initialization.

## Benchmarking Scripts

### `benchmark_optimization.py`
Tests the optimized constraint propagation algorithm by comparing results with cached values and measuring performance.

**Usage:**
```bash
python scripts/benchmark_optimization.py
```

**Purpose:** Verify correctness and measure performance of the optimization.

### `benchmark_comparison.py`
Compares naive backtracking vs optimized constraint propagation performance.

**Usage:**
```bash
python scripts/benchmark_comparison.py
```

**Purpose:** Measure speedup and validate the r ≥ n/2 threshold rule.

### `test_threshold.py`
Tests the r ≥ n/2 threshold hypothesis for optimization effectiveness.

**Usage:**
```bash
python scripts/test_threshold.py
```

**Purpose:** Validate when optimization is beneficial based on constraint density.

## Progress Monitoring Scripts

### `monitor_progress.py`
Monitors computation progress by querying the database and displaying current status.

**Usage:**
```bash
python scripts/monitor_progress.py
```

**Purpose:** Check progress when web UI is unavailable (e.g., port 5000 blocked).

### `check_progress.py`
One-time check of current computation progress.

**Usage:**
```bash
python scripts/check_progress.py
```

**Purpose:** Quick status check without continuous monitoring.

### `watch_progress.py`
Continuously watches and displays computation progress with auto-refresh.

**Usage:**
```bash
python scripts/watch_progress.py
```

**Purpose:** Real-time monitoring of long-running computations.

## Coverage Scripts

### `coverage_summary.sh`
Generates and displays test coverage summary.

**Usage:**
```bash
bash scripts/coverage_summary.sh
```

**Purpose:** Quick coverage report without opening HTML.

### `view_coverage.sh`
Opens the HTML coverage report in the default browser.

**Usage:**
```bash
bash scripts/view_coverage.sh
```

**Purpose:** View detailed coverage report with line-by-line analysis.

## Notes

- All Python scripts should be run from the project root directory
- Scripts assume the virtual environment is activated
- Database scripts expect `latin_rectangles.db` in the project root
