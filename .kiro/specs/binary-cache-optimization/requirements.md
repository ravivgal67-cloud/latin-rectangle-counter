# Requirements Document: Binary Cache Optimization

## Introduction

The Binary Cache Optimization feature replaces the current JSON-based derangement cache with a compact binary format to achieve significant memory reduction and performance improvements. This optimization is essential for enabling computations with larger dimensions (n=9, n=10) and improving parallel processing efficiency.

## Glossary

- **Derangement_Cache**: Storage system for pre-computed derangements with signs and constraint indices
- **Binary_Format**: Compact binary file format using NumPy arrays for efficient storage and loading
- **JSON_Cache**: Current text-based cache format with significant memory overhead
- **Compact_Cache**: New binary cache implementation with 90%+ memory reduction
- **Position_Value_Index**: Database-style index mapping (position, value) pairs to compatible derangement indices
- **Round_Trip_Property**: Converting JSON to binary and back should preserve all data

## Requirements

### Requirement 1: Memory Efficiency

**User Story:** As a researcher, I want the derangement cache to use minimal memory, so that I can perform computations with larger dimensions (n=9, n=10) without running out of memory.

#### Acceptance Criteria

1. WHEN loading n=8 cache, THE Compact_Cache SHALL use less than 1 MB of memory
2. WHEN loading any cache, THE Compact_Cache SHALL use at least 90% less memory than the JSON_Cache
3. WHEN storing derangements, THE Binary_Format SHALL use compact data types (uint8 for permutations, int8 for signs)
4. WHEN loading cache data, THE Compact_Cache SHALL load entirely into NumPy arrays for optimal memory layout

### Requirement 2: Performance Improvement

**User Story:** As a user, I want the cache to load quickly, so that computations start without long initialization delays.

#### Acceptance Criteria

1. WHEN loading cache from disk, THE Compact_Cache SHALL load at least 5x faster than JSON_Cache
2. WHEN accessing derangements, THE Compact_Cache SHALL provide O(1) access time using NumPy indexing
3. WHEN performing batch operations, THE Compact_Cache SHALL use NumPy advanced indexing for efficiency
4. WHEN filtering by constraints, THE Compact_Cache SHALL maintain the same performance as JSON_Cache

### Requirement 3: Data Integrity

**User Story:** As a developer, I want the binary cache to preserve all data accurately, so that computations remain mathematically correct.

#### Acceptance Criteria

1. WHEN converting JSON to binary, THE Compact_Cache SHALL preserve all derangement data exactly
2. WHEN converting JSON to binary, THE Compact_Cache SHALL preserve all sign values exactly
3. WHEN converting JSON to binary, THE Compact_Cache SHALL preserve all position-value indices exactly
4. WHEN loading binary cache, THE Compact_Cache SHALL validate data integrity using CRC32 checksums
5. WHEN binary data is corrupted, THE Compact_Cache SHALL detect corruption and fallback to JSON

### Requirement 4: API Compatibility

**User Story:** As a developer, I want the new cache to work with existing code, so that no changes are required to current implementations.

#### Acceptance Criteria

1. THE Compact_Cache SHALL implement the same public interface as SmartDerangementCache
2. WHEN calling get_compatible_derangements, THE Compact_Cache SHALL return identical results to JSON_Cache
3. WHEN calling get_all_derangements_with_signs, THE Compact_Cache SHALL return identical results to JSON_Cache
4. WHEN calling get_statistics, THE Compact_Cache SHALL return identical statistics to JSON_Cache
5. THE Compact_Cache SHALL be a drop-in replacement requiring no code changes

### Requirement 5: Automatic Migration

**User Story:** As a user, I want the system to automatically convert existing caches, so that I don't need to manually manage the migration.

#### Acceptance Criteria

1. WHEN a JSON cache exists and no binary cache exists, THE System SHALL automatically convert JSON to binary
2. WHEN both JSON and binary caches exist, THE System SHALL use the binary cache
3. WHEN binary cache loading fails, THE System SHALL fallback to JSON cache automatically
4. WHEN conversion completes, THE System SHALL preserve the original JSON files for rollback safety
5. THE System SHALL log conversion progress and completion status

### Requirement 6: Binary File Format

**User Story:** As a developer, I want a well-defined binary format, so that the cache files are reliable and can be validated.

#### Acceptance Criteria

1. THE Binary_Format SHALL include a 64-byte header with magic number "LRCC"
2. THE Binary_Format SHALL include version, n, count, and checksum in the header
3. THE Binary_Format SHALL store derangements as (count × n × uint8) array
4. THE Binary_Format SHALL store signs as (count × int8) array
5. THE Binary_Format SHALL store position-value indices in binary-encoded format
6. THE Binary_Format SHALL include CRC32 checksum for data validation

### Requirement 7: Scalability

**User Story:** As a researcher, I want the cache to support larger dimensions, so that I can explore n=9 and n=10 computations.

#### Acceptance Criteria

1. WHEN n=9 cache is created, THE Compact_Cache SHALL use less than 10 MB of memory
2. WHEN n=10 cache is created, THE Compact_Cache SHALL use less than 100 MB of memory
3. WHEN parallel processing is used, THE Compact_Cache SHALL maintain efficiency with multiple processes
4. THE Compact_Cache SHALL support dimensions up to n=15 without architectural limitations

### Requirement 8: Error Handling

**User Story:** As a developer, I want robust error handling, so that cache failures don't crash the application.

#### Acceptance Criteria

1. WHEN binary file is corrupted, THE Compact_Cache SHALL detect corruption and report clear error messages
2. WHEN binary file format is invalid, THE Compact_Cache SHALL fallback to JSON cache gracefully
3. WHEN disk space is insufficient, THE Compact_Cache SHALL handle write failures gracefully
4. WHEN JSON conversion fails, THE Compact_Cache SHALL report specific error details
5. THE Compact_Cache SHALL never crash the application due to cache errors