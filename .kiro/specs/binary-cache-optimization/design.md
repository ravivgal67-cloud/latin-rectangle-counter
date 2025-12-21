# Design Document: Binary Cache Optimization

## Overview

The Binary Cache Optimization replaces the current JSON-based derangement cache with a compact binary format using NumPy arrays. This optimization achieves 90%+ memory reduction and 5-10x faster loading times, enabling computations with larger dimensions (n=9, n=10) and improving parallel processing efficiency.

The design maintains full API compatibility with the existing SmartDerangementCache while providing automatic migration from JSON to binary format.

## Architecture

The system follows a layered approach with automatic format detection and fallback:

```
┌─────────────────────────────────────────┐
│         Cache Factory Layer             │
│  (Format Detection | Fallback Logic)    │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│      CompactDerangementCache            │
│  (Binary Format | NumPy Arrays)         │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         Binary File Format              │
│  (Header | Arrays | Indices | CRC32)    │
└─────────────────────────────────────────┘
```

### Technology Stack

- **NumPy**: Efficient array storage and operations
- **Struct**: Binary file format encoding/decoding
- **CRC32**: Data integrity validation
- **Pathlib**: Cross-platform file handling

## Components and Interfaces

### 1. Binary File Format

#### File Structure
```
┌─────────────────────────────────────────┐
│ Header (64 bytes)                       │
│ - Magic: "LRCC" (4 bytes)               │
│ - Version: uint32 (4 bytes)             │
│ - n: uint32 (4 bytes)                   │
│ - count: uint32 (4 bytes)               │
│ - derangements_offset: uint32 (4 bytes) │
│ - signs_offset: uint32 (4 bytes)        │
│ - indices_offset: uint32 (4 bytes)      │
│ - checksum: uint32 (4 bytes)            │
│ - reserved: 32 bytes                    │
├─────────────────────────────────────────┤
│ Derangements Array                      │
│ (count × n × uint8)                     │
├─────────────────────────────────────────┤
│ Signs Array                             │
│ (count × int8)                          │
├─────────────────────────────────────────┤
│ Position-Value Index                    │
│ (binary encoded dictionary)             │
└─────────────────────────────────────────┘
```

#### Header Format
- **Magic**: "LRCC" identifier for Latin Rectangle Compact Cache
- **Version**: Format version for future compatibility
- **n**: Dimension size
- **count**: Number of derangements
- **Offsets**: Byte positions of each data section
- **Checksum**: CRC32 of all data sections
- **Reserved**: Space for future extensions

### 2. CompactDerangementCache Class

```python
class CompactDerangementCache:
    """
    Compact binary cache with NumPy arrays for maximum efficiency.
    
    Features:
    - 10-30x smaller memory footprint than JSON
    - Fast binary loading (no JSON parsing)
    - NumPy arrays for optimal access patterns
    - Same API as current SmartDerangementCache
    """
    
    def __init__(self, n: int, cache_dir: str = "cache/smart_derangements"):
        self.n = n
        self.cache_dir = Path(cache_dir)
        
        # NumPy arrays for efficient storage
        self.derangements: np.ndarray = None    # shape: (count, n), dtype: uint8
        self.signs: np.ndarray = None           # shape: (count,), dtype: int8
        
        # Database-style indices (same as JSON version)
        self.position_value_index: Dict[Tuple[int, int], Set[int]] = {}
        self.prefix_index: Dict[int, List[int]] = {}
        self.multi_prefix_index: Dict[Tuple[int, ...], List[int]] = {}
        self.constraint_cache: Dict[str, Set[int]] = {}
        
    def get_derangement(self, index: int) -> Tuple[List[int], int]:
        """O(1) access to derangement by index."""
        
    def get_derangements_batch(self, indices: List[int]) -> List[Tuple[List[int], int]]:
        """Efficient batch access using NumPy advanced indexing."""
        
    def get_compatible_derangements(self, constraints: BitsetConstraints) -> List[Tuple[List[int], int]]:
        """Same interface as SmartDerangementCache."""
```

### 3. Migration System

#### Automatic Conversion Logic
```python
def _load_or_build_cache(self):
    """Load from binary cache, convert from JSON if needed, or build from scratch."""
    binary_file = self._get_binary_cache_file_path()
    json_file = self._get_json_cache_file_path()
    
    if binary_file.exists():
        try:
            self._load_from_binary(binary_file)
            return
        except Exception as e:
            print(f"⚠️  Binary cache failed: {e}, falling back to JSON")
    
    if json_file.exists():
        self._convert_json_to_binary(json_file, binary_file)
        self._load_from_binary(binary_file)
    else:
        self._build_cache()
        self._save_to_binary(binary_file)
```

