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
    
    # Special case: r=2 uses efficient derangement formula (no cache needed)
    if r == 2:
        print(f"   ⚡ Using derangement formula for r=2 (no cache needed)")
        from core.permutation import count_derangements
        
        # Compute total derangements
        total_count = count_derangements(n)
        
        # Compute difference using closed-form formula
        # diff = det(J_n - I_n) = (-1)^(n-1) * (n-1)
        diff = ((-1) ** (n - 1)) * (n - 1)
        
        # Solve for positive and negative counts
        positive_count = (total_count + diff) // 2
        negative_count = (total_count - diff) // 2
        
        return total_count, positive_count, negative_count
    
    # For r >= 3, use smart derangement cache
    # Use get_smart_derangement_cache to avoid double-loading
    from core.smart_derangement_cache import get_smart_derangement_cache
    cache = get_smart_derangement_cache(n)
    
    # Check if we have the optimized binary cache with pre-computed bitwise data
    if hasattr(cache, 'get_bitwise_data') and hasattr(cache, 'get_derangement_value'):
        return _count_rectangles_with_binary_cache(r, n, cache)
    else:
        return _count_rectangles_with_json_cache(r, n, cache)


def count_rectangles_ultra_safe_bitwise_constrained(r: int, n: int, 
                                                   first_column: List[int],
                                                   initial_valid_mask: Optional[int] = None) -> Tuple[int, int]:
    """
    Ultra-safe rectangle counting with bitwise operations and first column constraints.
    
    Optimized version that pre-filters derangements to only those matching first column constraints,
    then uses the original bitwise algorithm on the much smaller filtered set.
    
    Args:
        r: Number of rows
        n: Number of columns  
        first_column: Fixed first column values [1, a2, a3, ..., ar]
        initial_valid_mask: Pre-computed valid derangement mask (optional optimization)
        
    Returns:
        Tuple of (positive_count, negative_count)
    """
    
    # Validate parameters
    if r < 2:
        raise ValueError(f"r must be >= 2, got r={r}")
    if r > n:
        raise ValueError(f"r must be <= n, got r={r}, n={n}")
    if len(first_column) != r:
        raise ValueError(f"first_column must have length r={r}, got {len(first_column)}")
    if first_column[0] != 1:
        raise ValueError(f"first_column must start with 1, got {first_column[0]}")
    
    # Special case: r=2 - just count the single rectangle
    if r == 2:
        a = first_column[1]
        rectangle_sign = (-1) ** (a - 1)
        if rectangle_sign > 0:
            return 1, 0
        else:
            return 0, 1
    
    # For r >= 3, use smart derangement cache with pre-filtering optimization
    from core.smart_derangement_cache import get_smart_derangement_cache
    cache = get_smart_derangement_cache(n)
    
    # Get derangements and create filtered sets for each row
    if hasattr(cache, 'get_bitwise_data'):
        return _count_rectangles_constrained_binary_cache(r, n, first_column, cache)
    else:
        return _count_rectangles_constrained_json_cache(r, n, first_column, cache)


