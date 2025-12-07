#!/usr/bin/env python3
"""
Benchmark script to test the optimized Latin rectangle generation.

This script:
1. Tests correctness by comparing results with cached values
2. Measures performance improvements for various dimensions
"""

import time
import sqlite3
from core.counter import count_rectangles
from cache.cache_manager import CacheManager

def format_time(seconds):
    """Format time in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"

def get_cached_result(r, n):
    """Get cached result from database."""
    conn = sqlite3.connect('latin_rectangles.db')
    cursor = conn.cursor()
    cursor.execute('SELECT positive_count, negative_count FROM results WHERE r=? AND n=?', (r, n))
    result = cursor.fetchone()
    conn.close()
    return result

def benchmark_dimension(r, n):
    """Benchmark a single dimension and verify correctness."""
    print(f"\n{'='*70}")
    print(f"Testing ({r},{n})")
    print(f"{'='*70}")
    
    # Get cached result for comparison
    cached = get_cached_result(r, n)
    if cached:
        cached_pos, cached_neg = cached
        print(f"Cached result: +{cached_pos:,}, -{cached_neg:,}, Δ={cached_pos-cached_neg:,}")
    else:
        print("No cached result available")
        cached_pos, cached_neg = None, None
    
    # Time the computation
    print(f"\nComputing with optimized algorithm...")
    start_time = time.time()
    
    # Don't use cache for this test - we want to measure raw performance
    result = count_rectangles(r, n, cache_manager=None)
    
    elapsed = time.time() - start_time
    
    print(f"Computed result: +{result.positive_count:,}, -{result.negative_count:,}, Δ={result.difference:,}")
    print(f"Time elapsed: {format_time(elapsed)}")
    
    # Verify correctness
    if cached_pos is not None:
        if result.positive_count == cached_pos and result.negative_count == cached_neg:
            print("✅ CORRECT: Results match cached values!")
        else:
            print("❌ ERROR: Results DO NOT match cached values!")
            print(f"   Expected: +{cached_pos:,}, -{cached_neg:,}")
            print(f"   Got:      +{result.positive_count:,}, -{result.negative_count:,}")
            return False
    
    return True

def main():
    """Run benchmarks for specified dimensions."""
    print("="*70)
    print("Latin Rectangle Generation Optimization Benchmark")
    print("="*70)
    print("\nThis script tests the optimized constraint propagation algorithm")
    print("by comparing results with cached values and measuring performance.")
    
    # Test dimensions
    test_cases = [
        (4, 4),
        (5, 5),
        (3, 6),
    ]
    
    all_correct = True
    results = []
    
    for r, n in test_cases:
        start = time.time()
        correct = benchmark_dimension(r, n)
        elapsed = time.time() - start
        
        all_correct = all_correct and correct
        results.append((r, n, elapsed, correct))
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Dimension':<15} {'Time':<15} {'Status':<15}")
    print(f"{'-'*70}")
    
    for r, n, elapsed, correct in results:
        status = "✅ PASS" if correct else "❌ FAIL"
        print(f"({r},{n}){' '*10} {format_time(elapsed):<15} {status}")
    
    print(f"\n{'='*70}")
    if all_correct:
        print("✅ All tests PASSED! Optimization is working correctly.")
    else:
        print("❌ Some tests FAILED! Do not commit this change.")
    print(f"{'='*70}")
    
    return all_correct

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
