#!/usr/bin/env python3
"""
Completion optimization with first column optimization - FOCUSED ON (4,5) → (5,5).

This implementation combines the bijection theorem with first column optimization
specifically optimized for the (4,5) → (5,5) case.

Algorithm for (4,5) → (5,5):
1. Enumerate 4 canonical first columns: [1,2,3,4], [1,2,3,5], [1,2,4,5], [1,3,4,5]
2. For each first column, use constrained bitwise to build all (4,5) rectangles
3. For each (4,5) rectangle found, use bitwise operations to find its unique 5th completion row
4. Count both (4,5) and (5,5) rectangles in one pass
5. Apply symmetry factor 3! = 6 to get final counts
"""

import time
from typing import List, Tuple, Optional
from core.first_column_enumerator import FirstColumnEnumerator
from core.smart_derangement_cache import get_smart_derangement_cache


def count_rectangles_4_5_with_completion_and_first_column() -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (4,5) and (5,5) rectangles using completion optimization with first column optimization.
    
    Specifically optimized for the (4,5) → (5,5) case.
    
    Returns:
        Tuple of ((total_4_5, pos_4_5, neg_4_5), (total_5_5, pos_5_5, neg_5_5))
    """
    
    r, n = 4, 5
    
    print(f"🚀 Starting (4,5) → (5,5) completion optimization with first column optimization")
    
    # Initialize first column enumerator
    enumerator = FirstColumnEnumerator()
    first_columns = enumerator.enumerate_first_columns(r, n)
    symmetry_factor = enumerator.get_symmetry_factor(r)
    
    print(f"   First column choices: {len(first_columns):,} = {first_columns}")
    print(f"   Symmetry factor: {symmetry_factor:,}")
    print(f"   Total work reduction: {symmetry_factor:,}x")
    
    # Get smart derangement cache for completion row lookup
    cache = get_smart_derangement_cache(n)
    derangements_with_signs = cache.get_all_derangements_with_signs()
    
    # Create a lookup table for derangement signs
    derangement_sign_lookup = {}
    for derang, sign in derangements_with_signs:
        derang_tuple = tuple(derang.tolist() if hasattr(derang, 'tolist') else derang)
        derangement_sign_lookup[derang_tuple] = sign
    
    print(f"   Derangement cache loaded: {len(derangements_with_signs):,} derangements")
    
    # Counters for canonical rectangles (before applying symmetry factor)
    canonical_total_4_5 = 0
    canonical_positive_4_5 = 0
    canonical_negative_4_5 = 0
    canonical_total_5_5 = 0
    canonical_positive_5_5 = 0
    canonical_negative_5_5 = 0
    
    # Process each canonical first column
    for i, first_column in enumerate(first_columns):
        print(f"   Processing first column {i+1}/{len(first_columns)}: {first_column}")
        
        # Enumerate all (4,5) rectangles with this first column and find their completions
        col_4_5_pos, col_4_5_neg, col_5_5_pos, col_5_5_neg = _enumerate_4_5_rectangles_and_completions(
            first_column, derangement_sign_lookup, cache
        )
        
        canonical_total_4_5 += col_4_5_pos + col_4_5_neg
        canonical_positive_4_5 += col_4_5_pos
        canonical_negative_4_5 += col_4_5_neg
        
        canonical_total_5_5 += col_5_5_pos + col_5_5_neg
        canonical_positive_5_5 += col_5_5_pos
        canonical_negative_5_5 += col_5_5_neg
        
        print(f"     (4,5): +{col_4_5_pos} -{col_4_5_neg} = {col_4_5_pos + col_4_5_neg}")
        print(f"     (5,5): +{col_5_5_pos} -{col_5_5_neg} = {col_5_5_pos + col_5_5_neg}")
    
    # Apply symmetry factor to get final counts
    total_4_5 = canonical_total_4_5 * symmetry_factor
    positive_4_5 = canonical_positive_4_5 * symmetry_factor
    negative_4_5 = canonical_negative_4_5 * symmetry_factor
    
    total_5_5 = canonical_total_5_5 * symmetry_factor
    positive_5_5 = canonical_positive_5_5 * symmetry_factor
    negative_5_5 = canonical_negative_5_5 * symmetry_factor
    
    print(f"✅ (4,5) → (5,5) completion optimization complete:")
    print(f"   Canonical (4,5): {canonical_total_4_5:,} rectangles (+{canonical_positive_4_5:,} -{canonical_negative_4_5:,})")
    print(f"   Final (4,5): {total_4_5:,} rectangles (+{positive_4_5:,} -{negative_4_5:,})")
    print(f"   Canonical (5,5): {canonical_total_5_5:,} rectangles (+{canonical_positive_5_5:,} -{canonical_negative_5_5:,})")
    print(f"   Final (5,5): {total_5_5:,} rectangles (+{positive_5_5:,} -{negative_5_5:,})")
    
    # Verify the bijection theorem
    if total_4_5 == total_5_5:
        print(f"✅ Bijection theorem verified: NLR(4,5) = NLR(5,5) = {total_4_5:,}")
    else:
        print(f"❌ Bijection theorem FAILED: NLR(4,5) = {total_4_5:,} ≠ NLR(5,5) = {total_5_5:,}")
    
    return ((total_4_5, positive_4_5, negative_4_5), (total_5_5, positive_5_5, negative_5_5))


def _enumerate_4_5_rectangles_and_completions(first_column: List[int], derangement_sign_lookup: dict, 
                                            cache) -> Tuple[int, int, int, int]:
    """
    Enumerate all (4,5) rectangles with the given first column and find their completions.
    
    Args:
        first_column: Fixed first column [1, a, b, c]
        derangement_sign_lookup: Lookup table for derangement signs
        cache: Smart derangement cache
        
    Returns:
        Tuple of (pos_4_5, neg_4_5, pos_5_5, neg_5_5)
    """
    
    n = 5
    
    # Get derangements and create filtered sets for each row based on first column constraints
    if hasattr(cache, 'get_bitwise_data'):
        conflict_masks, all_valid_mask = cache.get_bitwise_data()
        
        # Convert to lists for easier processing
        all_derangements = []
        all_signs = []
        
        for i in range(len(cache.derangements)):
            all_derangements.append(cache.derangements[i].tolist())
            all_signs.append(int(cache.signs[i]))
    else:
        derangements_with_signs = cache.get_all_derangements_with_signs()
        position_value_index = cache.position_value_index
        
        # Pre-compute conflict bitsets
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
        
        all_derangements = []
        all_signs = []
        for derang, sign in derangements_with_signs:
            if hasattr(derang, 'tolist'):
                all_derangements.append(derang.tolist())
            else:
                all_derangements.append(list(derang))
            all_signs.append(sign)
    
    # Create filtered derangement sets for rows 2, 3, 4 based on first column constraints
    filtered_sets = []
    
    for row_idx in range(1, 4):  # rows 1, 2, 3 (second, third, fourth rows)
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
        
        print(f"     Row {row_idx+1}: {len(filtered_indices)} candidates (start with {required_start_value})")
    
    # Create remapped conflict masks for the filtered sets
    def create_filtered_conflict_masks(filtered_set, pos, val):
        """Create conflict mask for filtered derangement set."""
        mask = 0
        original_conflicts = conflict_masks.get((pos, val), 0)
        
        for new_idx, orig_idx in enumerate(filtered_set['indices']):
            if original_conflicts & (1 << orig_idx):
                mask |= (1 << new_idx)
        
        return mask
    
    pos_4_5 = 0
    neg_4_5 = 0
    pos_5_5 = 0
    neg_5_5 = 0
    first_sign = 1  # Identity permutation
    
    # Enumerate all (4,5) rectangles with the given first column
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
                fourth_row = fourth_set['derangements'][fourth_idx]
                fourth_sign = fourth_set['signs'][fourth_idx]
                
                # This is a complete (4,5) rectangle
                rectangle_sign_4_5 = first_sign * second_sign * third_sign * fourth_sign
                if rectangle_sign_4_5 > 0:
                    pos_4_5 += 1
                else:
                    neg_4_5 += 1
                
                # Find the unique completion row for (5,5)
                first_row = list(range(1, n + 1))  # Identity permutation [1,2,3,4,5]
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
                        rectangle_sign_5_5 = rectangle_sign_4_5 * completion_sign
                        if rectangle_sign_5_5 > 0:
                            pos_5_5 += 1
                        else:
                            neg_5_5 += 1
                    else:
                        print(f"     WARNING: Completion row {completion_row} not found in derangement lookup")
                else:
                    print(f"     WARNING: Could not find completion row for rectangle")
    
    return pos_4_5, neg_4_5, pos_5_5, neg_5_5


if __name__ == "__main__":
    # Test the (4,5) → (5,5) implementation
    print("🧪 Testing (4,5) → (5,5) Completion Optimization with First Column")
    print("=" * 70)
    
    try:
        start_time = time.time()
        result = count_rectangles_4_5_with_completion_and_first_column()
        elapsed = time.time() - start_time
        print(f"\nTotal time: {elapsed:.4f}s")
        
        (total_4_5, pos_4_5, neg_4_5), (total_5_5, pos_5_5, neg_5_5) = result
        print(f"\nFinal Results:")
        print(f"  (4,5): {total_4_5:,} rectangles (+{pos_4_5:,} -{neg_4_5:,})")
        print(f"  (5,5): {total_5_5:,} rectangles (+{pos_5_5:,} -{neg_5_5:,})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()