#!/usr/bin/env python3
"""
Setup-once constrained enumeration for parallel processing.

This module separates the expensive setup work (pre-filtering, constraint tables, base masks)
from the actual rectangle counting, allowing setup to be done once per process
and counting to be done many times with different first columns.
"""

import time
from typing import List, Tuple, Dict, Optional
from core.smart_derangement_cache import get_smart_derangement_cache


def popcount(x: int) -> int:
    """Fast bit counting using Brian Kernighan's algorithm."""
    count = 0
    while x:
        count += 1
        x &= x - 1
    return count


class SetupOnceConstrainedCounter:
    """
    Constrained rectangle counter that does expensive setup once,
    then can count rectangles for many different first columns efficiently.
    """
    
    def __init__(self, r: int, n: int, cache=None):
        """
        Initialize the counter with expensive setup work.
        
        Args:
            r: Number of rows
            n: Number of columns
            cache: Pre-loaded smart derangement cache (None = load automatically)
        """
        self.r = r
        self.n = n
        
        # Get smart derangement cache (load if not provided)
        if cache is None:
            cache = get_smart_derangement_cache(n)
        self.cache = cache
        
        # Do all expensive setup work once
        self._setup_derangement_data()
        self._setup_constraint_tables()
        self._setup_base_masks()
        
        print(f"   ✅ Setup complete for ({r},{n}) - ready for fast counting")
    
    def _setup_derangement_data(self):
        """Set up derangement data structures."""
        derangements_with_signs = self.cache.get_all_derangements_with_signs()
        self.position_value_index = self.cache.position_value_index
        
        # Pre-filter derangements for each row position
        print(f"   Pre-filtering derangements for {self.r-1} rows...")
        self.filtered_sets_by_start_value = {}
        self.original_to_filtered_maps_by_start_value = {}
        
        # For each possible start value (2 to n, since 1 is always first row)
        for start_value in range(2, self.n + 1):
            filtered_derangements = []
            filtered_signs = []
            original_to_filtered = {}
            
            filtered_idx = 0
            for orig_idx, (derangement, sign) in enumerate(derangements_with_signs):
                if hasattr(derangement, 'tolist'):
                    derang_list = derangement.tolist()
                else:
                    derang_list = list(derangement)
                
                if derang_list[0] == start_value:
                    filtered_derangements.append(derang_list)
                    filtered_signs.append(sign)
                    original_to_filtered[orig_idx] = filtered_idx
                    filtered_idx += 1
            
            self.filtered_sets_by_start_value[start_value] = {
                'derangements': filtered_derangements,
                'signs': filtered_signs
            }
            self.original_to_filtered_maps_by_start_value[start_value] = original_to_filtered
            
            reduction = len(derangements_with_signs) / len(filtered_derangements) if len(filtered_derangements) > 0 else float('inf')
            print(f"   Start value {start_value}: {len(filtered_derangements)}/{len(derangements_with_signs)} candidates ({reduction:.1f}x reduction)")
    
    def _setup_constraint_tables(self):
        """Set up constraint lookup tables for all start values."""
        print(f"   Pre-computing constraint lookup tables...")
        self.constraint_tables_by_start_value = {}
        
        for start_value in range(2, self.n + 1):
            original_to_filtered = self.original_to_filtered_maps_by_start_value[start_value]
            
            table = {}
            for pos in range(self.n):
                for val in range(1, self.n + 1):
                    mask = 0
                    if (pos, val) in self.position_value_index:
                        original_conflicts = set(self.position_value_index[(pos, val)])
                        
                        # Map original indices to filtered indices
                        for orig_idx in original_conflicts:
                            if orig_idx in original_to_filtered:
                                filtered_idx = original_to_filtered[orig_idx]
                                mask |= (1 << filtered_idx)
                    
                    table[(pos, val)] = mask
            
            self.constraint_tables_by_start_value[start_value] = table
    
    def _setup_base_masks(self):
        """Set up pre-computed base masks for optimization."""
        print(f"   Pre-computing base masks...")
        # This will be used for r>=4 optimizations
        # For now, we'll compute them on-demand in the counting methods
        pass
    
    def count_rectangles_with_first_column(self, first_column: List[int]) -> Tuple[int, int]:
        """
        Count rectangles with the given first column.
        
        This is the fast operation that uses pre-computed setup data.
        
        Args:
            first_column: Fixed first column values [1, a2, a3, ..., ar]
            
        Returns:
            Tuple of (positive_count, negative_count)
        """
        # Validate parameters
        if len(first_column) != self.r:
            raise ValueError(f"first_column must have length r={self.r}, got {len(first_column)}")
        if first_column[0] != 1:
            raise ValueError(f"first_column must start with 1, got {first_column[0]}")
        
        # Special case: r=2 - just count the single rectangle
        if self.r == 2:
            a = first_column[1]
            rectangle_sign = (-1) ** (a - 1)
            if rectangle_sign > 0:
                return 1, 0
            else:
                return 0, 1
        
        # Get filtered sets for each row based on first column values
        filtered_sets = []
        constraint_tables = []
        
        for row_idx in range(1, self.r):  # rows 1 to r-1
            start_value = first_column[row_idx]
            filtered_sets.append(self.filtered_sets_by_start_value[start_value])
            constraint_tables.append(self.constraint_tables_by_start_value[start_value])
        
        # Pre-compute sign masks for final row
        final_set = filtered_sets[-1]
        positive_final_mask = 0
        negative_final_mask = 0
        
        for final_idx, final_sign in enumerate(final_set['signs']):
            if final_sign > 0:
                positive_final_mask |= (1 << final_idx)
            else:
                negative_final_mask |= (1 << final_idx)
        
        positive_count = 0
        negative_count = 0
        first_sign = 1
        
        # Use explicit implementations for each r value for maximum performance
        if self.r == 3:
            return self._count_r3(filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign)
        elif self.r == 4:
            return self._count_r4(filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign)
        elif self.r == 5:
            return self._count_r5(filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign)
        elif self.r == 6:
            return self._count_r6(filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign)
        else:
            return self._count_stack_approach(filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign)
    
    def _count_r3(self, filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign):
        """Count r=3 rectangles using pre-computed data."""
        positive_count = 0
        negative_count = 0
        
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        third_conflicts = constraint_tables[1]
        
        for second_row, second_sign in zip(second_set['derangements'], second_set['signs']):
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(self.n):
                third_row_valid &= ~third_conflicts[(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            # Use fast popcount
            combined_sign = first_sign * second_sign
            
            if combined_sign > 0:
                positive_rectangles = popcount(third_row_valid & positive_final_mask)
                negative_rectangles = popcount(third_row_valid & negative_final_mask)
                positive_count += positive_rectangles
                negative_count += negative_rectangles
            else:
                positive_rectangles = popcount(third_row_valid & negative_final_mask)
                negative_rectangles = popcount(third_row_valid & positive_final_mask)
                positive_count += positive_rectangles
                negative_count += negative_rectangles
        
        return positive_count, negative_count
    
    def _count_r4(self, filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign):
        """Count r=4 rectangles using pre-computed data."""
        positive_count = 0
        negative_count = 0
        
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        third_conflicts = constraint_tables[1]
        fourth_conflicts = constraint_tables[2]
        
        # Pre-compute fourth row base masks for each second row
        second_row_fourth_base_masks = []
        for second_row in second_set['derangements']:
            fourth_base_mask = (1 << len(fourth_set['derangements'])) - 1
            for pos in range(self.n):
                fourth_base_mask &= ~fourth_conflicts[(pos, second_row[pos])]
            second_row_fourth_base_masks.append(fourth_base_mask)
        
        for second_idx, (second_row, second_sign) in enumerate(zip(second_set['derangements'], second_set['signs'])):
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(self.n):
                third_row_valid &= ~third_conflicts[(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            # Use pre-computed fourth row base mask
            fourth_base_mask = second_row_fourth_base_masks[second_idx]
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = third_set['derangements'][third_idx]
                third_sign = third_set['signs'][third_idx]
                
                # Calculate valid fourth rows using pre-computed base mask
                fourth_row_valid = fourth_base_mask
                for pos in range(self.n):
                    fourth_row_valid &= ~fourth_conflicts[(pos, third_row[pos])]
                
                if fourth_row_valid == 0:
                    continue
                
                # Use fast popcount
                combined_sign = first_sign * second_sign * third_sign
                
                if combined_sign > 0:
                    positive_rectangles = popcount(fourth_row_valid & positive_final_mask)
                    negative_rectangles = popcount(fourth_row_valid & negative_final_mask)
                    positive_count += positive_rectangles
                    negative_count += negative_rectangles
                else:
                    positive_rectangles = popcount(fourth_row_valid & negative_final_mask)
                    negative_rectangles = popcount(fourth_row_valid & positive_final_mask)
                    positive_count += positive_rectangles
                    negative_count += negative_rectangles
        
        return positive_count, negative_count
    
    def _count_r5(self, filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign):
        """Count r=5 rectangles using pre-computed data."""
        positive_count = 0
        negative_count = 0
        
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        fifth_set = filtered_sets[3]
        third_conflicts = constraint_tables[1]
        fourth_conflicts = constraint_tables[2]
        fifth_conflicts = constraint_tables[3]
        
        # Pre-compute fifth row base masks for each second row
        second_row_fifth_base_masks = []
        for second_row in second_set['derangements']:
            fifth_base_mask = (1 << len(fifth_set['derangements'])) - 1
            for pos in range(self.n):
                fifth_base_mask &= ~fifth_conflicts[(pos, second_row[pos])]
            second_row_fifth_base_masks.append(fifth_base_mask)
        
        for second_idx, (second_row, second_sign) in enumerate(zip(second_set['derangements'], second_set['signs'])):
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(self.n):
                third_row_valid &= ~third_conflicts[(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            # Use pre-computed fifth row base mask
            fifth_base_mask = second_row_fifth_base_masks[second_idx]
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row = third_set['derangements'][third_idx]
                third_sign = third_set['signs'][third_idx]
                
                # Calculate valid fourth rows
                fourth_row_valid = (1 << len(fourth_set['derangements'])) - 1
                for pos in range(self.n):
                    fourth_row_valid &= ~fourth_conflicts[(pos, second_row[pos])]
                    fourth_row_valid &= ~fourth_conflicts[(pos, third_row[pos])]
                
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row = fourth_set['derangements'][fourth_idx]
                    fourth_sign = fourth_set['signs'][fourth_idx]
                    
                    # Calculate valid fifth rows using pre-computed base mask
                    fifth_row_valid = fifth_base_mask
                    for pos in range(self.n):
                        fifth_row_valid &= ~fifth_conflicts[(pos, third_row[pos])]
                        fifth_row_valid &= ~fifth_conflicts[(pos, fourth_row[pos])]
                    
                    if fifth_row_valid == 0:
                        continue
                    
                    # Use fast popcount
                    combined_sign = first_sign * second_sign * third_sign * fourth_sign
                    
                    if combined_sign > 0:
                        positive_rectangles = popcount(fifth_row_valid & positive_final_mask)
                        negative_rectangles = popcount(fifth_row_valid & negative_final_mask)
                        positive_count += positive_rectangles
                        negative_count += negative_rectangles
                    else:
                        positive_rectangles = popcount(fifth_row_valid & negative_final_mask)
                        negative_rectangles = popcount(fifth_row_valid & positive_final_mask)
                        positive_count += positive_rectangles
                        negative_count += negative_rectangles
        
        return positive_count, negative_count
    
    def _count_r6(self, filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign):
        """Count r=6 rectangles using pre-computed data."""
        positive_count = 0
        negative_count = 0
        
        second_set = filtered_sets[0]
        third_set = filtered_sets[1]
        fourth_set = filtered_sets[2]
        fifth_set = filtered_sets[3]
        sixth_set = filtered_sets[4]
        third_conflicts = constraint_tables[1]
        fourth_conflicts = constraint_tables[2]
        fifth_conflicts = constraint_tables[3]
        sixth_conflicts = constraint_tables[4]
        
        for second_row, second_sign in zip(second_set['derangements'], second_set['signs']):
            # Calculate valid third rows
            third_row_valid = (1 << len(third_set['derangements'])) - 1
            for pos in range(self.n):
                third_row_valid &= ~third_conflicts[(pos, second_row[pos])]
            
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
                for pos in range(self.n):
                    fourth_row_valid &= ~fourth_conflicts[(pos, second_row[pos])]
                    fourth_row_valid &= ~fourth_conflicts[(pos, third_row[pos])]
                
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
                    for pos in range(self.n):
                        fifth_row_valid &= ~fifth_conflicts[(pos, second_row[pos])]
                        fifth_row_valid &= ~fifth_conflicts[(pos, third_row[pos])]
                        fifth_row_valid &= ~fifth_conflicts[(pos, fourth_row[pos])]
                    
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
                        for pos in range(self.n):
                            sixth_row_valid &= ~sixth_conflicts[(pos, second_row[pos])]
                            sixth_row_valid &= ~sixth_conflicts[(pos, third_row[pos])]
                            sixth_row_valid &= ~sixth_conflicts[(pos, fourth_row[pos])]
                            sixth_row_valid &= ~sixth_conflicts[(pos, fifth_row[pos])]
                        
                        if sixth_row_valid == 0:
                            continue
                        
                        # Use fast popcount
                        combined_sign = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        
                        if combined_sign > 0:
                            positive_rectangles = popcount(sixth_row_valid & positive_final_mask)
                            negative_rectangles = popcount(sixth_row_valid & negative_final_mask)
                            positive_count += positive_rectangles
                            negative_count += negative_rectangles
                        else:
                            positive_rectangles = popcount(sixth_row_valid & negative_final_mask)
                            negative_rectangles = popcount(sixth_row_valid & positive_final_mask)
                            positive_count += positive_rectangles
                            negative_count += negative_rectangles
        
        return positive_count, negative_count
    
    def _count_stack_approach(self, filtered_sets, constraint_tables, positive_final_mask, negative_final_mask, first_sign):
        """Count rectangles using stack approach for r > 6."""
        positive_count = 0
        negative_count = 0
        
        second_set = filtered_sets[0]
        
        for second_row, second_sign in zip(second_set['derangements'], second_set['signs']):
            # Calculate initial valid mask for third row
            third_row_valid = (1 << len(filtered_sets[1]['derangements'])) - 1
            for pos in range(self.n):
                third_row_valid &= ~constraint_tables[1][(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            # Initialize stack with (level, valid_mask, accumulated_sign)
            # Level 2 = third row (0-indexed: 0=first, 1=second, 2=third, ...)
            stack = [(2, third_row_valid, first_sign * second_sign)]
            
            while stack:
                level, valid_mask, accumulated_sign = stack.pop()
                
                if level == self.r - 1:
                    # Final row - use fast popcount
                    if accumulated_sign > 0:
                        positive_rectangles = popcount(valid_mask & positive_final_mask)
                        negative_rectangles = popcount(valid_mask & negative_final_mask)
                        positive_count += positive_rectangles
                        negative_count += negative_rectangles
                    else:
                        positive_rectangles = popcount(valid_mask & negative_final_mask)
                        negative_rectangles = popcount(valid_mask & positive_final_mask)
                        positive_count += positive_rectangles
                        negative_count += negative_rectangles
                else:
                    # Not final row - iterate and push to stack
                    current_set = filtered_sets[level - 1]  # -1 because we skip first row
                    next_conflicts = constraint_tables[level] if level < len(constraint_tables) else constraint_tables[-1]
                    
                    current_mask = valid_mask
                    while current_mask:
                        current_idx = (current_mask & -current_mask).bit_length() - 1
                        current_mask &= current_mask - 1
                        current_row = current_set['derangements'][current_idx]
                        current_sign = current_set['signs'][current_idx]
                        
                        # Calculate valid mask for next row
                        if level + 1 < self.r:
                            next_valid = (1 << len(filtered_sets[level]['derangements'])) - 1
                            for pos in range(self.n):
                                next_valid &= ~next_conflicts[(pos, current_row[pos])]
                            
                            if next_valid != 0:
                                new_accumulated_sign = accumulated_sign * current_sign
                                stack.append((level + 1, next_valid, new_accumulated_sign))
        
        return positive_count, negative_count


def main():
    """Test the setup-once constrained counter."""
    
    # Test cases
    test_cases = [
        (3, 6, [1, 2, 3]),
        (4, 6, [1, 2, 3, 4]),
        (5, 6, [1, 2, 3, 4, 5]),
    ]
    
    for r, n, first_column in test_cases:
        print(f"\n=== Testing Setup-Once ({r},{n}) with first column {first_column} ===")
        
        try:
            # Setup once
            setup_start = time.time()
            counter = SetupOnceConstrainedCounter(r, n)
            setup_time = time.time() - setup_start
            
            # Count many times (simulate multiple first columns)
            count_start = time.time()
            positive, negative = counter.count_rectangles_with_first_column(first_column)
            count_time = time.time() - count_start
            
            total = positive + negative
            
            print(f"Results:")
            print(f"  Setup time: {setup_time:.6f}s")
            print(f"  Count time: {count_time:.6f}s")
            print(f"  Total time: {setup_time + count_time:.6f}s")
            print(f"  Positive: {positive:,}")
            print(f"  Negative: {negative:,}")
            print(f"  Total: {total:,}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()