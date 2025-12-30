#!/usr/bin/env python3
"""
TRULY OPTIMIZED completion optimization - incremental completion mask.

The key insight: Instead of recalculating the completion mask from scratch for each
(5,6) rectangle, we build it incrementally as we construct the rectangle.

This should achieve the true theoretical 5-10% overhead.
"""

import time
from typing import List, Tuple, Optional
from core.smart_derangement_cache import get_smart_derangement_cache


def count_rectangles_5_6_with_completion_truly_optimized() -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (5,6) and (6,6) rectangles using TRULY OPTIMIZED completion with incremental masks.
    
    Returns:
        Tuple of ((total_5_6, pos_5_6, neg_5_6), (total_6_6, pos_6_6, neg_6_6))
    """
    
    r, n = 5, 6
    
    print(f"🚀 Starting TRULY OPTIMIZED completion optimization for (5,6) → (6,6)")
    print(f"   Using incremental completion mask building")
    
    # Use the same cache loading as main trunk
    cache = get_smart_derangement_cache(n)
    
    # Check if we have the optimized binary cache (same as main trunk)
    if hasattr(cache, 'get_bitwise_data') and hasattr(cache, 'get_derangement_value'):
        return _count_5_6_with_completion_truly_optimized_binary(cache)
    else:
        return _count_5_6_with_completion_truly_optimized_json(cache)


def _count_5_6_with_completion_truly_optimized_binary(cache) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Truly optimized completion - binary cache version."""
    
    n = 6
    
    # Get pre-computed bitwise data (EXACT same as main trunk)
    conflict_masks, all_valid_mask = cache.get_bitwise_data()
    
    # Convert NumPy arrays to Python lists (EXACT same as main trunk)
    derangements_lists = []
    signs_list = []
    
    for i in range(len(cache.derangements)):
        derangements_lists.append(cache.derangements[i].tolist())
        signs_list.append(int(cache.signs[i]))
    
    num_derangements = len(derangements_lists)
    
    print(f"   🚀 Using binary cache with Python list conversion: {num_derangements:,} derangements")
    print(f"   🔢 Using bitwise operations for {num_derangements}-bit bitsets")
    
    # Counters for (5,6) and (6,6) rectangles
    total_5_6 = 0
    positive_5_6 = 0
    negative_5_6 = 0
    total_6_6 = 0
    positive_6_6 = 0
    negative_6_6 = 0
    
    # First row is identity [1,2,3,4,5,6] with sign +1
    first_sign = 1
    first_row = list(range(1, n + 1))
    
    # Pre-compute completion mask after first row (identity)
    completion_mask_after_first = all_valid_mask
    for pos in range(n):
        completion_mask_after_first &= ~conflict_masks[(pos, first_row[pos])]
    
    # EXACT main trunk algorithm for r=5 with INCREMENTAL completion mask
    for second_idx in range(num_derangements):
        second_row = derangements_lists[second_idx]
        second_sign = signs_list[second_idx]
        
        # Update completion mask after second row (INCREMENTAL)
        completion_mask_after_second = completion_mask_after_first
        for pos in range(n):
            completion_mask_after_second &= ~conflict_masks[(pos, second_row[pos])]
        
        third_row_valid = all_valid_mask
        for pos in range(n):
            third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
        
        if third_row_valid == 0:
            continue
        
        third_mask = third_row_valid
        while third_mask:
            third_idx = (third_mask & -third_mask).bit_length() - 1
            third_mask &= third_mask - 1
            third_row = derangements_lists[third_idx]
            third_sign = signs_list[third_idx]
            
            # Update completion mask after third row (INCREMENTAL)
            completion_mask_after_third = completion_mask_after_second
            for pos in range(n):
                completion_mask_after_third &= ~conflict_masks[(pos, third_row[pos])]
            
            fourth_row_valid = third_row_valid
            for pos in range(n):
                fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
            
            if fourth_row_valid == 0:
                continue
            
            fourth_mask = fourth_row_valid
            while fourth_mask:
                fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                fourth_mask &= fourth_mask - 1
                fourth_row = derangements_lists[fourth_idx]
                fourth_sign = signs_list[fourth_idx]
                
                # Update completion mask after fourth row (INCREMENTAL)
                completion_mask_after_fourth = completion_mask_after_third
                for pos in range(n):
                    completion_mask_after_fourth &= ~conflict_masks[(pos, fourth_row[pos])]
                
                fifth_row_valid = fourth_row_valid
                for pos in range(n):
                    fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                
                fifth_mask = fifth_row_valid
                while fifth_mask:
                    fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                    fifth_mask &= fifth_mask - 1
                    fifth_sign = signs_list[fifth_idx]
                    
                    # This is a complete (5,6) rectangle
                    rectangle_sign_5_6 = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                    total_5_6 += 1
                    if rectangle_sign_5_6 > 0:
                        positive_5_6 += 1
                    else:
                        negative_5_6 += 1
                    
                    # TRULY OPTIMIZED COMPLETION: Just 6 more operations (one per position)
                    # We already have the mask after 4 rows, just need to add conflicts from 5th row
                    completion_mask_final = completion_mask_after_fourth
                    fifth_row = derangements_lists[fifth_idx]
                    for pos in range(n):
                        completion_mask_final &= ~conflict_masks[(pos, fifth_row[pos])]
                    
                    # There should be exactly one valid completion row
                    if completion_mask_final != 0:
                        num_completions = bin(completion_mask_final).count('1')
                        if num_completions == 1:
                            sixth_idx = (completion_mask_final & -completion_mask_final).bit_length() - 1
                            sixth_sign = signs_list[sixth_idx]
                            
                            rectangle_sign_6_6 = rectangle_sign_5_6 * sixth_sign
                            total_6_6 += 1
                            if rectangle_sign_6_6 > 0:
                                positive_6_6 += 1
                            else:
                                negative_6_6 += 1
                        else:
                            print(f"     WARNING: Found {num_completions} completion rows, expected 1")
                    else:
                        print(f"     WARNING: No valid completion row found")
    
    print(f"✅ Truly optimized completion optimization complete:")
    print(f"   (5,6): {total_5_6:,} rectangles (+{positive_5_6:,} -{negative_5_6:,})")
    print(f"   (6,6): {total_6_6:,} rectangles (+{positive_6_6:,} -{negative_6_6:,})")
    
    # Verify the bijection theorem
    if total_5_6 == total_6_6:
        print(f"✅ Bijection theorem verified: NLR(5,6) = NLR(6,6) = {total_5_6:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR(5,6) = {total_5_6:,} ≠ NLR(6,6) = {total_6_6:,}")
    
    return ((total_5_6, positive_5_6, negative_5_6), (total_6_6, positive_6_6, negative_6_6))


