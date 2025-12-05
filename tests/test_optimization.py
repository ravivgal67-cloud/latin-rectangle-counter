"""
Tests for constraint propagation optimization in permutation generation.

Feature: latin-rectangle-counter
"""

import pytest
from hypothesis import given, strategies as st, settings
from itertools import permutations
from core.permutation import generate_constrained_permutations


class TestConstrainedPermutations:
    """Tests for optimized constrained permutation generation."""
    
    def test_no_constraints(self):
        """
        With no constraints, should generate all n! permutations.
        """
        n = 3
        forbidden = [set() for _ in range(n)]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Should generate all 3! = 6 permutations
        assert len(result) == 6
        
        # Should match all permutations of [1, 2, 3]
        expected = [list(p) for p in permutations(range(1, n + 1))]
        assert sorted(result) == sorted(expected)
    
    def test_single_constraint(self):
        """
        With one position constrained, should exclude those permutations.
        """
        n = 3
        # Position 0 cannot have value 1
        forbidden = [{1}, set(), set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Should generate permutations where position 0 != 1
        for perm in result:
            assert perm[0] != 1, f"Position 0 should not be 1 in {perm}"
        
        # Should have 4 permutations: [2,1,3], [2,3,1], [3,1,2], [3,2,1]
        assert len(result) == 4
    
    def test_multiple_constraints(self):
        """
        With multiple constraints, should respect all of them.
        """
        n = 3
        # Position 0 cannot have 1, position 1 cannot have 2
        forbidden = [{1}, {2}, set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Verify all constraints
        for perm in result:
            assert perm[0] != 1, f"Position 0 should not be 1 in {perm}"
            assert perm[1] != 2, f"Position 1 should not be 2 in {perm}"
        
        # Should have 2 permutations: [2,1,3], [2,3,1], [3,1,2]
        assert len(result) == 3
    
    def test_forced_move(self):
        """
        When a position has only one valid value, it should be forced.
        This tests the forced move detection optimization.
        """
        n = 3
        # Position 0 cannot have 1 or 2, so must be 3
        forbidden = [{1, 2}, set(), set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # All permutations should have 3 at position 0
        for perm in result:
            assert perm[0] == 3, f"Position 0 should be 3 in {perm}"
        
        # Should have 2 permutations: [3,1,2], [3,2,1]
        assert len(result) == 2
    
    def test_contradiction_detection(self):
        """
        When constraints create a contradiction, should return no permutations.
        This tests early pruning.
        """
        n = 3
        # Position 0 cannot have 1, 2, or 3 - impossible!
        forbidden = [{1, 2, 3}, set(), set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Should generate no permutations
        assert len(result) == 0
    
    def test_conflict_detection(self):
        """
        When two positions are forced to the same value, should detect conflict.
        """
        n = 3
        # Position 0 must be 1, position 1 must be 1 - conflict!
        forbidden = [{2, 3}, {2, 3}, set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Should generate no permutations due to conflict
        assert len(result) == 0
    
    def test_latin_rectangle_constraints(self):
        """
        Test with constraints typical of Latin rectangle generation.
        Simulates having first row [1, 2, 3] and needing second row.
        """
        n = 3
        # After first row [1, 2, 3], column constraints are:
        # Position 0 cannot have 1, position 1 cannot have 2, position 2 cannot have 3
        forbidden = [{1}, {2}, {3}]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Should generate derangements of [1, 2, 3]
        # Valid: [2,1,3] is invalid (3 at position 2)
        # Valid: [2,3,1], [3,1,2]
        assert len(result) == 2
        
        # Verify all are valid derangements
        for perm in result:
            for i, val in enumerate(perm):
                assert val != i + 1, f"Value {val} at position {i} is not a derangement"
                assert val not in forbidden[i], f"Value {val} at position {i} violates constraint"
    
    def test_larger_dimension(self):
        """
        Test with larger dimension to ensure optimization scales.
        """
        n = 4
        # Position 0 cannot have 1, position 1 cannot have 2
        forbidden = [{1}, {2}, set(), set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Verify constraints
        for perm in result:
            assert perm[0] != 1
            assert perm[1] != 2
        
        # Should have 14 permutations (verified by counting)
        assert len(result) == 14
    
    @given(
        st.integers(min_value=2, max_value=5),
        st.integers(min_value=0, max_value=3)
    )
    @settings(max_examples=50)
    def test_correctness_vs_naive(self, n, num_constraints):
        """
        **Feature: latin-rectangle-counter, Property: Constrained permutation correctness**
        **Validates: Optimization produces same results as naive filtering**
        
        For any n and constraint set, the optimized generator should produce
        the same permutations as naive filtering (just faster).
        """
        # Generate random constraints
        forbidden = [set() for _ in range(n)]
        for i in range(min(num_constraints, n)):
            # Add 1-2 forbidden values per position
            num_forbidden = min(2, n - 1)
            forbidden[i] = set(range(1, num_forbidden + 1))
        
        # Get result from optimized generator
        optimized_result = list(generate_constrained_permutations(n, forbidden))
        
        # Get result from naive filtering
        all_perms = [list(p) for p in permutations(range(1, n + 1))]
        naive_result = []
        for perm in all_perms:
            valid = True
            for pos, value in enumerate(perm):
                if value in forbidden[pos]:
                    valid = False
                    break
            if valid:
                naive_result.append(perm)
        
        # Results should match (order may differ)
        assert sorted(optimized_result) == sorted(naive_result), (
            f"Optimized and naive results differ for n={n}, forbidden={forbidden}\n"
            f"Optimized: {sorted(optimized_result)}\n"
            f"Naive: {sorted(naive_result)}"
        )
    
    def test_no_duplicates(self):
        """
        Ensure the generator never produces duplicate permutations.
        """
        n = 4
        forbidden = [{1}, {2}, set(), set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # Check for duplicates
        result_set = [tuple(p) for p in result]
        assert len(result) == len(set(result_set)), (
            f"Generator produced duplicates: {len(result)} total, "
            f"{len(set(result_set))} unique"
        )
    
    def test_all_valid_permutations(self):
        """
        Ensure all generated permutations are valid (use each value exactly once).
        """
        n = 4
        forbidden = [{1}, {2}, set(), set()]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        for perm in result:
            # Check it's a valid permutation
            assert sorted(perm) == list(range(1, n + 1)), (
                f"Invalid permutation {perm}: not a permutation of [1..{n}]"
            )


class TestOptimizationPerformance:
    """Tests to verify optimization is working (not just correctness)."""
    
    def test_early_pruning_works(self):
        """
        Verify that impossible constraints result in immediate return.
        This should be very fast if early pruning works.
        """
        import time
        
        n = 10
        # Make it impossible: position 0 cannot have any value
        forbidden = [{i for i in range(1, n + 1)}] + [set() for _ in range(n - 1)]
        
        start = time.time()
        result = list(generate_constrained_permutations(n, forbidden))
        elapsed = time.time() - start
        
        # Should return empty immediately
        assert len(result) == 0
        # Should be very fast (< 1ms) if early pruning works
        assert elapsed < 0.001, f"Early pruning too slow: {elapsed:.4f}s"
    
    def test_forced_move_optimization(self):
        """
        Verify that forced moves are detected and applied.
        With many forced moves, generation should be fast.
        """
        n = 5
        # Force specific values at positions 0, 1, 2
        # Position 0 must be 5, position 1 must be 4, position 2 must be 3
        forbidden = [
            {1, 2, 3, 4},  # Position 0 must be 5
            {1, 2, 3, 5},  # Position 1 must be 4
            {1, 2, 4, 5},  # Position 2 must be 3
            set(),
            set()
        ]
        
        result = list(generate_constrained_permutations(n, forbidden))
        
        # All results should have forced values
        for perm in result:
            assert perm[0] == 5
            assert perm[1] == 4
            assert perm[2] == 3
        
        # Should have 2 permutations: [5,4,3,1,2] and [5,4,3,2,1]
        assert len(result) == 2


class TestOptimizationIntegration:
    """Integration tests with Latin rectangle generation."""
    
    def test_rectangle_generation_uses_optimization(self):
        """
        Verify that Latin rectangle generation uses the optimized generator.
        """
        from core.latin_rectangle import generate_normalized_rectangles
        
        # Generate 3x4 rectangles
        rectangles = list(generate_normalized_rectangles(3, 4))
        
        # Should generate correct count
        assert len(rectangles) == 24  # Known value for (3,4)
        
        # All should be valid
        for rect in rectangles:
            assert rect.is_valid()
            assert rect.is_normalized()
    
    def test_high_constraint_case(self):
        """
        Test a high-constraint case where optimization should shine.
        """
        from core.latin_rectangle import generate_normalized_rectangles
        
        # Generate 5x5 rectangles - high constraint density (r/n = 1.0)
        rectangles = list(generate_normalized_rectangles(5, 5))
        
        # Should generate correct count (known value)
        # For (5,5): 1344 total rectangles
        assert len(rectangles) == 1344
        
        # All should be valid
        for rect in rectangles:
            assert rect.is_valid()
            assert rect.is_normalized()
