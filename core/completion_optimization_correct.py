#!/usr/bin/env python3
"""
Correct completion optimization implementation following the mathematical theory.

Based on the bijection theorem: NLR(n-1, n) = NLR(n, n)
Key insight: Every (n-1, n) rectangle has exactly one completion to an (n, n) square.

This implementation follows the mathematical approach described in 
docs/nlr_n_minus_1_n_equality_and_parity.md
"""

import time
from typing import List, Tuple, Optional
from core.smart_derangement_cache import get_smart_derangement_cache


def count_rectangles_with_completion_bitwise(r: int, n: int) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (r,n) and (r+1,n) rectangles using completion optimization.
    
    This function implements the bijection theorem: for every (n-1, n) rectangle,
    there exists exactly one completion row that makes it an (n, n) square.
    
    Args:
        r: Number of rows (must equal n-1)
        n: Number of columns
        
    Returns:
        Tuple of ((total_r, pos_r, neg_r), (total_r_plus_1, pos_r_plus_1, neg_r_plus_1))
    """
    
    if r != n - 1:
        raise ValueError(f"Completion optimization requires r = n-1, got r={r}, n={n}")
    
    print(f"🚀 Starting completion optimization for ({r},{n}) -> ({n},{n})")
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
    
    # Use the main trunk ultra-safe bitwise structure but with completion logic
    if r == 2:  # Computing (2,3) and (3,3)
        for second_idx in range(len(derangements_with_signs)):
            second_row, second_sign = derangements_with_signs[second_idx]
            
            # Count the (2,3) rectangle
            rectangle_sign_r = first_sign * second_sign
            total_r += 1
            if rectangle_sign_r > 0:
                positive_r += 1
            else:
                negative_r += 1
            
            # Find all valid completion rows (third rows) using the same logic as main trunk
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            # Count all valid third rows (completion rows)
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                _, third_sign = derangements_with_signs[third_idx]
                
                # Count the (3,3) rectangle: (2,3) sign * third row sign
                rectangle_sign_r_plus_1 = rectangle_sign_r * third_sign
                total_r_plus_1 += 1
                if rectangle_sign_r_plus_1 > 0:
                    positive_r_plus_1 += 1
                else:
                    negative_r_plus_1 += 1
    
    elif r == 3:  # Computing (3,4) and (4,4)
        for second_idx in range(len(derangements_with_signs)):
            second_row, second_sign = derangements_with_signs[second_idx]
            
            # Calculate valid third rows
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
                
                # Count the (3,4) rectangle
                rectangle_sign_r = first_sign * second_sign * third_sign
                total_r += 1
                if rectangle_sign_r > 0:
                    positive_r += 1
                else:
                    negative_r += 1
                
                # Find all valid completion rows (fourth rows) using the same logic as main trunk
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                # Count all valid fourth rows (completion rows)
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    _, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    # Count the (4,4) rectangle: (3,4) sign * fourth row sign
                    rectangle_sign_r_plus_1 = rectangle_sign_r * fourth_sign
                    total_r_plus_1 += 1
                    if rectangle_sign_r_plus_1 > 0:
                        positive_r_plus_1 += 1
                    else:
                        negative_r_plus_1 += 1
    
    elif r == 4:  # Computing (4,5) and (5,5)
        for second_idx in range(len(derangements_with_signs)):
            second_row, second_sign = derangements_with_signs[second_idx]
            
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
                        
                        # Count the (4,5) rectangle
                        rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        total_r += 1
                        if rectangle_sign_r > 0:
                            positive_r += 1
                        else:
                            negative_r += 1
                        
                        # Find all valid completion rows (sixth rows) using the same logic as main trunk
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        
                        # Count all valid sixth rows (completion rows)
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            _, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            # Count the (5,5) rectangle: (4,5) sign * sixth row sign
                            rectangle_sign_r_plus_1 = rectangle_sign_r * sixth_sign
                            total_r_plus_1 += 1
                            if rectangle_sign_r_plus_1 > 0:
                                positive_r_plus_1 += 1
                            else:
                                negative_r_plus_1 += 1
    
    elif r == 5:  # Computing (5,6) and (6,6)
        for second_idx in range(len(derangements_with_signs)):
            second_row, second_sign = derangements_with_signs[second_idx]
            
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
                        
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        
                        if sixth_row_valid == 0:
                            continue
                        
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            sixth_row, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            # Count the (5,6) rectangle
                            rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign
                            total_r += 1
                            if rectangle_sign_r > 0:
                                positive_r += 1
                            else:
                                negative_r += 1
                            
                            # Find all valid completion rows (seventh rows) using the same logic as main trunk
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            
                            # Count all valid seventh rows (completion rows)
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                _, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                # Count the (6,6) rectangle: (5,6) sign * seventh row sign
                                rectangle_sign_r_plus_1 = rectangle_sign_r * seventh_sign
                                total_r_plus_1 += 1
                                if rectangle_sign_r_plus_1 > 0:
                                    positive_r_plus_1 += 1
                                else:
                                    negative_r_plus_1 += 1
    
    else:
        raise NotImplementedError(f"Completion optimization not implemented for r={r}")
    
    print(f"✅ Completion optimization complete:")
    print(f"   ({r},{n}): {total_r:,} rectangles (+{positive_r:,} -{negative_r:,})")
    print(f"   ({n},{n}): {total_r_plus_1:,} rectangles (+{positive_r_plus_1:,} -{negative_r_plus_1:,})")
    
    # Verify the bijection theorem
    if total_r == total_r_plus_1:
        print(f"✅ Bijection theorem verified: NLR({r},{n}) = NLR({n},{n}) = {total_r:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR({r},{n}) = {total_r:,} ≠ NLR({n},{n}) = {total_r_plus_1:,}")
    
    return ((total_r, positive_r, negative_r), (total_r_plus_1, positive_r_plus_1, negative_r_plus_1))


def test_completion_optimization():
    """Test the completion optimization implementation."""
    
    print("🧪 Testing Completion Optimization Implementation")
    print("=" * 60)
    
    test_cases = [
        (2, 3),
        (3, 4), 
        (4, 5),
        (5, 6),
    ]
    
    for r, n in test_cases:
        print(f"\n--- Testing ({r},{n}) -> ({n},{n}) ---")
        
        try:
            start_time = time.time()
            (total_r, pos_r, neg_r), (total_r_plus_1, pos_r_plus_1, neg_r_plus_1) = \
                count_rectangles_with_completion_bitwise(r, n)
            elapsed = time.time() - start_time
            
            print(f"Time: {elapsed:.4f}s")
            
            # Verify against known values if available
            known_values = {
                (2, 3): (2, 2),  # (2,3) and (3,3) both have 2 rectangles
                (3, 4): (24, 24),  # (3,4) and (4,4) both have 24 rectangles
                (4, 5): (1344, 1344),  # (4,5) and (5,5) both have 1344 rectangles
                (5, 6): (1128960, 1128960),  # (5,6) and (6,6) both have 1,128,960 rectangles
            }
            
            if (r, n) in known_values:
                expected_r, expected_r_plus_1 = known_values[(r, n)]
                if total_r == expected_r and total_r_plus_1 == expected_r_plus_1:
                    print(f"✅ Results match known values")
                else:
                    print(f"❌ Results don't match known values:")
                    print(f"   Expected: ({r},{n})={expected_r:,}, ({n},{n})={expected_r_plus_1:,}")
                    print(f"   Got:      ({r},{n})={total_r:,}, ({n},{n})={total_r_plus_1:,}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_completion_optimization()