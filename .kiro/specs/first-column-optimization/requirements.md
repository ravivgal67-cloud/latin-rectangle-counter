# Requirements Document

## Introduction

This specification defines the requirements for implementing first column optimization in the Latin rectangle enumeration algorithm. The optimization exploits the (r-1)! symmetry by fixing the first column and provides better parallelization through finer-grained work distribution.

## Glossary

- **First_Column**: The leftmost column of a Latin rectangle, containing elements [1, a, b, c, ...] where a,b,c are chosen from {2,3,...,n}
- **Column_Choice**: A specific selection of (r-1) values from {2,3,...,n} to fill positions 2 through r in the first column
- **Symmetry_Factor**: The value (r-1)! representing the number of equivalent normalized Latin rectangles for each first column choice
- **Work_Unit**: An independent computational task consisting of enumerating all rectangles with a fixed first column
- **Constraint_Propagation**: The process of reducing search space by applying known constraints early in the enumeration
- **Ultra_Safe_Bitwise**: The current enumeration algorithm using bitwise operations for constraint checking

## Requirements

### Requirement 1: First Column Enumeration

**User Story:** As a mathematician, I want to enumerate all possible first column configurations, so that I can parallelize computation across these configurations.

#### Acceptance Criteria

1. THE First_Column_Enumerator SHALL generate all combinations of (r-1) values from {2,3,...,n}
2. WHEN r=5 and n=8, THE First_Column_Enumerator SHALL produce exactly 35 column choices
3. THE First_Column_Enumerator SHALL maintain the first element as 1 (normalized form)
4. FOR ALL generated column choices, THE First_Column_Enumerator SHALL ensure no duplicate values within each column

### Requirement 2: Work Distribution

**User Story:** As a system administrator, I want to distribute first column choices across available threads, so that computation is parallelized efficiently.

#### Acceptance Criteria

1. THE Work_Distributor SHALL assign column choices to threads in round-robin fashion
2. WHEN 35 column choices are distributed across 8 threads, THE Work_Distributor SHALL assign 4-5 choices per thread
3. THE Work_Distributor SHALL ensure each thread receives approximately equal computational load
4. THE Work_Distributor SHALL maintain thread independence (no shared mutable state)

### Requirement 3: Constrained Rectangle Enumeration

**User Story:** As a computational mathematician, I want to enumerate rectangles with fixed first columns, so that I can exploit constraint propagation for faster computation.

#### Acceptance Criteria

1. THE Constrained_Enumerator SHALL generate all valid rectangles for a given first column choice
2. WHEN the first column is fixed, THE Constrained_Enumerator SHALL apply constraints to reduce second row possibilities by at least 80%
3. THE Constrained_Enumerator SHALL maintain compatibility with the Ultra_Safe_Bitwise algorithm
4. THE Constrained_Enumerator SHALL preserve sign calculations for accurate NLR counting

### Requirement 4: Symmetry Factor Application

**User Story:** As a mathematician, I want to apply the (r-1)! symmetry factor, so that I get the correct count of normalized Latin rectangles.

#### Acceptance Criteria

1. THE Symmetry_Calculator SHALL multiply rectangle counts by (r-1)! for each first column choice
2. WHEN r=5, THE Symmetry_Calculator SHALL apply a factor of 24 to each rectangle count
3. THE Symmetry_Calculator SHALL maintain separate positive and negative counts before applying the factor
4. THE Symmetry_Calculator SHALL preserve the sign of the final difference after applying the factor

### Requirement 5: Derangement Filtering

**User Story:** As an algorithm designer, I want to filter second row derangements based on first column constraints, so that I only process valid combinations.

#### Acceptance Criteria

1. THE Derangement_Filter SHALL exclude derangements where the first element conflicts with the fixed first column
2. WHEN the first column contains value 'a' in position 2, THE Derangement_Filter SHALL exclude all derangements starting with 'a'
3. THE Derangement_Filter SHALL maintain the sign information for filtered derangements
4. THE Derangement_Filter SHALL reduce the derangement set size by approximately 85% for typical first column choices

### Requirement 6: Constraint Propagation Enhancement

**User Story:** As a performance engineer, I want enhanced constraint propagation, so that the search space is minimized early in the enumeration process.

#### Acceptance Criteria

1. THE Enhanced_Propagator SHALL update bitwise constraint masks to reflect fixed first column values
2. THE Enhanced_Propagator SHALL eliminate invalid position-value combinations before enumeration begins
3. THE Enhanced_Propagator SHALL maintain correctness of all constraint checks
4. THE Enhanced_Propagator SHALL achieve at least 1.5x speedup compared to the current algorithm

### Requirement 7: Result Aggregation

**User Story:** As a computational scientist, I want to aggregate results from all first column choices, so that I get the final NLR count.

#### Acceptance Criteria

1. THE Result_Aggregator SHALL sum positive and negative counts from all work units
2. THE Result_Aggregator SHALL compute the final difference (positive - negative)
3. THE Result_Aggregator SHALL ensure thread-safe accumulation of results
4. THE Result_Aggregator SHALL produce results identical to the current algorithm

### Requirement 8: Backward Compatibility

**User Story:** As a system maintainer, I want backward compatibility with existing interfaces, so that current tests and usage patterns continue to work.

#### Acceptance Criteria

1. THE Optimized_Algorithm SHALL maintain the same public API as the current algorithm
2. THE Optimized_Algorithm SHALL pass all existing unit tests without modification
3. THE Optimized_Algorithm SHALL produce identical results to the current algorithm on test cases
4. THE Optimized_Algorithm SHALL support the same input parameters (r, n) as the current algorithm

### Requirement 9: Performance Validation

**User Story:** As a performance analyst, I want to measure performance improvements, so that I can validate the optimization effectiveness.

#### Acceptance Criteria

1. THE Performance_Monitor SHALL measure rectangles processed per second
2. THE Performance_Monitor SHALL track constraint propagation efficiency
3. THE Performance_Monitor SHALL compare performance against the current algorithm baseline
4. THE Performance_Monitor SHALL demonstrate at least 1.5x speedup on (5,8) computation

### Requirement 10: Memory Efficiency

**User Story:** As a system administrator, I want efficient memory usage, so that the optimization doesn't increase memory requirements significantly.

#### Acceptance Criteria

1. THE Memory_Manager SHALL reuse constraint masks across work units where possible
2. THE Memory_Manager SHALL avoid storing redundant first column information
3. THE Memory_Manager SHALL maintain memory usage within 110% of current algorithm
4. THE Memory_Manager SHALL support garbage collection of completed work units