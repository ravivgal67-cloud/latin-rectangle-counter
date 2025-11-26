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
    """
    r: int
    n: int
    positive_count: int
    negative_count: int
    difference: int
    from_cache: bool = False


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
    
    # Compute the result
    if r == 2:
        result = count_nlr_r2(n)
        # For r=2, we use a formula so complete immediately
        if progress_tracker:
            progress_tracker.complete_dimension()
    else:
        result = count_nlr_general(r, n, progress_tracker)
    
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
    for r in range(2, n + 1):
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
