#!/usr/bin/env python3
"""
Test the r >= n/2 threshold hypothesis for optimization effectiveness.
"""

# Test cases organized by r/n ratio
test_cases = [
    # r/n ratio < 0.5 (should favor naive)
    (3, 7),   # 0.43
    (3, 6),   # 0.50 - boundary
    (4, 9),   # 0.44
    
    # r/n ratio >= 0.5 (should favor optimized)
    (4, 8),   # 0.50 - boundary
    (5, 10),  # 0.50 - boundary
    (4, 7),   # 0.57
    (5, 9),   # 0.56
    (5, 8),   # 0.63
    (6, 10),  # 0.60
    
    # r/n ratio > 0.7 (should strongly favor optimized)
    (5, 6),   # 0.83
    (6, 7),   # 0.86
    (7, 8),   # 0.88
]

print("Hypothesis: Optimization is worthwhile when r >= n/2")
print("\nTest cases organized by r/n ratio:")
print(f"{'Dimension':<12} {'r/n ratio':<12} {'Prediction':<20}")
print("-" * 50)

for r, n in test_cases:
    ratio = r / n
    prediction = "Optimized wins" if ratio >= 0.5 else "Naive wins"
    print(f"({r},{n}){' '*8} {ratio:.2f}{' '*8} {prediction}")

print("\nKey insight: As r approaches n, more constraints accumulate from")
print("previous rows, making early pruning and forced move detection more effective.")
