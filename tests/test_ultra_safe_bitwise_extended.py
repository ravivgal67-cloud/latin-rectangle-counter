#!/usr/bin/env python3
"""
Extended tests for ultra_safe_bitwise module to improve coverage.

Tests the core ultra-safe bitwise algorithm implementation that currently has 24% coverage.
"""

import pytest
import time
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise
from tests.test_base import TestBaseWithProductionLogs


class TestUltraSafeBitwiseExtended(TestBaseWithProductionLogs):
    """Extended tests for ultra-safe bitwise implementation."""
    
    def test_parameter_validation(self):
        """Test parameter validation and error handling."""
        
        # Test r < 2
        with pytest.raises(ValueError, match="r must be >= 2"):
            count_rectangles_ultra_safe_bitwise(1, 5)
        
        # Test r > n
        with pytest.raises(ValueError, match="r must be <= n"):
            count_rectangles_ultra_safe_bitwise(6, 5)
        
        # Test r > 10 (implementation limit)
        with pytest.raises(NotImplementedError, match="only supports r <= 10"):
            count_rectangles_ultra_safe_bitwise(11, 15)
        
        print("✅ Parameter validation tests passed")
    
    def test_r2_cases_comprehensive(self):
        """Test r=2 cases comprehensively."""
        
        # Test various n values for r=2
        test_cases = [
            (2, 3, 2),    # Known: 2 derangements for n=3
            (2, 4, 9),    # Known: 9 derangements for n=4  
            (2, 5, 44),   # Known: 44 derangements for n=5
            (2, 6, 265),  # Known: 265 derangements for n=6
        ]
        
        for r, n, expected_total in test_cases:
            total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            assert total == expected_total, f"({r},{n}) total mismatch: got {total}, expected {expected_total}"
            assert positive + negative == total, f"({r},{n}) positive + negative != total"
            assert positive >= 0 and negative >= 0, f"({r},{n}) negative counts"
            
            print(f"✅ ({r},{n}): {total} rectangles (+{positive} -{negative})")
    
    def test_r3_cases_extended(self):
        """Test r=3 cases with various n values."""
        
        # Test cases where we can verify correctness
        test_cases = [
            (3, 4),   # Small case
            (3, 5),   # Medium case
            (3, 6),   # Larger case
        ]
        
        for r, n in test_cases:
            total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Basic sanity checks
            assert total > 0, f"({r},{n}) should have rectangles"
            assert positive + negative == total, f"({r},{n}) count mismatch"
            assert positive >= 0 and negative >= 0, f"({r},{n}) negative counts"
            
            # For r=3, we expect some positive and some negative rectangles
            assert positive > 0 and negative > 0, f"({r},{n}) should have both positive and negative"
            
            print(f"✅ ({r},{n}): {total} rectangles (+{positive} -{negative})")
    
    def test_performance_characteristics(self):
        """Test performance characteristics and timing."""
        
        # Test that small problems complete quickly
        start_time = time.time()
        total, positive, negative = count_rectangles_ultra_safe_bitwise(3, 5)
        elapsed = time.time() - start_time
        
        assert elapsed < 5.0, f"(3,5) took too long: {elapsed:.2f}s"
        assert total > 0, "Should find rectangles"
        
        print(f"✅ Performance test (3,5): {total} rectangles in {elapsed:.3f}s")
    
    def test_consistency_with_cache(self):
        """Test consistency with cached results."""
        
        from cache.cache_manager import CacheManager
        cache = CacheManager()
        
        # Test cases that should be in cache
        test_cases = [(3, 6), (4, 6), (5, 6)]
        
        for r, n in test_cases:
            cached = cache.get(r, n)
            if cached:
                # Compare with cached result
                total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
                
                cached_total = cached.positive_count + cached.negative_count
                
                assert total == cached_total, f"({r},{n}) total mismatch with cache: got {total}, cached {cached_total}"
                assert positive == cached.positive_count, f"({r},{n}) positive mismatch with cache"
                assert negative == cached.negative_count, f"({r},{n}) negative mismatch with cache"
                
                print(f"✅ ({r},{n}): Matches cache ({total} rectangles)")
            else:
                # Just verify it runs without error
                total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
                assert total > 0, f"({r},{n}) should have rectangles"
                print(f"✅ ({r},{n}): {total} rectangles (no cache)")
    
    def test_derangement_cache_integration(self):
        """Test integration with smart derangement cache."""
        
        # Test that the function properly uses the smart derangement cache
        from core.smart_derangement_cache import get_smart_derangement_cache
        
        n = 5
        cache = get_smart_derangement_cache(n)
        derangements = cache.get_all_derangements_with_signs()
        
        # For r=2, result should match derangement count
        total, positive, negative = count_rectangles_ultra_safe_bitwise(2, n)
        
        assert total == len(derangements), f"r=2 total should equal derangement count"
        
        # Verify signs match
        expected_positive = sum(1 for _, sign in derangements if sign > 0)
        expected_negative = len(derangements) - expected_positive
        
        assert positive == expected_positive, f"Positive count mismatch: got {positive}, expected {expected_positive}"
        assert negative == expected_negative, f"Negative count mismatch: got {negative}, expected {expected_negative}"
        
        print(f"✅ Derangement cache integration: {total} derangements (+{positive} -{negative})")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        
        # Test minimum valid case - (2,2) has 1 derangement: [2,1]
        total, positive, negative = count_rectangles_ultra_safe_bitwise(2, 2)
        assert total == 1, "2x2 should have 1 rectangle from derangement [2,1]"
        assert positive == 0 and negative == 1, "2x2 rectangle should have negative sign"
        
        # Test r = n case
        total, positive, negative = count_rectangles_ultra_safe_bitwise(4, 4)
        assert total > 0, "4x4 should have rectangles"
        assert positive + negative == total, "Count consistency"
        
        print(f"✅ Edge cases: (2,2)={total}, (4,4)={positive + negative}")
    
    def test_deterministic_results(self):
        """Test that results are deterministic across multiple runs."""
        
        r, n = 3, 5
        
        # Run multiple times
        results = []
        for _ in range(3):
            total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
            results.append((total, positive, negative))
        
        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, f"Run {i+1} differs from run 1: {result} vs {first_result}"
        
        print(f"✅ Deterministic results: {first_result} across 3 runs")
    
    def test_bitwise_operations_coverage(self):
        """Test to trigger bitwise operations code paths."""
        
        # Test cases that should trigger different code paths
        test_cases = [
            (3, 4),  # Small case - should use explicit loops
            (3, 6),  # Medium case - should use bitwise operations
            (4, 5),  # Different r value
        ]
        
        for r, n in test_cases:
            total, positive, negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Verify basic properties
            assert total > 0, f"({r},{n}) should have rectangles"
            assert positive + negative == total, f"({r},{n}) count consistency"
            
            # For r >= 3, should have both positive and negative
            if r >= 3:
                assert positive > 0 and negative > 0, f"({r},{n}) should have mixed signs"
            
            print(f"✅ Bitwise operations ({r},{n}): {total} rectangles")


