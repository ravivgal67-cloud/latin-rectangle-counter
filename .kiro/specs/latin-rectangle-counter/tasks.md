# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create Python project with virtual environment
  - Install Flask/FastAPI, Hypothesis, SQLite dependencies
  - Set up basic project structure: core/, web/, cache/, tests/
  - _Requirements: All_

- [x] 2. Implement core permutation utilities
  - _Requirements: 3.3_

- [x] 2.1 Implement permutation sign computation
  - Write function to compute sign based on inversion count
  - Handle edge cases: empty permutation, single element
  - _Requirements: 3.3_

- [x] 2.2 Write property test for permutation sign
  - **Property 9: Permutation sign correctness**
  - **Validates: Requirements 3.3**

- [x] 2.3 Implement derangement utilities
  - Write function to check if permutation is derangement
  - Write function to count derangements using recurrence D(n) = (n-1)*(D(n-1) + D(n-2))
  - _Requirements: 2.2_

- [x] 2.4 Write property test for derangement count
  - Verify derangement count matches known values for small n
  - _Requirements: 2.2_

- [x] 2.5 Implement determinant computation
  - Write function to compute determinant of square matrix
  - Use standard algorithm (LU decomposition or cofactor expansion)
  - _Requirements: 4.1_

- [x] 2.6 Write unit tests for determinant
  - Test known matrices: identity, all-ones-except-diagonal
  - _Requirements: 4.1_

- [x] 3. Implement efficient r=2 counting
  - _Requirements: 4.1, 4.4_

- [x] 3.1 Implement count_nlr_r2 function
  - Use derangement count formula
  - Compute determinant of (n×n) matrix with 0 on diagonal, 1 elsewhere
  - Solve for positive and negative counts
  - _Requirements: 4.1, 4.4_

- [x] 3.2 Write property test for r=2 counting accuracy
  - **Property 10: Count accuracy (r=2 case)**
  - **Validates: Requirements 4.1**

- [x] 3.3 Write property test for difference calculation
  - **Property 11: Difference calculation**
  - **Validates: Requirements 4.2**

- [x] 4. Implement Latin rectangle data structure
  - _Requirements: 2.1, 2.2, 3.1_

- [x] 4.1 Create LatinRectangle class
  - Store dimensions (r, n) and data (2D array)
  - Implement is_valid() method
  - Implement is_normalized() method
  - _Requirements: 2.1, 2.2_

- [x] 4.2 Implement compute_sign() method
  - Compute sign as product of row permutation signs
  - _Requirements: 3.1_

- [x] 4.3 Write property test for sign computation
  - **Property 8: Sign computation correctness**
  - **Validates: Requirements 3.1**

- [x] 4.4 Write property test for normalized first row
  - **Property 5: Normalized first row**
  - **Validates: Requirements 2.1**

- [x] 4.5 Write property test for valid rectangle structure
  - **Property 6: Valid rectangle structure**
  - **Validates: Requirements 2.2**

- [x] 5. Implement rectangle generator for r > 2
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 5.1 Implement constrained permutation generator
  - Generate permutations avoiding forbidden values in each position
  - Use backtracking with early pruning
  - _Requirements: 2.2_

- [x] 5.2 Implement generate_normalized_rectangles function
  - Start with identity first row
  - Recursively add valid rows using constrained generator
  - Track column constraints
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 5.3 Write property test for generation completeness
  - **Property 7: Generation completeness and uniqueness**
  - **Validates: Requirements 2.3**

- [x] 6. Implement general counting algorithm
  - _Requirements: 4.1_

- [x] 6.1 Implement count_nlr_general function for r > 2
  - Use generator to produce all rectangles
  - Classify by sign and count
  - _Requirements: 4.1_

- [x] 6.2 Implement count_rectangles dispatcher
  - Route to count_nlr_r2 for r=2
  - Route to count_nlr_general for r>2
  - Return CountResult with counts and difference
  - _Requirements: 4.1_

- [x] 6.3 Write property test for count accuracy (small dimensions)
  - **Property 10: Count accuracy**
  - **Validates: Requirements 4.1**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement input validation
  - _Requirements: 1.1, 1.4_

- [x] 8.1 Create DimensionSpec data class
  - Support types: single (r, n), all_for_n (n), range (n1..n2)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 8.2 Implement validate_dimensions function
  - Check 2 ≤ r ≤ n
  - Check n ≥ 2
  - Return validation result with error messages
  - _Requirements: 1.1, 1.4_

- [x] 8.3 Implement parse_input function
  - Parse string inputs like "<r,n>", "n", "n1..n2"
  - Return DimensionSpec or validation error
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 8.4 Write property test for valid dimension acceptance
  - **Property 1: Valid dimension acceptance**
  - **Validates: Requirements 1.1**

- [x] 8.5 Write property test for invalid dimension rejection
  - **Property 2: Invalid dimension rejection**
  - **Validates: Requirements 1.4**

- [x] 9. Implement range counting
  - _Requirements: 1.2, 1.3_

- [x] 9.1 Implement count_for_n function
  - Count for all r from 2 to n
  - Return list of CountResults
  - _Requirements: 1.2_

- [x] 9.2 Implement count_range function
  - Count for all n in range n1..n2
  - For each n, count all r from 2 to n
  - Return list of CountResults
  - _Requirements: 1.3_

- [x] 9.3 Write property test for complete range coverage (single n)
  - **Property 3: Complete range coverage for single n**
  - **Validates: Requirements 1.2**

- [x] 9.4 Write property test for complete range coverage (n range)
  - **Property 4: Complete range coverage for n range**
  - **Validates: Requirements 1.3**

