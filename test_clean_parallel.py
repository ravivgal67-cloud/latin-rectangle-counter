#!/usr/bin/env python3
"""
Test the cleaned-up parallel implementation without checkpoint complications.
"""

from core.parallel_generation import count_rectangles_parallel, count_rectangles_auto
from cache.cache_manager import CacheManager
import time


def test_sequential_no_checkpoints():
    """Test sequential processing (n≤6) without checkpoints."""
    print("🧪 Testing sequential processing (n≤6) - no checkpoints needed...")
    
    # Test with checkpoints requested (should be ignored)
    result1 = count_rectangles_parallel(4, 6, use_checkpoints=True)
    print(f"   With checkpoints=True: +{result1.positive_count:,} -{result1.negative_count:,} in {result1.computation_time:.2f}s")
    
    # Test without checkpoints
    result2 = count_rectangles_parallel(4, 6, use_checkpoints=False)
    print(f"   With checkpoints=False: +{result2.positive_count:,} -{result2.negative_count:,} in {result2.computation_time:.2f}s")
    
    # Should be identical
    same_results = (
        result1.positive_count == result2.positive_count and
        result1.negative_count == result2.negative_count
    )
    
    print(f"   Results identical: {'✅' if same_results else '❌'}")
    return same_results


def test_parallel_no_checkpoints():
    """Test parallel processing (n≥7) without checkpoints."""
    print("\n🧪 Testing parallel processing (n≥7) - checkpoints disabled...")
    
    # Test with checkpoints requested (should be ignored)
    result1 = count_rectangles_parallel(3, 7, num_processes=4, use_checkpoints=True)
    print(f"   With checkpoints=True: +{result1.positive_count:,} -{result1.negative_count:,} in {result1.computation_time:.2f}s")
    
    # Test without checkpoints
    result2 = count_rectangles_parallel(3, 7, num_processes=4, use_checkpoints=False)
    print(f"   With checkpoints=False: +{result2.positive_count:,} -{result2.negative_count:,} in {result2.computation_time:.2f}s")
    
    # Should be identical
    same_results = (
        result1.positive_count == result2.positive_count and
        result1.negative_count == result2.negative_count
    )
    
    print(f"   Results identical: {'✅' if same_results else '❌'}")
    
    # Verify correctness against known values
    expected_total = 1073760
    expected_positive = 538680
    expected_negative = 535080
    
    actual_total = result1.positive_count + result1.negative_count
    correct = (actual_total == expected_total and 
              result1.positive_count == expected_positive and
              result1.negative_count == expected_negative)
    
    print(f"   Correctness: {'✅' if correct else '❌'} (expected: {expected_total:,}, got: {actual_total:,})")
    
    return same_results and correct


def test_auto_selection():
    """Test automatic parallel/sequential selection."""
    print("\n🧪 Testing automatic selection...")
    
    # Should use sequential
    print("   Testing (4,6) - should use sequential:")
    result1 = count_rectangles_auto(4, 6)
    print(f"     Result: {result1.positive_count + result1.negative_count:,} rectangles in {result1.computation_time:.2f}s")
    
    # Should use parallel
    print("   Testing (3,7) - should use parallel:")
    result2 = count_rectangles_auto(3, 7)
    print(f"     Result: {result2.positive_count + result2.negative_count:,} rectangles in {result2.computation_time:.2f}s")
    
    # Verify both are correct
    cache = CacheManager()
    cached_46 = cache.get(4, 6)
    cached_37 = cache.get(3, 7)
    
    correct1 = True
    correct2 = True
    
    if cached_46:
        correct1 = (result1.positive_count == cached_46.positive_count and
                   result1.negative_count == cached_46.negative_count)
    
    if cached_37:
        correct2 = (result2.positive_count == cached_37.positive_count and
                   result2.negative_count == cached_37.negative_count)
    
    print(f"   Sequential correctness: {'✅' if correct1 else '❌'}")
    print(f"   Parallel correctness: {'✅' if correct2 else '❌'}")
    
    return correct1 and correct2


def test_performance_comparison():
    """Compare performance between sequential and parallel."""
    print("\n🧪 Testing performance comparison...")
    
    # Sequential on (3,7) for comparison
    print("   Sequential (3,7):")
    start_time = time.time()
    total_count = 0
    positive_count = 0
    
    from core.latin_rectangle import generate_normalized_rectangles_bitset_optimized
    for rect in generate_normalized_rectangles_bitset_optimized(3, 7):
        total_count += 1
        if rect.compute_sign() > 0:
            positive_count += 1
    
    seq_time = time.time() - start_time
    print(f"     Sequential: {total_count:,} rectangles in {seq_time:.2f}s")
    
    # Parallel on (3,7)
    print("   Parallel (3,7):")
    par_result = count_rectangles_parallel(3, 7, num_processes=4)
    par_time = par_result.computation_time
    print(f"     Parallel: {par_result.positive_count + par_result.negative_count:,} rectangles in {par_time:.2f}s")
    
    # Calculate speedup
    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"   Speedup: {speedup:.2f}x ({seq_time:.2f}s → {par_time:.2f}s)")
    
    return speedup > 1.5  # Should be significantly faster


def main():
    """Run all tests for the cleaned-up parallel implementation."""
    print("🚀 CLEAN PARALLEL IMPLEMENTATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Sequential (no checkpoints)", test_sequential_no_checkpoints),
        ("Parallel (no checkpoints)", test_parallel_no_checkpoints),
        ("Auto selection", test_auto_selection),
        ("Performance comparison", test_performance_comparison)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY:")
    
    passed = 0
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Clean parallel implementation ready:")
        print("   - No checkpoint complications")
        print("   - Correct results in all modes")
        print("   - Significant performance improvements")
        print("   - Clear separation of concerns")
        return True
    else:
        print("⚠️  Some tests failed")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)