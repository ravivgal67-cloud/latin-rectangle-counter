# Latin Rectangle Counter 🔢

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-171%20passed-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)](htmlcov/index.html)

A high-performance web application for counting and analyzing normalized Latin rectangles, featuring a comprehensive optimization stack with up to **2x speedup** and resumable computation capabilities.

## ✨ Features

- **Ultra-Fast Computation**: Multi-layer optimization stack with up to **2x speedup** for large problems
- **Resumable Computation**: Counter-based checkpointing enables interruption and resumption of long-running computations
- **Advanced Optimizations**: Bitset constraints, lexicographic generation, and batch operations
- **Smart Caching**: SQLite-based caching with computation time tracking
- **Dual Views**: 
  - **Calculate**: Compute new results with real-time progress tracking
  - **Results**: Browse and filter cached computations
- **Property-Based Testing**: 171 tests with 94% coverage using Hypothesis
- **Performance Insights**: Track computation time and timestamps for all results

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ravivgal67-cloud/latin-rectangle-counter.git
cd latin-rectangle-counter
```

2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python -m flask --app web.app run --port 5001
```

5. **Open your browser**
```
http://localhost:5001
```

## 📊 What are Latin Rectangles?

A **Latin rectangle** is an r×n array where:
- Each row is a permutation of {1, 2, ..., n}
- No column contains duplicate values

A **normalized** Latin rectangle has its first row as the identity permutation [1, 2, 3, ..., n].

Each rectangle has a **sign** (±1) based on the parity of its row permutations:
- **Positive (+1)**: Even number of inversions
- **Negative (-1)**: Odd number of inversions

## 🏆 Optimization Achievements

This project demonstrates systematic performance optimization through multiple complementary approaches:

### **🔬 Methodology**
1. **Profiling-Driven**: Identified bottlenecks through systematic profiling
2. **Incremental Optimization**: Layered optimizations building on each other
3. **Correctness-First**: 100% correctness maintained throughout optimization
4. **Comprehensive Testing**: Each optimization thoroughly tested and documented

### **📈 Results Summary**
- **2.04x speedup** for (4,7) - most significant improvement
- **1.59x-1.72x speedup** across n=7 problems  
- **9+ minutes saved** for large computations
- **Zero correctness regressions** - all optimizations maintain identical results

### **🛠️ Technical Innovations**
- **Bitset Constraints**: Revolutionary O(1) constraint checking using integer bitsets
- **Lexicographic Generation**: Eliminates expensive sorting through direct ordered generation
- **Batch Operations**: Reduces function call overhead through intelligent batching
- **Resumable Architecture**: Counter-based deterministic generation enables precise checkpointing

This optimization work makes previously impractical computations (n≥7) feasible for mathematical research.

## 🎯 Usage Examples

### Calculate View
- **Single pair**: Compute (r, n) for specific dimensions
- **All for n**: Compute all r from 2 to n
- **Range**: Compute all combinations for n in a range

### Results View
- Browse all cached computations
- Filter by dimensions
- Sort by any column
- View computation time and timestamps

## 🏗️ Project Structure

