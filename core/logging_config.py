"""
Comprehensive logging system for Latin rectangle computations.

This module provides session-based logging with progress tracking for long-running
computations, especially parallel processing tasks.
"""

import logging
import logging.handlers
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json


class ProgressLogger:
    """
    Session-based logger with progress tracking for long-running computations.
    
    Features:
    - Session-based log files with timestamps
    - Progress updates every N minutes from parallel processes
    - Structured logging with JSON format for analysis
    - Thread-safe logging for multiprocessing environments
    - Automatic log rotation and cleanup
    """
    
    def __init__(self, session_name: str = None, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Generate session name if not provided
        if session_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"latin_rectangles_{timestamp}"
        
        self.session_name = session_name
        self.session_start = time.time()
        
        # Create loggers
        self._setup_loggers()
        
        # Progress tracking
        self.progress_lock = threading.Lock()
        self.process_progress: Dict[int, Dict[str, Any]] = {}
        
        # Start progress monitoring thread
        self.progress_thread = None
        self.stop_progress_monitoring_flag = False
        
    def _setup_loggers(self):
        """Set up main logger and progress logger."""
        
        # Main session logger
        self.logger = logging.getLogger(f"latin_rectangles.{self.session_name}")
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Console handler (for immediate feedback)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (detailed logs)
        log_file = self.log_dir / f"{self.session_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=50*1024*1024, backupCount=5  # 50MB max, 5 backups
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Progress logger (JSON format for analysis)
        progress_file = self.log_dir / f"{self.session_name}_progress.jsonl"
        self.progress_logger = logging.getLogger(f"progress.{self.session_name}")
        self.progress_logger.setLevel(logging.INFO)
        self.progress_logger.handlers.clear()
        
        progress_handler = logging.FileHandler(progress_file)
        progress_handler.setLevel(logging.INFO)
        progress_formatter = logging.Formatter('%(message)s')
        progress_handler.setFormatter(progress_formatter)
        self.progress_logger.addHandler(progress_handler)
        
        # Log session start
        self.logger.info(f"=== SESSION START: {self.session_name} ===")
        self.logger.info(f"Log directory: {self.log_dir.absolute()}")
        
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data."""
        self.logger.info(message)
        if kwargs:
            self._log_structured("INFO", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data."""
        self.logger.debug(message)
        if kwargs:
            self._log_structured("DEBUG", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data."""
        self.logger.warning(message)
        if kwargs:
            self._log_structured("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data."""
        self.logger.error(message)
        if kwargs:
            self._log_structured("ERROR", message, **kwargs)
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log structured data in JSON format."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "session": self.session_name,
            "elapsed_time": time.time() - self.session_start,
            **kwargs
        }
        self.progress_logger.info(json.dumps(log_entry))
    
    def start_computation(self, computation_type: str, **params):
        """Log the start of a computation with parameters."""
        self.info(f"🚀 Starting {computation_type}", 
                 computation_type=computation_type, 
                 parameters=params)
    
    def register_process(self, process_id: int, total_work: int, description: str = ""):
        """Register a process for progress tracking."""
        with self.progress_lock:
            self.process_progress[process_id] = {
                "total_work": total_work,
                "completed_work": 0,
                "description": description,
                "start_time": time.time(),
                "last_update": time.time(),
                "status": "running"
            }
        
        self.info(f"📋 Process {process_id} registered: {description}",
                 process_id=process_id,
                 total_work=total_work,
                 description=description)
    
    def update_process_progress(self, process_id: int, completed_work: int, 
                              additional_info: Dict[str, Any] = None):
        """Update progress for a specific process."""
        with self.progress_lock:
            if process_id in self.process_progress:
                progress = self.process_progress[process_id]
                progress["completed_work"] = completed_work
                progress["last_update"] = time.time()
                
                # Store additional info (rectangles_found, positive_count, etc.)
                if additional_info:
                    progress.update(additional_info)
                
                # Calculate progress percentage
                pct = (completed_work / progress["total_work"]) * 100 if progress["total_work"] > 0 else 0
                elapsed = time.time() - progress["start_time"]
                rate = completed_work / elapsed if elapsed > 0 else 0
                
                # Enhanced debug logging with rectangle details
                rectangles_found = additional_info.get("rectangles_found", 0) if additional_info else 0
                positive_count = additional_info.get("positive_count", 0) if additional_info else 0
                negative_count = additional_info.get("negative_count", 0) if additional_info else 0
                
                if rectangles_found > 0:
                    self.debug(f"Thread {process_id + 1} progress: {rectangles_found:,} rectangles "
                             f"(+{positive_count:,} -{negative_count:,}) - {pct:.1f}% work units",
                             process_id=process_id,
                             progress_pct=pct,
                             completed_work=completed_work,
                             rectangles_found=rectangles_found,
                             positive_count=positive_count,
                             negative_count=negative_count,
                             rate=rate,
                             elapsed_time=elapsed)
                else:
                    self.debug(f"Process {process_id} progress: {pct:.1f}% ({completed_work:,}/{progress['total_work']:,})",
                             process_id=process_id,
                             progress_pct=pct,
                             completed_work=completed_work,
                             total_work=progress["total_work"],
                             rate=rate,
                             elapsed_time=elapsed)
    
    def complete_process(self, process_id: int, final_results: Dict[str, Any] = None):
        """Mark a process as completed."""
        with self.progress_lock:
            if process_id in self.process_progress:
                progress = self.process_progress[process_id]
                progress["status"] = "completed"
                progress["end_time"] = time.time()
                elapsed = progress["end_time"] - progress["start_time"]
                
                self.info(f"✅ Process {process_id} completed in {elapsed:.2f}s",
                         process_id=process_id,
                         elapsed_time=elapsed,
                         final_results=final_results or {})
    
    def start_progress_monitoring(self, interval_minutes: int = 1):
        """Start background thread for periodic progress updates."""
        if self.progress_thread is not None:
            return  # Already running
        
        def monitor_progress():
            while not self.stop_progress_monitoring_flag:
                time.sleep(interval_minutes * 60)  # Convert to seconds
                if not self.stop_progress_monitoring_flag:
                    self._log_progress_summary()
        
        self.progress_thread = threading.Thread(target=monitor_progress, daemon=True)
        self.progress_thread.start()
        
        self.info(f"📊 Started progress monitoring (updates every {interval_minutes} minutes)")
    
    def _log_progress_summary(self):
        """Log a detailed summary of all process progress."""
        with self.progress_lock:
            if not self.process_progress:
                return
            
            session_elapsed = time.time() - self.session_start
            session_hours = int(session_elapsed // 3600)
            session_minutes = int((session_elapsed % 3600) // 60)
            session_seconds = int(session_elapsed % 60)
            
            self.info(f"📊 PROGRESS SUMMARY - Session time: {session_hours:02d}:{session_minutes:02d}:{session_seconds:02d}")
            
            for process_id, progress in self.process_progress.items():
                if progress["status"] == "running":
                    elapsed = time.time() - progress["start_time"]
                    hours = int(elapsed // 3600)
                    minutes = int((elapsed % 3600) // 60)
                    seconds = int(elapsed % 60)
                    
                    # Get additional info from progress data
                    rectangles_found = progress.get("rectangles_found", 0)
                    positive_count = progress.get("positive_count", 0)
                    negative_count = progress.get("negative_count", 0)
                    rate = progress.get("rate_rectangles_per_sec", 0)
                    
                    # Format the detailed progress message
                    thread_name = f"Thread {process_id + 1}"
                    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    if rectangles_found > 0:
                        self.info(f"   {thread_name}: After {time_str} - {rectangles_found:,} latin rectangles scanned, "
                                f"{positive_count:,} positive, {negative_count:,} negative (rate: {rate:,.0f} rect/s)")
                    else:
                        # Fallback for basic progress tracking
                        pct = (progress["completed_work"] / progress["total_work"]) * 100 if progress["total_work"] > 0 else 0
                        self.info(f"   {thread_name}: After {time_str} - {progress['completed_work']:,}/{progress['total_work']:,} "
                                f"work units completed ({pct:.1f}%)")
            
            # Log structured data for analysis
            summary = {
                "session_elapsed": session_elapsed,
                "processes": {}
            }
            
            for process_id, progress in self.process_progress.items():
                if progress["status"] == "running":
                    summary["processes"][process_id] = {
                        "elapsed": time.time() - progress["start_time"],
                        "rectangles_found": progress.get("rectangles_found", 0),
                        "positive_count": progress.get("positive_count", 0),
                        "negative_count": progress.get("negative_count", 0),
                        "rate": progress.get("rate_rectangles_per_sec", 0)
                    }
            
            if summary["processes"]:
                self._log_structured("INFO", "Progress Summary", **summary)
    
    def stop_progress_monitoring(self):
        """Stop the progress monitoring thread."""
        self.stop_progress_monitoring_flag = True
        if self.progress_thread:
            self.progress_thread.join(timeout=5)
    
    def close_session(self):
        """Close the logging session."""
        self.stop_progress_monitoring_flag = True
        if self.progress_thread:
            self.progress_thread.join(timeout=5)
        
        session_elapsed = time.time() - self.session_start
        self.info(f"=== SESSION END: {self.session_name} ===")
        self.info(f"Total session time: {session_elapsed:.2f}s")
        
        # Close handlers
        for handler in self.logger.handlers:
            handler.close()
        for handler in self.progress_logger.handlers:
            handler.close()


# Global logger instance
_global_logger: Optional[ProgressLogger] = None

def get_logger(session_name: str = None) -> ProgressLogger:
    """Get or create the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = ProgressLogger(session_name)
    return _global_logger

def close_logger():
    """Close the global logger instance."""
    global _global_logger
    if _global_logger:
        _global_logger.close_session()
        _global_logger = None