#!/usr/bin/env python3
"""
Enhanced Constraint Propagator for First Column Optimization.

This module provides enhanced constraint propagation by generating bitwise
constraint masks for fixed first column values and optimizing constraint
checking for better performance.
"""

from typing import List, Dict, Tuple, Set
import time
from core.smart_derangement_cache import get_smart_derangement_cache


class EnhancedConstraintPropagator:
    """
    Enhanced constraint propagator for first column optimization.
    
    Generates bitwise constraint masks for fixed first column values and
    updates position-value constraints to reflect first column constraints.
    Maintains compatibility with existing constraint checking while providing
    significant performance improvements.
    """
    
    def __init__(self):
        """Initialize the enhanced constraint propagator."""
        self._mask_cache = {}  # Cache for constraint masks
        self._constraint_cache = {}  # Cache for position-value constraints
        self._pattern_cache = {}  # Cache for common constraint patterns
        self._similarity_cache = {}  # Cache for similar first column choices
    
    def create_first_column_masks(self, first_column: List[int], n: int) -> List[int]:
        """
        Create bitwise constraint masks for fixed first column values.
        
        Uses optimization techniques:
        - Caches masks for identical first column choices
        - Reuses patterns across similar choices
        - Pre-computes common constraint patterns
        
        Args:
            first_column: Fixed first column values [1, a, b, c, ...]
            n: Number of columns
            
        Returns:
            List of constraint masks, one per row (excluding first row)
        """
        # Create cache key
        cache_key = (tuple(first_column), n)
        if cache_key in self._mask_cache:
            return self._mask_cache[cache_key]
        
        # Check for similar first column choices that can be reused
        similar_masks = self._find_similar_masks(first_column, n)
        if similar_masks is not None:
            self._mask_cache[cache_key] = similar_masks
            return similar_masks
        
        # Get derangement cache for bitwise operations
        cache = get_smart_derangement_cache(n)
        
        # Check if binary cache is available for bitwise operations
        if hasattr(cache, 'get_bitwise_data'):
            masks = self._create_masks_with_binary_cache(first_column, n, cache)
        else:
            masks = self._create_masks_with_json_cache(first_column, n, cache)
        
        # Cache the result and update similarity patterns
        self._mask_cache[cache_key] = masks
        self._update_similarity_patterns(first_column, n, masks)
        
        return masks
    
    def _create_masks_with_binary_cache(self, first_column: List[int], n: int, cache) -> List[int]:
        """Create constraint masks using binary cache with bitwise operations."""
        
        try:
            conflict_masks, all_valid_mask = cache.get_bitwise_data()
        except Exception:
            # Fallback to JSON cache if binary operations fail
            return self._create_masks_with_json_cache(first_column, n, cache)
        
        masks = []
        
        # For each row after the first (which is identity)
        for row_idx in range(1, len(first_column)):
            # The value at position 0 (first column) is fixed
            fixed_value = first_column[row_idx]
            
            # Create constraint mask: exclude derangements that conflict
            # with this fixed value at position 0
            constraint_mask = 0
            if (0, fixed_value) in conflict_masks:
                constraint_mask = conflict_masks[(0, fixed_value)]
            
            masks.append(constraint_mask)
        
        return masks
    
    def _create_masks_with_json_cache(self, first_column: List[int], n: int, cache) -> List[int]:
        """Create constraint masks using JSON cache (fallback implementation)."""
        
        # Get all derangements
        derangements_with_signs = cache.get_all_derangements_with_signs()
        
        masks = []
        
        # For each row after the first
        for row_idx in range(1, len(first_column)):
            fixed_value = first_column[row_idx]
            
            # Create bitmask: bit i is set if derangement i is incompatible
            mask = 0
            for i, (derangement, sign) in enumerate(derangements_with_signs):
                # Convert to list if needed
                if hasattr(derangement, 'tolist'):
                    derangement_list = derangement.tolist()
                else:
                    derangement_list = list(derangement)
                
                # Check if this derangement is incompatible with the fixed first column value
                # A derangement is incompatible if its first element equals the fixed value
                if derangement_list[0] == fixed_value:
                    mask |= (1 << i)
            
            masks.append(mask)
        
        return masks
    
    def update_position_value_constraints(self, constraints: Dict, 
                                        first_column: List[int]) -> Dict:
        """
        Update position-value constraints to reflect first column constraints.
        
        Args:
            constraints: Current constraint dictionary
            first_column: Fixed first column values
            
        Returns:
            Updated constraints with first column applied
        """
        # Create cache key
        cache_key = (tuple(first_column), id(constraints))
        if cache_key in self._constraint_cache:
            return self._constraint_cache[cache_key]
        
        # Create updated constraints
        updated_constraints = constraints.copy()
        
        # Add first column constraints
        for row_idx, value in enumerate(first_column):
            # Position (row_idx, 0) is fixed to 'value'
            position_key = (row_idx, 0)
            if position_key not in updated_constraints:
                updated_constraints[position_key] = set()
            
            # All other values are forbidden at this position
            for other_value in range(1, len(first_column) + 1):
                if other_value != value:
                    updated_constraints[position_key].add(other_value)
        
        # Cache the result
        self._constraint_cache[cache_key] = updated_constraints
        return updated_constraints
    
    def apply_first_column_constraints(self, valid_mask: int, first_column: List[int], 
                                     row_idx: int, n: int) -> int:
        """
        Apply first column constraints to a valid derangement mask.
        
        Args:
            valid_mask: Current valid derangement mask
            first_column: Fixed first column values
            row_idx: Current row index (1-based)
            n: Number of columns
            
        Returns:
            Updated mask with first column constraints applied
        """
        if row_idx >= len(first_column):
            return valid_mask
        
        # Get constraint masks for this first column
        constraint_masks = self.create_first_column_masks(first_column, n)
        
        # Apply constraint for this row
        if row_idx - 1 < len(constraint_masks):
            # Remove derangements that conflict with the first column constraint
            valid_mask &= ~constraint_masks[row_idx - 1]
        
        return valid_mask
    
    def get_compatible_derangements(self, first_column: List[int], row_idx: int, 
                                  n: int) -> List[Tuple[int, List[int], int]]:
        """
        Get derangements compatible with first column constraint for a specific row.
        
        Args:
            first_column: Fixed first column values
            row_idx: Row index (1-based)
            n: Number of columns
            
        Returns:
            List of (index, derangement, sign) tuples for compatible derangements
        """
        if row_idx >= len(first_column):
            # No constraint for this row
            cache = get_smart_derangement_cache(n)
            derangements_with_signs = cache.get_all_derangements_with_signs()
            return [(i, list(d), int(s)) for i, (d, s) in enumerate(derangements_with_signs)]
        
        # Get required first element for this row
        required_first_element = first_column[row_idx]
        
        # Get derangements that start with the required element
        cache = get_smart_derangement_cache(n)
        derangements_with_signs = cache.get_all_derangements_with_signs()
        
        compatible = []
        for i, (derangement, sign) in enumerate(derangements_with_signs):
            # Convert to list if needed
            if hasattr(derangement, 'tolist'):
                derangement_list = derangement.tolist()
            else:
                derangement_list = list(derangement)
            
            # Check if this derangement starts with the required element
            if derangement_list[0] == required_first_element:
                compatible.append((i, derangement_list, int(sign)))
        
        return compatible
    
    def optimize_constraint_checking(self, first_column: List[int], n: int) -> Dict:
        """
        Pre-compute optimization data for constraint checking.
        
        Args:
            first_column: Fixed first column values
            n: Number of columns
            
        Returns:
            Dictionary with optimization data
        """
        optimization_data = {
            'first_column': first_column,
            'n': n,
            'constraint_masks': self.create_first_column_masks(first_column, n),
            'compatible_derangements': {}
        }
        
        # Pre-compute compatible derangements for each row
        for row_idx in range(1, len(first_column)):
            compatible = self.get_compatible_derangements(first_column, row_idx, n)
            optimization_data['compatible_derangements'][row_idx] = compatible
        
        return optimization_data
    
    def clear_cache(self):
        """Clear all cached data."""
        self._mask_cache.clear()
        self._constraint_cache.clear()
        self._pattern_cache.clear()
        self._similarity_cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'mask_cache_size': len(self._mask_cache),
            'constraint_cache_size': len(self._constraint_cache),
            'pattern_cache_size': len(self._pattern_cache),
            'similarity_cache_size': len(self._similarity_cache)
        }
    
    def _find_similar_masks(self, first_column: List[int], n: int) -> List[int]:
        """
        Find similar first column choices that can reuse constraint masks.
        
        Two first column choices are similar if they have the same pattern
        of value relationships, allowing mask reuse with value mapping.
        
        Args:
            first_column: Current first column values
            n: Number of columns
            
        Returns:
            Cached masks if similar pattern found, None otherwise
        """
        # Create pattern signature based on relative positions
        pattern = self._create_pattern_signature(first_column)
        pattern_key = (pattern, n)
        
        if pattern_key in self._pattern_cache:
            # Found similar pattern, can reuse masks
            return self._pattern_cache[pattern_key].copy()
        
        return None
    
    def _create_pattern_signature(self, first_column: List[int]) -> Tuple:
        """
        Create a pattern signature for first column that captures
        the relative ordering relationships.
        
        Args:
            first_column: First column values
            
        Returns:
            Pattern signature tuple
        """
        # For optimization, we can group first columns by their sorted order
        # Two first columns with the same sorted values will have similar constraints
        sorted_values = tuple(sorted(first_column[1:]))  # Exclude the fixed 1
        return sorted_values
    
    def _update_similarity_patterns(self, first_column: List[int], n: int, masks: List[int]):
        """
        Update similarity patterns cache with new masks.
        
        Args:
            first_column: First column values
            n: Number of columns
            masks: Generated constraint masks
        """
        pattern = self._create_pattern_signature(first_column)
        pattern_key = (pattern, n)
        
        # Store pattern for future reuse
        if pattern_key not in self._pattern_cache:
            self._pattern_cache[pattern_key] = masks.copy()
    
    def precompute_common_patterns(self, r: int, n: int, max_patterns: int = 100):
        """
        Pre-compute constraint masks for common first column patterns.
        
        This method analyzes common patterns in first column choices and
        pre-computes their constraint masks to improve performance.
        
        Args:
            r: Number of rows
            n: Number of columns
            max_patterns: Maximum number of patterns to pre-compute
        """
        from core.first_column_enumerator import FirstColumnEnumerator
        
        # Generate all possible first column choices
        enumerator = FirstColumnEnumerator()
        first_columns = enumerator.enumerate_first_columns(r, n)
        
        # Pre-compute masks for up to max_patterns choices
        patterns_computed = 0
        for first_column in first_columns:
            if patterns_computed >= max_patterns:
                break
            
            # This will cache the masks
            self.create_first_column_masks(first_column, n)
            patterns_computed += 1
        
        print(f"Pre-computed constraint masks for {patterns_computed} first column patterns")
    
    def optimize_for_workload(self, first_columns: List[List[int]], n: int):
        """
        Optimize constraint propagator for a specific workload.
        
        Pre-computes all constraint masks for the given first column choices
        and optimizes internal data structures for this workload.
        
        Args:
            first_columns: List of first column choices that will be processed
            n: Number of columns
        """
        print(f"Optimizing constraint propagator for {len(first_columns)} first column choices...")
        
        start_time = time.time()
        
        # Pre-compute all masks
        for first_column in first_columns:
            self.create_first_column_masks(first_column, n)
        
        elapsed = time.time() - start_time
        stats = self.get_cache_stats()
        
        print(f"Optimization complete in {elapsed:.3f}s")
        print(f"Cache sizes: {stats}")
        
        # Calculate cache hit rate potential
        unique_patterns = len(self._pattern_cache)
        total_choices = len(first_columns)
        potential_reuse = max(0, total_choices - unique_patterns)
        
        if total_choices > 0:
            reuse_percentage = (potential_reuse / total_choices) * 100
            print(f"Potential cache reuse: {reuse_percentage:.1f}% ({potential_reuse}/{total_choices})")
    
    def get_optimization_stats(self) -> Dict:
        """
        Get detailed optimization statistics.
        
        Returns:
            Dictionary with optimization performance metrics
        """
        stats = self.get_cache_stats()
        
        # Calculate efficiency metrics
        total_cached_items = sum(stats.values())
        unique_patterns = stats['pattern_cache_size']
        
        efficiency_metrics = {
            'total_cached_items': total_cached_items,
            'unique_patterns': unique_patterns,
            'cache_efficiency': unique_patterns / total_cached_items if total_cached_items > 0 else 0,
            'memory_usage_estimate': total_cached_items * 64,  # Rough estimate in bytes
        }
        
        return {**stats, **efficiency_metrics}