```
.
├── core/              # Core counting engine
│   ├── counter.py     # Main counting algorithms
│   ├── latin_rectangle.py # Rectangle generation with optimizations
│   ├── bitset_constraints.py # Bitset constraint optimization
│   ├── permutation.py # Permutation utilities & optimization
│   └── validation.py
├── cache/             # SQLite caching layer
│   └── cache_manager.py
├── web/               # Flask web application
│   ├── app.py         # API endpoints
│   ├── templates/     # HTML templates
│   └── static/        # CSS & JavaScript
├── tests/             # Comprehensive test suite
├── scripts/           # Helper scripts
│   ├── benchmark_optimization.py
│   ├── monitor_progress.py
│   └── README.md
└── .kiro/specs/       # Feature specifications
```

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=. --cov-report=html
```

### View coverage report
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test Statistics
- **171 tests** - All passing ✅
- **94% coverage** - Excellent coverage across all modules
- **Property-based tests** - Using Hypothesis for robust validation
- **Optimization tests** - Comprehensive coverage of all optimization layers

## ⚡ Performance

### Multi-Layer Optimization Stack

Our comprehensive optimization approach delivers substantial performance improvements:

#### **🚀 Optimization Layers**
1. **Counter-Based Generation**: Deterministic ordering + resumable computation
2. **Bitset Constraints**: O(1) constraint operations using integer bitsets  
3. **Lexicographic Generation**: Direct sorted order (eliminates sorting overhead)
4. **Batch Operations**: Reduced function call overhead

#### **📊 Performance Results**

| Problem | Original | Fully Optimized | Total Speedup | Time Saved |
|---------|----------|-----------------|---------------|-------------|
| **(3,7)** | 210,000 rect/s | **333,188 rect/s** | **1.59x** | Significant |
| **(4,7)** | 144,988 rect/s | **295,482 rect/s** | **2.04x** | ~9 minutes |
| **(5,7)** | 147,000 rect/s | **252,132 rect/s** | **1.72x** | Substantial |

#### **🎯 Real-World Impact**

**Problem (4,7)** - 155,185,920 rectangles:
- **Before**: ~18 minutes computation time
- **After**: ~9 minutes computation time  
- **Improvement**: 2x faster, saves 9 minutes

#### **🔧 Legacy Optimizations**

Previous constraint propagation optimization for high-constraint cases:

| Dimension | Naive Time | Optimized Time | Speedup |
|-----------|------------|----------------|---------|
| (5,5) | 49ms | 33ms | **1.5x** |
| (6,6) | >180s | ~50ms | **>3600x** |

**Key insight**: Most effective when **r ≥ n/2** (constraint density ≥ 50%)

See detailed analysis in our optimization documentation below.

## 📚 Documentation

### Core Documentation
- **[README.md](README.md)** - This file, project overview and quick start
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contributor guidelines, setup, and code style

### Technical Documentation
- **[docs/BITSET_OPTIMIZATION.md](docs/BITSET_OPTIMIZATION.md)** - Bitset constraint optimization (1.5x speedup)
- **[docs/PERMUTATION_OPTIMIZATION.md](docs/PERMUTATION_OPTIMIZATION.md)** - Lexicographic generation optimization (1.24x speedup)
- **[docs/BATCH_CONSTRAINTS_OPTIMIZATION.md](docs/BATCH_CONSTRAINTS_OPTIMIZATION.md)** - Batch operations optimization (1.07x speedup)
- **[docs/OPTIMIZATION.md](docs/OPTIMIZATION.md)** - Legacy constraint propagation optimization analysis
- **[docs/RESUMABLE_COMPUTATION.md](docs/RESUMABLE_COMPUTATION.md)** - Resumable computation with checkpointing
- **[docs/COVERAGE.md](docs/COVERAGE.md)** - Test coverage report and gap analysis

### Specifications
- **[Design Document](.kiro/specs/latin-rectangle-counter/design.md)** - Architecture, algorithms, and correctness properties
- **[Requirements](.kiro/specs/latin-rectangle-counter/requirements.md)** - Feature specifications and acceptance criteria
- **[Tasks](.kiro/specs/latin-rectangle-counter/tasks.md)** - Implementation plan and task list

### Helper Scripts
- **[scripts/README.md](scripts/README.md)** - Documentation for all helper scripts

## 🛠️ Development

### Helper Scripts

```bash
# Benchmark optimization
python scripts/benchmark_optimization.py

# Monitor progress
python scripts/monitor_progress.py

# View coverage
bash scripts/view_coverage.sh
```

See [scripts/README.md](scripts/README.md) for all available scripts.

### Code Quality

- **Type hints** throughout the codebase
- **Docstrings** with examples
- **Property-based testing** with Hypothesis
- **94% test coverage**
- **Clean architecture** with clear separation of concerns

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Tested with [Hypothesis](https://hypothesis.readthedocs.io/)
- Inspired by combinatorial mathematics and Latin square theory
- Performance optimization techniques inspired by systems programming and algorithmic optimization

## 📧 Contact

Raviv - [@ravivgal67-cloud](https://github.com/ravivgal67-cloud)

Project Link: [https://github.com/ravivgal67-cloud/latin-rectangle-counter](https://github.com/ravivgal67-cloud/latin-rectangle-counter)

---

⭐ Star this repo if you find it helpful!
