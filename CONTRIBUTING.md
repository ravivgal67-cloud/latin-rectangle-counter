# Contributing to Latin Rectangle Counter

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🚀 Getting Started

### Development Environment Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/latin-rectangle-counter.git
cd latin-rectangle-counter
```

2. **Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Verify installation**
```bash
pytest  # Should pass all 141 tests
```

## 🧪 Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_counter.py -v
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html  # View detailed report
```

### Run property-based tests with more examples
```bash
pytest tests/test_optimization.py --hypothesis-show-statistics
```

### Quick coverage check
```bash
bash scripts/coverage_summary.sh
```

## 🏃 Running the Application

### Development server
```bash
python -m flask --app web.app run --port 5001
```

### Access the application
```
http://localhost:5001
```

### Monitor progress (when web UI unavailable)
```bash
python scripts/monitor_progress.py
```

## 📝 Code Style Guidelines

### Python Code Style

We follow **PEP 8** with some project-specific conventions:

#### General Principles
- **Clear over clever**: Prioritize readability
- **Type hints**: Use type hints for all function signatures
- **Docstrings**: All public functions must have docstrings with examples
- **Comments**: Explain *why*, not *what*

#### Naming Conventions
```python
# Functions and variables: snake_case
def count_rectangles(r: int, n: int) -> CountResult:
    positive_count = 0
    
# Classes: PascalCase
class LatinRectangle:
    pass
    
# Constants: UPPER_SNAKE_CASE
MAX_DIMENSION = 10
```

#### Docstring Format
```python
def function_name(arg1: Type1, arg2: Type2) -> ReturnType:
    """
    Brief description of what the function does.
    
    More detailed explanation if needed. Explain the algorithm,
    mathematical background, or important implementation details.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Examples:
        >>> function_name(value1, value2)
        expected_result
    """
```

#### Import Organization
```python
# Standard library
import time
from typing import List, Optional

# Third-party
from flask import Flask, jsonify

# Local
from core.counter import count_rectangles
from cache.cache_manager import CacheManager
```

### JavaScript Code Style

#### General Principles
- **ES6+ syntax**: Use modern JavaScript features
- **Const by default**: Use `const` unless reassignment needed
- **Descriptive names**: Clear, self-documenting variable names
- **Comments**: Explain complex logic

#### Naming Conventions
```javascript
// Functions and variables: camelCase
function formatNumber(num) {
    const formattedValue = num.toString();
    return formattedValue;
}

// Constants: UPPER_SNAKE_CASE
const API_BASE_URL = window.location.origin;

// Classes: PascalCase (if used)
class ResultsManager {
    constructor() {}
}
```

### HTML/CSS Style

- **Semantic HTML**: Use appropriate tags (`<section>`, `<article>`, etc.)
- **BEM-like naming**: Use descriptive class names (`.results-table`, `.calc-card`)
- **Accessibility**: Include ARIA labels where appropriate
- **Responsive**: Mobile-friendly design

## 🔧 Development Workflow

### Before Starting Work

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Check current test status**
```bash
pytest
```

### During Development

1. **Write tests first** (TDD approach recommended)
```bash
# Create test file
touch tests/test_your_feature.py

# Write failing tests
# Implement feature
# Make tests pass
```

2. **Run tests frequently**
```bash
pytest tests/test_your_feature.py -v
```

3. **Check coverage**
```bash
pytest --cov=. --cov-report=term-missing
```

### Before Committing

1. **Run all tests**
```bash
pytest
```

2. **Check coverage** (should maintain ≥94%)
```bash
pytest --cov=. --cov-report=html
```

3. **Verify no regressions**
```bash
python scripts/benchmark_optimization.py
```

4. **Test the web UI manually**
```bash
python -m flask --app web.app run --port 5001
# Test in browser
```

### Commit Guidelines

#### Commit Message Format
```
<type>: <subject>

<body>

<footer>
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `style`: Code style changes (formatting, etc.)
- `chore`: Maintenance tasks

#### Examples
```bash
# Good commit messages
git commit -m "feat: Add constraint propagation optimization

