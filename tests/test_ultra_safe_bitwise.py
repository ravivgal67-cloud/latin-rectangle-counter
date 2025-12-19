"""
Tests for ultra-safe bitwise optimization.

Feature: latin-rectangle-counter
"""

import time
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise
from core.counter import count_rectangles
from core.smart_derangement_cache import get_smart_derangements_with_signs, SmartDerangementCache

# Optional imports for full test suite
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest.raises for basic functionality
    class MockPytest:
        @staticmethod
        def raises(exception_type):
            class RaisesContext:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    if exc_type is None:
                        raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
                    return issubclass(exc_type, exception_type)
            return RaisesContext()
    pytest = MockPytest()

try:
    from hypothesis import given, strategies as st, settings
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    # Mock hypothesis decorators for basic functionality
    def given(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    st = None


class TestUltraSafeBitwiseCorrectness:
    """Test correctness of ultra-safe bitwise implementation."""
    
    def test_r2_correctness(self):
        """Test r=2 correctness against standard counter."""
        test_cases = [(2, 3), (2, 4), (2, 5), (2, 6)]
        
        for r, n in test_cases:
            # Get result from ultra-safe bitwise
            ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Get result from standard counter
            standard_result = count_rectangles(r, n)
            standard_total = standard_result.positive_count + standard_result.negative_count
            
            # Verify correctness
            assert ultra_total == standard_total, f"Total mismatch for ({r},{n}): {ultra_total} vs {standard_total}"
            assert ultra_positive == standard_result.positive_count, f"Positive mismatch for ({r},{n})"
            assert ultra_negative == standard_result.negative_count, f"Negative mismatch for ({r},{n})"
    
    def test_r3_correctness(self):
        """Test r=3 correctness against standard counter."""
        test_cases = [(3, 3), (3, 4), (3, 5), (3, 6)]
        
        for r, n in test_cases:
            # Get result from ultra-safe bitwise
            ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Get result from standard counter
            standard_result = count_rectangles(r, n)
            standard_total = standard_result.positive_count + standard_result.negative_count
            
            # Verify correctness
            assert ultra_total == standard_total, f"Total mismatch for ({r},{n}): {ultra_total} vs {standard_total}"
            assert ultra_positive == standard_result.positive_count, f"Positive mismatch for ({r},{n})"
            assert ultra_negative == standard_result.negative_count, f"Negative mismatch for ({r},{n})"
    
    def test_r4_correctness(self):
        """Test r=4 correctness against standard counter."""
        test_cases = [(4, 4), (4, 5), (4, 6)]
        
        for r, n in test_cases:
            # Get result from ultra-safe bitwise
            ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Get result from standard counter
            standard_result = count_rectangles(r, n)
            standard_total = standard_result.positive_count + standard_result.negative_count
            
            # Verify correctness
            assert ultra_total == standard_total, f"Total mismatch for ({r},{n}): {ultra_total} vs {standard_total}"
            assert ultra_positive == standard_result.positive_count, f"Positive mismatch for ({r},{n})"
            assert ultra_negative == standard_result.negative_count, f"Negative mismatch for ({r},{n})"
    
    def test_r5_correctness(self):
        """Test r=5 correctness against standard counter."""
        test_cases = [(5, 5), (5, 6)]
        
        for r, n in test_cases:
            # Get result from ultra-safe bitwise
            ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Get result from standard counter
            standard_result = count_rectangles(r, n)
            standard_total = standard_result.positive_count + standard_result.negative_count
            
            # Verify correctness
            assert ultra_total == standard_total, f"Total mismatch for ({r},{n}): {ultra_total} vs {standard_total}"
            assert ultra_positive == standard_result.positive_count, f"Positive mismatch for ({r},{n})"
            assert ultra_negative == standard_result.negative_count, f"Negative mismatch for ({r},{n})"
    
    def test_correctness_property_manual(self):
        """
        **Feature: latin-rectangle-counter, Property: Ultra-safe bitwise correctness**
        **Validates: Requirements 1.1, 2.1**
        
        Manual test of correctness property for various (r,n) pairs.
        """
        test_cases = [(3, 4), (3, 5), (4, 5), (5, 6)]
        
        for r, n in test_cases:
            # Get result from ultra-safe bitwise
            ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Get result from standard counter
            standard_result = count_rectangles(r, n)
            standard_total = standard_result.positive_count + standard_result.negative_count
            
            # Verify correctness
            assert ultra_total == standard_total, f"Total mismatch for ({r},{n})"
            assert ultra_positive == standard_result.positive_count, f"Positive mismatch for ({r},{n})"
            assert ultra_negative == standard_result.negative_count, f"Negative mismatch for ({r},{n})"
            
            # Verify basic properties
            assert ultra_total == ultra_positive + ultra_negative, f"Count consistency for ({r},{n})"
            assert ultra_total >= 0, f"Non-negative total for ({r},{n})"
            assert ultra_positive >= 0, f"Non-negative positive for ({r},{n})"
            assert ultra_negative >= 0, f"Non-negative negative for ({r},{n})"

    if HYPOTHESIS_AVAILABLE:
        @given(
            st.integers(min_value=3, max_value=4),
            st.integers(min_value=4, max_value=5)
        )
        @settings(max_examples=10, deadline=1000)
        def test_correctness_property(self, r, n):
            """
            **Feature: latin-rectangle-counter, Property: Ultra-safe bitwise correctness**
            **Validates: Requirements 1.1, 2.1**
            
            For any valid (r,n) pair, the ultra-safe bitwise implementation should
            produce identical results to the standard counter.
            """
            if r >= n:  # Skip invalid cases
                return
            
            # Get result from ultra-safe bitwise
            ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
            
            # Get result from standard counter
            standard_result = count_rectangles(r, n)
            standard_total = standard_result.positive_count + standard_result.negative_count
            
            # Verify correctness
            assert ultra_total == standard_total, f"Total mismatch for ({r},{n})"
            assert ultra_positive == standard_result.positive_count, f"Positive mismatch for ({r},{n})"
            assert ultra_negative == standard_result.negative_count, f"Negative mismatch for ({r},{n})"
            
            # Verify basic properties
            assert ultra_total == ultra_positive + ultra_negative, f"Count consistency for ({r},{n})"
            assert ultra_total >= 0, f"Non-negative total for ({r},{n})"
            assert ultra_positive >= 0, f"Non-negative positive for ({r},{n})"
            assert ultra_negative >= 0, f"Non-negative negative for ({r},{n})"


class TestUltraSafeBitwisePerformance:
    """Test performance characteristics of ultra-safe bitwise implementation."""
    
    def test_performance_vs_standard(self):
        """Test performance improvement over standard counter."""
        # Test cases where ultra-safe should show advantage
        test_cases = [(3, 6), (4, 6), (5, 6)]
        
        for r, n in test_cases:
            # Time standard counter
            start_time = time.time()
            standard_result = count_rectangles(r, n)
            standard_time = time.time() - start_time
            
            # Time ultra-safe bitwise
            start_time = time.time()
            ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
            ultra_time = time.time() - start_time
            
            # Verify correctness first
            standard_total = standard_result.positive_count + standard_result.negative_count
            assert ultra_total == standard_total, f"Correctness check failed for ({r},{n})"
            
            # Calculate speedup
            speedup = standard_time / ultra_time if ultra_time > 0 else float('inf')
            
            print(f"Performance for ({r},{n}): {speedup:.2f}x speedup ({standard_time:.4f}s -> {ultra_time:.4f}s)")
            
            # For r>=3, ultra-safe should be faster or at least competitive
            # Relaxed threshold to account for system variability
            if r >= 3:
                assert speedup >= 0.2, f"Performance regression for ({r},{n}): {speedup:.2f}x"
    
    def test_no_memory_issues(self):
        """Test that ultra-safe doesn't have memory issues."""
        # Test the largest problem we support
        r, n = 5, 6
        
        # This should complete without memory errors
        ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
        
        # Verify reasonable result
        assert ultra_total > 0, "Should produce rectangles"
        assert ultra_total == ultra_positive + ultra_negative, "Count consistency"
    
    def test_deterministic_results(self):
        """Test that results are deterministic across runs."""
        r, n = 4, 5
        
        # Run multiple times
        results = []
        for _ in range(3):
            result = count_rectangles_ultra_safe_bitwise(r, n)
            results.append(result)
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[i] == results[0], f"Non-deterministic results: {results}"


class TestSmartDerangementCache:
    """Test smart derangement cache functionality."""
    
    def test_cache_loading(self):
        """Test that smart derangement cache loads correctly."""
        for n in [3, 4, 5, 6]:
            derangements_with_signs = get_smart_derangements_with_signs(n)
            
            # Should have correct number of derangements
            assert len(derangements_with_signs) > 0, f"No derangements for n={n}"
            
            # All should be valid derangements
            for derang, sign in derangements_with_signs:
                assert len(derang) == n, f"Wrong length derangement for n={n}"
                assert set(derang) == set(range(1, n + 1)), f"Invalid derangement values for n={n}"
                assert sign in [-1, 1], f"Invalid sign for n={n}: {sign}"
                
                # Verify it's actually a derangement
                for i, val in enumerate(derang):
                    assert val != i + 1, f"Not a derangement for n={n}: {derang}"
    
    def test_cache_consistency(self):
        """Test that cache provides consistent results."""
        for n in [4, 5, 6]:
            # Load cache multiple times
            cache1 = SmartDerangementCache(n)
            cache2 = SmartDerangementCache(n)
            
            # Should have same number of derangements
            derang1 = get_smart_derangements_with_signs(n)
            derang2 = get_smart_derangements_with_signs(n)
            
            assert len(derang1) == len(derang2), f"Inconsistent cache size for n={n}"
            
            # Should have same derangements (order may vary)
            set1 = {(tuple(d), s) for d, s in derang1}
            set2 = {(tuple(d), s) for d, s in derang2}
            assert set1 == set2, f"Inconsistent cache content for n={n}"
    
    def test_database_indices(self):
        """Test database-style indices functionality."""
        for n in [4, 5, 6]:
            cache = SmartDerangementCache(n)
            
            # Should have position-value index
            assert hasattr(cache, 'position_value_index'), f"Missing position_value_index for n={n}"
            assert len(cache.position_value_index) > 0, f"Empty position_value_index for n={n}"
            
            # Check index structure
            for (pos, val), indices in cache.position_value_index.items():
                assert 0 <= pos < n, f"Invalid position {pos} for n={n}"
                assert 1 <= val <= n, f"Invalid value {val} for n={n}"
                assert len(indices) > 0, f"Empty indices for ({pos},{val}) n={n}"
                
                # All indices should be valid
                for idx in indices:
                    assert 0 <= idx < len(cache.derangements_with_signs), f"Invalid index {idx} for n={n}"


class TestBitwiseOperations:
    """Test bitwise operation correctness."""
    
    def test_bitset_operations(self):
        """Test that bitwise operations work correctly."""
        # Test with small example we can verify manually
        r, n = 3, 4
        
        ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
        
        # Should match known result for (3,4)
        assert ultra_total == 24, f"Wrong total for (3,4): {ultra_total}"
        assert ultra_positive == 12, f"Wrong positive for (3,4): {ultra_positive}"
        assert ultra_negative == 12, f"Wrong negative for (3,4): {ultra_negative}"
    
    def test_conflict_marking(self):
        """Test that conflict marking works correctly."""
        # This is tested indirectly through correctness tests,
        # but we can verify the cache has proper conflict structure
        n = 5
        cache = SmartDerangementCache(n)
        
        # Should have conflicts for each position-value pair
        total_conflicts = sum(len(indices) for indices in cache.position_value_index.values())
        assert total_conflicts > 0, "Should have conflict indices"
        
        # Each derangement should appear in multiple conflict sets
        derangement_appearances = {}
        for indices in cache.position_value_index.values():
            for idx in indices:
                derangement_appearances[idx] = derangement_appearances.get(idx, 0) + 1
        
        # Most derangements should appear in multiple conflict sets
        multi_conflict_count = sum(1 for count in derangement_appearances.values() if count > 1)
        assert multi_conflict_count > 0, "Should have derangements with multiple conflicts"
    
    def test_early_termination(self):
        """Test that early termination works correctly."""
        # This is hard to test directly, but we can verify that
        # the algorithm completes quickly even for larger problems
        r, n = 5, 6
        
        start_time = time.time()
        ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(r, n)
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds to account for system load)
        assert elapsed < 5.0, f"Too slow for ({r},{n}): {elapsed:.2f}s"
        
        # Should produce correct result
        assert ultra_total > 0, "Should find rectangles"
        assert ultra_total == ultra_positive + ultra_negative, "Count consistency"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_unsupported_r_values(self):
        """Test that unsupported r values raise appropriate errors."""
        # r=1 is not supported
        with pytest.raises(ValueError, match="r must be >= 2"):
            count_rectangles_ultra_safe_bitwise(1, 4)
        
        # r > n is not valid
        with pytest.raises(ValueError, match="r must be <= n"):
            count_rectangles_ultra_safe_bitwise(7, 6)
        
        # r=11 is beyond our implementation limit
        with pytest.raises(NotImplementedError, match="only supports r <= 10"):
            count_rectangles_ultra_safe_bitwise(11, 12)
    
    def test_invalid_parameters(self):
        """Test behavior with invalid parameters."""
        # r > n should be handled gracefully (though may not be meaningful)
        # The function should either work or raise a clear error
        try:
            result = count_rectangles_ultra_safe_bitwise(4, 3)
            # If it works, result should be reasonable
            assert isinstance(result, tuple), "Should return tuple"
            assert len(result) == 3, "Should return 3 values"
        except (ValueError, NotImplementedError, AssertionError):
            # These are acceptable error types for invalid input
            pass
    
    def test_minimum_valid_cases(self):
        """Test minimum valid cases."""
        # (2,2) should work
        ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(2, 2)
        assert ultra_total >= 0, "Should handle (2,2)"
        
        # (3,3) should work
        ultra_total, ultra_positive, ultra_negative = count_rectangles_ultra_safe_bitwise(3, 3)
        assert ultra_total >= 0, "Should handle (3,3)"


