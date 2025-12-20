#!/usr/bin/env python3
"""
Base test class for Latin Rectangle Counter tests.

Provides common functionality like test-specific log directories
and proper cleanup to avoid interfering with production logs.
"""

import tempfile
import shutil
from pathlib import Path
from core.logging_config import close_logger


class TestBase:
    """Base class for tests that need logging functionality."""
    
    def setup_method(self):
        """Set up test environment with isolated log directory."""
        # Create test-specific temporary log directory
        self.test_log_dir = Path(tempfile.mkdtemp(prefix="test_logs_"))
        
        # Store original log directory for restoration if needed
        self._original_log_dir = Path("logs")
    
    def teardown_method(self):
        """Clean up test environment."""
        # Close any open loggers
        close_logger()
        
        # Clean up test log directory
        if hasattr(self, 'test_log_dir') and self.test_log_dir.exists():
            shutil.rmtree(self.test_log_dir, ignore_errors=True)
    
    def get_test_log_dir(self) -> str:
        """Get the test-specific log directory path."""
        return str(self.test_log_dir)


class TestBaseWithProductionLogs:
    """Base class for tests that need to use production log directory but clean up properly."""
    
    def setup_method(self):
        """Set up test environment."""
        self.production_log_dir = Path("logs")
        # Store list of existing log files to avoid cleaning them
        self._existing_logs = set()
        if self.production_log_dir.exists():
            self._existing_logs = {f.name for f in self.production_log_dir.iterdir() if f.is_file()}
    
    def teardown_method(self):
        """Clean up test environment - only remove logs created during test."""
        close_logger()
        
        # Only clean up logs that were created during this test
        if self.production_log_dir.exists():
            current_logs = {f.name for f in self.production_log_dir.iterdir() if f.is_file()}
            test_created_logs = current_logs - self._existing_logs
            
            for log_name in test_created_logs:
                log_file = self.production_log_dir / log_name
                try:
                    log_file.unlink(missing_ok=True)
                except (OSError, PermissionError):
                    # If we can't delete the file, just continue
                    pass