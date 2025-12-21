#!/usr/bin/env python3
"""
Fresh test for (5,8) computation with enhanced inner-loop progress reporting.
"""

import time
from core.parallel_ultra_bitwise import count_rectangles_parallel_ultra_bitwise

def main():
    print("🚀 Starting fresh (5,8) test with enhanced progress reporting...")
    print("Using 2 processes to make it easier to monitor")
    print("Watch for progress messages in both console and log files")
    
    start_time = time.time()
    
    try:
        result = count_rectangles_parallel_ultra_bitwise(
            r=5, 
            n=8, 
            num_processes=2, 
            logger_session="fresh_5_8"
        )
        
        elapsed = time.time() - start_time
        print(f"\n✅ COMPLETED in {elapsed:.2f}s")
        print(f"Result: {result}")
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n⏹️ Test interrupted after {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Error after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()