def _count_5_6_with_completion_truly_optimized_json(cache) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Truly optimized completion - JSON cache version."""
    
    n = 6
    
    derangements_with_signs = cache.get_all_derangements_with_signs()
    num_derangements = len(derangements_with_signs)
    
    print(f"   🚀 Using JSON cache fallback: {num_derangements:,} derangements")
    print(f"   🔢 Using bitwise operations for {num_derangements}-bit bitsets")
    
    # Pre-compute conflict bitsets (EXACT same as main trunk)
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
    
    # Counters for (5,6) and (6,6) rectangles
    total_5_6 = 0
    positive_5_6 = 0
    negative_5_6 = 0
    total_6_6 = 0
    positive_6_6 = 0
    negative_6_6 = 0
    
    # First row is identity [1,2,3,4,5,6] with sign +1
    first_sign = 1
    first_row = list(range(1, n + 1))
    
    # Pre-compute completion mask after first row
    completion_mask_after_first = all_valid_mask
    for pos in range(n):
        completion_mask_after_first &= ~conflict_masks[(pos, first_row[pos])]
    
    # EXACT main trunk algorithm for r=5 with INCREMENTAL completion mask
    for second_idx in range(num_derangements):
        second_row, second_sign = derangements_with_signs[second_idx]
        if hasattr(second_row, 'tolist'):
            second_row = second_row.tolist()
        else:
            second_row = list(second_row)
        
        # Update completion mask after second row (INCREMENTAL)
        completion_mask_after_second = completion_mask_after_first
        for pos in range(n):
            completion_mask_after_second &= ~conflict_masks[(pos, second_row[pos])]
        
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
            
            # Update completion mask after third row (INCREMENTAL)
            completion_mask_after_third = completion_mask_after_second
            for pos in range(n):
                completion_mask_after_third &= ~conflict_masks[(pos, third_row[pos])]
            
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
                
                # Update completion mask after fourth row (INCREMENTAL)
                completion_mask_after_fourth = completion_mask_after_third
                for pos in range(n):
                    completion_mask_after_fourth &= ~conflict_masks[(pos, fourth_row[pos])]
                
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
                    
                    # TRULY OPTIMIZED COMPLETION: Just 6 more operations
                    completion_mask_final = completion_mask_after_fourth
                    for pos in range(n):
                        completion_mask_final &= ~conflict_masks[(pos, fifth_row[pos])]
                    
                    # There should be exactly one valid completion row
                    if completion_mask_final != 0:
                        num_completions = bin(completion_mask_final).count('1')
                        if num_completions == 1:
                            sixth_idx = (completion_mask_final & -completion_mask_final).bit_length() - 1
                            _, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            rectangle_sign_6_6 = rectangle_sign_5_6 * sixth_sign
                            total_6_6 += 1
                            if rectangle_sign_6_6 > 0:
                                positive_6_6 += 1
                            else:
                                negative_6_6 += 1
                        else:
                            print(f"     WARNING: Found {num_completions} completion rows, expected 1")
                    else:
                        print(f"     WARNING: No valid completion row found")
    
    print(f"✅ Truly optimized completion optimization complete:")
    print(f"   (5,6): {total_5_6:,} rectangles (+{positive_5_6:,} -{negative_5_6:,})")
    print(f"   (6,6): {total_6_6:,} rectangles (+{positive_6_6:,} -{negative_6_6:,})")
    
    # Verify the bijection theorem
    if total_5_6 == total_6_6:
        print(f"✅ Bijection theorem verified: NLR(5,6) = NLR(6,6) = {total_5_6:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR(5,6) = {total_5_6:,} ≠ NLR(6,6) = {total_6_6:,}")
    
    return ((total_5_6, positive_5_6, negative_5_6), (total_6_6, positive_6_6, negative_6_6))


if __name__ == "__main__":
    print("🧪 Testing TRULY OPTIMIZED Completion Optimization for (5,6) → (6,6)")
    print("=" * 70)
    
    try:
        start_time = time.time()
        result = count_rectangles_5_6_with_completion_truly_optimized()
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