#!/usr/bin/env python3
"""
Test row-based parallel implementation on (4,7).
"""

from core.parallel_row_based import count_rectangles_parallel_row_based
from cache.cache_manager import CacheManager
import time


def test_47():
    """Test (4,7) with row-based parallel processing."""
    print("🧪 Testing (4,7) with row-based parallel processing...")
    
    # Run parallel computation
    result = count_rectangles_parallel_row_based(4, 7)
    
    print(f"\nRow-based parallel result:")
    print(f"  +{result.positive_count:,} -{result.negative_count:,} diff={result.difference:,}")
    print(f"  Total: {result.positive_count + result.negative_count:,} rectangles")
    print(f"  Time: {result.computation_time:.2f}s")
    
    # Compare with cached result
    cache = CacheManager()
    cached = cache.get(4, 7)
    if cached:
        cached_total = cached.positive_count + cached.negative_count
        result_total = result.positive_count + result.negative_count
        
        print(f"\nComparison with cached result:")
        print(f"  Cached:   +{cached.positive_count:,} -{cached.negative_count:,} total={cached_total:,}")
        print(f"  Parallel: +{result.positive_count:,} -{result.negative_count:,} total={result_total:,}")
        
        if (result.positive_count == cached.positive_count and 
            result.negative_count == cached.negative_count):
            print("  ✅ Perfect match!")
            
            # Calculate speedup
            speedup = cached.computation_time / result.computation_time
            print(f"  ⚡ Speedup: {speedup:.2f}x ({cached.computation_time:.1f}s → {result.computation_time:.1f}s)")
            return True
        else:
            print("  ❌ Mismatch detected!")
            print(f"  Positive diff: {result.positive_count - cached.positive_count:,}")
            print(f"  Negative diff: {result.negative_count - cached.negative_count:,}")
            print(f"  Total diff: {result_total - cached_total:,}")
            return False
    else:
        print("⚠️  No cached result to compare against")
        return None


if __name__ == "__main__":
    success = test_47()
    
    if success:
        print("\n🎉 Row-based parallel processing works correctly for (4,7)!")
    elif success is False:
        print("\n❌ Row-based parallel processing has issues for (4,7)")
    else:
        print("\n⚠️  Cannot verify without cached result")