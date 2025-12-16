"""
Latin Rectangle data structure and utilities.

This module provides the LatinRectangle class for representing and
validating normalized Latin rectangles.
"""

from typing import List, Iterator, Set
from core.permutation import permutation_sign, generate_constrained_permutations
from core.bitset_constraints import BitsetConstraints, generate_constrained_permutations_bitset, generate_constrained_permutations_bitset_optimized


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



def generate_normalized_rectangles_resumable(r: int, n: int, 
                                           start_from: List[List[int]] = None) -> Iterator[LatinRectangle]:
    """
    Generate all normalized Latin rectangles of dimension r×n with resume capability.
    
    A normalized Latin rectangle has:
    - First row as the identity permutation [1, 2, 3, ..., n]
    - Each subsequent row is a valid permutation with no column conflicts
    
    This function uses backtracking to recursively build valid rectangles,
    tracking column constraints to ensure no duplicates in any column.
    
    Args:
        r: Number of rows (2 ≤ r ≤ n)
        n: Number of columns (n ≥ 2)
        start_from: Partial rectangle to resume from (None = start fresh)
        
    Yields:
        LatinRectangle objects representing all valid normalized rectangles
        
    Examples:
        >>> # Generate all 2×2 normalized Latin rectangles
        >>> rects = list(generate_normalized_rectangles_resumable(2, 2))
        >>> len(rects)
        1
        >>> rects[0].data
        [[1, 2], [2, 1]]
        
        >>> # Resume from partial rectangle
        >>> partial = [[1, 2, 3], [2, 3, 1]]
        >>> rects = list(generate_normalized_rectangles_resumable(3, 3, partial))
        >>> # Will generate rectangles starting from the partial state
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
    
    # Start from checkpoint or fresh
    if start_from is None:
        # Start with identity first row
        start_rows = [list(range(1, n + 1))]
    else:
        # Resume from checkpoint
        start_rows = [row.copy() for row in start_from]
    
    yield from backtrack(start_rows)


def generate_normalized_rectangles(r: int, n: int) -> Iterator[LatinRectangle]:
    """
    Generate all normalized Latin rectangles of dimension r×n.
    
    A normalized Latin rectangle has:
    - First row as the identity permutation [1, 2, 3, ..., n]
    - Each subsequent row is a valid permutation with no column conflicts
    
    This function uses bitset-optimized counter-based iteration for 2-2.5x speedup
    while maintaining deterministic ordering and precise resumption capability.
    
    Args:
        r: Number of rows (2 ≤ r ≤ n)
        n: Number of columns (n ≥ 2)
        
    Yields:
        LatinRectangle objects in deterministic lexicographic order
        
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
    # Use the bitset-optimized implementation for best performance
    yield from generate_normalized_rectangles_bitset_optimized(r, n)


