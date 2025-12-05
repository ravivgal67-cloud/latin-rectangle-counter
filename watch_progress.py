#!/usr/bin/env python3
"""
Watch live computation progress from the database.
Usage: python watch_progress.py [--loop]
"""

import sqlite3
import time
import sys
from datetime import datetime

DB_PATH = 'latin_rectangles.db'

def format_number(n):
    """Format number with commas."""
    return f"{n:,}"

def clear_lines(n):
    """Clear n lines by moving cursor up and clearing."""
    for _ in range(n):
        sys.stdout.write('\033[F')  # Move cursor up
        sys.stdout.write('\033[K')  # Clear line

def watch_progress(loop=False):
    """Monitor the progress table in real-time."""
    if loop:
        print("Watching Latin Rectangle Counter progress...")
        print("Press Ctrl+C to stop\n")
    
    lines_printed = 0
    
    try:
        while True:
            # Clear previous output if looping
            if loop and lines_printed > 0:
                clear_lines(lines_printed)
            
            lines_printed = 0
            
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                # Query the progress table
                cursor.execute('''
                    SELECT r, n, rectangles_scanned, positive_count, negative_count, 
                           is_complete, updated_at 
                    FROM progress
                ''')
                rows = cursor.fetchall()
                
                if rows:
                    header = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Active Computations:"
                    print(header)
                    lines_printed += 1
                    
                    separator = "=" * 90
                    print(separator)
                    lines_printed += 1
                    
                    for row in rows:
                        r, n, scanned, pos, neg, complete, updated_at = row
                        
                        status = "✓ COMPLETE" if complete else "⏳ COMPUTING"
                        diff = pos - neg
                        
                        print(f"\n({r},{n}): {status}")
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
                else:
                    msg = f"[{datetime.now().strftime('%H:%M:%S')}] No active computations in progress table"
                    print(msg)
                    lines_printed += 1
                
                conn.close()
                
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                lines_printed += 1
            except Exception as e:
                print(f"Error: {e}")
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