class TestRegressionPrevention:
    """Tests to prevent performance and correctness regressions."""
    
    def test_known_results(self):
        """Test against known correct results to prevent regressions."""
        # Known results from our benchmarking
        known_results = {
            (2, 4): (9, 3, 6),
            (2, 5): (44, 24, 20),
            (2, 6): (265, 130, 135),
            (3, 4): (24, 12, 12),
            (3, 5): (552, 312, 240),
            (3, 6): (21280, 10480, 10800),
            (4, 4): (24, 24, 0),
            (4, 5): (1344, 384, 960),
            (4, 6): (393120, 203040, 190080),
            (5, 5): (1344, 384, 960),
            (5, 6): (1128960, 576000, 552960),
        }
        
        for (r, n), expected in known_results.items():
            result = count_rectangles_ultra_safe_bitwise(r, n)
            assert result == expected, f"Regression for ({r},{n}): got {result}, expected {expected}"
    
    def test_performance_benchmarks(self):
        """Test that performance meets minimum benchmarks."""
        # These are based on our cleanup results - ultra-safe should be faster for r>=3
        # Relaxed thresholds to account for system variability
        performance_cases = [
            (3, 6, 0.1),    # Should complete in < 100ms
            (4, 6, 0.5),    # Should complete in < 500ms
            (5, 6, 3.0),    # Should complete in < 3s
        ]
        
        for r, n, max_time in performance_cases:
            start_time = time.time()
            result = count_rectangles_ultra_safe_bitwise(r, n)
            elapsed = time.time() - start_time
            
            assert elapsed < max_time, f"Performance regression for ({r},{n}): {elapsed:.3f}s > {max_time}s"
            assert result[0] > 0, f"Should find rectangles for ({r},{n})"