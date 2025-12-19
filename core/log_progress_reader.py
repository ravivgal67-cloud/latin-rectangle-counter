"""
Log-based progress reader for Latin Rectangle computations.

This module reads progress information from log files instead of using
a temporary database table. Since we log progress every 10 minutes,
we can parse the logs to get current computation status.
"""

import os
import re
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta


def get_progress_from_logs(log_dir: str = "logs") -> List[Dict]:
    """
    Read progress information from JSONL progress files.
    
    Reads structured progress data from .jsonl files that contain
    progress updates logged every 10 minutes during computations.
    
    Args:
        log_dir: Directory containing log files
        
    Returns:
        List of dictionaries with progress information:
        [
            {
                'r': int,
                'n': int, 
                'rectangles_scanned': int,
                'positive_count': int,
                'negative_count': int,
                'is_complete': bool,
                'last_update': str,  # ISO timestamp
                'process_id': str    # e.g., "parallel_6_7_process_0"
            }
        ]
    """
    if not os.path.exists(log_dir):
        return []
    
    progress_entries = []
    
    # Find all JSONL progress files that match parallel computation pattern
    jsonl_files = []
    for filename in os.listdir(log_dir):
        if filename.endswith('_progress.jsonl') and 'parallel_' in filename:
            jsonl_files.append(os.path.join(log_dir, filename))
    
    # Parse each JSONL file for progress information
    for jsonl_file in jsonl_files:
        try:
            progress = _parse_jsonl_file(jsonl_file)
            if progress:
                progress_entries.append(progress)
        except Exception as e:
            # Skip files that can't be parsed
            continue
    
    return progress_entries


def _parse_jsonl_file(jsonl_file: str) -> Optional[Dict]:
    """
    Parse a single JSONL progress file to extract the latest progress information.
    
    Args:
        jsonl_file: Path to JSONL progress file
        
    Returns:
        Dictionary with progress info, or None if no progress found
    """
    if not os.path.exists(jsonl_file):
        return None
    
    # Extract process info from filename
    # e.g., "parallel_completion_6_7_process_0_progress.jsonl" -> r=6, n=7, process=0
    filename = os.path.basename(jsonl_file)
    match = re.match(r'parallel_completion_(\d+)_(\d+)_process_(\d+)_progress\.jsonl', filename)
    if not match:
        return None
    
    r, n, process_num = map(int, match.groups())
    process_id = f"parallel_completion_{r}_{n}_process_{process_num}"
    
    # Read the JSONL file and find the latest progress entry
    latest_progress = None
    latest_timestamp = None
    
    try:
        with open(jsonl_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    
                    # Look for progress entries (have progress_pct field)
                    if 'progress_pct' in entry and 'completed_work' in entry:
                        timestamp_str = entry.get('timestamp')
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            
                            if latest_timestamp is None or timestamp > latest_timestamp:
                                latest_timestamp = timestamp
                                
                                # Check if this is a completion (100% progress)
                                is_complete = entry.get('progress_pct', 0) >= 100.0
                                
                                latest_progress = {
                                    'rectangles_scanned': entry.get('completed_work', 0),
                                    'positive_count': entry.get('positive_count', 0),
                                    'negative_count': entry.get('negative_count', 0),
                                    'is_complete': is_complete,
                                    'progress_pct': entry.get('progress_pct', 0),
                                    'completed_work': entry.get('completed_work', 0),
                                    'total_work': entry.get('total_work', 0)
                                }
                
                except json.JSONDecodeError:
                    continue
    
    except Exception as e:
        return None
    
    if latest_progress and latest_timestamp:
        latest_progress.update({
            'r': r,
            'n': n,
            'process_id': process_id,
            'last_update': latest_timestamp.isoformat()
        })
        return latest_progress
    
    return None


def _extract_timestamp_from_line(line: str) -> Optional[datetime]:
    """Extract timestamp from log line."""
    # Format: "2025-12-17 23:15:09,123"
    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}', line)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        except:
            pass
    return None


def _extract_progress_from_line(line: str) -> Optional[Dict]:
    """
    Extract progress information from a log line.
    
    Expected format: "📊 Progress: 1,234,567 rectangles scanned (+567,890 -666,777)"
    """
    # Look for progress pattern
    match = re.search(r'📊 Progress: ([\d,]+) rectangles scanned \(\+?([\d,]+) -?([\d,]+)\)', line)
    if match:
        try:
            rectangles_scanned = int(match.group(1).replace(',', ''))
            positive_count = int(match.group(2).replace(',', ''))
            negative_count = int(match.group(3).replace(',', ''))
            
            return {
                'rectangles_scanned': rectangles_scanned,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'is_complete': False
            }
        except:
            pass
    
    return None


def _extract_completion_from_line(line: str) -> Optional[Dict]:
    """
    Extract final counts from completion log line.
    
    Expected format: "✅ Completed: 12,345,678 total (+6,789,012 -5,556,666)"
    """
    # Look for completion pattern
    match = re.search(r'(?:✅ Completed|FINAL RESULT).*?(\d[\d,]*) total.*?\(\+?([\d,]+) -?([\d,]+)\)', line)
    if match:
        try:
            total_count = int(match.group(1).replace(',', ''))
            positive_count = int(match.group(2).replace(',', ''))
            negative_count = int(match.group(3).replace(',', ''))
            
            return {
                'rectangles_scanned': total_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'is_complete': True
            }
        except:
            pass
    
    return None


def is_computation_active(log_dir: str = "logs", max_age_minutes: int = 15) -> bool:
    """
    Check if there are any active computations based on recent log activity.
    
    Args:
        log_dir: Directory containing log files
        max_age_minutes: Consider computation active if logs updated within this time
        
    Returns:
        True if there are active computations
    """
    progress_entries = get_progress_from_logs(log_dir)
    
    if not progress_entries:
        return False
    
    cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
    
    for entry in progress_entries:
        if not entry.get('is_complete', False):
            try:
                last_update = datetime.fromisoformat(entry['last_update'])
                if last_update > cutoff_time:
                    return True
            except:
                continue
    
    return False


if __name__ == "__main__":
    # Test the log reader
    print("Testing log-based progress reader...")
    
    progress = get_progress_from_logs()
    print(f"Found {len(progress)} progress entries:")
    
    for entry in progress:
        status = "✅ Complete" if entry.get('is_complete') else "🔄 Running"
        print(f"  ({entry['r']},{entry['n']}) {status}: {entry['rectangles_scanned']:,} scanned "
              f"(+{entry['positive_count']:,} -{entry['negative_count']:,}) "
              f"[{entry['process_id']}]")
    
    print(f"\nActive computations: {is_computation_active()}")