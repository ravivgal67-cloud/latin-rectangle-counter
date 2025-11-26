"""
Input validation module for Latin Rectangle Counter.

This module provides data structures and functions for validating
and parsing user input for dimension specifications.
"""

from dataclasses import dataclass
from typing import Optional, Union
from enum import Enum


class DimensionType(Enum):
    """Type of dimension specification."""
    SINGLE = "single"      # Single (r, n) pair
    ALL_FOR_N = "all_for_n"  # All r from 2 to n for a given n
    RANGE = "range"        # Range of n values (n1..n2)


@dataclass
class DimensionSpec:
    """
    Specification for dimensions to count.
    
    Supports three types of specifications:
    1. Single: A specific (r, n) pair
    2. All for n: All r from 2 to n for a given n
    3. Range: All n from n1 to n2, and for each n, all r from 2 to n
    
    Attributes:
        type: Type of dimension specification
        r: Optional specific row count (for SINGLE type)
        n: Optional specific column count (for SINGLE and ALL_FOR_N types)
        n_start: Optional range start (for RANGE type)
        n_end: Optional range end (for RANGE type)
    """
    type: DimensionType
    r: Optional[int] = None
    n: Optional[int] = None
    n_start: Optional[int] = None
    n_end: Optional[int] = None
    
    def __post_init__(self):
        """Validate that required fields are present for each type."""
        if self.type == DimensionType.SINGLE:
            if self.r is None or self.n is None:
                raise ValueError("SINGLE type requires both r and n")
        elif self.type == DimensionType.ALL_FOR_N:
            if self.n is None:
                raise ValueError("ALL_FOR_N type requires n")
        elif self.type == DimensionType.RANGE:
            if self.n_start is None or self.n_end is None:
                raise ValueError("RANGE type requires both n_start and n_end")


@dataclass
class ValidationResult:
    """
    Result of input validation.
    
    Attributes:
        is_valid: Whether the input is valid
        error_message: Error message if validation failed (None if valid)
    """
    is_valid: bool
    error_message: Optional[str] = None


def validate_dimensions(r: Optional[int] = None, n: Optional[int] = None, 
                       n_start: Optional[int] = None, n_end: Optional[int] = None) -> ValidationResult:
    """
    Validate dimension specifications.
    
    Validates that dimensions satisfy the constraints:
    - 2 ≤ r ≤ n (when r is specified)
    - n ≥ 2 (when n is specified)
    - n_start ≤ n_end (when range is specified)
    - n_start ≥ 2 and n_end ≥ 2 (when range is specified)
    
    Args:
        r: Optional row count
        n: Optional column count
        n_start: Optional range start
        n_end: Optional range end
        
    Returns:
        ValidationResult indicating whether dimensions are valid and any error message
        
    Examples:
        >>> validate_dimensions(r=2, n=3)
        ValidationResult(is_valid=True, error_message=None)
        
        >>> validate_dimensions(r=5, n=3)
        ValidationResult(is_valid=False, error_message='Invalid dimensions: r must satisfy 2 ≤ r ≤ n')
        
        >>> validate_dimensions(r=1, n=3)
        ValidationResult(is_valid=False, error_message='Invalid dimensions: r must be at least 2')
        
        >>> validate_dimensions(n=1)
        ValidationResult(is_valid=False, error_message='Invalid dimensions: n must be at least 2')
        
        >>> validate_dimensions(n_start=5, n_end=3)
        ValidationResult(is_valid=False, error_message='Invalid range: n_start must be ≤ n_end')
    """
    # Validate single (r, n) pair
    if r is not None and n is not None:
        if r < 2:
            return ValidationResult(False, "Invalid dimensions: r must be at least 2")
        if n < 2:
            return ValidationResult(False, "Invalid dimensions: n must be at least 2")
        if r > n:
            return ValidationResult(False, "Invalid dimensions: r must satisfy 2 ≤ r ≤ n")
        return ValidationResult(True)
    
    # Validate single n (for all_for_n type)
    if n is not None:
        if n < 2:
            return ValidationResult(False, "Invalid dimensions: n must be at least 2")
        return ValidationResult(True)
    
    # Validate range
    if n_start is not None and n_end is not None:
        if n_start < 2:
            return ValidationResult(False, "Invalid range: n_start must be at least 2")
        if n_end < 2:
            return ValidationResult(False, "Invalid range: n_end must be at least 2")
        if n_start > n_end:
            return ValidationResult(False, "Invalid range: n_start must be ≤ n_end")
        return ValidationResult(True)
    
    # If we get here, no valid combination of parameters was provided
    return ValidationResult(False, "Invalid input: must specify either (r, n), n, or (n_start, n_end)")


