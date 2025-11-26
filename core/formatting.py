"""
Result formatting module for Latin Rectangle Counter.

This module provides functions for formatting CountResult objects
for display in different contexts (text table, web JSON).
"""

from typing import List, Dict, Any
from core.counter import CountResult


def format_table(results: List[CountResult]) -> str:
    """
    Format a list of CountResults as a text table.
    
    The table includes columns for:
    - r: Number of rows
    - n: Number of columns
    - positive: Count of positive (even) rectangles
    - negative: Count of negative (odd) rectangles
    - difference: positive - negative
    - cached: Indicator if result was from cache
    
    Args:
        results: List of CountResult objects to format
        
    Returns:
        Formatted string representing a text table
        
    Examples:
        >>> from core.counter import CountResult
        >>> results = [
        ...     CountResult(2, 3, 1, 2, -1, False),
        ...     CountResult(2, 4, 3, 6, -3, True)
        ... ]
        >>> table = format_table(results)
        >>> print(table)
        r | n | Positive | Negative | Difference | Cached
        --|---|----------|----------|------------|-------
        2 | 3 |        1 |        2 |         -1 | No
        2 | 4 |        3 |        6 |         -3 | Yes
    """
    if not results:
        return "No results to display."
    
    # Define column headers
    headers = ["r", "n", "Positive", "Negative", "Difference", "Cached"]
    
    # Calculate column widths based on content
    col_widths = [len(h) for h in headers]
    
    # Update widths based on data
    for result in results:
        col_widths[0] = max(col_widths[0], len(str(result.r)))
        col_widths[1] = max(col_widths[1], len(str(result.n)))
        col_widths[2] = max(col_widths[2], len(str(result.positive_count)))
        col_widths[3] = max(col_widths[3], len(str(result.negative_count)))
        col_widths[4] = max(col_widths[4], len(str(result.difference)))
        cached_text = "Yes" if result.from_cache else "No"
        col_widths[5] = max(col_widths[5], len(cached_text))
    
    # Build header row
    header_row = " | ".join(
        headers[i].ljust(col_widths[i]) for i in range(len(headers))
    )
    
    # Build separator row
    separator_row = "-|-".join("-" * w for w in col_widths)
    
    # Build data rows
    data_rows = []
    for result in results:
        cached_text = "Yes" if result.from_cache else "No"
        row = " | ".join([
            str(result.r).ljust(col_widths[0]),
            str(result.n).ljust(col_widths[1]),
            str(result.positive_count).rjust(col_widths[2]),
            str(result.negative_count).rjust(col_widths[3]),
            str(result.difference).rjust(col_widths[4]),
            cached_text.ljust(col_widths[5])
        ])
        data_rows.append(row)
    
    # Combine all parts
    table_lines = [header_row, separator_row] + data_rows
    return "\n".join(table_lines)


def format_for_web(results: List[CountResult]) -> Dict[str, Any]:
    """
    Convert a list of CountResults to a JSON-serializable dictionary.
    
    This function prepares the results for web API responses by converting
    them to a dictionary structure that can be easily serialized to JSON.
    
    Args:
        results: List of CountResult objects to convert
        
    Returns:
        Dictionary with 'results' key containing list of result dictionaries.
        Each result dictionary includes all fields: r, n, positive_count,
        negative_count, difference, and from_cache.
        
    Examples:
        >>> from core.counter import CountResult
        >>> results = [
        ...     CountResult(2, 3, 1, 2, -1, False),
        ...     CountResult(2, 4, 3, 6, -3, True)
        ... ]
        >>> web_data = format_for_web(results)
        >>> web_data['results'][0]['r']
        2
        >>> web_data['results'][0]['from_cache']
        False
        >>> web_data['results'][1]['from_cache']
        True
    """
    return {
        "results": [
            {
                "r": result.r,
                "n": result.n,
                "positive_count": result.positive_count,
                "negative_count": result.negative_count,
                "difference": result.difference,
                "from_cache": result.from_cache
            }
            for result in results
        ]
    }
