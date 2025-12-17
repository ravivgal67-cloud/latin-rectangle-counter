"""
Automatic counter selection based on problem size.

This module provides intelligent selection between single-threaded and parallel
ultra-safe bitwise implementations based on problem characteristics.
"""

import multiprocessing as mp
from typing import Tuple, Optional

from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise
from core.counter import CountResult


def count_rectangles_auto(r: int, n: int, 
                          num_processes: Optional[int] = None,
                          force_parallel: bool = False,
                          force_single: bool = False) -> CountResult:
    """
    Automatically select the best counting method based on problem size.
    
    Selection strategy:
    - n ≤ 6: Single-threaded ultra-safe bitwise (already very fast, <2s)
    - n ≥ 7: Parallel ultra-safe bitwise with 8 processes (large problems)
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes for parallel (None = auto-detect, default 8)
        force_parallel: Force parallel processing even for small n
        force_single: Force single-threaded processing even for large n
        
    Returns:
        CountResult with computation results
    """
    import time
    
    # Handle force flags
    if force_single and force_parallel:
        raise ValueError("Cannot force both single and parallel processing")
    
    # Determine processing mode
    if force_single:
        use_parallel = False
        reason = "forced single-threaded"
    elif force_parallel:
        use_parallel = True
        reason = "forced parallel"
    else:
        # Auto-select based on problem size
        if n <= 6:
            use_parallel = False
            reason = f"n={n} ≤ 6 (single-threaded is fast enough)"
        else:
            use_parallel = True
            reason = f"n={n} ≥ 7 (large problem, parallel recommended)"
    
    # Execute
    if use_parallel:
        # Use parallel ultra-safe bitwise
        if num_processes is None:
            num_processes = min(mp.cpu_count(), 8)
        
        print(f"🚀 Auto-selected: Parallel ultra-safe bitwise ({reason})")
        print(f"   Using {num_processes} processes")
        
        return count_rectangles_parallel_ultra_bitwise(r, n, num_processes)
    else:
        # Use single-threaded ultra-safe bitwise
        print(f"⚡ Auto-selected: Single-threaded ultra-safe bitwise ({reason})")
        
        start_time = time.time()
        total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
        computation_time = time.time() - start_time
        
        return CountResult(
            r=r, n=n,
            positive_count=positive,
            negative_count=negative,
            difference=positive - negative,
            from_cache=False,
            computation_time=computation_time
        )


def get_recommended_processes(n: int) -> int:
    """
    Get recommended number of processes for given n.
    
    Args:
        n: Number of columns
        
    Returns:
        Recommended number of processes (1 for single-threaded)
    """
    if n <= 6:
        return 1  # Single-threaded
    else:
        # For large problems, use up to 8 processes
        return min(mp.cpu_count(), 8)


def estimate_computation_time(r: int, n: int, num_processes: Optional[int] = None) -> str:
    """
    Estimate computation time based on problem size and historical data.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes (None = auto)
        
    Returns:
        Human-readable time estimate
    """
    # Historical rates (rectangles/second)
    # Based on benchmarks:
    # - Single-threaded: ~2.8M rect/s for n=7
    # - Parallel (8 proc): ~15M rect/s for n=7
    
    if num_processes is None:
        num_processes = get_recommended_processes(n)
    
    # Rough estimates based on problem size
    if n <= 6:
        # Small problems, very fast
        if r <= 4:
            return "< 1 second"
        elif r <= 5:
            return "< 1 second"
        else:
            return "1-2 seconds"
    elif n == 7:
        # Medium problems
        if num_processes == 1:
            # Single-threaded estimates
            if r == 3:
                return "< 1 minute"
            elif r == 4:
                return "~1 minute"
            elif r == 5:
                return "~20 minutes"
            else:
                return "> 1 hour"
        else:
            # Parallel estimates (8 processes)
            if r == 3:
                return "< 10 seconds"
            elif r == 4:
                return "~10 seconds"
            elif r == 5:
                return "~5 minutes"
            else:
                return "> 10 minutes"
    else:
        # Large problems (n ≥ 8)
        return "Unknown (very large problem)"


def print_recommendation(r: int, n: int):
    """
    Print recommendation for computing (r, n).
    
    Args:
        r: Number of rows
        n: Number of columns
    """
    num_processes = get_recommended_processes(n)
    estimate = estimate_computation_time(r, n, num_processes)
    
    print(f"\n📊 Recommendation for ({r},{n}):")
    print(f"   Method: {'Parallel' if num_processes > 1 else 'Single-threaded'} ultra-safe bitwise")
    if num_processes > 1:
        print(f"   Processes: {num_processes}")
    print(f"   Estimated time: {estimate}")


if __name__ == "__main__":
    # Test auto-selection
    print("Testing auto-selection...")
    
    # Test small problem
    print("\n" + "=" * 80)
    print_recommendation(5, 6)
    result = count_rectangles_auto(5, 6)
    print(f"Result: {result.positive_count + result.negative_count:,} rectangles in {result.computation_time:.2f}s")
    
    # Test large problem
    print("\n" + "=" * 80)
    print_recommendation(4, 7)
    result = count_rectangles_auto(4, 7)
    print(f"Result: {result.positive_count + result.negative_count:,} rectangles in {result.computation_time:.2f}s")
