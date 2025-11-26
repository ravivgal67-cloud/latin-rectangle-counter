"""
Tests for input validation module.

This module contains unit tests and property-based tests for validating
dimension specifications and parsing user input.
"""

import pytest
from hypothesis import given, strategies as st

from core.validation import (
    DimensionSpec,
    DimensionType,
    ValidationResult,
    validate_dimensions,
    parse_input
)


# Property-Based Tests

@given(
    r=st.integers(min_value=2, max_value=10),
    n=st.integers(min_value=2, max_value=10)
)
def test_property_valid_dimension_acceptance(r, n):
    """
    **Feature: latin-rectangle-counter, Property 1: Valid dimension acceptance**
    **Validates: Requirements 1.1**
    
    For any dimension pair (r, n) where 2 ≤ r ≤ n and n ≥ 2,
    the input validation should accept the dimensions as valid.
    """
    # Only test when r <= n (valid constraint)
    if r <= n:
        result = validate_dimensions(r=r, n=n)
        assert result.is_valid, f"Expected valid dimensions for r={r}, n={n}, but got: {result.error_message}"
        assert result.error_message is None


@given(
    r=st.one_of(
        st.integers(max_value=1),  # r < 2
        st.integers(min_value=11, max_value=20)  # r > n (when n is in valid range)
    ),
    n=st.integers(min_value=2, max_value=10)
)
def test_property_invalid_dimension_rejection_r(r, n):
    """
    **Feature: latin-rectangle-counter, Property 2: Invalid dimension rejection**
    **Validates: Requirements 1.4**
    
    For any dimension pair (r, n) where r > n or r < 2,
    the input validation should reject the dimensions and report an error.
    """
    result = validate_dimensions(r=r, n=n)
    assert not result.is_valid, f"Expected invalid dimensions for r={r}, n={n}, but validation passed"
    assert result.error_message is not None
    assert len(result.error_message) > 0


@given(
    r=st.integers(min_value=2, max_value=10),
    n=st.integers(max_value=1)  # n < 2
)
def test_property_invalid_dimension_rejection_n(r, n):
    """
    **Feature: latin-rectangle-counter, Property 2: Invalid dimension rejection**
    **Validates: Requirements 1.4**
    
    For any dimension pair (r, n) where n < 2,
    the input validation should reject the dimensions and report an error.
    """
    result = validate_dimensions(r=r, n=n)
    assert not result.is_valid, f"Expected invalid dimensions for r={r}, n={n}, but validation passed"
    assert result.error_message is not None
    assert len(result.error_message) > 0


# Unit Tests

def test_validate_dimensions_valid_single():
    """Test validation of valid single (r, n) pair."""
    result = validate_dimensions(r=2, n=3)
    assert result.is_valid
    assert result.error_message is None


def test_validate_dimensions_r_too_small():
    """Test validation rejects r < 2."""
    result = validate_dimensions(r=1, n=3)
    assert not result.is_valid
    assert "r must be at least 2" in result.error_message


def test_validate_dimensions_n_too_small():
    """Test validation rejects n < 2."""
    result = validate_dimensions(r=2, n=1)
    assert not result.is_valid
    assert "n must be at least 2" in result.error_message


def test_validate_dimensions_r_greater_than_n():
    """Test validation rejects r > n."""
    result = validate_dimensions(r=5, n=3)
    assert not result.is_valid
    assert "r must satisfy 2 ≤ r ≤ n" in result.error_message


def test_validate_dimensions_valid_n_only():
    """Test validation of valid n for all_for_n type."""
    result = validate_dimensions(n=5)
    assert result.is_valid
    assert result.error_message is None


def test_validate_dimensions_n_only_too_small():
    """Test validation rejects n < 2 for all_for_n type."""
    result = validate_dimensions(n=1)
    assert not result.is_valid
    assert "n must be at least 2" in result.error_message


def test_validate_dimensions_valid_range():
    """Test validation of valid range."""
    result = validate_dimensions(n_start=3, n_end=6)
    assert result.is_valid
    assert result.error_message is None


def test_validate_dimensions_range_start_too_small():
    """Test validation rejects n_start < 2."""
    result = validate_dimensions(n_start=1, n_end=5)
    assert not result.is_valid
    assert "n_start must be at least 2" in result.error_message


def test_validate_dimensions_range_end_too_small():
    """Test validation rejects n_end < 2."""
    result = validate_dimensions(n_start=2, n_end=1)
    assert not result.is_valid
    assert "n_end must be at least 2" in result.error_message