- [x] 10. Implement cache layer
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 10.1 Create SQLite database schema
  - Create results table with (r, n, positive_count, negative_count, difference)
  - Add indexes on r and n
  - _Requirements: 5.5_

- [x] 10.2 Implement CacheManager class
  - Implement get(r, n) method
  - Implement put(result) method
  - Implement get_all_cached_dimensions() method
  - Implement get_range(r_min, r_max, n_min, n_max) method
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 10.3 Write property test for cache retrieval consistency
  - **Property 12: Cache retrieval consistency**
  - **Validates: Requirements 5.1, 5.2**

- [x] 10.4 Write property test for cache storage
  - **Property 13: Cache storage after computation**
  - **Validates: Requirements 5.4**

- [x] 10.5 Write property test for partial cache utilization
  - **Property 14: Partial cache utilization**
  - **Validates: Requirements 5.3**

- [x] 11. Integrate cache with counting
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 11.1 Update count_rectangles to check cache first
  - Check cache before computing
  - Store results in cache after computing
  - Set from_cache flag appropriately
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 11.2 Update count_for_n to use cache
  - Retrieve cached results where available
  - Compute only missing dimensions
  - _Requirements: 5.3_

- [x] 11.3 Update count_range to use cache
  - Retrieve cached results where available
  - Compute only missing dimensions
  - _Requirements: 5.3_

- [x] 11.4 Write property test for cache flag accuracy
  - **Property 15: Cache flag accuracy**
  - **Validates: Requirements 6.5**

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement result formatting
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 13.1 Implement format_table function
  - Format list of CountResults as text table
  - Include columns: r, n, positive, negative, difference
  - Indicate cached results
  - _Requirements: 6.1, 6.2, 6.5_

- [x] 13.2 Implement format_for_web function
  - Convert CountResults to JSON-serializable dict
  - Include all fields including from_cache flag
  - _Requirements: 6.1, 6.5_

- [x] 14. Implement web API endpoints
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3_

- [x] 14.1 Set up Flask/FastAPI application
  - Create app instance
  - Configure CORS for frontend
  - Set up error handlers
  - _Requirements: 7.1_

- [x] 14.2 Implement POST /api/count endpoint
  - Parse request body for dimensions
  - Validate input
  - Call appropriate counting function
  - Return results or error
  - _Requirements: 7.2, 7.3, 7.4_

- [x] 14.3 Implement GET /api/cache endpoint
  - Query all cached dimensions
  - Return list of (r, n) pairs
  - _Requirements: 8.1_

- [x] 14.4 Implement GET /api/cache/results endpoint
  - Accept query parameters for dimension range
  - Retrieve cached results
  - Return formatted results
  - _Requirements: 8.2, 8.3_

- [x] 14.5 Write property test for cache dimension query
  - **Property 16: Cache dimension query completeness**
  - **Validates: Requirements 8.1**

- [x] 15. Implement web frontend - calculation view
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 15.1 Create HTML structure for calculation view
  - Input form with fields for r, n, or range
  - Submit button
  - Progress indicator
  - Results table container
  - _Requirements: 7.1_

- [x] 15.2 Implement CSS styling
  - Clean, self-explanatory layout
  - Clear labels and examples
  - Responsive design
  - _Requirements: 7.1_

- [x] 15.3 Implement JavaScript for calculation view
  - Handle form submission
  - Call POST /api/count endpoint
  - Display progress feedback
  - Render results table
  - Display error messages
  - Allow new queries without refresh
  - _Requirements: 7.2, 7.3, 7.4, 7.5_

- [x] 16. Implement web frontend - presentation view
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 16.1 Create HTML structure for presentation view
  - Dimension selector (dropdown or checkboxes)
  - Results display area
  - Navigation to switch views
  - _Requirements: 8.1, 8.5_

- [x] 16.2 Implement JavaScript for presentation view
  - Fetch cached dimensions on load
  - Allow user to select dimensions
  - Fetch and display selected results
  - Handle empty cache case
  - Provide navigation between views
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 17. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. End-to-end testing
  - Test complete workflow: input → compute → cache → display
  - Test cache persistence across restarts
  - Test range calculations with partial cache
  - Test both calculation and presentation views

- [x] 19. Tests cleanup and refactoring
  - Consolidate duplicate test logic across test files
  - Remove unused test files that don't align with current spec
  - Standardize test patterns and naming conventions
  - Optimize test performance and resource usage
  - Improve test organization and maintainability
  - _Requirements: All (test quality improvement)_

- [x] 19.1 Audit and remove unused test files
  - Identify test files that don't correspond to current spec modules
  - Remove obsolete test files (e.g., test_auto_counter_extended.py, test_bitset_optimization.py)
  - Clean up test files that test deprecated functionality
  - _Requirements: All_

- [x] 19.2 Consolidate duplicate test logic
  - Move cache flag accuracy tests from test_counter.py to test_cache.py
  - Eliminate redundant test patterns across files
  - Create shared test utilities for common patterns
  - _Requirements: All_

- [x] 19.3 Standardize test file organization
  - Ensure consistent property-based test documentation format
  - Standardize temporary database handling patterns
  - Unify test class naming conventions
  - _Requirements: All_

- [x] 19.4 Optimize test performance
  - Reduce test execution time by optimizing hypothesis settings
  - Improve temporary file cleanup patterns
  - Optimize database operations in tests
  - _Requirements: All_

- [x] 19.5 Improve test maintainability
  - Add missing docstrings and improve test documentation
  - Ensure all property tests reference correct requirement numbers
  - Standardize assertion messages and error reporting
  - _Requirements: All_
