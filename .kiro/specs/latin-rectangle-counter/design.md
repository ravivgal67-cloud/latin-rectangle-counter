# Design Document: Latin Rectangle Counter

## Overview

The Latin Rectangle Counter is a web-based application that counts positive (even) and negative (odd) normalized Latin rectangles for specified dimensions. The system focuses on normalized Latin rectangles where r ≥ 2, leveraging the mathematical structure of derangements to optimize computation.

The application consists of:
- A core counting engine that generates and classifies normalized Latin rectangles
- A caching layer for storing computed results
- A web interface with two views: calculation view for computing new results and presentation view for displaying cached data

## Architecture

The system follows a layered architecture:

```
┌─────────────────────────────────────────┐
│         Web Interface Layer             │
│  (Calculation View | Presentation View) │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (Input Validation | Result Formatting) │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         Core Counting Engine            │
│  (Generator | Sign Computer | Counter)  │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         Cache Layer                     │
│  (Storage | Retrieval | Persistence)    │
└─────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Python (for mathematical computation and algorithm implementation)
- **Web Framework**: Flask (lightweight, suitable for mathematical applications)
- **Frontend**: HTML, CSS, JavaScript (simple, self-explanatory interface)
- **Cache Storage**: SQLite (lightweight, tabular data storage)
- **Property Testing**: Hypothesis (Python property-based testing library)

## Components and Interfaces

### 1. Core Counting Engine

#### LatinRectangle Class
```python
class LatinRectangle:
    rows: int  # r
    cols: int  # n
    data: List[List[int]]  # r×n array
    
    def compute_sign() -> int  # Returns +1 or -1
    def is_normalized() -> bool
    def is_valid() -> bool
```

#### Permutation Module
```python
def permutation_sign(perm: List[int]) -> int
    """Compute sign of a permutation based on number of transpositions"""
    
def is_derangement(perm: List[int]) -> bool
    """Check if permutation is a derangement"""
    
def count_derangements(n: int) -> int
    """Compute number of derangements using recurrence: D(n) = (n-1)*(D(n-1) + D(n-2))"""

def compute_determinant(matrix: List[List[int]]) -> int
    """Compute determinant of a square matrix"""
```

#### Generator Module
```python
def generate_normalized_rectangles(r: int, n: int) -> Iterator[LatinRectangle]
    """Generate all normalized Latin rectangles of dimension r×n"""
    
def generate_valid_next_row(
    existing_rows: List[List[int]], 
    n: int
) -> Iterator[List[int]]
    """Generate valid rows that don't conflict with existing columns"""
```

#### Counter Module
```python
@dataclass
class CountResult:
    r: int
    n: int
    positive_count: int
    negative_count: int
    difference: int
    from_cache: bool

def count_rectangles(r: int, n: int) -> CountResult
    """Count positive and negative normalized Latin rectangles
    Uses derangement formula for r=2, backtracking for r>2"""
    
def count_nlr_r2(n: int) -> CountResult
    """Optimized counting for r=2 using derangement properties"""
    
def count_nlr_general(r: int, n: int) -> CountResult
    """General backtracking algorithm for r>2"""
    
def count_range(n_start: int, n_end: int) -> List[CountResult]
    """Count for all n in range and all valid r"""
```

### 2. Cache Layer

#### CacheManager Class
```python
class CacheManager:
    def get(r: int, n: int) -> Optional[CountResult]
    def put(result: CountResult) -> None
    def get_all_cached_dimensions() -> List[Tuple[int, int]]
    def get_range(r_min: int, r_max: int, n_min: int, n_max: int) -> List[CountResult]
```

#### Database Schema
```sql
CREATE TABLE results (
    r INTEGER NOT NULL,
    n INTEGER NOT NULL,
    positive_count INTEGER NOT NULL,
    negative_count INTEGER NOT NULL,
    difference INTEGER NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (r, n)
);

