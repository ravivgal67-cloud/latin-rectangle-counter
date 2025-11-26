"""
Property-based tests for LatinRectangle class.

Feature: latin-rectangle-counter
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.latin_rectangle import LatinRectangle
from core.permutation import permutation_sign


# Custom strategy for generating valid Latin rectangles
@st.composite
def latin_rectangle_strategy(draw, min_r=2, max_r=5, min_n=2, max_n=6):
    """
    Generate a valid Latin rectangle for testing.
    
    For simplicity, we generate normalized rectangles by:
    1. Starting with identity first row
    2. Adding valid subsequent rows that don't conflict with columns
    """
    n = draw(st.integers(min_value=min_n, max_value=max_n))
    r = draw(st.integers(min_value=min_r, max_value=min(max_r, n)))
    
    # Start with identity first row
    data = [list(range(1, n + 1))]
    
    # Generate remaining rows
    for _ in range(r - 1):
        # Generate a valid row by creating a permutation that doesn't
        # conflict with existing columns
        attempts = 0
        max_attempts = 1000
        
        while attempts < max_attempts:
            # Generate a random permutation
            row = draw(st.permutations(range(1, n + 1)))
            row_list = list(row)
            
            # Check if it conflicts with existing columns
            valid = True
            for col_idx in range(n):
                column_values = [data[row_idx][col_idx] for row_idx in range(len(data))]
                if row_list[col_idx] in column_values:
                    valid = False
                    break
            
            if valid:
                data.append(row_list)
                break
            
            attempts += 1
        
        # If we couldn't find a valid row, return what we have
        if len(data) < r:
            break
    
    return LatinRectangle(len(data), n, data)


class TestSignComputation:
    """Tests for sign computation correctness."""
    
    @given(latin_rectangle_strategy(min_r=2, max_r=4, min_n=2, max_n=5))
    @settings(max_examples=100, deadline=None)
    def test_sign_computation_correctness(self, rect):
        """
        **Feature: latin-rectangle-counter, Property 8: Sign computation correctness**
        **Validates: Requirements 3.1**
        
        For any Latin rectangle, the computed sign should equal the product
        of the signs of all its row permutations.
        """
        # Compute sign using the method
        computed_sign = rect.compute_sign()
        
        # Independently compute sign as product of row signs
        expected_sign = 1
        for row in rect.data:
            expected_sign *= permutation_sign(row)
        
        assert computed_sign == expected_sign, (
            f"Sign computation mismatch for rectangle {rect.data}: "
            f"computed {computed_sign}, expected {expected_sign}"
        )
        
        # Sign should be either +1 or -1
        assert computed_sign in [1, -1], (
            f"Sign should be +1 or -1, got {computed_sign}"
        )
    
    def test_sign_with_known_rectangles(self):
        """Test sign computation with known rectangles."""
        # 2×3 rectangle with identity first row and even second row
        # [1, 2, 3] -> sign = +1
        # [2, 3, 1] -> sign = +1 (2 inversions)
        # Total sign = +1 * +1 = +1
        rect1 = LatinRectangle(2, 3, [[1, 2, 3], [2, 3, 1]])
        assert rect1.compute_sign() == 1
        
        # 2×3 rectangle with identity first row and odd second row
        # [1, 2, 3] -> sign = +1
        # [3, 1, 2] -> sign = +1 (2 inversions)
        # Total sign = +1 * +1 = +1
        rect2 = LatinRectangle(2, 3, [[1, 2, 3], [3, 1, 2]])
        assert rect2.compute_sign() == 1
        
        # 2×2 rectangle
        # [1, 2] -> sign = +1
        # [2, 1] -> sign = -1 (1 inversion)
        # Total sign = +1 * -1 = -1
        rect3 = LatinRectangle(2, 2, [[1, 2], [2, 1]])
        assert rect3.compute_sign() == -1


class TestNormalizedFirstRow:
    """Tests for normalized first row property."""
    
    @given(latin_rectangle_strategy(min_r=2, max_r=4, min_n=2, max_n=6))
    @settings(max_examples=100, deadline=None)
    def test_normalized_first_row(self, rect):
        """
        **Feature: latin-rectangle-counter, Property 5: Normalized first row**
        **Validates: Requirements 2.1**
        
        For any generated normalized Latin rectangle with dimensions (r, n),
        the first row should be the identity permutation [1, 2, 3, ..., n].
        """
        # Our generator creates normalized rectangles, so this should always pass
        expected_first_row = list(range(1, rect.cols + 1))
        
        assert rect.data[0] == expected_first_row, (
            f"First row should be identity permutation {expected_first_row}, "
            f"got {rect.data[0]}"
        )
        
        # Also verify is_normalized() returns True
        assert rect.is_normalized(), (
            f"Rectangle should be normalized but is_normalized() returned False"
        )
    
    def test_non_normalized_rectangle(self):
        """Test that non-normalized rectangles are correctly identified."""
        # Rectangle with non-identity first row
        rect = LatinRectangle(2, 3, [[2, 1, 3], [1, 3, 2]])
        assert not rect.is_normalized()
        
        # Rectangle with identity first row should be normalized
        rect2 = LatinRectangle(2, 3, [[1, 2, 3], [2, 3, 1]])
        assert rect2.is_normalized()


class TestValidRectangleStructure:
    """Tests for valid rectangle structure property."""
    
    @given(latin_rectangle_strategy(min_r=2, max_r=4, min_n=2, max_n=6))
    @settings(max_examples=100, deadline=None)
    def test_valid_rectangle_structure(self, rect):
        """
        **Feature: latin-rectangle-counter, Property 6: Valid rectangle structure**
        **Validates: Requirements 2.2**
        
        For any generated normalized Latin rectangle, each row should be a
        permutation of [1, 2, ..., n] and no column should contain duplicate values.
        """
        n = rect.cols
        expected_set = set(range(1, n + 1))
        
        # Check each row is a permutation
        for row_idx, row in enumerate(rect.data):
            assert set(row) == expected_set, (
                f"Row {row_idx} is not a permutation of [1..{n}]: {row}"
            )
            assert len(row) == n, (
                f"Row {row_idx} has incorrect length: {len(row)} != {n}"
            )
        
        # Check no column has duplicates
        for col_idx in range(n):
            column_values = [rect.data[row_idx][col_idx] for row_idx in range(rect.rows)]
            assert len(column_values) == len(set(column_values)), (
                f"Column {col_idx} has duplicate values: {column_values}"
            )
        
        # Also verify is_valid() returns True
        assert rect.is_valid(), (
            f"Rectangle should be valid but is_valid() returned False"
        )
    
    def test_invalid_rectangles(self):
        """Test that invalid rectangles are correctly identified."""
        # Rectangle with duplicate in column
        rect1 = LatinRectangle(2, 3, [[1, 2, 3], [1, 3, 2]])
        assert not rect1.is_valid()
        
        # Rectangle with invalid row (not a permutation)
        rect2 = LatinRectangle(2, 3, [[1, 2, 3], [1, 1, 1]])
        assert not rect2.is_valid()
        
        # Valid rectangle
        rect3 = LatinRectangle(2, 3, [[1, 2, 3], [2, 3, 1]])
        assert rect3.is_valid()
        
        # Rectangle with wrong number of rows
        rect4 = LatinRectangle(3, 3, [[1, 2, 3], [2, 3, 1]])  # Says 3 rows but has 2
        assert not rect4.is_valid()
        
        # Rectangle with wrong number of columns in a row
        rect5 = LatinRectangle(2, 3, [[1, 2, 3], [2, 3]])  # Second row too short
        assert not rect5.is_valid()
        
        # Empty rectangle (edge case)
        rect6 = LatinRectangle(0, 0, [])
        assert not rect6.is_normalized()  # Empty can't be normalized
        
        # Rectangle with 0 columns
        rect7 = LatinRectangle(2, 0, [[], []])
        assert not rect7.is_normalized()
    
    def test_rectangle_equality(self):
        """Test __eq__ method for rectangle equality."""
        rect1 = LatinRectangle(2, 3, [[1, 2, 3], [2, 3, 1]])
        rect2 = LatinRectangle(2, 3, [[1, 2, 3], [2, 3, 1]])
        rect3 = LatinRectangle(2, 3, [[1, 2, 3], [3, 1, 2]])
        
        # Same data should be equal
        assert rect1 == rect2
        
        # Different data should not be equal
        assert rect1 != rect3
        
        # Comparison with non-LatinRectangle should return False
        assert rect1 != "not a rectangle"
        assert rect1 != [[1, 2, 3], [2, 3, 1]]
    
    def test_rectangle_repr(self):
        """Test __repr__ method for string representation."""
        rect = LatinRectangle(2, 3, [[1, 2, 3], [2, 3, 1]])
        repr_str = repr(rect)
        
        # Should contain dimensions and data
        assert "2×3" in repr_str or "2x3" in repr_str
        assert "[[1, 2, 3], [2, 3, 1]]" in repr_str



from core.latin_rectangle import generate_normalized_rectangles


class TestGenerationCompleteness:
    """Tests for generation completeness and uniqueness."""
    
    @given(
        st.integers(min_value=2, max_value=4).flatmap(
            lambda n: st.tuples(st.just(n), st.integers(min_value=2, max_value=min(4, n)))
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_generation_completeness_and_uniqueness(self, dims):
        """
        **Feature: latin-rectangle-counter, Property 7: Generation completeness and uniqueness**
        **Validates: Requirements 2.3**
        
        For any small dimensions (r, n) where exhaustive verification is feasible,
        the generator should produce exactly the known count of valid normalized
        Latin rectangles with no duplicates.
        """
        n, r = dims
        
        # Generate all rectangles
        rectangles = list(generate_normalized_rectangles(r, n))
        
        # Check all are valid and normalized
        for rect in rectangles:
            assert rect.is_valid(), (
                f"Generated rectangle is not valid: {rect.data}"
            )
            assert rect.is_normalized(), (
                f"Generated rectangle is not normalized: {rect.data}"
            )
            assert rect.rows == r and rect.cols == n, (
                f"Generated rectangle has wrong dimensions: "
                f"expected ({r}, {n}), got ({rect.rows}, {rect.cols})"
            )
        
        # Check for uniqueness (no duplicates)
        # Convert to tuples for hashability
        rect_tuples = [tuple(tuple(row) for row in rect.data) for rect in rectangles]
        unique_rects = set(rect_tuples)
        
        assert len(rect_tuples) == len(unique_rects), (
            f"Generator produced duplicates for ({r}, {n}): "
            f"generated {len(rect_tuples)}, unique {len(unique_rects)}"
        )
        
        # For very small dimensions, verify against known counts
        # These are known values from combinatorial theory
        known_counts = {
            (2, 2): 1,   # Only [[1,2], [2,1]]
            (2, 3): 2,   # Two derangements of [1,2,3]
            (2, 4): 9,   # Nine derangements of [1,2,3,4]
            (3, 3): 2,   # Two 3×3 normalized Latin rectangles
            (3, 4): 24,  # Twenty-four 3×4 normalized Latin rectangles
        }
        
        if (r, n) in known_counts:
            expected_count = known_counts[(r, n)]
            assert len(rectangles) == expected_count, (
                f"Generated count mismatch for ({r}, {n}): "
                f"expected {expected_count}, got {len(rectangles)}"
            )
    
    def test_generation_small_cases(self):
        """Test generation for specific small cases with known results."""
        # Test r=2, n=2: should generate exactly 1 rectangle
        rects_2_2 = list(generate_normalized_rectangles(2, 2))
        assert len(rects_2_2) == 1
        assert rects_2_2[0].data == [[1, 2], [2, 1]]
        
        # Test r=2, n=3: should generate exactly 2 rectangles (derangements)
        rects_2_3 = list(generate_normalized_rectangles(2, 3))
        assert len(rects_2_3) == 2
        
        # Both should be valid and normalized
        for rect in rects_2_3:
            assert rect.is_valid()
            assert rect.is_normalized()
            assert rect.data[0] == [1, 2, 3]  # First row is identity
        
        # Check the two derangements are present
        second_rows = [rect.data[1] for rect in rects_2_3]
        assert [2, 3, 1] in second_rows
        assert [3, 1, 2] in second_rows
        
        # Test r=3, n=3: should generate exactly 2 rectangles
        rects_3_3 = list(generate_normalized_rectangles(3, 3))
        assert len(rects_3_3) == 2
        
        # Both should be valid and normalized
        for rect in rects_3_3:
            assert rect.is_valid()
            assert rect.is_normalized()
            assert rect.data[0] == [1, 2, 3]  # First row is identity
        
        # The two 3×3 normalized Latin rectangles
        expected_rects = [
            [[1, 2, 3], [2, 3, 1], [3, 1, 2]],
            [[1, 2, 3], [3, 1, 2], [2, 3, 1]]
        ]
        actual_data = [rect.data for rect in rects_3_3]
        for expected in expected_rects:
            assert expected in actual_data
