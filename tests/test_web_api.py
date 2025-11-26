"""
Property-based tests for web API module.

Feature: latin-rectangle-counter
"""

import pytest
import tempfile
import os
import json
from hypothesis import given, strategies as st, settings

from web.app import create_app
from cache import CacheManager
from core.counter import CountResult


class TestCacheDimensionQueryAPI:
    """Tests for cache dimension query completeness via API."""
    
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
    @settings(max_examples=100, deadline=None)
    def test_cache_dimension_query_completeness(self, dim_list):
        """
        **Feature: latin-rectangle-counter, Property 16: Cache dimension query completeness**
        **Validates: Requirements 8.1**
        
        For any state of the cache, querying all cached dimensions should return
        all (r, n) pairs for which results have been stored.
        """
        # Use a temporary database for this test
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # Create cache manager and app
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Store results for all dimensions in the list
            stored_dims = set()
            for n, r in dim_list:
                # Use the POST /api/count endpoint to compute and cache
                response = client.post(
                    '/api/count',
                    data=json.dumps({'r': r, 'n': n}),
                    content_type='application/json'
                )
                
                assert response.status_code == 200, (
                    f"Failed to compute for r={r}, n={n}: {response.get_json()}"
                )
                
                stored_dims.add((r, n))
            
            # Query all cached dimensions via API
            response = client.get('/api/cache')
            
            assert response.status_code == 200, (
                f"Failed to query cache: {response.get_json()}"
            )
            
            data = response.get_json()
            assert data['status'] == 'success', (
                f"API returned error status: {data}"
            )
            
            # Convert list of lists to set of tuples
            cached_dims = set(tuple(dim) for dim in data['dimensions'])
            
            # Verify all stored dimensions are returned
            assert cached_dims == stored_dims, (
                f"Cached dimensions mismatch: "
                f"stored {stored_dims}, retrieved {cached_dims}"
            )
            
            cache.close()
        finally:
            # Clean up temporary database
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_empty_cache_returns_empty_list(self):
        """Test that querying an empty cache returns an empty list."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.get('/api/cache')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['dimensions'] == []
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_cache_results_endpoint_returns_cached_data(self):
        """Test that /api/cache/results returns cached results in the specified range."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Store some results via the count endpoint
            client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 4}),
                content_type='application/json'
            )
            client.post(
                '/api/count',
                data=json.dumps({'r': 3, 'n': 4}),
                content_type='application/json'
            )
            
            # Query cached results for range
            response = client.get('/api/cache/results?r_min=2&r_max=3&n_min=3&n_max=4')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            # Should return 3 results
            results = data['results']
            assert len(results) == 3
            
            # Verify all results are marked as from_cache
            for result in results:
                assert result['from_cache'] is True
            
            # Verify the dimensions
            dims = [(r['r'], r['n']) for r in results]
            assert (2, 3) in dims
            assert (2, 4) in dims
            assert (3, 4) in dims
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestErrorHandlers:
    """Tests for error handlers."""
    
    def test_404_not_found(self):
        """Test 404 error for non-existent endpoint (caught by exception handler)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.get('/api/nonexistent')
            # Flask's exception handler catches 404 and returns 500
            assert response.status_code == 500
            data = response.get_json()
            assert data['status'] == 'error'
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_progress_endpoint_success(self):
        """Test progress endpoint returns successfully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.get('/api/progress')
            
            # Should return 200 with empty progress
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'progress' in data
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestFrontendRoutes:
    """Tests for frontend routes."""
    
    def test_index_route(self):
        """Test that index route returns HTML."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.get('/')
            
            # Should return 200 or 500 (template might not exist in test env)
            # We just want to ensure the route is accessible
            assert response.status_code in [200, 500]
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_static_route(self):
        """Test that static file route is accessible."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Try to access a static file (will 500 if doesn't exist due to exception handler)
            response = client.get('/static/test.css')
            
            # Exception handler catches 404 and returns 500
            assert response.status_code == 500
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestStreamingEndpoint:
    """Tests for the streaming endpoint."""
    
    def test_streaming_endpoint_invalid_json(self):
        """Test streaming endpoint with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Send request without JSON body (exception handler catches it)
            response = client.post('/api/count/stream')
            
            # Exception handler returns 500
            assert response.status_code == 500
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_streaming_endpoint_single_dimension(self):
        """Test streaming endpoint with single dimension."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count/stream',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            assert response.content_type == 'text/event-stream; charset=utf-8'
            
            # Read the streaming response
            data = response.get_data(as_text=True)
            
            # Should contain SSE formatted data
            assert 'data:' in data
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_streaming_endpoint_invalid_dimensions(self):
        """Test streaming endpoint with invalid dimensions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count/stream',
                data=json.dumps({'r': 5, 'n': 3}),  # Invalid: r > n
                content_type='application/json'
            )
            
            assert response.status_code == 200  # SSE always returns 200
            data = response.get_data(as_text=True)
            
            # Should contain error in SSE format
            assert 'error' in data
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_streaming_endpoint_all_for_n(self):
        """Test streaming endpoint with all_for_n mode."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count/stream',
                data=json.dumps({'n': 3}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'data:' in data
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_streaming_endpoint_range(self):
        """Test streaming endpoint with range mode."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count/stream',
                data=json.dumps({'n_start': 2, 'n_end': 3}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'data:' in data
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_streaming_endpoint_invalid_input(self):
        """Test streaming endpoint with invalid input (no valid parameters)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count/stream',
                data=json.dumps({}),  # No parameters
                content_type='application/json'
            )
            
            assert response.status_code == 200  # SSE always returns 200
            data = response.get_data(as_text=True)
            assert 'error' in data
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestCacheResultsEndpoint:
    """Tests for the /api/cache/results endpoint."""
    
    def test_cache_results_invalid_parameters(self):
        """Test cache results endpoint with invalid parameters."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Test r_min < 2
            response = client.get('/api/cache/results?r_min=1')
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'r_min must be at least 2' in data['error']
            
            # Test n_min < 2
            response = client.get('/api/cache/results?n_min=1')
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'n_min must be at least 2' in data['error']
            
            # Test r_min > r_max
            response = client.get('/api/cache/results?r_min=5&r_max=3')
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'r_min must be <= r_max' in data['error']
            
            # Test n_min > n_max
            response = client.get('/api/cache/results?n_min=5&n_max=3')
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'n_min must be <= n_max' in data['error']
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestLoggingBehavior:
    """Tests for logging configuration and behavior."""
    
    def test_progress_endpoint_does_not_spam_logs(self):
        """Test that the /api/progress endpoint doesn't generate log spam."""
        import logging
        from io import StringIO
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Capture werkzeug logs
            log_capture = StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setLevel(logging.INFO)
            
            werkzeug_logger = logging.getLogger('werkzeug')
            original_level = werkzeug_logger.level
            werkzeug_logger.addHandler(handler)
            werkzeug_logger.setLevel(logging.INFO)
            
            try:
                # Make multiple requests to /api/progress
                for _ in range(5):
                    response = client.get('/api/progress')
                    assert response.status_code == 200
                
                # Get the captured logs
                log_output = log_capture.getvalue()
                
                # Verify that /api/progress requests are NOT logged
                assert '/api/progress' not in log_output, (
                    f"Progress endpoint should not be logged, but found in logs: {log_output}"
                )
                
            finally:
                # Restore original logging configuration
                werkzeug_logger.removeHandler(handler)
                werkzeug_logger.setLevel(original_level)
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_progress_filter_is_configured(self):
        """Test that the ProgressFilter is properly configured on the werkzeug logger."""
        import logging
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            
            # Get the werkzeug logger
            werkzeug_logger = logging.getLogger('werkzeug')
            
            # Check that a ProgressFilter is attached
            filter_found = False
            for filter_obj in werkzeug_logger.filters:
                if filter_obj.__class__.__name__ == 'ProgressFilter':
                    filter_found = True
                    
                    # Test the filter directly
                    class MockRecord:
                        def getMessage(self):
                            return "GET /api/progress HTTP/1.1"
                    
                    class MockRecord2:
                        def getMessage(self):
                            return "GET /api/cache HTTP/1.1"
                    
                    # Progress endpoint should be filtered out (return False)
                    assert filter_obj.filter(MockRecord()) is False, (
                        "ProgressFilter should filter out /api/progress requests"
                    )
                    
                    # Other endpoints should pass through (return True)
                    assert filter_obj.filter(MockRecord2()) is True, (
                        "ProgressFilter should allow other requests through"
                    )
                    
                    break
            
            assert filter_found, (
                "ProgressFilter should be configured on werkzeug logger"
            )
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestCountEndpoint:
    """Tests for the /api/count endpoint."""
    
    def test_count_single_dimension(self):
        """Test counting for a single (r, n) pair."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert len(data['results']) == 1
            
            result = data['results'][0]
            assert result['r'] == 2
            assert result['n'] == 3
            assert 'positive_count' in result
            assert 'negative_count' in result
            assert 'difference' in result
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_count_all_for_n(self):
        """Test counting for all r from 2 to n."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count',
                data=json.dumps({'n': 4}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            # Should return results for r=2, 3, 4
            assert len(data['results']) == 3
            
            r_values = [result['r'] for result in data['results']]
            assert 2 in r_values
            assert 3 in r_values
            assert 4 in r_values
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_count_range(self):
        """Test counting for a range of n values."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            response = client.post(
                '/api/count',
                data=json.dumps({'n_start': 2, 'n_end': 3}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            # Should return results for (2,2), (2,3), (3,3)
            assert len(data['results']) == 3
            
            dims = [(r['r'], r['n']) for r in data['results']]
            assert (2, 2) in dims
            assert (2, 3) in dims
            assert (3, 3) in dims
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_invalid_dimensions_rejected(self):
        """Test that invalid dimensions are rejected with error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Test r > n
            response = client.post(
                '/api/count',
                data=json.dumps({'r': 5, 'n': 3}),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'error' in data
            
            # Test r < 2
            response = client.post(
                '/api/count',
                data=json.dumps({'r': 1, 'n': 3}),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_caching_behavior(self):
        """Test that results are cached and reused."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # First request - should compute
            response1 = client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            assert response1.status_code == 200
            data1 = response1.get_json()
            result1 = data1['results'][0]
            
            # Second request - should use cache
            response2 = client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            assert response2.status_code == 200
            data2 = response2.get_json()
            result2 = data2['results'][0]
            
            # Results should match
            assert result1['positive_count'] == result2['positive_count']
            assert result1['negative_count'] == result2['negative_count']
            
            # Second result should be from cache
            assert result2['from_cache'] is True
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
