"""
Tests for result formatting functions.
"""

import pytest
from core.counter import CountResult
from core.formatting import format_table, format_for_web


def test_format_table_single_result():
    """Test formatting a single result as a table."""
    results = [CountResult(2, 3, 1, 2, -1, False)]
    table = format_table(results)
    
    # Check that table contains expected elements
    assert "r" in table
    assert "n" in table
    assert "Positive" in table
    assert "Negative" in table
    assert "Difference" in table
    assert "Cached" in table
    assert "2" in table
    assert "3" in table
    assert "1" in table
    assert "-1" in table
    assert "No" in table


def test_format_table_multiple_results():
    """Test formatting multiple results as a table."""
    results = [
        CountResult(2, 3, 1, 2, -1, False),
        CountResult(2, 4, 3, 6, -3, True),
        CountResult(3, 4, 2, 4, -2, False)
    ]
    table = format_table(results)
    
    # Check all results are present
    lines = table.split("\n")
    assert len(lines) >= 5  # header + separator + 3 data rows
    
    # Check cached indicator
    assert "Yes" in table  # For the cached result
    assert "No" in table   # For non-cached results


def test_format_table_empty_results():
    """Test formatting empty results list."""
    results = []
    table = format_table(results)
    
    assert "No results" in table


def test_format_table_cached_indicator():
    """Test that cached results are properly indicated."""
    results = [
        CountResult(2, 3, 1, 2, -1, True),
        CountResult(2, 4, 3, 6, -3, False)
    ]
    table = format_table(results)
    
    lines = table.split("\n")
    # First data row should have "Yes" for cached
    assert "Yes" in lines[2]
    # Second data row should have "No" for not cached
    assert "No" in lines[3]


def test_format_for_web_single_result():
    """Test converting a single result to web format."""
    results = [CountResult(2, 3, 1, 2, -1, False)]
    web_data = format_for_web(results)
    
    assert "results" in web_data
    assert len(web_data["results"]) == 1
    
    result = web_data["results"][0]
    assert result["r"] == 2
    assert result["n"] == 3
    assert result["positive_count"] == 1
    assert result["negative_count"] == 2
    assert result["difference"] == -1
    assert result["from_cache"] is False


def test_format_for_web_multiple_results():
    """Test converting multiple results to web format."""
    results = [
        CountResult(2, 3, 1, 2, -1, False),
        CountResult(2, 4, 3, 6, -3, True),
        CountResult(3, 4, 2, 4, -2, False)
    ]
    web_data = format_for_web(results)
    
    assert "results" in web_data
    assert len(web_data["results"]) == 3
    
    # Check first result
    assert web_data["results"][0]["r"] == 2
    assert web_data["results"][0]["n"] == 3
    assert web_data["results"][0]["from_cache"] is False
    
    # Check second result (cached)
    assert web_data["results"][1]["r"] == 2
    assert web_data["results"][1]["n"] == 4
    assert web_data["results"][1]["from_cache"] is True
    
    # Check third result
    assert web_data["results"][2]["r"] == 3
    assert web_data["results"][2]["n"] == 4
    assert web_data["results"][2]["from_cache"] is False


def test_format_for_web_empty_results():
    """Test converting empty results list to web format."""
    results = []
    web_data = format_for_web(results)
    
    assert "results" in web_data
    assert len(web_data["results"]) == 0
    assert web_data["results"] == []


def test_format_for_web_all_fields_included():
    """Test that all CountResult fields are included in web format."""
    result = CountResult(3, 5, 10, 20, -10, True)
    web_data = format_for_web([result])
    
    result_dict = web_data["results"][0]
    
    # Verify all fields are present
    assert "r" in result_dict
    assert "n" in result_dict
    assert "positive_count" in result_dict
    assert "negative_count" in result_dict
    assert "difference" in result_dict
    assert "from_cache" in result_dict
    
    # Verify values
    assert result_dict["r"] == 3
    assert result_dict["n"] == 5
    assert result_dict["positive_count"] == 10
    assert result_dict["negative_count"] == 20
    assert result_dict["difference"] == -10
    assert result_dict["from_cache"] is True
