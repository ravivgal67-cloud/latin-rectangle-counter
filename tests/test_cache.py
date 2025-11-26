"""
Property-based tests for cache module.

Feature: latin-rectangle-counter
"""

import pytest
import tempfile
import os
from hypothesis import given, strategies as st, settings
from cache import CacheManager
from core.counter import CountResult, count_rectangles


class TestCacheRetrievalConsistency:
    """Tests for cache retrieval consistency property."""
    
    @given(
        st.integers(min_value=2, max_value=4).flatmap(
            lambda n: st.tuples(st.just(n), st.integers(min_value=2, max_value=n))
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_cache_retrieval_consistency(self, dims):
        """
        **Feature: latin-rectangle-counter, Property 12: Cache retrieval consistency**
        **Validates: Requirements 5.1, 5.2**
        
        For any dimensions (r, n), if results are computed and then requested again,
        the second request should return cached results that match the original computation.
        """
        n, r = dims
        
        # Use a temporary database for this test
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # Create cache manager
            cache = CacheManager(db_path)
            
            # Compute the result
            original_result = count_rectangles(r, n)
            
            # Store in cache
            cache.put(original_result)
            
            # Retrieve from cache
            cached_result = cache.get(r, n)
            
            # Verify cached result exists
            assert cached_result is not None, (
                f"Cache returned None for dimensions r={r}, n={n} after storing"
            )
            
            # Verify cached result matches original
            assert cached_result.r == original_result.r, (
                f"Cached r mismatch: expected {original_result.r}, got {cached_result.r}"
            )
            assert cached_result.n == original_result.n, (
                f"Cached n mismatch: expected {original_result.n}, got {cached_result.n}"
            )
            assert cached_result.positive_count == original_result.positive_count, (
                f"Cached positive_count mismatch for r={r}, n={n}: "
                f"expected {original_result.positive_count}, got {cached_result.positive_count}"
            )
            assert cached_result.negative_count == original_result.negative_count, (
                f"Cached negative_count mismatch for r={r}, n={n}: "
                f"expected {original_result.negative_count}, got {cached_result.negative_count}"
            )
            assert cached_result.difference == original_result.difference, (
                f"Cached difference mismatch for r={r}, n={n}: "
                f"expected {original_result.difference}, got {cached_result.difference}"
            )
            
            # Verify from_cache flag is set correctly
            assert cached_result.from_cache is True, (
                f"from_cache flag should be True for cached result"
            )
            
            cache.close()
        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_cache_miss_returns_none(self):
        """Test that cache returns None for dimensions not in cache."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            
            # Try to get a result that doesn't exist
            result = cache.get(2, 3)
            
            assert result is None, "Cache should return None for cache miss"
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_cache_persistence(self):
        """Test that cache persists across manager instances."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # Store a result with first cache manager
            cache1 = CacheManager(db_path)
            original_result = count_rectangles(2, 3)
            cache1.put(original_result)
            cache1.close()
            
            # Retrieve with a new cache manager
            cache2 = CacheManager(db_path)
            cached_result = cache2.get(2, 3)
            
            assert cached_result is not None
            assert cached_result.positive_count == original_result.positive_count
            assert cached_result.negative_count == original_result.negative_count
            
            cache2.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestCacheStorage:
    """Tests for cache storage property."""
    
    @given(
        st.integers(min_value=2, max_value=4).flatmap(
            lambda n: st.tuples(st.just(n), st.integers(min_value=2, max_value=n))
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_cache_storage_after_computation(self, dims):
        """
        **Feature: latin-rectangle-counter, Property 13: Cache storage after computation**
        **Validates: Requirements 5.4**
        
        For any dimensions (r, n), after computing counts, the results should be
        retrievable from the cache.
        """
        n, r = dims
        
        # Use a temporary database for this test
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            
            # Compute the result
            result = count_rectangles(r, n)
            
            # Store in cache
            cache.put(result)
            
            # Verify it's retrievable
            cached_result = cache.get(r, n)
            
            assert cached_result is not None, (
                f"Result for r={r}, n={n} should be retrievable after storage"
            )
            
            # Verify the stored data is correct
            assert cached_result.r == r
            assert cached_result.n == n
            assert cached_result.positive_count == result.positive_count
            assert cached_result.negative_count == result.negative_count
            assert cached_result.difference == result.difference
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_cache_update_replaces_existing(self):
        """Test that storing a result for existing dimensions replaces the old value."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            
            # Store initial result
            result1 = CountResult(2, 3, 1, 2, -1, False)
            cache.put(result1)
            
            # Store updated result for same dimensions
            result2 = CountResult(2, 3, 10, 20, -10, False)
            cache.put(result2)
            
            # Retrieve and verify it's the updated result
            cached = cache.get(2, 3)
            
            assert cached.positive_count == 10
            assert cached.negative_count == 20
            assert cached.difference == -10
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestPartialCacheUtilization:
    """Tests for partial cache utilization property."""
    
    @given(
        st.integers(min_value=2, max_value=5).flatmap(
            lambda n1: st.tuples(st.just(n1), st.integers(min_value=n1, max_value=5))
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_partial_cache_utilization(self, range_spec):
        """
        **Feature: latin-rectangle-counter, Property 14: Partial cache utilization**
        **Validates: Requirements 5.3**
        
        For any range request where some dimensions are cached and others are not,
        the system should return cached results for available dimensions and compute
        only the missing ones.
        """
        n_start, n_end = range_spec
        
        # Use a temporary database for this test
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            
            # Pre-populate cache with some dimensions in the range
            # We'll cache results for the first n value only
            if n_start <= n_end:
                for r in range(2, n_start + 1):
                    result = count_rectangles(r, n_start)
                    cache.put(result)
            
            # Get all dimensions in the range
            all_results = []
            for n in range(n_start, n_end + 1):
                for r in range(2, n + 1):
                    # Check cache first
                    cached = cache.get(r, n)
                    if cached is not None:
                        all_results.append(cached)
                    else:
                        # Compute if not cached
                        computed = count_rectangles(r, n)
                        all_results.append(computed)
            
            # Verify we got results for all expected dimensions
            expected_count = sum(n - 1 for n in range(n_start, n_end + 1))
            assert len(all_results) == expected_count, (
                f"Expected {expected_count} results for range {n_start}..{n_end}, "
                f"got {len(all_results)}"
            )
            
            # Verify cached results have from_cache=True
            cached_results = [r for r in all_results if r.from_cache]
            
            # For n=n_start, all r values should be cached
            expected_cached_count = n_start - 1 if n_start <= n_end else 0
            assert len(cached_results) == expected_cached_count, (
                f"Expected {expected_cached_count} cached results, got {len(cached_results)}"
            )
            
            # Verify all cached results are for n=n_start
            for result in cached_results:
                assert result.n == n_start, (
                    f"Cached result should be for n={n_start}, got n={result.n}"
                )
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_get_range_method(self):
        """Test the get_range method for retrieving multiple cached results."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            
            # Store several results
            cache.put(CountResult(2, 3, 1, 2, -1, False))
            cache.put(CountResult(3, 3, 0, 2, -2, False))
            cache.put(CountResult(2, 4, 3, 6, -3, False))
            cache.put(CountResult(3, 4, 5, 6, -1, False))
            cache.put(CountResult(4, 4, 1, 1, 0, False))
            
            # Get range r=2..3, n=3..4
            results = cache.get_range(2, 3, 3, 4)
            
            # Should return 4 results: (2,3), (3,3), (2,4), (3,4)
            assert len(results) == 4
            
            pairs = [(r.r, r.n) for r in results]
            assert (2, 3) in pairs
            assert (3, 3) in pairs
            assert (2, 4) in pairs
            assert (3, 4) in pairs
            
            # (4, 4) should not be included (r > 3)
            assert (4, 4) not in pairs
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestCacheDimensionQuery:
    """Tests for cache dimension query completeness."""
    
    def test_get_all_cached_dimensions(self):
        """Test get_all_cached_dimensions returns all stored dimensions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            
            # Initially should be empty
            dimensions = cache.get_all_cached_dimensions()
            assert len(dimensions) == 0
            
            # Store some results
            cache.put(CountResult(2, 3, 1, 2, -1, False))
            cache.put(CountResult(3, 4, 5, 6, -1, False))
            cache.put(CountResult(2, 5, 10, 20, -10, False))
            
            # Get all dimensions
            dimensions = cache.get_all_cached_dimensions()
            
            assert len(dimensions) == 3
            assert (2, 3) in dimensions
            assert (3, 4) in dimensions
            assert (2, 5) in dimensions
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @given(
        st.lists(
            st.integers(min_value=2, max_value=4).flatmap(
                lambda n: st.tuples(st.just(n), st.integers(min_value=2, max_value=n))
            ),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_dimension_query_completeness(self, dim_list):
        """
        Test that querying cached dimensions returns all stored dimensions.
        
        This is related to Property 16 but focuses on the get_all_cached_dimensions method.
        """
        # Use a temporary database for this test
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            
            # Store results for all dimensions in the list
            stored_dims = set()
            for n, r in dim_list:
                result = count_rectangles(r, n)
                cache.put(result)
                stored_dims.add((r, n))
            
            # Query all cached dimensions
            cached_dims = cache.get_all_cached_dimensions()
            cached_dims_set = set(cached_dims)
            
            # Verify all stored dimensions are returned
            assert cached_dims_set == stored_dims, (
                f"Cached dimensions mismatch: "
                f"stored {stored_dims}, retrieved {cached_dims_set}"
            )
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)



class TestCacheManagerContextManager:
    """Tests for cache manager context manager usage."""
    
    def test_context_manager_usage(self):
        """Test using CacheManager as a context manager."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # Use cache manager as context manager
            with CacheManager(db_path) as cache:
                # Store a result
                result = CountResult(r=2, n=3, positive_count=1, negative_count=2, difference=-1, from_cache=False)
                cache.put(result)
                
                # Retrieve it
                retrieved = cache.get(2, 3)
                assert retrieved is not None
                assert retrieved.r == 2
                assert retrieved.n == 3
            
            # Cache should be closed after exiting context
            # Verify by opening a new connection
            cache2 = CacheManager(db_path)
            result2 = cache2.get(2, 3)
            assert result2 is not None
            cache2.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