class TestUltraSafeBitwiseIntegration(TestBaseWithProductionLogs):
    """Integration tests for ultra-safe bitwise with other components."""
    
    def test_smart_cache_compatibility(self):
        """Test compatibility with smart derangement cache."""
        
        # Test that function works with different cache states
        from core.smart_derangement_cache import get_smart_derangement_cache
        
        n = 6
        cache = get_smart_derangement_cache(n)
        
        # Verify cache is loaded
        assert cache is not None
        derangements = cache.get_all_derangements_with_signs()
        assert len(derangements) > 0
        
        # Test computation uses cache correctly
        total, positive, negative = count_rectangles_ultra_safe_bitwise(3, n)
        
        assert total > 0, "Should compute rectangles"
        print(f"✅ Smart cache compatibility: {total} rectangles for (3,{n})")
    
    def test_memory_efficiency(self):
        """Test memory efficiency for larger problems."""
        
        import psutil
        import os
        
        # Get memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run computation
        total, positive, negative = count_rectangles_ultra_safe_bitwise(4, 6)
        
        # Get memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_used = mem_after - mem_before
        
        # Should not use excessive memory (less than 100MB for this problem)
        assert mem_used < 100, f"Excessive memory usage: {mem_used:.1f} MB"
        
        print(f"✅ Memory efficiency: {mem_used:.1f} MB for {total} rectangles")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])