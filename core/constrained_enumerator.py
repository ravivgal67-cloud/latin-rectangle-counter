#!/usr/bin/env python3
"""
Constrained Rectangle Enumerator for First Column Optimization.

This module enumerates Latin rectangles with fixed first column constraints,
integrating with the existing ultra_safe_bitwise algorithm.
"""

from typing import List, Tuple, Dict, Set
import time
from core.smart_derangement_cache import get_smart_derangement_cache


class ConstrainedEnumerator:
    """
    Enumerates Latin rectangles with fixed first column constraints.
    
    Integrates with the existing ultra_safe_bitwise algorithm by pre-applying
    first column constraints to reduce the search space.
    """
    
    def __init__(self):
        """Initialize the constrained enumerator."""
        self._cache = {}  # Cache for filtered derangements
    
    def enumerate_with_fixed_first_column(self, r: int, n: int, 
                                        first_column: List[int],
                                        cache=None) -> Tuple[int, int]:
        """
        Enumerate rectangles with fixed first column (regular version).
        
        Args:
            r: Number of rows
            n: Number of columns  
            first_column: Fixed first column values [1, a, b, c, ...]
            cache: Pre-loaded smart derangement cache (None = load automatically)
            
        Returns:
            Tuple of (positive_count, negative_count)
        """
        # Validate inputs
        self._validate_inputs(r, n, first_column)
        
        # Use our ultra-optimized constrained enumeration
        from core.ultra_optimized_constrained import count_rectangles_ultra_optimized_constrained
        
        return count_rectangles_ultra_optimized_constrained(r, n, first_column, cache=cache)

    def enumerate_with_fixed_first_column_completion(self, r: int, n: int, 
                                                   first_column: List[int],
                                                   cache=None) -> Tuple[int, int, int, int]:
        """
        Enumerate rectangles with fixed first column using completion optimization.
        
        When r = n-1, this computes both (r, n) and (n, n) rectangles together
        by completing each (r, n) rectangle to its unique (n, n) completion.
        
        Args:
            r: Number of rows (must equal n-1)
            n: Number of columns  
            first_column: Fixed first column values [1, a, b, c, ...]
            cache: Pre-loaded smart derangement cache (None = load automatically)
            
        Returns:
            Tuple of (positive_r, negative_r, positive_r_plus_1, negative_r_plus_1)
        """
        if r != n - 1:
            raise ValueError(f"Completion optimization requires r = n-1, got r={r}, n={n}")
        
        # Validate inputs
        self._validate_inputs(r, n, first_column)
        
        # Use our ultra-optimized constrained enumeration with completion
        from core.ultra_optimized_constrained import count_rectangles_ultra_optimized_constrained_completion
        
        return count_rectangles_ultra_optimized_constrained_completion(r, n, first_column, cache=cache)
    
    def _filter_derangements_for_first_column(self, cache, first_column: List[int], 
                                            r: int, n: int) -> List[Tuple[int, List[int], int]]:
        """
        Filter second row derangements that are compatible with the first column.
        
        Args:
            cache: Derangement cache
            first_column: Fixed first column values
            r: Number of rows
            n: Number of columns
            
        Returns:
            List of (index, derangement, sign) tuples for valid derangements
        """
        # Create cache key
        cache_key = (tuple(first_column), r, n)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get all derangements with signs - handle different cache types
        if hasattr(cache, 'get_all_derangements_with_signs'):
            # SmartDerangementCache or CompactDerangementCache
            derangements_with_signs = cache.get_all_derangements_with_signs()
        elif hasattr(cache, 'derangements_with_signs'):
            # SmartDerangementCache direct access
            derangements_with_signs = cache.derangements_with_signs
        elif hasattr(cache, 'derangements') and hasattr(cache, 'signs'):
            # Legacy cache format with separate arrays
            derangements_with_signs = list(zip(cache.derangements, cache.signs))
        else:
            raise ValueError(f"Unknown cache type: {type(cache)}")
        
        # Filter derangements: exclude those whose first element conflicts with first column
        filtered = []
        excluded_first_elements = set(first_column[1:])  # Elements in positions 2+ of first column
        
        for idx, (derangement, sign) in enumerate(derangements_with_signs):
            # Convert derangement to list if it's a numpy array
            if hasattr(derangement, 'tolist'):
                derangement_list = derangement.tolist()
            else:
                derangement_list = list(derangement)
            
            # Check if first element of derangement conflicts with first column
            first_element = derangement_list[0]
            if first_element not in excluded_first_elements:
                filtered.append((idx, derangement_list, int(sign)))
        
        # Cache the result
        self._cache[cache_key] = filtered
        
        return filtered
    
    def _enumerate_with_binary_cache(self, r: int, n: int, first_column: List[int],
                                   cache) -> Tuple[int, int]:
        """Enumerate using binary cache with first column constraints."""
        
        # For now, fall back to JSON cache method since the binary optimization
        # needs to be updated to handle the new constraint logic
        return self._enumerate_with_json_cache(r, n, first_column, cache)
    
    def _create_first_column_constraint_masks(self, first_column: List[int], n: int, 
                                            conflict_masks: Dict) -> List[int]:
        """
        Create constraint masks for the fixed first column.
        
        Args:
            first_column: Fixed first column values [1, a, b, c, ...]
            n: Number of columns
            conflict_masks: Pre-computed conflict masks
            
        Returns:
            List of constraint masks, one per row (excluding first row)
        """
        constraints = []
        
        # For each row after the first (which is identity)
        for row_idx in range(1, len(first_column)):
            # The value at position 0 (first column) is fixed
            fixed_value = first_column[row_idx]
            
            # Create constraint mask: exclude derangements that have conflicts
            # with this fixed value at position 0
            constraint_mask = 0
            if (0, fixed_value) in conflict_masks:
                constraint_mask = conflict_masks[(0, fixed_value)]
            
            constraints.append(constraint_mask)
        
        return constraints
    
    def _enumerate_r3_binary(self, filtered_derangements: List[Tuple[int, List[int], int]],
                           first_column_constraints: List[int], conflict_masks: Dict,
                           all_valid_mask: int, cache) -> Tuple[int, int]:
        """Enumerate r=3 rectangles with first column constraints."""
        
        positive_count = 0
        negative_count = 0
        
        # Get signs for quick lookup
        signs_list = [int(cache.signs[i]) for i in range(len(cache.signs))]
        
        for second_idx, second_row, second_sign in filtered_derangements:
            # Apply constraints from second row
            third_row_valid = all_valid_mask
            for pos in range(len(second_row)):
                if (pos, second_row[pos]) in conflict_masks:
                    third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            # Apply first column constraint for third row
            if len(first_column_constraints) > 1:
                third_row_valid &= ~first_column_constraints[1]
            
            # Enumerate valid third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_sign = signs_list[third_idx]
                
                # Calculate rectangle sign (first row sign is always +1)
                rectangle_sign = 1 * second_sign * third_sign
                
                if rectangle_sign > 0:
                    positive_count += 1
                else:
                    negative_count += 1
        
        return (positive_count, negative_count)
    
    def _enumerate_r4_binary(self, filtered_derangements: List[Tuple[int, List[int], int]],
                           first_column_constraints: List[int], conflict_masks: Dict,
                           all_valid_mask: int, cache) -> Tuple[int, int]:
        """Enumerate r=4 rectangles with first column constraints."""
        
        positive_count = 0
        negative_count = 0
        
        # Get derangements and signs for quick lookup
        derangements_lists = [cache.derangements[i].tolist() for i in range(len(cache.derangements))]
        signs_list = [int(cache.signs[i]) for i in range(len(cache.signs))]
        
        for second_idx, second_row, second_sign in filtered_derangements:
            # Apply constraints from second row
            third_row_valid = all_valid_mask
            for pos in range(len(second_row)):
                if (pos, second_row[pos]) in conflict_masks:
                    third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            # Apply first column constraint for third row
            if len(first_column_constraints) > 1:
                third_row_valid &= ~first_column_constraints[1]
            
            if third_row_valid == 0:
                continue
            
            # Enumerate valid third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = derangements_lists[third_idx]
                third_sign = signs_list[third_idx]
                
                # Apply constraints from third row
                fourth_row_valid = third_row_valid
                for pos in range(len(third_row)):
                    if (pos, third_row[pos]) in conflict_masks:
                        fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                # Apply first column constraint for fourth row
                if len(first_column_constraints) > 2:
                    fourth_row_valid &= ~first_column_constraints[2]
                
                # Enumerate valid fourth rows
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_sign = signs_list[fourth_idx]
                    
                    # Calculate rectangle sign
                    rectangle_sign = 1 * second_sign * third_sign * fourth_sign
                    
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
        
        return (positive_count, negative_count)
    
    def _enumerate_r5_binary(self, filtered_derangements: List[Tuple[int, List[int], int]],
                           first_column_constraints: List[int], conflict_masks: Dict,
                           all_valid_mask: int, cache) -> Tuple[int, int]:
        """Enumerate r=5 rectangles with first column constraints."""
        
        positive_count = 0
        negative_count = 0
        
        # Get derangements and signs for quick lookup
        derangements_lists = [cache.derangements[i].tolist() for i in range(len(cache.derangements))]
        signs_list = [int(cache.signs[i]) for i in range(len(cache.signs))]
        
        for second_idx, second_row, second_sign in filtered_derangements:
            # Apply constraints from second row
            third_row_valid = all_valid_mask
            for pos in range(len(second_row)):
                if (pos, second_row[pos]) in conflict_masks:
                    third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            # Apply first column constraint for third row
            if len(first_column_constraints) > 1:
                third_row_valid &= ~first_column_constraints[1]
            
            if third_row_valid == 0:
                continue
            
            # Enumerate third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = derangements_lists[third_idx]
                third_sign = signs_list[third_idx]
                
                # Apply constraints from third row
                fourth_row_valid = third_row_valid
                for pos in range(len(third_row)):
                    if (pos, third_row[pos]) in conflict_masks:
                        fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                # Apply first column constraint for fourth row
                if len(first_column_constraints) > 2:
                    fourth_row_valid &= ~first_column_constraints[2]
                
                if fourth_row_valid == 0:
                    continue
                
                # Enumerate fourth rows
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row = derangements_lists[fourth_idx]
                    fourth_sign = signs_list[fourth_idx]
                    
                    # Apply constraints from fourth row
                    fifth_row_valid = fourth_row_valid
                    for pos in range(len(fourth_row)):
                        if (pos, fourth_row[pos]) in conflict_masks:
                            fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    
                    # Apply first column constraint for fifth row
                    if len(first_column_constraints) > 3:
                        fifth_row_valid &= ~first_column_constraints[3]
                    
                    # Enumerate valid fifth rows
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_sign = signs_list[fifth_idx]
                        
                        # Calculate rectangle sign
                        rectangle_sign = 1 * second_sign * third_sign * fourth_sign * fifth_sign
                        
                        if rectangle_sign > 0:
                            positive_count += 1
                        else:
                            negative_count += 1
        
        return (positive_count, negative_count)
    
    def _enumerate_r6_binary(self, filtered_derangements: List[Tuple[int, List[int], int]],
                           first_column_constraints: List[int], conflict_masks: Dict,
                           all_valid_mask: int, cache) -> Tuple[int, int]:
        """Enumerate r=6 rectangles with first column constraints."""
        # Similar to r=5 but with one more nested loop
        # Implementation would follow the same pattern
        # For brevity, using parametrized approach
        return self._enumerate_parametrized_binary(
            6, filtered_derangements, first_column_constraints,
            conflict_masks, all_valid_mask, cache
        )
    
    def _enumerate_parametrized_binary(self, r: int, filtered_derangements: List[Tuple[int, List[int], int]],
                                     first_column_constraints: List[int], conflict_masks: Dict,
                                     all_valid_mask: int, cache) -> Tuple[int, int]:
        """Parametrized enumeration for any r using recursion."""
        
        derangements_lists = [cache.derangements[i].tolist() for i in range(len(cache.derangements))]
        signs_list = [int(cache.signs[i]) for i in range(len(cache.signs))]
        
        def enumerate_recursive(row_idx: int, current_valid_mask: int, current_sign: int) -> Tuple[int, int]:
            """Recursively enumerate remaining rows."""
            if row_idx == r:
                # Base case: all rows filled
                if current_sign > 0:
                    return (1, 0)
                else:
                    return (0, 1)
            
            pos_count = 0
            neg_count = 0
            
            # Apply first column constraint for this row
            row_valid_mask = current_valid_mask
            if row_idx - 1 < len(first_column_constraints):
                row_valid_mask &= ~first_column_constraints[row_idx - 1]
            
            # Enumerate valid derangements for this row
            mask = row_valid_mask
            while mask:
                idx = (mask & -mask).bit_length() - 1
                mask &= mask - 1
                
                row_derangement = derangements_lists[idx]
                row_sign = signs_list[idx]
                
                # Apply constraints from this row to next row
                next_valid_mask = row_valid_mask
                for pos in range(len(row_derangement)):
                    if (pos, row_derangement[pos]) in conflict_masks:
                        next_valid_mask &= ~conflict_masks[(pos, row_derangement[pos])]
                
                # Recurse to next row
                sub_pos, sub_neg = enumerate_recursive(row_idx + 1, next_valid_mask, current_sign * row_sign)
                pos_count += sub_pos
                neg_count += sub_neg
            
            return (pos_count, neg_count)
        
        total_positive = 0
        total_negative = 0
        
        # Start with second row (first row is identity)
        for second_idx, second_row, second_sign in filtered_derangements:
            # Apply constraints from second row
            third_row_valid = all_valid_mask
            for pos in range(len(second_row)):
                if (pos, second_row[pos]) in conflict_masks:
                    third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            # Recurse for remaining rows
            pos_count, neg_count = enumerate_recursive(3, third_row_valid, 1 * second_sign)
            total_positive += pos_count
            total_negative += neg_count
        
        return (total_positive, total_negative)
    
    def _enumerate_with_json_cache(self, r: int, n: int, first_column: List[int],
                                 cache) -> Tuple[int, int]:
        """Enumerate using JSON cache with proper first column constraints."""
        
        # Get all derangements for constraint checking - handle different cache types
        if hasattr(cache, 'get_all_derangements_with_signs'):
            # SmartDerangementCache or CompactDerangementCache
            all_derangements_with_signs = cache.get_all_derangements_with_signs()
        elif hasattr(cache, 'derangements_with_signs'):
            # SmartDerangementCache direct access
            all_derangements_with_signs = cache.derangements_with_signs
        elif hasattr(cache, 'derangements') and hasattr(cache, 'signs'):
            # Legacy cache format with separate arrays
            all_derangements_with_signs = list(zip(cache.derangements, cache.signs))
        else:
            raise ValueError(f"Unknown cache type: {type(cache)}")
        
        def has_conflict(row1: List[int], row2: List[int]) -> bool:
            """Check if two rows have conflicting values at any position."""
            for pos in range(len(row1)):
                if row1[pos] == row2[pos]:
                    return True
            return False
        
        def enumerate_recursive(row_idx: int, current_rows: List[List[int]], current_sign: int) -> Tuple[int, int]:
            """Recursively enumerate remaining rows."""
            if row_idx == r:
                # Base case: all rows filled
                if current_sign > 0:
                    return (1, 0)
                else:
                    return (0, 1)
            
            pos_count = 0
            neg_count = 0
            
            # Get the required first element for this row from the first column
            required_first_element = first_column[row_idx]
            
            # Find derangements that start with the required first element
            candidates = []
            for idx, (derangement, sign) in enumerate(all_derangements_with_signs):
                # Convert to list if needed
                if hasattr(derangement, 'tolist'):
                    derangement_list = derangement.tolist()
                else:
                    derangement_list = list(derangement)
                
                # Check if this derangement starts with the required element
                if derangement_list[0] == required_first_element:
                    candidates.append((idx, derangement_list, int(sign)))
            
            # Try each candidate derangement
            for idx, row_derangement, row_sign in candidates:
                # Check conflicts with all previous rows
                has_any_conflict = False
                for prev_row in current_rows[1:]:  # Skip identity row
                    if has_conflict(prev_row, row_derangement):
                        has_any_conflict = True
                        break
                
                if not has_any_conflict:
                    # This row is valid, recurse to next row
                    new_rows = current_rows + [row_derangement]
                    sub_pos, sub_neg = enumerate_recursive(row_idx + 1, new_rows, current_sign * row_sign)
                    pos_count += sub_pos
                    neg_count += sub_neg
            
            return (pos_count, neg_count)
        
        # Start enumeration with identity first row
        identity_row = list(range(1, n + 1))
        total_positive, total_negative = enumerate_recursive(1, [identity_row], 1)
        
        return (total_positive, total_negative)
    
    def _enumerate_r2_with_first_column(self, n: int, first_column: List[int]) -> Tuple[int, int]:
        """Handle r=2 case with first column constraints."""
        # For r=2, we just need to count valid second rows
        # Second row must be a derangement that doesn't conflict with first column
        
        # The first column constraint is [1, a] where a is from {2, ..., n}
        a = first_column[1]
        
        # Second row must be a derangement of [1,2,...,n] where:
        # - First element cannot be 1 (derangement property)  
        # - Second element cannot be a (first column constraint)
        
        # Count valid derangements
        from core.permutation import count_derangements
        
        # This is a simplified calculation - in practice we'd need to
        # enumerate actual derangements and filter them
        # For now, return a placeholder
        return (0, 0)  # TODO: Implement proper r=2 handling
    
    def _validate_inputs(self, r: int, n: int, first_column: List[int]) -> None:
        """Validate inputs for constrained enumeration."""
        if r < 2:
            raise ValueError(f"r must be >= 2, got r={r}")
        if r > n:
            raise ValueError(f"r must be <= n, got r={r}, n={n}")
        if len(first_column) != r:
            raise ValueError(f"First column length {len(first_column)} must equal r={r}")
        if first_column[0] != 1:
            raise ValueError(f"First column must start with 1, got {first_column[0]}")
        if len(set(first_column)) != len(first_column):
            raise ValueError(f"First column must have unique values, got {first_column}")
        if not all(1 <= val <= n for val in first_column):
            raise ValueError(f"All first column values must be in [1,{n}], got {first_column}")


def main():
    """
    Test the constrained enumerator.
    """
    enumerator = ConstrainedEnumerator()
    
    # Test cases
    test_cases = [
        (3, 4, [1, 2, 3]),
        (3, 4, [1, 2, 4]),
        (3, 4, [1, 3, 4]),
    ]
    
    for r, n, first_column in test_cases:
        print(f"\n=== Testing ({r},{n}) with first column {first_column} ===")
        
        try:
            start_time = time.time()
            positive, negative = enumerator.enumerate_with_fixed_first_column(r, n, first_column)
            elapsed = time.time() - start_time
            
            total = positive + negative
            difference = positive - negative
            
            print(f"Results:")
            print(f"  Positive: {positive:,}")
            print(f"  Negative: {negative:,}")
            print(f"  Total: {total:,}")
            print(f"  Difference: {difference:+,}")
            print(f"  Time: {elapsed:.4f}s")
            
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()