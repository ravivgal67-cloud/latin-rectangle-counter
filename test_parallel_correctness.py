#!/usr/bin/env python3
"""
Comprehensive correctness testing for parallel Latin rectangle counting.

This script performs thorough testing of the parallel implementation by:
1. Comparing parallel vs sequential results for correctness
2. Testing against cached results for verification
3. Running full computations for (3,7) and (4,7)
4. Testing checkpoint functionality
"""

import time
import sys
from typing import Dict, Any

# Import our modules
from core.parallel_generation import count_rectangles_parallel, count_rectangles_auto
from core.parallel_checkpointing import count_rectangles_parallel_resumable
from core.counter import count_rectangles, CountResult
from cache.cache_manager import CacheManager


def compare_results(result1: CountResult, result2: CountResult, name1: str, name2: str) -> bool:
    """Compare two CountResult objects for correctness."""
    print(f"\n🔍 Comparing {name1} vs {name2}:")
    print(f"  {name1}: +{result1.positive_count:,} -{result1.negative_count:,} diff={result1.difference:,} time={result1.computation_time:.2f}s")
    print(f"  {name2}: +{result2.positive_count:,} -{result2.negative_count:,} diff={result2.difference:,} time={result2.computation_time:.2f}s")
    
    # Check correctness
    correct = (
        result1.positive_count == result2.positive_count and
        result1.negative_count == result2.negative_count and
        result1.difference == result2.difference
    )
    
    if correct:
        print(f"  ✅ Results match perfectly!")
        speedup = result1.computation_time / result2.computation_time if result2.computation_time > 0 else 0
        print(f"  ⚡ Speedup: {speedup:.2f}x")
    else:
        print(f"  ❌ Results DO NOT match!")
        print(f"  Positive diff: {result1.positive_count - result2.positive_count}")
        print(f"  Negative diff: {result1.negative_count - result2.negative_count}")
        print(f"  Difference diff: {result1.difference - result2.difference}")
    
    return correct


def test_cached_vs_computed(r: int, n: int) -> Dict[str, Any]:
    """Test parallel computation against cached results."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing ({r},{n}) - Cached vs Computed")
    print(f"{'='*60}")
    
    cache = CacheManager()
    
    # Check if we have cached results
    cached_result = cache.get(r, n)
    if cached_result:
        print(f"📋 Found cached result: +{cached_result.positive_count:,} -{cached_result.negative_count:,} diff={cached_result.difference:,}")
        
        # Compute using parallel method
        print(f"🚀 Computing using parallel method...")
        parallel_result = count_rectangles_parallel(r, n)
        
        # Compare results
        correct = compare_results(cached_result, parallel_result, "Cached", "Parallel")
        
        return {
            'dimension': (r, n),
            'cached_available': True,
            'correct': correct,
            'cached_result': cached_result,
            'parallel_result': parallel_result
        }
    else:
        print(f"❌ No cached result found for ({r},{n})")
        return {
            'dimension': (r, n),
            'cached_available': False,
            'correct': None,
            'cached_result': None,
            'parallel_result': None
        }


def test_sequential_vs_parallel(r: int, n: int) -> Dict[str, Any]:
    """Test sequential vs parallel implementation for correctness."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing ({r},{n}) - Sequential vs Parallel")
    print(f"{'='*60}")
    
    # Force sequential computation (bypass cache)
    print(f"⚡ Computing using sequential method...")
    start_time = time.time()
    
    # Use the core counter module for sequential computation
    from core.latin_rectangle import generate_normalized_rectangles_bitset_optimized
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    for rect in generate_normalized_rectangles_bitset_optimized(r, n):
        total_count += 1
        sign = rect.compute_sign()
        if sign > 0:
            positive_count += 1
        else:
            negative_count += 1
    
    sequential_time = time.time() - start_time
    sequential_result = CountResult(
        r=r, n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=positive_count - negative_count,
        from_cache=False,
        computation_time=sequential_time
    )
    
    # Compute using parallel method
    print(f"🚀 Computing using parallel method...")
    parallel_result = count_rectangles_parallel(r, n)
    
    # Compare results
    correct = compare_results(sequential_result, parallel_result, "Sequential", "Parallel")
    
    return {
        'dimension': (r, n),
        'correct': correct,
        'sequential_result': sequential_result,
        'parallel_result': parallel_result
    }


def test_checkpoint_functionality(r: int, n: int) -> Dict[str, Any]:
    """Test checkpoint-compatible parallel processing."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing ({r},{n}) - Checkpoint Functionality")
    print(f"{'='*60}")
    
    cache = CacheManager()
    
    # Clean up any existing checkpoints
    cache.delete_checkpoint_counters(r, n)
    
    # Test checkpoint-compatible parallel processing
    print(f"🔄 Testing checkpoint-compatible parallel processing...")
    checkpoint_result = count_rectangles_parallel_resumable(r, n, use_checkpoints=True)
    
    # Compare with regular parallel processing
    print(f"🚀 Computing using regular parallel method for comparison...")
    parallel_result = count_rectangles_parallel(r, n)
    
    # Compare results
    correct = compare_results(checkpoint_result, parallel_result, "Checkpoint-Compatible", "Regular Parallel")
    
    return {
        'dimension': (r, n),
        'correct': correct,
        'checkpoint_result': checkpoint_result,
        'parallel_result': parallel_result
    }


def run_full_test_suite():
    """Run comprehensive correctness tests."""
    print("🧪 COMPREHENSIVE PARALLEL PROCESSING CORRECTNESS TESTS")
    print("=" * 80)
    
    test_results = []
    
    # Test dimensions
    test_dimensions = [
        (3, 7),  # Large problem - should use parallel
        (4, 7),  # Large problem - should use parallel
    ]
    
    for r, n in test_dimensions:
        print(f"\n🎯 Testing dimension ({r},{n})")
        
        # Test 1: Compare with cached results (if available)
        cached_test = test_cached_vs_computed(r, n)
        test_results.append(('cached_vs_computed', cached_test))
        
        # Test 2: Compare sequential vs parallel
        sequential_test = test_sequential_vs_parallel(r, n)
        test_results.append(('sequential_vs_parallel', sequential_test))
        
        # Test 3: Test checkpoint functionality
        checkpoint_test = test_checkpoint_functionality(r, n)
        test_results.append(('checkpoint_functionality', checkpoint_test))
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    all_correct = True
    for test_type, result in test_results:
        if result.get('correct') is not None:
            status = "✅ PASS" if result['correct'] else "❌ FAIL"
            dimension = result['dimension']
            print(f"{status} {test_type} for {dimension}")
            if not result['correct']:
                all_correct = False
        elif result.get('cached_available') is False:
            dimension = result['dimension']
            print(f"⚠️  SKIP cached_vs_computed for {dimension} (no cached result)")
    
    print(f"\n{'='*80}")
    if all_correct:
        print("🎉 ALL TESTS PASSED! Parallel implementation is correct.")
    else:
        print("❌ SOME TESTS FAILED! Please investigate the issues.")
    print(f"{'='*80}")
    
    return all_correct


if __name__ == "__main__":
    # Run the comprehensive test suite
    success = run_full_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)