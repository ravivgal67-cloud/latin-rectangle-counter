# Comprehensive Logging System

## Overview

The Latin Rectangle Counter includes a comprehensive logging system designed for long-running computations, especially parallel processing tasks. The system provides session-based logging with detailed progress tracking, structured data logging, and crash recovery information.

## Key Features

- **Session-based logging** with unique timestamps
- **Detailed progress tracking** for parallel processes
- **Structured JSON logging** for analysis and monitoring
- **Thread-safe logging** for multiprocessing environments
- **Automatic log rotation** and cleanup
- **Real-time progress monitoring** with configurable intervals
- **Crash recovery information** to resume interrupted computations

## Architecture

### Core Components

- **`core/logging_config.py`**: Main logging infrastructure with `ProgressLogger` class
- **`core/logged_parallel_generation.py`**: Parallel processing wrapper with integrated logging
- **`logs/`**: Directory containing all log files (auto-created)

### Log File Types

1. **Session Logs** (`{session_name}.log`): Detailed human-readable logs
2. **Progress Logs** (`{session_name}_progress.jsonl`): Structured JSON data for analysis
3. **Process Logs** (`{session_name}_process_{id}.log`): Individual process logs

## Usage

### Basic Logging

```python
from core.logging_config import get_logger, close_logger

# Create a logger for your session
logger = get_logger("my_computation")

# Log different types of messages
logger.info("Starting computation")
logger.warning("This is a warning")
logger.error("An error occurred")

# Structured logging with additional data
logger.info("Computation started", 
           problem_size="(5,7)", 
           num_processes=8,
           estimated_time=3600)

# Close the logger when done
close_logger()
```

### Parallel Processing with Logging

```python
from core.logged_parallel_generation import count_rectangles_parallel_logged

# Run parallel computation with comprehensive logging
result = count_rectangles_parallel_logged(
    r=5, n=7, 
    num_processes=8,
    session_name="large_computation_20241217"
)

print(f"Result: {result.positive_count + result.negative_count:,} rectangles")
```

### Progress Monitoring

```python
from core.logging_config import get_logger

logger = get_logger("progress_test")

# Start automatic progress monitoring (updates every 10 minutes)
logger.start_progress_monitoring(interval_minutes=10)

# Register processes for tracking
for i in range(8):
    logger.register_process(i, total_work=1000, description=f"Process {i+1}")

# Update progress during computation
logger.update_process_progress(
    process_id=0, 
    completed_work=250,
    additional_info={
        "rectangles_found": 1250000,
        "positive_count": 625500,
        "negative_count": 624500,
        "rate_rectangles_per_sec": 50000
    }
)

# Complete processes
logger.complete_process(0, {"total_rectangles": 5000000})
```

## Progress Monitoring Output

The system provides detailed progress updates showing:

```
📊 PROGRESS SUMMARY - Session time: 01:23:45
   Thread 1: After 01:20:30 - 2,450,000 latin rectangles scanned, 1,225,500 positive, 1,224,500 negative (rate: 50,000 rect/s)
   Thread 2: After 01:20:28 - 2,380,000 latin rectangles scanned, 1,165,400 positive, 1,214,600 negative (rate: 48,000 rect/s)
   Thread 3: After 01:20:32 - 2,520,000 latin rectangles scanned, 1,310,400 positive, 1,209,600 negative (rate: 52,000 rect/s)
   Thread 4: After 01:20:29 - 2,350,000 latin rectangles scanned, 1,128,000 positive, 1,222,000 negative (rate: 47,000 rect/s)
```

## Log File Structure

### Session Log Format
```
2025-12-17 10:30:15 - INFO - === SESSION START: large_computation_20241217 ===
2025-12-17 10:30:15 - INFO - 🚀 Starting parallel_latin_rectangles
2025-12-17 10:30:15 - INFO - 🚀 Using row-based parallel processing with 8 processes
2025-12-17 10:30:16 - INFO - 📋 Process 0 registered: Processing 231 second-row permutations
...
2025-12-17 11:45:32 - INFO - ✅ Process 1/8 complete: 19,340,224 rectangles (+9,701,072 -9,639,152) in 4532.5s
2025-12-17 12:15:45 - INFO - === SESSION END: large_computation_20241217 ===
```

