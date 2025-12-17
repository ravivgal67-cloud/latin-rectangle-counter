#!/usr/bin/env python3
"""
Test parallel processing with ultra-safe bitwise integration.
"""

import time
from core.parallel_generation import count_rectangles_parallel
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise

def test_parallel_ultra_bitwise():
    """Test (4,7) with 2 processes using ultra-safe bitwise."""
    
    print("=" * 80)
    print("TESTING PARALLEL ULTRA-SAFE BITWISE INTEGRATION")
    print("=" * 80)
    
    r, n = 4, 7
    num_processes = 2
    
    # First, get the correct answer from single-threaded ultra-safe bitwise
    print(f"\n📊 Step 1: Single-threaded ultra-safe bitwise (reference)")
    print(f"Problem: ({r},{n})")
    start = time.time()
    total_single, pos_single, neg_single = count_rectangles_ultra_safe_bitwise(r, n)
    time_single = time.time() - start
    
    print(f"\n✅ Single-threaded results:")
    print(f"   Total: {total_single:,} rectangles")
    print(f"   Positive: {pos_single:,}")
    print(f"   Negative: {neg_single:,}")
    print(f"   Time: {time_single:.2f}s")
    print(f"   Rate: {total_single/time_single:,.0f} rect/s")
    
    # Now test parallel with 2 processes
    print(f"\n📊 Step 2: Parallel with {num_processes} processes")
    start = time.time()
    result = count_rectangles_parallel(r, n, num_processes=num_processes)
    time_parallel = time.time() - start
    
    total_parallel = result.positive_count + result.negative_count
    
    print(f"\n✅ Parallel results:")
    print(f"   Total: {total_parallel:,} rectangles")
    print(f"   Positive: {result.positive_count:,}")
    print(f"   Negative: {result.negative_count:,}")
    print(f"   Time: {time_parallel:.2f}s")
    print(f"   Rate: {total_parallel/time_parallel:,.0f} rect/s")
    
    # Compare results
    print(f"\n📊 Comparison:")
    print(f"   Speedup: {time_single/time_parallel:.2f}x")
    print(f"   Efficiency: {(time_single/time_parallel)/num_processes*100:.1f}%")
    
    # Verify correctness
    print(f"\n🔍 Correctness check:")
    if total_single == total_parallel:
        print(f"   ✅ Total count matches: {total_single:,}")
    else:
        print(f"   ❌ Total count mismatch: {total_single:,} vs {total_parallel:,}")
    
    if pos_single == result.positive_count:
        print(f"   ✅ Positive count matches: {pos_single:,}")
    else:
        print(f"   ❌ Positive count mismatch: {pos_single:,} vs {result.positive_count:,}")
    
    if neg_single == result.negative_count:
        print(f"   ✅ Negative count matches: {neg_single:,}")
    else:
        print(f"   ❌ Negative count mismatch: {neg_single:,} vs {result.negative_count:,}")
    
    if (total_single == total_parallel and 
        pos_single == result.positive_count and 
        neg_single == result.negative_count):
        print(f"\n✅ ALL CHECKS PASSED - Parallel ultra-safe bitwise is working correctly!")
        return True
    else:
        print(f"\n❌ CHECKS FAILED - There are correctness issues")
        return False

if __name__ == "__main__":
    success = test_parallel_ultra_bitwise()
    exit(0 if success else 1)
