#!/usr/bin/env python3
"""
Test parallel processing with enhanced logging.
This will test a computation that should trigger parallel processing
and show per-process progress in the logs.
"""

import time
from core.auto_counter import count_rectangles_auto

def test_parallel_logging():
    """Test parallel processing with logging for (6,7)."""
    
    print("🚀 Testing parallel processing with enhanced logging")
    print("   This will use parallel processing and log per-process progress")
    print("   Check logs/ directory for detailed progress logs")
    print()
    
    # Test (6,7) - should trigger parallel processing
    r, n = 6, 7
    print(f"Computing ({r},{n}) - this should use parallel processing...")
    
    start_time = time.time()
    result = count_rectangles_auto(r, n, num_processes=4)  # Force 4 processes for testing
    elapsed = time.time() - start_time
    
    print(f"\n✅ Computation complete!")
    print(f"   Result: {result.positive_count + result.negative_count:,} rectangles")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   From cache: {result.from_cache}")
    
    print(f"\n📋 Check the log files in logs/ directory:")
    print(f"   - Main session log: logs/web_session.log")
    print(f"   - Progress log: logs/web_session_progress.jsonl")
    print(f"   - Parallel computation logs: logs/parallel_{r}_{n}*.log")

if __name__ == "__main__":
    test_parallel_logging()