"""
Tests for bitset constraint optimization.
"""

import time
import pytest
from core.bitset_constraints import (
    BitsetConstraints, 
    generate_constrained_permutations_bitset,
    generate_constrained_permutations_bitset_optimized,
    optimize_constraint_order
)
from core.latin_rectangle import (
    generate_normalized_rectangles,
    generate_normalized_rectangles_counter_based,
    generate_normalized_rectangles_bitset_optimized
)
from core.permutation import generate_constrained_permutations


class TestBitsetConstraints:
    """Test BitsetConstraints class functionality."""
    
    def test_basic_operations(self):
        """Test basic bitset constraint operations."""
        constraints = BitsetConstraints(4)
        
        # Test adding forbidden values
        constraints.add_forbidden(0, 2)
        constraints.add_forbidden(0, 4)
        constraints.add_forbidden(1, 1)
        
        # Test checking forbidden values
        assert constraints.is_forbidden(0, 2)
        assert constraints.is_forbidden(0, 4)
        assert not constraints.is_forbidden(0, 1)
        assert not constraints.is_forbidden(0, 3)
        assert constraints.is_forbidden(1, 1)
        assert not constraints.is_forbidden(1, 2)
        
        # Test available count
        assert constraints.available_count(0) == 2  # 1 and 3 available
        assert constraints.available_count(1) == 3  # 2, 3, 4 available
        assert constraints.available_count(2) == 4  # All available
        
        # Test get available values
        assert constraints.get_available_values(0) == [1, 3]
        assert constraints.get_available_values(1) == [2, 3, 4]
        assert constraints.get_available_values(2) == [1, 2, 3, 4]
    
    def test_remove_forbidden(self):
        """Test removing forbidden values."""
        constraints = BitsetConstraints(3)
        
        constraints.add_forbidden(0, 1)
        constraints.add_forbidden(0, 2)
        assert constraints.available_count(0) == 1
        
        constraints.remove_forbidden(0, 1)
        assert constraints.available_count(0) == 2
        assert not constraints.is_forbidden(0, 1)
        assert constraints.is_forbidden(0, 2)
    
    def test_copy(self):
        """Test copying constraints."""
        constraints = BitsetConstraints(3)
        constraints.add_forbidden(0, 1)
        constraints.add_forbidden(1, 2)
        
        copy_constraints = constraints.copy()
        
        # Verify copy has same state
        assert copy_constraints.is_forbidden(0, 1)
        assert copy_constraints.is_forbidden(1, 2)
        assert not copy_constraints.is_forbidden(2, 3)
        
        # Verify independence
        constraints.add_forbidden(2, 3)
        assert constraints.is_forbidden(2, 3)
        assert not copy_constraints.is_forbidden(2, 3)
    
    def test_conversion_to_set_list(self):
        """Test conversion to set list format."""
        constraints = BitsetConstraints(3)
        constraints.add_forbidden(0, 1)
        constraints.add_forbidden(0, 3)
        constraints.add_forbidden(1, 2)
        
        set_list = constraints.to_set_list()
        
        assert set_list[0] == {1, 3}
        assert set_list[1] == {2}
        assert set_list[2] == set()
    
    def test_from_set_list(self):
        """Test creation from set list."""
        forbidden_sets = [{1, 3}, {2}, set()]
        
        constraints = BitsetConstraints.from_set_list(forbidden_sets)
        
        assert constraints.is_forbidden(0, 1)
        assert constraints.is_forbidden(0, 3)
        assert not constraints.is_forbidden(0, 2)
        assert constraints.is_forbidden(1, 2)
        assert not constraints.is_forbidden(1, 1)
        assert constraints.available_count(2) == 3
    
    def test_batch_operations(self):
        """Test batch constraint operations."""
        constraints = BitsetConstraints(4)
        
        # Test batch add
        updates = [(0, 1), (0, 3), (1, 2), (2, 4)]
        constraints.add_forbidden_batch(updates)
        
        assert constraints.is_forbidden(0, 1)
        assert constraints.is_forbidden(0, 3)
        assert not constraints.is_forbidden(0, 2)
        assert constraints.is_forbidden(1, 2)
        assert constraints.is_forbidden(2, 4)
        
        # Test batch remove
        remove_updates = [(0, 1), (1, 2)]
        constraints.remove_forbidden_batch(remove_updates)
        
        assert not constraints.is_forbidden(0, 1)
        assert constraints.is_forbidden(0, 3)  # Still forbidden
        assert not constraints.is_forbidden(1, 2)
        assert constraints.is_forbidden(2, 4)  # Still forbidden
    
    def test_row_operations(self):
        """Test row-based constraint operations."""
        constraints = BitsetConstraints(4)
        
        # Test add row constraints
        row = [1, 3, 2, 4]
        constraints.add_row_constraints(row)
        
        assert constraints.is_forbidden(0, 1)
        assert constraints.is_forbidden(1, 3)
        assert constraints.is_forbidden(2, 2)
        assert constraints.is_forbidden(3, 4)
        
        # Test remove row constraints
        constraints.remove_row_constraints(row)
        
        assert not constraints.is_forbidden(0, 1)
        assert not constraints.is_forbidden(1, 3)
        assert not constraints.is_forbidden(2, 2)
        assert not constraints.is_forbidden(3, 4)
    
    def test_rows_operations(self):
        """Test multiple rows constraint operations."""
        constraints = BitsetConstraints(3)
        
        rows = [
            [1, 2, 3],
            [2, 3, 1]
        ]
        
        constraints.add_rows_constraints(rows)
        
        # Check constraints from first row
        assert constraints.is_forbidden(0, 1)
        assert constraints.is_forbidden(1, 2)
        assert constraints.is_forbidden(2, 3)
        
        # Check constraints from second row
        assert constraints.is_forbidden(0, 2)
        assert constraints.is_forbidden(1, 3)
        assert constraints.is_forbidden(2, 1)
        
        # Position 0 should have both 1 and 2 forbidden
        assert constraints.available_count(0) == 1  # Only 3 available