def test_validate_dimensions_range_inverted():
    """Test validation rejects n_start > n_end."""
    result = validate_dimensions(n_start=5, n_end=3)
    assert not result.is_valid
    assert "n_start must be ≤ n_end" in result.error_message


def test_parse_input_single_valid():
    """Test parsing valid single dimension format."""
    result = parse_input("<2,3>")
    assert isinstance(result, DimensionSpec)
    assert result.type == DimensionType.SINGLE
    assert result.r == 2
    assert result.n == 3


def test_parse_input_single_with_spaces():
    """Test parsing single dimension format with spaces."""
    result = parse_input("< 2 , 3 >")
    assert isinstance(result, DimensionSpec)
    assert result.type == DimensionType.SINGLE
    assert result.r == 2
    assert result.n == 3


def test_parse_input_single_invalid_dimensions():
    """Test parsing single dimension with invalid values."""
    result = parse_input("<5,3>")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "r must satisfy 2 ≤ r ≤ n" in result.error_message


def test_parse_input_all_for_n_valid():
    """Test parsing valid all_for_n format."""
    result = parse_input("5")
    assert isinstance(result, DimensionSpec)
    assert result.type == DimensionType.ALL_FOR_N
    assert result.n == 5


def test_parse_input_all_for_n_invalid():
    """Test parsing all_for_n with invalid n."""
    result = parse_input("1")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "n must be at least 2" in result.error_message


def test_parse_input_range_valid():
    """Test parsing valid range format."""
    result = parse_input("3..6")
    assert isinstance(result, DimensionSpec)
    assert result.type == DimensionType.RANGE
    assert result.n_start == 3
    assert result.n_end == 6


def test_parse_input_range_with_spaces():
    """Test parsing range format with spaces."""
    result = parse_input(" 3 .. 6 ")
    assert isinstance(result, DimensionSpec)
    assert result.type == DimensionType.RANGE
    assert result.n_start == 3
    assert result.n_end == 6


def test_parse_input_range_invalid():
    """Test parsing range with invalid values."""
    result = parse_input("5..3")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "n_start must be ≤ n_end" in result.error_message


def test_parse_input_malformed_single():
    """Test parsing malformed single dimension format."""
    result = parse_input("<2,3,4>")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "expected '<r,n>' with exactly two values" in result.error_message


def test_parse_input_malformed_range():
    """Test parsing malformed range format."""
    result = parse_input("2..3..4")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "expected 'n1..n2' with exactly two values" in result.error_message


def test_parse_input_non_integer():
    """Test parsing non-integer input."""
    result = parse_input("abc")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "could not parse as integer" in result.error_message


def test_dimension_spec_validation_errors():
    """Test DimensionSpec __post_init__ validation."""
    # SINGLE type without r should raise ValueError
    with pytest.raises(ValueError, match="SINGLE type requires both r and n"):
        DimensionSpec(type=DimensionType.SINGLE, n=3)
    
    # SINGLE type without n should raise ValueError
    with pytest.raises(ValueError, match="SINGLE type requires both r and n"):
        DimensionSpec(type=DimensionType.SINGLE, r=2)
    
    # ALL_FOR_N type without n should raise ValueError
    with pytest.raises(ValueError, match="ALL_FOR_N type requires n"):
        DimensionSpec(type=DimensionType.ALL_FOR_N)
    
    # RANGE type without n_start should raise ValueError
    with pytest.raises(ValueError, match="RANGE type requires both n_start and n_end"):
        DimensionSpec(type=DimensionType.RANGE, n_end=5)
    
    # RANGE type without n_end should raise ValueError
    with pytest.raises(ValueError, match="RANGE type requires both n_start and n_end"):
        DimensionSpec(type=DimensionType.RANGE, n_start=3)


def test_validate_dimensions_no_parameters():
    """Test validation with no parameters provided."""
    result = validate_dimensions()
    assert not result.is_valid
    assert "must specify either (r, n), n, or (n_start, n_end)" in result.error_message


def test_parse_input_invalid_integers_in_single():
    """Test parsing with invalid integers in single format."""
    result = parse_input("<2.5,3>")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "could not parse integers in '<r,n>'" in result.error_message


def test_parse_input_invalid_integers_in_range():
    """Test parsing with invalid integers in range format."""
    result = parse_input("2.5..3")
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "could not parse integers in 'n1..n2'" in result.error_message
