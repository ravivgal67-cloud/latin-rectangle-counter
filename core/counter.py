"""
Counter module for Latin Rectangle counting.

This module provides functions for counting positive and negative
normalized Latin rectangles.
"""

from dataclasses import dataclass
from typing import List, Optional
from core.permutation import count_derangements, compute_determinant
from core.latin_rectangle import generate_normalized_rectangles


@dataclass
class CountResult:
    """
    Result of counting normalized Latin rectangles.
    
    Attributes:
        r: Number of rows
        n: Number of columns
        positive_count: Count of rectangles with sign +1 (even parity)
        negative_count: Count of rectangles with sign -1 (odd parity)
        difference: positive_count - negative_count
        from_cache: Whether this result was retrieved from cache
        computation_time: Time taken to compute in seconds (None if from cache)
        computed_at: Timestamp when computed (None if not yet cached)
    """
    r: int
    n: int
    positive_count: int
    negative_count: int
    difference: int
    from_cache: bool = False
    computation_time: Optional[float] = None
    computed_at: Optional[str] = None


def count_nlr_r2(n: int) -> CountResult:
    """
    Efficiently count positive and negative normalized Latin rectangles for r=2.
    
    For r=2, normalized Latin rectangles consist of:
    - First row: [1, 2, 3, ..., n] (identity permutation)
    - Second row: A derangement of [1, 2, 3, ..., n]
    
    This function uses the derangement formula and determinant computation
    to count without explicit generation:
    
    Step 1: Compute total derangements using recurrence D(n)
    Step 2: Compute difference (positive - negative) as determinant of matrix M
            where M[i][j] = 0 if i == j, else 1
    Step 3: Solve the system:
            positive + negative = D(n)
            positive - negative = det(M)
            
            Therefore:
            positive = (D(n) + det(M)) / 2
            negative = (D(n) - det(M)) / 2
    
    Args:
        n: Number of columns (n >= 2)
        
    Returns:
        CountResult with positive and negative counts
        
    Examples:
        >>> result = count_nlr_r2(3)
        >>> result.positive_count
        1
        >>> result.negative_count
        2
        >>> result.difference
        -1
    """
    # Step 1: Compute total derangements
    total = count_derangements(n)
    
    # Step 2: Compute difference using closed-form formula
    # diff = det(J_n - I_n) = (-1)^(n-1) * (n-1)
    # This is much more efficient than computing the determinant
    diff = ((-1) ** (n - 1)) * (n - 1)
    
    # Step 3: Solve for positive and negative counts
    positive = (total + diff) // 2
    negative = (total - diff) // 2
    
    return CountResult(
        r=2,
        n=n,
        positive_count=positive,
        negative_count=negative,
        difference=diff,
        from_cache=False
    )


def count_nlr_general(r: int, n: int, progress_tracker=None) -> CountResult:
    """
    Count positive and negative normalized Latin rectangles for r > 2.
    
    This function uses the generator to produce all normalized Latin rectangles
    of dimension r×n, then classifies each by its sign and counts them.
    
    Args:
        r: Number of rows (r > 2)
        n: Number of columns (n >= r)
        
    Returns:
        CountResult with positive and negative counts
        
    Examples:
        >>> result = count_nlr_general(3, 3)
        >>> result.positive_count + result.negative_count  # Total count
        2
    """
    positive_count = 0
    negative_count = 0
    
    # Notify progress tracker if provided
    if progress_tracker:
        progress_tracker.start_dimension(r, n)
    
    # Generate all normalized rectangles and classify by sign
    for rectangle in generate_normalized_rectangles(r, n):
        sign = rectangle.compute_sign()
        if sign == 1:
            positive_count += 1
            if progress_tracker:
                progress_tracker.update(positive_delta=1)
        else:
            negative_count += 1
            if progress_tracker:
                progress_tracker.update(negative_delta=1)
    
    difference = positive_count - negative_count
    
    # Mark dimension as complete
    if progress_tracker:
        progress_tracker.complete_dimension()
    
    return CountResult(
        r=r,
        n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=difference,
        from_cache=False
    )


