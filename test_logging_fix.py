#!/usr/bin/env python3
"""
Test the fixed logging system with a small parallel computation.
"""

import time
from core.auto_counter import count_rectangles_auto

def test_logging():
    """Test logging with a small parallel computation."""
    
    print("🧪 Testing fixed logging system")
    print("   This will run a small computation and check logging")
    
    # Test (4,7) - should trigger parallel processing but be quick
    r, n = 4, 7
    print(f"\nComputing ({r},{n}) with forced parallel processing...")
    
    start_time = time.time()
    result = count_rectangles_auto(r, n, num_processes=2, force_parallel=True)
    elapsed = time.time() - start_time
    
    print(f"\n✅ Computation complete!")
    print(f"   Result: {result.positive_count + result.negative_count:,} rectangles")
    print(f"   Time: {elapsed:.2f}s")
    
    # Check log files
    import os
    log_files = os.listdir("logs")
    print(f"\n📋 Log files created:")
    for log_file in sorted(log_files):
        if log_file.endswith('.log') or log_file.endswith('.jsonl'):
            print(f"   - {log_file}")
    
    # Show recent log entries
    print(f"\n📖 Recent log entries from web_session.log:")
    try:
        with open("logs/web_session.log", "r") as f:
            lines = f.readlines()
            for line in lines[-10:]:  # Last 10 lines
                print(f"   {line.strip()}")
    except FileNotFoundError:
        print("   No log file found")

if __name__ == "__main__":
    test_logging()