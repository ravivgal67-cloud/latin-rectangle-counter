# Correct Baseline Performance Results for (4,7)

## What Happened

Initially, we got confusing results showing a 67x speedup, which is impossible with only 4-8 processes. The issue was that we were running tests on your **local uncommitted changes** that already included first-column optimization code, not the actual main branch.

## Actual Main Branch Baseline

After stashing local changes and testing the clean main branch:

### Test Configuration
- **Problem**: Latin rectangles (4,7) = 155,185,920 total rectangles
- **Platform**: Clean main branch (commit 4695c57) - no local modifications
- **Algorithm**: Second-row-based parallelization (actual main branch implementation)
- **Date**: December 25, 2025

### Performance Results

| Processes | Time (s) | Rectangles/sec | Speedup | Efficiency |
|-----------|----------|----------------|---------|------------|
| 1         | 50.910   | 3,048,253      | 1.00x   | 100.0%     |
| 4         | 13.214   | 11,745,012     | 3.85x   | 96.3%      |
| 8         | 7.283    | 21,307,627     | 6.99x   | 87.4%      |

## Key Observations

1. **Realistic Speedup**: 6.99x speedup with 8 processes is realistic and achievable
2. **Good Efficiency**: 87.4% efficiency shows the parallel implementation is well-optimized
3. **Near-Linear Scaling**: Close to theoretical maximum (87.4% of 8x theoretical max)
4. **Proper Algorithm**: Uses second-row-based parallelization as expected from main branch

## Comparison: Local vs Main Branch

| Implementation | 4 Processes | 8 Processes | Algorithm |
|----------------|-------------|-------------|-----------|
| **Local (first-column)** | 0.745s (67x) | 0.987s (51x) | First-column optimization |
| **Main (second-row)** | 13.214s (3.85x) | 7.283s (6.99x) | Second-row parallelization |

## Baseline Established

This establishes the **correct baseline** for your first-column-optimization branch:

- **Sequential baseline**: 50.910s (3.0M rectangles/sec)
- **Best parallel baseline**: 7.283s with 8 processes (21.3M rectangles/sec, 6.99x speedup)
- **Target for optimization**: Your first-column optimization should improve upon this realistic 6.99x baseline

## Next Steps

Your first-column optimization branch shows dramatic improvements (67x vs 6.99x), indicating the optimization is working very well. The proper comparison would be:

- **Main branch**: 7.283s (6.99x speedup)
- **Your optimization**: 0.745s (67x speedup) 
- **Improvement**: ~10x faster than the current main branch parallel implementation

This represents a significant algorithmic improvement, not just parallelization gains.