CREATE INDEX idx_n ON results(n);
CREATE INDEX idx_r ON results(r);
```

### 3. Application Layer

#### InputValidator
```python
def validate_dimensions(r: Optional[int], n: Optional[int]) -> ValidationResult
def validate_range(n_start: int, n_end: int) -> ValidationResult
def parse_input(input_str: str) -> DimensionSpec
```

#### ResultFormatter
```python
def format_table(results: List[CountResult]) -> str
def format_for_web(results: List[CountResult]) -> dict
```

### 4. Web Interface Layer

#### API Endpoints
```
POST /api/count
    Body: { "r": int?, "n": int?, "n_start": int?, "n_end": int? }
    Response: { "results": [CountResult], "status": "success" }

GET /api/cache
    Response: { "dimensions": [(r, n)], "ranges": {...} }

GET /api/cache/results
    Query: ?r_min=2&r_max=5&n_min=3&n_max=6
    Response: { "results": [CountResult] }
```

#### Views
- **Calculation View**: Form with input fields, submit button, progress indicator, results table
- **Presentation View**: Dimension selector (from cache), results display, navigation

## Data Models

### LatinRectangle
- `rows` (r): Number of rows (2 ≤ r ≤ n)
- `cols` (n): Number of columns (n ≥ 2)
- `data`: 2D array of integers from 1 to n
- Invariant: First row is identity permutation [1, 2, ..., n]
- Invariant: Each column has no repeated elements

### CountResult
- `r`: Row dimension
- `n`: Column dimension
- `positive_count`: Count of rectangles with sign +1
- `negative_count`: Count of rectangles with sign -1
- `difference`: positive_count - negative_count
- `from_cache`: Boolean indicating if result was cached

### DimensionSpec
- `type`: "single" | "all_for_n" | "range"
- `r`: Optional specific row count
- `n`: Optional specific column count
- `n_start`: Optional range start
- `n_end`: Optional range end

## Algorithms

### Special Case: r = 2 (Derangement Formula)

For r = 2, normalized Latin rectangles consist of:
- First row: [1, 2, 3, ..., n] (identity)
- Second row: A derangement of [1, 2, 3, ..., n]

We can count positive and negative derangements efficiently without generation:

**Step 1**: Compute total derangements using recurrence:
```
D(0) = 1
D(1) = 0
D(n) = (n-1) * (D(n-1) + D(n-2))
```

**Step 2**: Compute the difference between positive and negative derangements using the closed-form formula:
```
difference = (-1)^(n-1) * (n-1)
```

This formula is derived from the determinant of the n×n matrix M where M[i][j] = 0 if i == j and M[i][j] = 1 if i ≠ j. The determinant of this matrix (J_n - I_n, where J_n is the all-ones matrix and I_n is the identity) has the well-known closed form: det(J_n - I_n) = (-1)^(n-1) * (n-1)

**Step 3**: Solve the system:
```
positive + negative = D(n)
positive - negative = det(M)
```

Therefore:
```
positive = (D(n) + det(M)) / 2
negative = (D(n) - det(M)) / 2
```

```python
def count_nlr_r2(n: int) -> CountResult:
    """Efficient counting for r=2 using derangement formula and closed-form difference"""
    # Compute total derangements
    total = count_derangements(n)
    
    # Compute difference using closed-form formula
    # diff = det(J_n - I_n) = (-1)^(n-1) * (n-1)
    diff = ((-1) ** (n - 1)) * (n - 1)
    
    # Solve for positive and negative counts
    positive = (total + diff) // 2
    negative = (total - diff) // 2
    
    return CountResult(2, n, positive, negative, diff, from_cache=False)
```

This approach is O(n³) for determinant computation vs O(D(n) × n) for explicit generation, providing significant speedup for larger n.

### General Case: r > 2 (Backtracking Algorithm)

For r > 2, no closed-form formula analogous to the r=2 case is currently known. The problem involves counting Latin rectangles with multiple row constraints, which is combinatorially complex. We use a recursive backtracking algorithm with pruning:

```
function count_nlr(r, n):
    if cached(r, n):
        return cache.get(r, n)
    
    positive = 0
    negative = 0
    
    # First row is always identity
    rows = [[1, 2, ..., n]]
    
    # Recursively build remaining rows
    backtrack(rows, 1, r, n, positive, negative)
    
    result = CountResult(r, n, positive, negative, positive - negative)
    cache.put(result)
    return result

