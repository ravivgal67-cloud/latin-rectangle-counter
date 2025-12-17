#!/usr/bin/env python3
"""
Test improved completion optimization (v2) for ultra-safe bitwise with n=6.
Compare computing (5,6) and (6,6) together vs separately.

Key improvement: Maintain bitwise vectors for both rows throughout computation.
No dictionary lookups or completion row building - just bitwise operations.
"""

import time
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise, count_rectangles_with_completion_bitwise


def test_completion_v2_n6():
    """Test improved completion optimization for (5,6) + (6,6)."""
    
    print("=" * 80)
    print("IMPROVED COMPLETION OPTIMIZATION TEST (V2): (5,6) + (6,6)")
    print("=" * 80)
    
    # Method 1: Compute separately
    print("\n📊 Method 1: Compute (5,6) and (6,6) separately")
    print("-" * 80)
    
    start = time.time()
    total_5_6_sep, pos_5_6_sep, neg_5_6_sep = count_rectangles_ultra_safe_bitwise(5, 6)
    time_5_6 = time.time() - start
    print(f"   (5,6): {total_5_6_sep:,} rectangles in {time_5_6:.3f}s")
    
    start = time.time()
    total_6_6_sep, pos_6_6_sep, neg_6_6_sep = count_rectangles_ultra_safe_bitwise(6, 6)
    time_6_6 = time.time() - start
    print(f"   (6,6): {total_6_6_sep:,} rectangles in {time_6_6:.3f}s")
    
    time_separate = time_5_6 + time_6_6
    print(f"\n   Total time (separate): {time_separate:.3f}s")
    
    # Method 2: Compute together with improved completion (v2)
    print("\n📊 Method 2: Compute (5,6) and (6,6) together with improved completion (v2)")
    print("-" * 80)
    
    start = time.time()
    (total_5_6_tog, pos_5_6_tog, neg_5_6_tog), (total_6_6_tog, pos_6_6_tog, neg_6_6_tog) = \
        count_rectangles_with_completion_bitwise(5, 6)
    time_together = time.time() - start
    
    print(f"   (5,6): {total_5_6_tog:,} rectangles")
    print(f"   (6,6): {total_6_6_tog:,} rectangles")
    print(f"\n   Total time (together v2): {time_together:.3f}s")
    
    # Compare
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    
    print(f"\n⏱️  Time comparison:")
    print(f"   Separate: {time_separate:.3f}s")
    print(f"   Together v2: {time_together:.3f}s")
    
    if time_separate < time_together:
        speedup = time_together / time_separate
        print(f"   ✅ Separate is FASTER by {speedup:.2f}x")
        print(f"   Time wasted by v2: {time_together - time_separate:.3f}s")
        winner = "separate"
    else:
        speedup = time_separate / time_together
        print(f"   ✅ Together v2 is FASTER by {speedup:.2f}x")
        print(f"   Time saved by v2: {time_separate - time_together:.3f}s")
        winner = "together"
    
    # Verify correctness
    print(f"\n🔍 Correctness check:")
    
    match_5_6_total = (total_5_6_sep == total_5_6_tog)
    match_5_6_pos = (pos_5_6_sep == pos_5_6_tog)
    match_5_6_neg = (neg_5_6_sep == neg_5_6_tog)
    match_5_6 = match_5_6_total and match_5_6_pos and match_5_6_neg
    
    match_6_6_total = (total_6_6_sep == total_6_6_tog)
    match_6_6_pos = (pos_6_6_sep == pos_6_6_tog)
    match_6_6_neg = (neg_6_6_sep == neg_6_6_tog)
    match_6_6 = match_6_6_total and match_6_6_pos and match_6_6_neg
    
    print(f"   (5,6) total: {'✅ MATCH' if match_5_6_total else '❌ MISMATCH'} ({total_5_6_sep:,} vs {total_5_6_tog:,})")
    print(f"   (5,6) positive: {'✅ MATCH' if match_5_6_pos else '❌ MISMATCH'} ({pos_5_6_sep:,} vs {pos_5_6_tog:,})")
    print(f"   (5,6) negative: {'✅ MATCH' if match_5_6_neg else '❌ MISMATCH'} ({neg_5_6_sep:,} vs {neg_5_6_tog:,})")
    
    print(f"   (6,6) total: {'✅ MATCH' if match_6_6_total else '❌ MISMATCH'} ({total_6_6_sep:,} vs {total_6_6_tog:,})")
    print(f"   (6,6) positive: {'✅ MATCH' if match_6_6_pos else '❌ MISMATCH'} ({pos_6_6_sep:,} vs {pos_6_6_tog:,})")
    print(f"   (6,6) negative: {'✅ MATCH' if match_6_6_neg else '❌ MISMATCH'} ({neg_6_6_sep:,} vs {neg_6_6_tog:,})")
    
    if match_5_6 and match_6_6:
        print(f"\n   🎉 ALL CHECKS PASSED - Results match perfectly!")
    else:
        print(f"\n   ❌ CHECKS FAILED - Results do not match")
        return False
    
    # Recommendation
    print(f"\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    if winner == "together":
        print(f"\n✅ The improved completion optimization (v2) IS beneficial for n=6!")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Time saved: {time_separate - time_together:.3f}s")
        print(f"\n   We should use the improved completion optimization for (n-1, n) + (n, n).")
        print(f"   Key insight: Maintaining bitwise vectors avoids dictionary lookups.")
    else:
        print(f"\n❌ The improved completion optimization (v2) is still NOT beneficial for n=6.")
        print(f"   Computing separately is {speedup:.2f}x faster.")
        print(f"   Time wasted: {time_together - time_separate:.3f}s")
        print(f"\n   Even with bitwise-only operations, separate computation is faster.")
        print(f"   The ultra-safe bitwise is so optimized that any extra work hurts performance.")
    
    return True


if __name__ == "__main__":
    success = test_completion_v2_n6()
    exit(0 if success else 1)