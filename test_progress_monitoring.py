#!/usr/bin/env python3
"""
Test enhanced progress monitoring with detailed per-thread information.
"""

import time
from core.logging_config import get_logger, close_logger


def test_enhanced_progress_monitoring():
    """Test the enhanced progress monitoring with detailed thread information."""
    print("🧪 Testing enhanced progress monitoring...")
    
    logger = get_logger("test_progress_monitoring")
    
    logger.start_computation("enhanced_progress_test", 
                           problem_size="(5,7)", 
                           num_processes=4)
    
    # Start progress monitoring with shorter interval for testing
    logger.start_progress_monitoring(interval_minutes=0.5)  # 30 seconds for testing
    
    # Simulate 4 threads working on Latin rectangles
    thread_data = [
        {"name": "Thread 1", "rate": 50000, "positive_ratio": 0.51},
        {"name": "Thread 2", "rate": 48000, "positive_ratio": 0.49},
        {"name": "Thread 3", "rate": 52000, "positive_ratio": 0.52},
        {"name": "Thread 4", "rate": 47000, "positive_ratio": 0.48},
    ]
    
    # Register processes
    for i, thread in enumerate(thread_data):
        logger.register_process(i, 1000, f"{thread['name']} - Latin rectangle computation")
    
    logger.info("🚀 Starting simulated Latin rectangle computation with 4 threads")
    
    # Simulate 2 minutes of work with progress updates
    total_steps = 120  # 2 minutes in seconds
    for step in range(total_steps):
        time.sleep(1)  # 1 second per step
        
        # Update progress for each thread
        for i, thread in enumerate(thread_data):
            # Simulate rectangles found based on thread rate
            rectangles_this_second = thread["rate"] + (step * 10)  # Increasing rate
            total_rectangles = rectangles_this_second * (step + 1)
            positive_count = int(total_rectangles * thread["positive_ratio"])
            negative_count = total_rectangles - positive_count
            
            # Update progress (work units completed)
            work_completed = min(step * 8, 1000)  # Simulate work units
            
            logger.update_process_progress(
                i, work_completed,
                {
                    "rectangles_found": total_rectangles,
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "rate_rectangles_per_sec": rectangles_this_second
                }
            )
        
        # Log milestone updates
        if step % 30 == 0 and step > 0:
            logger.info(f"⏱️  Milestone: {step} seconds elapsed")
    
    # Complete all processes
    for i, thread in enumerate(thread_data):
        final_rectangles = thread["rate"] * total_steps
        final_positive = int(final_rectangles * thread["positive_ratio"])
        final_negative = final_rectangles - final_positive
        
        logger.complete_process(i, {
            "total_rectangles": final_rectangles,
            "positive_count": final_positive,
            "negative_count": final_negative,
            "elapsed_time": total_steps,
            "average_rate": thread["rate"]
        })
    
    logger.info("🎯 Enhanced progress monitoring test completed!")
    
    # Wait a bit to see final progress summary
    time.sleep(35)  # Wait for one more progress update
    
    # Stop monitoring and close
    logger.stop_progress_monitoring_flag = True
    close_logger()


if __name__ == "__main__":
    test_enhanced_progress_monitoring()
    print("✅ Enhanced progress monitoring test completed!")
    print("📁 Check logs/test_progress_monitoring.log for detailed thread progress")