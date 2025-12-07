#!/usr/bin/env python3
"""
Monitor computation progress for Latin Rectangle Counter.
Usage: python monitor_progress.py
"""

import urllib.request
import json
import time
import sys
from datetime import datetime

API_URL = "http://localhost:5000/api/progress"

def format_number(n):
    """Format number with commas."""
    return f"{n:,}"

def monitor_progress():
    """Poll the progress endpoint and display updates."""
    print("Monitoring Latin Rectangle Counter progress...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            try:
                req = urllib.request.Request(API_URL)
                req.add_header('User-Agent', 'Mozilla/5.0')
                with urllib.request.urlopen(req, timeout=2) as response:
                    data = json.loads(response.read().decode())
                
                if data.get('status') == 'success':
                    progress_list = data.get('progress', [])
                    
                    if progress_list:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Active computations:")
                        print("-" * 80)
                        
                        for prog in progress_list:
                            r = prog['r']
                            n = prog['n']
                            scanned = format_number(prog['rectangles_scanned'])
                            pos = format_number(prog['positive_count'])
                            neg = format_number(prog['negative_count'])
                            complete = prog['is_complete']
                            
                            status = "✓ Complete" if complete else "⏳ Computing"
                            print(f"  ({r},{n}): {status}")
                            print(f"    Scanned: {scanned} | Positive: {pos} | Negative: {neg}")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] No active computations")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No progress data available")
                    
            except urllib.error.URLError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error connecting to server: {e}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
            
            time.sleep(2)  # Poll every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)

if __name__ == "__main__":
    monitor_progress()
