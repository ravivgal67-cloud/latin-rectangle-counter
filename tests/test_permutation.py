"""
Property-based tests for permutation utilities.

Feature: latin-rectangle-counter
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.permutation import permutation_sign


class TestPermutationSign:
    """Tests for permutation sign computation."""
    
    @given(st.permutations(range(1, 11)))
    @settings(max_examples=100)
    def test_permutation_sign_correctness(self, perm):
        """
        **Feature: latin-rectangle-counter, Property 9: Permutation sign correctness**
        **Validates: Requirements 3.3**
        
        For any permutation, the computed sign should match the standard definition:
        +1 if the number of inversions is even, -1 if odd.
        """
        # Compute sign using the function
        computed_sign = permutation_sign(list(perm))
        
        # Independently compute sign by counting inversions
        inversions = 0
        perm_list = list(perm)
        for i in range(len(perm_list)):
            for j in range(i + 1, len(perm_list)):
                if perm_list[i] > perm_list[j]:
                    inversions += 1
        
        expected_sign = 1 if inversions % 2 == 0 else -1
        
        assert computed_sign == expected_sign, (
            f"Sign mismatch for permutation {perm_list}: "
            f"computed {computed_sign}, expected {expected_sign} "
            f"(inversions: {inversions})"
        )
    
    def test_identity_permutation_positive(self):
        """Identity permutation should always have sign +1."""
        assert permutation_sign([1, 2, 3, 4, 5]) == 1
        assert permutation_sign([1]) == 1
        assert permutation_sign([1, 2]) == 1
    
    def test_single_transposition_negative(self):
        """A single transposition should have sign -1."""
        assert permutation_sign([2, 1, 3]) == -1
        assert permutation_sign([1, 3, 2]) == -1
        assert permutation_sign([2, 1]) == -1
    
    def test_empty_permutation(self):
        """Empty permutation should have sign +1."""
        assert permutation_sign([]) == 1
    
    def test_known_permutations(self):
        """Test known permutations with known signs."""
        # [3, 2, 1] has 3 inversions: (0,1), (0,2), (1,2) -> odd -> -1
        assert permutation_sign([3, 2, 1]) == -1
        
        # [2, 3, 1] has 2 inversions: (0,2), (1,2) -> even -> +1
        assert permutation_sign([2, 3, 1]) == 1
        
        # [3, 1, 2] has 2 inversions: (0,1), (0,2) -> even -> +1
        assert permutation_sign([3, 1, 2]) == 1



from core.permutation import is_derangement, count_derangements
from itertools import permutations


class TestDerangements:
    """Tests for derangement utilities."""
    
    @given(st.integers(min_value=0, max_value=8))
    @settings(max_examples=100)
    def test_derangement_count_matches_known_values(self, n):
        """
        **Feature: latin-rectangle-counter, Property: Derangement count correctness**
        **Validates: Requirements 2.2**
        
        For any small n, the derangement count should match known values.
        We verify this by generating all permutations and counting derangements.
        """
        computed_count = count_derangements(n)
        
        # For small n, verify by brute force
        if n <= 8:
            # Generate all permutations and count derangements
            all_perms = list(permutations(range(1, n + 1)))
            actual_derangements = sum(1 for perm in all_perms if is_derangement(list(perm)))
            
            assert computed_count == actual_derangements, (
                f"Derangement count mismatch for n={n}: "
                f"computed {computed_count}, actual {actual_derangements}"
            )
    
    def test_known_derangement_values(self):
        """Test against known derangement sequence values."""
        # Known values from OEIS A000166
        known_values = {
            0: 1,
            1: 0,
            2: 1,
            3: 2,
            4: 9,
            5: 44,
            6: 265,
            7: 1854,
            8: 14833,
        }
        
        for n, expected in known_values.items():
            assert count_derangements(n) == expected, (
                f"Derangement count for n={n} should be {expected}, "
                f"got {count_derangements(n)}"
            )
    
    def test_is_derangement_examples(self):
        """Test is_derangement with specific examples."""
        # Derangements
        assert is_derangement([2, 1]) == True
        assert is_derangement([2, 3, 1]) == True
        assert is_derangement([3, 1, 2]) == True
        
        # Not derangements
        assert is_derangement([1, 2, 3]) == False  # All in place
        assert is_derangement([2, 2, 1]) == False  # 2 in position 1 (if valid perm)
        assert is_derangement([2, 1, 3]) == False  # 3 in position 2



from core.permutation import compute_determinant


class TestDeterminant:
    """Unit tests for determinant computation."""
    
    def test_identity_matrix(self):
        """Identity matrix should have determinant 1."""
        # 2x2 identity
        assert compute_determinant([[1, 0], [0, 1]]) == 1
        
        # 3x3 identity
        assert compute_determinant([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ]) == 1
        
        # 4x4 identity
        assert compute_determinant([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]) == 1
    
    def test_all_ones_except_diagonal(self):
        """
        Matrix with 0 on diagonal and 1 elsewhere.
        This is the key matrix for r=2 counting.
        """
        # 2x2: [[0, 1], [1, 0]] -> det = -1
        assert compute_determinant([[0, 1], [1, 0]]) == -1
        
        # 3x3: [[0, 1, 1], [1, 0, 1], [1, 1, 0]] -> det = 2
        assert compute_determinant([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ]) == 2
        
        # 4x4: [[0, 1, 1, 1], [1, 0, 1, 1], [1, 1, 0, 1], [1, 1, 1, 0]] -> det = -3
        assert compute_determinant([
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0]
        ]) == -3
    
    def test_known_matrices(self):
        """Test determinant with known values."""
        # [[1, 2], [3, 4]] -> det = -2
        assert compute_determinant([[1, 2], [3, 4]]) == -2
        
        # [[2, 1], [1, 2]] -> det = 3
        assert compute_determinant([[2, 1], [1, 2]]) == 3
        
        # [[1, 2, 3], [4, 5, 6], [7, 8, 9]] -> det = 0 (singular)
        assert compute_determinant([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ]) == 0
    
    def test_single_element_matrix(self):
        """Single element matrix determinant is the element itself."""
        assert compute_determinant([[5]]) == 5
        assert compute_determinant([[0]]) == 0
        assert compute_determinant([[-3]]) == -3
