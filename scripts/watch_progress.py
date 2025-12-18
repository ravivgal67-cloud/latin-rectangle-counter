#!/usr/bin/env python3
"""
Watch live computation progress from log files.
Usage: python watch_progress.py [--loop]
"""

import time
import sys
from datetime import datetime
import os
import sys

# Add the parent directory to the path so we can import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.log_progress_reader import get_progress_from_logs, is_computation_active

def format_number(n):
    """Format number with commas."""
    return f"{n:,}"

def clear_lines(n):
    """Clear n lines by moving cursor up and clearing."""
    for _ in range(n):
        sys.stdout.write('\033[F')  # Move cursor up
        sys.stdout.write('\033[K')  # Clear line

def watch_progress(loop=False):
    """Monitor computation progress from log files in real-time."""
    if loop:
        print("Watching Latin Rectangle Counter progress from logs...")
        print("Press Ctrl+C to stop\n")
    
    lines_printed = 0
    
    try:
        while True:
            # Clear previous output if looping
            if loop and lines_printed > 0:
                clear_lines(lines_printed)
            
            lines_printed = 0
            
            try:
                # Get progress from log files
                progress_entries = get_progress_from_logs()
                active = is_computation_active()
                
                if progress_entries:
                    header = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Computations from Logs:"
                    print(header)
                    lines_printed += 1
                    
                    if active:
                        print("🔄 Active computations detected")
                        lines_printed += 1
                    else:
                        print("💤 No recent activity (computations may be complete)")
                        lines_printed += 1
                    
                    separator = "=" * 90
                    print(separator)
                    lines_printed += 1
                    
                    for entry in progress_entries:
                        r = entry['r']
                        n = entry['n']
                        scanned = entry['rectangles_scanned']
                        pos = entry['positive_count']
                        neg = entry['negative_count']
                        complete = entry['is_complete']
                        updated_at = entry['last_update']
                        process_id = entry['process_id']
                        
                        status = "✅ COMPLETE" if complete else "⏳ COMPUTING"
                        diff = pos - neg
                        
                        print(f"\n({r},{n}): {status} [{process_id}]")
                        lines_printed += 2
                        print(f"  Scanned:  {format_number(scanned)}")
                        lines_printed += 1
                        print(f"  Positive: {format_number(pos)}")
                        lines_printed += 1
                        print(f"  Negative: {format_number(neg)}")
                        lines_printed += 1
                        print(f"  Diff:     {format_number(diff)}")
                        lines_printed += 1
                        print(f"  Updated:  {updated_at}")
                        lines_printed += 1
                        
                        # Show progress percentage if available
                        if 'progress_pct' in entry:
                            print(f"  Progress: {entry['progress_pct']:.1f}%")
                            lines_printed += 1
                else:
                    msg = f"[{datetime.now().strftime('%H:%M:%S')}] No computation logs found"
                    print(msg)
                    lines_printed += 1
                
            except Exception as e:
                print(f"Error reading logs: {e}")
                lines_printed += 1
            
            if not loop:
                break
                
            time.sleep(5)  # Update every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)

if __name__ == "__main__":
    loop_mode = "--loop" in sys.argv
    watch_progress(loop=loop_mode)
