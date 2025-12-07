#!/usr/bin/env python3
"""
Benchmark comparison: Naive vs Optimized constraint propagation.

This script compares the performance of:
1. Naive backtracking (generate all permutations, filter invalid ones)
2. Optimized constraint propagation (prune early, forced moves, most-constrained-first)
"""

import time
from typing import List, Set, Iterator
from itertools import permutations
from core.counter import count_rectangles


def generate_constrained_permutations_naive(n: int, forbidden: List[Set[int]]) -> Iterator[List[int]]:
    """
    Naive approach: Generate all permutations, then filter out invalid ones.
    
    This is the baseline for comparison - no optimization.
    """
    for perm in permutations(range(1, n + 1)):
        perm_list = list(perm)
        # Check if this permutation violates any constraints
        valid = True
        for pos, value in enumerate(perm_list):
            if value in forbidden[pos]:
                valid = False
                break
        if valid:
            yield perm_list


def count_rectangles_naive(r: int, n: int) -> tuple:
    """
    Count rectangles using naive permutation generation.
    
    Returns:
        (positive_count, negative_count, time_elapsed)
    """
    from core.permutation import permutation_sign
    
    start_time = time.time()
    
    positive = 0
    negative = 0
    
    # First row is identity
    first_row = list(range(1, n + 1))
    
    def backtrack(rows: List[List[int]]):
        nonlocal positive, negative
        
        if len(rows) == r:
            # Compute sign
            sign = 1
            for row in rows:
                sign *= permutation_sign(row)
            
            if sign == 1:
                positive += 1
            else:
                negative += 1
            return
        
        # Build forbidden set
        forbidden = [set() for _ in range(n)]
        for row in rows:
            for col_idx, value in enumerate(row):
                forbidden[col_idx].add(value)
        
        # Use naive generator
        for next_row in generate_constrained_permutations_naive(n, forbidden):
            rows.append(next_row)
            backtrack(rows)
            rows.pop()
    
    backtrack([first_row])
    
    elapsed = time.time() - start_time
    return positive, negative, elapsed


def count_rectangles_optimized(r: int, n: int) -> tuple:
    """
    Count rectangles using optimized constraint propagation.
    
    Returns:
        (positive_count, negative_count, time_elapsed)
    """
    start_time = time.time()
    result = count_rectangles(r, n, cache_manager=None)
    elapsed = time.time() - start_time
    return result.positive_count, result.negative_count, elapsed


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


def benchmark_comparison(r, n):
    """Compare naive vs optimized for a given dimension."""
    print(f"\n{'='*80}")
    print(f"Benchmarking ({r},{n})")
    print(f"{'='*80}")
    
    # Run naive version
    print("Running NAIVE version (no optimization)...")
    pos_naive, neg_naive, time_naive = count_rectangles_naive(r, n)
    print(f"  Result: +{pos_naive:,}, -{neg_naive:,}")
    print(f"  Time: {format_time(time_naive)}")
    
    # Run optimized version
    print("\nRunning OPTIMIZED version (constraint propagation)...")
    pos_opt, neg_opt, time_opt = count_rectangles_optimized(r, n)
    print(f"  Result: +{pos_opt:,}, -{neg_opt:,}")
    print(f"  Time: {format_time(time_opt)}")
    
    # Verify correctness
    if pos_naive == pos_opt and neg_naive == neg_opt:
        print("\n✅ Results match!")
    else:
        print("\n❌ ERROR: Results don't match!")
        return None
    
    # Calculate speedup
    speedup = time_naive / time_opt if time_opt > 0 else float('inf')
    time_saved = time_naive - time_opt
    percent_saved = (time_saved / time_naive * 100) if time_naive > 0 else 0
    
    print(f"\n📊 Performance Improvement:")
    print(f"  Speedup: {speedup:.2f}x faster")
    print(f"  Time saved: {format_time(time_saved)} ({percent_saved:.1f}% reduction)")
    
    return {
        'r': r,
        'n': n,
        'time_naive': time_naive,
        'time_opt': time_opt,
        'speedup': speedup,
        'time_saved': time_saved,
        'percent_saved': percent_saved
    }


def main():
    """Run comparison benchmarks."""
    print("="*80)
    print("CONSTRAINT PROPAGATION OPTIMIZATION BENCHMARK")
    print("="*80)
    print("\nComparing naive backtracking vs optimized constraint propagation")
    print("for Latin rectangle generation.\n")
    
    # Test cases - focus on where optimization matters
    test_cases = [
        (4, 4),  # Small square
        (5, 5),  # Medium square - optimization wins here
        (6, 6),  # Larger square - should show bigger win
        (4, 5),  # Rectangular
        (5, 6),  # Larger rectangular
    ]
    
    results = []
    
    for r, n in test_cases:
        result = benchmark_comparison(r, n)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Dimension':<12} {'Naive':<12} {'Optimized':<12} {'Speedup':<12} {'Saved':<12}")
    print(f"{'-'*80}")
    
    for res in results:
        dim = f"({res['r']},{res['n']})"
        naive_time = format_time(res['time_naive'])
        opt_time = format_time(res['time_opt'])
        speedup = f"{res['speedup']:.2f}x"
        saved = f"{res['percent_saved']:.1f}%"
        print(f"{dim:<12} {naive_time:<12} {opt_time:<12} {speedup:<12} {saved:<12}")
    
    # Overall statistics
    if results:
        avg_speedup = sum(r['speedup'] for r in results) / len(results)
        avg_saved = sum(r['percent_saved'] for r in results) / len(results)
        print(f"\n{'='*80}")
        print(f"Average speedup: {avg_speedup:.2f}x faster")
        print(f"Average time saved: {avg_saved:.1f}%")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()