def generate_normalized_rectangles_bitset_optimized(r: int, n: int, start_counters: List[int] = None) -> Iterator[LatinRectangle]:
    """
    Generate all normalized Latin rectangles using bitset-optimized constraints.
    
    This implementation uses bitset operations for 2-2.5x faster constraint checking
    compared to the standard counter-based approach.
    
    Args:
        r: Number of rows (2 ≤ r ≤ n)
        n: Number of columns (n ≥ 2)
        start_counters: List of counters for each row level (None = start from beginning)
        
    Yields:
        LatinRectangle objects in deterministic lexicographic order
        
    Examples:
        >>> # Generate all rectangles from beginning
        >>> rects = list(generate_normalized_rectangles_bitset_optimized(2, 3))
        >>> len(rects)
        2
        
        >>> # Resume from specific position
        >>> rects = list(generate_normalized_rectangles_bitset_optimized(2, 3, [0, 1]))
        >>> # Starts from second permutation of row 2
    """
    
    if start_counters is None:
        start_counters = [0] * r
    
    # Ensure we have enough counters
    counters = start_counters + [0] * (r - len(start_counters))
    
    # Cache for permutations to avoid recomputation (only for larger problems)
    use_cache = (r * n) >= 20  # Only cache for larger problems to avoid overhead
    permutation_cache = {} if use_cache else None
    
    def get_cache_key(constraints: BitsetConstraints) -> tuple:
        """Create a hashable cache key from bitset constraints."""
        return tuple(constraints.forbidden)
    
    def get_valid_permutations_cached(constraints: BitsetConstraints) -> List[List[int]]:
        """Get all valid permutations for given constraints, with optional caching."""
        if not use_cache:
            # For small problems, don't use cache to avoid overhead
            # Use optimized generator that produces lexicographic order directly
            return list(generate_constrained_permutations_bitset_optimized(n, constraints))
        
        cache_key = get_cache_key(constraints)
        
        if cache_key not in permutation_cache:
            # Generate permutations in lexicographic order directly (no sorting needed)
            valid_perms = list(generate_constrained_permutations_bitset_optimized(n, constraints))
            permutation_cache[cache_key] = valid_perms  # Already in lexicographic order
        
        return permutation_cache[cache_key]
    
    def generate_from_counters(partial_rows: List[List[int]], level: int, 
                             constraints: BitsetConstraints, current_counters: List[int]) -> Iterator[LatinRectangle]:
        """Generate rectangles starting from specified counter positions."""
        
        if level == r:
            # Base case: complete rectangle
            yield LatinRectangle(r, n, [row[:] for row in partial_rows])  # Faster list copy
            return
        
        # Get valid permutations for this level (cached with bitset constraints)
        valid_perms = get_valid_permutations_cached(constraints)
        
        if not valid_perms:
            # No valid permutations possible - dead end
            return
        
        # Start from the specified counter for this level
        start_idx = current_counters[level] if level < len(current_counters) else 0
        
        # Ensure start_idx is valid
        if start_idx >= len(valid_perms):
            return  # Counter is beyond available permutations
        
        for i, perm in enumerate(valid_perms[start_idx:], start_idx):
            # Add this row to partial rectangle
            partial_rows.append(perm)
            
            # Update bitset constraints by adding values from this row
            for col_idx, value in enumerate(perm):
                constraints.add_forbidden(col_idx, value)
            
            # Prepare counters for next level
            if i == start_idx:
                # First iteration - use existing deeper counters
                next_counters = current_counters
            else:
                # Subsequent iterations - reset deeper counters
                next_counters = current_counters[:level+1] + [0] * (r - level - 1)
                next_counters[level] = i
            
            yield from generate_from_counters(partial_rows, level + 1, constraints, next_counters)
            
            # Backtrack: remove this row and its constraints
            partial_rows.pop()
            for col_idx, value in enumerate(perm):
                constraints.remove_forbidden(col_idx, value)
    
    # Start with identity first row and initial bitset constraints
    first_row = list(range(1, n + 1))
    initial_constraints = BitsetConstraints(n)
    for col_idx, value in enumerate(first_row):
        initial_constraints.add_forbidden(col_idx, value)
    
    yield from generate_from_counters([first_row], 1, initial_constraints, counters)


