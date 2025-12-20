#!/usr/bin/env python3
"""
Simple completion optimization tests - no hanging, no complex logging.

Tests the basic completion optimization logic by directly calling the core
partition function without parallel processing overhead.

NOTE: These tests are marked as 'slow' because pytest coverage causes 100x slowdown
in the tight nested loops of the completion optimization code.
"""

import pytest
from pathlib import Path

from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise
from core.parallel_completion_optimization import count_rectangles_completion_partition
from core.logging_config import close_logger
from tests.test_base import TestBaseWithProductionLogs


class TestCompletionOptimization(TestBaseWithProductionLogs):
    """Test completion optimization functionality."""
    
    def test_completion_correctness_fast(self):
        """Test completion optimization correctness using known values - fast test."""
        # Known correct values from cache/previous computations
        known_values = {
            (3, 4): (24, 12, 12),
            (4, 4): (24, 24, 0),
            (4, 5): (1344, 384, 960), 
            (5, 5): (1344, 384, 960),
        }
        
        test_cases = [(3, 4), (4, 5)]  # Fast cases only
        
        for r, n in test_cases:
            print(f"\n🧪 Testing completion optimization for ({r},{n}) + ({r+1},{n})")
            
            # Use known values instead of computing
            expected_r = known_values[(r, n)]
            expected_r1 = known_values[(r+1, n)]
            
            # Get all derangement indices for direct partition call
            from core.smart_derangement_cache import get_smart_derangement_cache
            cache = get_smart_derangement_cache(n)
            derangements_with_signs = cache.get_all_derangements_with_signs()
            all_indices = list(range(len(derangements_with_signs)))
            
            # Call completion partition directly (no parallel overhead)
            # Note: This still uses production logs since the partition function doesn't accept log_dir
            total_r_tog, pos_r_tog, neg_r_tog, total_r1_tog, pos_r1_tog, neg_r1_tog, elapsed = \
                count_rectangles_completion_partition(r, n, all_indices, 0, f"test_completion_{r}_{n}")
            
            # Verify correctness against known values
            assert (total_r_tog, pos_r_tog, neg_r_tog) == expected_r, f"({r},{n}) mismatch: got {(total_r_tog, pos_r_tog, neg_r_tog)}, expected {expected_r}"
            assert (total_r1_tog, pos_r1_tog, neg_r1_tog) == expected_r1, f"({r+1},{n}) mismatch: got {(total_r1_tog, pos_r1_tog, neg_r1_tog)}, expected {expected_r1}"
            
            print(f"✅ ({r},{n}) + ({r+1},{n}): Correctness verified in {elapsed:.3f}s")

    
    def test_completion_parallel_multiprocess(self):  # pragma: no cover
        """Test parallel completion optimization with 4 processes for (5,6).
        
        This validates the multiprocess completion optimization works correctly
        and prepares us for production (6,7) runs with multiple processes.
        """
        from core.parallel_completion_optimization import count_rectangles_with_completion_parallel
        
        r, n = 5, 6
        num_processes = 4
        
        print(f"\n🚀 Testing parallel completion optimization ({r},{n}) + ({r+1},{n}) with {num_processes} processes")
        
        # Known correct values from cache/previous computations
        expected_5_6 = (1128960, 576000, 552960)
        expected_6_6 = (1128960, 426240, 702720)
        
        # Compute with parallel completion optimization
        (total_r_par, pos_r_par, neg_r_par), (total_r1_par, pos_r1_par, neg_r1_par) = \
            count_rectangles_with_completion_parallel(r, n, num_processes=num_processes)
        
        # Verify correctness against known values
        actual_5_6 = (total_r_par, pos_r_par, neg_r_par)
        actual_6_6 = (total_r1_par, pos_r1_par, neg_r1_par)
        
        assert actual_5_6 == expected_5_6, f"(5,6) mismatch: got {actual_5_6}, expected {expected_5_6}"
        assert actual_6_6 == expected_6_6, f"(6,6) mismatch: got {actual_6_6}, expected {expected_6_6}"
        
        print(f"✅ Parallel completion optimization with {num_processes} processes: PASSED")
        print(f"   (5,6): {total_r_par:,} rectangles (+{pos_r_par:,} -{neg_r_par:,})")
        print(f"   (6,6): {total_r1_par:,} rectangles (+{pos_r1_par:,} -{neg_r1_par:,})")
        

    
    def test_completion_invalid_input(self):
        """Test that completion optimization rejects invalid inputs."""
        
        from core.parallel_completion_optimization import count_rectangles_with_completion_parallel
        
        # Test with invalid r != n-1 cases
        with pytest.raises(ValueError, match="requires r = n-1"):
            # This should fail because r != n-1
            count_rectangles_with_completion_parallel(3, 6, num_processes=1)
        
        with pytest.raises(ValueError, match="requires r = n-1"):
            # This should fail because r != n-1  
            count_rectangles_with_completion_parallel(2, 5, num_processes=1)
        
        print("✅ Invalid input handling verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-cov"])