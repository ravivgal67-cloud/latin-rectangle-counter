#!/usr/bin/env python3
"""
Basic test for the logging system without parallel dependencies.
"""

import time
import threading
from core.logging_config import get_logger, close_logger


def simulate_long_computation():
    """Simulate a long computation with progress updates."""
    logger = get_logger("test_basic_logging")
    
    logger.start_computation("simulated_computation", 
                           problem_size="(5,7)", 
                           num_processes=8)
    
    # Start progress monitoring
    logger.start_progress_monitoring(interval_minutes=1)  # 1 minute for testing
    
    # Simulate 8 processes
    for process_id in range(8):
        logger.register_process(process_id, 1000, f"Process {process_id+1} simulation")
    
    # Simulate work progress
    for step in range(100):
        time.sleep(0.1)  # Simulate work
        
        # Update progress for all processes
        for process_id in range(8):
            completed = step * 10 + process_id
            if completed <= 1000:
                logger.update_process_progress(
                    process_id, completed,
                    {"rectangles_found": completed * 1000, "rate": completed * 10}
                )
        
        if step % 20 == 0:
            logger.info(f"Simulation step {step}/100 completed")
    
    # Complete all processes
    for process_id in range(8):
        logger.complete_process(process_id, {
            "total_rectangles": 1000000,
            "elapsed_time": 10.0 + process_id
        })
    
    logger.info("🎯 Simulation completed successfully!")
    
    # Stop monitoring and close
    logger.stop_progress_monitoring()
    close_logger()


def test_basic_logging():
    """Test basic logging functionality."""
    print("🧪 Testing basic logging system...")
    
    logger = get_logger("test_basic")
    
    logger.info("Testing basic logging functionality")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    
    logger.info("Testing structured logging", 
               test_param=123, 
               test_data={"key": "value"})
    
    print("✅ Basic logging test completed!")
    print("📁 Check the 'logs/' directory for log files")
    
    close_logger()


if __name__ == "__main__":
    print("1. Testing basic logging...")
    test_basic_logging()
    
    print("\n2. Testing simulated long computation...")
    simulate_long_computation()
    
    print("\n✅ All logging tests completed!")
    print("📁 Check the 'logs/' directory for detailed log files")