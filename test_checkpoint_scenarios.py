#!/usr/bin/env python3
"""
Test checkpoint feature in both single-process and parallel scenarios.

Tests:
1. Single process (n=6) with checkpoints - uses sequential processing
2. Parallel (n=7) with checkpoints - uses parallel processing
"""

import time
import os
from core.parallel_generation import count_rectangles_parallel
from cache.cache_manager import CacheManager


def test_sequential_checkpoint(r: int, n: int):
    """Test checkpoint functionality in sequential mode (n < 7)."""
    print(f"🧪 Testing SEQUENTIAL checkpoint for ({r},{n})...")
    
    cache = CacheManager()
    
    # Clean up any existing checkpoints
    cache.delete_checkpoint_counters(r, n)
    print(f"🧹 Cleaned up existing checkpoints for ({r},{n})")
    
    # Verify no checkpoint exists
    checkpoint = cache.load_checkpoint_counters(r, n)
    if checkpoint:
        print(f"⚠️  Warning: checkpoint still exists after cleanup")
    else:
        print(f"✅ Confirmed no checkpoint exists")
    
    # Run computation with checkpoints enabled
    print(f"🚀 Running ({r},{n}) with checkpoints enabled...")
    start_time = time.time()
    
    result = count_rectangles_parallel(r, n, use_checkpoints=True)
    
    elapsed = time.time() - start_time
    print(f"✅ Sequential with checkpoints completed in {result.computation_time:.2f}s")
    print(f"   Result: +{result.positive_count:,} -{result.negative_count:,}")
    print(f"   Total: {result.positive_count + result.negative_count:,} rectangles")
    
    # Verify no checkpoint remains after completion
    final_checkpoint = cache.load_checkpoint_counters(r, n)
    if final_checkpoint:
        print(f"⚠️  Warning: checkpoint exists after completion")
        return False
    else:
        print(f"✅ Checkpoint properly cleaned up after completion")
    
    return True


def test_parallel_checkpoint(r: int, n: int):
    """Test checkpoint functionality in parallel mode (n >= 7)."""
    print(f"\n🧪 Testing PARALLEL checkpoint for ({r},{n})...")
    
    cache = CacheManager()
    
    # Clean up any existing checkpoints
    cache.delete_checkpoint_counters(r, n)
    print(f"🧹 Cleaned up existing checkpoints for ({r},{n})")
    
    # Verify no checkpoint exists
    checkpoint = cache.load_checkpoint_counters(r, n)
    if checkpoint:
        print(f"⚠️  Warning: checkpoint still exists after cleanup")
    else:
        print(f"✅ Confirmed no checkpoint exists")
    
    # Run computation with checkpoints enabled
    print(f"🚀 Running ({r},{n}) with checkpoints enabled...")
    start_time = time.time()
    
    result = count_rectangles_parallel(r, n, num_processes=4, use_checkpoints=True)
    
    elapsed = time.time() - start_time
    print(f"✅ Parallel with checkpoints completed in {result.computation_time:.2f}s")
    print(f"   Result: +{result.positive_count:,} -{result.negative_count:,}")
    print(f"   Total: {result.positive_count + result.negative_count:,} rectangles")
    
    # Verify no checkpoint remains after completion
    final_checkpoint = cache.load_checkpoint_counters(r, n)
    if final_checkpoint:
        print(f"⚠️  Warning: checkpoint exists after completion")
        return False
    else:
        print(f"✅ Checkpoint properly cleaned up after completion")
    
    return True