- Implement forced move detection
- Add early conflict detection
- Achieve 1.5x-3600x speedup for high-constraint cases"

git commit -m "fix: Correct timezone handling in date display

- SQLite stores UTC, JavaScript now converts to local time
- Add 'Z' suffix to indicate UTC timestamps"

git commit -m "test: Add property tests for optimization correctness

- Verify optimization produces same results as naive approach
- Test forced moves, early pruning, and conflict detection"
```

## 🧪 Testing Guidelines

### Test Organization

- **Unit tests**: Test individual functions in isolation
- **Property tests**: Test universal properties across many inputs
- **Integration tests**: Test complete workflows

### Property-Based Testing

We use **Hypothesis** for property-based testing:

```python
from hypothesis import given, strategies as st, settings

@given(st.integers(min_value=2, max_value=10))
@settings(max_examples=100)
def test_property(n):
    """Test that property holds for all valid n."""
    result = function_under_test(n)
    assert property_holds(result)
```

### Test Naming
```python
# Unit tests
def test_function_name_specific_case():
    """Test specific behavior."""
    
# Property tests
def test_property_name():
    """
    **Feature: feature-name, Property X: Property description**
    **Validates: Requirements X.Y**
    """
```

### Coverage Goals

- **Overall**: ≥94%
- **Core modules**: ≥95%
- **New features**: ≥90%

## 🐛 Reporting Issues

### Bug Reports

Include:
1. **Description**: What happened vs what you expected
2. **Steps to reproduce**: Minimal example
3. **Environment**: Python version, OS
4. **Error messages**: Full traceback if applicable

### Feature Requests

Include:
1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Other approaches considered

## 📚 Documentation

### Code Documentation

- **All public functions**: Must have docstrings with examples
- **Complex algorithms**: Explain the approach and complexity
- **Mathematical concepts**: Reference papers or provide background

### Project Documentation

When adding features, update:
- `README.md` - If user-facing
- `.kiro/specs/*/design.md` - If architectural
- `scripts/README.md` - If adding helper scripts

## 🎯 Areas for Contribution

### High Priority

1. **Performance optimizations**: Further algorithm improvements
2. **Additional properties**: More correctness properties and tests
3. **UI enhancements**: Better visualization, export features
4. **Documentation**: More examples, tutorials

### Good First Issues

1. **Add more unit tests**: Increase coverage to 95%+
2. **Improve error messages**: More helpful validation errors
3. **Add keyboard shortcuts**: Better UX
4. **Add favicon**: Professional touch

### Advanced

1. **Parallel computation**: Multi-threaded counting
2. **Visualization**: Display Latin rectangles graphically
3. **API extensions**: REST API for programmatic access
4. **Algorithm research**: New optimization techniques

## ✅ Pull Request Process

1. **Create feature branch** from `main`
2. **Make changes** following code style guidelines
3. **Add tests** for new functionality
4. **Run full test suite** - all tests must pass
5. **Update documentation** as needed
6. **Commit with clear messages**
7. **Push to your fork**
8. **Open Pull Request** with description of changes

### PR Checklist

- [ ] All tests pass (`pytest`)
- [ ] Coverage maintained or improved (≥94%)
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No unnecessary files committed

## 💡 Tips

- **Start small**: Begin with small, focused changes
- **Ask questions**: Open an issue if unsure about approach
- **Test thoroughly**: Property-based tests catch edge cases
- **Read the specs**: Check `.kiro/specs/` for design decisions
- **Benchmark changes**: Use `scripts/benchmark_optimization.py` for performance changes

## 📞 Getting Help

- **Open an issue**: For questions or discussions
- **Check documentation**: See `.kiro/specs/` for design details
- **Review tests**: Tests serve as usage examples

## 🙏 Thank You!

Every contribution helps make this project better. Whether it's fixing a typo, adding tests, or implementing new features - all contributions are valued and appreciated!

Happy coding! 🎉
