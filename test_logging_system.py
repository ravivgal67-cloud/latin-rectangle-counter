#!/usr/bin/env python3
"""
Test script for the comprehensive logging system.
"""

import time
from core.logged_parallel_generation import count_rectangles_parallel_logged
from core.logging_config import close_logger


def test_logging_system():
    """Test the logging system with a small computation."""
    print("🧪 Testing comprehensive logging system...")
    
    # Test 1: Small parallel computation with logging
    print("\n1️⃣ Testing (3,7) with 2 processes and logging:")
    result = count_rectangles_parallel_logged(3, 7, num_processes=2, session_name="test_small_parallel")
    print(f"   Result: {result.positive_count + result.negative_count:,} rectangles in {result.computation_time:.3f}s")
    
    # Test 2: Sequential computation with logging
    print("\n2️⃣ Testing (4,6) sequential with logging:")
    result = count_rectangles_parallel_logged(4, 6, session_name="test_sequential")
    print(f"   Result: {result.positive_count + result.negative_count:,} rectangles in {result.computation_time:.3f}s")
    
    print("\n✅ Logging system test completed!")
    print("📁 Check the 'logs/' directory for detailed log files")
    
    # Close logger
    close_logger()


if __name__ == "__main__":
    test_logging_system()