def main():
    """
    Test the enhanced constraint propagator with optimizations.
    """
    propagator = EnhancedConstraintPropagator()
    
    # Test cases
    test_cases = [
        (3, 4, [1, 2, 3]),
        (3, 4, [1, 2, 4]),  # Similar pattern to first
        (3, 4, [1, 3, 4]),  # Similar pattern to first
        (4, 5, [1, 2, 3, 4]),
    ]
    
    print("=== Testing Enhanced Constraint Propagator with Optimizations ===")
    
    # Test basic functionality
    for r, n, first_column in test_cases:
        print(f"\n--- Testing ({r},{n}) with first column {first_column} ---")
        
        try:
            start_time = time.time()
            
            # Test constraint mask generation (with caching)
            masks = propagator.create_first_column_masks(first_column, n)
            print(f"Constraint masks: {masks}")
            
            elapsed = time.time() - start_time
            print(f"Processing time: {elapsed:.4f}s")
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Test optimization features
    print(f"\n=== Testing Optimization Features ===")
    
    # Test pre-computation
    propagator.precompute_common_patterns(3, 4, max_patterns=10)
    
    # Test workload optimization
    from core.first_column_enumerator import FirstColumnEnumerator
    enumerator = FirstColumnEnumerator()
    first_columns = enumerator.enumerate_first_columns(3, 5)
    propagator.optimize_for_workload(first_columns, 5)
    
    # Show optimization statistics
    opt_stats = propagator.get_optimization_stats()
    print(f"\nOptimization statistics:")
    for key, value in opt_stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()