def parse_input(input_str: str) -> Union[DimensionSpec, ValidationResult]:
    """
    Parse string input into a DimensionSpec.
    
    Supports three input formats:
    1. "<r,n>" - Single dimension pair (e.g., "<2,3>")
    2. "n" - Single n value for all r from 2 to n (e.g., "5")
    3. "n1..n2" - Range of n values (e.g., "3..6")
    
    Args:
        input_str: String input to parse
        
    Returns:
        DimensionSpec if parsing and validation succeed, ValidationResult with error otherwise
        
    Examples:
        >>> parse_input("<2,3>")
        DimensionSpec(type=<DimensionType.SINGLE: 'single'>, r=2, n=3, n_start=None, n_end=None)
        
        >>> parse_input("5")
        DimensionSpec(type=<DimensionType.ALL_FOR_N: 'all_for_n'>, r=None, n=5, n_start=None, n_end=None)
        
        >>> parse_input("3..6")
        DimensionSpec(type=<DimensionType.RANGE: 'range'>, r=None, n=None, n_start=3, n_end=6)
        
        >>> parse_input("<5,3>")
        ValidationResult(is_valid=False, error_message='Invalid dimensions: r must satisfy 2 ≤ r ≤ n')
        
        >>> parse_input("invalid")
        ValidationResult(is_valid=False, error_message='Invalid input format: ...')
    """
    input_str = input_str.strip()
    
    # Try to parse as "<r,n>" format
    if input_str.startswith("<") and input_str.endswith(">"):
        try:
            # Remove angle brackets and split by comma
            content = input_str[1:-1]
            parts = content.split(",")
            
            if len(parts) != 2:
                return ValidationResult(False, "Invalid input format: expected '<r,n>' with exactly two values")
            
            r = int(parts[0].strip())
            n = int(parts[1].strip())
            
            # Validate dimensions
            validation = validate_dimensions(r=r, n=n)
            if not validation.is_valid:
                return validation
            
            return DimensionSpec(type=DimensionType.SINGLE, r=r, n=n)
            
        except ValueError as e:
            return ValidationResult(False, f"Invalid input format: could not parse integers in '<r,n>': {e}")
    
    # Try to parse as "n1..n2" range format
    elif ".." in input_str:
        try:
            parts = input_str.split("..")
            
            if len(parts) != 2:
                return ValidationResult(False, "Invalid input format: expected 'n1..n2' with exactly two values")
            
            n_start = int(parts[0].strip())
            n_end = int(parts[1].strip())
            
            # Validate range
            validation = validate_dimensions(n_start=n_start, n_end=n_end)
            if not validation.is_valid:
                return validation
            
            return DimensionSpec(type=DimensionType.RANGE, n_start=n_start, n_end=n_end)
            
        except ValueError as e:
            return ValidationResult(False, f"Invalid input format: could not parse integers in 'n1..n2': {e}")
    
    # Try to parse as single "n" format
    else:
        try:
            n = int(input_str)
            
            # Validate n
            validation = validate_dimensions(n=n)
            if not validation.is_valid:
                return validation
            
            return DimensionSpec(type=DimensionType.ALL_FOR_N, n=n)
            
        except ValueError as e:
            return ValidationResult(False, f"Invalid input format: could not parse as integer: {e}")