def _count_rectangles_constrained_binary_cache(r: int, n: int, first_column: List[int], cache) -> Tuple[int, int]:
    """Constrained counting using binary cache with pre-filtered derangement sets."""
    
    # Get pre-computed bitwise data
    conflict_masks, all_valid_mask = cache.get_bitwise_data()
    
    # Convert to lists for easier processing
    all_derangements = []
    all_signs = []
    
    for i in range(len(cache.derangements)):
        all_derangements.append(cache.derangements[i].tolist())
        all_signs.append(int(cache.signs[i]))
    
    total_derangements = len(all_derangements)
    
    # PRE-FILTER: Create filtered derangement sets for each row based on first column constraints
    filtered_sets = []
    
    for row_idx in range(1, r):  # rows 1 to r-1 (second row to last row)
        required_start_value = first_column[row_idx]
        filtered_indices = []
        filtered_derangements = []
        filtered_signs = []
        
        for orig_idx, (derangement, sign) in enumerate(zip(all_derangements, all_signs)):
            if derangement[0] == required_start_value:
                filtered_indices.append(orig_idx)
                filtered_derangements.append(derangement)
                filtered_signs.append(sign)
        
        filtered_sets.append({
            'indices': filtered_indices,
            'derangements': filtered_derangements,
            'signs': filtered_signs
        })
        
        reduction = total_derangements / len(filtered_indices) if len(filtered_indices) > 0 else float('inf')
        print(f"   Row {row_idx+1}: {len(filtered_indices)}/{total_derangements} candidates ({reduction:.1f}x reduction)")
    
    # Create remapped conflict masks for the filtered sets
    def create_filtered_conflict_masks(filtered_set, pos, val):
        """Create conflict mask for filtered derangement set."""
        mask = 0
        original_conflicts = conflict_masks.get((pos, val), 0)
        
        for new_idx, orig_idx in enumerate(filtered_set['indices']):
            if original_conflicts & (1 << orig_idx):
                mask |= (1 << new_idx)
        
        return mask
    
    positive_count = 0
    negative_count = 0
    first_sign = 1
    
    # Use original bitwise algorithm structure with filtered sets
    if r == 3:
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        
        for second_idx in range(len(second_set['derangements'])):
            second_row = second_set['derangements'][second_idx]
            second_sign = second_set['signs'][second_idx]
            
            # Calculate valid third rows using filtered conflict masks
            third_row_valid = (1 << len(third_set['derangements'])) - 1  # All third rows initially valid
            
            for pos in range(n):
                conflict_mask = create_filtered_conflict_masks(third_set, pos, second_row[pos])
                third_row_valid &= ~conflict_mask
            
            # Count valid third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_sign = third_set['signs'][third_idx]
                
                rectangle_sign = first_sign * second_sign * third_sign
                if rectangle_sign > 0:
                    positive_count += 1
                else:
                    negative_count += 1
    
    elif r == 4:
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        
        for second_idx in range(len(second_set['derangements'])):
            second_row = second_set['derangements'][second_idx]
            second_sign = second_set['signs'][second_idx]
            
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(n):
                conflict_mask = create_filtered_conflict_masks(third_set, pos, second_row[pos])
                third_row_valid &= ~conflict_mask
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = third_set['derangements'][third_idx]
                third_sign = third_set['signs'][third_idx]
                
                # Calculate valid fourth rows
                fourth_row_valid = (1 << len(fourth_set['derangements'])) - 1
                for pos in range(n):
                    # Conflicts with second row
                    conflict_mask = create_filtered_conflict_masks(fourth_set, pos, second_row[pos])
                    fourth_row_valid &= ~conflict_mask
                    # Conflicts with third row
                    conflict_mask = create_filtered_conflict_masks(fourth_set, pos, third_row[pos])
                    fourth_row_valid &= ~conflict_mask
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_sign = fourth_set['signs'][fourth_idx]
                    
                    rectangle_sign = first_sign * second_sign * third_sign * fourth_sign
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
    
    elif r == 5:
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        fifth_set = filtered_sets[3]
        
        for second_idx in range(len(second_set['derangements'])):
            second_row = second_set['derangements'][second_idx]
            second_sign = second_set['signs'][second_idx]
            
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(n):
                conflict_mask = create_filtered_conflict_masks(third_set, pos, second_row[pos])
                third_row_valid &= ~conflict_mask
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = third_set['derangements'][third_idx]
                third_sign = third_set['signs'][third_idx]
                
                # Calculate valid fourth rows
                fourth_row_valid = (1 << len(fourth_set['derangements'])) - 1
                for pos in range(n):
                    conflict_mask = create_filtered_conflict_masks(fourth_set, pos, second_row[pos])
                    fourth_row_valid &= ~conflict_mask
                    conflict_mask = create_filtered_conflict_masks(fourth_set, pos, third_row[pos])
                    fourth_row_valid &= ~conflict_mask
                
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row = fourth_set['derangements'][fourth_idx]
                    fourth_sign = fourth_set['signs'][fourth_idx]
                    
                    # Calculate valid fifth rows
                    fifth_row_valid = (1 << len(fifth_set['derangements'])) - 1
                    for pos in range(n):
                        conflict_mask = create_filtered_conflict_masks(fifth_set, pos, second_row[pos])
                        fifth_row_valid &= ~conflict_mask
                        conflict_mask = create_filtered_conflict_masks(fifth_set, pos, third_row[pos])
                        fifth_row_valid &= ~conflict_mask
                        conflict_mask = create_filtered_conflict_masks(fifth_set, pos, fourth_row[pos])
                        fifth_row_valid &= ~conflict_mask
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_sign = fifth_set['signs'][fifth_idx]
                        
                        rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        if rectangle_sign > 0:
                            positive_count += 1
                        else:
                            negative_count += 1
    
    else:
        raise NotImplementedError(f"Constrained binary cache not implemented for r={r} > 5 yet")
    
    return positive_count, negative_count


