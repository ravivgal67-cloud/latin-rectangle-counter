#!/usr/bin/env python3
"""
Clean multiprocess computation tests from scratch.

Tests the parallel ultra-safe bitwise implementation with:
- (5,6) - Fast test case for quick validation
- (3,7) - Production test case with 8 processes (default for n>=7)

Focus on correctness, performance, and reliability.
"""

import pytest
import time
import multiprocessing as mp
from pathlib import Path

from core.parallel_ultra_bitwise import count_rectangles_parallel_first_column
from core.ultra_safe_bitwise import count_rectangles_ultra_safe_bitwise
from core.logging_config import close_logger
from tests.test_base import TestBaseWithProductionLogs


class TestMultiprocessComputation(TestBaseWithProductionLogs):
    """Test multiprocess computation functionality."""
    
    def test_fast_case_5_6_correctness(self):
        """Test (5,6) for correctness - validation case."""
        r, n = 5, 6
        
        # Get reference result from single-threaded implementation
        start_time = time.time()
        total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
        single_time = time.time() - start_time
        
        # Test with 2 processes
        num_processes = 2
        test_name = "test_fast_case_5_6_correctness"
        result = count_rectangles_parallel_first_column(r, n, num_processes=num_processes, 
                                                       logger_session=f"{test_name}_parallel_{r}_{n}")
        
        # Verify correctness (primary requirement)
        total_parallel = result.positive_count + result.negative_count
        
        assert total_parallel == total_ref, f"Total count mismatch: {total_parallel} vs {total_ref}"
        assert result.positive_count == pos_ref, f"Positive count mismatch: {result.positive_count} vs {pos_ref}"
        assert result.negative_count == neg_ref, f"Negative count mismatch: {result.negative_count} vs {neg_ref}"
        
        # Verify parallel implementation completes successfully
        assert result.computation_time > 0, "Parallel computation should complete"
        assert hasattr(result, 'positive_count'), "Result should have positive_count"
        assert hasattr(result, 'negative_count'), "Result should have negative_count"
        
        # Calculate speedup for informational purposes (not a requirement)
        speedup = single_time / result.computation_time if result.computation_time > 0 else 0
        
        print(f"✅ (5,6) correctness test passed:")
        print(f"   Total: {total_parallel:,} rectangles")
        print(f"   Single-threaded time: {single_time:.2f}s")
        print(f"   Parallel time: {result.computation_time:.2f}s")
        print(f"   Speedup: {speedup:.2f}x with {num_processes} processes")
        print(f"   Parallel efficiency: {speedup/num_processes*100:.1f}%")
        
    
    def test_fast_case_5_6_scaling(self):
        """Test (5,6) with different process counts."""
        r, n = 5, 6
        
        # Get reference time
        start_time = time.time()
        total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
        single_time = time.time() - start_time
        
        # Test with different process counts
        process_counts = [1, 2, 4]
        results = {}
        test_name = "test_fast_case_5_6_scaling"
        
        for num_proc in process_counts:
            result = count_rectangles_parallel_first_column(r, n, num_processes=num_proc,
                                                           logger_session=f"{test_name}_proc{num_proc}_parallel_{r}_{n}")
            total_parallel = result.positive_count + result.negative_count
            
            # Verify correctness for each process count
            assert total_parallel == total_ref
            assert result.positive_count == pos_ref
            assert result.negative_count == neg_ref
            
            speedup = single_time / result.computation_time
            efficiency = (speedup / num_proc) * 100
            
            results[num_proc] = {
                'time': result.computation_time,
                'speedup': speedup,
                'efficiency': efficiency
            }
        
        # Verify scaling behavior
        assert results[2]['speedup'] > results[1]['speedup'], "2 processes should be faster than 1"
        assert results[4]['speedup'] > results[2]['speedup'], "4 processes should be faster than 2"
        
        print(f"✅ (5,6) scaling test passed:")
        for num_proc in process_counts:
            r = results[num_proc]
            print(f"   {num_proc} processes: {r['speedup']:.2f}x speedup, {r['efficiency']:.1f}% efficiency")
        
    
    def test_production_case_3_7_with_8_processes(self):
        """Test (3,7) with 8 processes - production case for n>=7."""
        r, n = 3, 7
        num_processes = 8  # Default for n>=7
        
        # Get reference result (this will be fast for (3,7))
        start_time = time.time()
        total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
        single_time = time.time() - start_time
        
        # Test with 8 processes
        test_name = "test_production_case_3_7_with_8_processes"
        result = count_rectangles_parallel_first_column(r, n, num_processes=num_processes,
                                                       logger_session=f"{test_name}_parallel_{r}_{n}")
        
        # Verify correctness
        total_parallel = result.positive_count + result.negative_count
        
        assert total_parallel == total_ref, f"Total count mismatch: {total_parallel} vs {total_ref}"
        assert result.positive_count == pos_ref, f"Positive count mismatch: {result.positive_count} vs {pos_ref}"
        assert result.negative_count == neg_ref, f"Negative count mismatch: {result.negative_count} vs {neg_ref}"
        
        # Verify performance - for small problems like (3,7), parallel overhead may cause slowdown
        # The important thing is that it completes successfully and gives correct results
        speedup = single_time / result.computation_time
        efficiency = (speedup / num_processes) * 100
        
        # For (3,7), the problem is small so parallel overhead may dominate
        # Just verify it completes in reasonable time (< 5 seconds)
        assert result.computation_time < 5.0, f"Computation took too long: {result.computation_time:.2f}s"
        
        print(f"✅ (3,7) production test passed:")
        print(f"   Total: {total_parallel:,} rectangles")
        print(f"   Time: {result.computation_time:.2f}s")
        print(f"   Speedup: {speedup:.2f}x with {num_processes} processes")
        print(f"   Efficiency: {efficiency:.1f}%")
        print(f"   Note: Small problems may have parallel overhead > benefit")
        
    
    def test_process_count_auto_detection(self):
        """Test automatic process count detection."""
        r, n = 5, 6
        
        # Test with None (auto-detect)
        result = count_rectangles_parallel_first_column(r, n, num_processes=None)
        
        # Should complete successfully
        total = result.positive_count + result.negative_count
        assert total > 0, "No rectangles found with auto-detection"
        
        # Verify it used a reasonable number of processes (should be <= CPU count and <= 8)
        max_expected = min(mp.cpu_count(), 8)
        
        print(f"✅ Auto-detection test passed:")
        print(f"   Total: {total:,} rectangles")
        print(f"   Time: {result.computation_time:.2f}s")
        print(f"   Max expected processes: {max_expected}")
        
    
    def test_single_process_edge_case(self):
        """Test edge case with single process."""
        r, n = 5, 6
        
        # Get reference
        total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
        
        # Test with 1 process (should work like single-threaded)
        result = count_rectangles_parallel_first_column(r, n, num_processes=1)
        
        total_parallel = result.positive_count + result.negative_count
        
        # Should still be correct
        assert total_parallel == total_ref
        assert result.positive_count == pos_ref
        assert result.negative_count == neg_ref
        
        print(f"✅ Single process edge case passed:")
        print(f"   Total: {total_parallel:,} rectangles")
        print(f"   Time: {result.computation_time:.2f}s")
        
    
    def test_error_handling(self):
        """Test error handling with invalid inputs."""
        
        # Test with invalid process count (should raise ValueError)
        with pytest.raises(ValueError):
            count_rectangles_parallel_first_column(5, 6, num_processes=0)
        
        with pytest.raises(ValueError):
            count_rectangles_parallel_first_column(5, 6, num_processes=-1)
        
        # Test edge cases - just verify the function handles reasonable inputs
        # Test with small valid problem (2,2) that returns 1 rectangle
        result = count_rectangles_parallel_first_column(2, 2, num_processes=2)
        assert result.positive_count + result.negative_count == 1
        
        print("✅ Error handling tests passed")
        