def generate_normalized_rectangles_counter_based(r: int, n: int, start_counters: List[int] = None) -> Iterator[LatinRectangle]:
    """
    Generate all normalized Latin rectangles using optimized counter-based iteration.
    
    This implementation uses explicit counters for each row level, providing
    deterministic ordering and enabling precise resumption for checkpointing.
    
    Optimizations:
    - Cached permutation generation to avoid recomputation
    - Incremental constraint building
    - Reduced list copying
    
    Args:
        r: Number of rows (2 ≤ r ≤ n)
        n: Number of columns (n ≥ 2)
        start_counters: List of counters for each row level (None = start from beginning)
        
    Yields:
        LatinRectangle objects in deterministic lexicographic order
        
    Examples:
        >>> # Generate all rectangles from beginning
        >>> rects = list(generate_normalized_rectangles_counter_based(2, 3))
        >>> len(rects)
        2
        
        >>> # Resume from specific position
        >>> rects = list(generate_normalized_rectangles_counter_based(2, 3, [0, 1]))
        >>> # Starts from second permutation of row 2
    """
    
    if start_counters is None:
        start_counters = [0] * r
    
    # Ensure we have enough counters
    counters = start_counters + [0] * (r - len(start_counters))
    
    # Cache for permutations to avoid recomputation (only for larger problems)
    use_cache = (r * n) >= 20  # Only cache for larger problems to avoid overhead
    permutation_cache = {} if use_cache else None
    
    def get_cache_key(forbidden_sets: List[Set[int]]) -> tuple:
        """Create a hashable cache key from forbidden sets."""
        return tuple(frozenset(s) for s in forbidden_sets)
    
    def get_valid_permutations_cached(forbidden: List[Set[int]]) -> List[List[int]]:
        """Get all valid permutations for given constraints, with optional caching."""
        if not use_cache:
            # For small problems, don't use cache to avoid overhead
            valid_perms = list(generate_constrained_permutations(n, forbidden))
            return sorted(valid_perms)
        
        cache_key = get_cache_key(forbidden)
        
        if cache_key not in permutation_cache:
            # Generate and sort all valid permutations
            valid_perms = list(generate_constrained_permutations(n, forbidden))
            permutation_cache[cache_key] = sorted(valid_perms)  # Lexicographic order for determinism
        
        return permutation_cache[cache_key]
    
    def generate_from_counters(partial_rows: List[List[int]], level: int, 
                             forbidden: List[Set[int]], current_counters: List[int]) -> Iterator[LatinRectangle]:
        """Generate rectangles starting from specified counter positions."""
        
        if level == r:
            # Base case: complete rectangle
            yield LatinRectangle(r, n, [row[:] for row in partial_rows])  # Faster list copy
            return
        
        # Get valid permutations for this level (cached)
        valid_perms = get_valid_permutations_cached(forbidden)
        
        if not valid_perms:
            # No valid permutations possible - dead end
            return
        
        # Start from the specified counter for this level
        start_idx = current_counters[level] if level < len(current_counters) else 0
        
        # Ensure start_idx is valid
        if start_idx >= len(valid_perms):
            return  # Counter is beyond available permutations
        
        for i, perm in enumerate(valid_perms[start_idx:], start_idx):
            # Add this row to partial rectangle
            partial_rows.append(perm)
            
            # Update forbidden sets by adding values from this row
            for col_idx, value in enumerate(perm):
                forbidden[col_idx].add(value)
            
            # Prepare counters for next level
            if i == start_idx:
                # First iteration - use existing deeper counters
                next_counters = current_counters
            else:
                # Subsequent iterations - reset deeper counters
                next_counters = current_counters[:level+1] + [0] * (r - level - 1)
                next_counters[level] = i
            
            yield from generate_from_counters(partial_rows, level + 1, forbidden, next_counters)
            
            # Backtrack: remove this row and its constraints
            partial_rows.pop()
            for col_idx, value in enumerate(perm):
                forbidden[col_idx].remove(value)
    
    # Start with identity first row and initial forbidden sets
    first_row = list(range(1, n + 1))
    initial_forbidden = [set() for _ in range(n)]
    for col_idx, value in enumerate(first_row):
        initial_forbidden[col_idx].add(value)
    
    yield from generate_from_counters([first_row], 1, initial_forbidden, counters)


