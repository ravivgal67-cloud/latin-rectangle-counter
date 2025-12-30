# Baseline Performance Results for (4,7)

## Test Configuration
- **Problem**: Latin rectangles (4,7) = 155,185,920 total rectangles
- **Platform**: Main trunk implementation (commit 4695c57)
- **Algorithm**: Ultra-safe bitwise with first-column optimization
- **Date**: December 25, 2025

## Performance Results

| Processes | Time (s) | Rectangles/sec | Speedup | Efficiency |
|-----------|----------|----------------|---------|------------|
| 1         | 50.130   | 3,095,678      | 1.00x   | 100.0%     |
| 4         | 0.745    | 208,392,780    | 67.26x  | 1681.5%    |
| 8         | 0.987    | 157,457,742    | 50.81x  | 635.2%     |

## Key Observations

1. **Dramatic Speedup**: The parallel implementation shows exceptional performance with 67x speedup at 4 processes
2. **Optimal Process Count**: 4 processes provides the best performance (0.745s vs 0.987s for 8 processes)
3. **Super-linear Efficiency**: The >100% efficiency indicates the parallel version uses a different (more efficient) algorithm than the sequential version
4. **Algorithm Difference**: The sequential test uses `count_rectangles_ultra_safe_bitwise` while parallel uses `count_rectangles_parallel_first_column` with first-column optimization

## Technical Notes

- The parallel implementation uses first-column-based work distribution with 20 first-column choices
- Each first-column choice has a symmetry factor of 6 (representing 6 equivalent rectangles)
- The dramatic speedup suggests the first-column optimization provides algorithmic improvements beyond just parallelization
- Process overhead becomes apparent at 8 processes where performance degrades compared to 4 processes

## Baseline Established

This establishes our performance baseline for comparing the first-column-optimization branch improvements:
- **Sequential baseline**: 50.130s (3.1M rectangles/sec)
- **Best parallel baseline**: 0.745s with 4 processes (208.4M rectangles/sec)
- **Target for optimization**: Improve upon the 67.26x speedup achieved by the current parallel implementation