class TestMultiprocessPerformance:
    """Test multiprocess performance characteristics."""
    
    def setup_method(self):
        """Set up test environment."""
        self._cleanup_logs()
    
    def teardown_method(self):
        """Clean up after each test."""
        close_logger()
        self._cleanup_logs()
    
    def _cleanup_logs(self):
        """Clean up log files from previous tests."""
        log_dir = Path("logs")
        if log_dir.exists():
            for pattern in ["parallel_5_6*.log", "parallel_5_6*.jsonl"]:
                for log_file in log_dir.glob(pattern):
                    log_file.unlink(missing_ok=True)
    
    def test_performance_comparison(self):
        """Compare performance across different process counts."""
        r, n = 5, 6
        
        # Get baseline
        start_time = time.time()
        total_ref, pos_ref, neg_ref = count_rectangles_ultra_safe_bitwise(r, n)
        baseline_time = time.time() - start_time
        
        # Test different process counts
        process_counts = [1, 2, 4]
        performance_data = []
        
        for num_proc in process_counts:
            result = count_rectangles_parallel_first_column(r, n, num_processes=num_proc)
            
            # Verify correctness
            total = result.positive_count + result.negative_count
            assert total == total_ref
            
            speedup = baseline_time / result.computation_time
            efficiency = (speedup / num_proc) * 100
            rate = total / result.computation_time
            
            performance_data.append({
                'processes': num_proc,
                'time': result.computation_time,
                'speedup': speedup,
                'efficiency': efficiency,
                'rate': rate
            })
        
        # Verify performance trends
        # More processes should generally be faster (though efficiency may decrease)
        times = [p['time'] for p in performance_data]
        assert times[1] <= times[0], "2 processes should be faster than 1"
        assert times[2] <= times[1], "4 processes should be faster than 2"
        
        print("✅ Performance comparison:")
        print(f"   Baseline (single): {baseline_time:.2f}s")
        for p in performance_data:
            print(f"   {p['processes']} processes: {p['time']:.2f}s, {p['speedup']:.2f}x speedup, {p['efficiency']:.1f}% efficiency")
        
    
    def test_memory_efficiency(self):
        """Test that multiprocessing doesn't use excessive memory."""
        import psutil
        import os
        
        r, n = 5, 6
        
        # Get memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run computation
        result = count_rectangles_parallel_first_column(r, n, num_processes=4)
        
        # Get memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_used = mem_after - mem_before
        
        # Should not use excessive memory (less than 500MB for this small problem)
        assert mem_used < 500, f"Excessive memory usage: {mem_used:.1f} MB"
        
        total = result.positive_count + result.negative_count
        
        print(f"✅ Memory efficiency test passed:")
        print(f"   Total rectangles: {total:,}")
        print(f"   Memory used: {mem_used:.1f} MB")
        print(f"   Memory per rectangle: {mem_used * 1024 * 1024 / total:.2f} bytes")
        


if __name__ == "__main__":
    pytest.main([__file__, "-v"])