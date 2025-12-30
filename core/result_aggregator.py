#!/usr/bin/env python3
"""
Result Aggregator for First Column Optimization.

This module provides thread-safe result aggregation for the first column
optimization system. It accumulates results from all work units and
computes final rectangle counts.
"""

import threading
import time
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import Future


@dataclass
class WorkUnitResult:
    """Result from processing a single work unit."""
    thread_id: int
    positive_count: int
    negative_count: int
    work_units_processed: int
    processing_time: float
    first_columns_processed: List[List[int]] = field(default_factory=list)
    
    @property
    def total_count(self) -> int:
        """Total rectangles in this work unit."""
        return self.positive_count + self.negative_count
    
    @property
    def difference(self) -> int:
        """Difference (positive - negative) for this work unit."""
        return self.positive_count - self.negative_count


@dataclass
class AggregatedResult:
    """Final aggregated result from all work units."""
    total_positive: int
    total_negative: int
    total_difference: int
    total_processing_time: float
    total_work_units: int
    total_first_columns: int
    thread_results: List[WorkUnitResult]
    
    @property
    def total_rectangles(self) -> int:
        """Total rectangles processed."""
        return self.total_positive + self.total_negative
    
    @property
    def average_processing_time(self) -> float:
        """Average processing time per work unit."""
        return self.total_processing_time / len(self.thread_results) if self.thread_results else 0
    
    @property
    def rectangles_per_second(self) -> float:
        """Processing rate in rectangles per second."""
        return self.total_rectangles / self.total_processing_time if self.total_processing_time > 0 else 0


