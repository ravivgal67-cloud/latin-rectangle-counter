"""
Progress tracking for Latin Rectangle counting operations.

This module provides utilities for tracking and reporting progress
during long-running counting operations.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgressUpdate:
    """
    Progress update for a counting operation.
    
    Attributes:
        r: Current row dimension being computed
        n: Current column dimension being computed
        rectangles_scanned: Total rectangles examined so far
        positive_count: Count of positive rectangles found
        negative_count: Count of negative rectangles found
        is_complete: Whether this dimension is complete
    """
    r: int
    n: int
    rectangles_scanned: int
    positive_count: int
    negative_count: int
    is_complete: bool = False
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'r': self.r,
            'n': self.n,
            'rectangles_scanned': self.rectangles_scanned,
            'positive_count': self.positive_count,
            'negative_count': self.negative_count,
            'is_complete': self.is_complete
        }


class ProgressTracker:
    """
    Tracks progress during counting operations.
    
    This class maintains state about the current counting operation
    and can be queried for progress updates.
    """
    
    def __init__(self, cache_manager=None):
        """
        Initialize a new progress tracker.
        
        Args:
            cache_manager: Optional CacheManager to persist progress to database
        """
        self.current_r: Optional[int] = None
        self.current_n: Optional[int] = None
        self.rectangles_scanned: int = 0
        self.positive_count: int = 0
        self.negative_count: int = 0
        self.callback = None
        self.cache_manager = cache_manager
        self.update_counter = 0  # Track updates to avoid writing too frequently
    
    def start_dimension(self, r: int, n: int):
        """
        Start tracking a new dimension.
        
        Args:
            r: Row dimension
            n: Column dimension
        """
        self.current_r = r
        self.current_n = n
        self.rectangles_scanned = 0
        self.positive_count = 0
        self.negative_count = 0
        self._notify()
    
    def update(self, positive_delta: int = 0, negative_delta: int = 0, scanned_delta: int = 1):
        """
        Update progress counters.
        
        Args:
            positive_delta: Number of positive rectangles found
            negative_delta: Number of negative rectangles found
            scanned_delta: Number of rectangles scanned
        """
        self.positive_count += positive_delta
        self.negative_count += negative_delta
        self.rectangles_scanned += scanned_delta
        self.update_counter += 1
        
        # Progress is now tracked via log files (see core/log_progress_reader.py)
        
        self._notify()
    
    def complete_dimension(self):
        """Mark the current dimension as complete."""
        if self.current_r is not None and self.current_n is not None:
            # Progress completion is now tracked via log files
            self._notify(is_complete=True)
    
    def set_callback(self, callback):
        """
        Set a callback function to be called on progress updates.
        
        Args:
            callback: Function that takes a ProgressUpdate as argument
        """
        self.callback = callback
    
    def _notify(self, is_complete: bool = False):
        """Send progress update to callback if set."""
        if self.callback and self.current_r is not None and self.current_n is not None:
            update = ProgressUpdate(
                r=self.current_r,
                n=self.current_n,
                rectangles_scanned=self.rectangles_scanned,
                positive_count=self.positive_count,
                negative_count=self.negative_count,
                is_complete=is_complete
            )
            self.callback(update)
    
    def get_current_progress(self) -> Optional[ProgressUpdate]:
        """
        Get the current progress state.
        
        Returns:
            ProgressUpdate if tracking is active, None otherwise
        """
        if self.current_r is None or self.current_n is None:
            return None
        
        return ProgressUpdate(
            r=self.current_r,
            n=self.current_n,
            rectangles_scanned=self.rectangles_scanned,
            positive_count=self.positive_count,
            negative_count=self.negative_count,
            is_complete=False
        )
