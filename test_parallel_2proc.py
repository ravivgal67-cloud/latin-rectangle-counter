#!/usr/bin/env python3
"""
Test parallel ultra-safe bitwise with 2 processes.
"""

import time
import psutil
import os
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise


def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def main():
    """Test (4,7) with 2 processes."""
    r, n = 4, 7
    num_processes = 2
    
    print("=" * 80)
    print(f"TEST: ({r},{n}) WITH {num_processes} PROCESSES")
    print("=" * 80)
    
    # Get reference answer
    print("\n📊 STEP 1: Single-threaded baseline")
    print("-" * 80)
    mem_before = get_memory_usage()
    print(f"Memory before: {mem_before:.1f} MB")
    
    start = time.time()
    total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
    time_ref = time.time() - start
    
    mem_after = get_memory_usage()
    mem_used_single = mem_after - mem_before
    
    print(f"\n✅ Baseline results:")
    print(f"   Total: {total_ref:,} rectangles")
    print(f"   Positive: {pos_ref:,}")
    print(f"   Negative: {neg_ref:,}")
    print(f"   Time: {time_ref:.2f}s")
    print(f"   Rate: {total_ref/time_ref:,.0f} rect/s")
    print(f"   Memory after: {mem_after:.1f} MB")
    print(f"   Memory used: {mem_used_single:.1f} MB")
    
    # Test with 2 processes
    print(f"\n📊 STEP 2: Parallel with {num_processes} processes")
    print("-" * 80)
    mem_before = get_memory_usage()
    print(f"Memory before: {mem_before:.1f} MB")
    
    start = time.time()
    result = count_rectangles_parallel_ultra_bitwise(r, n, num_processes=num_processes)
    elapsed = time.time() - start
    
    mem_after = get_memory_usage()
    mem_used_parallel = mem_after - mem_before
    
    total = result.positive_count + result.negative_count
    rate = total / elapsed
    speedup = time_ref / elapsed
    efficiency = (speedup / num_processes) * 100
    
    print(f"\n✅ Parallel results:")
    print(f"   Total: {total:,} rectangles")
    print(f"   Positive: {result.positive_count:,}")
    print(f"   Negative: {result.negative_count:,}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Rate: {rate:,.0f} rect/s")
    print(f"   Memory after: {mem_after:.1f} MB")
    print(f"   Memory used: {mem_used_parallel:.1f} MB")
    
    # Comparison
    print(f"\n📊 COMPARISON:")
    print("-" * 80)
    print(f"   Speedup: {speedup:.2f}x")
    print(f"   Efficiency: {efficiency:.1f}%")
    print(f"   Time saved: {time_ref - elapsed:.2f}s")
    print(f"   Memory overhead: {mem_used_parallel - mem_used_single:.1f} MB")
    
    # Correctness check
    print(f"\n🔍 CORRECTNESS CHECK:")
    print("-" * 80)
    if total == total_ref:
        print(f"   ✅ Total count matches: {total:,}")
    else:
        print(f"   ❌ Total count mismatch: {total:,} vs {total_ref:,}")
    
    if result.positive_count == pos_ref:
        print(f"   ✅ Positive count matches: {result.positive_count:,}")
    else:
        print(f"   ❌ Positive count mismatch: {result.positive_count:,} vs {pos_ref:,}")
    
    if result.negative_count == neg_ref:
        print(f"   ✅ Negative count matches: {result.negative_count:,}")
    else:
        print(f"   ❌ Negative count mismatch: {result.negative_count:,} vs {neg_ref:,}")
    
    if total == total_ref and result.positive_count == pos_ref:
        print(f"\n✅ ALL CHECKS PASSED!")
    else:
        print(f"\n❌ SOME CHECKS FAILED!")


if __name__ == "__main__":
    main()
