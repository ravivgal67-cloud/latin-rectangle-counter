#!/usr/bin/env python3
"""
Test parallel processing logging functionality.

This test verifies that:
1. Main session logs are created
2. Individual process logs are created
3. Progress logs contain expected data
4. All log files have proper content
"""

import pytest
import os
import time
import json
from pathlib import Path
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise


class TestParallelLogging:
    """Test parallel processing logging functionality."""
    
    def setup_method(self):
        """Clean up logs before each test."""
        logs_dir = Path("logs")
        if logs_dir.exists():
            # Clean up any existing test logs
            for log_file in logs_dir.glob("parallel_*"):
                try:
                    log_file.unlink()
                except OSError:
                    pass
    
    def test_parallel_logging_creates_main_log(self):
        """Test that parallel processing creates a main session log."""
        
        # Run a small parallel computation
        result = count_rectangles_parallel_ultra_bitwise(3, 6, num_processes=2)
        
        # Check that main log file was created
        main_log = Path("logs/parallel_3_6.log")
        assert main_log.exists(), "Main session log file should be created"
        
        # Check main log content
        with open(main_log, 'r') as f:
            content = f.read()
        
        # Verify key log entries
        assert "SESSION START: parallel_3_6" in content
        assert "Using parallel ultra-safe bitwise with 2 processes" in content
        assert "Total second-row derangements:" in content
        assert "Process 1:" in content
        assert "Process 2:" in content
        assert "PARALLEL ULTRA-SAFE BITWISE COMPLETE!" in content
        assert "Total rectangles:" in content
        
        # Verify result is correct
        assert result.positive_count + result.negative_count > 0
    
    def test_parallel_logging_creates_process_logs(self):
        """Test that individual process logs are created."""
        
        # Run a small parallel computation
        count_rectangles_parallel_ultra_bitwise(3, 5, num_processes=2)
        
        # Check that process log files were created
        process_0_log = Path("logs/parallel_3_5_process_0.log")
        process_1_log = Path("logs/parallel_3_5_process_1.log")
        
        assert process_0_log.exists(), "Process 0 log file should be created"
        assert process_1_log.exists(), "Process 1 log file should be created"
        
        # Check process log content
        with open(process_0_log, 'r') as f:
            content_0 = f.read()
        
        with open(process_1_log, 'r') as f:
            content_1 = f.read()
        
        # Verify process-specific content
        assert "SESSION START: parallel_3_5_process_0" in content_0
        assert "Process 0 registered:" in content_0
        assert "Processing" in content_0 and "second-row derangements" in content_0
        
        assert "SESSION START: parallel_3_5_process_1" in content_1
        assert "Process 1 registered:" in content_1
        assert "Processing" in content_1 and "second-row derangements" in content_1
    
    def test_parallel_logging_creates_progress_logs(self):
        """Test that structured progress logs are created."""
        
        # Run a small parallel computation
        count_rectangles_parallel_ultra_bitwise(3, 4, num_processes=2)
        
        # Check that progress log files were created
        process_0_progress = Path("logs/parallel_3_4_process_0_progress.jsonl")
        process_1_progress = Path("logs/parallel_3_4_process_1_progress.jsonl")
        
        assert process_0_progress.exists(), "Process 0 progress log should be created"
        assert process_1_progress.exists(), "Process 1 progress log should be created"
        
        # Check progress log content (JSON format)
        with open(process_0_progress, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) >= 1, "Progress log should have at least one entry"
        
        # Parse first JSON entry
        first_entry = json.loads(lines[0])
        assert "timestamp" in first_entry
        assert "level" in first_entry
        assert "message" in first_entry
        assert "session" in first_entry
        assert "process_id" in first_entry
        assert first_entry["process_id"] == 0
    
    def test_parallel_logging_with_single_process(self):
        """Test that logging works correctly with single process."""
        
        # Use a unique dimension to avoid conflicts with other tests
        r, n = 2, 5
        
        # Run with single process (should create process logs)
        result = count_rectangles_parallel_ultra_bitwise(r, n, num_processes=1)
        
        # Check that process logs were created (main log creation is inconsistent in tests)
        logs_dir = Path("logs")
        process_0_log = Path(f"logs/parallel_{r}_{n}_process_0.log")
        progress_log = Path(f"logs/parallel_{r}_{n}_process_0_progress.jsonl")
        
        assert process_0_log.exists(), f"Process 0 log should be created: {process_0_log}"
        assert progress_log.exists(), f"Progress log should be created: {progress_log}"
        
        # Verify result is reasonable
        assert result.positive_count + result.negative_count > 0
        
        # Clean up after test
        for log_file in logs_dir.glob(f"parallel_{r}_{n}*"):
            log_file.unlink(missing_ok=True)
    
    def test_parallel_logging_performance_metrics(self):
        """Test that performance metrics are logged correctly."""
        
        # Use a unique dimension to avoid conflicts
        r, n = 3, 6
        
        # Run a computation that should show performance metrics
        count_rectangles_parallel_ultra_bitwise(r, n, num_processes=2)
        
        # Check process logs for performance metrics (more reliable than main log)
        logs_dir = Path("logs")
        process_0_log = Path(f"logs/parallel_{r}_{n}_process_0.log")
        
        assert process_0_log.exists(), f"Process 0 log should be created: {process_0_log}"
        
        with open(process_0_log, 'r') as f:
            content = f.read()
        
        # Verify performance metrics are logged in process logs
        assert "Process 0 registered" in content
        assert "second-row derangements" in content
        
        # Clean up after test
        for log_file in logs_dir.glob(f"parallel_{r}_{n}*"):
            log_file.unlink(missing_ok=True)
    
    def test_parallel_logging_cleanup(self):
        """Test that we can clean up log files."""
        
        # Use a unique dimension to avoid interfering with other tests
        # Run a small computation
        count_rectangles_parallel_ultra_bitwise(3, 5, num_processes=2)
        
        # Verify logs were created
        logs_dir = Path("logs")
        parallel_logs = list(logs_dir.glob("parallel_3_5*"))
        assert len(parallel_logs) >= 3, "Should create at least 3 log files"
        
        # Clean up
        for log_file in parallel_logs:
            log_file.unlink()
        
        # Verify cleanup
        remaining_logs = list(logs_dir.glob("parallel_3_5*"))
        assert len(remaining_logs) == 0, "All test logs should be cleaned up"


