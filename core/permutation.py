"""
Permutation utilities for Latin Rectangle Counter.

This module provides functions for computing permutation signs,
checking derangements, and computing determinants.
"""

from typing import List, Set, Iterator


def permutation_sign(perm: List[int]) -> int:
    """
    Compute the sign of a permutation based on the number of inversions.
    
    An inversion is a pair of indices (i, j) where i < j but perm[i] > perm[j].
    The sign is +1 if the number of inversions is even, -1 if odd.
    
    Args:
        perm: A permutation represented as a list of integers
        
    Returns:
        +1 if the permutation has even parity (even number of inversions)
        -1 if the permutation has odd parity (odd number of inversions)
        
    Examples:
        >>> permutation_sign([1, 2, 3])
        1
        >>> permutation_sign([2, 1, 3])
        -1
        >>> permutation_sign([3, 2, 1])
        -1
    """
    # Handle edge cases
    if len(perm) <= 1:
        return 1
    
    # Count inversions
    inversions = 0
    for i in range(len(perm)):
        for j in range(i + 1, len(perm)):
            if perm[i] > perm[j]:
                inversions += 1
    
    # Return sign based on parity of inversions
    return 1 if inversions % 2 == 0 else -1



def is_derangement(perm: List[int]) -> bool:
    """
    Check if a permutation is a derangement.
    
    A derangement is a permutation where no element appears in its original position.
    For a permutation of [1, 2, 3, ..., n], element i should not be at position i-1.
    
    Args:
        perm: A permutation represented as a list of integers (1-indexed values)
        
    Returns:
        True if the permutation is a derangement, False otherwise
        
    Examples:
        >>> is_derangement([2, 1, 3])
        False  # 3 is in position 2 (its original position)
        >>> is_derangement([2, 3, 1])
        True   # No element is in its original position
        >>> is_derangement([3, 1, 2])
        True
    """
    for i, value in enumerate(perm):
        # Check if value is in its original position (1-indexed)
        if value == i + 1:
            return False
    return True


def count_derangements(n: int) -> int:
    """
    Count the number of derangements of n elements using the recurrence relation.
    
    The recurrence relation is:
        D(0) = 1
        D(1) = 0
        D(n) = (n-1) * (D(n-1) + D(n-2)) for n >= 2
    
    Args:
        n: The number of elements to derange
        
    Returns:
        The number of derangements of n elements
        
    Examples:
        >>> count_derangements(0)
        1
        >>> count_derangements(1)
        0
        >>> count_derangements(2)
        1
        >>> count_derangements(3)
        2
        >>> count_derangements(4)
        9
    """
    if n == 0:
        return 1
    if n == 1:
        return 0
    
    # Use iterative approach to avoid recursion overhead
    d_prev_prev = 1  # D(0)
    d_prev = 0       # D(1)
    
    for i in range(2, n + 1):
        d_current = (i - 1) * (d_prev + d_prev_prev)
        d_prev_prev = d_prev
        d_prev = d_current
    
    return d_prev



def compute_determinant(matrix: List[List[int]]) -> int:
    """
    Compute the determinant of a square matrix using LU decomposition.
    
    This implementation uses a simple recursive cofactor expansion for clarity,
    which is suitable for the small matrices used in this application.
    
    Args:
        matrix: A square matrix represented as a list of lists
        
    Returns:
        The determinant of the matrix
        
    Examples:
        >>> compute_determinant([[1]])
        1
        >>> compute_determinant([[1, 0], [0, 1]])
        1
        >>> compute_determinant([[0, 1], [1, 0]])
        -1
        >>> compute_determinant([[1, 2], [3, 4]])
        -2
    """
    n = len(matrix)
    
    # Base case: 1x1 matrix
    if n == 1:
        return matrix[0][0]
    
    # Base case: 2x2 matrix
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    
    # Recursive case: cofactor expansion along first row
    det = 0
    for j in range(n):
        # Create minor matrix by removing row 0 and column j
        minor = []
        for i in range(1, n):
            row = []
            for k in range(n):
                if k != j:
                    row.append(matrix[i][k])
            minor.append(row)
        
        # Add cofactor contribution
        cofactor = ((-1) ** j) * matrix[0][j] * compute_determinant(minor)
        det += cofactor
    
    return det



def generate_constrained_permutations(n: int, forbidden: List[Set[int]]) -> Iterator[List[int]]:
    """
    Generate all permutations of [1, 2, ..., n] that avoid forbidden values at each position.
    
    Uses backtracking with early pruning to efficiently generate only valid permutations.
    At position i, the value cannot be in forbidden[i].
    
    Args:
        n: The size of the permutation
        forbidden: List of n sets, where forbidden[i] contains values that cannot
                  appear at position i
                  
    Yields:
        Valid permutations as lists of integers
        
    Examples:
        >>> # Generate permutations where position 0 cannot have value 1
        >>> list(generate_constrained_permutations(2, [{1}, set()]))
        [[2, 1]]
        
        >>> # Generate permutations where position 0 cannot have 1, position 1 cannot have 2
        >>> list(generate_constrained_permutations(3, [{1}, {2}, set()]))
        [[2, 1, 3], [2, 3, 1], [3, 1, 2]]
    """
    def backtrack(position: int, used: Set[int], current: List[int]) -> Iterator[List[int]]:
        """
        Recursive backtracking to build permutations.
        
        Args:
            position: Current position being filled (0-indexed)
            used: Set of values already used in the permutation
            current: Current partial permutation being built
        """
        # Base case: we've filled all positions
        if position == n:
            yield current.copy()
            return
        
        # Try each value from 1 to n
        for value in range(1, n + 1):
            # Skip if value is already used
            if value in used:
                continue
            
            # Skip if value is forbidden at this position
            if value in forbidden[position]:
                continue
            
            # Use this value at this position
            current.append(value)
            used.add(value)
            
            # Recursively fill remaining positions
            yield from backtrack(position + 1, used, current)
            
            # Backtrack
            current.pop()
            used.remove(value)
    
    # Start backtracking from position 0
    yield from backtrack(0, set(), [])
