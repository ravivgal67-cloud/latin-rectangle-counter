#!/usr/bin/env python3
"""
Test (5,8) computation with enhanced progress reporting.
"""

import time
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise

def test_5_8_with_progress():
    print("Testing (5,8) computation with enhanced progress reporting...")
    print("This will run for a few minutes to test progress reporting.")
    print("Watch the logs/parallel_5_8_process_*.log files for progress updates.")
    
    start_time = time.time()
    
    try:
        # Run for a limited time to test progress reporting
        result = count_rectangles_parallel_ultra_bitwise(5, 8, num_processes=2, logger_session="test_5_8")
        print(f"✅ Completed: {result}")
    except KeyboardInterrupt:
        print("⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    elapsed = time.time() - start_time
    print(f"Test ran for {elapsed:.1f} seconds")

if __name__ == "__main__":
    test_5_8_with_progress()