#!/usr/bin/env python3
"""
Simple test to understand the parallel processing issue.
"""

from core.latin_rectangle import generate_normalized_rectangles_bitset_optimized
from core.counter import CountResult
import time


def test_sequential_correctness():
    """Test that sequential processing gives correct results."""
    print("🧪 Testing sequential correctness...")
    
    # Test (3,7)
    start_time = time.time()
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    for rect in generate_normalized_rectangles_bitset_optimized(3, 7):
        total_count += 1
        sign = rect.compute_sign()
        if sign > 0:
            positive_count += 1
        else:
            negative_count += 1
    
    elapsed = time.time() - start_time
    
    print(f"Sequential (3,7): +{positive_count:,} -{negative_count:,} total={total_count:,} in {elapsed:.2f}s")
    
    # Check against cache
    from cache.cache_manager import CacheManager
    cache = CacheManager()
    cached = cache.get(3, 7)
    if cached:
        cached_total = cached.positive_count + cached.negative_count
        print(f"Cached (3,7):    +{cached.positive_count:,} -{cached.negative_count:,} total={cached_total:,}")
        
        if (positive_count == cached.positive_count and 
            negative_count == cached.negative_count and
            total_count == cached_total):
            print("✅ Sequential matches cached results perfectly!")
            return True
        else:
            print("❌ Sequential does NOT match cached results!")
            return False
    else:
        print("⚠️  No cached result to compare against")
        return None


def test_counter_ranges():
    """Test counter-based generation with different start points."""
    print("\n🧪 Testing counter ranges...")
    
    # Test generating from different starting points
    test_cases = [
        ([0, 0, 0], "start"),
        ([0, 100, 0], "middle"),
        ([0, 500, 0], "later"),
    ]
    
    for start_counters, desc in test_cases:
        print(f"\nTesting from {desc} position {start_counters}:")
        
        count = 0
        start_time = time.time()
        
        for rect in generate_normalized_rectangles_bitset_optimized(3, 7, start_counters):
            count += 1
            if count >= 10000:  # Sample first 10k
                break
        
        elapsed = time.time() - start_time
        print(f"  Generated {count:,} rectangles in {elapsed:.3f}s")


if __name__ == "__main__":
    # Test sequential correctness first
    sequential_correct = test_sequential_correctness()
    
    # Test counter ranges
    test_counter_ranges()
    
    if sequential_correct:
        print("\n✅ Sequential processing is correct - parallel issue is in partitioning logic")
    else:
        print("\n❌ Sequential processing has issues - need to investigate generator")