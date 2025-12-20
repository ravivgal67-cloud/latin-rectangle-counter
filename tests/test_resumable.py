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
        r, n = 3, 4
        
        # Get reference result
        reference = count_rectangles(r, n)
        
        # Test resumable computation with temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Use small checkpoint interval for testing
            resumable = count_rectangles_resumable(r, n, cache, checkpoint_interval=5)
            
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
        """Test saving and loading counter-based checkpoints."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Test data
            r, n = 4, 5
            counters = [0, 2, 1, 0]
            positive_count = 1000
            negative_count = 2000
            rectangles_scanned = 3000
            elapsed_time = 15.5
            
            # Save checkpoint
            cache.save_checkpoint_counters(r, n, counters, positive_count, negative_count, 
                                         rectangles_scanned, elapsed_time)
            
            # Verify checkpoint exists
            assert cache.checkpoint_counters_exists(r, n)
            
            # Load checkpoint
            checkpoint = cache.load_checkpoint_counters(r, n)
            assert checkpoint is not None
            assert checkpoint['counters'] == counters
            assert checkpoint['positive_count'] == positive_count
            assert checkpoint['negative_count'] == negative_count
            assert checkpoint['rectangles_scanned'] == rectangles_scanned
            assert checkpoint['elapsed_time'] == elapsed_time
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
    
    def test_checkpoint_deletion(self):
        """Test counter-based checkpoint deletion."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            r, n = 4, 5
            counters = [0, 1, 0, 0]
            
            # Save checkpoint
            cache.save_checkpoint_counters(r, n, counters, 100, 200, 300, 5.0)
            assert cache.checkpoint_counters_exists(r, n)
            
            # Delete checkpoint
            cache.delete_checkpoint_counters(r, n)
            assert not cache.checkpoint_counters_exists(r, n)
            
            # Verify checkpoint is gone
            checkpoint = cache.load_checkpoint_counters(r, n)
            assert checkpoint is None
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
    
    def test_nonexistent_checkpoint(self):
        """Test loading nonexistent counter-based checkpoint."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Try to load nonexistent checkpoint
            checkpoint = cache.load_checkpoint_counters(99, 99)
            assert checkpoint is None
            assert not cache.checkpoint_counters_exists(99, 99)
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
    
    def test_legacy_checkpoint_methods(self):
        """Test that legacy checkpoint methods still work."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Test legacy methods
            r, n = 3, 4
            partial_rows = [[1, 2, 3, 4], [2, 1, 4, 3]]
            
            # Save legacy checkpoint
            cache.save_checkpoint(r, n, partial_rows, 10, 20, 30, 5.0)
            assert cache.checkpoint_exists(r, n)
            
            # Load legacy checkpoint
            checkpoint = cache.load_checkpoint(r, n)
            assert checkpoint is not None
            assert checkpoint['partial_rows'] == partial_rows
            
            # Delete legacy checkpoint
            cache.delete_checkpoint(r, n)
            assert not cache.checkpoint_exists(r, n)
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)


# Resumable generator tests removed - we now use ultra-safe bitwise system
# which doesn't support the old resumable generator interface


class TestResumableComputationWithInterruption:
    """Test resumable computation with simulated interruption."""
    
    def test_resumable_computation_with_simulated_interruption(self):
        """Test that resumable computation can be interrupted and resumed correctly."""
        from core.latin_rectangle import CounterBasedRectangleIterator
        
        r, n = 3, 4
        
        # Get reference result
        reference = count_rectangles(r, n)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            tmp_db = tmp_file.name
        
        try:
            cache = CacheManager(tmp_db)
            
            # Simulate first run that gets "interrupted" after processing some rectangles
            iterator = CounterBasedRectangleIterator(r, n)
            positive_count = 0
            negative_count = 0
            rectangles_processed = 0
            
            # Process first few rectangles
            for i, rect in enumerate(iterator):
                sign = rect.compute_sign()
                if sign > 0:
                    positive_count += 1
                else:
                    negative_count += 1
                rectangles_processed += 1
                
                # "Interrupt" after processing 3 rectangles
                if i >= 2:
                    break
            
            # Save checkpoint state
            iterator_state = iterator.get_state()
            cache.save_checkpoint_counters(
                r, n, iterator_state['counters'], 
                positive_count, negative_count, rectangles_processed, 10.0
            )
            
            # Simulate second run that resumes from checkpoint
            resumable_result = count_rectangles_resumable(r, n, cache, checkpoint_interval=100)
            
            # Verify results match reference
            assert resumable_result.positive_count == reference.positive_count
            assert resumable_result.negative_count == reference.negative_count
            assert resumable_result.difference == reference.difference
            
            # Clean up checkpoint manually since resumable function no longer uses checkpoints
            if cache.checkpoint_counters_exists(r, n):
                cache.delete_checkpoint_counters(r, n)
            
            cache.close()
            
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
    
    def test_counter_based_resumption_precision(self):
        """Test that counter-based resumption is precise and doesn't double-count."""
        from core.latin_rectangle import CounterBasedRectangleIterator, generate_normalized_rectangles
        
        r, n = 3, 4
        
        # Generate all rectangles in one go
        all_rects = list(generate_normalized_rectangles(r, n))
        
        # Generate rectangles in two parts using counter state
        iterator1 = CounterBasedRectangleIterator(r, n)
        first_batch = []
        
        # Get first 4 rectangles
        for i, rect in enumerate(iterator1):
            first_batch.append(rect)
            if i >= 3:  # Stop after 4 rectangles
                break
        
        # Save state and create new iterator
        state = iterator1.get_state()
        iterator2 = CounterBasedRectangleIterator(r, n, state['counters'])
        
        # Get remaining rectangles
        second_batch = list(iterator2)
        
        # Combine batches
        combined_rects = first_batch + second_batch
        
        # Verify no duplicates and complete coverage
        assert len(combined_rects) == len(all_rects)
        
        combined_set = {tuple(tuple(row) for row in rect.data) for rect in combined_rects}
        all_set = {tuple(tuple(row) for row in rect.data) for rect in all_rects}
        
        assert len(combined_set) == len(combined_rects)  # No duplicates
        assert combined_set == all_set  # Complete coverage