"""
Smart derangement cache with constraint-aware optimization.

This module provides pre-computed derangements with signs and lexicographic
ordering for efficient constraint-based pruning during rectangle generation.
"""

import json
import time
from typing import List, Tuple, Dict, Set
from pathlib import Path

from core.bitset_constraints import BitsetConstraints, generate_constrained_permutations_bitset_optimized
from core.latin_rectangle import LatinRectangle


class SmartDerangementCache:
    """
    Smart derangement cache with pre-computed signs and database-style constraint indexing.
    
    Features:
    - Pre-computed signs eliminate O(n²) determinant calculations
    - Database-style indexing for O(1) constraint filtering
    - Bitset-based constraint compatibility for maximum performance
    - Persistent disk cache for instant loading
    """
    
    def __init__(self, n: int, cache_dir: str = "cache/smart_derangements"):
        self.n = n
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Core data structures
        self.derangements_with_signs: List[Tuple[List[int], int]] = []
        
        # Database-style indices for ultra-fast constraint filtering
        self.position_value_index: Dict[Tuple[int, int], Set[int]] = {}  # (pos, val) -> set of derangement indices
        self.position_forbidden_index: Dict[Tuple[int, frozenset], Set[int]] = {}  # (pos, forbidden_vals) -> compatible indices
        self.constraint_cache: Dict[str, Set[int]] = {}  # constraint_hash -> compatible indices
        
        # Legacy indices (kept for compatibility)
        self.prefix_index: Dict[int, List[int]] = {}  # first_value -> list of indices
        self.multi_prefix_index: Dict[Tuple[int, ...], List[int]] = {}  # (val1, val2, ...) -> indices
        
        # Load or build cache
        self._load_or_build_cache()
    
    def _get_cache_file_path(self) -> Path:
        """Get the file path for cached smart derangements."""
        return self.cache_dir / f"smart_derangements_n{self.n}.json"
    
    def _load_or_build_cache(self):
        """Load from disk cache or build if not available."""
        cache_file = self._get_cache_file_path()
        
        if cache_file.exists():
            self._load_from_disk(cache_file)
        else:
            self._build_cache()
            self._save_to_disk(cache_file)
    
    def _load_from_disk(self, cache_file: Path):
        """Load smart derangement cache from disk."""
        print(f"📂 Loading smart derangement cache for n={self.n} from {cache_file}")
        start_time = time.time()
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        self.derangements_with_signs = [(perm, sign) for perm, sign in data['derangements_with_signs']]
        self.prefix_index = {int(k): v for k, v in data['prefix_index'].items()}
        
        # Load database indices if available, otherwise rebuild
        if 'position_value_index' in data:
            # Convert string keys back to tuples and sets
            self.position_value_index = {}
            for key_str, indices in data['position_value_index'].items():
                pos, val = map(int, key_str.split(','))
                self.position_value_index[(pos, val)] = set(indices)
        else:
            # Rebuild database indices for older cache files
            self._build_database_indices()
        
        # Rebuild indices that aren't stored (to keep file size manageable)
        self._build_multi_prefix_index()
        
        elapsed = time.time() - start_time
        print(f"✅ Loaded {len(self.derangements_with_signs):,} smart derangements in {elapsed:.3f}s")
        print(f"   Database indices: {len(self.position_value_index)} position-value pairs")
    
    def _save_to_disk(self, cache_file: Path):
        """Save smart derangement cache to disk."""
        # Convert position_value_index to JSON-serializable format
        position_value_index_serializable = {}
        for (pos, val), indices in self.position_value_index.items():
            key_str = f"{pos},{val}"
            position_value_index_serializable[key_str] = list(indices)
        
        data = {
            'n': self.n,
            'derangements_with_signs': self.derangements_with_signs,
            'prefix_index': self.prefix_index,
            'position_value_index': position_value_index_serializable,
            'created_at': time.time()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, separators=(',', ':'))  # Compact format
        
        file_size_kb = cache_file.stat().st_size / 1024
        print(f"💾 Saved smart derangement cache to {cache_file} ({file_size_kb:.1f} KB)")
    
    def _build_cache(self):
        """Build the smart cache with pre-computed signs and database-style indexing."""
        print(f"🔄 Building smart derangement cache for n={self.n}...")
        start_time = time.time()
        
        # Generate all derangements
        constraints = BitsetConstraints(self.n)
        constraints.add_row_constraints(list(range(1, self.n + 1)))
        derangements = list(generate_constrained_permutations_bitset_optimized(self.n, constraints))
        
        print(f"   Generated {len(derangements):,} derangements")
        
        # Pre-compute signs for 2-row rectangles
        for derangement in derangements:
            # Create 2-row rectangle to get sign
            rect = LatinRectangle(2, self.n, [list(range(1, self.n + 1)), derangement])
            sign = rect.compute_sign()
            self.derangements_with_signs.append((derangement, sign))
        
        # Sort lexicographically for prefix optimization
        self.derangements_with_signs.sort(key=lambda x: x[0])
        
        # Build all indices
        self._build_prefix_index()
        self._build_multi_prefix_index()
        self._build_database_indices()
        
        elapsed = time.time() - start_time
        print(f"✅ Smart cache built in {elapsed:.3f}s")
        print(f"   Single-prefix index: {len(self.prefix_index)} entries")
        print(f"   Multi-prefix index: {len(self.multi_prefix_index)} entries")
        print(f"   Database indices: {len(self.position_value_index)} position-value pairs")
    
    def _build_prefix_index(self):
        """Build single-element prefix index."""
        self.prefix_index = {}
        for i, (derangement, _) in enumerate(self.derangements_with_signs):
            first_val = derangement[0]
            if first_val not in self.prefix_index:
                self.prefix_index[first_val] = []
            self.prefix_index[first_val].append(i)
    
    def _build_multi_prefix_index(self):
        """Build multi-element prefix index for aggressive pruning."""
        self.multi_prefix_index = {}
        
        # Build 2-element prefixes
        for i, (derangement, _) in enumerate(self.derangements_with_signs):
            if len(derangement) >= 2:
                prefix = (derangement[0], derangement[1])
                if prefix not in self.multi_prefix_index:
                    self.multi_prefix_index[prefix] = []
                self.multi_prefix_index[prefix].append(i)
        
        # Could extend to 3-element prefixes for even more aggressive pruning
        # Trade-off: memory usage vs pruning effectiveness
    
    def _build_database_indices(self):
        """Build database-style indices for ultra-fast constraint filtering."""
        print(f"   Building database-style constraint indices...")
        
        # Build position-value index: (pos, val) -> set of compatible derangement indices
        self.position_value_index = {}
        for pos in range(self.n):
            for val in range(1, self.n + 1):
                compatible_indices = set()
                for i, (derangement, _) in enumerate(self.derangements_with_signs):
                    if derangement[pos] == val:
                        compatible_indices.add(i)
                if compatible_indices:  # Only store non-empty sets
                    self.position_value_index[(pos, val)] = compatible_indices
        
        print(f"     Position-value index: {len(self.position_value_index)} entries")
    
    def _get_constraint_hash(self, constraints: BitsetConstraints) -> str:
        """Generate a hash key for constraint state for caching."""
        # Create a compact representation of the constraint state
        forbidden_list = []
        for pos in range(self.n):
            forbidden_vals = []
            for val in range(1, self.n + 1):
                if constraints.is_forbidden(pos, val):
                    forbidden_vals.append(val)
            if forbidden_vals:
                forbidden_list.append(f"{pos}:{','.join(map(str, forbidden_vals))}")
        return "|".join(forbidden_list)
    
    def get_compatible_derangements(self, constraints: BitsetConstraints, 
                                  max_prefix_length: int = 2) -> List[Tuple[List[int], int]]:
        """
        Get derangements compatible with constraints using database-style indexing.
        
        This method uses O(1) set intersections instead of O(n) linear scans,
        providing dramatic performance improvements for constraint filtering.
        
        Args:
            constraints: Current constraint state
            max_prefix_length: Unused (kept for compatibility)
            
        Returns:
            List of (derangement, sign) tuples that satisfy constraints
        """
        return self._get_compatible_with_database_index(constraints)
    
    def _get_compatible_with_single_prefix(self, constraints: BitsetConstraints) -> List[Tuple[List[int], int]]:
        """Get compatible derangements using single-element prefix optimization."""
        compatible = []
        
        # Find possible first values
        possible_first = []
        for val in range(1, self.n + 1):
            if not constraints.is_forbidden(0, val):
                possible_first.append(val)
        
        # Only check derangements with compatible first values
        for first_val in possible_first:
            if first_val in self.prefix_index:
                for idx in self.prefix_index[first_val]:
                    derangement, sign = self.derangements_with_signs[idx]
                    if self._is_fully_compatible(derangement, constraints):
                        compatible.append((derangement, sign))
        
        return compatible
    
    def _get_compatible_with_database_index(self, constraints: BitsetConstraints) -> List[Tuple[List[int], int]]:
        """Get compatible derangements using optimized removal-based filtering."""
        
        # Check cache first
        constraint_hash = self._get_constraint_hash(constraints)
        if constraint_hash in self.constraint_cache:
            compatible_indices = self.constraint_cache[constraint_hash]
            return [(self.derangements_with_signs[i][0], self.derangements_with_signs[i][1]) 
                    for i in compatible_indices]
        
        # Step 1: Start with all derangement indices allowed
        compatible_indices = set(range(len(self.derangements_with_signs)))
        
        # Step 2: For each position, remove derangements with forbidden values
        for pos in range(self.n):
            # Find which values are forbidden at this position
            forbidden_values = []
            for val in range(1, self.n + 1):
                if constraints.is_forbidden(pos, val):
                    forbidden_values.append(val)
            
            # Remove derangements that have forbidden values at this position
            for forbidden_val in forbidden_values:
                if (pos, forbidden_val) in self.position_value_index:
                    # Direct removal of derangements with forbidden value
                    forbidden_indices = self.position_value_index[(pos, forbidden_val)]
                    compatible_indices -= forbidden_indices
            
            # Early termination if no compatible derangements remain
            if not compatible_indices:
                break
        
        # Cache the result for future use
        self.constraint_cache[constraint_hash] = compatible_indices
        
        # Return the compatible derangements with signs
        return [(self.derangements_with_signs[i][0], self.derangements_with_signs[i][1]) 
                for i in compatible_indices]
    
    def _get_compatible_with_multi_prefix(self, constraints: BitsetConstraints) -> List[Tuple[List[int], int]]:
        """Get compatible derangements using multi-element prefix optimization (legacy)."""
        compatible = []
        
        # Find possible 2-element prefixes
        possible_prefixes = []
        for val1 in range(1, self.n + 1):
            if not constraints.is_forbidden(0, val1):
                for val2 in range(1, self.n + 1):
                    if val2 != val1 and not constraints.is_forbidden(1, val2):
                        possible_prefixes.append((val1, val2))
        
        # Only check derangements with compatible prefixes
        for prefix in possible_prefixes:
            if prefix in self.multi_prefix_index:
                for idx in self.multi_prefix_index[prefix]:
                    derangement, sign = self.derangements_with_signs[idx]
                    if self._is_fully_compatible(derangement, constraints):
                        compatible.append((derangement, sign))
        
        return compatible
    
    def _is_fully_compatible(self, derangement: List[int], constraints: BitsetConstraints) -> bool:
        """Check if entire derangement is compatible with constraints."""
        for pos, val in enumerate(derangement):
            if constraints.is_forbidden(pos, val):
                return False
        return True
    
    def get_all_derangements_with_signs(self) -> List[Tuple[List[int], int]]:
        """Get all derangements with pre-computed signs."""
        return self.derangements_with_signs.copy()
    
    def get_statistics(self) -> Dict[str, any]:
        """Get cache statistics and analysis."""
        total_derangements = len(self.derangements_with_signs)
        
        # Analyze prefix distribution
        prefix_distribution = {}
        for val in range(1, self.n + 1):
            count = len(self.prefix_index.get(val, []))
            prefix_distribution[val] = {
                'count': count,
                'percentage': (count / total_derangements) * 100 if total_derangements > 0 else 0
            }
        
        # Analyze sign distribution
        positive_count = sum(1 for _, sign in self.derangements_with_signs if sign > 0)
        negative_count = total_derangements - positive_count
        
        return {
            'n': self.n,
            'total_derangements': total_derangements,
            'prefix_distribution': prefix_distribution,
            'sign_distribution': {
                'positive': positive_count,
                'negative': negative_count,
                'difference': positive_count - negative_count
            },
            'index_sizes': {
                'single_prefix': len(self.prefix_index),
                'multi_prefix': len(self.multi_prefix_index)
            }
        }


