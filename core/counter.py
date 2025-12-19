"""
Counter module for Latin Rectangle counting.

This module provides functions for counting positive and negative
normalized Latin rectangles.
"""

from dataclasses import dataclass
from typing import List, Optional
from core.permutation import count_derangements, compute_determinant
# Old generator import removed - using ultra-safe bitwise system


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



# Old completion function removed - use ultra-safe bitwise system instead


def count_rectangles(r: int, n: int, cache_manager: Optional['CacheManager'] = None, progress_tracker=None, enable_progress_db: bool = False) -> CountResult:
    """
    Count positive and negative normalized Latin rectangles for given dimensions.
    
    This dispatcher function routes to the appropriate counting algorithm:
    - For r=2: Uses the efficient derangement-based formula (count_nlr_r2)
    - For r>2: Uses auto-selection (ultra-safe bitwise with parallel processing)
    
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
    
    # Compute the result using auto-selection for optimal performance
    if r == 2:
        result = count_nlr_r2(n)
        # For r=2, we use a formula so complete immediately
        if progress_tracker:
            progress_tracker.complete_dimension()
    else:
        # Use auto-selection for r > 2 (chooses between single/parallel ultra-safe bitwise)
        from core.auto_counter import count_rectangles_auto
        result = count_rectangles_auto(r, n)
        # Mark progress as complete since auto_counter handles its own progress
        if progress_tracker:
            progress_tracker.complete_dimension()
    
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
    
    # Use completion optimization when both (n-1, n) and (n, n) need to be computed
    # Only enable if neither is cached and n >= 3 (so n-1 >= 2)
    use_optimization = (n >= 3 and 
                       (cache_manager is None or (n_minus_1_cached is None and n_n_cached is None)))
    
    # Compute r from 2 to n
    for r in range(2, n + 1):
        # Special case: use optimization for (n-1, n) when applicable
        if r == n - 1 and use_optimization:
            import time
            from core.parallel_completion_optimization import count_rectangles_with_completion_parallel
            # Compute both (n-1, n) and (n, n) together using parallel completion optimization
            start_time = time.time()
            (total_n_minus_1, pos_n_minus_1, neg_n_minus_1), (total_n, pos_n, neg_n) = \
                count_rectangles_with_completion_parallel(n - 1, n)
            elapsed = time.time() - start_time
            
            # Create CountResult objects
            result_n_minus_1 = CountResult(
                r=n-1, n=n, 
                positive_count=pos_n_minus_1, 
                negative_count=neg_n_minus_1, 
                difference=pos_n_minus_1 - neg_n_minus_1
            )
            result_n = CountResult(
                r=n, n=n,
                positive_count=pos_n,
                negative_count=neg_n,
                difference=pos_n - neg_n
            )
            
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
    Count normalized Latin rectangles with checkpoint-based resumption.
    
    NOTE: This function now just calls the regular count_rectangles since our
    ultra-safe bitwise system is so fast that checkpointing is no longer needed.
    
    Args:
        r: Number of rows
        n: Number of columns  
        cache_manager: Optional cache manager
        progress_tracker: Optional progress tracker
        checkpoint_interval: Ignored (kept for compatibility)
        
    Returns:
        CountResult with computation results
    """
    # Just use the regular fast counter - no need for checkpointing anymore
    return count_rectangles(r, n, cache_manager, progress_tracker)