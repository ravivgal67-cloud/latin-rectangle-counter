#!/usr/bin/env python3
"""
Tests for multiprocessing logging functionality.

Tests the logging system with actual parallel computation to ensure:
- Each process creates its own log file
- Main session log is created
- Progress tracking works across processes
- No deadlocks or hangs occur
"""

import pytest
import tempfile
import shutil
import time
import json
from pathlib import Path
import multiprocessing as mp

from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise
from core.logging_config import ProgressLogger, close_logger


class TestMultiprocessLogging:
    """Test logging with actual multiprocessing."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Clean up any existing logs from previous tests
        self._cleanup_logs()
        # Ensure clean logger state
        close_logger()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up logs and temp directory
        self._cleanup_logs()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        close_logger()
    
    def _cleanup_logs(self):
        """Clean up log files from previous test runs."""
        from pathlib import Path
        log_dir = Path("logs")
        if log_dir.exists():
            # Clean up parallel computation logs
            for pattern in ["parallel_3_7*.log", "parallel_3_7*.jsonl"]:
                for log_file in log_dir.glob(pattern):
                    log_file.unlink(missing_ok=True)
            # Clean up test session logs
            for pattern in ["test_*.log", "test_*.jsonl"]:
                for log_file in log_dir.glob(pattern):
                    log_file.unlink(missing_ok=True)
    
    def test_multiprocess_logging_with_computation(self):
        """Test that multiprocessing logging works with actual computation (3,7)."""
        r, n = 3, 7
        num_processes = 8
        
        # Run computation with logging
        result = count_rectangles_parallel_ultra_bitwise(
            r, n, 
            num_processes=num_processes
        )
        
        # Verify computation completed
        assert result is not None
        assert result.positive_count > 0 or result.negative_count > 0
        
        # Check that log files were created
        log_dir = Path("logs")
        assert log_dir.exists()
        
        # Check for main session log
        main_log_pattern = f"parallel_{r}_{n}.log"
        main_logs = list(log_dir.glob(main_log_pattern))
        assert len(main_logs) > 0, f"Main log file {main_log_pattern} not found"
        
        # Check for process-specific logs
        process_log_pattern = f"parallel_{r}_{n}_process_*.log"
        process_logs = list(log_dir.glob(process_log_pattern))
        
        # Should have logs for each process (or at least some processes)
        assert len(process_logs) > 0, "No process-specific log files found"
        assert len(process_logs) <= num_processes, f"Too many process logs: {len(process_logs)}"
        
        print(f"✅ Found {len(process_logs)} process log files")
        
        # Check for JSONL progress files
        jsonl_pattern = f"parallel_{r}_{n}_process_*_progress.jsonl"
        jsonl_files = list(log_dir.glob(jsonl_pattern))
        assert len(jsonl_files) > 0, "No JSONL progress files found"
        
        print(f"✅ Found {len(jsonl_files)} JSONL progress files")
        
        # Verify JSONL files contain valid progress data
        for jsonl_file in jsonl_files:
            content = jsonl_file.read_text()
            lines = [line for line in content.strip().split('\n') if line.strip()]
            
            assert len(lines) > 0, f"JSONL file {jsonl_file.name} is empty"
            
            # Check that at least one line has progress data
            has_progress = False
            for line in lines:
                try:
                    data = json.loads(line)
                    if 'rectangles_found' in data or 'process_id' in data:
                        has_progress = True
                        break
                except json.JSONDecodeError:
                    continue
            
            assert has_progress, f"JSONL file {jsonl_file.name} has no progress data"
        
        print(f"✅ All JSONL files contain valid progress data")
    
    def test_process_log_separation(self):
        """Test that each process writes to its own log file."""
        r, n = 3, 7
        num_processes = 4  # Use fewer processes for faster test
        
        # Run computation
        result = count_rectangles_parallel_ultra_bitwise(
            r, n,
            num_processes=num_processes,
            
        )
        
        assert result is not None
        
        # Get all process logs
        log_dir = Path("logs")
        process_logs = list(log_dir.glob(f"parallel_{r}_{n}_process_*.log"))
        
        # Each log should have unique process ID
        process_ids = set()
        for log_file in process_logs:
            # Extract process ID from filename
            # Format: parallel_3_7_process_0.log
            parts = log_file.stem.split('_')
            if len(parts) >= 5 and parts[3] == 'process':
                process_id = parts[4]
                assert process_id not in process_ids, f"Duplicate process ID: {process_id}"
                process_ids.add(process_id)
        
        print(f"✅ Found {len(process_ids)} unique process IDs: {sorted(process_ids)}")
        assert len(process_ids) > 0
    
    def test_main_log_contains_summary(self):
        """Test that main log contains overall computation summary."""
        r, n = 3, 7
        num_processes = 4
        
        # Run computation
        result = count_rectangles_parallel_ultra_bitwise(
            r, n,
            num_processes=num_processes,
            
        )
        
        assert result is not None
        
        # Check main log content
        log_dir = Path("logs")
        main_logs = list(log_dir.glob(f"parallel_{r}_{n}.log"))
        assert len(main_logs) > 0
        
        main_log = main_logs[0]
        content = main_log.read_text()
        
        # Should contain session start
        assert "SESSION START" in content or "parallel" in content.lower()
        
        # Should mention number of processes
        assert str(num_processes) in content or "process" in content.lower()
        
        print(f"✅ Main log contains computation summary")
    
    def test_progress_tracking_in_logs(self):
        """Test that progress updates are logged during computation."""
        r, n = 3, 7
        num_processes = 4
        
        # Run computation
        result = count_rectangles_parallel_ultra_bitwise(
            r, n,
            num_processes=num_processes,
            
        )
        
        assert result is not None
        
        # Check JSONL files for progress updates
        log_dir = Path("logs")
        jsonl_files = list(log_dir.glob(f"parallel_{r}_{n}_process_*_progress.jsonl"))
        
        progress_updates_found = 0
        
        for jsonl_file in jsonl_files:
            content = jsonl_file.read_text()
            lines = [line for line in content.strip().split('\n') if line.strip()]
            
            for line in lines:
                try:
                    data = json.loads(line)
                    
                    # Look for progress-related fields
                    if any(key in data for key in ['rectangles_found', 'positive_count', 
                                                     'negative_count', 'progress_pct']):
                        progress_updates_found += 1
                        
                        # Verify data structure
                        if 'rectangles_found' in data:
                            assert isinstance(data['rectangles_found'], (int, float))
                            assert data['rectangles_found'] >= 0
                        
                        if 'positive_count' in data:
                            assert isinstance(data['positive_count'], (int, float))
                            assert data['positive_count'] >= 0
                        
                        if 'negative_count' in data:
                            assert isinstance(data['negative_count'], (int, float))
                            assert data['negative_count'] >= 0
                
                except json.JSONDecodeError:
                    continue
        
        print(f"✅ Found {progress_updates_found} progress updates across all processes")
        assert progress_updates_found > 0, "No progress updates found in logs"
    
    def test_no_log_corruption_with_multiprocessing(self):
        """Test that concurrent logging doesn't corrupt log files."""
        r, n = 3, 7
        num_processes = 8  # Use all 8 processes to stress test
        
        # Run computation
        result = count_rectangles_parallel_ultra_bitwise(
            r, n,
            num_processes=num_processes,
            
        )
        
        assert result is not None
        
        # Check that all JSONL files are valid JSON
        log_dir = Path("logs")
        jsonl_files = list(log_dir.glob(f"parallel_{r}_{n}_process_*_progress.jsonl"))
        
        for jsonl_file in jsonl_files:
            content = jsonl_file.read_text()
            lines = [line for line in content.strip().split('\n') if line.strip()]
            
            valid_lines = 0
            for line in lines:
                try:
                    json.loads(line)
                    valid_lines += 1
                except json.JSONDecodeError as e:
                    # Log corruption detected
                    pytest.fail(f"Corrupted JSON in {jsonl_file.name}: {line[:100]}... Error: {e}")
            
            assert valid_lines > 0, f"No valid JSON lines in {jsonl_file.name}"
        
        print(f"✅ All {len(jsonl_files)} JSONL files are valid (no corruption)")
    
    def test_log_cleanup_after_computation(self):
        """Test that logger cleanup works properly after multiprocessing."""
        r, n = 3, 7
        num_processes = 4
        
        # Run computation
        result = count_rectangles_parallel_ultra_bitwise(
            r, n,
            num_processes=num_processes,
            
        )
        
        assert result is not None
        
        # Verify logs exist
        log_dir = Path("logs")
        process_logs = list(log_dir.glob(f"parallel_{r}_{n}_process_*.log"))
        assert len(process_logs) > 0
        
        # Close logger
        close_logger()
        
        # Should be able to create new logger without issues
        new_logger = ProgressLogger("test_after_cleanup", log_dir=str(log_dir))
        new_logger.info("Test message after cleanup")
        new_logger.close_session()
        
        # Verify new log was created
        test_log = log_dir / "test_after_cleanup.log"
        assert test_log.exists()
        
        print(f"✅ Logger cleanup and recreation works correctly")


