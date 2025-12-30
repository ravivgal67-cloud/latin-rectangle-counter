#!/usr/bin/env python3
"""
CORRECT completion optimization implementation following the mathematical theory.

The key insight: We need to generate (r,n) rectangles (r rows, n columns) and then
find their unique completion to (r+1,n) rectangles.

For (4,5) -> (5,5): Generate 4-row rectangles, then add the 5th completion row.
For (5,6) -> (6,6): Generate 5-row rectangles, then add the 6th completion row.
"""

import time
from typing import List, Tuple, Optional
from core.smart_derangement_cache import get_smart_derangement_cache


def count_rectangles_with_completion_bitwise(r: int, n: int) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (r,n) and (r+1,n) rectangles using completion optimization.
    
    This function implements the bijection theorem: for every (r, n) rectangle,
    there exists exactly one completion row that makes it an (r+1, n) rectangle.
    
    Args:
        r: Number of rows (must equal n-1)
        n: Number of columns
        
    Returns:
        Tuple of ((total_r, pos_r, neg_r), (total_r_plus_1, pos_r_plus_1, neg_r_plus_1))
    """
    
    if r != n - 1:
        raise ValueError(f"Completion optimization requires r = n-1, got r={r}, n={n}")
    
    print(f"🚀 Starting completion optimization for ({r},{n}) -> ({r+1},{n})")
    print(f"   Using bijection theorem: every ({r},{n}) rectangle has exactly one completion")
    
    # Get smart derangement cache
    cache = get_smart_derangement_cache(n)
    derangements_with_signs = cache.get_all_derangements_with_signs()
    position_value_index = cache.position_value_index
    
    # Pre-compute conflict masks for bitwise operations
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
    
    all_valid_mask = (1 << len(derangements_with_signs)) - 1
    
    # Counters for (r, n) and (r+1, n)
    total_r = 0
    positive_r = 0
    negative_r = 0
    total_r_plus_1 = 0
    positive_r_plus_1 = 0
    negative_r_plus_1 = 0
    
    first_sign = 1  # Identity permutation
    
    # Create a lookup table for derangement signs
    derangement_sign_lookup = {}
    for derang, sign in derangements_with_signs:
        derang_tuple = tuple(derang.tolist() if hasattr(derang, 'tolist') else derang)
        derangement_sign_lookup[derang_tuple] = sign
    
    # Generate (r,n) rectangles and find their completions
    if r == 2:  # Computing (2,3) and (3,3)
        # Generate all (2,3) rectangles: identity + one derangement
        for second_idx in range(len(derangements_with_signs)):
            second_row, second_sign = derangements_with_signs[second_idx]
            
            # Convert to list if needed
            if hasattr(second_row, 'tolist'):
                second_row = second_row.tolist()
            else:
                second_row = list(second_row)
            
            # This is a complete (2,3) rectangle
            rectangle_sign_r = first_sign * second_sign
            total_r += 1
            if rectangle_sign_r > 0:
                positive_r += 1
            else:
                negative_r += 1
            
            # Find the unique completion row for (3,3)
            first_row = list(range(1, n + 1))  # Identity permutation
            completion_row = []
            for col in range(n):
                used_values = {first_row[col], second_row[col]}
                missing_values = set(range(1, n + 1)) - used_values
                if len(missing_values) == 1:
                    completion_row.append(missing_values.pop())
                else:
                    completion_row = None
                    break
            
            if completion_row is not None:
                completion_tuple = tuple(completion_row)
                completion_sign = derangement_sign_lookup.get(completion_tuple)
                
                if completion_sign is not None:
                    rectangle_sign_r_plus_1 = rectangle_sign_r * completion_sign
                    total_r_plus_1 += 1
                    if rectangle_sign_r_plus_1 > 0:
                        positive_r_plus_1 += 1
                    else:
                        negative_r_plus_1 += 1
    
    elif r == 3:  # Computing (3,4) and (4,4)
        # Generate all (3,4) rectangles: identity + two derangements
        for second_idx in range(len(derangements_with_signs)):
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
                
                # This is a complete (3,4) rectangle
                rectangle_sign_r = first_sign * second_sign * third_sign
                total_r += 1
                if rectangle_sign_r > 0:
                    positive_r += 1
                else:
                    negative_r += 1
                
                # Find the unique completion row for (4,4)
                first_row = list(range(1, n + 1))  # Identity permutation
                completion_row = []
                for col in range(n):
                    used_values = {first_row[col], second_row[col], third_row[col]}
                    missing_values = set(range(1, n + 1)) - used_values
                    if len(missing_values) == 1:
                        completion_row.append(missing_values.pop())
                    else:
                        completion_row = None
                        break
                
                if completion_row is not None:
                    completion_tuple = tuple(completion_row)
                    completion_sign = derangement_sign_lookup.get(completion_tuple)
                    
                    if completion_sign is not None:
                        rectangle_sign_r_plus_1 = rectangle_sign_r * completion_sign
                        total_r_plus_1 += 1
                        if rectangle_sign_r_plus_1 > 0:
                            positive_r_plus_1 += 1
                        else:
                            negative_r_plus_1 += 1
    
    elif r == 4:  # Computing (4,5) and (5,5)
        # Generate all (4,5) rectangles: identity + three derangements (4 rows total)
        for second_idx in range(len(derangements_with_signs)):
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
                    
                    # STOP HERE - This is a complete (4,5) rectangle (4 rows, 5 columns)
                    rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign
                    total_r += 1
                    if rectangle_sign_r > 0:
                        positive_r += 1
                    else:
                        negative_r += 1
                    
                    # Find the unique completion row for (5,5)
                    first_row = list(range(1, n + 1))  # Identity permutation
                    completion_row = []
                    for col in range(n):
                        used_values = {first_row[col], second_row[col], third_row[col], fourth_row[col]}
                        missing_values = set(range(1, n + 1)) - used_values
                        if len(missing_values) == 1:
                            completion_row.append(missing_values.pop())
                        else:
                            completion_row = None
                            break
                    
                    if completion_row is not None:
                        completion_tuple = tuple(completion_row)
                        completion_sign = derangement_sign_lookup.get(completion_tuple)
                        
                        if completion_sign is not None:
                            rectangle_sign_r_plus_1 = rectangle_sign_r * completion_sign
                            total_r_plus_1 += 1
                            if rectangle_sign_r_plus_1 > 0:
                                positive_r_plus_1 += 1
                            else:
                                negative_r_plus_1 += 1
    
    elif r == 5:  # Computing (5,6) and (6,6)
        # Generate all (5,6) rectangles: identity + four derangements (5 rows total)
        for second_idx in range(len(derangements_with_signs)):
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
                    
                    if fifth_row_valid == 0:
                        continue
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_row, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        if hasattr(fifth_row, 'tolist'):
                            fifth_row = fifth_row.tolist()
                        else:
                            fifth_row = list(fifth_row)
                        
                        # STOP HERE - This is a complete (5,6) rectangle (5 rows, 6 columns)
                        rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        total_r += 1
                        if rectangle_sign_r > 0:
                            positive_r += 1
                        else:
                            negative_r += 1
                        
                        # Find the unique completion row for (6,6)
                        first_row = list(range(1, n + 1))  # Identity permutation
                        completion_row = []
                        for col in range(n):
                            used_values = {first_row[col], second_row[col], third_row[col], fourth_row[col], fifth_row[col]}
                            missing_values = set(range(1, n + 1)) - used_values
                            if len(missing_values) == 1:
                                completion_row.append(missing_values.pop())
                            else:
                                completion_row = None
                                break
                        
                        if completion_row is not None:
                            completion_tuple = tuple(completion_row)
                            completion_sign = derangement_sign_lookup.get(completion_tuple)
                            
                            if completion_sign is not None:
                                rectangle_sign_r_plus_1 = rectangle_sign_r * completion_sign
                                total_r_plus_1 += 1
                                if rectangle_sign_r_plus_1 > 0:
                                    positive_r_plus_1 += 1
                                else:
                                    negative_r_plus_1 += 1
    
    else:
        raise NotImplementedError(f"Completion optimization not implemented for r={r}")
    
    print(f"✅ Completion optimization complete:")
    print(f"   ({r},{n}): {total_r:,} rectangles (+{positive_r:,} -{negative_r:,})")
    print(f"   ({r+1},{n}): {total_r_plus_1:,} rectangles (+{positive_r_plus_1:,} -{negative_r_plus_1:,})")
    
    # Verify the bijection theorem
    if total_r == total_r_plus_1:
        print(f"✅ Bijection theorem verified: NLR({r},{n}) = NLR({r+1},{n}) = {total_r:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR({r},{n}) = {total_r:,} ≠ NLR({r+1},{n}) = {total_r_plus_1:,}")
    
    return ((total_r, positive_r, negative_r), (total_r_plus_1, positive_r_plus_1, negative_r_plus_1))


if __name__ == "__main__":
    # Test the implementation
    test_cases = [(2, 3), (3, 4), (4, 5), (5, 6)]
    
    for r, n in test_cases:
        print(f"\n--- Testing ({r},{n}) -> ({r+1},{n}) ---")
        try:
            start_time = time.time()
            result = count_rectangles_with_completion_bitwise(r, n)
            elapsed = time.time() - start_time
            print(f"Time: {elapsed:.4f}s")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()