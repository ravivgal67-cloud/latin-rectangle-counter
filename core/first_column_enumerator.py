#!/usr/bin/env python3
"""
First Column Enumerator for Latin Rectangle Optimization.

This module implements the first column enumeration strategy for optimizing
Latin rectangle computation by exploiting (r-1)! symmetry.
"""

from itertools import combinations, permutations
from typing import List, Iterator
import math


class FirstColumnEnumerator:
    """
    Enumerates canonical first column configurations for Latin rectangles.
    
    For normalized Latin rectangles with r rows and n columns, the first row
    is fixed as [1, 2, 3, ..., n]. The first column can be chosen as 
    [1, a, b, c, ...] where a,b,c are distinct values from {2,3,...,n}.
    
    Each canonical first column choice represents (r-1)! equivalent rectangles
    due to row interchange symmetry (rows 2 through r can be permuted).
    """
    
    def __init__(self):
        """Initialize the first column enumerator."""
        pass
    
    def enumerate_first_columns(self, r: int, n: int) -> List[List[int]]:
        """
        Generate canonical first column configurations.
        
        Args:
            r: Number of rows (must be >= 2)
            n: Number of columns (must be > r)
            
        Returns:
            List of canonical first column configurations, each as [1, a, b, c, ...]
            where a < b < c are chosen from {2,3,...,n} in sorted order
            
        Raises:
            ValueError: If r < 2 or n <= r
        """
        self._validate_dimensions(r, n)
        
        # First element is always 1 (normalized form)
        # Choose (r-1) values from {2, 3, ..., n} in sorted order (canonical form)
        available_values = list(range(2, n + 1))
        
        first_columns = []
        
        # Generate all combinations of length (r-1) from available values
        for combination in combinations(available_values, r - 1):
            # Create canonical first column: [1] + sorted chosen values
            first_column = [1] + list(combination)
            first_columns.append(first_column)
        
        return first_columns
    
    def enumerate_first_columns_iterator(self, r: int, n: int) -> Iterator[List[int]]:
        """
        Generate canonical first column configurations as an iterator for memory efficiency.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Yields:
            Canonical first column configurations one at a time
        """
        self._validate_dimensions(r, n)
        
        available_values = list(range(2, n + 1))
        
        for combination in combinations(available_values, r - 1):
            first_column = [1] + list(combination)
            yield first_column
    
    def count_first_columns(self, r: int, n: int) -> int:
        """
        Count total number of canonical first column configurations.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            C(n-1, r-1) - the number of ways to choose (r-1) values from {2,...,n}
        """
        self._validate_dimensions(r, n)
        
        # C(n-1, r-1) = (n-1)! / ((r-1)! * (n-r)!)
        return math.comb(n - 1, r - 1)
    
    def get_symmetry_factor(self, r: int) -> int:
        """
        Get the symmetry factor for a given number of rows.
        
        Each canonical first column represents (r-1)! equivalent rectangles
        due to row interchange symmetry (rows 2 through r can be permuted).
        
        Args:
            r: Number of rows
            
        Returns:
            (r-1)! - the number of equivalent rectangles per canonical first column
        """
        if r < 2:
            raise ValueError(f"Symmetry factor requires r >= 2, got r={r}")
        
        return math.factorial(r - 1)
    
    def validate_first_column(self, first_column: List[int], r: int, n: int) -> bool:
        """
        Validate that a first column configuration is valid.
        
        Args:
            first_column: The first column to validate
            r: Number of rows
            n: Number of columns
            
        Returns:
            True if valid, False otherwise
        """
        # Check length
        if len(first_column) != r:
            return False
        
        # Check first element is 1
        if first_column[0] != 1:
            return False
        
        # Check all values are in valid range
        if not all(1 <= val <= n for val in first_column):
            return False
        
        # Check no duplicates
        if len(set(first_column)) != len(first_column):
            return False
        
        # Check remaining values are from {2, ..., n}
        remaining_values = first_column[1:]
        if not all(2 <= val <= n for val in remaining_values):
            return False
        
        return True
    
    def _validate_dimensions(self, r: int, n: int) -> None:
        """
        Validate that dimensions are suitable for first column enumeration.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Raises:
            ValueError: If dimensions are invalid
        """
        if r < 2:
            raise ValueError(f"First column enumeration requires r >= 2, got r={r}")
        
        if n < r:
            raise ValueError(f"Invalid dimensions: n must be >= r, got n={n}, r={r}")
        
        if n - 1 < r - 1:
            raise ValueError(f"Not enough values to choose from: need {r-1} from {n-1} values")


def main():
    """
    Demonstration of first column enumeration.
    """
    enumerator = FirstColumnEnumerator()
    
    # Test cases
    test_cases = [(3, 4), (3, 5), (4, 5), (5, 8)]
    
    for r, n in test_cases:
        print(f"\n=== First Column Enumeration for ({r},{n}) ===")
        
        # Count configurations
        count = enumerator.count_first_columns(r, n)
        symmetry_factor = enumerator.get_symmetry_factor(r)
        
        print(f"Total first column choices: {count}")
        print(f"Symmetry factor (r-1)!: {symmetry_factor}")
        print(f"Total work units: {count} (vs {symmetry_factor * count} rectangles)")
        
        # Show first few configurations
        columns = enumerator.enumerate_first_columns(r, n)
        print(f"\nFirst column configurations:")
        for i, col in enumerate(columns[:min(10, len(columns))]):
            print(f"  {i+1:2d}: {col}")
        
        if len(columns) > 10:
            print(f"  ... and {len(columns) - 10} more")


if __name__ == "__main__":
    main()