class TestMultiprocessLoggingEdgeCases:
    """Test edge cases in multiprocessing logging."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clean up any existing logs from previous tests
        self._cleanup_logs()
        close_logger()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clean up logs and ensure clean state
        self._cleanup_logs()
        close_logger()
    
    def _cleanup_logs(self):
        """Clean up log files from previous test runs."""
        import shutil
        from pathlib import Path
        log_dir = Path("logs")
        if log_dir.exists():
            # Clean up parallel computation logs
            for pattern in ["parallel_3_7*.log", "parallel_3_7*.jsonl"]:
                for log_file in log_dir.glob(pattern):
                    log_file.unlink(missing_ok=True)
            # Clean up test session logs  
            for pattern in ["test_*.log", "test_*.jsonl"]:
                for log_file in log_dir.glob(pattern):
                    log_file.unlink(missing_ok=True)
    
    def test_single_process_logging(self):
        """Test logging with num_processes=1 (edge case)."""
        r, n = 3, 7
        
        result = count_rectangles_parallel_ultra_bitwise(
            r, n,
            num_processes=1,
            
        )
        
        assert result is not None
        
        # Should still create logs even with single process
        log_dir = Path("logs")
        process_logs = list(log_dir.glob(f"parallel_{r}_{n}_process_*.log"))
        
        # Should have exactly 1 process log
        assert len(process_logs) == 1
        
        print(f"✅ Single process logging works correctly")
    
    def test_default_process_count(self):
        """Test logging with default (auto-detected) process count."""
        r, n = 3, 7
        
        # Don't specify num_processes - let it auto-detect
        result = count_rectangles_parallel_ultra_bitwise(
            r, n,
            num_processes=None,  # Auto-detect
            
        )
        
        assert result is not None
        
        # Should create logs for auto-detected number of processes
        log_dir = Path("logs")
        process_logs = list(log_dir.glob(f"parallel_{r}_{n}_process_*.log"))
        
        # Should have at least 1 process log, at most cpu_count or 8
        max_expected = min(mp.cpu_count(), 8)
        assert 1 <= len(process_logs) <= max_expected
        
        print(f"✅ Auto-detected {len(process_logs)} processes, created logs correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
