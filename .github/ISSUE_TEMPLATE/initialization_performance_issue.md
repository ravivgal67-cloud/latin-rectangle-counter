---
name: Initialization Performance Issue
about: Report slow initialization phases that delay computation start
title: 'PERF: Slow initialization phase for large computations (5,8)'
labels: ['performance', 'initialization', 'optimization', 'high-priority']
assignees: ''
---

## Problem Description

The initialization phase for large computations like (5,8) is taking an excessive amount of time (>1 minute) before actual computation begins. This creates a poor user experience and delays results.

## Steps to Reproduce

1. Start computation for dimensions (5,8) using parallel ultra-safe bitwise
2. Observe that processes register but don't start actual computation
3. Wait >1 minute for initialization to complete

## Expected Behavior

- Initialization should complete in <10 seconds
- Clear progress indication during initialization
- Processes should start computation quickly

## Actual Behavior

- (5,8) computation stuck in initialization for >1 minute
- No progress indication during initialization phase
- Appears frozen to users

## Root Cause Analysis

Based on code analysis, the bottleneck is in **smart derangement cache initialization**:

1. **Database Index Building**: Each process rebuilds database-style constraint indices
   - `position_value_index` with 30+ entries for n=8
   - `prefix_index` and `multi_prefix_index` 
   - This happens **per process** (8 times for 8 processes)

2. **Cache Loading**: 14,833 derangements loaded from JSON
   - File I/O happens multiple times
   - JSON parsing for large datasets
   - Sign computation verification

3. **Bitset Initialization**: 14,833-bit bitsets created per process
   - Memory allocation for large bitsets
   - Constraint compatibility matrices

## Proposed Solutions

### 1. Pre-computed Cache Optimization (High Priority)
- Pre-build database indices and save to disk alongside derangements
- Serialize bitset structures to avoid runtime reconstruction
- Single initialization with shared memory for indices

### 2. Lazy Loading (Medium Priority)  
- Load only the derangements needed for each process partition
- Stream derangements instead of loading all 14,833 at once
- Progressive index building as needed

### 3. Shared Memory Architecture (Low Priority)
- Use multiprocessing shared memory for common data structures
- Single parent process loads cache, children access via shared memory

## Environment

- **Computation**: (5,8) with 8 processes
- **Derangements**: 14,833 for n=8
- **System**: macOS with Python multiprocessing

## Files Involved

- `core/smart_derangement_cache.py` - Cache loading and index building
- `core/parallel_ultra_bitwise.py` - Process initialization
- `core/ultra_safe_bitwise.py` - Cache access
- `cache/smart_derangements/` - Cache files

## Priority

**HIGH** - This blocks usability for large computations and creates poor user experience.

## Estimated Effort

2-3 hours:
- 1 hour: Enhanced cache format
- 1 hour: Partition loading  
- 1 hour: Testing and validation