def _count_rectangles_constrained_json_cache(r: int, n: int, first_column: List[int], cache) -> Tuple[int, int]:
    """Constrained counting using JSON cache with pre-filtered derangement sets."""
    
    derangements_with_signs = cache.get_all_derangements_with_signs()
    position_value_index = cache.position_value_index
    total_derangements = len(derangements_with_signs)
    
    # PRE-FILTER: Create filtered derangement sets for each row based on first column constraints
    filtered_sets = []
    
    for row_idx in range(1, r):  # rows 1 to r-1 (second row to last row)
        required_start_value = first_column[row_idx]
        filtered_indices = []
        filtered_derangements = []
        filtered_signs = []
        
        for orig_idx, (derangement, sign) in enumerate(derangements_with_signs):
            if hasattr(derangement, 'tolist'):
                derang_list = derangement.tolist()
            else:
                derang_list = list(derangement)
            
            if derang_list[0] == required_start_value:
                filtered_indices.append(orig_idx)
                filtered_derangements.append(derang_list)
                filtered_signs.append(sign)
        
        filtered_sets.append({
            'indices': filtered_indices,
            'derangements': filtered_derangements,
            'signs': filtered_signs
        })
        
        reduction = total_derangements / len(filtered_indices) if len(filtered_indices) > 0 else float('inf')
        print(f"   Row {row_idx+1}: {len(filtered_indices)}/{total_derangements} candidates ({reduction:.1f}x reduction)")
    
    # PRE-COMPUTE: Create all filtered conflict masks once (major optimization)
    filtered_conflict_masks = {}
    
    for set_idx, filtered_set in enumerate(filtered_sets):
        filtered_conflict_masks[set_idx] = {}
        
        for pos in range(n):
            for val in range(1, n + 1):
                conflict_key = (pos, val)
                mask = 0
                
                if conflict_key in position_value_index:
                    original_conflicts = set(position_value_index[conflict_key])
                    
                    for new_idx, orig_idx in enumerate(filtered_set['indices']):
                        if orig_idx in original_conflicts:
                            mask |= (1 << new_idx)
                
                filtered_conflict_masks[set_idx][conflict_key] = mask
    
    positive_count = 0
    negative_count = 0
    first_sign = 1
    
    # Use original bitwise algorithm structure with pre-computed filtered conflict masks
    if r == 3:
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        second_conflicts = filtered_conflict_masks[0]
        third_conflicts = filtered_conflict_masks[1]
        
        for second_idx in range(len(second_set['derangements'])):
            second_row = second_set['derangements'][second_idx]
            second_sign = second_set['signs'][second_idx]
            
            # Calculate valid third rows using pre-computed filtered conflict masks
            third_row_valid = (1 << len(third_set['derangements'])) - 1  # All third rows initially valid
            
            for pos in range(n):
                conflict_mask = third_conflicts[(pos, second_row[pos])]
                third_row_valid &= ~conflict_mask
            
            # Count valid third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_sign = third_set['signs'][third_idx]
                
                rectangle_sign = first_sign * second_sign * third_sign
                if rectangle_sign > 0:
                    positive_count += 1
                else:
                    negative_count += 1
    
    elif r == 4:
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        second_conflicts = filtered_conflict_masks[0]
        third_conflicts = filtered_conflict_masks[1]
        fourth_conflicts = filtered_conflict_masks[2]
        
        for second_idx in range(len(second_set['derangements'])):
            second_row = second_set['derangements'][second_idx]
            second_sign = second_set['signs'][second_idx]
            
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(n):
                conflict_mask = third_conflicts[(pos, second_row[pos])]
                third_row_valid &= ~conflict_mask
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = third_set['derangements'][third_idx]
                third_sign = third_set['signs'][third_idx]
                
                # Calculate valid fourth rows
                fourth_row_valid = (1 << len(fourth_set['derangements'])) - 1
                for pos in range(n):
                    # Conflicts with second row
                    conflict_mask = fourth_conflicts[(pos, second_row[pos])]
                    fourth_row_valid &= ~conflict_mask
                    # Conflicts with third row
                    conflict_mask = fourth_conflicts[(pos, third_row[pos])]
                    fourth_row_valid &= ~conflict_mask
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_sign = fourth_set['signs'][fourth_idx]
                    
                    rectangle_sign = first_sign * second_sign * third_sign * fourth_sign
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
    
    elif r == 5:
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        fifth_set = filtered_sets[3]
        second_conflicts = filtered_conflict_masks[0]
        third_conflicts = filtered_conflict_masks[1]
        fourth_conflicts = filtered_conflict_masks[2]
        fifth_conflicts = filtered_conflict_masks[3]
        
        for second_idx in range(len(second_set['derangements'])):
            second_row = second_set['derangements'][second_idx]
            second_sign = second_set['signs'][second_idx]
            
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(n):
                conflict_mask = third_conflicts[(pos, second_row[pos])]
                third_row_valid &= ~conflict_mask
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = third_set['derangements'][third_idx]
                third_sign = third_set['signs'][third_idx]
                
                # Calculate valid fourth rows
                fourth_row_valid = (1 << len(fourth_set['derangements'])) - 1
                for pos in range(n):
                    conflict_mask = fourth_conflicts[(pos, second_row[pos])]
                    fourth_row_valid &= ~conflict_mask
                    conflict_mask = fourth_conflicts[(pos, third_row[pos])]
                    fourth_row_valid &= ~conflict_mask
                
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row = fourth_set['derangements'][fourth_idx]
                    fourth_sign = fourth_set['signs'][fourth_idx]
                    
                    # Calculate valid fifth rows
                    fifth_row_valid = (1 << len(fifth_set['derangements'])) - 1
                    for pos in range(n):
                        conflict_mask = fifth_conflicts[(pos, second_row[pos])]
                        fifth_row_valid &= ~conflict_mask
                        conflict_mask = fifth_conflicts[(pos, third_row[pos])]
                        fifth_row_valid &= ~conflict_mask
                        conflict_mask = fifth_conflicts[(pos, fourth_row[pos])]
                        fifth_row_valid &= ~conflict_mask
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_sign = fifth_set['signs'][fifth_idx]
                        
                        rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        if rectangle_sign > 0:
                            positive_count += 1
                        else:
                            negative_count += 1
    
    elif r == 6:
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        fifth_set = filtered_sets[3]
        sixth_set = filtered_sets[4]
        second_conflicts = filtered_conflict_masks[0]
        third_conflicts = filtered_conflict_masks[1]
        fourth_conflicts = filtered_conflict_masks[2]
        fifth_conflicts = filtered_conflict_masks[3]
        sixth_conflicts = filtered_conflict_masks[4]
        
        for second_idx in range(len(second_set['derangements'])):
            second_row = second_set['derangements'][second_idx]
            second_sign = second_set['signs'][second_idx]
            
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(n):
                conflict_mask = third_conflicts[(pos, second_row[pos])]
                third_row_valid &= ~conflict_mask
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = third_set['derangements'][third_idx]
                third_sign = third_set['signs'][third_idx]
                
                # Calculate valid fourth rows
                fourth_row_valid = (1 << len(fourth_set['derangements'])) - 1
                for pos in range(n):
                    conflict_mask = fourth_conflicts[(pos, second_row[pos])]
                    fourth_row_valid &= ~conflict_mask
                    conflict_mask = fourth_conflicts[(pos, third_row[pos])]
                    fourth_row_valid &= ~conflict_mask
                
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row = fourth_set['derangements'][fourth_idx]
                    fourth_sign = fourth_set['signs'][fourth_idx]
                    
                    # Calculate valid fifth rows
                    fifth_row_valid = (1 << len(fifth_set['derangements'])) - 1
                    for pos in range(n):
                        conflict_mask = fifth_conflicts[(pos, second_row[pos])]
                        fifth_row_valid &= ~conflict_mask
                        conflict_mask = fifth_conflicts[(pos, third_row[pos])]
                        fifth_row_valid &= ~conflict_mask
                        conflict_mask = fifth_conflicts[(pos, fourth_row[pos])]
                        fifth_row_valid &= ~conflict_mask
                    
                    if fifth_row_valid == 0:
                        continue
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_row = fifth_set['derangements'][fifth_idx]
                        fifth_sign = fifth_set['signs'][fifth_idx]
                        
                        # Calculate valid sixth rows
                        sixth_row_valid = (1 << len(sixth_set['derangements'])) - 1
                        for pos in range(n):
                            conflict_mask = sixth_conflicts[(pos, second_row[pos])]
                            sixth_row_valid &= ~conflict_mask
                            conflict_mask = sixth_conflicts[(pos, third_row[pos])]
                            sixth_row_valid &= ~conflict_mask
                            conflict_mask = sixth_conflicts[(pos, fourth_row[pos])]
                            sixth_row_valid &= ~conflict_mask
                            conflict_mask = sixth_conflicts[(pos, fifth_row[pos])]
                            sixth_row_valid &= ~conflict_mask
                        
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            sixth_sign = sixth_set['signs'][sixth_idx]
                            
                            rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign
                            if rectangle_sign > 0:
                                positive_count += 1
                            else:
                                negative_count += 1
    
    else:
        raise NotImplementedError(f"Constrained JSON cache not implemented for r={r} > 6 yet")
    
    return positive_count, negative_count


