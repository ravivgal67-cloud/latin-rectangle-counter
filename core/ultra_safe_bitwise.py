"""
Ultra-safe implementation - BITWISE VERSION

Hybrid implementation:
- Explicit nested loops for r=3,4,5,6 (maximum performance)
- Parametrized iterative approach for r≥7 (flexibility)
- Use integers as bitsets for valid/invalid derangements
- Bitwise AND/OR operations instead of array operations
"""

import time
from typing import List, Tuple, Optional
from core.smart_derangement_cache import get_smart_derangements_with_signs, SmartDerangementCache


def count_rectangles_ultra_safe_bitwise(r: int, n: int) -> Tuple[int, int, int]:
    """
    Ultra-safe rectangle counting with bitwise operations.
    
    Uses bitsets (integers) instead of boolean arrays for 10-100x faster operations.
    Hybrid approach: explicit loops for r≤6, parametrized for r≥7.
    """
    
    # Validate parameters before expensive operations
    if r < 2:
        raise ValueError(f"r must be >= 2, got r={r}")
    if r > n:
        raise ValueError(f"r must be <= n, got r={r}, n={n}")
    if r > 10:
        raise NotImplementedError(f"Ultra-safe bitwise implementation only supports r <= 10, got r={r}")
    
    # Get smart derangements with pre-computed signs
    # Use get_smart_derangement_cache to avoid double-loading
    from core.smart_derangement_cache import get_smart_derangement_cache
    cache = get_smart_derangement_cache(n)
    derangements_with_signs = cache.get_all_derangements_with_signs()
    num_derangements = len(derangements_with_signs)
    
    print(f"   🚀 Using smart derangement cache: {num_derangements:,} derangements")
    print(f"   🔢 Using bitwise operations for {num_derangements}-bit bitsets")
    
    if r == 2:
        # For r=2, just count the signs directly
        total_count = num_derangements
        positive_count = sum(1 for _, sign in derangements_with_signs if sign > 0)
        negative_count = total_count - positive_count
        return total_count, positive_count, negative_count
    
    # Pre-compute conflict bitsets for faster operations
    position_value_index = cache.position_value_index
    
    # Pre-compute conflict bitsets - each conflict set becomes a bitmask
    conflict_masks = {}
    for pos in range(n):
        for val in range(1, n + 1):
            conflict_key = (pos, val)
            if conflict_key in position_value_index:
                # Convert conflict indices to bitmask
                mask = 0
                for conflict_idx in position_value_index[conflict_key]:
                    mask |= (1 << conflict_idx)
                conflict_masks[conflict_key] = mask
            else:
                conflict_masks[conflict_key] = 0
    
    # All derangements initially valid (all bits set)
    all_valid_mask = (1 << num_derangements) - 1
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # First row is identity [1,2,3,...,n] with sign +1
    first_sign = 1
    
    # Use explicit nested loops for r≤6 (maximum performance)
    if r == 3:
        for second_idx in range(num_derangements):
            second_row, second_sign = derangements_with_signs[second_idx]
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                _, third_sign = derangements_with_signs[third_idx]
                
                rectangle_sign = first_sign * second_sign * third_sign
                total_count += 1
                if rectangle_sign > 0:
                    positive_count += 1
                else:
                    negative_count += 1
    
    elif r == 4:
        for second_idx in range(num_derangements):
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
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    _, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    rectangle_sign = first_sign * second_sign * third_sign * fourth_sign
                    total_count += 1
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
    
    elif r == 5:
        for second_idx in range(num_derangements):
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
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        _, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        total_count += 1
                        if rectangle_sign > 0:
                            positive_count += 1
                        else:
                            negative_count += 1
    
    elif r == 6:
        for second_idx in range(num_derangements):
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
                        
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            _, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign
                            total_count += 1
                            if rectangle_sign > 0:
                                positive_count += 1
                            else:
                                negative_count += 1
    
    elif r == 7:
        for second_idx in range(num_derangements):
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
                            
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                _, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign * seventh_sign
                                total_count += 1
                                if rectangle_sign > 0:
                                    positive_count += 1
                                else:
                                    negative_count += 1
    
    elif r == 8:
        for second_idx in range(num_derangements):
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
                            
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            if seventh_row_valid == 0:
                                continue
                            
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                seventh_row, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                eighth_row_valid = seventh_row_valid
                                for pos in range(n):
                                    eighth_row_valid &= ~conflict_masks[(pos, seventh_row[pos])]
                                
                                eighth_mask = eighth_row_valid
                                while eighth_mask:
                                    eighth_idx = (eighth_mask & -eighth_mask).bit_length() - 1
                                    eighth_mask &= eighth_mask - 1
                                    _, eighth_sign = derangements_with_signs[eighth_idx]
                                    
                                    rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign * seventh_sign * eighth_sign
                                    total_count += 1
                                    if rectangle_sign > 0:
                                        positive_count += 1
                                    else:
                                        negative_count += 1
    
    elif r == 9:
        for second_idx in range(num_derangements):
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
                            
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            if seventh_row_valid == 0:
                                continue
                            
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                seventh_row, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                eighth_row_valid = seventh_row_valid
                                for pos in range(n):
                                    eighth_row_valid &= ~conflict_masks[(pos, seventh_row[pos])]
                                if eighth_row_valid == 0:
                                    continue
                                
                                eighth_mask = eighth_row_valid
                                while eighth_mask:
                                    eighth_idx = (eighth_mask & -eighth_mask).bit_length() - 1
                                    eighth_mask &= eighth_mask - 1
                                    eighth_row, eighth_sign = derangements_with_signs[eighth_idx]
                                    
                                    ninth_row_valid = eighth_row_valid
                                    for pos in range(n):
                                        ninth_row_valid &= ~conflict_masks[(pos, eighth_row[pos])]
                                    
                                    ninth_mask = ninth_row_valid
                                    while ninth_mask:
                                        ninth_idx = (ninth_mask & -ninth_mask).bit_length() - 1
                                        ninth_mask &= ninth_mask - 1
                                        _, ninth_sign = derangements_with_signs[ninth_idx]
                                        
                                        rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign * seventh_sign * eighth_sign * ninth_sign
                                        total_count += 1
                                        if rectangle_sign > 0:
                                            positive_count += 1
                                        else:
                                            negative_count += 1
    
    elif r == 10:
        for second_idx in range(num_derangements):
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
                            
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            if seventh_row_valid == 0:
                                continue
                            
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                seventh_row, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                eighth_row_valid = seventh_row_valid
                                for pos in range(n):
                                    eighth_row_valid &= ~conflict_masks[(pos, seventh_row[pos])]
                                if eighth_row_valid == 0:
                                    continue
                                
                                eighth_mask = eighth_row_valid
                                while eighth_mask:
                                    eighth_idx = (eighth_mask & -eighth_mask).bit_length() - 1
                                    eighth_mask &= eighth_mask - 1
                                    eighth_row, eighth_sign = derangements_with_signs[eighth_idx]
                                    
                                    ninth_row_valid = eighth_row_valid
                                    for pos in range(n):
                                        ninth_row_valid &= ~conflict_masks[(pos, eighth_row[pos])]
                                    if ninth_row_valid == 0:
                                        continue
                                    
                                    ninth_mask = ninth_row_valid
                                    while ninth_mask:
                                        ninth_idx = (ninth_mask & -ninth_mask).bit_length() - 1
                                        ninth_mask &= ninth_mask - 1
                                        ninth_row, ninth_sign = derangements_with_signs[ninth_idx]
                                        
                                        tenth_row_valid = ninth_row_valid
                                        for pos in range(n):
                                            tenth_row_valid &= ~conflict_masks[(pos, ninth_row[pos])]
                                        
                                        tenth_mask = tenth_row_valid
                                        while tenth_mask:
                                            tenth_idx = (tenth_mask & -tenth_mask).bit_length() - 1
                                            tenth_mask &= tenth_mask - 1
                                            _, tenth_sign = derangements_with_signs[tenth_idx]
                                            
                                            rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign * seventh_sign * eighth_sign * ninth_sign * tenth_sign
                                            total_count += 1
                                            if rectangle_sign > 0:
                                                positive_count += 1
                                            else:
                                                negative_count += 1
    
    else:
        # For r>10, use parametrized iterative approach
        # Stack: (current_row, valid_mask, sign_product)
        stack = [(2, all_valid_mask, first_sign)]
        
        while stack:
            current_row, valid_mask, sign_product = stack.pop()
            
            if current_row == r:
                # Count all valid final rows
                mask = valid_mask
                while mask:
                    idx = (mask & -mask).bit_length() - 1
                    mask &= mask - 1
                    _, final_sign = derangements_with_signs[idx]
                    rectangle_sign = sign_product * final_sign
                    
                    total_count += 1
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
                continue
            
            # Process all valid derangements for current row
            valid_indices = []
            mask = valid_mask
            while mask:
                idx = (mask & -mask).bit_length() - 1
                mask &= mask - 1
                valid_indices.append(idx)
            
            # Push in reverse order for consistent ordering
            for idx in reversed(valid_indices):
                row, sign = derangements_with_signs[idx]
                
                # Calculate conflicts for next row
                next_valid_mask = valid_mask
                for pos in range(n):
                    next_valid_mask &= ~conflict_masks[(pos, row[pos])]
                
                # Early termination
                if next_valid_mask != 0:
                    stack.append((current_row + 1, next_valid_mask, sign_product * sign))
    
    return total_count, positive_count, negative_count


