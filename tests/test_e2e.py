"""
End-to-end tests for Latin Rectangle Counter application.

These tests verify the complete workflow from input through computation,
caching, and display. They test the integration of all system components.
"""

import pytest
import tempfile
import os
import json
import sqlite3
from pathlib import Path

from web.app import create_app
from cache.cache_manager import CacheManager
from core.counter import count_rectangles


class TestCompleteWorkflow:
    """Test complete workflow: input → compute → cache → display."""
    
    def test_single_dimension_workflow(self):
        """
        Test the complete workflow for a single dimension:
        1. Submit dimension via API
        2. Verify computation occurs
        3. Verify result is cached
        4. Verify result can be retrieved
        5. Verify subsequent request uses cache
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Step 1: Submit dimension via API
            response = client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            # Step 2: Verify computation occurs
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
            assert result['from_cache'] is False  # First computation
            
            # Store the computed values
            positive = result['positive_count']
            negative = result['negative_count']
            difference = result['difference']
            
            # Step 3: Verify result is cached
            cached_result = cache.get(2, 3)
            assert cached_result is not None
            assert cached_result.r == 2
            assert cached_result.n == 3
            assert cached_result.positive_count == positive
            assert cached_result.negative_count == negative
            
            # Step 4: Verify result can be retrieved via cache API
            cache_response = client.get('/api/cache')
            assert cache_response.status_code == 200
            cache_data = cache_response.get_json()
            assert (2, 3) in [tuple(dim) for dim in cache_data['dimensions']]
            
            # Step 5: Verify subsequent request uses cache
            response2 = client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            assert response2.status_code == 200
            data2 = response2.get_json()
            result2 = data2['results'][0]
            
            # Values should match
            assert result2['positive_count'] == positive
            assert result2['negative_count'] == negative
            assert result2['difference'] == difference
            
            # Should be from cache
            assert result2['from_cache'] is True
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_range_workflow_with_display(self):
        """
        Test workflow for range calculation with display:
        1. Submit range request
        2. Verify all dimensions computed
        3. Verify all results cached
        4. Retrieve via cache/results endpoint
        5. Verify presentation view data
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Step 1: Submit range request (n=2 to n=3)
            response = client.post(
                '/api/count',
                data=json.dumps({'n_start': 2, 'n_end': 3}),
                content_type='application/json'
            )
            
            # Step 2: Verify all dimensions computed
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            # Should have results for (2,2), (2,3), (3,3)
            results = data['results']
            assert len(results) == 3
            
            dims = [(r['r'], r['n']) for r in results]
            assert (2, 2) in dims
            assert (2, 3) in dims
            assert (3, 3) in dims
            
            # Step 3: Verify all results cached
            for r, n in dims:
                cached = cache.get(r, n)
                assert cached is not None
                assert cached.r == r
                assert cached.n == n
            
            # Step 4: Retrieve via cache/results endpoint
            cache_results_response = client.get(
                '/api/cache/results?r_min=2&r_max=3&n_min=2&n_max=3'
            )
            
            assert cache_results_response.status_code == 200
            cache_data = cache_results_response.get_json()
            assert cache_data['status'] == 'success'
            
            # Step 5: Verify presentation view data
            cached_results = cache_data['results']
            assert len(cached_results) == 3
            
            # All should be marked as from_cache
            for result in cached_results:
                assert result['from_cache'] is True
            
            # Verify dimensions match
            cached_dims = [(r['r'], r['n']) for r in cached_results]
            assert set(cached_dims) == set(dims)
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_all_for_n_workflow(self):
        """
        Test workflow for counting all r for a given n:
        1. Submit n-only request
        2. Verify all r from 2 to n computed
        3. Verify caching
        4. Verify retrieval
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Step 1: Submit n-only request
            response = client.post(
                '/api/count',
                data=json.dumps({'n': 4}),
                content_type='application/json'
            )
            
            # Step 2: Verify all r from 2 to n computed
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            results = data['results']
            assert len(results) == 3  # r=2, 3, 4
            
            r_values = [result['r'] for result in results]
            assert 2 in r_values
            assert 3 in r_values
            assert 4 in r_values
            
            # All should have n=4
            for result in results:
                assert result['n'] == 4
            
            # Step 3: Verify caching
            for r in [2, 3, 4]:
                cached = cache.get(r, 4)
                assert cached is not None
                assert cached.r == r
                assert cached.n == 4
            
            # Step 4: Verify retrieval via cache dimensions
            cache_response = client.get('/api/cache')
            assert cache_response.status_code == 200
            cache_data = cache_response.get_json()
            
            dims = [tuple(dim) for dim in cache_data['dimensions']]
            assert (2, 4) in dims
            assert (3, 4) in dims
            assert (4, 4) in dims
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestCachePersistence:
    """Test cache persistence across application restarts."""
    
    def test_cache_survives_restart(self):
        """
        Test that cached results persist across application restarts:
        1. Compute and cache results
        2. Close cache/app
        3. Create new cache/app with same database
        4. Verify results still available
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # Phase 1: First application instance
            cache1 = CacheManager(db_path)
            app1 = create_app(cache1)
            client1 = app1.test_client()
            
            # Compute some results
            response1 = client1.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            assert response1.status_code == 200
            data1 = response1.get_json()
            result1 = data1['results'][0]
            
            positive1 = result1['positive_count']
            negative1 = result1['negative_count']
            
            # Close the first instance
            cache1.close()
            
            # Phase 2: Second application instance (simulating restart)
            cache2 = CacheManager(db_path)
            app2 = create_app(cache2)
            client2 = app2.test_client()
            
            # Verify cached dimensions are available
            cache_response = client2.get('/api/cache')
            assert cache_response.status_code == 200
            cache_data = cache_response.get_json()
            
            dims = [tuple(dim) for dim in cache_data['dimensions']]
            assert (2, 3) in dims
            
            # Request the same dimension - should use cache
            response2 = client2.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            
            assert response2.status_code == 200
            data2 = response2.get_json()
            result2 = data2['results'][0]
            
            # Values should match original computation
            assert result2['positive_count'] == positive1
            assert result2['negative_count'] == negative1
            
            # Should be from cache
            assert result2['from_cache'] is True
            
            cache2.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_database_file_persistence(self):
        """
        Test that the SQLite database file persists correctly:
        1. Create cache and store results
        2. Close cache
        3. Verify database file exists
        4. Open database directly and verify data
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # Create cache and store results
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Compute multiple results
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
            
            cache.close()
            
            # Verify database file exists
            assert os.path.exists(db_path)
            
            # Open database directly and verify data
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT r, n FROM results ORDER BY r, n")
            rows = cursor.fetchall()
            
            assert len(rows) == 2
            assert (2, 3) in rows
            assert (2, 4) in rows
            
            conn.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestPartialCacheUtilization:
    """Test range calculations with partial cache."""
    
    def test_range_with_partial_cache(self):
        """
        Test that range calculations efficiently use partial cache:
        1. Pre-populate cache with some dimensions
        2. Request range including cached and uncached
        3. Verify cached results used
        4. Verify only missing dimensions computed
        5. Verify all results returned
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Step 1: Pre-populate cache with (2,3) and (3,3)
            response1 = client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 3}),
                content_type='application/json'
            )
            assert response1.status_code == 200
            
            response2 = client.post(
                '/api/count',
                data=json.dumps({'r': 3, 'n': 3}),
                content_type='application/json'
            )
            assert response2.status_code == 200
            
            # Verify these are cached
            assert cache.get(2, 3) is not None
            assert cache.get(3, 3) is not None
            assert cache.get(2, 4) is None  # Not yet cached
            
            # Step 2: Request range that includes cached and uncached
            # Range: n=3 to n=4, which includes (2,3), (3,3), (2,4), (3,4), (4,4)
            response3 = client.post(
                '/api/count',
                data=json.dumps({'n_start': 3, 'n_end': 4}),
                content_type='application/json'
            )
            
            assert response3.status_code == 200
            data = response3.get_json()
            assert data['status'] == 'success'
            
            results = data['results']
            
            # Step 3 & 4: Verify cached results used and missing computed
            result_dict = {(r['r'], r['n']): r for r in results}
            
            # Previously cached should be marked as from_cache
            assert result_dict[(2, 3)]['from_cache'] is True
            assert result_dict[(3, 3)]['from_cache'] is True
            
            # Newly computed should not be marked as from_cache initially
            # (but will be cached after computation)
            
            # Step 5: Verify all results returned
            expected_dims = [(2, 3), (3, 3), (2, 4), (3, 4), (4, 4)]
            actual_dims = [(r['r'], r['n']) for r in results]
            
            assert set(actual_dims) == set(expected_dims)
            
            # Verify all are now cached
            for r, n in expected_dims:
                assert cache.get(r, n) is not None
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_all_for_n_with_partial_cache(self):
        """
        Test counting all r for n when some are already cached:
        1. Cache (2,4)
        2. Request all for n=4
        3. Verify (2,4) from cache
        4. Verify (3,4) and (4,4) computed
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Step 1: Cache (2,4)
            response1 = client.post(
                '/api/count',
                data=json.dumps({'r': 2, 'n': 4}),
                content_type='application/json'
            )
            assert response1.status_code == 200
            
            # Verify cached
            cached_2_4 = cache.get(2, 4)
            assert cached_2_4 is not None
            
            # Step 2: Request all for n=4
            response2 = client.post(
                '/api/count',
                data=json.dumps({'n': 4}),
                content_type='application/json'
            )
            
            assert response2.status_code == 200
            data = response2.get_json()
            results = data['results']
            
            # Should have 3 results
            assert len(results) == 3
            
            # Step 3: Verify (2,4) from cache
            result_dict = {(r['r'], r['n']): r for r in results}
            assert result_dict[(2, 4)]['from_cache'] is True
            
            # Step 4: Verify all dimensions present
            dims = [(r['r'], r['n']) for r in results]
            assert (2, 4) in dims
            assert (3, 4) in dims
            assert (4, 4) in dims
            
            # All should now be cached
            assert cache.get(2, 4) is not None
            assert cache.get(3, 4) is not None
            assert cache.get(4, 4) is not None
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestBothViews:
    """Test both calculation and presentation views."""
    
    def test_calculation_view_accessible(self):
        """Test that the calculation view (main page) is accessible."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Access main page
            response = client.get('/')
            
            assert response.status_code == 200
            assert b'html' in response.data.lower()
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_presentation_view_workflow(self):
        """
        Test presentation view workflow:
        1. Compute some results (calculation view)
        2. Query cached dimensions (presentation view)
        3. Retrieve cached results for display (presentation view)
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Step 1: Compute results via calculation view API
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
            
            # Step 2: Query cached dimensions (presentation view)
            cache_response = client.get('/api/cache')
            
            assert cache_response.status_code == 200
            cache_data = cache_response.get_json()
            assert cache_data['status'] == 'success'
            
            dims = cache_data['dimensions']
            assert len(dims) == 2
            assert [2, 3] in dims
            assert [2, 4] in dims
            
            # Step 3: Retrieve cached results for display
            results_response = client.get(
                '/api/cache/results?r_min=2&r_max=2&n_min=3&n_max=4'
            )
            
            assert results_response.status_code == 200
            results_data = results_response.get_json()
            assert results_data['status'] == 'success'
            
            results = results_data['results']
            assert len(results) == 2
            
            # All should be from cache
            for result in results:
                assert result['from_cache'] is True
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_empty_cache_presentation_view(self):
        """
        Test presentation view with empty cache:
        1. Query dimensions with empty cache
        2. Verify empty list returned
        3. Query results with empty cache
        4. Verify empty list returned
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Step 1 & 2: Query dimensions with empty cache
            cache_response = client.get('/api/cache')
            
            assert cache_response.status_code == 200
            cache_data = cache_response.get_json()
            assert cache_data['status'] == 'success'
            assert cache_data['dimensions'] == []
            
            # Step 3 & 4: Query results with empty cache
            results_response = client.get(
                '/api/cache/results?r_min=2&r_max=5&n_min=2&n_max=5'
            )
            
            assert results_response.status_code == 200
            results_data = results_response.get_json()
            assert results_data['status'] == 'success'
            assert results_data['results'] == []
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestErrorHandling:
    """Test error handling in end-to-end workflows."""
    
    def test_invalid_input_workflow(self):
        """
        Test that invalid inputs are properly rejected:
        1. Submit invalid dimensions
        2. Verify error response
        3. Verify no cache pollution
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Test r > n
            response1 = client.post(
                '/api/count',
                data=json.dumps({'r': 5, 'n': 3}),
                content_type='application/json'
            )
            
            assert response1.status_code == 400
            data1 = response1.get_json()
            assert data1['status'] == 'error'
            
            # Test r < 2
            response2 = client.post(
                '/api/count',
                data=json.dumps({'r': 1, 'n': 3}),
                content_type='application/json'
            )
            
            assert response2.status_code == 400
            data2 = response2.get_json()
            assert data2['status'] == 'error'
            
            # Verify no cache pollution
            cache_response = client.get('/api/cache')
            cache_data = cache_response.get_json()
            assert cache_data['dimensions'] == []
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_malformed_request_workflow(self):
        """Test handling of malformed requests."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            app = create_app(cache)
            client = app.test_client()
            
            # Test missing JSON body (returns 500 due to content-type mismatch)
            response1 = client.post(
                '/api/count',
                data='not json',
                content_type='text/plain'
            )
            
            # Server returns 500 for unsupported media type
            assert response1.status_code == 500
            data1 = response1.get_json()
            assert data1['status'] == 'error'
            
            # Test empty JSON (missing required fields)
            response2 = client.post(
                '/api/count',
                data=json.dumps({}),
                content_type='application/json'
            )
            
            assert response2.status_code == 400
            data2 = response2.get_json()
            assert data2['status'] == 'error'
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