def count_nlr_with_completion(r: int, n: int, progress_tracker=None) -> tuple[CountResult, CountResult]:
    """
    Count (r, n) and simultaneously compute (r+1, n) by completing each rectangle.
    
    This optimization works when r = n-1. Every (n-1)×n normalized Latin rectangle
    can be uniquely completed to an n×n Latin square by adding the missing element
    in each column as the last row.
    
    Args:
        r: Number of rows (must equal n-1)
        n: Number of columns
        progress_tracker: Optional progress tracker
        
    Returns:
        Tuple of (result_r, result_r_plus_1) where:
        - result_r is the CountResult for (r, n)
        - result_r_plus_1 is the CountResult for (r+1, n)
        
    Raises:
        ValueError: If r != n-1
    """
    if r != n - 1:
        raise ValueError(f"count_nlr_with_completion requires r = n-1, got r={r}, n={n}")
    
    # Counters for (r, n)
    positive_r = 0
    negative_r = 0
    
    # Counters for (r+1, n) = (n, n)
    positive_r_plus_1 = 0
    negative_r_plus_1 = 0
    
    # Notify progress tracker for (r, n) if provided
    if progress_tracker:
        progress_tracker.start_dimension(r, n)
    
    # Generate all (r, n) rectangles
    for rectangle in generate_normalized_rectangles(r, n):
        sign_r = rectangle.compute_sign()
        
        # Count for (r, n)
        if sign_r == 1:
            positive_r += 1
        else:
            negative_r += 1
        
        # Complete to (r+1, n) by finding missing element in each column
        last_row = []
        for col_idx in range(n):
            # Find which element is missing in this column
            column_values = {rectangle.data[row_idx][col_idx] for row_idx in range(r)}
            missing = next(val for val in range(1, n + 1) if val not in column_values)
            last_row.append(missing)
        
        # Compute sign of the completed (r+1, n) rectangle
        # The sign changes based on the parity of the last row permutation
        from core.permutation import permutation_sign
        last_row_sign = permutation_sign(last_row)
        sign_r_plus_1 = sign_r * last_row_sign
        
        # Count for (r+1, n)
        if sign_r_plus_1 == 1:
            positive_r_plus_1 += 1
        else:
            negative_r_plus_1 += 1
        
        # Update progress for the (r, n) computation
        if progress_tracker:
            progress_tracker.update(positive_delta=1 if sign_r == 1 else 0,
                                   negative_delta=1 if sign_r == -1 else 0)
    
    # Mark (r, n) as complete
    if progress_tracker:
        progress_tracker.complete_dimension()
    
    # Now notify progress tracker for (r+1, n) - it's instantly complete since we already computed it
    if progress_tracker:
        progress_tracker.start_dimension(r + 1, n)
        # Update with final counts
        progress_tracker.update(positive_delta=positive_r_plus_1, negative_delta=negative_r_plus_1)
        progress_tracker.complete_dimension()
    
    result_r = CountResult(
        r=r,
        n=n,
        positive_count=positive_r,
        negative_count=negative_r,
        difference=positive_r - negative_r,
        from_cache=False
    )
    
    result_r_plus_1 = CountResult(
        r=r + 1,
        n=n,
        positive_count=positive_r_plus_1,
        negative_count=negative_r_plus_1,
        difference=positive_r_plus_1 - negative_r_plus_1,
        from_cache=False
    )
    
    return result_r, result_r_plus_1


def count_rectangles(r: int, n: int, cache_manager: Optional['CacheManager'] = None, progress_tracker=None, enable_progress_db: bool = False) -> CountResult:
    """
    Count positive and negative normalized Latin rectangles for given dimensions.
    
    This dispatcher function routes to the appropriate counting algorithm:
    - For r=2: Uses the efficient derangement-based formula (count_nlr_r2)
    - For r>2: Uses the general backtracking algorithm (count_nlr_general)
    
    If a cache_manager is provided, this function will:
    1. Check the cache for existing results
    2. Return cached results if available
    3. Compute and store new results if not cached
    
    Args:
        r: Number of rows (2 <= r <= n)
        n: Number of columns (n >= 2)
        cache_manager: Optional CacheManager instance for caching results
        
    Returns:
        CountResult with positive count, negative count, and their difference
        
    Examples:
        >>> result = count_rectangles(2, 3)
        >>> result.positive_count
        2
        >>> result.negative_count
        0
        
        >>> result = count_rectangles(3, 4)
        >>> result.r
        3
        >>> result.n
        4
    """
    import time
    
    # Initialize progress tracker with cache manager if needed
    if progress_tracker and enable_progress_db and cache_manager:
        progress_tracker.cache_manager = cache_manager
    
    # Check cache first if cache_manager is provided
    if cache_manager is not None:
        cached_result = cache_manager.get(r, n)
        if cached_result is not None:
            # Cached results don't need progress tracking - no computation happening
            return cached_result
    
    # Notify progress tracker for non-cached results
    if progress_tracker:
        progress_tracker.start_dimension(r, n)
    
    # Start timing
    start_time = time.time()
    
    # Compute the result
    if r == 2:
        result = count_nlr_r2(n)
        # For r=2, we use a formula so complete immediately
        if progress_tracker:
            progress_tracker.complete_dimension()
    else:
        result = count_nlr_general(r, n, progress_tracker)
    
    # Calculate computation time
    computation_time = time.time() - start_time
    result.computation_time = computation_time
    
    # Store in cache if cache_manager is provided
    if cache_manager is not None:
        cache_manager.put(result)
        # Update the from_cache flag to False since we just computed it
        result.from_cache = False
    
    return result


