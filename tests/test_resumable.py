"""
Tests for resumable computation functionality.
"""

import os
import tempfile
import pytest
from cache.cache_manager import CacheManager
from core.counter import count_rectangles_resumable, count_rectangles


class TestResumableComputation:
    """Test resumable computation with checkpoints."""
    
    def test_resumable_matches_regular_computation(self):
        """Test that resumable computation produces same results as regular computation."""
        # Use a smaller dimension for faster testing
        r, n = 4, 5
        
        # Get reference result
        reference = count_rectangles(r, n)
        
        # Test resumable computation with temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Use small checkpoint interval for testing
            resumable = count_rectangles_resumable(r, n, cache, checkpoint_interval=1000)
            
            # Verify results match
            assert resumable.positive_count == reference.positive_count
            assert resumable.negative_count == reference.negative_count
            assert resumable.difference == reference.difference
            assert not resumable.from_cache  # Should be fresh computation
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
    
    def test_cached_result_retrieval(self):
        """Test that cached results are retrieved correctly."""
        r, n = 3, 4
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # First computation
            result1 = count_rectangles_resumable(r, n, cache)
            assert not result1.from_cache
            
            # Second computation should use cache
            result2 = count_rectangles_resumable(r, n, cache)
            assert result2.from_cache
            assert result2.positive_count == result1.positive_count
            assert result2.negative_count == result1.negative_count
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)


class TestCheckpointManagement:
    """Test checkpoint save/load/delete functionality."""
    
    def test_checkpoint_save_and_load(self):
        """Test saving and loading checkpoints."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Test data
            r, n = 5, 6
            partial_rows = [
                [1, 2, 3, 4, 5, 6],
                [2, 6, 1, 3, 4, 5]
            ]
            positive_count = 1000
            negative_count = 2000
            rectangles_scanned = 3000
            elapsed_time = 15.5
            
            # Save checkpoint
            cache.save_checkpoint(r, n, partial_rows, positive_count, negative_count, 
                                rectangles_scanned, elapsed_time)
            
            # Verify checkpoint exists
            assert cache.checkpoint_exists(r, n)
            
            # Load checkpoint
            checkpoint = cache.load_checkpoint(r, n)
            assert checkpoint is not None
            assert checkpoint['partial_rows'] == partial_rows
            assert checkpoint['positive_count'] == positive_count
            assert checkpoint['negative_count'] == negative_count
            assert checkpoint['rectangles_scanned'] == rectangles_scanned
            assert checkpoint['elapsed_time'] == elapsed_time
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
    
    def test_checkpoint_deletion(self):
        """Test checkpoint deletion."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            r, n = 4, 5
            partial_rows = [[1, 2, 3, 4, 5]]
            
            # Save checkpoint
            cache.save_checkpoint(r, n, partial_rows, 100, 200, 300, 5.0)
            assert cache.checkpoint_exists(r, n)
            
            # Delete checkpoint
            cache.delete_checkpoint(r, n)
            assert not cache.checkpoint_exists(r, n)
            
            # Verify checkpoint is gone
            checkpoint = cache.load_checkpoint(r, n)
            assert checkpoint is None
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
    
    def test_nonexistent_checkpoint(self):
        """Test loading nonexistent checkpoint."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Try to load nonexistent checkpoint
            checkpoint = cache.load_checkpoint(99, 99)
            assert checkpoint is None
            assert not cache.checkpoint_exists(99, 99)
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)


class TestResumableGenerator:
    """Test the resumable rectangle generator."""
    
    def test_resumable_generator_fresh_start(self):
        """Test resumable generator starting fresh."""
        from core.latin_rectangle import generate_normalized_rectangles_resumable, generate_normalized_rectangles
        
        r, n = 3, 4
        
        # Generate with regular generator
        regular_rects = list(generate_normalized_rectangles(r, n))
        
        # Generate with resumable generator (fresh start)
        resumable_rects = list(generate_normalized_rectangles_resumable(r, n, None))
        
        # Should produce same results
        assert len(regular_rects) == len(resumable_rects)
        
        # Convert to sets for comparison (order might differ)
        regular_set = {tuple(tuple(row) for row in rect.data) for rect in regular_rects}
        resumable_set = {tuple(tuple(row) for row in rect.data) for rect in resumable_rects}
        
        assert regular_set == resumable_set
    
    def test_resumable_generator_with_partial(self):
        """Test resumable generator with partial rectangle."""
        from core.latin_rectangle import generate_normalized_rectangles_resumable
        
        r, n = 3, 4
        partial_rows = [
            [1, 2, 3, 4],  # Identity first row
            [2, 1, 4, 3]   # Second row
        ]
        
        # Generate rectangles starting from partial
        rects = list(generate_normalized_rectangles_resumable(r, n, partial_rows))
        
        # All rectangles should start with the partial rows
        for rect in rects:
            assert rect.data[0] == partial_rows[0]
            assert rect.data[1] == partial_rows[1]
            assert len(rect.data) == r
            assert rect.is_valid()
            assert rect.is_normalized()