def _count_rectangles_with_binary_cache(r: int, n: int, cache) -> Tuple[int, int, int]:
    """Optimized version using binary cache with Python list conversion for performance."""
    
    # Get pre-computed bitwise data
    conflict_masks, all_valid_mask = cache.get_bitwise_data()
    
    # PERFORMANCE FIX: Convert NumPy arrays to Python lists for computation
    # (Keep NumPy for storage, use Python lists for computation speed)
    derangements_lists = []
    signs_list = []
    
    for i in range(len(cache.derangements)):
        derangements_lists.append(cache.derangements[i].tolist())
        signs_list.append(int(cache.signs[i]))
    
    num_derangements = len(derangements_lists)
    
    print(f"   🚀 Using binary cache with Python list conversion: {num_derangements:,} derangements")
    print(f"   🔢 Using bitwise operations for {num_derangements}-bit bitsets")
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # First row is identity [1,2,3,...,n] with sign +1
    first_sign = 1
    
    # Use explicit nested loops for r≤6 (maximum performance)
    if r == 3:
        for second_idx in range(num_derangements):
            second_row = derangements_lists[second_idx]
            second_sign = signs_list[second_idx]
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_sign = signs_list[third_idx]
                
                rectangle_sign = first_sign * second_sign * third_sign
                total_count += 1
                if rectangle_sign > 0:
                    positive_count += 1
                else:
                    negative_count += 1
    
    elif r == 4:
        for second_idx in range(num_derangements):
            second_row = derangements_lists[second_idx]
            second_sign = signs_list[second_idx]
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
                
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_sign = signs_list[fourth_idx]
                    
                    rectangle_sign = first_sign * second_sign * third_sign * fourth_sign
                    total_count += 1
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
    
    elif r == 5:
        for second_idx in range(num_derangements):
            second_row = derangements_lists[second_idx]
            second_sign = signs_list[second_idx]
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
                    
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_sign = signs_list[fifth_idx]
                        
                        rectangle_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        total_count += 1
                        if rectangle_sign > 0:
                            positive_count += 1
                        else:
                            negative_count += 1
    
    # Add more cases for r=5,6,7... as needed
    else:
        # For now, fall back to the JSON cache version for r > 4
        return _count_rectangles_with_json_cache(r, n, cache)
    
    return total_count, positive_count, negative_count


