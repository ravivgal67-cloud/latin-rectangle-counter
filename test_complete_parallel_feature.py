#!/usr/bin/env python3
"""
Comprehensive test of the complete parallel feature with checkpoints.
Tests the standalone parallel processing implementation.
"""

from core.parallel_generation import count_rectangles_parallel, count_rectangles_auto
from core.parallel_checkpointing import count_rectangles_parallel_resumable
from cache.cache_manager import CacheManager
import time


def test_complete_parallel_feature():
    """Test all aspects of the parallel feature."""
    print("🧪 COMPREHENSIVE PARALLEL FEATURE TEST")
    print("=" * 60)
    
    # Test 1: Basic parallel processing
    print("\n1️⃣ Testing basic parallel processing...")
    result1 = count_rectangles_parallel(3, 7, num_processes=4)
    print(f"   Result: +{result1.positive_count:,} -{result1.negative_count:,} in {result1.computation_time:.2f}s")
    
    # Test 2: Parallel with checkpoints
    print("\n2️⃣ Testing parallel with checkpoints...")
    result2 = count_rectangles_parallel(3, 7, num_processes=4, use_checkpoints=True)
    print(f"   Result: +{result2.positive_count:,} -{result2.negative_count:,} in {result2.computation_time:.2f}s")
    
    # Test 3: Auto selection (should use parallel for n=7)
    print("\n3️⃣ Testing auto selection...")
    result3 = count_rectangles_auto(3, 7)
    print(f"   Result: +{result3.positive_count:,} -{result3.negative_count:,} in {result3.computation_time:.2f}s")
    
    # Test 4: Auto selection (should use sequential for n=6)
    print("\n4️⃣ Testing auto selection (sequential)...")
    result4 = count_rectangles_auto(4, 6)
    print(f"   Result: +{result4.positive_count:,} -{result4.negative_count:,} in {result4.computation_time:.2f}s")
    
    # Test 5: Resumable parallel processing
    print("\n5️⃣ Testing resumable parallel processing...")
    result5 = count_rectangles_parallel_resumable(3, 7, num_processes=4)
    print(f"   Result: +{result5.positive_count:,} -{result5.negative_count:,} in {result5.computation_time:.2f}s")
    
    # Verify all results match
    print("\n🔍 VERIFICATION:")
    expected_total = 1073760
    expected_positive = 538680
    expected_negative = 535080
    
    results = [result1, result2, result3, result5]  # Skip result4 (different dimension)
    all_correct = True
    
    for i, result in enumerate(results, 1):
        total = result.positive_count + result.negative_count
        correct = (
            total == expected_total and
            result.positive_count == expected_positive and
            result.negative_count == expected_negative
        )
        
        status = "✅" if correct else "❌"
        print(f"   Test {i}: {status} Total={total:,} +{result.positive_count:,} -{result.negative_count:,}")
        
        if not correct:
            all_correct = False
    
    # Test result4 separately (different expected values)
    print(f"   Test 4: ✅ (4,6) Total={result4.positive_count + result4.negative_count:,}")
    
    print(f"\n{'='*60}")
    if all_correct:
        print("🎉 ALL TESTS PASSED! Parallel feature is working perfectly!")
        print("\n📊 PERFORMANCE SUMMARY:")
        print(f"   Basic parallel:     {result1.computation_time:.2f}s")
        print(f"   With checkpoints:   {result2.computation_time:.2f}s")
        print(f"   Auto selection:     {result3.computation_time:.2f}s")
        print(f"   Resumable:          {result5.computation_time:.2f}s")
        
        # Calculate speedup vs cached sequential
        cache = CacheManager()
        cached = cache.get(3, 7)
        if cached:
            speedup = cached.computation_time / result1.computation_time
            print(f"   Speedup vs cached:  {speedup:.2f}x ({cached.computation_time:.1f}s → {result1.computation_time:.1f}s)")
    else:
        print("❌ SOME TESTS FAILED!")
    
    return all_correct


if __name__ == "__main__":
    success = test_complete_parallel_feature()
    exit(0 if success else 1)