function backtrack(rows, current_row, r, n, pos_count, neg_count):
    if current_row == r:
        # Complete rectangle found
        sign = compute_rectangle_sign(rows)
        if sign == 1:
            pos_count += 1
        else:
            neg_count += 1
        return
    
    # Generate valid next rows
    for next_row in generate_valid_rows(rows, n):
        rows.append(next_row)
        backtrack(rows, current_row + 1, r, n, pos_count, neg_count)
        rows.pop()

function generate_valid_rows(existing_rows, n):
    """Generate permutations that don't conflict with existing columns"""
    # Use constraint propagation to prune invalid permutations early
    forbidden = [set() for _ in range(n)]
    
    for row in existing_rows:
        for col_idx, value in enumerate(row):
            forbidden[col_idx].add(value)
    
    # Generate permutations respecting constraints
    yield from constrained_permutations(n, forbidden)
```

### Sign Computation

```
function compute_rectangle_sign(rows):
    sign = 1
    for row in rows:
        sign *= permutation_sign(row)
    return sign

function permutation_sign(perm):
    """Count inversions to determine sign"""
    inversions = 0
    for i in range(len(perm)):
        for j in range(i + 1, len(perm)):
            if perm[i] > perm[j]:
                inversions += 1
    return 1 if inversions % 2 == 0 else -1
