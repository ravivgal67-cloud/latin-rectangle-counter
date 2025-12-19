#!/usr/bin/env python3
"""
Tests for the log progress reader functionality.
"""

import pytest
import tempfile
import shutil
import json
import os
from pathlib import Path
from datetime import datetime

from core.log_progress_reader import (
    get_progress_from_logs, 
    is_computation_active,
    _parse_jsonl_file
)


class TestLogProgressReader:
    """Test log progress reader functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_log_directory(self):
        """Test behavior with empty log directory."""
        progress = get_progress_from_logs(self.temp_dir)
        assert progress == []
        
        active = is_computation_active(self.temp_dir)
        assert active is False
    
    def test_nonexistent_log_directory(self):
        """Test behavior with nonexistent log directory."""
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        
        progress = get_progress_from_logs(nonexistent_dir)
        assert progress == []
        
        active = is_computation_active(nonexistent_dir)
        assert active is False
    
    def test_parse_valid_jsonl_file(self):
        """Test parsing a valid JSONL progress file."""
        # Create a test JSONL file
        jsonl_file = Path(self.temp_dir) / "parallel_6_7_process_0_progress.jsonl"
        
        # Create sample progress entries
        entries = [
            {
                "timestamp": "2023-12-17T10:00:00",
                "level": "DEBUG",
                "message": "Progress update",
                "rectangles_found": 10000,
                "positive_count": 5000,
                "negative_count": 5000,
                "progress_pct": 25.0,
                "completed_work": 250,
                "total_work": 1000
            },
            {
                "timestamp": "2023-12-17T10:05:00",
                "level": "DEBUG", 
                "message": "Progress update",
                "rectangles_found": 20000,
                "positive_count": 10000,
                "negative_count": 10000,
                "progress_pct": 50.0,
                "completed_work": 500,
                "total_work": 1000
            }
        ]
        
        with open(jsonl_file, 'w') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')
        
        # Parse the file
        result = _parse_jsonl_file(str(jsonl_file))
        
        assert result is not None
        assert result['r'] == 6
        assert result['n'] == 7
        assert result['process_id'] == "parallel_6_7_process_0"
        assert result['rectangles_scanned'] == 20000  # Latest entry
        assert result['positive_count'] == 10000
        assert result['negative_count'] == 10000
        assert result['progress_pct'] == 50.0
        assert result['is_complete'] is False
    
    def test_parse_completed_computation(self):
        """Test parsing a completed computation (100% progress)."""
        jsonl_file = Path(self.temp_dir) / "parallel_5_6_process_1_progress.jsonl"
        
        entry = {
            "timestamp": "2023-12-17T10:10:00",
            "level": "DEBUG",
            "message": "Final progress",
            "rectangles_found": 50000,
            "positive_count": 25000,
            "negative_count": 25000,
            "progress_pct": 100.0,
            "completed_work": 1000,
            "total_work": 1000
        }
        
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        result = _parse_jsonl_file(str(jsonl_file))
        
        assert result is not None
        assert result['r'] == 5
        assert result['n'] == 6
        assert result['is_complete'] is True
        assert result['rectangles_scanned'] == 50000
    
    def test_parse_invalid_filename(self):
        """Test parsing file with invalid filename format."""
        jsonl_file = Path(self.temp_dir) / "invalid_filename.jsonl"
        
        with open(jsonl_file, 'w') as f:
            f.write('{"test": "data"}\n')
        
        result = _parse_jsonl_file(str(jsonl_file))
        assert result is None
    
    def test_parse_malformed_json(self):
        """Test parsing file with malformed JSON."""
        jsonl_file = Path(self.temp_dir) / "parallel_4_5_process_0_progress.jsonl"
        
        with open(jsonl_file, 'w') as f:
            f.write('{"valid": "json"}\n')
            f.write('invalid json line\n')
            f.write('{"timestamp": "2023-12-17T10:00:00", "rectangles_found": 1000, "positive_count": 500, "negative_count": 500}\n')
        
        result = _parse_jsonl_file(str(jsonl_file))
        
        # Should still parse the valid entries that have required fields
        assert result is not None
        assert result['rectangles_scanned'] == 1000
    
    def test_get_progress_from_multiple_files(self):
        """Test getting progress from multiple JSONL files."""
        # Create multiple progress files
        files_data = [
            ("parallel_6_7_process_0_progress.jsonl", {
                "rectangles_found": 10000,
                "positive_count": 5000,
                "negative_count": 5000,
                "progress_pct": 50.0
            }),
            ("parallel_6_7_process_1_progress.jsonl", {
                "rectangles_found": 15000,
                "positive_count": 7500,
                "negative_count": 7500,
                "progress_pct": 75.0
            }),
            ("parallel_5_6_process_0_progress.jsonl", {
                "rectangles_found": 30000,
                "positive_count": 15000,
                "negative_count": 15000,
                "progress_pct": 100.0
            })
        ]
        
        for filename, data in files_data:
            jsonl_file = Path(self.temp_dir) / filename
            entry = {
                "timestamp": "2023-12-17T10:00:00",
                "level": "DEBUG",
                "message": "Progress update",
                **data
            }
            
            with open(jsonl_file, 'w') as f:
                f.write(json.dumps(entry) + '\n')
        
        # Get all progress
        progress_list = get_progress_from_logs(self.temp_dir)
        
        assert len(progress_list) == 3
        
        # Check that we got data from all files
        r_n_pairs = {(p['r'], p['n']) for p in progress_list}
        assert (6, 7) in r_n_pairs
        assert (5, 6) in r_n_pairs
        
        # Check completion status
        completed = [p for p in progress_list if p.get('is_complete')]
        running = [p for p in progress_list if not p.get('is_complete')]
        
        assert len(completed) == 1  # The 100% one
        assert len(running) == 2    # The others
    
    def test_is_computation_active_with_recent_logs(self):
        """Test active computation detection with recent logs."""
        jsonl_file = Path(self.temp_dir) / "parallel_6_7_process_0_progress.jsonl"
        
        # Create recent entry (current time)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "DEBUG",
            "message": "Progress update",
            "rectangles_found": 10000,
            "positive_count": 5000,
            "negative_count": 5000,
            "progress_pct": 50.0
        }
        
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Should detect as active
        active = is_computation_active(self.temp_dir, max_age_minutes=15)
        assert active is True
    
    def test_is_computation_active_with_old_logs(self):
        """Test active computation detection with old logs."""
        jsonl_file = Path(self.temp_dir) / "parallel_6_7_process_0_progress.jsonl"
        
        # Create old entry (1 hour ago)
        old_time = datetime.now().replace(hour=datetime.now().hour - 1)
        entry = {
            "timestamp": old_time.isoformat(),
            "level": "DEBUG",
            "message": "Progress update",
            "rectangles_found": 10000,
            "positive_count": 5000,
            "negative_count": 5000,
            "progress_pct": 50.0
        }
        
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Should not detect as active (too old)
        active = is_computation_active(self.temp_dir, max_age_minutes=15)
        assert active is False
    
    def test_is_computation_active_with_completed_logs(self):
        """Test active computation detection with completed computations."""
        jsonl_file = Path(self.temp_dir) / "parallel_6_7_process_0_progress.jsonl"
        
        # Create recent but completed entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "DEBUG",
            "message": "Final progress",
            "rectangles_found": 50000,
            "positive_count": 25000,
            "negative_count": 25000,
            "progress_pct": 100.0
        }
        
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Should not detect as active (completed)
        active = is_computation_active(self.temp_dir, max_age_minutes=15)
        assert active is False
    
    def test_ignore_non_parallel_files(self):
        """Test that non-parallel log files are ignored."""
        # Create non-parallel files
        files = [
            "regular_log.jsonl",
            "web_session_progress.jsonl", 
            "test_session_progress.jsonl"
        ]
        
        for filename in files:
            jsonl_file = Path(self.temp_dir) / filename
            entry = {
                "timestamp": datetime.now().isoformat(),
                "message": "Some log entry"
            }
            
            with open(jsonl_file, 'w') as f:
                f.write(json.dumps(entry) + '\n')
        
        # Should find no progress (no parallel files)
        progress_list = get_progress_from_logs(self.temp_dir)
        assert len(progress_list) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])