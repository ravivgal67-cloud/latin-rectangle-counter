#!/usr/bin/env python3
"""
First Column Optimization - Main Coordinator.

This module coordinates the complete first column optimization system,
integrating enumeration, work distribution, and result aggregation.
"""

import time
import math
from typing import Tuple, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from core.first_column_enumerator import FirstColumnEnumerator
from core.work_distributor import WorkDistributor, WorkUnit
from core.constrained_enumerator import ConstrainedEnumerator


@dataclass
class OptimizationResult:
    """Results from first column optimization."""
    total_positive: int
    total_negative: int
    difference: int
    processing_time: float
    rectangles_per_second: float
    first_columns_processed: int
    symmetry_factor: int
    work_units_processed: int
    
    @property
    def total_rectangles(self) -> int:
        """Total rectangles processed."""
        return self.total_positive + self.total_negative


class FirstColumnOptimizer:
    """
    Main coordinator for first column optimization.
    
    Orchestrates the complete optimization pipeline:
    1. Generate first column choices
    2. Distribute work across threads
    3. Enumerate rectangles with constraints
    4. Apply symmetry factors
    5. Aggregate results
    """
    
    def __init__(self, num_threads: int = 8):
        """
        Initialize the optimizer.
        
        Args:
            num_threads: Number of threads to use for parallel processing
        """
        self.num_threads = num_threads
        self.enumerator = FirstColumnEnumerator()
        self.distributor = WorkDistributor()
        self.constrained_enumerator = ConstrainedEnumerator()
    
    def count_rectangles_optimized(self, r: int, n: int) -> OptimizationResult:
        """
        Count Latin rectangles using first column optimization.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            OptimizationResult with complete statistics
        """
        start_time = time.time()
        
        print(f"🚀 Starting first column optimization for ({r},{n})")
        print(f"   Using {self.num_threads} threads")
        
        # Step 1: Generate first column choices
        print(f"📋 Step 1: Generating first column choices...")
        first_columns = self.enumerator.enumerate_first_columns(r, n)
        symmetry_factor = self.enumerator.get_symmetry_factor(r)
        
        print(f"   Generated {len(first_columns)} first column choices")
        print(f"   Symmetry factor: {symmetry_factor} (each choice represents {symmetry_factor} rectangles)")
        
        # Step 2: Distribute work across threads
        print(f"📦 Step 2: Distributing work across {self.num_threads} threads...")
        work_units = self.distributor.distribute_work(first_columns, self.num_threads)
        
        stats = self.distributor.get_distribution_stats(work_units)
        print(f"   Work distribution: {stats['work_distribution']}")
        print(f"   Balanced: {stats['is_balanced']}")
        
        # Step 3: Process work units in parallel
        print(f"⚡ Step 3: Processing work units in parallel...")
        
        if self.num_threads == 1:
            # Single-threaded execution
            results = [self._process_work_unit(work_units[0], r, n, symmetry_factor)]
        else:
            # Multi-threaded execution
            results = self._process_work_units_parallel(work_units, r, n, symmetry_factor)
        
        # Step 4: Aggregate results
        print(f"📊 Step 4: Aggregating results...")
        total_positive = sum(result['positive'] for result in results)
        total_negative = sum(result['negative'] for result in results)
        total_work_units = sum(result['work_units'] for result in results)
        
        # Calculate final statistics
        processing_time = time.time() - start_time
        total_rectangles = total_positive + total_negative
        rectangles_per_second = total_rectangles / processing_time if processing_time > 0 else 0
        
        result = OptimizationResult(
            total_positive=total_positive,
            total_negative=total_negative,
            difference=total_positive - total_negative,
            processing_time=processing_time,
            rectangles_per_second=rectangles_per_second,
            first_columns_processed=len(first_columns),
            symmetry_factor=symmetry_factor,
            work_units_processed=total_work_units
        )
        
        print(f"✅ Optimization complete!")
        print(f"   Total rectangles: {total_rectangles:,}")
        print(f"   Positive: {total_positive:,}")
        print(f"   Negative: {total_negative:,}")
        print(f"   Difference: {result.difference:+,}")
        print(f"   Processing time: {processing_time:.3f}s")
        print(f"   Rate: {rectangles_per_second:,.0f} rectangles/second")
        
        return result
    
    def _process_work_units_parallel(self, work_units: List[WorkUnit], r: int, n: int, 
                                   symmetry_factor: int) -> List[Dict[str, Any]]:
        """Process work units in parallel using ThreadPoolExecutor."""
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            # Submit all work units
            future_to_unit = {
                executor.submit(self._process_work_unit, unit, r, n, symmetry_factor): unit
                for unit in work_units
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_unit):
                unit = future_to_unit[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"   Thread {unit.thread_id}: {result['work_units']} work units, "
                          f"{result['positive'] + result['negative']:,} rectangles")
                except Exception as e:
                    print(f"   Thread {unit.thread_id} failed: {e}")
                    results.append({'positive': 0, 'negative': 0, 'work_units': 0})
        
        return results
    
    def _process_work_unit(self, work_unit: WorkUnit, r: int, n: int, 
                          symmetry_factor: int) -> Dict[str, Any]:
        """
        Process a single work unit (one thread's worth of first column choices).
        
        Args:
            work_unit: Work unit to process
            r: Number of rows
            n: Number of columns
            symmetry_factor: Symmetry factor to apply for row interchange equivalence
            
        Returns:
            Dictionary with processing results
        """
        total_positive = 0
        total_negative = 0
        work_units_processed = 0
        
        for first_column in work_unit.first_column_choices:
            try:
                # Enumerate rectangles for this canonical first column choice
                positive, negative = self.constrained_enumerator.enumerate_with_fixed_first_column(
                    r, n, first_column
                )
                
                # Apply symmetry factor: each canonical first column choice represents
                # (r-1)! equivalent rectangles due to row interchange symmetry
                total_positive += positive * symmetry_factor
                total_negative += negative * symmetry_factor
                work_units_processed += 1
                
            except Exception as e:
                print(f"   Error processing first column {first_column}: {e}")
                # Continue with other work units
        
        return {
            'positive': total_positive,
            'negative': total_negative,
            'work_units': work_units_processed
        }
    
    def compare_with_baseline(self, r: int, n: int) -> Dict[str, Any]:
        """
        Compare optimized algorithm with baseline implementation.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            Comparison statistics
        """
        print(f"🔬 Comparing first column optimization vs baseline for ({r},{n})")
        
        # Run optimized version
        print(f"\n--- Running Optimized Version ---")
        optimized_result = self.count_rectangles_optimized(r, n)
        
        # Run baseline version
        print(f"\n--- Running Baseline Version ---")
        baseline_start = time.time()
        
        try:
            from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise
            baseline_total, baseline_positive, baseline_negative = count_rectangles_ultra_safe_bitwise(r, n)
            baseline_time = time.time() - baseline_start
            baseline_rate = baseline_total / baseline_time if baseline_time > 0 else 0
            
            print(f"✅ Baseline complete!")
            print(f"   Total rectangles: {baseline_total:,}")
            print(f"   Positive: {baseline_positive:,}")
            print(f"   Negative: {baseline_negative:,}")
            print(f"   Difference: {baseline_positive - baseline_negative:+,}")
            print(f"   Processing time: {baseline_time:.3f}s")
            print(f"   Rate: {baseline_rate:,.0f} rectangles/second")
            
        except Exception as e:
            print(f"❌ Baseline failed: {e}")
            return {'error': str(e)}
        
        # Compare results
        print(f"\n--- Comparison Results ---")
        
        # Correctness check
        results_match = (
            optimized_result.total_rectangles == baseline_total and
            optimized_result.total_positive == baseline_positive and
            optimized_result.total_negative == baseline_negative
        )
        
        # Performance comparison
        speedup = optimized_result.rectangles_per_second / baseline_rate if baseline_rate > 0 else 0
        time_ratio = baseline_time / optimized_result.processing_time if optimized_result.processing_time > 0 else 0
        
        comparison = {
            'correctness_match': results_match,
            'optimized_time': optimized_result.processing_time,
            'baseline_time': baseline_time,
            'speedup_factor': speedup,
            'time_ratio': time_ratio,
            'optimized_rate': optimized_result.rectangles_per_second,
            'baseline_rate': baseline_rate,
            'work_reduction': f"{14833 / optimized_result.first_columns_processed:.1f}x" if r == 5 and n == 8 else "N/A"
        }
        
        print(f"Correctness: {'✅ PASS' if results_match else '❌ FAIL'}")
        print(f"Speedup: {speedup:.2f}x")
        print(f"Time ratio: {time_ratio:.2f}x")
        print(f"Work reduction: {comparison['work_reduction']}")
        
        if not results_match:
            print(f"❌ CORRECTNESS MISMATCH:")
            print(f"   Optimized: {optimized_result.total_positive:,} pos, {optimized_result.total_negative:,} neg")
            print(f"   Baseline:  {baseline_positive:,} pos, {baseline_negative:,} neg")
        
        return comparison


def main():
    """
    Test the complete first column optimization system.
    """
    optimizer = FirstColumnOptimizer(num_threads=4)
    
    # Test cases - start with small dimensions
    test_cases = [(3, 4), (3, 5), (4, 5)]
    
    for r, n in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing First Column Optimization: ({r},{n})")
        print(f"{'='*60}")
        
        try:
            # Test optimization
            result = optimizer.count_rectangles_optimized(r, n)
            
            # Compare with baseline if possible
            if r <= 6 and n <= 8:  # Only compare for dimensions we know work
                comparison = optimizer.compare_with_baseline(r, n)
                
                if comparison.get('correctness_match', False):
                    print(f"🎯 SUCCESS: Results match baseline with {comparison['speedup_factor']:.2f}x speedup")
                else:
                    print(f"⚠️  WARNING: Results don't match baseline")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()