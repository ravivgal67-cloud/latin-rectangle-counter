"""
Bitset-based constraint management for Latin rectangle generation.

This module provides optimized constraint operations using bitsets
for faster forbidden value tracking and availability checking.
"""

from typing import List, Set, Iterator


class BitsetConstraints:
    """
    Fast constraint management using bitsets.
    
    Each position's forbidden values are stored as bits in an integer,
    enabling O(1) constraint operations instead of O(k) set operations.
    
    Attributes:
        n: Number of columns (values 1 to n)
        forbidden: List of integers representing forbidden bitsets
    """
    
    def __init__(self, n: int):
        """
        Initialize bitset constraints.
        
        Args:
            n: Number of columns (values 1 to n)
        """
        self.n = n
        self.forbidden = [0] * n  # Each int represents a bitset
    
    def add_forbidden(self, pos: int, value: int):
        """
        Add a forbidden value at position.
        
        Args:
            pos: Column position (0-indexed)
            value: Value to forbid (1-indexed)
        """
        self.forbidden[pos] |= (1 << (value - 1))
    
    def remove_forbidden(self, pos: int, value: int):
        """
        Remove a forbidden value at position.
        
        Args:
            pos: Column position (0-indexed)
            value: Value to remove from forbidden set (1-indexed)
        """
        self.forbidden[pos] &= ~(1 << (value - 1))
    
    def is_forbidden(self, pos: int, value: int) -> bool:
        """
        Check if value is forbidden at position.
        
        Args:
            pos: Column position (0-indexed)
            value: Value to check (1-indexed)
            
        Returns:
            True if value is forbidden at position
        """
        return bool(self.forbidden[pos] & (1 << (value - 1)))
    
    def available_count(self, pos: int) -> int:
        """
        Count available values at position.
        
        Args:
            pos: Column position (0-indexed)
            
        Returns:
            Number of available (non-forbidden) values
        """
        return self.n - bin(self.forbidden[pos]).count('1')
    
    def get_available_values(self, pos: int) -> List[int]:
        """
        Get list of available values at position.
        
        Args:
            pos: Column position (0-indexed)
            
        Returns:
            List of available values (1-indexed)
        """
        available = []
        forbidden_bits = self.forbidden[pos]
        
        for value in range(1, self.n + 1):
            if not (forbidden_bits & (1 << (value - 1))):
                available.append(value)
        
        return available
    
    def copy(self) -> 'BitsetConstraints':
        """
        Create a copy of the constraints.
        
        Returns:
            New BitsetConstraints instance with same state
        """
        new_constraints = BitsetConstraints(self.n)
        new_constraints.forbidden = self.forbidden[:]
        return new_constraints
    
    def to_set_list(self) -> List[Set[int]]:
        """
        Convert to list of sets format for compatibility.
        
        Returns:
            List of sets representing forbidden values at each position
        """
        result = []
        for pos in range(self.n):
            forbidden_set = set()
            forbidden_bits = self.forbidden[pos]
            
            for value in range(1, self.n + 1):
                if forbidden_bits & (1 << (value - 1)):
                    forbidden_set.add(value)
            
            result.append(forbidden_set)
        
        return result
    
    @classmethod
    def from_set_list(cls, forbidden_sets: List[Set[int]]) -> 'BitsetConstraints':
        """
        Create BitsetConstraints from list of forbidden sets.
        
        Args:
            forbidden_sets: List of sets containing forbidden values
            
        Returns:
            New BitsetConstraints instance
        """
        n = len(forbidden_sets)
        constraints = cls(n)
        
        for pos, forbidden_set in enumerate(forbidden_sets):
            for value in forbidden_set:
                constraints.add_forbidden(pos, value)
        
        return constraints
    
    def __repr__(self) -> str:
        """String representation showing forbidden values."""
        forbidden_lists = []
        for pos in range(self.n):
            forbidden_values = []
            forbidden_bits = self.forbidden[pos]
            
            for value in range(1, self.n + 1):
                if forbidden_bits & (1 << (value - 1)):
                    forbidden_values.append(value)
            
            forbidden_lists.append(forbidden_values)
        
        return f"BitsetConstraints(n={self.n}, forbidden={forbidden_lists})"


def generate_constrained_permutations_bitset(n: int, constraints: BitsetConstraints) -> Iterator[List[int]]:
    """
    Generate all permutations satisfying bitset constraints.
    
    This is an optimized version of generate_constrained_permutations
    that uses bitset operations for faster constraint checking.
    
    Args:
        n: Length of permutations
        constraints: BitsetConstraints object
        
    Yields:
        Valid permutations as lists of integers
        
    Examples:
        >>> constraints = BitsetConstraints(3)
        >>> constraints.add_forbidden(0, 2)  # Position 0 cannot be 2
        >>> constraints.add_forbidden(1, 1)  # Position 1 cannot be 1
        >>> perms = list(generate_constrained_permutations_bitset(3, constraints))
        >>> len(perms)
        2
    """
    
    def backtrack(partial_perm: List[int], used_values: int, pos: int) -> Iterator[List[int]]:
        """
        Backtrack to build valid permutations.
        
        Args:
            partial_perm: Current partial permutation
            used_values: Bitset of already used values
            pos: Current position to fill
        """
        if pos == n:
            yield partial_perm[:]
            return
        
        # Get available values at this position
        forbidden_bits = constraints.forbidden[pos]
        
        for value in range(1, n + 1):
            value_bit = 1 << (value - 1)
            
            # Check if value is available (not forbidden and not used)
            if not (forbidden_bits & value_bit) and not (used_values & value_bit):
                partial_perm.append(value)
                yield from backtrack(partial_perm, used_values | value_bit, pos + 1)
                partial_perm.pop()
    
    yield from backtrack([], 0, 0)


def optimize_constraint_order(constraints: BitsetConstraints) -> List[int]:
    """
    Determine optimal constraint ordering using most-constrained-first heuristic.
    
    Args:
        constraints: BitsetConstraints object
        
    Returns:
        List of position indices ordered by constraint tightness (most constrained first)
        
    Examples:
        >>> constraints = BitsetConstraints(4)
        >>> constraints.add_forbidden(0, 1)
        >>> constraints.add_forbidden(0, 2)  # Position 0: 2 forbidden
        >>> constraints.add_forbidden(2, 3)  # Position 2: 1 forbidden
        >>> order = optimize_constraint_order(constraints)
        >>> order[0]  # Most constrained position should be first
        0
    """
    # Calculate constraint scores (number of forbidden values)
    constraint_scores = []
    for pos in range(constraints.n):
        forbidden_count = bin(constraints.forbidden[pos]).count('1')
        available_count = constraints.n - forbidden_count
        constraint_scores.append((available_count, pos))
    
    # Sort by available count (ascending = most constrained first)
    constraint_scores.sort()
    
    return [pos for _, pos in constraint_scores]