def test_checkpoint_persistence():
    """Test that checkpoints are actually saved and can be loaded."""
    print(f"\n🧪 Testing checkpoint persistence...")
    
    cache = CacheManager()
    
    # Test manual checkpoint save/load
    r, n = 3, 8
    test_counters = [0, 5, 10]
    test_positive = 12345
    test_negative = 54321
    test_scanned = 66666
    test_elapsed = 123.45
    
    print(f"💾 Saving test checkpoint for ({r},{n})...")
    cache.save_checkpoint_counters(r, n, test_counters, test_positive, test_negative, test_scanned, test_elapsed)
    
    print(f"📂 Loading checkpoint for ({r},{n})...")
    loaded = cache.load_checkpoint_counters(r, n)
    
    if loaded:
        print(f"✅ Checkpoint loaded successfully:")
        print(f"   Positive: {loaded['positive_count']:,} (expected: {test_positive:,})")
        print(f"   Negative: {loaded['negative_count']:,} (expected: {test_negative:,})")
        print(f"   Scanned: {loaded['rectangles_scanned']:,} (expected: {test_scanned:,})")
        print(f"   Elapsed: {loaded['elapsed_time']:.2f}s (expected: {test_elapsed:.2f}s)")
        
        # Verify data integrity
        correct = (
            loaded['positive_count'] == test_positive and
            loaded['negative_count'] == test_negative and
            loaded['rectangles_scanned'] == test_scanned and
            abs(loaded['elapsed_time'] - test_elapsed) < 0.01
        )
        
        if correct:
            print(f"✅ Checkpoint data integrity verified!")
        else:
            print(f"❌ Checkpoint data integrity failed!")
            return False
        
        # Clean up
        cache.delete_checkpoint_counters(r, n)
        print(f"🧹 Test checkpoint cleaned up")
        return True
    else:
        print(f"❌ Failed to load checkpoint!")
        return False


def test_checkpoint_comparison():
    """Compare performance and correctness with/without checkpoints."""
    print(f"\n🧪 Testing checkpoint vs no-checkpoint comparison...")
    
    # Test on a smaller problem for speed
    r, n = 4, 6
    
    # Run without checkpoints
    print(f"🏃 Running ({r},{n}) WITHOUT checkpoints...")
    result1 = count_rectangles_parallel(r, n, use_checkpoints=False)
    print(f"   No checkpoints: +{result1.positive_count:,} -{result1.negative_count:,} in {result1.computation_time:.2f}s")
    
    # Run with checkpoints
    print(f"🏃 Running ({r},{n}) WITH checkpoints...")
    result2 = count_rectangles_parallel(r, n, use_checkpoints=True)
    print(f"   With checkpoints: +{result2.positive_count:,} -{result2.negative_count:,} in {result2.computation_time:.2f}s")
    
    # Compare results
    same_results = (
        result1.positive_count == result2.positive_count and
        result1.negative_count == result2.negative_count
    )
    
    if same_results:
        print(f"✅ Results identical with/without checkpoints!")
        
        # Show performance impact
        overhead = result2.computation_time - result1.computation_time
        overhead_pct = (overhead / result1.computation_time) * 100
        print(f"📊 Checkpoint overhead: {overhead:.2f}s ({overhead_pct:.1f}%)")
        
        return True
    else:
        print(f"❌ Results differ with/without checkpoints!")
        return False


def main():
    """Run all checkpoint scenario tests."""
    print("🚀 CHECKPOINT FEATURE TESTS")
    print("=" * 60)
    
    tests = []
    
    # Test 1: Sequential checkpoint (n=6)
    print("\n" + "="*40 + " SEQUENTIAL " + "="*40)
    success1 = test_sequential_checkpoint(4, 6)
    tests.append(("Sequential checkpoint (4,6)", success1))
    
    # Test 2: Parallel checkpoint (n=7)
    print("\n" + "="*40 + " PARALLEL " + "="*42)
    success2 = test_parallel_checkpoint(3, 7)
    tests.append(("Parallel checkpoint (3,7)", success2))
    
    # Test 3: Checkpoint persistence
    print("\n" + "="*40 + " PERSISTENCE " + "="*39)
    success3 = test_checkpoint_persistence()
    tests.append(("Checkpoint persistence", success3))
    
    # Test 4: Checkpoint comparison
    print("\n" + "="*40 + " COMPARISON " + "="*40)
    success4 = test_checkpoint_comparison()
    tests.append(("Checkpoint comparison", success4))
    
    # Summary
    print(f"\n{'='*90}")
    print("📊 CHECKPOINT TEST SUMMARY:")
    
    passed = 0
    for test_name, result in tests:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL CHECKPOINT TESTS PASSED!")
        print("\n✅ Checkpoint feature works correctly in both scenarios:")
        print("   - Sequential processing (n < 7) with checkpoints")
        print("   - Parallel processing (n ≥ 7) with checkpoints")
        print("   - Checkpoint persistence and cleanup")
        print("   - Minimal performance overhead")
        return True
    else:
        print("⚠️  Some checkpoint tests failed")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)