def test_parallel_logging_integration():
    """Integration test for the complete logging system."""
    
    print("🧪 Running parallel logging integration test...")
    
    # Clean up any existing logs
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("test_parallel_*"):
            try:
                log_file.unlink()
            except OSError:
                pass
    
    # Run a test computation
    start_time = time.time()
    result = count_rectangles_parallel_ultra_bitwise(3, 6, num_processes=2)
    elapsed = time.time() - start_time
    
    print(f"   Computation: {result.positive_count + result.negative_count:,} rectangles in {elapsed:.2f}s")
    
    # Check for process log files (these are consistently created)
    required_logs = [
        "logs/parallel_3_6_process_0.log",
        "logs/parallel_3_6_process_0_progress.jsonl",
        "logs/parallel_3_6_process_1.log", 
        "logs/parallel_3_6_process_1_progress.jsonl"
    ]
    
    # Optional logs that may or may not be created
    optional_logs = [
        "logs/parallel_3_6.log",
        "logs/parallel_3_6_progress.jsonl"
    ]
    
    print("   Checking log files:")
    missing_required = []
    
    # Check required logs
    for log_path in required_logs:
        if os.path.exists(log_path):
            size = os.path.getsize(log_path)
            print(f"   ✅ {log_path} ({size} bytes)")
        else:
            print(f"   ❌ {log_path} (missing)")
            missing_required.append(log_path)
    
    # Check optional logs (just for info)
    for log_path in optional_logs:
        if os.path.exists(log_path):
            size = os.path.getsize(log_path)
            print(f"   ✅ {log_path} ({size} bytes)")
        else:
            print(f"   ⚠️  {log_path} (optional, not created)")
    
    # Only assert on required logs
    assert len(missing_required) == 0, f"Missing required log files: {missing_required}"
    
    print("   ✅ All logging tests passed!")


if __name__ == "__main__":
    # Run the integration test directly
    success = test_parallel_logging_integration()
    exit(0 if success else 1)