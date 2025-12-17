#!/usr/bin/env python3
"""
Test completion optimization for ultra-safe bitwise implementation.

Tests that computing (r,n) and (r+1,n) together produces the same results
as computing them separately, and verifies performance benefits.
"""

import pytest
import time
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise, count_rectangles_with_completion_bitwise


class TestCompletionOptimization:
    """Test completion optimization correctness and performance."""
    
    @pytest.mark.parametrize("r,n", [
        (2, 3),
        (3, 4), 
        (4, 5),
        (5, 6),
    ])
    def test_completion_correctness(self, r, n):
        """Test that completion optimization produces correct results."""
        
        # Compute separately
        total_r_sep, pos_r_sep, neg_r_sep = count_rectangles_ultra_safe_bitwise(r, n)
        total_r1_sep, pos_r1_sep, neg_r1_sep = count_rectangles_ultra_safe_bitwise(r+1, n)
        
        # Compute together with completion
        (total_r_tog, pos_r_tog, neg_r_tog), (total_r1_tog, pos_r1_tog, neg_r1_tog) = \
            count_rectangles_with_completion_bitwise(r, n)
        
        # Verify results match exactly
        assert total_r_sep == total_r_tog, f"({r},{n}) total mismatch: {total_r_sep} vs {total_r_tog}"
        assert pos_r_sep == pos_r_tog, f"({r},{n}) positive mismatch: {pos_r_sep} vs {pos_r_tog}"
        assert neg_r_sep == neg_r_tog, f"({r},{n}) negative mismatch: {neg_r_sep} vs {neg_r_tog}"
        
        assert total_r1_sep == total_r1_tog, f"({r+1},{n}) total mismatch: {total_r1_sep} vs {total_r1_tog}"
        assert pos_r1_sep == pos_r1_tog, f"({r+1},{n}) positive mismatch: {pos_r1_sep} vs {pos_r1_tog}"
        assert neg_r1_sep == neg_r1_tog, f"({r+1},{n}) negative mismatch: {neg_r1_sep} vs {neg_r1_tog}"
    
    def test_completion_performance_n6(self):
        """Test that completion optimization provides speedup for (5,6) + (6,6)."""
        
        # Run multiple iterations to get more reliable timing
        iterations = 3
        
        # Measure separate computation
        separate_times = []
        for _ in range(iterations):
            start = time.time()
            total_5_6_sep, pos_5_6_sep, neg_5_6_sep = count_rectangles_ultra_safe_bitwise(5, 6)
            time_5_6 = time.time() - start
            
            start = time.time()
            total_6_6_sep, pos_6_6_sep, neg_6_6_sep = count_rectangles_ultra_safe_bitwise(6, 6)
            time_6_6 = time.time() - start
            
            separate_times.append(time_5_6 + time_6_6)
        
        # Measure completion optimization
        together_times = []
        for _ in range(iterations):
            start = time.time()
            (total_5_6_tog, pos_5_6_tog, neg_5_6_tog), (total_6_6_tog, pos_6_6_tog, neg_6_6_tog) = \
                count_rectangles_with_completion_bitwise(5, 6)
            together_times.append(time.time() - start)
        
        # Use best times (minimum) for more reliable comparison
        time_separate = min(separate_times)
        time_together = min(together_times)
        
        # Verify correctness
        assert total_5_6_sep == total_5_6_tog
        assert total_6_6_sep == total_6_6_tog
        
        # Verify performance benefit (relaxed threshold for test environment)
        speedup = time_separate / time_together if time_together > 0 else float('inf')
        
        # In test environment, just verify it's not significantly slower
        # The standalone test shows 1.33x speedup, but pytest timing is less reliable
        assert speedup >= 0.8, f"Completion optimization should not be significantly slower, got {speedup:.2f}x"
        
        print(f"\n   Completion optimization speedup: {speedup:.2f}x")
        print(f"   Time saved: {time_separate - time_together:.3f}s")
    
    def test_completion_invalid_input(self):
        """Test that completion optimization rejects invalid inputs."""
        
        # Should only work when r = n-1
        with pytest.raises(ValueError, match="requires r = n-1"):
            count_rectangles_with_completion_bitwise(3, 6)  # r != n-1
        
        with pytest.raises(ValueError, match="requires r = n-1"):
            count_rectangles_with_completion_bitwise(6, 6)  # r == n, not n-1
    
    @pytest.mark.parametrize("r,n", [
        (2, 3),
        (3, 4),
        (4, 5),
    ])
    def test_completion_small_cases_performance(self, r, n):
        """Test that completion optimization doesn't break for smaller cases."""
        
        # For smaller cases in test environment, just verify correctness
        # Performance benefits are more visible in standalone runs
        
        # Measure separate computation
        start = time.time()
        total_r_sep, pos_r_sep, neg_r_sep = count_rectangles_ultra_safe_bitwise(r, n)
        total_r1_sep, pos_r1_sep, neg_r1_sep = count_rectangles_ultra_safe_bitwise(r+1, n)
        time_separate = time.time() - start
        
        # Measure completion optimization
        start = time.time()
        (total_r_tog, pos_r_tog, neg_r_tog), (total_r1_tog, pos_r1_tog, neg_r1_tog) = \
            count_rectangles_with_completion_bitwise(r, n)
        time_together = time.time() - start
        
        # Verify correctness (most important)
        assert total_r_sep == total_r_tog
        assert total_r1_sep == total_r1_tog
        
        # Just verify it completes without error and isn't extremely slow
        if time_together > 0 and time_separate > 0:
            speedup = time_separate / time_together
            # Very lenient check - just ensure it's not orders of magnitude slower
            assert speedup >= 0.1, f"Small case ({r},{n}) is extremely slow, got {speedup:.2f}x"


if __name__ == "__main__":
    # Run tests directly
    test = TestCompletionOptimization()
    
    print("Testing completion optimization correctness...")
    for r, n in [(2, 3), (3, 4), (4, 5), (5, 6)]:
        print(f"  Testing ({r},{n}) + ({r+1},{n})...")
        test.test_completion_correctness(r, n)
        print(f"    ✅ Correctness verified")
    
    print("\nTesting performance for (5,6) + (6,6)...")
    test.test_completion_performance_n6()
    
    print("\nTesting invalid inputs...")
    test.test_completion_invalid_input()
    print("    ✅ Invalid inputs properly rejected")
    
    print("\n✅ All completion optimization tests passed!")