# Global cache instances
_smart_caches: Dict[int, SmartDerangementCache] = {}

def get_smart_derangement_cache(n: int) -> SmartDerangementCache:
    """Get or create smart derangement cache for given n."""
    if n not in _smart_caches:
        _smart_caches[n] = SmartDerangementCache(n)
    return _smart_caches[n]


def get_smart_derangements_with_signs(n: int) -> List[Tuple[List[int], int]]:
    """
    Convenience function to get all derangements with pre-computed signs.
    
    Args:
        n: Size of permutations
        
    Returns:
        List of (derangement, sign) tuples
    """
    cache = get_smart_derangement_cache(n)
    return cache.get_all_derangements_with_signs()


def get_constraint_compatible_derangements(n: int, constraints: BitsetConstraints) -> List[Tuple[List[int], int]]:
    """
    Get derangements compatible with constraints using smart optimization.
    
    Args:
        n: Size of permutations
        constraints: Current constraint state
        
    Returns:
        List of (derangement, sign) tuples that satisfy constraints
    """
    cache = get_smart_derangement_cache(n)
    return cache.get_compatible_derangements(constraints)


if __name__ == "__main__":
    # Test the smart derangement cache
    print("🧪 Testing Smart Derangement Cache...")
    
    for n in [7, 8]:
        print(f"\n📊 Testing n={n}:")
        cache = SmartDerangementCache(n)
        stats = cache.get_statistics()
        
        print(f"   Total derangements: {stats['total_derangements']:,}")
        print(f"   Sign distribution: +{stats['sign_distribution']['positive']:,} -{stats['sign_distribution']['negative']:,}")
        print(f"   Difference: {stats['sign_distribution']['difference']:+,}")
        
        # Test constraint filtering
        constraints = BitsetConstraints(n)
        constraints.add_row_constraints(list(range(1, n + 1)))
        constraints.add_forbidden(0, 2)  # Position 0 cannot be 2
        
        compatible = cache.get_compatible_derangements(constraints)
        reduction = (1 - len(compatible) / stats['total_derangements']) * 100
        print(f"   With constraints: {len(compatible):,} compatible ({reduction:.1f}% reduction)")