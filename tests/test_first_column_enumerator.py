#!/usr/bin/env python3
"""
Unit tests for FirstColumnEnumerator.
"""

import unittest
import math
from core.first_column_enumerator import FirstColumnEnumerator


class TestFirstColumnEnumerator(unittest.TestCase):
    """Test cases for FirstColumnEnumerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enumerator = FirstColumnEnumerator()
    
    def test_enumerate_first_columns_basic(self):
        """Test basic first column enumeration."""
        # Test (3,4) case
        columns = self.enumerator.enumerate_first_columns(3, 4)
        expected = [
            [1, 2, 3],
            [1, 2, 4], 
            [1, 3, 4]
        ]
        self.assertEqual(columns, expected)
        
        # Test (4,5) case
        columns = self.enumerator.enumerate_first_columns(4, 5)
        expected = [
            [1, 2, 3, 4],
            [1, 2, 3, 5],
            [1, 2, 4, 5],
            [1, 3, 4, 5]
        ]
        self.assertEqual(columns, expected)
    
    def test_count_first_columns(self):
        """Test counting of first column configurations."""
        # Test known values
        test_cases = [
            (3, 4, 3),   # C(3,2) = 3
            (3, 5, 6),   # C(4,2) = 6  
            (4, 5, 4),   # C(4,3) = 4
            (5, 8, 35),  # C(7,4) = 35
        ]
        
        for r, n, expected in test_cases:
            with self.subTest(r=r, n=n):
                count = self.enumerator.count_first_columns(r, n)
                self.assertEqual(count, expected)
                
                # Verify against math.comb
                expected_comb = math.comb(n-1, r-1)
                self.assertEqual(count, expected_comb)
    
    def test_get_symmetry_factor(self):
        """Test symmetry factor calculation."""
        test_cases = [
            (3, 2),    # (3-1)! = 2! = 2
            (4, 6),    # (4-1)! = 3! = 6
            (5, 24),   # (5-1)! = 4! = 24
            (6, 120),  # (6-1)! = 5! = 120
        ]
        
        for r, expected in test_cases:
            with self.subTest(r=r):
                factor = self.enumerator.get_symmetry_factor(r)
                self.assertEqual(factor, expected)
                
                # Verify against math.factorial
                expected_factorial = math.factorial(r-1)
                self.assertEqual(factor, expected_factorial)
    
    def test_validate_first_column(self):
        """Test first column validation."""
        # Valid cases
        valid_cases = [
            ([1, 2, 3], 3, 4),
            ([1, 2, 4], 3, 5),
            ([1, 3, 4, 5], 4, 6),
        ]
        
        for column, r, n in valid_cases:
            with self.subTest(column=column, r=r, n=n):
                self.assertTrue(self.enumerator.validate_first_column(column, r, n))
        
        # Invalid cases
        invalid_cases = [
            ([2, 3, 4], 3, 4),      # First element not 1
            ([1, 2], 3, 4),         # Wrong length
            ([1, 2, 2], 3, 4),      # Duplicate values
            ([1, 2, 5], 3, 4),      # Value out of range
            ([1, 1, 3], 3, 4),      # Duplicate 1
        ]
        
        for column, r, n in invalid_cases:
            with self.subTest(column=column, r=r, n=n):
                self.assertFalse(self.enumerator.validate_first_column(column, r, n))
    
    def test_enumerate_first_columns_iterator(self):
        """Test iterator version of enumeration."""
        # Compare iterator results with list results
        r, n = 4, 5
        
        list_result = self.enumerator.enumerate_first_columns(r, n)
        iterator_result = list(self.enumerator.enumerate_first_columns_iterator(r, n))
        
        self.assertEqual(list_result, iterator_result)
    
    def test_dimension_validation(self):
        """Test dimension validation."""
        # Invalid r values
        with self.assertRaises(ValueError):
            self.enumerator.enumerate_first_columns(1, 4)  # r < 2
        
        with self.assertRaises(ValueError):
            self.enumerator.enumerate_first_columns(0, 4)  # r < 2
        
        # Invalid n values
        with self.assertRaises(ValueError):
            self.enumerator.enumerate_first_columns(3, 2)  # n < r
        
        with self.assertRaises(ValueError):
            self.enumerator.enumerate_first_columns(5, 3)  # n < r
    
    def test_first_column_properties(self):
        """Test mathematical properties of first columns."""
        test_cases = [(3, 4), (3, 5), (4, 5), (4, 6), (5, 8)]
        
        for r, n in test_cases:
            with self.subTest(r=r, n=n):
                columns = self.enumerator.enumerate_first_columns(r, n)
                
                # All columns should have length r
                for col in columns:
                    self.assertEqual(len(col), r)
                
                # All columns should start with 1
                for col in columns:
                    self.assertEqual(col[0], 1)
                
                # All columns should have unique values
                for col in columns:
                    self.assertEqual(len(col), len(set(col)))
                
                # All values should be in range [1, n]
                for col in columns:
                    for val in col:
                        self.assertGreaterEqual(val, 1)
                        self.assertLessEqual(val, n)
                
                # Should generate exactly C(n-1, r-1) columns
                expected_count = math.comb(n-1, r-1)
                self.assertEqual(len(columns), expected_count)
                
                # All columns should be unique
                unique_columns = set(tuple(col) for col in columns)
                self.assertEqual(len(unique_columns), len(columns))
    
    def test_symmetry_factor_validation(self):
        """Test symmetry factor validation."""
        # Valid cases
        # Test valid cases including r=2
        for r in range(2, 8):
            factor = self.enumerator.get_symmetry_factor(r)
            self.assertEqual(factor, math.factorial(r-1))
        
        # Invalid cases
        with self.assertRaises(ValueError):
            self.enumerator.get_symmetry_factor(1)
        
        with self.assertRaises(ValueError):
            self.enumerator.get_symmetry_factor(0)
    
    def test_large_dimensions(self):
        """Test with larger dimensions to ensure scalability."""
        # Test (6,8) - should generate C(7,5) = 21 columns
        r, n = 6, 8
        count = self.enumerator.count_first_columns(r, n)
        expected = math.comb(7, 5)  # C(7,5) = 21
        self.assertEqual(count, expected)
        
        # Verify enumeration produces correct count
        columns = self.enumerator.enumerate_first_columns(r, n)
        self.assertEqual(len(columns), count)
        
        # Verify all columns are valid
        for col in columns:
            self.assertTrue(self.enumerator.validate_first_column(col, r, n))


if __name__ == '__main__':
    unittest.main()