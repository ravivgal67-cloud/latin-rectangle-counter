#!/usr/bin/env python3
"""
Progress monitoring for parallel computations.

This module provides utilities to monitor progress across multiple processes
by reading their individual log files.
"""

import os
import time
import glob
from typing import List, Dict, Optional


def monitor_process_logs(r: int, n: int, num_processes: int, 
                        check_interval: int = 60) -> None:
    """
    Monitor progress logs from parallel processes.
    
    Args:
        r: Number of rows
        n: Number of columns  
        num_processes: Number of processes to monitor
        check_interval: How often to check logs (seconds)
    """
    log_pattern = f"logs/process_*_{r}_{n}.log"
    
    print(f"📊 Monitoring progress for ({r},{n}) with {num_processes} processes")
    print(f"   Checking logs every {check_interval} seconds")
    print(f"   Log pattern: {log_pattern}")
    
    start_time = time.time()
    last_check = start_time
    
    while True:
        current_time = time.time()
        
        if current_time - last_check >= check_interval:
            # Check all process log files
            log_files = glob.glob(log_pattern)
            
            if log_files:
                print(f"\n⏱️  Progress check at {time.strftime('%H:%M:%S')} ({current_time - start_time:.0f}s elapsed)")
                
                for log_file in sorted(log_files):
                    process_id = extract_process_id(log_file)
                    latest_progress = get_latest_progress(log_file)
                    
                    if latest_progress:
                        print(f"   Process {process_id}: {latest_progress}")
                    else:
                        print(f"   Process {process_id}: No progress yet")
            else:
                print(f"⏳ No process logs found yet at {time.strftime('%H:%M:%S')}")
            
            last_check = current_time
        
        time.sleep(5)  # Check every 5 seconds for new logs


def extract_process_id(log_file: str) -> int:
    """Extract process ID from log filename."""
    # Format: logs/process_X_r_n.log
    basename = os.path.basename(log_file)
    parts = basename.split('_')
    return int(parts[1])


def get_latest_progress(log_file: str) -> Optional[str]:
    """Get the latest progress message from a process log file."""
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Find the most recent progress or completion message
        for line in reversed(lines):
            if '⏱️' in line or '🏁' in line or '🚀' in line:
                # Extract just the message part (after the timestamp and process info)
                parts = line.strip().split(' - ', 2)
                if len(parts) >= 3:
                    return parts[2]
                else:
                    return line.strip()
        
        return None
    except (FileNotFoundError, IOError):
        return None


def get_process_summary(r: int, n: int) -> Dict[int, Dict]:
    """Get summary of all process progress."""
    log_pattern = f"logs/process_*_{r}_{n}.log"
    log_files = glob.glob(log_pattern)
    
    summary = {}
    
    for log_file in log_files:
        process_id = extract_process_id(log_file)
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Extract key information
            started = False
            completed = False
            latest_progress = None
            total_rectangles = None
            
            for line in lines:
                if '🚀 Starting' in line:
                    started = True
                elif '🏁 COMPLETED' in line:
                    completed = True
                    # Extract rectangle count
                    if 'rectangles' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'rectangles' in part and i > 0:
                                total_rectangles = parts[i-1].replace(',', '')
                                break
                elif '⏱️' in line:
                    latest_progress = line.strip()
            
            summary[process_id] = {
                'started': started,
                'completed': completed,
                'latest_progress': latest_progress,
                'total_rectangles': total_rectangles,
                'log_file': log_file
            }
            
        except (FileNotFoundError, IOError):
            summary[process_id] = {
                'started': False,
                'completed': False,
                'latest_progress': None,
                'total_rectangles': None,
                'log_file': log_file
            }
    
    return summary


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) >= 3:
        r = int(sys.argv[1])
        n = int(sys.argv[2])
        num_processes = int(sys.argv[3]) if len(sys.argv) > 3 else 8
        
        monitor_process_logs(r, n, num_processes)
    else:
        print("Usage: python core/progress_monitor.py <r> <n> [num_processes]")
        print("Example: python core/progress_monitor.py 6 7 8")