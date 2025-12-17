#!/usr/bin/env python3
"""
Simple test of parallel ultra-safe bitwise.
"""

import time
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise

def test_simple():
    """Test (4,7) with 2 processes."""
    
    r, n = 4, 7
    num_processes = 2
    
    print("=" * 80)
    print(f"TEST: ({r},{n}) with {num_processes} processes")
    print("=" * 80)
    
    # Get reference answer
    print("\n1. Single-threaded reference:")
    start = time.time()
    total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
    time_ref = time.time() - start
    print(f"   Result: {total_ref:,} rectangles in {time_ref:.2f}s")
    
    # Test parallel
    print(f"\n2. Parallel with {num_processes} processes:")
    result = count_rectangles_parallel_ultra_bitwise(r, n, num_processes=num_processes)
    total_par = result.positive_count + result.negative_count
    
    # Compare
    print(f"\n3. Comparison:")
    print(f"   Single: {total_ref:,} (+{pos_ref:,} -{neg_ref:,})")
    print(f"   Parallel: {total_par:,} (+{result.positive_count:,} -{result.negative_count:,})")
    print(f"   Match: {total_ref == total_par and pos_ref == result.positive_count}")
    print(f"   Speedup: {time_ref/result.computation_time:.2f}x")

if __name__ == "__main__":
    test_simple()