### Structured JSON Log Format
```json
{"timestamp": "2025-12-17T10:30:15.123456", "level": "INFO", "message": "🚀 Starting parallel_latin_rectangles", "session": "large_computation_20241217", "elapsed_time": 0.001, "computation_type": "parallel_latin_rectangles", "parameters": {"r": 5, "n": 7, "num_processes": 8}}
{"timestamp": "2025-12-17T10:40:15.789012", "level": "INFO", "message": "Progress Summary", "session": "large_computation_20241217", "elapsed_time": 600.0, "processes": {"0": {"elapsed": 600, "rectangles_found": 1500000, "positive_count": 750000, "negative_count": 750000, "rate": 2500}}}
```

## Configuration

### Log Levels
- **DEBUG**: Detailed progress updates and internal operations
- **INFO**: General information and progress summaries
- **WARNING**: Non-critical issues and warnings
- **ERROR**: Errors and exceptions

### Progress Monitoring Intervals
- **Default**: 10 minutes for production computations
- **Testing**: 30 seconds to 1 minute for development
- **Long computations**: 5-15 minutes depending on expected duration

### Log Rotation
- **File size limit**: 50MB per log file
- **Backup count**: 5 backup files retained
- **Automatic cleanup**: Old logs rotated automatically

## Crash Recovery

The logging system provides detailed information for crash recovery:

1. **Last known progress** for each process
2. **Exact timing** of when each process was last active
3. **Intermediate results** showing partial computation state
4. **Process configuration** for restarting with same parameters

### Recovery Information Example
```
Thread 3: After 01:15:23 - 2,100,000 latin rectangles scanned, 1,050,500 positive, 1,049,500 negative
Last update: 2025-12-17 11:45:23
Status: running (process may have crashed after this point)
```

## Performance Impact

The logging system is designed for minimal performance impact:

- **Asynchronous logging**: Non-blocking log writes
- **Efficient JSON serialization**: Fast structured data logging
- **Configurable verbosity**: Adjust detail level based on needs
- **Memory efficient**: Streaming logs to disk, minimal memory usage

### Benchmarks
- **Logging overhead**: < 1% of computation time
- **Memory usage**: < 10MB for typical sessions
- **Disk usage**: ~1-5MB per hour of computation

## Integration with Existing Code

The logging system integrates seamlessly with existing parallel processing:

```python
# Before: Basic parallel processing
from core.parallel_generation import count_rectangles_parallel
result = count_rectangles_parallel(5, 7, num_processes=8)

# After: Parallel processing with comprehensive logging
from core.logged_parallel_generation import count_rectangles_parallel_logged
result = count_rectangles_parallel_logged(5, 7, num_processes=8, session_name="my_computation")
```

## Best Practices

### Session Naming
- Use descriptive names: `"latin_5x7_optimization_20241217"`
- Include date/time for uniqueness
- Avoid special characters and spaces

### Progress Monitoring
- Use appropriate intervals (10+ minutes for long computations)
- Include meaningful additional_info in progress updates
- Register processes with descriptive names

### Log Analysis
- Use structured JSON logs for automated analysis
- Monitor progress logs for performance trends
- Check session logs for error diagnosis

### Cleanup
- Regularly archive old log files
- Monitor disk usage in logs directory
- Use log rotation settings appropriately

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure write access to logs directory
2. **Disk space**: Monitor available space for log files
3. **Process hanging**: Check progress logs for last activity
4. **Memory issues**: Reduce logging verbosity if needed

### Debug Mode
```python
# Enable debug logging for detailed information
logger = get_logger("debug_session")
logger.logger.setLevel(logging.DEBUG)
```

## Future Enhancements

- **Web dashboard** for real-time monitoring
- **Email alerts** for long-running computations
- **Log analysis tools** for performance optimization
- **Distributed logging** for multi-machine computations
- **Integration with monitoring systems** (Prometheus, Grafana)

## Examples

See the following test files for complete examples:
- `test_logging_basic.py`: Basic logging functionality
- `test_progress_monitoring.py`: Enhanced progress monitoring
- `test_logging_system.py`: Complete integration test