## Data Models

### 1. Binary Header Structure

```python
@dataclass
class BinaryHeader:
    magic: bytes = b"LRCC"
    version: int = 1
    n: int = 0
    count: int = 0
    derangements_offset: int = 64
    signs_offset: int = 0
    indices_offset: int = 0
    checksum: int = 0
    reserved: bytes = b'\x00' * 32
```

### 2. Memory Layout Comparison

| Component | JSON Format | Binary Format | Reduction |
|-----------|-------------|---------------|-----------|
| **Derangements** | List[List[int]] | np.uint8[count,n] | 75% |
| **Signs** | List[int] | np.int8[count] | 75% |
| **Indices** | Dict with strings | Binary encoded | 60% |
| **Overall** | ~17 MB (n=8) | ~0.8 MB (n=8) | 95% |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Now I need to analyze the acceptance criteria for testability using the prework tool:

<function_calls>
<invoke name="prework">
<parameter name="featureName">binary-cache-optimization


### Property Reflection

After analyzing all acceptance criteria, I've identified several areas where properties can be consolidated:

**Consolidation Opportunities:**
1. Properties 3.1, 3.2, 3.3 (JSON to binary preservation) can be combined into a single comprehensive round-trip property
2. Properties 4.2, 4.3, 4.4 (API compatibility) can be combined into a single property about result equivalence
3. Properties 6.1, 6.2, 6.3, 6.4, 6.5, 6.6 (binary format structure) can be combined into a single property about format correctness
4. Properties 1.3 and 1.4 (data types and NumPy arrays) can be combined into a single property about internal representation

**Unique Properties to Keep:**
- Memory efficiency comparison (1.2)
- Loading performance comparison (2.1)
- Round-trip data preservation (3.1-3.3 combined)
- Checksum validation (3.4)
- Error handling and fallback (3.5, 8.2)
- API compatibility (4.1, 4.2-4.4 combined, 4.5)
- Binary format correctness (6.1-6.6 combined)
- Scalability (7.4)
- Robustness (8.5)

### Correctness Properties

**Property 1: Memory Efficiency**
*For any* cache dimension n ≥ 2, the Compact_Cache memory usage should be at least 90% less than the JSON_Cache memory usage for the same data.
**Validates: Requirements 1.2**

**Property 2: Loading Performance**
*For any* cache dimension n ≥ 2, the Compact_Cache loading time should be at least 5x faster than the JSON_Cache loading time.
**Validates: Requirements 2.1**

**Property 3: Round-Trip Data Preservation**
*For any* JSON cache file, converting to binary format and loading should preserve all derangements, signs, and position-value indices exactly.
**Validates: Requirements 3.1, 3.2, 3.3**

**Property 4: Checksum Validation**
*For any* binary cache file, if the data is modified after creation, the CRC32 checksum validation should detect the corruption.
**Validates: Requirements 3.4**

**Property 5: Graceful Error Handling**
*For any* corrupted or invalid binary cache file, the system should detect the error and fallback to JSON cache without crashing.
**Validates: Requirements 3.5, 8.2, 8.5**

**Property 6: API Compatibility**
*For any* valid constraints, calling get_compatible_derangements, get_all_derangements_with_signs, or get_statistics on Compact_Cache should return identical results to SmartDerangementCache.
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

**Property 7: Binary Format Correctness**
*For any* generated binary cache file, the file should contain a valid 64-byte header with magic "LRCC", correct version/n/count fields, properly typed NumPy arrays (uint8 for derangements, int8 for signs), and a valid CRC32 checksum.
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

**Property 8: Internal Representation**
*For any* loaded Compact_Cache, the derangements should be stored as NumPy uint8 arrays and signs as NumPy int8 arrays.
**Validates: Requirements 1.3, 1.4**

**Property 9: JSON File Preservation**
*For any* JSON to binary conversion, the original JSON file should remain intact after conversion completes.
**Validates: Requirements 5.4**

**Property 10: Scalability**
*For any* dimension n ≤ 15, the Compact_Cache should be able to create and load cache files without architectural limitations.
**Validates: Requirements 7.4**

## Error Handling

### Error Detection
- **Checksum Validation**: CRC32 checksum computed during write, validated during read
- **Magic Number Check**: Verify "LRCC" magic number on load
- **Version Compatibility**: Check version field for format compatibility
- **Array Dimension Validation**: Verify array shapes match header metadata

