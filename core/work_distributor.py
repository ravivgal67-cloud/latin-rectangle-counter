#!/usr/bin/env python3
"""
Work Distribution System for First Column Optimization.

This module distributes first column choices across available threads
for optimal parallel processing.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import math


@dataclass
class WorkUnit:
    """Represents a work unit for a single thread."""
    thread_id: int
    first_column_choices: List[List[int]]
    positive_count: int = 0
    negative_count: int = 0
    
    def add_result(self, positive: int, negative: int, symmetry_factor: int):
        """Add results from one first column choice."""
        self.positive_count += positive * symmetry_factor
        self.negative_count += negative * symmetry_factor
    
    def get_difference(self) -> int:
        """Get the difference (positive - negative)."""
        return self.positive_count - self.negative_count


class WorkDistributor:
    """
    Distributes first column choices across threads for parallel processing.
    
    Uses round-robin distribution to ensure balanced workload across all threads.
    """
    
    def __init__(self):
        """Initialize the work distributor."""
        pass
    
    def distribute_work(self, first_column_choices: List[List[int]], 
                       num_threads: int) -> List[WorkUnit]:
        """
        Distribute first column choices across threads using round-robin.
        
        Args:
            first_column_choices: All first column configurations to process
            num_threads: Number of available threads
            
        Returns:
            List of WorkUnit objects, one per thread
            
        Raises:
            ValueError: If num_threads <= 0 or no work to distribute
        """
        if num_threads <= 0:
            raise ValueError(f"Number of threads must be positive, got {num_threads}")
        
        if not first_column_choices:
            raise ValueError("No first column choices to distribute")
        
        # Create work units for each thread
        work_units = [WorkUnit(thread_id=i, first_column_choices=[]) 
                     for i in range(num_threads)]
        
        # Distribute choices using round-robin
        for i, choice in enumerate(first_column_choices):
            thread_id = i % num_threads
            work_units[thread_id].first_column_choices.append(choice)
        
        return work_units
    
    def get_distribution_stats(self, work_units: List[WorkUnit]) -> Dict[str, Any]:
        """
        Get statistics about work distribution.
        
        Args:
            work_units: List of work units to analyze
            
        Returns:
            Dictionary with distribution statistics
        """
        if not work_units:
            return {}
        
        work_counts = [len(unit.first_column_choices) for unit in work_units]
        total_work = sum(work_counts)
        
        return {
            'total_threads': len(work_units),
            'total_work_units': total_work,
            'min_work_per_thread': min(work_counts) if work_counts else 0,
            'max_work_per_thread': max(work_counts) if work_counts else 0,
            'avg_work_per_thread': total_work / len(work_units) if work_units else 0,
            'work_distribution': work_counts,
            'is_balanced': max(work_counts) - min(work_counts) <= 1 if work_counts else True
        }
    
    def validate_distribution(self, work_units: List[WorkUnit], 
                            original_choices: List[List[int]]) -> bool:
        """
        Validate that distribution preserves all work and maintains uniqueness.
        
        Args:
            work_units: Distributed work units
            original_choices: Original first column choices
            
        Returns:
            True if distribution is valid, False otherwise
        """
        # Collect all distributed choices
        distributed_choices = []
        for unit in work_units:
            distributed_choices.extend(unit.first_column_choices)
        
        # Check total count
        if len(distributed_choices) != len(original_choices):
            return False
        
        # Check that all original choices are present
        original_set = set(tuple(choice) for choice in original_choices)
        distributed_set = set(tuple(choice) for choice in distributed_choices)
        
        return original_set == distributed_set
    
    def optimize_distribution(self, first_column_choices: List[List[int]], 
                            num_threads: int, 
                            complexity_estimator=None) -> List[WorkUnit]:
        """
        Distribute work with optional complexity-based balancing.
        
        Args:
            first_column_choices: All first column configurations
            num_threads: Number of available threads
            complexity_estimator: Optional function to estimate work complexity
            
        Returns:
            List of WorkUnit objects with optimized distribution
        """
        if complexity_estimator is None:
            # Use simple round-robin if no complexity estimator provided
            return self.distribute_work(first_column_choices, num_threads)
        
        # Estimate complexity for each choice
        choices_with_complexity = []
        for choice in first_column_choices:
            complexity = complexity_estimator(choice)
            choices_with_complexity.append((choice, complexity))
        
        # Sort by complexity (descending) for better load balancing
        choices_with_complexity.sort(key=lambda x: x[1], reverse=True)
        
        # Create work units
        work_units = [WorkUnit(thread_id=i, first_column_choices=[]) 
                     for i in range(num_threads)]
        
        # Distribute using greedy algorithm (assign to thread with least total complexity)
        thread_complexities = [0.0] * num_threads
        
        for choice, complexity in choices_with_complexity:
            # Find thread with minimum current complexity
            min_thread = min(range(num_threads), key=lambda i: thread_complexities[i])
            
            # Assign work to that thread
            work_units[min_thread].first_column_choices.append(choice)
            thread_complexities[min_thread] += complexity
        
        return work_units


def main():
    """
    Demonstration of work distribution.
    """
    from core.first_column_enumerator import FirstColumnEnumerator
    
    distributor = WorkDistributor()
    enumerator = FirstColumnEnumerator()
    
    # Test cases
    test_cases = [(3, 5, 4), (4, 6, 8), (5, 8, 8)]
    
    for r, n, num_threads in test_cases:
        print(f"\n=== Work Distribution for ({r},{n}) with {num_threads} threads ===")
        
        # Generate first column choices
        choices = enumerator.enumerate_first_columns(r, n)
        print(f"Total first column choices: {len(choices)}")
        
        # Distribute work
        work_units = distributor.distribute_work(choices, num_threads)
        
        # Get distribution statistics
        stats = distributor.get_distribution_stats(work_units)
        print(f"Distribution stats: {stats}")
        
        # Validate distribution
        is_valid = distributor.validate_distribution(work_units, choices)
        print(f"Distribution valid: {is_valid}")
        
        # Show work assignment
        print("Work assignment:")
        for i, unit in enumerate(work_units):
            print(f"  Thread {i}: {len(unit.first_column_choices)} choices")
            if len(unit.first_column_choices) <= 3:
                for choice in unit.first_column_choices:
                    print(f"    {choice}")
            elif len(unit.first_column_choices) > 3:
                print(f"    {unit.first_column_choices[0]} ... {unit.first_column_choices[-1]}")


if __name__ == "__main__":
    main()