def _count_rectangles_with_json_cache(r: int, n: int, cache) -> Tuple[int, int, int]:
    """Original version using JSON cache (fallback)."""
    
    derangements_with_signs = cache.get_all_derangements_with_signs()
    num_derangements = len(derangements_with_signs)
    
    print(f"   🚀 Using JSON cache fallback: {num_derangements:,} derangements")
    print(f"   🔢 Using bitwise operations for {num_derangements}-bit bitsets")
    
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
    
    # For r > 6, implement the rest of the original algorithm
    # (This is a simplified version - the full implementation would include all cases)
    else:
        raise NotImplementedError(f"JSON cache fallback not implemented for r={r}")
    
    return total_count, positive_count, negative_count
    
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
    
    elif r == 8:  # pragma: no cover
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
    
    elif r == 9:  # pragma: no cover
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
    
    elif r == 10:  # pragma: no cover
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






if __name__ == "__main__":
    # Test the bitwise implementation
    print("🚀 Testing BITWISE Ultra-Safe Implementation")
    print("=" * 50)
    
    test_cases = [(3, 6), (4, 6), (5, 6), (6, 6)]
    
    for r, n in test_cases:
        print(f"\nTesting ({r}, {n}):")
        start_time = time.time()
        total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
        elapsed = time.time() - start_time
        
        print(f"  Total: {total:,}")
        print(f"  Positive: {positive:,}")
        print(f"  Negative: {negative:,}")
        print(f"  Difference: {positive - negative:,}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Rate: {total/elapsed:,.0f} rectangles/second")