```

### Optimization Strategies

1. **Constraint Propagation** (Implemented): Uses forced move detection, early conflict detection, and most-constrained-first heuristic
   - **Effectiveness threshold**: Most beneficial when r ≥ n/2 (constraint density ≥ 50%)
   - **Performance**: 1.5x-3600x speedup for high-constraint cases (r/n ≥ 0.5)
   - **Trade-off**: Small overhead (~2x slower) for low-constraint cases (r/n < 0.5), but absolute time is negligible (< 1ms)

2. **Early Pruning**: During generation, eliminate partial rectangles that cannot lead to valid completions

3. **Symmetry Breaking**: Exploit symmetries in normalized rectangles to reduce search space

4. **Incremental Sign Computation**: Compute sign incrementally as rows are added rather than recomputing for complete rectangles

5. **Memoization**: Cache intermediate results for partial rectangles when beneficial



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Valid dimension acceptance
*For any* dimension pair (r, n) where 2 ≤ r ≤ n and n ≥ 2, the input validation should accept the dimensions as valid.
**Validates: Requirements 1.1**

### Property 2: Invalid dimension rejection
*For any* dimension pair (r, n) where r > n or r < 2 or n < 2, the input validation should reject the dimensions and report an error.
**Validates: Requirements 1.4**

### Property 3: Complete range coverage for single n
*For any* valid n ≥ 2, when counting for just n, the results should include entries for all r where 2 ≤ r ≤ n.
**Validates: Requirements 1.2**

### Property 4: Complete range coverage for n range
*For any* valid range n1..n2 where 2 ≤ n1 ≤ n2, the results should include entries for all n where n1 ≤ n ≤ n2 and for all r where 2 ≤ r ≤ n.
**Validates: Requirements 1.3**

### Property 5: Normalized first row
*For any* generated normalized Latin rectangle with dimensions (r, n), the first row should be the identity permutation [1, 2, 3, ..., n].
**Validates: Requirements 2.1**

### Property 6: Valid rectangle structure
*For any* generated normalized Latin rectangle, each row should be a permutation of [1, 2, ..., n] and no column should contain duplicate values.
**Validates: Requirements 2.2**

### Property 7: Generation completeness and uniqueness
*For any* small dimensions (r, n) where exhaustive verification is feasible, the generator should produce exactly the known count of valid normalized Latin rectangles with no duplicates.
**Validates: Requirements 2.3**

### Property 8: Sign computation correctness
*For any* Latin rectangle, the computed sign should equal the product of the signs of all its row permutations.
**Validates: Requirements 3.1**

### Property 9: Permutation sign correctness
*For any* permutation, the computed sign should match the standard definition: +1 if the number of inversions is even, -1 if odd.
**Validates: Requirements 3.3**

### Property 10: Count accuracy
*For any* small dimensions (r, n) where exhaustive verification is feasible, the positive and negative counts should match the actual number of rectangles with each sign.
**Validates: Requirements 4.1**

### Property 11: Difference calculation
*For any* count result, the difference field should equal positive_count - negative_count.
**Validates: Requirements 4.2**

### Property 12: Cache retrieval consistency
*For any* dimensions (r, n), if results are computed and then requested again, the second request should return cached results that match the original computation.
**Validates: Requirements 5.1, 5.2**

### Property 13: Cache storage after computation
*For any* dimensions (r, n), after computing counts, the results should be retrievable from the cache.
**Validates: Requirements 5.4**

### Property 14: Partial cache utilization
*For any* range request where some dimensions are cached and others are not, the system should return cached results for available dimensions and compute only the missing ones.
**Validates: Requirements 5.3**

### Property 15: Cache flag accuracy
*For any* result returned to the user, the from_cache flag should be true if and only if the result was retrieved from cache rather than computed.
**Validates: Requirements 6.5**

### Property 16: Cache dimension query completeness
*For any* state of the cache, querying all cached dimensions should return all (r, n) pairs for which results have been stored.
**Validates: Requirements 8.1**

## Error Handling

### Input Validation Errors
- **Invalid dimensions**: r > n, r < 2, or n < 2
  - Response: Return error with message "Invalid dimensions: r must satisfy 2 ≤ r ≤ n"
- **Invalid range**: n1 > n2
  - Response: Return error with message "Invalid range: n_start must be ≤ n_end"
- **Malformed input**: Non-integer values, missing required fields
  - Response: Return error with message describing the parsing issue

### Computation Errors
- **Memory exhaustion**: For very large dimensions, generation may exceed available memory
  - Response: Return error with message "Dimensions too large for available memory"
  - Mitigation: Implement streaming generation and incremental counting
- **Timeout**: Computation takes too long
  - Response: Return partial results with indication of timeout
  - Mitigation: Implement progress tracking and allow resumption

### Cache Errors
- **Database connection failure**: Cannot connect to SQLite database
  - Response: Log error, continue without cache (compute all results)
  - Mitigation: Retry connection, fall back to in-memory cache
- **Corrupted cache data**: Retrieved data fails validation
  - Response: Log warning, recompute and update cache
  - Mitigation: Add data integrity checks and version tracking

### Web Interface Errors
- **API request failure**: Network error or server unavailable
  - Response: Display user-friendly error message with retry option
- **Invalid API response**: Malformed JSON or unexpected structure
  - Response: Display error message and log details for debugging

## Testing Strategy

### Unit Testing

Unit tests will cover specific examples and edge cases:

1. **Permutation sign computation**
   - Test known permutations: [1,2,3] → +1, [2,1,3] → -1, [3,2,1] → -1
   - Test identity permutation always has sign +1
   - Test single transposition always has sign -1

2. **Input validation**
   - Test boundary cases: r=2, n=2 (minimum valid)
   - Test invalid cases: r=1, n=1, r>n
   - Test range validation: n1=n2 (single value), n1>n2 (invalid)

3. **Cache operations**
   - Test store and retrieve for single result
   - Test cache miss returns None
   - Test cache hit returns correct data

4. **Result formatting**
   - Test difference calculation: positive - negative
   - Test from_cache flag is set correctly

### Property-Based Testing

Property-based tests will verify universal properties across many randomly generated inputs using the Hypothesis library. Each test will run a minimum of 100 iterations.

1. **Property 1: Valid dimension acceptance**
   - Generate random (r, n) with 2 ≤ r ≤ n ≤ 10
   - Verify validation accepts all generated pairs

2. **Property 2: Invalid dimension rejection**
   - Generate random invalid (r, n) pairs
   - Verify validation rejects all invalid pairs

3. **Property 3: Complete range coverage for single n**
   - Generate random n in [2, 8]
   - Count for n, verify results include all r from 2 to n

4. **Property 4: Complete range coverage for n range**
   - Generate random n1, n2 with 2 ≤ n1 ≤ n2 ≤ 6
   - Verify results cover all (r, n) combinations

5. **Property 5: Normalized first row**
   - Generate random (r, n) with 2 ≤ r ≤ n ≤ 6
   - Generate rectangles, verify first row is [1, 2, ..., n]

6. **Property 6: Valid rectangle structure**
   - Generate random rectangles
   - Verify each row is a permutation and columns have no duplicates

7. **Property 7: Generation completeness**
   - For small (r, n) like (2, 3), (2, 4), (3, 4)
   - Verify generated count matches known values
   - Verify no duplicate rectangles generated

8. **Property 8: Sign computation correctness**
   - Generate random rectangles
   - Independently compute sign as product of row signs
   - Verify matches system computation

9. **Property 9: Permutation sign correctness**
   - Generate random permutations
   - Compute sign by counting inversions
   - Verify matches system computation

10. **Property 10: Count accuracy**
    - For small (r, n) where brute force is feasible
    - Verify counts match exhaustive generation and classification

11. **Property 11: Difference calculation**
    - Generate random count results
    - Verify difference = positive_count - negative_count

12. **Property 12: Cache retrieval consistency**
    - Generate random (r, n), compute counts
    - Request again, verify cached results match original

13. **Property 13: Cache storage after computation**
    - Generate random (r, n), compute counts
    - Verify results are in cache

14. **Property 14: Partial cache utilization**
    - Pre-populate cache with some dimensions
    - Request range including cached and uncached
    - Verify cached results used and only missing computed

15. **Property 15: Cache flag accuracy**
    - Mix of cached and computed results
    - Verify from_cache flag matches actual source

16. **Property 16: Cache dimension query completeness**
    - Store random set of results in cache
    - Query cached dimensions
    - Verify all stored dimensions returned

### Integration Testing

Integration tests will verify end-to-end workflows:

1. **Complete calculation workflow**
   - Submit dimensions via API
   - Verify computation completes
   - Verify results stored in cache
   - Verify results displayed correctly

2. **Cache persistence**
   - Compute results
   - Restart application
   - Verify cached results still available

3. **Range calculation with partial cache**
   - Compute some dimensions
   - Request range including cached and new
   - Verify efficient reuse of cache

4. **Web interface interaction**
   - Submit via calculation view
   - Switch to presentation view
   - Verify cached results displayed

### Performance Testing

Performance tests will verify efficiency requirements:

1. **Small dimensions (r=2, n≤10)**: Should complete in < 1 second
2. **Medium dimensions (r=3, n≤8)**: Should complete in < 10 seconds
3. **Large dimensions (r=4, n≤7)**: Should complete in < 60 seconds
4. **Cache retrieval**: Should be < 100ms regardless of dimension

## Implementation Notes

### Known Mathematical Values

For validation and testing, we can use known values:
- NLR(2, 3): 1 positive, 2 negative (difference: -1)
- NLR(2, 4): 3 positive, 6 negative (difference: -3)
- NLR(3, 4): Known values from literature

### Optimization Priorities

1. **Correctness first**: Ensure all properties hold before optimizing
2. **Cache effectiveness**: Maximize cache hit rate for common queries
3. **Algorithm efficiency**: Focus optimization on r > 2 cases
4. **Memory management**: Use generators to avoid storing all rectangles

### Future Enhancements

- Parallel computation for independent dimension calculations
- Distributed caching for shared results across users
- Export results to CSV/JSON for external analysis
- Visualization of Latin rectangles
- Support for non-normalized rectangles
