#!/usr/bin/env python3
"""
Smart parallel dispatcher that automatically chooses between sequential and parallel
processing based on problem size to avoid ProcessPoolExecutor overhead on small problems.
"""

import time
from typing import Optional
from core.counter import CountResult
from core.parallel_ultra_bitwise import count_rectangles_parallel_first_column
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise


def count_rectangles_smart_parallel(r: int, n: int, 
                                   num_processes: Optional[int] = None,
                                   logger_session: Optional[str] = None,
                                   force_parallel: bool = False) -> CountResult:
    """
    Smart parallel dispatcher that automatically chooses the best approach.
    
    Uses sequential processing for small problems where ProcessPoolExecutor overhead
    dominates, and parallel processing for large problems where computation dominates.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        logger_session: Custom session name for logging (None = auto-generate)
        force_parallel: Force parallel processing even if not recommended
        
    Returns:
        CountResult with computation results
    """
    
    # Determine if parallel processing is beneficial based on empirical analysis
    should_use_parallel = _should_use_parallel_processing(r, n) or force_parallel
    
    if should_use_parallel:
        print(f"🚀 Using parallel processing for (r={r}, n={n}) - computation dominates overhead")
        return count_rectangles_parallel_first_column(r, n, num_processes, logger_session)
    else:
        print(f"⚡ Using sequential processing for (r={r}, n={n}) - avoiding ProcessPoolExecutor overhead")
        return _count_rectangles_sequential_with_result_format(r, n)


def _should_use_parallel_processing(r: int, n: int) -> bool:
    """
    Determine if parallel processing is beneficial for the given problem size.
    
    Based on empirical analysis:
    - ProcessPoolExecutor has ~0.16s fixed overhead
    - Parallel processing becomes beneficial when sequential time > ~0.3s
    - This corresponds to r >= 5 for n=6
    
    Args:
        r: Number of rows
        n: Number of columns
        
    Returns:
        True if parallel processing is recommended, False otherwise
    """
    
    # Empirically determined thresholds based on overhead analysis
    if n <= 6:
        # For n=6, parallel becomes beneficial at r=5
        return r >= 5
    elif n <= 7:
        # For n=7, expect parallel to be beneficial at r=4 due to more first columns
        return r >= 4
    elif n <= 8:
        # For n=8, expect parallel to be beneficial at r=3 due to much more computation
        return r >= 3
    else:
        # For n>=9, parallel should almost always be beneficial
        return r >= 3
    
    # Conservative fallback: use parallel for larger problems
    return r >= 5


def _count_rectangles_sequential_with_result_format(r: int, n: int) -> CountResult:
    """
    Count rectangles sequentially and format result as CountResult.
    
    Args:
        r: Number of rows
        n: Number of columns
        
    Returns:
        CountResult with computation results
    """
    start_time = time.time()
    
    # Use the existing ultra-safe bitwise sequential implementation
    total_count, positive_count, negative_count = count_rectangles_ultra_safe_bitwise(r, n)
    
    computation_time = time.time() - start_time
    
    return CountResult(
        r=r, n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=positive_count - negative_count,
        from_cache=False,
        computation_time=computation_time
    )


def get_parallel_processing_recommendation(r: int, n: int) -> dict:
    """
    Get detailed recommendation about parallel processing for the given problem size.
    
    Args:
        r: Number of rows
        n: Number of columns
        
    Returns:
        Dictionary with recommendation details
    """
    
    should_use_parallel = _should_use_parallel_processing(r, n)
    
    # Estimate sequential time based on empirical data
    estimated_seq_time = _estimate_sequential_time(r, n)
    
    # ProcessPoolExecutor overhead is approximately 0.16s
    overhead_estimate = 0.16
    
    recommendation = {
        'use_parallel': should_use_parallel,
        'estimated_sequential_time': estimated_seq_time,
        'overhead_estimate': overhead_estimate,
        'reason': '',
        'expected_speedup': None
    }
    
    if should_use_parallel:
        # Estimate potential speedup (conservative estimate)
        if r >= 6:
            expected_speedup = 8.0  # Based on (6,6) results
        elif r >= 5:
            expected_speedup = 3.0  # Based on (5,6) results
        else:
            expected_speedup = 2.0  # Conservative estimate
        
        recommendation['expected_speedup'] = expected_speedup
        recommendation['reason'] = f"Sequential time (~{estimated_seq_time:.3f}s) >> overhead ({overhead_estimate:.3f}s)"
    else:
        recommendation['reason'] = f"Sequential time (~{estimated_seq_time:.3f}s) < overhead ({overhead_estimate:.3f}s)"
    
    return recommendation


def _estimate_sequential_time(r: int, n: int) -> float:
    """
    Estimate sequential computation time based on empirical data.
    
    This is a rough estimate based on observed performance patterns.
    """
    
    # Empirical data points from testing
    if n == 6:
        if r == 3:
            return 0.005
        elif r == 4:
            return 0.10
        elif r == 5:
            return 0.60
        elif r == 6:
            return 1.60
    
    # Rough extrapolation for other cases
    # Time grows exponentially with r and factorially with n
    base_time = 0.001  # Base computation time
    r_factor = 10 ** (r - 3)  # Exponential growth with r
    n_factor = 1
    for i in range(4, n + 1):
        n_factor *= i  # Factorial-like growth with n
    
    return base_time * r_factor * n_factor / 1000  # Scale down the estimate


def main():
    """Test the smart parallel dispatcher."""
    
    test_cases = [
        (3, 6),  # Should use sequential
        (4, 6),  # Should use sequential
        (5, 6),  # Should use parallel
        (6, 6),  # Should use parallel
    ]
    
    print("🧠 TESTING SMART PARALLEL DISPATCHER")
    print("=" * 70)
    
    for r, n in test_cases:
        print(f"\n--- Testing (r={r}, n={n}) ---")
        
        # Get recommendation
        rec = get_parallel_processing_recommendation(r, n)
        print(f"Recommendation: {'Parallel' if rec['use_parallel'] else 'Sequential'}")
        print(f"Reason: {rec['reason']}")
        if rec['expected_speedup']:
            print(f"Expected speedup: {rec['expected_speedup']:.1f}x")
        
        # Test the dispatcher
        try:
            start_time = time.time()
            result = count_rectangles_smart_parallel(r, n)
            elapsed = time.time() - start_time
            
            total = result.positive_count + result.negative_count
            
            print(f"Result: {total:,} rectangles in {elapsed:.6f}s")
            print(f"Positive: {result.positive_count:,}, Negative: {result.negative_count:,}")
            
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()