def count_rectangles_with_completion_bitwise(r: int, n: int) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (r, n) and (r+1, n) simultaneously using improved completion optimization.
    
    Key insight: Maintain bitwise vectors for both row r and row r+1 throughout computation.
    When we set row r, we count it AND immediately compute valid options for row r+1.
    
    This avoids the overhead of building completion rows and dictionary lookups.
    Results in 1.34x speedup for (5,6)+(6,6) compared to separate computation.
    
    Args:
        r: Number of rows (must equal n-1)
        n: Number of columns
        
    Returns:
        Tuple of ((total_r, pos_r, neg_r), (total_r_plus_1, pos_r_plus_1, neg_r_plus_1))
    """
    if r != n - 1:
        raise ValueError(f"count_rectangles_with_completion_bitwise requires r = n-1, got r={r}, n={n}")
    
    print(f"   🔗 Using improved completion optimization: computing ({r},{n}) and ({r+1},{n}) together")
    
    # Get smart derangements with pre-computed signs
    from core.smart_derangement_cache import get_smart_derangement_cache
    cache = get_smart_derangement_cache(n)
    derangements_with_signs = cache.get_all_derangements_with_signs()
    num_derangements = len(derangements_with_signs)
    
    print(f"   🚀 Using smart derangement cache: {num_derangements:,} derangements")
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
    
    # Counters for (r, n)
    total_r = 0
    positive_r = 0
    negative_r = 0
    
    # Counters for (r+1, n) = (n, n)
    total_r_plus_1 = 0
    positive_r_plus_1 = 0
    negative_r_plus_1 = 0
    
    first_sign = 1  # Identity permutation
    
    # Implementation for r = 5 (computing (5,6) and (6,6))
    if r == 5:
        for second_idx in range(num_derangements):
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
                        
                        # Count for (5, 6) - this is a complete (5,6) rectangle
                        rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        total_r += 1
                        if rectangle_sign_r > 0:
                            positive_r += 1
                        else:
                            negative_r += 1
                        
                        # Now compute valid sixth rows (for completion to (6,6))
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        
                        # Count all valid sixth rows
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            _, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            # Count for (6, 6) - this is the completed rectangle
                            rectangle_sign_r_plus_1 = rectangle_sign_r * sixth_sign
                            total_r_plus_1 += 1
                            if rectangle_sign_r_plus_1 > 0:
                                positive_r_plus_1 += 1
                            else:
                                negative_r_plus_1 += 1
    
    elif r == 4:  # Computing (4,5) and (5,5)
        for second_idx in range(num_derangements):
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
                    
                    # Count for (4, 5) - this is a complete (4,5) rectangle
                    rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign
                    total_r += 1
                    if rectangle_sign_r > 0:
                        positive_r += 1
                    else:
                        negative_r += 1
                    
                    # Now compute valid fifth rows (for completion to (5,5))
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    
                    # Count all valid fifth rows
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        _, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        # Count for (5, 5) - this is the completed rectangle
                        rectangle_sign_r_plus_1 = rectangle_sign_r * fifth_sign
                        total_r_plus_1 += 1
                        if rectangle_sign_r_plus_1 > 0:
                            positive_r_plus_1 += 1
                        else:
                            negative_r_plus_1 += 1
    
    elif r == 3:  # Computing (3,4) and (4,4)
        for second_idx in range(num_derangements):
            second_row, second_sign = derangements_with_signs[second_idx]
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                # Count for (3, 4) - this is a complete (3,4) rectangle
                rectangle_sign_r = first_sign * second_sign * third_sign
                total_r += 1
                if rectangle_sign_r > 0:
                    positive_r += 1
                else:
                    negative_r += 1
                
                # Now compute valid fourth rows (for completion to (4,4))
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                # Count all valid fourth rows
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    _, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    # Count for (4, 4) - this is the completed rectangle
                    rectangle_sign_r_plus_1 = rectangle_sign_r * fourth_sign
                    total_r_plus_1 += 1
                    if rectangle_sign_r_plus_1 > 0:
                        positive_r_plus_1 += 1
                    else:
                        negative_r_plus_1 += 1
    
    elif r == 2:  # Computing (2,3) and (3,3)
        for second_idx in range(num_derangements):
            second_row, second_sign = derangements_with_signs[second_idx]
            
            # Count for (2, 3) - this is a complete (2,3) rectangle
            rectangle_sign_r = first_sign * second_sign
            total_r += 1
            if rectangle_sign_r > 0:
                positive_r += 1
            else:
                negative_r += 1
            
            # Now compute valid third rows (for completion to (3,3))
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            # Count all valid third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                _, third_sign = derangements_with_signs[third_idx]
                
                # Count for (3, 3) - this is the completed rectangle
                rectangle_sign_r_plus_1 = rectangle_sign_r * third_sign
                total_r_plus_1 += 1
                if rectangle_sign_r_plus_1 > 0:
                    positive_r_plus_1 += 1
                else:
                    negative_r_plus_1 += 1
    
    else:
        raise ValueError(f"Completion optimization v2 not implemented for r={r}, n={n}")
    
    return ((total_r, positive_r, negative_r), (total_r_plus_1, positive_r_plus_1, negative_r_plus_1))


if __name__ == "__main__":
    # Test the bitwise implementation
    print("🚀 Testing BITWISE Ultra-Safe Implementation")
    print("=" * 50)
    
    test_cases = [(3, 6), (4, 6), (5, 6), (6, 6)]
    
    for r, n in test_cases:
        print(f"\nTesting ({r},{n}):")
        
        start_time = time.time()
        total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
        elapsed = time.time() - start_time
        
        rate = total / elapsed if elapsed > 0 else 0
        
        print(f"✅ Result: {total:,} rectangles in {elapsed:.3f}s")
        print(f"📊 Rate: {rate:,.0f} rectangles/second")
        print(f"🎯 Breakdown: +{positive:,} -{negative:,} (diff: {positive - negative:+,})")




