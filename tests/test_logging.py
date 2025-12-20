#!/usr/bin/env python3
"""
Comprehensive tests for the logging system.
Consolidated from test_logging_basic.py and test_logging_system.py to eliminate redundancy.
"""

import pytest
import tempfile
import shutil
import json
import time
import threading
from pathlib import Path

from core.logging_config import ProgressLogger, get_logger, close_logger


class TestProgressLogger:
    """Test the ProgressLogger class - consolidated from basic and system tests."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = ProgressLogger("test_session", log_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'logger'):
            self.logger.close_session()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        close_logger()
    
    def test_logger_initialization(self):
        """Test logger initialization and file creation."""
        log_dir = Path(self.temp_dir)
        
        # Check that log directory exists
        assert log_dir.exists()
        
        # Log a message to trigger file creation
        self.logger.info("Test message")
        
        # Check that log files are created
        session_log = log_dir / "test_session.log"
        progress_log = log_dir / "test_session_progress.jsonl"
        
        assert session_log.exists()
        assert progress_log.exists()
    
    def test_basic_log_levels(self):
        """Test basic logging functionality."""
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.debug("Debug message")
        
        # Check log file content
        log_file = Path(self.temp_dir) / "test_session.log"
        content = log_file.read_text()
        
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content
        # Debug messages might not appear depending on log level
    
    def test_structured_logging(self):
        """Test structured logging with additional data."""
        self.logger.info("Structured message", 
                        param1="value1", 
                        param2=123, 
                        param3={"nested": "data"})
        
        # Check JSON log file
        progress_file = Path(self.temp_dir) / "test_session_progress.jsonl"
        content = progress_file.read_text()
        
        # Should contain JSON line
        lines = [line for line in content.strip().split('\n') if line.strip()]
        assert len(lines) > 0
        
        json_data = json.loads(lines[-1])
        
        assert json_data["message"] == "Structured message"
        assert json_data["param1"] == "value1"
        assert json_data["param2"] == 123
        assert json_data["param3"] == {"nested": "data"}
    
    def test_process_registration(self):
        """Test process registration and tracking."""
        self.logger.register_process(0, 1000, "Test process")
        
        assert 0 in self.logger.process_progress
        progress = self.logger.process_progress[0]
        assert progress["total_work"] == 1000
        assert progress["description"] == "Test process"
        assert progress["status"] == "running"
    
    def test_process_progress_updates(self):
        """Test process progress updates."""
        self.logger.register_process(0, 1000, "Test process")
        
        # Update progress
        self.logger.update_process_progress(0, 250, {
            "rectangles_found": 50000,
            "positive_count": 25000,
            "negative_count": 25000
        })
        
        progress = self.logger.process_progress[0]
        assert progress["completed_work"] == 250
        assert progress["rectangles_found"] == 50000
        assert progress["positive_count"] == 25000
        assert progress["negative_count"] == 25000
    
    def test_process_completion(self):
        """Test process completion."""
        self.logger.register_process(0, 1000, "Test process")
        
        self.logger.complete_process(0, {
            "total_rectangles": 100000,
            "elapsed_time": 60.0
        })
        
        progress = self.logger.process_progress[0]
        assert progress["status"] == "completed"
        assert "end_time" in progress
    
    def test_computation_start_logging(self):
        """Test computation start logging."""
        self.logger.start_computation("test_computation", 
                                    r=5, n=7, num_processes=4)
        
        # Check that structured log contains computation info
        progress_file = Path(self.temp_dir) / "test_session_progress.jsonl"
        content = progress_file.read_text()
        
        lines = [line for line in content.strip().split('\n') if line.strip()]
        json_data = json.loads(lines[-1])
        
        assert json_data["computation_type"] == "test_computation"
        assert json_data["parameters"]["r"] == 5
        assert json_data["parameters"]["n"] == 7
        assert json_data["parameters"]["num_processes"] == 4
    
    def test_session_timing(self):
        """Test session timing functionality."""
        start_time = time.time()
        
        # Simulate some work
        time.sleep(0.1)
        
        self.logger.close_session()
        
        # Check session end log
        log_file = Path(self.temp_dir) / "test_session.log"
        content = log_file.read_text()
        
        assert "SESSION START" in content
        assert "SESSION END" in content
        assert "Total session time" in content
    
    def test_manual_progress_summary(self):
        """Test manual progress summary without threading."""
        # Register some processes
        for i in range(2):
            self.logger.register_process(i, 1000, f"Test process {i}")
            self.logger.update_process_progress(i, 500, {
                "rectangles_found": 10000 * (i + 1),
                "positive_count": 5000 * (i + 1),
                "negative_count": 5000 * (i + 1),
                "rate_rectangles_per_sec": 1000 * (i + 1)
            })
        
        # Manually trigger progress summary (no threading)
        self.logger._log_progress_summary()
        
        # Check that progress summary was logged
        log_file = Path(self.temp_dir) / "test_session.log"
        content = log_file.read_text()
        
        # Should contain progress summary
        assert "PROGRESS SUMMARY" in content
        assert "Thread 1:" in content
        assert "Thread 2:" in content
        assert "latin rectangles scanned" in content
    
    def test_progress_monitoring_thread(self):
        """Test progress monitoring thread functionality."""
        # Register some processes
        for i in range(3):
            self.logger.register_process(i, 1000, f"Process {i}")
            self.logger.update_process_progress(i, 500, {
                "rectangles_found": 10000 * (i + 1),
                "positive_count": 5000 * (i + 1),
                "negative_count": 5000 * (i + 1),
                "rate_rectangles_per_sec": 1000 * (i + 1)
            })
        
        # Start monitoring with very short interval for testing
        self.logger.start_progress_monitoring(interval_minutes=0.01)  # 0.6 seconds
        
        # Wait for at least one progress update
        time.sleep(1)
        
        # Stop monitoring
        self.logger.stop_progress_monitoring_flag = True
        
        # Check that progress summary was logged
        log_file = Path(self.temp_dir) / "test_session.log"
        content = log_file.read_text()
        
        # Should contain progress summary
        assert "PROGRESS SUMMARY" in content or "Thread" in content
    
    def test_log_rotation(self):
        """Test log rotation functionality."""
        # This is harder to test without generating large amounts of data
        # We'll just verify the handler is configured correctly
        file_handlers = [h for h in self.logger.logger.handlers 
                        if hasattr(h, 'maxBytes')]
        
        assert len(file_handlers) > 0
        handler = file_handlers[0]
        assert handler.maxBytes == 50 * 1024 * 1024  # 50MB
        assert handler.backupCount == 5
    
    def test_progress_summary_format(self):
        """Test progress summary format."""
        # Register and update processes
        for i in range(2):
            self.logger.register_process(i, 1000, f"Test process {i}")
            self.logger.update_process_progress(i, 500, {
                "rectangles_found": 10000,
                "positive_count": 5000,
                "negative_count": 5000,
                "rate_rectangles_per_sec": 1000
            })
        
        # Manually trigger progress summary
        self.logger._log_progress_summary()
        
        log_file = Path(self.temp_dir) / "test_session.log"
        content = log_file.read_text()
        
        # Should contain detailed thread information
        assert "PROGRESS SUMMARY" in content
        assert "Thread 1:" in content
        assert "Thread 2:" in content
        assert "latin rectangles scanned" in content
        assert "positive" in content
        assert "negative" in content


class TestGlobalLogger:
    """Test global logger functionality."""
    
    def teardown_method(self):
        """Clean up after each test."""
        close_logger()
        # Clean up any log files created by global logger tests
        log_dir = Path("logs")
        if log_dir.exists():
            # Only clean up test-specific logs, not production logs
            for pattern in ["test_global*.log", "test_global*.jsonl", 
                           "test_close*.log", "test_close*.jsonl",
                           "test_new*.log", "test_new*.jsonl"]:
                for log_file in log_dir.glob(pattern):
                    # Only remove if it's a test file (contains 'test_' in name)
                    if 'test_' in log_file.name:
                        log_file.unlink(missing_ok=True)
    
    def test_get_logger_singleton(self):
        """Test that get_logger returns singleton instance."""
        logger1 = get_logger("test_global")
        logger2 = get_logger("test_global")
        
        # Should be the same instance
        assert logger1 is logger2
    
    def test_close_logger(self):
        """Test global logger cleanup."""
        logger = get_logger("test_close")
        logger.info("Test message")
        
        close_logger()
        
        # Should be able to create new logger after closing
        new_logger = get_logger("test_new")
        assert new_logger is not logger


class TestLogFileFormats:
    """Test log file formats and content."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        close_logger()
    
    def test_session_log_format(self):
        """Test session log file format."""
        logger = ProgressLogger("format_test", log_dir=self.temp_dir)
        logger.info("Test message")
        logger.close_session()
        
        log_file = Path(self.temp_dir) / "format_test.log"
        content = log_file.read_text()
        
        lines = content.strip().split('\n')
        
        # Should have session start and end
        assert any("SESSION START" in line for line in lines)
        assert any("SESSION END" in line for line in lines)
        assert any("Test message" in line for line in lines)
        
        # Check timestamp format (should be readable)
        for line in lines:
            if "Test message" in line:
                # Should start with timestamp
                assert line.split(' - ')[0]  # Should not raise exception
    
    def test_json_log_format(self):
        """Test JSON log file format."""
        logger = ProgressLogger("json_test", log_dir=self.temp_dir)
        logger.info("JSON test", test_param=123)
        logger.close_session()
        
        json_file = Path(self.temp_dir) / "json_test_progress.jsonl"
        content = json_file.read_text()
        
        lines = [line for line in content.strip().split('\n') if line.strip()]
        
        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "timestamp" in data
            assert "level" in data
            assert "message" in data
            assert "session" in data
            assert "elapsed_time" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])