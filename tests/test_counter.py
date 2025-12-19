"""
Property-based tests for counter module.

Feature: latin-rectangle-counter
"""

import pytest
from hypothesis import given, strategies as st, settings
from itertools import permutations
from core.counter import count_nlr_r2, CountResult
from core.permutation import is_derangement, permutation_sign


class TestCountNLRR2:
    """Tests for r=2 counting accuracy."""
    
    @given(st.integers(min_value=2, max_value=8))
    @settings(max_examples=100, deadline=1000)
    def test_count_accuracy_r2(self, n):
        """
        **Feature: latin-rectangle-counter, Property 10: Count accuracy (r=2 case)**
        **Validates: Requirements 4.1**
        
        For any small n where exhaustive verification is feasible,
        the positive and negative counts should match the actual number
        of rectangles with each sign.
        
        For r=2, we can verify by:
        1. Generating all derangements of [1, 2, ..., n]
        2. Computing the sign of each derangement
        3. Counting positive and negative signs
        """
        # Get the computed result
        result = count_nlr_r2(n)
        
        # Verify by brute force for small n
        # Generate all permutations and filter derangements
        all_perms = list(permutations(range(1, n + 1)))
        derangements = [list(perm) for perm in all_perms if is_derangement(list(perm))]
        
        # Count positive and negative derangements
        positive_actual = 0
        negative_actual = 0
        
        for derang in derangements:
            sign = permutation_sign(derang)
            if sign == 1:
                positive_actual += 1
            else:
                negative_actual += 1
        
        # Verify counts match
        assert result.positive_count == positive_actual, (
            f"Positive count mismatch for n={n}: "
            f"computed {result.positive_count}, actual {positive_actual}"
        )
        
        assert result.negative_count == negative_actual, (
            f"Negative count mismatch for n={n}: "
            f"computed {result.negative_count}, actual {negative_actual}"
        )
    
    def test_known_r2_values(self):
        """Test against verified values for r=2."""
        # NLR(2, 2): 0 positive, 1 negative (difference: -1)
        result = count_nlr_r2(2)
        assert result.positive_count == 0
        assert result.negative_count == 1
        assert result.difference == -1
        
        # NLR(2, 3): 2 positive, 0 negative (difference: 2)
        result = count_nlr_r2(3)
        assert result.positive_count == 2
        assert result.negative_count == 0
        assert result.difference == 2
        
        # NLR(2, 4): 3 positive, 6 negative (difference: -3)
        result = count_nlr_r2(4)
        assert result.positive_count == 3
        assert result.negative_count == 6
        assert result.difference == -3


class TestDifferenceCalculation:
    """Tests for difference calculation property."""
    
    @given(st.integers(min_value=2, max_value=8))
    @settings(max_examples=100, deadline=None)
    def test_difference_calculation(self, n):
        """
        **Feature: latin-rectangle-counter, Property 11: Difference calculation**
        **Validates: Requirements 4.2**
        
        For any count result, the difference field should equal
        positive_count - negative_count.
        """
        result = count_nlr_r2(n)
        
        expected_difference = result.positive_count - result.negative_count
        
        assert result.difference == expected_difference, (
            f"Difference calculation incorrect for n={n}: "
            f"difference={result.difference}, "
            f"positive={result.positive_count}, negative={result.negative_count}, "
            f"expected difference={expected_difference}"
        )
    
    def test_difference_with_known_values(self):
        """Test difference calculation with known values."""
        # n=2: 0 positive, 1 negative -> difference = -1
        result = count_nlr_r2(2)
        assert result.difference == result.positive_count - result.negative_count
        assert result.difference == -1
        
        # n=3: 2 positive, 0 negative -> difference = 2
        result = count_nlr_r2(3)
        assert result.difference == result.positive_count - result.negative_count
        assert result.difference == 2
        
        # n=4: 3 positive, 6 negative -> difference = -3
        result = count_nlr_r2(4)
        assert result.difference == result.positive_count - result.negative_count
        assert result.difference == -3



