#!/usr/bin/env python3
"""
Completion optimization with PER-COLUMN BITWISE approach for (5,6) → (6,6).

Option 2: Use per-column bitwise vectors updated as we build the (5,6) rectangle.
This should be the most efficient approach since completion calculation becomes O(1).
"""

import time
from typing import List, Tuple, Optional
from core.first_column_enumerator import FirstColumnEnumerator
from core.smart_derangement_cache import get_smart_derangement_cache


def count_rectangles_5_6_with_completion_bitwise_column() -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (5,6) and (6,6) rectangles using completion optimization with PER-COLUMN BITWISE approach.
    
    Returns:
        Tuple of ((total_5_6, pos_5_6, neg_5_6), (total_6_6, pos_6_6, neg_6_6))
    """
    
    r, n = 5, 6
    
    print(f"🚀 Starting (5,6) → (6,6) completion optimization with PER-COLUMN BITWISE approach")
    
    # Initialize first column enumerator
    enumerator = FirstColumnEnumerator()
    first_columns = enumerator.enumerate_first_columns(r, n)
    symmetry_factor = enumerator.get_symmetry_factor(r)
    
    print(f"   First column choices: {len(first_columns):,}")
    print(f"   Symmetry factor: {symmetry_factor:,}")
    
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
    
    # Create derangement lookup for completion signs
    all_derangements = []
    all_signs = []
    derangement_lookup = {}  # Map derangement tuple to (index, sign)
    
    for i, (derang, sign) in enumerate(derangements_with_signs):
        if hasattr(derang, 'tolist'):
            derang_list = derang.tolist()
        else:
            derang_list = list(derang)
        
        all_derangements.append(derang_list)
        all_signs.append(sign)
        derangement_lookup[tuple(derang_list)] = (i, sign)
    
    print(f"   Derangement cache loaded: {len(derangements_with_signs):,} derangements")
    
    # Counters for canonical rectangles
    canonical_total_5_6 = 0
    canonical_positive_5_6 = 0
    canonical_negative_5_6 = 0
    canonical_total_6_6 = 0
    canonical_positive_6_6 = 0
    canonical_negative_6_6 = 0
    
    # Process each canonical first column
    for i, first_column in enumerate(first_columns):
        print(f"   Processing first column {i+1}/{len(first_columns)}: {first_column}")
        
        # Enumerate all (5,6) rectangles with this first column and find their completions
        col_5_6_pos, col_5_6_neg, col_6_6_pos, col_6_6_neg = _enumerate_5_6_rectangles_bitwise_column(
            first_column, all_derangements, all_signs, derangement_lookup, conflict_masks, all_valid_mask
        )
        
        canonical_total_5_6 += col_5_6_pos + col_5_6_neg
        canonical_positive_5_6 += col_5_6_pos
        canonical_negative_5_6 += col_5_6_neg
        
        canonical_total_6_6 += col_6_6_pos + col_6_6_neg
        canonical_positive_6_6 += col_6_6_pos
        canonical_negative_6_6 += col_6_6_neg
        
        print(f"     (5,6): +{col_5_6_pos} -{col_5_6_neg} = {col_5_6_pos + col_5_6_neg}")
        print(f"     (6,6): +{col_6_6_pos} -{col_6_6_neg} = {col_6_6_pos + col_6_6_neg}")
    
    # Apply symmetry factor
    total_5_6 = canonical_total_5_6 * symmetry_factor
    positive_5_6 = canonical_positive_5_6 * symmetry_factor
    negative_5_6 = canonical_negative_5_6 * symmetry_factor
    
    total_6_6 = canonical_total_6_6 * symmetry_factor
    positive_6_6 = canonical_positive_6_6 * symmetry_factor
    negative_6_6 = canonical_negative_6_6 * symmetry_factor
    
    print(f"✅ (5,6) → (6,6) completion optimization complete:")
    print(f"   Final (5,6): {total_5_6:,} rectangles (+{positive_5_6:,} -{negative_5_6:,})")
    print(f"   Final (6,6): {total_6_6:,} rectangles (+{positive_6_6:,} -{negative_6_6:,})")
    
    return ((total_5_6, positive_5_6, negative_5_6), (total_6_6, positive_6_6, negative_6_6))


def _enumerate_5_6_rectangles_bitwise_column(first_column: List[int], all_derangements: List[List[int]], 
                                           all_signs: List[int], derangement_lookup: dict,
                                           conflict_masks: dict, all_valid_mask: int) -> Tuple[int, int, int, int]:
    """
    Enumerate (5,6) rectangles using PER-COLUMN BITWISE approach for completion.
    
    Returns:
        Tuple of (pos_5_6, neg_5_6, pos_6_6, neg_6_6)
    """
    
    n = 6
    
    # Create filtered derangement sets for rows 2, 3, 4, 5 based on first column constraints
    filtered_sets = []
    
    for row_idx in range(1, 5):  # rows 1, 2, 3, 4 (second, third, fourth, fifth rows)
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
    
    # Create remapped conflict masks for the filtered sets
    def create_filtered_conflict_masks(filtered_set, pos, val):
        """Create conflict mask for filtered derangement set."""
        mask = 0
        original_conflicts = conflict_masks.get((pos, val), 0)
        
        for new_idx, orig_idx in enumerate(filtered_set['indices']):
            if original_conflicts & (1 << orig_idx):
                mask |= (1 << new_idx)
        
        return mask
    
    pos_5_6 = 0
    neg_5_6 = 0
    pos_6_6 = 0
    neg_6_6 = 0
    first_sign = 1  # Identity permutation
    first_row = list(range(1, n + 1))  # Identity permutation [1,2,3,4,5,6]
    
    # Enumerate all (5,6) rectangles with the given first column
    second_set = filtered_sets[0]
    third_set = filtered_sets[1]
    fourth_set = filtered_sets[2]
    fifth_set = filtered_sets[3]
    
    for second_idx in range(len(second_set['derangements'])):
        second_row = second_set['derangements'][second_idx]
        second_sign = second_set['signs'][second_idx]
        
        # Initialize per-column used values bitsets after adding second row
        # For each column, track which values are used (as bitset)
        column_used = []
        for col in range(n):
            used_mask = 0
            used_mask |= (1 << (first_row[col] - 1))   # Value from first row
            used_mask |= (1 << (second_row[col] - 1))  # Value from second row
            column_used.append(used_mask)
        
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
            
            # Update per-column used values after adding third row
            column_used_after_third = []
            for col in range(n):
                used_mask = column_used[col]
                used_mask |= (1 << (third_row[col] - 1))  # Value from third row
                column_used_after_third.append(used_mask)
            
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
                
                # Update per-column used values after adding fourth row
                column_used_after_fourth = []
                for col in range(n):
                    used_mask = column_used_after_third[col]
                    used_mask |= (1 << (fourth_row[col] - 1))  # Value from fourth row
                    column_used_after_fourth.append(used_mask)
                
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
                    fifth_row = fifth_set['derangements'][fifth_idx]
                    fifth_sign = fifth_set['signs'][fifth_idx]
                    
                    # This is a complete (5,6) rectangle
                    rectangle_sign_5_6 = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                    if rectangle_sign_5_6 > 0:
                        pos_5_6 += 1
                    else:
                        neg_5_6 += 1
                    
                    # PER-COLUMN BITWISE APPROACH: Calculate completion row directly from column bitsets
                    completion_row = []
                    completion_valid = True
                    
                    for col in range(n):
                        # Get used values in this column after 5 rows
                        used_mask = column_used_after_fourth[col]
                        used_mask |= (1 << (fifth_row[col] - 1))  # Value from fifth row
                        
                        # Find the missing value (should be exactly one)
                        all_values_mask = (1 << n) - 1  # All values 1-6 as bitset
                        missing_mask = all_values_mask & ~used_mask
                        
                        # Count missing values
                        num_missing = bin(missing_mask).count('1')
                        if num_missing == 1:
                            # Find the missing value
                            missing_value = (missing_mask & -missing_mask).bit_length()  # 1-indexed
                            completion_row.append(missing_value)
                        else:
                            completion_valid = False
                            break
                    
                    if completion_valid and len(completion_row) == n:
                        # Look up the completion row sign
                        completion_tuple = tuple(completion_row)
                        if completion_tuple in derangement_lookup:
                            _, completion_sign = derangement_lookup[completion_tuple]
                            
                            rectangle_sign_6_6 = rectangle_sign_5_6 * completion_sign
                            if rectangle_sign_6_6 > 0:
                                pos_6_6 += 1
                            else:
                                neg_6_6 += 1
                        else:
                            print(f"     WARNING: Completion row {completion_row} not found in derangement lookup")
                    else:
                        print(f"     WARNING: Invalid completion row calculation")
    
    return pos_5_6, neg_5_6, pos_6_6, neg_6_6


if __name__ == "__main__":
    print("🧪 Testing (5,6) → (6,6) Completion Optimization with PER-COLUMN BITWISE approach")
    print("=" * 70)
    
    try:
        start_time = time.time()
        result = count_rectangles_5_6_with_completion_bitwise_column()
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