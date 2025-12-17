#!/usr/bin/env python3
"""
Comprehensive test of parallel ultra-safe bitwise with memory analysis.
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


def test_with_processes(r, n, num_processes):
    """Test with specific number of processes."""
    print("\n" + "=" * 80)
    print(f"TESTING ({r},{n}) WITH {num_processes} PROCESSES")
    print("=" * 80)
    
    # Memory before
    mem_before = get_memory_usage()
    print(f"\n📊 Memory before: {mem_before:.1f} MB")
    
    # Run parallel
    start = time.time()
    result = count_rectangles_parallel_ultra_bitwise(r, n, num_processes=num_processes)
    elapsed = time.time() - start
    
    # Memory after
    mem_after = get_memory_usage()
    mem_used = mem_after - mem_before
    
    total = result.positive_count + result.negative_count
    rate = total / elapsed
    
    print(f"\n📊 RESULTS:")
    print(f"   Total rectangles: {total:,}")
    print(f"   Positive: {result.positive_count:,}")
    print(f"   Negative: {result.negative_count:,}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Rate: {rate:,.0f} rect/s")
    print(f"   Memory after: {mem_after:.1f} MB")
    print(f"   Memory used: {mem_used:.1f} MB")
    
    return {
        'num_processes': num_processes,
        'total': total,
        'positive': result.positive_count,
        'negative': result.negative_count,
        'time': elapsed,
        'rate': rate,
        'memory_used': mem_used
    }


def main():
    """Run comprehensive tests."""
    r, n = 4, 7
    
    print("=" * 80)
    print(f"COMPREHENSIVE PARALLEL TEST: ({r},{n})")
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
    mem_used = mem_after - mem_before
    
    print(f"\n✅ Baseline results:")
    print(f"   Total: {total_ref:,} rectangles")
    print(f"   Positive: {pos_ref:,}")
    print(f"   Negative: {neg_ref:,}")
    print(f"   Time: {time_ref:.2f}s")
    print(f"   Rate: {total_ref/time_ref:,.0f} rect/s")
    print(f"   Memory after: {mem_after:.1f} MB")
    print(f"   Memory used: {mem_used:.1f} MB")
    
    # Test with different process counts
    results = []
    for num_proc in [2, 4, 8]:
        result = test_with_processes(r, n, num_proc)
        results.append(result)
        
        # Verify correctness
        if result['total'] == total_ref and result['positive'] == pos_ref:
            print(f"   ✅ Correctness: PASS")
        else:
            print(f"   ❌ Correctness: FAIL")
    
    # Summary table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(f"\n{'Processes':<12} {'Time (s)':<12} {'Speedup':<12} {'Efficiency':<12} {'Rate (M/s)':<12} {'Memory (MB)':<12}")
    print("-" * 80)
    
    # Baseline
    print(f"{'1 (base)':<12} {time_ref:<12.2f} {'1.00x':<12} {'100.0%':<12} {total_ref/time_ref/1e6:<12.2f} {mem_used:<12.1f}")
    
    # Parallel results
    for result in results:
        speedup = time_ref / result['time']
        efficiency = (speedup / result['num_processes']) * 100
        rate_millions = result['rate'] / 1e6
        print(f"{result['num_processes']:<12} {result['time']:<12.2f} {speedup:<12.2f}x {efficiency:<12.1f}% {rate_millions:<12.2f} {result['memory_used']:<12.1f}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Find best configuration
    best_result = max(results, key=lambda x: x['rate'])
    print(f"\n🏆 Best performance: {best_result['num_processes']} processes")
    print(f"   Rate: {best_result['rate']:,.0f} rect/s")
    print(f"   Speedup: {time_ref/best_result['time']:.2f}x over single-threaded")
    print(f"   Time saved: {time_ref - best_result['time']:.2f}s")
    
    # Scaling analysis
    print(f"\n📊 Scaling analysis:")
    for result in results:
        speedup = time_ref / result['time']
        efficiency = (speedup / result['num_processes']) * 100
        print(f"   {result['num_processes']} processes: {speedup:.2f}x speedup, {efficiency:.1f}% efficiency")
    
    print("\n✅ All tests complete!")


if __name__ == "__main__":
    main()
