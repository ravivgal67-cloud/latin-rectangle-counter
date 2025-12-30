#!/usr/bin/env python3
"""
INCREMENTAL completion optimization - build completion mask as we build the rectangle.

The key insight: Compute the completion mask incrementally as we build the rectangle,
not as a separate step afterward. This should achieve true minimal overhead.

Algorithm:
1. Start with completion_mask = all_valid_mask after row 1 (identity)
2. As we iterate through rows 2,3,4,5, update completion_mask incrementally
3. When we find a complete (5,6) rectangle, completion_mask is already computed
4. Just do one lookup to get the completion row and sign
"""

import time
from typing import List, Tuple, Optional
from core.smart_derangement_cache import get_smart_derangement_cache


def count_rectangles_5_6_with_completion_incremental() -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (5,6) and (6,6) rectangles using INCREMENTAL completion mask building.
    
    Returns:
        Tuple of ((total_5_6, pos_5_6, neg_5_6), (total_6_6, pos_6_6, neg_6_6))
    """
    
    r, n = 5, 6
    
    print(f"🚀 Starting INCREMENTAL completion optimization for (5,6) → (6,6)")
    print(f"   Building completion mask incrementally as we build rectangles")
    
    # Use the same cache loading as main trunk
    cache = get_smart_derangement_cache(n)
    
    # Check if we have the optimized binary cache
    if hasattr(cache, 'get_bitwise_data') and hasattr(cache, 'get_derangement_value'):
        return _count_5_6_with_completion_incremental_binary(cache)
    else:
        return _count_5_6_with_completion_incremental_json(cache)


def _count_5_6_with_completion_incremental_binary(cache) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Incremental completion - binary cache version."""
    
    n = 6
    
    # Get pre-computed bitwise data
    conflict_masks, all_valid_mask = cache.get_bitwise_data()
    
    # Convert NumPy arrays to Python lists
    derangements_lists = []
    signs_list = []
    
    for i in range(len(cache.derangements)):
        derangements_lists.append(cache.derangements[i].tolist())
        signs_list.append(int(cache.signs[i]))
    
    num_derangements = len(derangements_lists)
    
    print(f"   🚀 Using binary cache with Python list conversion: {num_derangements:,} derangements")
    print(f"   🔢 Using bitwise operations for {num_derangements}-bit bitsets")
    
    # Counters
    total_5_6 = 0
    positive_5_6 = 0
    negative_5_6 = 0
    total_6_6 = 0
    positive_6_6 = 0
    negative_6_6 = 0
    
    # First row is identity [1,2,3,4,5,6] with sign +1
    first_sign = 1
    first_row = list(range(1, n + 1))
    
    # Initialize completion mask after first row
    completion_mask_level_1 = all_valid_mask
    for pos in range(n):
        completion_mask_level_1 &= ~conflict_masks[(pos, first_row[pos])]
    
    # INCREMENTAL algorithm: build completion mask as we build rectangle
    for second_idx in range(num_derangements):
        second_row = derangements_lists[second_idx]
        second_sign = signs_list[second_idx]
        
        # Update completion mask after adding second row (INCREMENTAL)
        completion_mask_level_2 = completion_mask_level_1
        for pos in range(n):
            completion_mask_level_2 &= ~conflict_masks[(pos, second_row[pos])]
        
        # Standard rectangle building (same as main trunk)
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
            
            # Update completion mask after adding third row (INCREMENTAL)
            completion_mask_level_3 = completion_mask_level_2
            for pos in range(n):
                completion_mask_level_3 &= ~conflict_masks[(pos, third_row[pos])]
            
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
                
                # Update completion mask after adding fourth row (INCREMENTAL)
                completion_mask_level_4 = completion_mask_level_3
                for pos in range(n):
                    completion_mask_level_4 &= ~conflict_masks[(pos, fourth_row[pos])]
                
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
                    
                    # MINIMAL COMPLETION: completion mask is already built incrementally!
                    # Just need to apply conflicts from the fifth row (6 operations total)
                    completion_mask_final = completion_mask_level_4
                    fifth_row = derangements_lists[fifth_idx]
                    for pos in range(n):
                        completion_mask_final &= ~conflict_masks[(pos, fifth_row[pos])]
                    
                    # Find the unique completion row (should be exactly one)
                    if completion_mask_final != 0:
                        num_completions = bin(completion_mask_final).count('1')
                        if num_completions == 1:
                            # Get completion row index and sign (2 operations total)
                            sixth_idx = (completion_mask_final & -completion_mask_final).bit_length() - 1
                            sixth_sign = signs_list[sixth_idx]
                            
                            # Count (6,6) rectangle
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
    
    print(f"✅ Incremental completion optimization complete:")
    print(f"   (5,6): {total_5_6:,} rectangles (+{positive_5_6:,} -{negative_5_6:,})")
    print(f"   (6,6): {total_6_6:,} rectangles (+{positive_6_6:,} -{negative_6_6:,})")
    
    # Verify the bijection theorem
    if total_5_6 == total_6_6:
        print(f"✅ Bijection theorem verified: NLR(5,6) = NLR(6,6) = {total_5_6:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR(5,6) = {total_5_6:,} ≠ NLR(6,6) = {total_6_6:,}")
    
    return ((total_5_6, positive_5_6, negative_5_6), (total_6_6, positive_6_6, negative_6_6))


