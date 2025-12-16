"""
Tests for counter-based rectangle generation.
"""

import pytest
from core.latin_rectangle import (
    generate_normalized_rectangles,
    generate_normalized_rectangles_counter_based,
    CounterBasedRectangleIterator
)


class TestCounterBasedGeneration:
    """Test counter-based rectangle generation functionality."""
    
    def test_counter_based_function_correctness(self):
        """Test that counter-based function produces correct results."""
        # Test several dimensions
        test_cases = [(2, 3), (3, 4), (4, 5)]
        
        for r, n in test_cases:
            # Generate with main function (now counter-based)
            main_rects = list(generate_normalized_rectangles(r, n))
            
            # Generate with explicit counter-based function
            counter_rects = list(generate_normalized_rectangles_counter_based(r, n))
            
            # Should produce same results
            assert len(main_rects) == len(counter_rects)
            
            # Convert to sets for comparison
            main_set = {tuple(tuple(row) for row in rect.data) for rect in main_rects}
            counter_set = {tuple(tuple(row) for row in rect.data) for rect in counter_rects}
            
            assert main_set == counter_set
    
    def test_counter_based_with_start_counters(self):
        """Test counter-based generation with start counters."""
        r, n = 3, 4
        
        # Generate all rectangles
        all_rects = list(generate_normalized_rectangles_counter_based(r, n))
        
        # Generate starting from counter [0, 1, 0] (skip first permutation of row 2)
        partial_rects = list(generate_normalized_rectangles_counter_based(r, n, [0, 1, 0]))
        
        # Should have fewer rectangles
        assert len(partial_rects) < len(all_rects)
        assert len(partial_rects) > 0
        
        # All partial rectangles should be in the full set
        all_set = {tuple(tuple(row) for row in rect.data) for rect in all_rects}
        partial_set = {tuple(tuple(row) for row in rect.data) for rect in partial_rects}
        
        assert partial_set.issubset(all_set)
    
    def test_deterministic_ordering(self):
        """Test that counter-based generation produces deterministic ordering."""
        r, n = 3, 4
        
        # Generate twice
        rects1 = list(generate_normalized_rectangles_counter_based(r, n))
        rects2 = list(generate_normalized_rectangles_counter_based(r, n))
        
        # Should be identical (same order)
        assert len(rects1) == len(rects2)
        
        for rect1, rect2 in zip(rects1, rects2):
            assert rect1.data == rect2.data


class TestCounterBasedIterator:
    """Test the CounterBasedRectangleIterator class."""
    
    def test_iterator_basic_functionality(self):
        """Test basic iterator functionality."""
        r, n = 3, 4
        
        # Generate with function
        function_rects = list(generate_normalized_rectangles_counter_based(r, n))
        
        # Generate with iterator
        iterator = CounterBasedRectangleIterator(r, n)
        iterator_rects = list(iterator)
        
        # Should produce same rectangles (though iterator may be slower)
        assert len(function_rects) == len(iterator_rects)
        
        function_set = {tuple(tuple(row) for row in rect.data) for rect in function_rects}
        iterator_set = {tuple(tuple(row) for row in rect.data) for rect in iterator_rects}
        
        assert function_set == iterator_set
    
    def test_iterator_state_management(self):
        """Test iterator state save/restore functionality."""
        r, n = 3, 4
        
        # Create iterator and generate some rectangles
        iterator1 = CounterBasedRectangleIterator(r, n)
        rects1 = []
        
        for i, rect in enumerate(iterator1):
            rects1.append(rect)
            if i >= 3:  # Stop after 4 rectangles
                break
        
        # Save state
        state = iterator1.get_state()
        
        # Create new iterator and restore state
        iterator2 = CounterBasedRectangleIterator(r, n)
        iterator2.set_state(state)
        
        # Generate remaining rectangles
        rects2 = list(iterator2)
        
        # Combine and verify completeness
        all_rects = rects1 + rects2
        expected_rects = list(generate_normalized_rectangles_counter_based(r, n))
        
        assert len(all_rects) == len(expected_rects)
        
        # Check no duplicates
        all_set = {tuple(tuple(row) for row in rect.data) for rect in all_rects}
        expected_set = {tuple(tuple(row) for row in rect.data) for rect in expected_rects}
        
        assert len(all_set) == len(all_rects)  # No duplicates
        assert all_set == expected_set  # Complete coverage
    
    def test_iterator_with_start_counters(self):
        """Test iterator initialization with start counters."""
        r, n = 3, 4
        
        # Create iterator starting from specific position
        start_counters = [0, 1, 0]
        iterator = CounterBasedRectangleIterator(r, n, start_counters)
        
        # Verify initial state
        state = iterator.get_state()
        assert state['counters'] == start_counters
        assert state['rectangles_generated'] == 0
        assert not state['finished']
        
        # Generate some rectangles
        rects = []
        for i, rect in enumerate(iterator):
            rects.append(rect)
            if i >= 2:  # Just a few rectangles
                break
        
        assert len(rects) == 3
        assert iterator.get_state()['rectangles_generated'] == 3