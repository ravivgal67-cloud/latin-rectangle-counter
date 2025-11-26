"""
Latin Rectangle data structure and utilities.

This module provides the LatinRectangle class for representing and
validating normalized Latin rectangles.
"""

from typing import List, Iterator, Set
from core.permutation import permutation_sign, generate_constrained_permutations


class LatinRectangle:
    """
    Represents a Latin rectangle with dimensions r×n.
    
    A Latin rectangle is an r×n array filled with n distinct symbols
    where each symbol occurs at most once in each row and at most once
    in each column.
    
    A normalized Latin rectangle has the first row as the identity
    permutation [1, 2, 3, ..., n].
    
    Attributes:
        rows: Number of rows (r)
        cols: Number of columns (n)
        data: 2D array representing the rectangle (r×n)
    """
    
    def __init__(self, rows: int, cols: int, data: List[List[int]]):
        """
        Initialize a Latin rectangle.
        
        Args:
            rows: Number of rows (r)
            cols: Number of columns (n)
            data: 2D array of integers representing the rectangle
        """
        self.rows = rows
        self.cols = cols
        self.data = data
    
    def is_valid(self) -> bool:
        """
        Check if this is a valid Latin rectangle.
        
        A valid Latin rectangle must satisfy:
        1. Each row is a permutation of [1, 2, ..., n]
        2. No column contains duplicate values
        
        Returns:
            True if the rectangle is valid, False otherwise
        """
        # Check dimensions match
        if len(self.data) != self.rows:
            return False
        
        for row in self.data:
            if len(row) != self.cols:
                return False
        
        # Check each row is a permutation of [1, 2, ..., n]
        expected_set = set(range(1, self.cols + 1))
        for row in self.data:
            if set(row) != expected_set:
                return False
        
        # Check no column has duplicates
        for col_idx in range(self.cols):
            column_values = [self.data[row_idx][col_idx] for row_idx in range(self.rows)]
            if len(column_values) != len(set(column_values)):
                return False
        
        return True
    
    def is_normalized(self) -> bool:
        """
        Check if this is a normalized Latin rectangle.
        
        A normalized Latin rectangle has the first row as the identity
        permutation [1, 2, 3, ..., n].
        
        Returns:
            True if the rectangle is normalized, False otherwise
        """
        if self.rows == 0 or self.cols == 0:
            return False
        
        # Check if first row is identity permutation
        expected_first_row = list(range(1, self.cols + 1))
        return self.data[0] == expected_first_row
    
    def compute_sign(self) -> int:
        """
        Compute the sign of this Latin rectangle.
        
        The sign is defined as the product of the signs of all row
        permutations. Each row permutation's sign is +1 if it has an
        even number of inversions, -1 if odd.
        
        Returns:
            +1 if the rectangle has even parity (positive)
            -1 if the rectangle has odd parity (negative)
        """
        sign = 1
        for row in self.data:
            sign *= permutation_sign(row)
        return sign
    
    def __repr__(self) -> str:
        """String representation of the Latin rectangle."""
        return f"LatinRectangle({self.rows}×{self.cols}, data={self.data})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another Latin rectangle."""
        if not isinstance(other, LatinRectangle):
            return False
        return (self.rows == other.rows and 
                self.cols == other.cols and 
                self.data == other.data)



def generate_normalized_rectangles(r: int, n: int) -> Iterator[LatinRectangle]:
    """
    Generate all normalized Latin rectangles of dimension r×n.
    
    A normalized Latin rectangle has:
    - First row as the identity permutation [1, 2, 3, ..., n]
    - Each subsequent row is a valid permutation with no column conflicts
    
    This function uses backtracking to recursively build valid rectangles,
    tracking column constraints to ensure no duplicates in any column.
    
    Args:
        r: Number of rows (2 ≤ r ≤ n)
        n: Number of columns (n ≥ 2)
        
    Yields:
        LatinRectangle objects representing all valid normalized rectangles
        
    Examples:
        >>> # Generate all 2×2 normalized Latin rectangles
        >>> rects = list(generate_normalized_rectangles(2, 2))
        >>> len(rects)
        1
        >>> rects[0].data
        [[1, 2], [2, 1]]
        
        >>> # Generate all 2×3 normalized Latin rectangles
        >>> rects = list(generate_normalized_rectangles(2, 3))
        >>> len(rects)
        2
    """
    def backtrack(rows: List[List[int]]) -> Iterator[LatinRectangle]:
        """
        Recursively build normalized Latin rectangles.
        
        Args:
            rows: Current list of rows built so far
            
        Yields:
            Complete LatinRectangle objects when r rows are built
        """
        # Base case: we've built all r rows
        if len(rows) == r:
            yield LatinRectangle(r, n, [row.copy() for row in rows])
            return
        
        # Build forbidden set for each position based on existing rows
        forbidden = [set() for _ in range(n)]
        for row in rows:
            for col_idx, value in enumerate(row):
                forbidden[col_idx].add(value)
        
        # Generate all valid next rows using constrained permutation generator
        for next_row in generate_constrained_permutations(n, forbidden):
            rows.append(next_row)
            yield from backtrack(rows)
            rows.pop()
    
    # Start with identity first row
    first_row = list(range(1, n + 1))
    yield from backtrack([first_row])
