#!/usr/bin/env python3
"""
Check computation progress by querying the database directly.
Usage: python check_progress.py
"""

import sqlite3
from datetime import datetime

DB_PATH = 'latin_rectangles.db'

def format_number(n):
    """Format number with commas."""
    return f"{n:,}"

def check_progress():
    """Check what's in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all cached results
        cursor.execute('SELECT r, n, positive_count, negative_count FROM results ORDER BY n, r')
        results = cursor.fetchall()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Cached Results in Database:")
        print("=" * 80)
        
        if results:
            current_n = None
            for r, n, pos, neg in results:
                if n != current_n:
                    if current_n is not None:
                        print()
                    print(f"\nn = {n}:")
                    current_n = n
                
                diff = pos - neg
                print(f"  ({r},{n}): +{format_number(pos)}, -{format_number(neg)}, Δ={format_number(diff)}")
        else:
            print("No results in database yet.")
        
        print("\n" + "=" * 80)
        print(f"Total cached: {len(results)} results")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_progress()
