#!/usr/bin/env python3
"""
Test (5,7) with 8 processes and compare with cached data.
"""

import time
import psutil
import os
import sqlite3
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise


def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def get_cached_result(r, n):
    """Get cached result from database."""
    conn = sqlite3.connect('latin_rectangles.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT positive_count, negative_count 
        FROM results 
        WHERE r=? AND n=?
    """, (r, n))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0], result[1]
    return None, None


def main():
    """Test (5,7) with 8 processes."""
    r, n = 5, 7
    num_processes = 8
    
    print("=" * 80)
    print(f"TESTING ({r},{n}) WITH {num_processes} PROCESSES")
    print("=" * 80)
    
    # Check cached result
    print(f"\n📊 Step 1: Check cached result")
    cached_pos, cached_neg = get_cached_result(r, n)
    
    if cached_pos is not None:
        cached_total = cached_pos + cached_neg
        print(f"   ✅ Found cached result:")
        print(f"      Total: {cached_total:,} rectangles")
        print(f"      Positive: {cached_pos:,}")
        print(f"      Negative: {cached_neg:,}")
        print(f"      Difference: {cached_pos - cached_neg:+,}")
    else:
        print(f"   ⚠️  No cached result found for ({r},{n})")
        print(f"   This will be our first computation!")
    
    # Memory before
    print(f"\n📊 Step 2: Memory analysis")
    mem_before = get_memory_usage()
    print(f"   Memory before: {mem_before:.1f} MB")
    
    # Run parallel computation
    print(f"\n📊 Step 3: Parallel computation with {num_processes} processes")
    print("-" * 80)
    
    start = time.time()
    result = count_rectangles_parallel_ultra_bitwise(r, n, num_processes=num_processes)
    elapsed = time.time() - start
    
    # Memory after
    mem_after = get_memory_usage()
    mem_used = mem_after - mem_before
    
    total = result.positive_count + result.negative_count
    rate = total / elapsed
    
    print(f"\n📊 Step 4: Results")
    print("-" * 80)
    print(f"   Total rectangles: {total:,}")
    print(f"   Positive: {result.positive_count:,}")
    print(f"   Negative: {result.negative_count:,}")
    print(f"   Difference: {result.positive_count - result.negative_count:+,}")
    print(f"   Time: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
    print(f"   Rate: {rate:,.0f} rect/s ({rate/1e6:.2f}M rect/s)")
    print(f"   Memory after: {mem_after:.1f} MB")
    print(f"   Memory used: {mem_used:.1f} MB")
    
    # Compare with cached result
    if cached_pos is not None:
        print(f"\n📊 Step 5: Comparison with cached result")
        print("-" * 80)
        
        total_match = (total == cached_total)
        pos_match = (result.positive_count == cached_pos)
        neg_match = (result.negative_count == cached_neg)
        
        print(f"   Total count: {'✅ MATCH' if total_match else '❌ MISMATCH'}")
        print(f"      Computed: {total:,}")
        print(f"      Cached:   {cached_total:,}")
        
        print(f"   Positive count: {'✅ MATCH' if pos_match else '❌ MISMATCH'}")
        print(f"      Computed: {result.positive_count:,}")
        print(f"      Cached:   {cached_pos:,}")
        
        print(f"   Negative count: {'✅ MATCH' if neg_match else '❌ MISMATCH'}")
        print(f"      Computed: {result.negative_count:,}")
        print(f"      Cached:   {cached_neg:,}")
        
        if total_match and pos_match and neg_match:
            print(f"\n   🎉 ALL CHECKS PASSED - Results match cached data perfectly!")
        else:
            print(f"\n   ❌ CHECKS FAILED - Results do not match cached data")
    
    # Performance summary
    print(f"\n📊 Step 6: Performance summary")
    print("-" * 80)
    print(f"   Problem size: ({r},{n})")
    print(f"   Processes: {num_processes}")
    print(f"   Total time: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
    print(f"   Throughput: {rate/1e6:.2f}M rectangles/second")
    print(f"   Memory overhead: {mem_used:.1f} MB")
    
    # Estimate for larger problems
    if cached_pos is not None:
        print(f"\n📊 Extrapolation:")
        print(f"   At this rate, we could compute:")
        print(f"   - 1 billion rectangles in {1e9/rate:.1f}s ({1e9/rate/60:.1f} minutes)")
        print(f"   - 10 billion rectangles in {10e9/rate:.1f}s ({10e9/rate/60:.1f} minutes)")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