def count_for_n(n: int, cache_manager: Optional['CacheManager'] = None, progress_tracker=None, enable_progress_db: bool = False) -> List[CountResult]:
    """
    Count normalized Latin rectangles for all r from 2 to n.
    
    For a given n, this function computes counts for all valid row counts
    r where 2 <= r <= n.
    
    If a cache_manager is provided, this function will retrieve cached results
    where available and compute only missing dimensions.
    
    OPTIMIZATION: When computing (n-1, n), we simultaneously compute (n, n)
    by completing each rectangle, which is much more efficient than generating
    all (n, n) rectangles separately. This optimization is only used when both
    (n-1, n) and (n, n) need to be computed (not cached).
    
    Args:
        n: Number of columns (n >= 2)
        cache_manager: Optional CacheManager instance for caching results
        
    Returns:
        List of CountResults, one for each r from 2 to n
        
    Examples:
        >>> results = count_for_n(3)
        >>> len(results)
        2
        >>> results[0].r
        2
        >>> results[1].r
        3
    """
    results = []
    
    # Check if both (n-1, n) and (n, n) are cached
    n_minus_1_cached = cache_manager.get(n - 1, n) if cache_manager and n > 2 else None
    n_n_cached = cache_manager.get(n, n) if cache_manager else None
    
    # Decide whether to use optimization
    use_optimization = (n > 2 and 
                       n_minus_1_cached is None and 
                       n_n_cached is None)
    
    # Compute r from 2 to n
    for r in range(2, n + 1):
        # Special case: use optimization for (n-1, n) when applicable
        if r == n - 1 and use_optimization:
            import time
            # Compute both (n-1, n) and (n, n) together
            start_time = time.time()
            result_n_minus_1, result_n = count_nlr_with_completion(n - 1, n, progress_tracker)
            elapsed = time.time() - start_time
            
            # Set computation time for both results (they were computed together)
            result_n_minus_1.computation_time = elapsed
            result_n.computation_time = elapsed
            
            # Store both in cache
            if cache_manager:
                cache_manager.put(result_n_minus_1)
                cache_manager.put(result_n)
            
            results.append(result_n_minus_1)
            results.append(result_n)
            break  # We've computed (n, n) already, so we're done
        else:
            # Normal computation
            result = count_rectangles(r, n, cache_manager, progress_tracker, enable_progress_db)
            results.append(result)
    
    return results


def count_range(n_start: int, n_end: int, cache_manager: Optional['CacheManager'] = None, progress_tracker=None, enable_progress_db: bool = False) -> List[CountResult]:
    """
    Count normalized Latin rectangles for a range of n values.
    
    For each n in the range [n_start, n_end], this function computes counts
    for all valid row counts r where 2 <= r <= n.
    
    If a cache_manager is provided, this function will retrieve cached results
    where available and compute only missing dimensions.
    
    Args:
        n_start: Start of n range (inclusive, n_start >= 2)
        n_end: End of n range (inclusive, n_end >= n_start)
        cache_manager: Optional CacheManager instance for caching results
        
    Returns:
        List of CountResults for all (r, n) combinations where
        n_start <= n <= n_end and 2 <= r <= n
        
    Examples:
        >>> results = count_range(2, 3)
        >>> len(results)
        3
        >>> # Should include: (2,2), (2,3), (3,3)
    """
    results = []
    for n in range(n_start, n_end + 1):
        results.extend(count_for_n(n, cache_manager, progress_tracker, enable_progress_db))
    return results


