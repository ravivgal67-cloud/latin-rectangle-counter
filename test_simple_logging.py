#!/usr/bin/env python3
"""
Simple test of parallel processing with logging - no web involved.
"""

import time
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise

def test_simple_logging():
    """Test parallel processing with logging."""
    
    print("🧪 Testing parallel processing with logging (no web)")
    print("   This will test a small parallel computation")
    
    # Test (4,7) - should be quick but use parallel processing
    r, n = 4, 7
    print(f"\nComputing ({r},{n}) with 2 processes...")
    
    start_time = time.time()
    result = count_rectangles_parallel_ultra_bitwise(r, n, num_processes=2)
    elapsed = time.time() - start_time
    
    print(f"\n✅ Computation complete!")
    print(f"   Result: {result.positive_count + result.negative_count:,} rectangles")
    print(f"   Time: {elapsed:.2f}s")
    
    # Check log files
    import os
    print(f"\n📋 Log files created:")
    if os.path.exists("logs"):
        log_files = os.listdir("logs")
        for log_file in sorted(log_files):
            if log_file.endswith('.log') or log_file.endswith('.jsonl'):
                print(f"   - {log_file}")
                
                # Show content of process logs
                if 'process' in log_file:
                    try:
                        with open(f"logs/{log_file}", "r") as f:
                            content = f.read().strip()
                            if content:
                                print(f"     Content: {content}")
                    except Exception:
                        pass
    else:
        print("   No logs directory found")

if __name__ == "__main__":
    test_simple_logging()