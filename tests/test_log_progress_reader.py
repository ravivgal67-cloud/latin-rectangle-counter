"""
Tests for log-based progress reader with aggregated format.

Tests the new aggregated progress system that combines multiple processes
working on the same (r,n) computation into single progress entries.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from core.log_progress_reader import get_progress_from_logs, is_computation_active, _parse_jsonl_file


class TestAggregatedLogProgressReader(unittest.TestCase):
    """Test the aggregated log progress reader functionality."""
    
    def setUp(self):
        """Set up temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_single_process_progress(self):
        """Test reading progress from a single process."""
        jsonl_file = Path(self.temp_dir) / "parallel_completion_6_7_process_0_progress.jsonl"
        
        entry = {
            "timestamp": "2023-12-17T10:00:00",
            "level": "DEBUG",
            "message": "Progress update",
            "progress_pct": 50.0,
            "completed_work": 100,
            "total_work": 200,
            "positive_count": 5000,
            "negative_count": 5000
        }
        
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        progress_list = get_progress_from_logs(self.temp_dir)
        
        assert len(progress_list) == 1
        result = progress_list[0]
        assert result['r'] == 6
        assert result['n'] == 7
        assert result['rectangles_scanned'] == 100
        assert result['positive_count'] == 5000
        assert result['negative_count'] == 5000
        assert result['progress_pct'] == 50.0
        assert result['process_count'] == 1
        assert result['is_complete'] is False
    
    def test_multiple_processes_aggregation(self):
        """Test aggregating progress from multiple processes for same (r,n)."""
        # Create 3 processes working on (6,7)
        for i in range(3):
            jsonl_file = Path(self.temp_dir) / f"parallel_completion_6_7_process_{i}_progress.jsonl"
            
            entry = {
                "timestamp": "2023-12-17T10:00:00",
                "level": "DEBUG",
                "message": "Progress update",
                "progress_pct": 50.0,
                "completed_work": 100 + i * 10,  # Different progress per process
                "total_work": 200,
                "positive_count": 1000 + i * 100,
                "negative_count": 2000 + i * 200
            }
            
            with open(jsonl_file, 'w') as f:
                f.write(json.dumps(entry) + '\n')
        
        progress_list = get_progress_from_logs(self.temp_dir)
        
        # Should aggregate into single (6,7) entry
        assert len(progress_list) == 1
        result = progress_list[0]
        
        assert result['r'] == 6
        assert result['n'] == 7
        assert result['process_count'] == 3
        assert result['rectangles_scanned'] == 100 + 110 + 120  # Sum of completed_work
        assert result['positive_count'] == 1000 + 1100 + 1200   # Sum of positive counts
        assert result['negative_count'] == 2000 + 2200 + 2400   # Sum of negative counts
        assert result['total_work'] == 600  # Sum of total work
        assert result['is_complete'] is False  # No processes at 100%
    
    def test_mixed_dimensions(self):
        """Test handling multiple different (r,n) computations."""
        # Create processes for (6,7) and (5,6)
        files_data = [
            ("parallel_completion_6_7_process_0_progress.jsonl", 6, 7, 50.0, False),
            ("parallel_completion_6_7_process_1_progress.jsonl", 6, 7, 75.0, False),
            ("parallel_completion_5_6_process_0_progress.jsonl", 5, 6, 100.0, True)
        ]
        
        for filename, r, n, pct, complete in files_data:
            jsonl_file = Path(self.temp_dir) / filename
            
            entry = {
                "timestamp": "2023-12-17T10:00:00",
                "level": "DEBUG",
                "message": "Progress update",
                "progress_pct": pct,
                "completed_work": int(pct * 2),  # 100, 150, 200
                "total_work": 200,
                "positive_count": int(pct * 100),
                "negative_count": int(pct * 100)
            }
            
            with open(jsonl_file, 'w') as f:
                f.write(json.dumps(entry) + '\n')
        
        progress_list = get_progress_from_logs(self.temp_dir)
        
        # Should have 2 aggregated entries
        assert len(progress_list) == 2
        
        # Check (6,7) aggregation
        progress_6_7 = next(p for p in progress_list if p['r'] == 6 and p['n'] == 7)
        assert progress_6_7['process_count'] == 2
        assert progress_6_7['rectangles_scanned'] == 100 + 150  # Sum
        assert progress_6_7['is_complete'] is False
        
        # Check (5,6) single process
        progress_5_6 = next(p for p in progress_list if p['r'] == 5 and p['n'] == 6)
        assert progress_5_6['process_count'] == 1
        assert progress_5_6['is_complete'] is True
    
    def test_computation_activity_detection(self):
        """Test detecting active computations."""
        jsonl_file = Path(self.temp_dir) / "parallel_completion_6_7_process_0_progress.jsonl"
        
        # Create recent entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "DEBUG",
            "message": "Progress update",
            "progress_pct": 50.0,
            "completed_work": 100,
            "total_work": 200,
            "positive_count": 5000,
            "negative_count": 5000
        }
        
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Should detect as active
        active = is_computation_active(self.temp_dir, max_age_minutes=15)
        assert active is True
    
    def test_no_active_computations(self):
        """Test when no computations are active."""
        # Empty directory
        active = is_computation_active(self.temp_dir)
        assert active is False
        
        # Old computation
        jsonl_file = Path(self.temp_dir) / "parallel_completion_6_7_process_0_progress.jsonl"
        old_time = datetime.now() - timedelta(hours=1)
        
        entry = {
            "timestamp": old_time.isoformat(),
            "level": "DEBUG",
            "message": "Progress update",
            "progress_pct": 100.0,
            "completed_work": 200,
            "total_work": 200,
            "positive_count": 10000,
            "negative_count": 10000
        }
        
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        active = is_computation_active(self.temp_dir, max_age_minutes=15)
        assert active is False


if __name__ == '__main__':
    unittest.main()