def _count_5_6_with_completion_incremental_json(cache) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Incremental completion - JSON cache version."""
    
    n = 6
    
    derangements_with_signs = cache.get_all_derangements_with_signs()
    num_derangements = len(derangements_with_signs)
    
    print(f"   🚀 Using JSON cache fallback: {num_derangements:,} derangements")
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
    
    # Initialize completion mask after first row
    completion_mask_level_1 = all_valid_mask
    for pos in range(n):
        completion_mask_level_1 &= ~conflict_masks[(pos, first_row[pos])]
    
    # INCREMENTAL algorithm
    for second_idx in range(num_derangements):
        second_row, second_sign = derangements_with_signs[second_idx]
        if hasattr(second_row, 'tolist'):
            second_row = second_row.tolist()
        else:
            second_row = list(second_row)
        
        # Update completion mask after adding second row
        completion_mask_level_2 = completion_mask_level_1
        for pos in range(n):
            completion_mask_level_2 &= ~conflict_masks[(pos, second_row[pos])]
        
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
            
            # Update completion mask after adding third row
            completion_mask_level_3 = completion_mask_level_2
            for pos in range(n):
                completion_mask_level_3 &= ~conflict_masks[(pos, third_row[pos])]
            
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
                
                # Update completion mask after adding fourth row
                completion_mask_level_4 = completion_mask_level_3
                for pos in range(n):
                    completion_mask_level_4 &= ~conflict_masks[(pos, fourth_row[pos])]
                
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
                    
                    # MINIMAL COMPLETION: just apply fifth row conflicts
                    completion_mask_final = completion_mask_level_4
                    for pos in range(n):
                        completion_mask_final &= ~conflict_masks[(pos, fifth_row[pos])]
                    
                    # Find the unique completion row
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
    
    print(f"✅ Incremental completion optimization complete:")
    print(f"   (5,6): {total_5_6:,} rectangles (+{positive_5_6:,} -{negative_5_6:,})")
    print(f"   (6,6): {total_6_6:,} rectangles (+{positive_6_6:,} -{negative_6_6:,})")
    
    # Verify the bijection theorem
    if total_5_6 == total_6_6:
        print(f"✅ Bijection theorem verified: NLR(5,6) = NLR(6,6) = {total_5_6:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR(5,6) = {total_5_6:,} ≠ NLR(6,6) = {total_6_6:,}")
    
    return ((total_5_6, positive_5_6, negative_5_6), (total_6_6, positive_6_6, negative_6_6))


if __name__ == "__main__":
    print("🧪 Testing INCREMENTAL Completion Optimization for (5,6) → (6,6)")
    print("=" * 70)
    
    try:
        start_time = time.time()
        result = count_rectangles_5_6_with_completion_incremental()
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