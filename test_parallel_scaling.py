#!/usr/bin/env python3
"""
Test parallel scaling with different process counts.
"""

import time
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise

def test_scaling():
    """Test (4,7) with 1, 2, 4 processes."""
    
    r, n = 4, 7
    
    print("=" * 80)
    print(f"PARALLEL SCALING TEST: ({r},{n})")
    print("=" * 80)
    
    # Get reference answer
    print("\n📊 Single-threaded baseline:")
    start = time.time()
    total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
    time_single = time.time() - start
    print(f"   Result: {total_ref:,} rectangles in {time_single:.2f}s")
    print(f"   Rate: {total_ref/time_single:,.0f} rect/s")
    
    # Test with different process counts
    for num_proc in [2, 4]:
        print(f"\n📊 Testing with {num_proc} processes:")
        result = count_rectangles_parallel_ultra_bitwise(r, n, num_processes=num_proc)
        total_par = result.positive_count + result.negative_count
        
        speedup = time_single / result.computation_time
        efficiency = (speedup / num_proc) * 100
        
        print(f"\n   Summary for {num_proc} processes:")
        print(f"   - Time: {result.computation_time:.2f}s")
        print(f"   - Speedup: {speedup:.2f}x")
        print(f"   - Efficiency: {efficiency:.1f}%")
        print(f"   - Correctness: {'✅ PASS' if total_par == total_ref else '❌ FAIL'}")

if __name__ == "__main__":
    test_scaling()