### Fallback Strategy
```python
def _load_or_build_cache(self):
    """Multi-level fallback strategy."""
    try:
        # Level 1: Try binary cache
        if binary_file.exists():
            self._load_from_binary(binary_file)
            return
    except Exception as e:
        logger.warning(f"Binary cache failed: {e}")
    
    try:
        # Level 2: Try JSON cache
        if json_file.exists():
            self._convert_json_to_binary(json_file, binary_file)
            self._load_from_binary(binary_file)
            return
    except Exception as e:
        logger.warning(f"JSON conversion failed: {e}")
    
    # Level 3: Build from scratch
    self._build_cache()
    self._save_to_binary(binary_file)
```

### Error Messages
- **Corruption Detected**: "Binary cache corrupted (checksum mismatch), falling back to JSON"
- **Invalid Format**: "Invalid binary format (magic number mismatch), falling back to JSON"
- **Version Mismatch**: "Binary cache version X not supported (current: Y), falling back to JSON"
- **Array Shape Mismatch**: "Binary cache array dimensions don't match header, falling back to JSON"

## Testing Strategy

### Dual Testing Approach

**Unit Tests**: Verify specific examples and edge cases
- Test n=8 memory usage is under 1 MB (example)
- Test automatic conversion when only JSON exists (example)
- Test binary cache is used when both formats exist (example)
- Test n=9 and n=10 memory thresholds (examples)
- Test error messages for specific corruption scenarios

**Property-Based Tests**: Verify universal properties across all inputs
- Test memory efficiency across multiple dimensions (property)
- Test loading performance across multiple dimensions (property)
- Test round-trip preservation for all cache sizes (property)
- Test checksum validation with random corruptions (property)
- Test API compatibility with random constraints (property)
- Test binary format correctness for all generated files (property)
- Test graceful error handling with various corruption types (property)

### Property Test Configuration
- Minimum 100 iterations per property test
- Each test tagged with: **Feature: binary-cache-optimization, Property N: [property text]**
- Use Hypothesis for generating test cases (random dimensions, random constraints, random corruptions)

### Testing Phases

**Phase 1: Small Dimensions (n=3-7)**
- Test correctness and performance on existing caches
- Verify conversion works correctly
- Validate memory and speed improvements
- Run full property test suite

**Phase 2: Medium Dimensions (n=4-7)**
- Test with larger cache files
- Verify parallel processing efficiency
- Validate scalability improvements

**Phase 3: Large Dimensions (n=8)**
- Careful testing due to long run times
- Verify memory usage under 1 MB
- Validate 95% memory reduction
- Test parallel processing with 8 processes

**Phase 4: Future Dimensions (n=9, n=10)**
- Generate and test new cache files
- Verify memory usage within limits
- Validate scalability for research use

### Test Coverage Goals
- 100% coverage of CompactDerangementCache public methods
- 100% coverage of binary format read/write operations
- 100% coverage of error handling and fallback logic
- 100% coverage of conversion utilities

## Implementation Notes

### NumPy Array Benefits
- **Contiguous Memory**: Better cache locality and performance
- **Vectorized Operations**: Fast batch access using advanced indexing
- **Type Safety**: Enforced uint8/int8 types prevent overflow
- **Memory Efficiency**: Minimal overhead compared to Python lists

### Migration Safety
- JSON files are never deleted automatically
- Binary files are written atomically (write to temp, then rename)
- Checksum validation ensures data integrity
- Automatic fallback provides robustness

### Performance Optimizations
- **Lazy Index Building**: Indices built on-demand if not in binary file
- **Batch Operations**: NumPy advanced indexing for multiple derangements
- **Memory Mapping**: Future optimization for very large caches (n>10)
- **Compression**: Future optimization using zlib for even smaller files

### Compatibility Considerations
- Same API as SmartDerangementCache (drop-in replacement)
- Factory function `get_smart_derangement_cache()` returns appropriate type
- Existing code requires zero changes
- Tests pass without modification

## Future Enhancements

### Potential Optimizations
1. **Compression**: Add zlib compression for 50-70% additional size reduction
2. **Memory Mapping**: Use np.memmap for caches larger than available RAM
3. **Incremental Loading**: Load only needed derangements for very large caches
4. **Parallel Conversion**: Use multiprocessing for faster JSON to binary conversion
5. **Index Optimization**: Store indices as NumPy arrays instead of Python dicts

### Scalability Path
- **n=11**: ~700 MB binary (feasible with current design)
- **n=12**: ~7 GB binary (requires memory mapping)
- **n=13+**: Requires streaming/incremental approaches

## References

- NumPy Documentation: https://numpy.org/doc/stable/
- Python struct module: https://docs.python.org/3/library/struct.html
- CRC32 checksums: https://docs.python.org/3/library/zlib.html#zlib.crc32
