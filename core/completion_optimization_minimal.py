#!/usr/bin/env python3
"""
MINIMAL completion optimization - reuse work from rectangle construction.

Key insight: When building (5,6) rectangles, we already compute which derangements
are valid for each position. We can reuse this information to compute the completion
mask more efficiently.

Algorithm:
1. Use the exact same algorithm as main trunk for (5,6)
2. When we find a complete (5,6) rectangle, we already have all the row data
3. Compute completion mask by intersecting the "unused" derangements
4. This should be much more efficient than our previous approaches
"""

import time
from typing import List, Tuple, Optional
from core.smart_derangement_cache import get_smart_derangement_cache


def count_rectangles_5_6_with_completion_minimal() -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (5,6) and (6,6) rectangles using MINIMAL completion optimization.
    
    Returns:
        Tuple of ((total_5_6, pos_5_6, neg_5_6), (total_6_6, pos_6_6, neg_6_6))
    """
    
    r, n = 5, 6
    
    print(f"🚀 Starting MINIMAL completion optimization for (5,6) → (6,6)")
    print(f"   Reusing work from rectangle construction for completion")
    
    # Use the same cache loading as main trunk
    cache = get_smart_derangement_cache(n)
    
    # Use JSON cache version for simplicity and clarity
    return _count_5_6_with_completion_minimal_json(cache)


def _count_5_6_with_completion_minimal_json(cache) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Minimal completion - JSON cache version."""
    
    n = 6
    
    derangements_with_signs = cache.get_all_derangements_with_signs()
    num_derangements = len(derangements_with_signs)
    
    print(f"   🚀 Using JSON cache: {num_derangements:,} derangements")
    print(f"   🔢 Using bitwise operations for {num_derangements}-bit bitsets")
    
    # Pre-compute conflict bitsets
    position_value_index = cache.position_value_index
    
    conflict_masks = {}
    for pos in range(n):
        for val in range(1, n + 1):
            conflict_key = (pos, val)
            if conflict_key in position_value_index:
                mask = 0
                for conflict_idx in position_value_index[conflict_key]:
                    mask |= (1 << conflict_idx)
                conflict_masks[conflict_key] = mask
            else:
                conflict_masks[conflict_key] = 0
    
    all_valid_mask = (1 << num_derangements) - 1
    
    # Create a fast lookup from derangement to index
    derangement_to_index = {}
    for i, (derang, sign) in enumerate(derangements_with_signs):
        if hasattr(derang, 'tolist'):
            derang_tuple = tuple(derang.tolist())
        else:
            derang_tuple = tuple(derang)
        derangement_to_index[derang_tuple] = (i, sign)
    
    # Counters
    total_5_6 = 0
    positive_5_6 = 0
    negative_5_6 = 0
    total_6_6 = 0
    positive_6_6 = 0
    negative_6_6 = 0
    
    # First row is identity
    first_sign = 1
    first_row = list(range(1, n + 1))
    
    # EXACT main trunk algorithm for r=5 with MINIMAL completion calculation
    for second_idx in range(num_derangements):
        second_row, second_sign = derangements_with_signs[second_idx]
        if hasattr(second_row, 'tolist'):
            second_row = second_row.tolist()
        else:
            second_row = list(second_row)
        
        third_row_valid = all_valid_mask
        for pos in range(n):
            third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
        
        if third_row_valid == 0:
            continue
        
        third_mask = third_row_valid
        while third_mask:
            third_idx = (third_mask & -third_mask).bit_length() - 1
            third_mask &= third_mask - 1
            third_row, third_sign = derangements_with_signs[third_idx]
            if hasattr(third_row, 'tolist'):
                third_row = third_row.tolist()
            else:
                third_row = list(third_row)
            
            fourth_row_valid = third_row_valid
            for pos in range(n):
                fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
            
            if fourth_row_valid == 0:
                continue
            
            fourth_mask = fourth_row_valid
            while fourth_mask:
                fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                fourth_mask &= fourth_mask - 1
                fourth_row, fourth_sign = derangements_with_signs[fourth_idx]
                if hasattr(fourth_row, 'tolist'):
                    fourth_row = fourth_row.tolist()
                else:
                    fourth_row = list(fourth_row)
                
                fifth_row_valid = fourth_row_valid
                for pos in range(n):
                    fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                
                fifth_mask = fifth_row_valid
                while fifth_mask:
                    fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                    fifth_mask &= fifth_mask - 1
                    fifth_row, fifth_sign = derangements_with_signs[fifth_idx]
                    if hasattr(fifth_row, 'tolist'):
                        fifth_row = fifth_row.tolist()
                    else:
                        fifth_row = list(fifth_row)
                    
                    # This is a complete (5,6) rectangle
                    rectangle_sign_5_6 = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                    total_5_6 += 1
                    if rectangle_sign_5_6 > 0:
                        positive_5_6 += 1
                    else:
                        negative_5_6 += 1
                    
                    # MINIMAL COMPLETION: Compute completion row directly from existing rows
                    # This is the most efficient approach - compute the completion row values directly
                    completion_row = []
                    for col in range(n):
                        # For each column, find the missing value
                        used_values = {first_row[col], second_row[col], third_row[col], fourth_row[col], fifth_row[col]}
                        all_values = {1, 2, 3, 4, 5, 6}
                        missing_values = all_values - used_values
                        
                        if len(missing_values) == 1:
                            completion_row.append(missing_values.pop())
                        else:
                            completion_row = None
                            break
                    
                    if completion_row is not None:
                        # Look up the completion row in our derangement index
                        completion_tuple = tuple(completion_row)
                        if completion_tuple in derangement_to_index:
                            _, sixth_sign = derangement_to_index[completion_tuple]
                            
                            rectangle_sign_6_6 = rectangle_sign_5_6 * sixth_sign
                            total_6_6 += 1
                            if rectangle_sign_6_6 > 0:
                                positive_6_6 += 1
                            else:
                                negative_6_6 += 1
                        else:
                            print(f"     WARNING: Completion row {completion_row} not found in derangements")
                    else:
                        print(f"     WARNING: Could not compute completion row")
    
    print(f"✅ Minimal completion optimization complete:")
    print(f"   (5,6): {total_5_6:,} rectangles (+{positive_5_6:,} -{negative_5_6:,})")
    print(f"   (6,6): {total_6_6:,} rectangles (+{positive_6_6:,} -{negative_6_6:,})")
    
    # Verify the bijection theorem
    if total_5_6 == total_6_6:
        print(f"✅ Bijection theorem verified: NLR(5,6) = NLR(6,6) = {total_5_6:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR(5,6) = {total_5_6:,} ≠ NLR(6,6) = {total_6_6:,}")
    
    return ((total_5_6, positive_5_6, negative_5_6), (total_6_6, positive_6_6, negative_6_6))


if __name__ == "__main__":
    print("🧪 Testing MINIMAL Completion Optimization for (5,6) → (6,6)")
    print("=" * 70)
    
    try:
        start_time = time.time()
        result = count_rectangles_5_6_with_completion_minimal()
        elapsed = time.time() - start_time
        print(f"\nTotal time: {elapsed:.4f}s")
        
        (total_5_6, pos_5_6, neg_5_6), (total_6_6, pos_6_6, neg_6_6) = result
        print(f"\nFinal Results:")
        print(f"  (5,6): {total_5_6:,} rectangles (+{pos_5_6:,} -{neg_5_6:,})")
        print(f"  (6,6): {total_6_6:,} rectangles (+{pos_6_6:,} -{neg_6_6:,})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()