class TestCountAccuracy:
    """Tests for general count accuracy property."""
    
    @given(
        st.integers(min_value=2, max_value=5).flatmap(
            lambda n: st.tuples(st.just(n), st.integers(min_value=2, max_value=n))
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_count_accuracy_general(self, dims):
        """
        **Feature: latin-rectangle-counter, Property 10: Count accuracy**
        **Validates: Requirements 4.1**
        
        For any small dimensions (r, n) where exhaustive verification is feasible,
        the positive and negative counts should match the actual number of
        rectangles with each sign.
        
        We verify by:
        1. Using the count_rectangles function to get computed counts
        2. Generating all rectangles explicitly and classifying by sign
        3. Comparing the counts
        """
        from core.counter import count_rectangles
        from core.latin_rectangle import generate_normalized_rectangles
        
        n, r = dims
        
        # Get the computed result
        result = count_rectangles(r, n)
        
        # Verify by brute force: generate all rectangles and count by sign
        positive_actual = 0
        negative_actual = 0
        
        for rectangle in generate_normalized_rectangles(r, n):
            sign = rectangle.compute_sign()
            if sign == 1:
                positive_actual += 1
            else:
                negative_actual += 1
        
        # Verify counts match
        assert result.positive_count == positive_actual, (
            f"Positive count mismatch for r={r}, n={n}: "
            f"computed {result.positive_count}, actual {positive_actual}"
        )
        
        assert result.negative_count == negative_actual, (
            f"Negative count mismatch for r={r}, n={n}: "
            f"computed {result.negative_count}, actual {negative_actual}"
        )
        
        # Also verify difference
        assert result.difference == positive_actual - negative_actual
    
    def test_known_values_various_dimensions(self):
        """Test against known values for various dimensions."""
        from core.counter import count_rectangles
        
        # r=2, n=2: 0 positive, 1 negative
        result = count_rectangles(2, 2)
        assert result.positive_count == 0
        assert result.negative_count == 1
        
        # r=2, n=3: 2 positive, 0 negative
        result = count_rectangles(2, 3)
        assert result.positive_count == 2
        assert result.negative_count == 0
        
        # r=2, n=4: 3 positive, 6 negative
        result = count_rectangles(2, 4)
        assert result.positive_count == 3
        assert result.negative_count == 6
        
        # r=3, n=3: Should have 2 total rectangles
        result = count_rectangles(3, 3)
        total = result.positive_count + result.negative_count
        assert total == 2


class TestCacheFlagAccuracy:
    """Tests for cache flag accuracy property."""
    
    @given(
        st.integers(min_value=2, max_value=4).flatmap(
            lambda n: st.tuples(st.just(n), st.integers(min_value=2, max_value=n))
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_cache_flag_accuracy(self, dims):
        """
        **Feature: latin-rectangle-counter, Property 15: Cache flag accuracy**
        **Validates: Requirements 6.5**
        
        For any result returned to the user, the from_cache flag should be true
        if and only if the result was retrieved from cache rather than computed.
        
        We verify by:
        1. Computing a result without cache (should have from_cache=False)
        2. Computing the same result with cache (first time, should have from_cache=False)
        3. Computing the same result with cache again (should have from_cache=True)
        """
        from core.counter import count_rectangles
        from cache.cache_manager import CacheManager
        
        n, r = dims
        
        # Test 1: Compute without cache
        result_no_cache = count_rectangles(r, n, cache_manager=None)
        assert result_no_cache.from_cache is False, (
            f"Result without cache should have from_cache=False for r={r}, n={n}"
        )
        
        # Test 2: Compute with fresh cache (first time)
        cache = CacheManager(":memory:")
        result_first_time = count_rectangles(r, n, cache_manager=cache)
        assert result_first_time.from_cache is False, (
            f"First computation with cache should have from_cache=False for r={r}, n={n}"
        )
        
        # Test 3: Compute with cache again (should be cached now)
        result_cached = count_rectangles(r, n, cache_manager=cache)
        assert result_cached.from_cache is True, (
            f"Second computation with cache should have from_cache=True for r={r}, n={n}"
        )
        
        # Verify the cached result has the same counts
        assert result_cached.positive_count == result_first_time.positive_count
        assert result_cached.negative_count == result_first_time.negative_count
        assert result_cached.difference == result_first_time.difference
        
        cache.close()
    
    def test_cache_flag_with_count_for_n(self):
        """Test cache flag accuracy with count_for_n function."""
        from core.counter import count_for_n
        from cache.cache_manager import CacheManager
        
        n = 3
        
        # First computation with cache
        cache = CacheManager(":memory:")
        results_first = count_for_n(n, cache_manager=cache)
        
        # All results should have from_cache=False
        for result in results_first:
            assert result.from_cache is False, (
                f"First computation should have from_cache=False for r={result.r}, n={result.n}"
            )
        
        # Second computation with cache
        results_second = count_for_n(n, cache_manager=cache)
        
        # All results should have from_cache=True
        for result in results_second:
            assert result.from_cache is True, (
                f"Second computation should have from_cache=True for r={result.r}, n={result.n}"
            )
        
        cache.close()
    
    def test_cache_flag_with_count_range(self):
        """Test cache flag accuracy with count_range function."""
        from core.counter import count_range
        from cache.cache_manager import CacheManager
        
        # First computation with cache
        cache = CacheManager(":memory:")
        results_first = count_range(2, 3, cache_manager=cache)
        
        # All results should have from_cache=False
        for result in results_first:
            assert result.from_cache is False, (
                f"First computation should have from_cache=False for r={result.r}, n={result.n}"
            )
        
        # Second computation with cache
        results_second = count_range(2, 3, cache_manager=cache)
        
        # All results should have from_cache=True
        for result in results_second:
            assert result.from_cache is True, (
                f"Second computation should have from_cache=True for r={result.r}, n={result.n}"
            )
        
        cache.close()
    
    def test_partial_cache_flag_accuracy(self):
        """Test cache flag accuracy with partial cache."""
        from core.counter import count_range
        from cache.cache_manager import CacheManager
        
        cache = CacheManager(":memory:")
        
        # Pre-populate cache with some results
        # Compute for n=2 (will cache r=2, n=2)
        count_range(2, 2, cache_manager=cache)
        
        # Now compute for range 2..3
        # This should have:
        # - (2, 2): from_cache=True (already cached)
        # - (2, 3): from_cache=False (new computation)
        # - (3, 3): from_cache=False (new computation)
        results = count_range(2, 3, cache_manager=cache)
        
        # Find each result and check its flag
        result_2_2 = next(r for r in results if r.r == 2 and r.n == 2)
        result_2_3 = next(r for r in results if r.r == 2 and r.n == 3)
        result_3_3 = next(r for r in results if r.r == 3 and r.n == 3)
        
        assert result_2_2.from_cache is True, "Result (2,2) should be from cache"
        assert result_2_3.from_cache is False, "Result (2,3) should not be from cache"
        assert result_3_3.from_cache is False, "Result (3,3) should not be from cache"
        
        cache.close()


class TestCompleteRangeCoverage:
    """Tests for complete range coverage properties."""
    
    @given(st.integers(min_value=2, max_value=5))
    @settings(max_examples=50, deadline=None)
    def test_complete_range_coverage_single_n(self, n):
        """
        **Feature: latin-rectangle-counter, Property 3: Complete range coverage for single n**
        **Validates: Requirements 1.2**
        
        For any valid n >= 2, when counting for just n, the results should
        include entries for all r where 2 <= r <= n.
        """
        from core.counter import count_for_n
        
        results = count_for_n(n)
        
        # Verify we have the correct number of results
        expected_count = n - 1  # r ranges from 2 to n, so n-1 values
        assert len(results) == expected_count, (
            f"Expected {expected_count} results for n={n}, got {len(results)}"
        )
        
        # Verify all r values from 2 to n are present
        r_values = [result.r for result in results]
        expected_r_values = list(range(2, n + 1))
        
        assert r_values == expected_r_values, (
            f"Missing or incorrect r values for n={n}: "
            f"expected {expected_r_values}, got {r_values}"
        )
        
        # Verify all results have the correct n value
        for result in results:
            assert result.n == n, (
                f"Result has incorrect n value: expected {n}, got {result.n}"
            )
    
    @given(
        st.integers(min_value=2, max_value=4).flatmap(
            lambda n1: st.tuples(st.just(n1), st.integers(min_value=n1, max_value=4))
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_complete_range_coverage_n_range(self, range_spec):
        """
        **Feature: latin-rectangle-counter, Property 4: Complete range coverage for n range**
        **Validates: Requirements 1.3**
        
        For any valid range n1..n2 where 2 <= n1 <= n2, the results should
        include entries for all n where n1 <= n <= n2 and for all r where 2 <= r <= n.
        """
        from core.counter import count_range
        
        n_start, n_end = range_spec
        
        results = count_range(n_start, n_end)
        
        # Calculate expected number of results
        # For each n from n_start to n_end, we have (n-1) values of r
        expected_count = sum(n - 1 for n in range(n_start, n_end + 1))
        
        assert len(results) == expected_count, (
            f"Expected {expected_count} results for range {n_start}..{n_end}, "
            f"got {len(results)}"
        )
        
        # Verify all (r, n) combinations are present
        result_pairs = [(result.r, result.n) for result in results]
        expected_pairs = [
            (r, n)
            for n in range(n_start, n_end + 1)
            for r in range(2, n + 1)
        ]
        
        assert result_pairs == expected_pairs, (
            f"Missing or incorrect (r, n) pairs for range {n_start}..{n_end}: "
            f"expected {expected_pairs}, got {result_pairs}"
        )
    
    def test_single_n_examples(self):
        """Test count_for_n with specific examples."""
        from core.counter import count_for_n
        
        # n=2: should have results for r=2
        results = count_for_n(2)
        assert len(results) == 1
        assert results[0].r == 2
        assert results[0].n == 2
        
        # n=3: should have results for r=2, r=3
        results = count_for_n(3)
        assert len(results) == 2
        assert results[0].r == 2
        assert results[0].n == 3
        assert results[1].r == 3
        assert results[1].n == 3
        
        # n=4: should have results for r=2, r=3, r=4
        results = count_for_n(4)
        assert len(results) == 3
        assert [r.r for r in results] == [2, 3, 4]
        assert all(r.n == 4 for r in results)
    
    def test_range_examples(self):
        """Test count_range with specific examples."""
        from core.counter import count_range
        
        # Range 2..2: should have results for (2,2)
        results = count_range(2, 2)
        assert len(results) == 1
        assert results[0].r == 2
        assert results[0].n == 2
        
        # Range 2..3: should have results for (2,2), (2,3), (3,3)
        results = count_range(2, 3)
        assert len(results) == 3
        pairs = [(r.r, r.n) for r in results]
        assert pairs == [(2, 2), (2, 3), (3, 3)]
        
        # Range 3..4: should have results for (2,3), (3,3), (2,4), (3,4), (4,4)
        results = count_range(3, 4)
        assert len(results) == 5
        pairs = [(r.r, r.n) for r in results]
        assert pairs == [(2, 3), (3, 3), (2, 4), (3, 4), (4, 4)]