def count_rectangles_resumable(r: int, n: int, cache_manager: Optional['CacheManager'] = None, 
                              progress_tracker=None, checkpoint_interval: int = 10000) -> CountResult:
    """
    Count normalized Latin rectangles with checkpoint-based resumption using counter state.
    
    This function uses the counter-based generation approach for precise checkpointing.
    It can resume computation from a previously saved checkpoint by restoring the
    exact counter state, ensuring no rectangles are double-counted or missed.
    
    Args:
        r: Number of rows (2 ≤ r ≤ n)
        n: Number of columns (n ≥ 2)
        cache_manager: Optional CacheManager for caching and checkpoints
        progress_tracker: Optional ProgressTracker for progress updates
        checkpoint_interval: Save checkpoint every N rectangles (default: 10000)
        
    Returns:
        CountResult with positive/negative counts and difference
        
    Examples:
        >>> # First run (gets interrupted)
        >>> cache = CacheManager(":memory:")
        >>> result = count_rectangles_resumable(5, 6, cache)  # Saves checkpoints
        
        >>> # Second run (resumes from checkpoint)
        >>> result = count_rectangles_resumable(5, 6, cache)  # Resumes automatically
    """
    import time
    from core.latin_rectangle import CounterBasedRectangleIterator
    
    # Check if result is already cached
    if cache_manager is not None:
        cached_result = cache_manager.get(r, n)
        if cached_result is not None:
            return cached_result
    
    # Try to load existing checkpoint
    checkpoint = None
    if cache_manager is not None:
        checkpoint = cache_manager.load_checkpoint_counters(r, n)
    
    if checkpoint:
        # Resume from checkpoint
        start_counters = checkpoint['counters']
        positive_count = checkpoint['positive_count']
        negative_count = checkpoint['negative_count']
        rectangles_scanned = checkpoint['rectangles_scanned']
        elapsed_time = checkpoint['elapsed_time']
        
        print(f"Resuming (r={r}, n={n}) from checkpoint:")
        print(f"  - Counter state: {start_counters}")
        print(f"  - Rectangles scanned: {rectangles_scanned:,}")
        print(f"  - Positive: {positive_count:,}, Negative: {negative_count:,}")
        print(f"  - Elapsed time: {elapsed_time:.2f}s")
    else:
        # Start fresh
        start_counters = None
        positive_count = negative_count = rectangles_scanned = 0
        elapsed_time = 0.0
        print(f"Starting fresh computation for (r={r}, n={n})")
    
    # Notify progress tracker
    if progress_tracker:
        progress_tracker.start_dimension(r, n)
        # If resuming, update with current counts
        if checkpoint:
            progress_tracker.positive_count = positive_count
            progress_tracker.negative_count = negative_count
            progress_tracker.rectangles_scanned = rectangles_scanned
    
    # Start timing (for this session)
    session_start_time = time.time()
    count_since_checkpoint = 0
    
    # Create iterator with checkpoint state
    iterator = CounterBasedRectangleIterator(r, n, start_counters)
    
    # Generate rectangles using iterator
    try:
        for rect in iterator:
            # Count rectangle
            sign = rect.compute_sign()
            if sign > 0:
                positive_count += 1
            else:
                negative_count += 1
            
            rectangles_scanned += 1
            count_since_checkpoint += 1
            
            # Update progress tracker
            if progress_tracker:
                progress_tracker.update(
                    positive_delta=1 if sign > 0 else 0,
                    negative_delta=1 if sign < 0 else 0,
                    scanned_delta=1
                )
            
            # Save checkpoint periodically
            if cache_manager and count_since_checkpoint >= checkpoint_interval:
                current_elapsed = elapsed_time + (time.time() - session_start_time)
                
                # Get current iterator state for checkpointing
                iterator_state = iterator.get_state()
                
                cache_manager.save_checkpoint_counters(
                    r, n, iterator_state['counters'], positive_count, negative_count, 
                    rectangles_scanned, current_elapsed
                )
                
                count_since_checkpoint = 0
                print(f"Checkpoint saved: {rectangles_scanned:,} rectangles, "
                      f"{current_elapsed:.1f}s elapsed, counters={iterator_state['counters']}")
    
    except StopIteration:
        # Normal completion
        pass
    
    # Calculate total computation time
    session_time = time.time() - session_start_time
    total_computation_time = elapsed_time + session_time
    
    # Mark as complete
    if progress_tracker:
        progress_tracker.complete_dimension()
    
    # Create result
    result = CountResult(
        r=r, n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=positive_count - negative_count,
        from_cache=False,
        computation_time=total_computation_time
    )
    
    # Store final result in cache and clean up checkpoint
    if cache_manager is not None:
        cache_manager.put(result)
        cache_manager.delete_checkpoint_counters(r, n)
        print(f"Computation complete! Final result cached, checkpoint deleted.")
    
    print(f"Final result: positive={positive_count:,}, negative={negative_count:,}, "
          f"difference={positive_count - negative_count:,}")
    print(f"Total time: {total_computation_time:.2f}s")
    
    return result