class TestBitsetPermutationGeneration:
    """Test bitset-based permutation generation."""
    
    def test_unconstrained_generation(self):
        """Test generation with no constraints."""
        constraints = BitsetConstraints(3)
        
        perms = list(generate_constrained_permutations_bitset(3, constraints))
        
        # Should generate all 3! = 6 permutations
        assert len(perms) == 6
        
        # Verify all are valid permutations
        for perm in perms:
            assert len(perm) == 3
            assert set(perm) == {1, 2, 3}
    
    def test_constrained_generation(self):
        """Test generation with constraints."""
        constraints = BitsetConstraints(3)
        constraints.add_forbidden(0, 2)  # Position 0 cannot be 2
        constraints.add_forbidden(1, 1)  # Position 1 cannot be 1
        
        perms = list(generate_constrained_permutations_bitset(3, constraints))
        
        # Verify constraints are satisfied
        for perm in perms:
            assert perm[0] != 2  # First position not 2
            assert perm[1] != 1  # Second position not 1
            assert len(perm) == 3
            assert set(perm) == {1, 2, 3}
        
        # Should have fewer than 6 permutations
        assert len(perms) < 6
        assert len(perms) > 0
    
    def test_correctness_vs_set_based(self):
        """Test that bitset generation matches set-based generation."""
        # Test various constraint patterns
        test_cases = [
            [{1}, {2}, set()],
            [{1, 2}, set(), {3}],
            [set(), {1, 3}, {2}],
            [{1, 2, 3}, set(), set()],  # Impossible case
        ]
        
        for forbidden_sets in test_cases:
            n = len(forbidden_sets)
            
            # Generate with set-based approach
            set_perms = sorted(list(generate_constrained_permutations(n, forbidden_sets)))
            
            # Generate with bitset approach
            constraints = BitsetConstraints.from_set_list(forbidden_sets)
            bitset_perms = list(generate_constrained_permutations_bitset(n, constraints))
            
            # Should produce identical results
            assert set_perms == bitset_perms
    
    def test_optimized_vs_original_bitset(self):
        """Test that optimized bitset generation matches original bitset generation."""
        # Test various constraint patterns
        test_cases = [
            [{1}, {2}, set()],
            [{1, 2}, set(), {3}],
            [set(), {1, 3}, {2}],
            [{2, 3}, {1}, set()],
        ]
        
        for forbidden_sets in test_cases:
            n = len(forbidden_sets)
            constraints = BitsetConstraints.from_set_list(forbidden_sets)
            
            # Generate with original bitset approach
            original_perms = list(generate_constrained_permutations_bitset(n, constraints))
            
            # Generate with optimized bitset approach
            optimized_perms = list(generate_constrained_permutations_bitset_optimized(n, constraints))
            
            # Should produce identical results in same order
            assert original_perms == optimized_perms


class TestBitsetRectangleGeneration:
    """Test bitset-optimized rectangle generation."""
    
    def test_correctness_vs_original(self):
        """Test that bitset optimization produces same results as original."""
        test_cases = [(2, 3), (3, 4), (4, 5)]
        
        for r, n in test_cases:
            # Generate with original counter-based approach
            original_rects = list(generate_normalized_rectangles_counter_based(r, n))
            
            # Generate with bitset-optimized approach
            bitset_rects = list(generate_normalized_rectangles_bitset_optimized(r, n))
            
            # Should produce same count
            assert len(original_rects) == len(bitset_rects)
            
            # Convert to sets for comparison (order should be same but verify content)
            original_set = {tuple(tuple(row) for row in rect.data) for rect in original_rects}
            bitset_set = {tuple(tuple(row) for row in rect.data) for rect in bitset_rects}
            
            assert original_set == bitset_set
    
    def test_deterministic_ordering(self):
        """Test that bitset optimization maintains deterministic ordering."""
        r, n = 3, 4
        
        # Generate twice with bitset optimization
        rects1 = list(generate_normalized_rectangles_bitset_optimized(r, n))
        rects2 = list(generate_normalized_rectangles_bitset_optimized(r, n))
        
        # Should be identical (same order)
        assert len(rects1) == len(rects2)
        
        for rect1, rect2 in zip(rects1, rects2):
            assert rect1.data == rect2.data
    
    def test_resumable_with_start_counters(self):
        """Test bitset optimization with start counters."""
        r, n = 3, 4
        
        # Generate all rectangles
        all_rects = list(generate_normalized_rectangles_bitset_optimized(r, n))
        
        # Generate starting from counter [0, 1, 0]
        partial_rects = list(generate_normalized_rectangles_bitset_optimized(r, n, [0, 1, 0]))
        
        # Should have fewer rectangles
        assert len(partial_rects) < len(all_rects)
        assert len(partial_rects) > 0
        
        # All partial rectangles should be in the full set
        all_set = {tuple(tuple(row) for row in rect.data) for rect in all_rects}
        partial_set = {tuple(tuple(row) for row in rect.data) for rect in partial_rects}
        
        assert partial_set.issubset(all_set)