class ResultAggregator:
    """
    Thread-safe result aggregator for first column optimization.
    
    Accumulates results from multiple work units running in parallel threads
    and provides final aggregated counts with comprehensive statistics.
    """
    
    def __init__(self):
        """Initialize the result aggregator."""
        self._lock = threading.Lock()
        self._results = []
        self._total_positive = 0
        self._total_negative = 0
        self._total_work_units = 0
        self._start_time = None
        self._end_time = None
    
    def start_aggregation(self):
        """Mark the start of result aggregation."""
        with self._lock:
            self._start_time = time.time()
            self._results.clear()
            self._total_positive = 0
            self._total_negative = 0
            self._total_work_units = 0
    
    def add_work_unit_result(self, result: WorkUnitResult):
        """
        Add result from a single work unit (thread-safe).
        
        Args:
            result: WorkUnitResult from processing a work unit
        """
        with self._lock:
            self._results.append(result)
            self._total_positive += result.positive_count
            self._total_negative += result.negative_count
            self._total_work_units += result.work_units_processed
    
    def add_result_counts(self, thread_id: int, positive: int, negative: int, 
                         work_units: int, processing_time: float,
                         first_columns: Optional[List[List[int]]] = None):
        """
        Add result counts directly (thread-safe).
        
        Args:
            thread_id: ID of the thread that produced this result
            positive: Number of positive rectangles
            negative: Number of negative rectangles
            work_units: Number of work units processed
            processing_time: Time taken to process
            first_columns: List of first column choices processed
        """
        result = WorkUnitResult(
            thread_id=thread_id,
            positive_count=positive,
            negative_count=negative,
            work_units_processed=work_units,
            processing_time=processing_time,
            first_columns_processed=first_columns or []
        )
        self.add_work_unit_result(result)
    
    def finalize_aggregation(self) -> AggregatedResult:
        """
        Finalize aggregation and return complete results.
        
        Returns:
            AggregatedResult with all accumulated data
        """
        with self._lock:
            self._end_time = time.time()
            
            # Calculate total processing time
            total_time = self._end_time - self._start_time if self._start_time else 0
            
            # Count total first columns processed
            total_first_columns = sum(len(result.first_columns_processed) for result in self._results)
            
            return AggregatedResult(
                total_positive=self._total_positive,
                total_negative=self._total_negative,
                total_difference=self._total_positive - self._total_negative,
                total_processing_time=total_time,
                total_work_units=self._total_work_units,
                total_first_columns=total_first_columns,
                thread_results=self._results.copy()
            )
    
    def get_current_totals(self) -> Tuple[int, int, int]:
        """
        Get current totals (thread-safe).
        
        Returns:
            Tuple of (positive_count, negative_count, work_units_processed)
        """
        with self._lock:
            return (self._total_positive, self._total_negative, self._total_work_units)
    
    def get_thread_statistics(self) -> Dict[str, Any]:
        """
        Get detailed thread-level statistics.
        
        Returns:
            Dictionary with thread performance analysis
        """
        with self._lock:
            if not self._results:
                return {'error': 'No results available'}
            
            # Calculate per-thread statistics
            thread_stats = {}
            for result in self._results:
                thread_stats[result.thread_id] = {
                    'positive_count': result.positive_count,
                    'negative_count': result.negative_count,
                    'total_count': result.total_count,
                    'work_units': result.work_units_processed,
                    'processing_time': result.processing_time,
                    'rectangles_per_second': result.total_count / result.processing_time if result.processing_time > 0 else 0,
                    'first_columns_count': len(result.first_columns_processed)
                }
            
            # Calculate load balancing statistics
            work_unit_counts = [result.work_units_processed for result in self._results]
            processing_times = [result.processing_time for result in self._results]
            
            load_balance_stats = {
                'work_unit_distribution': work_unit_counts,
                'min_work_units': min(work_unit_counts) if work_unit_counts else 0,
                'max_work_units': max(work_unit_counts) if work_unit_counts else 0,
                'work_unit_variance': self._calculate_variance(work_unit_counts),
                'processing_time_variance': self._calculate_variance(processing_times),
                'load_balance_ratio': min(work_unit_counts) / max(work_unit_counts) if work_unit_counts and max(work_unit_counts) > 0 else 0
            }
            
            return {
                'thread_count': len(self._results),
                'thread_stats': thread_stats,
                'load_balance': load_balance_stats
            }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def validate_results(self, expected_total: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate aggregated results for correctness.
        
        Args:
            expected_total: Expected total rectangle count (optional)
            
        Returns:
            Dictionary with validation results
        """
        with self._lock:
            validation = {
                'total_positive': self._total_positive,
                'total_negative': self._total_negative,
                'total_rectangles': self._total_positive + self._total_negative,
                'difference': self._total_positive - self._total_negative,
                'work_units_processed': self._total_work_units,
                'thread_count': len(self._results)
            }
            
            # Check for consistency
            calculated_positive = sum(result.positive_count for result in self._results)
            calculated_negative = sum(result.negative_count for result in self._results)
            calculated_work_units = sum(result.work_units_processed for result in self._results)
            
            validation['consistency_check'] = {
                'positive_match': calculated_positive == self._total_positive,
                'negative_match': calculated_negative == self._total_negative,
                'work_units_match': calculated_work_units == self._total_work_units
            }
            
            # Check against expected total if provided
            if expected_total is not None:
                validation['expected_total'] = expected_total
                validation['total_match'] = validation['total_rectangles'] == expected_total
                validation['accuracy'] = validation['total_rectangles'] / expected_total if expected_total > 0 else 0
            
            # Overall validation status
            validation['validation_passed'] = all(validation['consistency_check'].values())
            if expected_total is not None:
                validation['validation_passed'] = validation['validation_passed'] and validation['total_match']
            
            return validation
    
    def clear(self):
        """Clear all accumulated results."""
        with self._lock:
            self._results.clear()
            self._total_positive = 0
            self._total_negative = 0
            self._total_work_units = 0
            self._start_time = None
            self._end_time = None


def main():
    """
    Test the result aggregator.
    """
    aggregator = ResultAggregator()
    
    print("=== Testing Result Aggregator ===")
    
    # Test basic aggregation
    print("\n1. Testing basic result aggregation:")
    aggregator.start_aggregation()
    
    # Simulate results from multiple threads
    test_results = [
        (1, 4, 4, 1, 0.001),  # Thread 1: 4 pos, 4 neg, 1 work unit
        (2, 4, 4, 1, 0.001),  # Thread 2: 4 pos, 4 neg, 1 work unit  
        (3, 4, 4, 1, 0.001),  # Thread 3: 4 pos, 4 neg, 1 work unit
    ]
    
    for thread_id, pos, neg, work_units, proc_time in test_results:
        aggregator.add_result_counts(thread_id, pos, neg, work_units, proc_time)
        print(f"   Added result from thread {thread_id}: {pos} pos, {neg} neg")
    
    # Get current totals
    current_pos, current_neg, current_work = aggregator.get_current_totals()
    print(f"   Current totals: {current_pos} pos, {current_neg} neg, {current_work} work units")
    
    # Finalize aggregation
    final_result = aggregator.finalize_aggregation()
    print(f"   Final result: {final_result.total_positive} pos, {final_result.total_negative} neg")
    print(f"   Total rectangles: {final_result.total_rectangles}")
    print(f"   Processing rate: {final_result.rectangles_per_second:.0f} rectangles/second")
    
    # Test thread statistics
    print("\n2. Testing thread statistics:")
    thread_stats = aggregator.get_thread_statistics()
    print(f"   Thread count: {thread_stats['thread_count']}")
    print(f"   Load balance ratio: {thread_stats['load_balance']['load_balance_ratio']:.2f}")
    
    # Test validation
    print("\n3. Testing result validation:")
    validation = aggregator.validate_results(expected_total=24)  # Expected for (3,4) case
    print(f"   Validation passed: {'✅' if validation['validation_passed'] else '❌'}")
    print(f"   Total match: {'✅' if validation.get('total_match', False) else '❌'}")
    print(f"   Consistency: {validation['consistency_check']}")
    
    print("\n✅ Result aggregator tests completed")


if __name__ == "__main__":
    main()