class CounterBasedRectangleIterator:
    """
    Iterator class for generating rectangles with explicit counter state.
    
    This class maintains internal counters that can be saved/restored for
    precise checkpointing and resumption.
    
    Note: This iterator is optimized for checkpointing, not raw performance.
    For best performance, use generate_normalized_rectangles_counter_based().
    """
    
    def __init__(self, r: int, n: int, start_counters: List[int] = None):
        self.r = r
        self.n = n
        self.counters = start_counters[:] if start_counters else [0] * r
        self.finished = False
        self.rectangles_generated = 0
        
        # Ensure we have enough counters
        while len(self.counters) < r:
            self.counters.append(0)
        
        # Cache for performance optimization
        self._permutation_cache = {}  # Cache valid permutations by partial state
    
    def get_state(self) -> dict:
        """Get current iterator state for checkpointing."""
        return {
            'counters': self.counters.copy(),
            'rectangles_generated': self.rectangles_generated,
            'finished': self.finished
        }
    
    def set_state(self, state: dict):
        """Restore iterator state from checkpoint."""
        self.counters = state['counters'].copy()
        self.rectangles_generated = state['rectangles_generated']
        self.finished = state['finished']
    
    def __iter__(self):
        return self
    
    def __next__(self) -> LatinRectangle:
        """Generate next rectangle and advance counters."""
        if self.finished:
            raise StopIteration
        
        # Build rectangle from current counter state
        try:
            rectangle = self._build_rectangle_from_counters()
            self.rectangles_generated += 1
            self._advance_counters()
            return rectangle
        except (IndexError, ValueError):
            # No more valid rectangles
            self.finished = True
            raise StopIteration
    
    def _build_rectangle_from_counters(self) -> LatinRectangle:
        """Build a rectangle based on current counter values using bitset optimization."""
        rows = [list(range(1, self.n + 1))]  # Start with identity first row
        
        for level in range(1, self.r):
            # Build bitset constraints for this level
            constraints = BitsetConstraints(self.n)
            for row in rows:
                for col_idx, value in enumerate(row):
                    constraints.add_forbidden(col_idx, value)
            
            valid_perms = list(generate_constrained_permutations_bitset_optimized(self.n, constraints))
            
            if not valid_perms:
                raise ValueError(f"No valid permutations at level {level}")
            
            counter_val = self.counters[level]
            if counter_val >= len(valid_perms):
                raise IndexError(f"Counter {counter_val} exceeds available permutations {len(valid_perms)} at level {level}")
            
            rows.append(valid_perms[counter_val])
        
        return LatinRectangle(self.r, self.n, rows)
    
    def _advance_counters(self):
        """Advance counters to next rectangle position."""
        # Start from the last level and increment with carry
        level = self.r - 1
        
        while level >= 1:  # Don't modify level 0 (identity row)
            self.counters[level] += 1
            
            # Check if we need to carry to previous level
            if self._is_counter_valid(level):
                # Counter is valid, we're done
                # Reset all deeper level counters to 0
                for deeper_level in range(level + 1, self.r):
                    self.counters[deeper_level] = 0
                return
            else:
                # Counter exceeded limit, carry to previous level
                self.counters[level] = 0
                level -= 1
        
        # If we get here, we've exhausted all possibilities
        self.finished = True
    
    def _is_counter_valid(self, level: int) -> bool:
        """Check if counter at given level is valid for current state using bitset optimization."""
        try:
            # Build partial rectangle up to this level
            rows = [list(range(1, self.n + 1))]  # Identity first row
            
            for l in range(1, level):
                constraints = BitsetConstraints(self.n)
                for row in rows:
                    for col_idx, value in enumerate(row):
                        constraints.add_forbidden(col_idx, value)
                
                valid_perms = list(generate_constrained_permutations_bitset_optimized(self.n, constraints))
                if self.counters[l] >= len(valid_perms):
                    return False
                rows.append(valid_perms[self.counters[l]])
            
            # Check if current level counter is valid
            constraints = BitsetConstraints(self.n)
            for row in rows:
                for col_idx, value in enumerate(row):
                    constraints.add_forbidden(col_idx, value)
            
            valid_perms = list(generate_constrained_permutations_bitset_optimized(self.n, constraints))
            return self.counters[level] < len(valid_perms)
            
        except (IndexError, ValueError):
            return False