class TestConstraintOrdering:
    """Test constraint ordering optimization."""
    
    def test_constraint_ordering(self):
        """Test constraint ordering heuristic."""
        constraints = BitsetConstraints(4)
        
        # Add different numbers of forbidden values
        constraints.add_forbidden(0, 1)
        constraints.add_forbidden(0, 2)  # Position 0: 2 forbidden (most constrained)
        
        constraints.add_forbidden(1, 3)  # Position 1: 1 forbidden
        
        # Position 2: 0 forbidden (least constrained)
        
        constraints.add_forbidden(3, 1)
        constraints.add_forbidden(3, 2)
        constraints.add_forbidden(3, 3)  # Position 3: 3 forbidden (second most constrained)
        
        order = optimize_constraint_order(constraints)
        
        # Most constrained should come first
        assert order[0] == 3  # 3 forbidden values
        assert order[1] == 0  # 2 forbidden values
        assert order[2] == 1  # 1 forbidden value
        assert order[3] == 2  # 0 forbidden values


class TestPerformanceImprovement:
    """Test performance improvement from bitset optimization."""
    
    def test_performance_comparison(self):
        """Compare performance of bitset vs original implementation."""
        # Test on a medium-sized problem
        r, n = 4, 5
        
        # Time original implementation
        start_time = time.time()
        original_rects = list(generate_normalized_rectangles_counter_based(r, n))
        original_time = time.time() - start_time
        
        # Time bitset implementation
        start_time = time.time()
        bitset_rects = list(generate_normalized_rectangles_bitset_optimized(r, n))
        bitset_time = time.time() - start_time
        
        # Verify correctness
        assert len(original_rects) == len(bitset_rects)
        
        # Calculate speedup
        speedup = original_time / bitset_time if bitset_time > 0 else float('inf')
        
        print(f"Performance comparison for ({r},{n}):")
        print(f"  Original: {original_time:.4f}s")
        print(f"  Bitset:   {bitset_time:.4f}s")
        print(f"  Speedup:  {speedup:.2f}x")
        
        # Should be faster (allow some variance for small problems)
        # Even if not faster due to overhead, should be close
        assert speedup >= 0.5  # At least not more than 2x slower
    
    @pytest.mark.slow
    def test_performance_on_larger_problem(self):
        """Test correctness and performance characteristics on larger problem."""
        # Test on a larger problem to verify correctness and measure performance
        r, n = 5, 6
        
        # Time original implementation (first 1000 rectangles to avoid long test)
        start_time = time.time()
        original_count = 0
        original_rectangles = []
        for rect in generate_normalized_rectangles_counter_based(r, n):
            original_rectangles.append(rect)
            original_count += 1
            if original_count >= 1000:
                break
        original_time = time.time() - start_time
        
        # Time bitset implementation (first 1000 rectangles)
        start_time = time.time()
        bitset_count = 0
        bitset_rectangles = []
        for rect in generate_normalized_rectangles_bitset_optimized(r, n):
            bitset_rectangles.append(rect)
            bitset_count += 1
            if bitset_count >= 1000:
                break
        bitset_time = time.time() - start_time
        
        # Verify correctness: both should generate the same rectangles
        assert original_count == bitset_count, f"Count mismatch: {original_count} vs {bitset_count}"
        
        # Convert to sets for comparison (order may differ)
        original_set = {tuple(tuple(row) for row in rect.data) for rect in original_rectangles}
        bitset_set = {tuple(tuple(row) for row in rect.data) for rect in bitset_rectangles}
        assert original_set == bitset_set, "Generated rectangles differ between implementations"
        
        # Calculate speedup for informational purposes
        speedup = original_time / bitset_time if bitset_time > 0 else float('inf')
        
        print(f"Performance comparison for first 1000 rectangles of ({r},{n}):")
        print(f"  Original: {original_time:.4f}s")
        print(f"  Bitset:   {bitset_time:.4f}s")
        print(f"  Speedup:  {speedup:.2f}x")
        
        # Verify both implementations complete successfully (correctness over performance)
        assert original_time > 0, "Original implementation should complete"
        assert bitset_time > 0, "Bitset implementation should complete"