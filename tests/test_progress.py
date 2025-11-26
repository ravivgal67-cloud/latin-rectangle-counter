"""
Tests for progress tracking functionality.
"""

import pytest
from core.progress import ProgressTracker, ProgressUpdate
from core.counter import count_rectangles, count_for_n, count_range
from cache.cache_manager import CacheManager
import tempfile
import os


class TestProgressTracker:
    """Tests for the ProgressTracker class."""
    
    def test_progress_tracker_initialization(self):
        """Test that progress tracker initializes correctly."""
        tracker = ProgressTracker()
        assert tracker.current_r is None
        assert tracker.current_n is None
        assert tracker.rectangles_scanned == 0
        assert tracker.positive_count == 0
        assert tracker.negative_count == 0
    
    def test_start_dimension(self):
        """Test starting a new dimension."""
        tracker = ProgressTracker()
        tracker.start_dimension(3, 4)
        
        assert tracker.current_r == 3
        assert tracker.current_n == 4
        assert tracker.rectangles_scanned == 0
        assert tracker.positive_count == 0
        assert tracker.negative_count == 0
    
    def test_update_progress(self):
        """Test updating progress counters."""
        tracker = ProgressTracker()
        tracker.start_dimension(3, 4)
        
        tracker.update(positive_delta=1, scanned_delta=1)
        assert tracker.positive_count == 1
        assert tracker.negative_count == 0
        assert tracker.rectangles_scanned == 1
        
        tracker.update(negative_delta=1, scanned_delta=1)
        assert tracker.positive_count == 1
        assert tracker.negative_count == 1
        assert tracker.rectangles_scanned == 2
    
    def test_callback_invocation(self):
        """Test that callback is invoked on updates."""
        tracker = ProgressTracker()
        updates = []
        
        def callback(update):
            updates.append(update)
        
        tracker.set_callback(callback)
        tracker.start_dimension(3, 4)
        
        # Should have received start notification
        assert len(updates) == 1
        assert updates[0].r == 3
        assert updates[0].n == 4
        
        tracker.update(positive_delta=1)
        assert len(updates) == 2
        assert updates[1].positive_count == 1
    
    def test_complete_dimension(self):
        """Test marking dimension as complete."""
        tracker = ProgressTracker()
        updates = []
        
        tracker.set_callback(lambda u: updates.append(u))
        tracker.start_dimension(3, 4)
        tracker.update(positive_delta=5, negative_delta=3)
        tracker.complete_dimension()
        
        # Last update should be marked as complete
        assert updates[-1].is_complete is True
        assert updates[-1].positive_count == 5
        assert updates[-1].negative_count == 3


class TestProgressIntegration:
    """Integration tests for progress tracking with counting functions."""
    
    def test_count_rectangles_with_progress(self):
        """Test that count_rectangles reports progress."""
        tracker = ProgressTracker()
        updates = []
        
        tracker.set_callback(lambda u: updates.append(u))
        
        # Count for (3, 4) - should generate progress updates
        result = count_rectangles(3, 4, progress_tracker=tracker)
        
        # Should have received updates
        assert len(updates) > 0
        
        # First update should be start
        assert updates[0].r == 3
        assert updates[0].n == 4
        
        # Last update should be complete
        assert updates[-1].is_complete is True
        
        # Final counts should match result
        assert updates[-1].positive_count == result.positive_count
        assert updates[-1].negative_count == result.negative_count
    
    def test_count_for_n_with_progress(self):
        """Test that count_for_n reports progress for all dimensions."""
        tracker = ProgressTracker()
        updates = []
        
        tracker.set_callback(lambda u: updates.append(u))
        
        # Count for n=3 (should compute r=2,3)
        results = count_for_n(3, progress_tracker=tracker)
        
        # Should have updates for both dimensions
        dimensions_started = set()
        for update in updates:
            if not update.is_complete:
                dimensions_started.add((update.r, update.n))
        
        assert (2, 3) in dimensions_started
        assert (3, 3) in dimensions_started
    
    def test_count_range_with_progress(self):
        """Test that count_range reports progress for all dimensions."""
        tracker = ProgressTracker()
        updates = []
        
        tracker.set_callback(lambda u: updates.append(u))
        
        # Count for range n=2..3
        results = count_range(2, 3, progress_tracker=tracker)
        
        # Should have updates for (2,2), (2,3), (3,3)
        dimensions_completed = set()
        for update in updates:
            if update.is_complete:
                dimensions_completed.add((update.r, update.n))
        
        assert (2, 2) in dimensions_completed
        assert (2, 3) in dimensions_completed
        assert (3, 3) in dimensions_completed
    
    def test_progress_with_cache(self):
        """Test that progress tracking works with caching."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            cache = CacheManager(db_path)
            tracker = ProgressTracker()
            updates = []
            
            tracker.set_callback(lambda u: updates.append(u))
            
            # First computation - should report progress
            result1 = count_rectangles(3, 4, cache, tracker)
            update_count_1 = len(updates)
            assert update_count_1 > 0
            
            # Reset tracker
            updates.clear()
            
            # Second computation - should use cache (r=2 reports immediately)
            result2 = count_rectangles(3, 4, cache, tracker)
            
            # Should have no updates since it was cached
            assert len(updates) == 0
            assert result2.from_cache is True
            
            cache.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestProgressUpdate:
    """Tests for the ProgressUpdate dataclass."""
    
    def test_progress_update_to_dict(self):
        """Test converting ProgressUpdate to dictionary."""
        update = ProgressUpdate(
            r=3,
            n=4,
            rectangles_scanned=100,
            positive_count=45,
            negative_count=55,
            is_complete=False
        )
        
        d = update.to_dict()
        
        assert d['r'] == 3
        assert d['n'] == 4
        assert d['rectangles_scanned'] == 100
        assert d['positive_count'] == 45
        assert d['negative_count'] == 55
        assert d['is_complete'] is False


    def test_get_current_progress_not_tracking(self):
        """Test get_current_progress when tracker is not tracking any dimension."""
        tracker = ProgressTracker()
        
        # Should return None when not tracking
        assert tracker.get_current_progress() is None
        
        # Start tracking
        tracker.start_dimension(2, 3)
        
        # Should return progress now
        progress = tracker.get_current_progress()
        assert progress is not None
        assert progress.r == 2
        assert progress.n == 3
