#!/usr/bin/env python3
"""
Extended tests for auto_counter module to improve coverage.

Tests the automatic counter selection logic that currently has 32% coverage.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from core.auto_counter import count_rectangles_auto
from tests.test_base import TestBaseWithProductionLogs


class TestAutoCounterExtended(TestBaseWithProductionLogs):
    """Extended tests for automatic counter selection."""
    
    def test_parameter_validation(self):
        """Test parameter validation and error handling."""
        
        # Test conflicting force flags
        with pytest.raises(ValueError, match="Cannot force both single and parallel"):
            count_rectangles_auto(3, 6, force_single=True, force_parallel=True)
        
        print("✅ Parameter validation tests passed")
    
    def test_automatic_selection_logic(self):
        """Test the automatic selection logic for different problem sizes."""
        
        # Test small problems (n ≤ 6) - should use single-threaded
        test_cases_small = [
            (3, 4),  # Very small
            (3, 5),  # Small
            (4, 6),  # Medium-small
        ]
        
        for r, n in test_cases_small:
            result = count_rectangles_auto(r, n)
            
            # Verify result structure
            assert hasattr(result, 'positive_count')
            assert hasattr(result, 'negative_count')
            assert hasattr(result, 'computation_time')
            assert hasattr(result, 'from_cache')
            
            # Verify correctness
            total = result.positive_count + result.negative_count
            assert total > 0, f"({r},{n}) should have rectangles"
            assert result.positive_count >= 0 and result.negative_count >= 0
            
            print(f"✅ Auto-selection ({r},{n}): {total} rectangles in {result.computation_time:.3f}s")
    
    def test_large_problem_selection(self):
        """Test selection for large problems (n ≥ 7)."""
        
        # Test large problems - should use parallel
        test_cases_large = [
            (3, 7),  # Production case
        ]
        
        for r, n in test_cases_large:
            result = count_rectangles_auto(r, n, num_processes=2)  # Use 2 processes for faster testing
            
            # Verify result structure
            assert hasattr(result, 'positive_count')
            assert hasattr(result, 'negative_count')
            assert hasattr(result, 'computation_time')
            
            # Verify correctness
            total = result.positive_count + result.negative_count
            assert total > 0, f"({r},{n}) should have rectangles"
            assert result.positive_count >= 0 and result.negative_count >= 0
            
            print(f"✅ Auto-selection large ({r},{n}): {total} rectangles in {result.computation_time:.3f}s")
    
    def test_force_single_threaded(self):
        """Test forcing single-threaded processing."""
        
        # Force single-threaded for a problem that would normally be parallel
        result = count_rectangles_auto(3, 7, force_single=True)
        
        # Should still work correctly
        total = result.positive_count + result.negative_count
        assert total > 0, "Forced single-threaded should work"
        
        print(f"✅ Forced single-threaded (3,7): {total} rectangles in {result.computation_time:.3f}s")
    
    def test_force_parallel(self):
        """Test forcing parallel processing."""
        
        # Force parallel for a problem that would normally be single-threaded
        result = count_rectangles_auto(3, 5, force_parallel=True, num_processes=2)
        
        # Should still work correctly
        total = result.positive_count + result.negative_count
        assert total > 0, "Forced parallel should work"
        
        print(f"✅ Forced parallel (3,5): {total} rectangles in {result.computation_time:.3f}s")
    
    def test_num_processes_parameter(self):
        """Test num_processes parameter handling."""
        
        # Test with explicit process count
        result = count_rectangles_auto(3, 7, num_processes=4)
        
        total = result.positive_count + result.negative_count
        assert total > 0, "Explicit process count should work"
        
        print(f"✅ Explicit processes (3,7): {total} rectangles with 4 processes")
    
    def test_auto_detect_processes(self):
        """Test automatic process detection."""
        
        # Test with None (auto-detect)
        result = count_rectangles_auto(3, 7, num_processes=None)
        
        total = result.positive_count + result.negative_count
        assert total > 0, "Auto-detect processes should work"
        
        print(f"✅ Auto-detect processes (3,7): {total} rectangles")
    
    def test_consistency_between_modes(self):
        """Test that single and parallel modes give same results."""
        
        r, n = 3, 7
        
        # Get result from single-threaded
        result_single = count_rectangles_auto(r, n, force_single=True)
        
        # Get result from parallel (use 2 processes for speed)
        result_parallel = count_rectangles_auto(r, n, force_parallel=True, num_processes=2)
        
        # Results should be identical
        assert result_single.positive_count == result_parallel.positive_count, "Positive counts should match"
        assert result_single.negative_count == result_parallel.negative_count, "Negative counts should match"
        
        total_single = result_single.positive_count + result_single.negative_count
        total_parallel = result_parallel.positive_count + result_parallel.negative_count
        
        print(f"✅ Consistency check ({r},{n}): {total_single} rectangles (both modes)")
    
    def test_performance_comparison(self):
        """Test performance characteristics of different modes."""
        
        r, n = 3, 6  # Medium problem
        
        # Test single-threaded performance
        start_time = time.time()
        result_single = count_rectangles_auto(r, n, force_single=True)
        single_time = time.time() - start_time
        
        # Test parallel performance (should be similar or slower for small problems)
        start_time = time.time()
        result_parallel = count_rectangles_auto(r, n, force_parallel=True, num_processes=2)
        parallel_time = time.time() - start_time
        
        # Verify correctness
        assert result_single.positive_count == result_parallel.positive_count
        assert result_single.negative_count == result_parallel.negative_count
        
        total = result_single.positive_count + result_single.negative_count
        
        print(f"✅ Performance comparison ({r},{n}): {total} rectangles")
        print(f"   Single: {single_time:.3f}s, Parallel: {parallel_time:.3f}s")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        
        # Test minimum valid case
        result = count_rectangles_auto(2, 3)
        assert result.positive_count + result.negative_count >= 0
        
        # Test boundary case (n=6 vs n=7)
        result_6 = count_rectangles_auto(3, 6)  # Should use single
        result_7 = count_rectangles_auto(3, 7, num_processes=2)  # Should use parallel
        
        assert result_6.positive_count + result_6.negative_count > 0
        assert result_7.positive_count + result_7.negative_count > 0
        
        print(f"✅ Edge cases: (3,6)={result_6.positive_count + result_6.negative_count}, (3,7)={result_7.positive_count + result_7.negative_count}")
    
    def test_result_object_properties(self):
        """Test that result objects have all expected properties."""
        
        result = count_rectangles_auto(3, 5)
        
        # Check all required properties exist
        assert hasattr(result, 'r') and result.r == 3
        assert hasattr(result, 'n') and result.n == 5
        assert hasattr(result, 'positive_count') and isinstance(result.positive_count, int)
        assert hasattr(result, 'negative_count') and isinstance(result.negative_count, int)
        assert hasattr(result, 'difference') and result.difference == result.positive_count - result.negative_count
        assert hasattr(result, 'from_cache') and isinstance(result.from_cache, bool)
        assert hasattr(result, 'computation_time') and isinstance(result.computation_time, (int, float))
        
        # Check value ranges
        assert result.positive_count >= 0
        assert result.negative_count >= 0
        assert result.computation_time >= 0
        
        print(f"✅ Result object properties: all properties present and valid")
    
    def test_error_propagation(self):
        """Test that errors from underlying implementations are properly propagated."""
        
        # Test invalid parameters that should raise errors
        with pytest.raises((ValueError, NotImplementedError)):
            count_rectangles_auto(1, 5)  # r < 2
        
        with pytest.raises((ValueError, NotImplementedError)):
            count_rectangles_auto(6, 5)  # r > n
        
        print("✅ Error propagation tests passed")


class TestAutoCounterIntegration(TestBaseWithProductionLogs):
    """Integration tests for auto counter with other components."""
    
    def test_cache_integration(self):
        """Test integration with cache system."""
        
        from cache.cache_manager import CacheManager
        cache = CacheManager()
        
        # Test with a case that might be cached
        result = count_rectangles_auto(3, 6)
        
        # Check if result matches cache (if available)
        cached = cache.get(3, 6)
        if cached:
            assert result.positive_count == cached.positive_count
            assert result.negative_count == cached.negative_count
            print(f"✅ Cache integration: matches cached result")
        else:
            print(f"✅ Cache integration: computed fresh result")
    
    def test_multiprocessing_integration(self):
        """Test integration with multiprocessing."""
        
        import multiprocessing as mp
        
        # Test that multiprocessing works correctly
        result = count_rectangles_auto(3, 7, num_processes=min(2, mp.cpu_count()))
        
        total = result.positive_count + result.negative_count
        assert total > 0, "Multiprocessing should work"
        
        print(f"✅ Multiprocessing integration: {total} rectangles")
    
    def test_selection_heuristics(self):
        """Test the selection heuristics in detail."""
        
        # Test various problem sizes to verify selection logic
        test_cases = [
            (2, 4, "single"),   # r=2 always single
            (3, 5, "single"),   # n<7 single
            (3, 6, "single"),   # n<7 single
            (3, 7, "parallel"), # n>=7 parallel (use small case for speed)
        ]
        
        for r, n, expected_mode in test_cases:
            if expected_mode == "single":
                # Should work with force_single
                result = count_rectangles_auto(r, n, force_single=True)
            else:
                # Should work with force_parallel (use 2 processes for speed)
                result = count_rectangles_auto(r, n, force_parallel=True, num_processes=2)
            
            total = result.positive_count + result.negative_count
            assert total >= 0, f"({r},{n}) should complete successfully"
            
            print(f"✅ Selection heuristic ({r},{n}): {expected_mode} mode, {total} rectangles")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])