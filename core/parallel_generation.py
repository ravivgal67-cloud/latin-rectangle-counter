"""
Parallel Latin rectangle generation using row-based partitioning.

This module provides multiprocessing capabilities for large Latin rectangle
computations (>1M rectangles) by partitioning work across second-row permutations.
Each process handles a subset of second rows and completes all rectangles for those rows.
"""

import multiprocessing as mp
from typing import List, Iterator, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import math

from core.latin_rectangle import generate_normalized_rectangles_bitset_optimized, LatinRectangle
from core.counter import CountResult
from core.bitset_constraints import BitsetConstraints, generate_constrained_permutations_bitset_optimized


def get_valid_second_rows(n: int) -> List[List[int]]:
    """
    Get all valid second row permutations for normalized Latin rectangles.
    
    Uses smart derangement cache when available for instant loading with pre-computed signs,
    falls back to dynamic generation for compatibility.
    
    Args:
        n: Number of columns
        
    Returns:
        List of all valid second row permutations (derangements)
    """
    try:
        # Try to use smart derangement cache for optimized performance
        from core.smart_derangement_cache import get_smart_derangements_with_signs
        derangements_with_signs = get_smart_derangements_with_signs(n)
        # Extract just the derangements (signs will be used elsewhere)
        return [derangement for derangement, sign in derangements_with_signs]
    except (ImportError, ModuleNotFoundError):
        # Fall back to dynamic generation if smart cache not available
        constraints = BitsetConstraints(n)
        constraints.add_row_constraints(list(range(1, n + 1)))
        valid_rows = list(generate_constrained_permutations_bitset_optimized(n, constraints))
        return valid_rows


def count_rectangles_with_fixed_second_row(r: int, n: int, second_row: List[int], 
                                          precomputed_sign: Optional[int] = None) -> Tuple[int, int, int]:
    """
    Count all rectangles with a fixed first and second row.
    
    This function completes all possible rectangles starting with:
    - First row: [1, 2, 3, ..., n] (identity)
    - Second row: given second_row permutation
    
    Args:
        r: Number of rows
        n: Number of columns  
        second_row: Fixed second row permutation
        precomputed_sign: Optional pre-computed sign for r=2 case (optimization)
        
    Returns:
        Tuple of (total_count, positive_count, negative_count)
    """
    if r == 2:
        # For r=2, we just have the two-row rectangle
        if precomputed_sign is not None:
            # Use pre-computed sign for performance
            sign = precomputed_sign
        else:
            # Fall back to dynamic computation
            from core.latin_rectangle import LatinRectangle
            rect = LatinRectangle(2, n, [list(range(1, n + 1)), second_row])
            sign = rect.compute_sign()
        
        if sign > 0:
            return 1, 1, 0
        else:
            return 1, 0, 1
    
    # For r > 2, we need to complete the rectangle
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Build constraints from first two rows
    constraints = BitsetConstraints(n)
    constraints.add_row_constraints(list(range(1, n + 1)))  # First row
    constraints.add_row_constraints(second_row)  # Second row
    
    # Recursively build remaining rows
    def complete_rectangle(partial_rows: List[List[int]], level: int, 
                          current_constraints: BitsetConstraints):
        nonlocal total_count, positive_count, negative_count
        
        if level == r:
            # Complete rectangle - compute sign and count
            from core.latin_rectangle import LatinRectangle
            rect = LatinRectangle(r, n, [row[:] for row in partial_rows])
            sign = rect.compute_sign()
            
            total_count += 1
            if sign > 0:
                positive_count += 1
            else:
                negative_count += 1
            return
        
        # Try to use smart cache for final row optimization
        try:
            from core.smart_derangement_cache import get_constraint_compatible_derangements
            # Use smart cache with pre-computed signs for final row
            if level == r - 1:  # This is the final row
                compatible_derangements = get_constraint_compatible_derangements(n, current_constraints)
                # Get the sign of the second row from smart cache
                second_row_sign = None
                try:
                    from core.smart_derangement_cache import get_smart_derangements_with_signs
                    second_rows_with_signs = get_smart_derangements_with_signs(n)
                    for cached_row, cached_sign in second_rows_with_signs:
                        if cached_row == second_row:
                            second_row_sign = cached_sign
                            break
                except:
                    pass
                
                for next_row, third_row_sign in compatible_derangements:
                    # Direct sign computation without determinant!
                    # Rectangle sign = product of row signs (for normalized rectangles)
                    first_row_sign = 1  # Identity permutation always has sign +1
                    
                    if second_row_sign is not None:
                        # Use pre-computed signs: rectangle_sign = row1_sign * row2_sign * row3_sign
                        rectangle_sign = first_row_sign * second_row_sign * third_row_sign
                    else:
                        # Fallback to determinant calculation
                        partial_rows.append(next_row)
                        from core.latin_rectangle import LatinRectangle
                        rect = LatinRectangle(r, n, [row[:] for row in partial_rows])
                        rectangle_sign = rect.compute_sign()
                        partial_rows.pop()
                    
                    total_count += 1
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
                return  # Skip the general case below
        except (ImportError, ModuleNotFoundError):
            pass
        
        # General case: generate valid next rows using bitset constraints
        valid_next_rows = list(generate_constrained_permutations_bitset_optimized(n, current_constraints))
        
        for next_row in valid_next_rows:
            # Add this row
            partial_rows.append(next_row)
            current_constraints.add_row_constraints(next_row)
            
            # Recurse to next level
            complete_rectangle(partial_rows, level + 1, current_constraints)
            
            # Backtrack
            partial_rows.pop()
            current_constraints.remove_row_constraints(next_row)
    
    # Start completion with first two rows
    initial_rows = [list(range(1, n + 1)), second_row]
    complete_rectangle(initial_rows, 2, constraints)
    
    return total_count, positive_count, negative_count


def process_second_row_partition(r: int, n: int, second_rows_data) -> Tuple[int, int, int, float]:
    """
    Process a partition of second-row permutations with optional pre-computed signs.
    
    This function is designed to be run in a separate process.
    
    Args:
        r: Number of rows
        n: Number of columns
        second_rows_data: Either List[List[int]] (legacy) or List[Tuple[List[int], int]] (with signs)
        
    Returns:
        Tuple of (total_count, positive_count, negative_count, elapsed_time)
    """
    start_time = time.time()
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Handle both legacy format and new format with pre-computed signs
    if second_rows_data and isinstance(second_rows_data[0], tuple):
        # New format: List[Tuple[List[int], int]] with pre-computed signs
        for second_row, precomputed_sign in second_rows_data:
            part_total, part_positive, part_negative = count_rectangles_with_fixed_second_row(
                r, n, second_row, precomputed_sign
            )
            total_count += part_total
            positive_count += part_positive
            negative_count += part_negative
    else:
        # Legacy format: List[List[int]] without signs
        for second_row in second_rows_data:
            part_total, part_positive, part_negative = count_rectangles_with_fixed_second_row(r, n, second_row)
            total_count += part_total
            positive_count += part_positive
            negative_count += part_negative
    
    elapsed_time = time.time() - start_time
    return total_count, positive_count, negative_count, elapsed_time


def count_rectangles_parallel(r: int, n: int, num_processes: Optional[int] = None,
                            min_n: int = 7,
                            rectangles_per_chunk: int = 500000,
                            use_checkpoints: bool = False,
                            checkpoint_interval: int = 100000) -> CountResult:
    """
    Count Latin rectangles using row-based parallel processing for large problems (n≥7).
    
    This function uses row-based partitioning where each process handles a subset
    of second-row permutations and completes all rectangles for those rows.
    This ensures complete coverage with no overlap between processes.
    
    For small problems (n≤6), uses optimized sequential processing without checkpoints
    since these problems complete quickly and don't need resumable computation.
    
    Note: Checkpoints are disabled in this implementation. For checkpoint support,
    use the dedicated resumable computation functions in core.counter module.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        min_n: Minimum n value to justify parallel processing (default: 7)
        rectangles_per_chunk: Unused (kept for compatibility)
        use_checkpoints: Ignored (checkpoints disabled for performance/correctness)
        checkpoint_interval: Ignored (checkpoints disabled)
        
    Returns:
        CountResult with computation results
    """
    start_time = time.time()
    
    # Smart heuristics for parallel processing
    if r == 2:
        print(f"Using single-threaded processing (r=2 problems are always small)")
        use_parallel = False
    elif n < min_n:
        print(f"Using single-threaded processing (n={n} < {min_n})")
        use_parallel = False
    else:
        use_parallel = True
    
    if not use_parallel:
        # Fall back to sequential processing (no checkpoints needed for small problems)
        if use_checkpoints:
            print(f"⚠️  Checkpoints not needed for small problems (n≤{min_n-1}) - running without checkpoints")
        
        total_count = 0
        positive_count = 0
        negative_count = 0
        
        for rect in generate_normalized_rectangles_bitset_optimized(r, n):
            total_count += 1
            sign = rect.compute_sign()
            if sign > 0:
                positive_count += 1
            else:
                negative_count += 1
        
        computation_time = time.time() - start_time
        return CountResult(
            r=r, n=n,
            positive_count=positive_count,
            negative_count=negative_count,
            difference=positive_count - negative_count,
            from_cache=False,
            computation_time=computation_time
        )
    
    # Disable checkpoints for parallel processing (known issues with per-partition checkpointing)
    if use_checkpoints:
        print(f"⚠️  Checkpoints not supported in parallel mode (per-partition checkpointing not yet implemented)")
        print(f"   Running without checkpoints for correctness")
        use_checkpoints = False
    
    # Auto-detect optimal process count
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)
    
    print(f"🚀 Using row-based parallel processing with {num_processes} processes")
    
    # Get all valid second rows with smart cache optimization
    try:
        # Try to use smart derangement cache for maximum performance
        from core.smart_derangement_cache import get_smart_derangements_with_signs
        second_rows_with_signs = get_smart_derangements_with_signs(n)
        print(f"🚀 Using smart derangement cache: {len(second_rows_with_signs):,} derangements with pre-computed signs")
        use_smart_cache = True
    except (ImportError, ModuleNotFoundError):
        # Fall back to legacy approach
        second_rows = get_valid_second_rows(n)
        second_rows_with_signs = [(row, None) for row in second_rows]  # No pre-computed signs
        print(f"Found {len(second_rows):,} valid second-row permutations (dynamic generation)")
        use_smart_cache = False
    
    # Create work partitions by distributing second rows across processes
    total_rows = len(second_rows_with_signs)
    rows_per_process = total_rows // num_processes
    if rows_per_process == 0:
        rows_per_process = 1
        num_processes = total_rows
    
    partitions = []
    for i in range(num_processes):
        start_idx = i * rows_per_process
        if i == num_processes - 1:
            # Last process gets remaining rows
            end_idx = total_rows
        else:
            end_idx = (i + 1) * rows_per_process
        
        if use_smart_cache:
            # Partition with pre-computed signs
            partition_data = second_rows_with_signs[start_idx:end_idx]
        else:
            # Legacy partition format
            partition_data = [row for row, _ in second_rows_with_signs[start_idx:end_idx]]
        
        partitions.append(partition_data)
        print(f"Process {i+1}: {len(partition_data):,} second-row permutations (indices {start_idx}-{end_idx-1})")
    
    # Initialize counts
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Execute in parallel
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit all tasks
        futures = []
        for i, partition_rows in enumerate(partitions):
            future = executor.submit(
                process_second_row_partition, 
                r, n, partition_rows
            )
            futures.append((i, future))
        
        # Collect results as they complete (not in submission order)
        completed = 0
        process_results = {}
        
        for future in as_completed([f for _, f in futures]):
            try:
                # Find which process this future belongs to
                process_id = None
                for i, (pid, fut) in enumerate(futures):
                    if fut == future:
                        process_id = pid
                        break
                
                part_total, part_positive, part_negative, part_time = future.result()
                total_count += part_total
                positive_count += part_positive
                negative_count += part_negative
                
                completed += 1
                process_results[process_id] = {
                    'total': part_total,
                    'positive': part_positive,
                    'negative': part_negative,
                    'time': part_time
                }
                
                # Show per-process completion with details
                print(f"✅ Process {process_id+1}/{num_processes} complete: {part_total:,} rectangles (+{part_positive:,} -{part_negative:,}) in {part_time:.2f}s")
                
                # Show overall progress
                progress_pct = (completed / num_processes) * 100
                print(f"📊 Overall progress: {completed}/{num_processes} processes ({progress_pct:.0f}%) - {total_count:,} total rectangles")
                
            except Exception as e:
                print(f"❌ Process failed: {e}")
                # Continue with other processes
    
    computation_time = time.time() - start_time
    
    # Show final summary with per-process breakdown
    print(f"\n📋 PARALLEL COMPUTATION SUMMARY:")
    print(f"   Total time: {computation_time:.2f}s")
    print(f"   Total rectangles: {total_count:,}")
    print(f"   Result: +{positive_count:,} -{negative_count:,} (difference: {positive_count - negative_count:+,})")
    
    if process_results:
        print(f"\n📊 Per-process breakdown:")
        for proc_id in sorted(process_results.keys()):
            result = process_results[proc_id]
            rate = result['total'] / result['time'] if result['time'] > 0 else 0
            print(f"   Process {proc_id+1}: {result['total']:,} rectangles (+{result['positive']:,} -{result['negative']:,}) in {result['time']:.2f}s ({rate:,.0f} rect/s)")
    
    print(f"\n✅ Row-based parallel computation complete!")
    
    return CountResult(
        r=r, n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=positive_count - negative_count,
        from_cache=False,
        computation_time=computation_time
    )


def _dummy_work(size: int) -> int:
    """Dummy work function for benchmarking (must be at module level for pickling)."""
    return sum(1 for _ in range(size))


def _generate_rectangles_sample(r: int, n: int, sample_size: int) -> Tuple[int, float]:
    """Generate a sample of rectangles for benchmarking (must be at module level)."""
    start_time = time.time()
    count = 0
    positive_count = 0
    
    for rect in generate_normalized_rectangles_bitset_optimized(r, n):
        count += 1
        if rect.compute_sign() > 0:
            positive_count += 1
        if count >= sample_size:
            break
    
    elapsed = time.time() - start_time
    return count, positive_count, elapsed


def benchmark_parallel_vs_sequential(r: int, n: int, sample_size: int = 100000) -> dict:
    """
    Benchmark parallel vs sequential performance.
    
    Args:
        r: Number of rows
        n: Number of columns
        sample_size: Number of rectangles to process in benchmark
        
    Returns:
        Dictionary with benchmark results
    """
    print(f"Benchmarking ({r},{n}) with {sample_size:,} rectangles...")
    
    # Sequential benchmark
    print("Testing sequential performance...")
    count, positive_count, sequential_time = _generate_rectangles_sample(r, n, sample_size)
    sequential_rate = count / sequential_time if sequential_time > 0 else 0
    
    # Parallel benchmark - test actual rectangle generation
    print("Testing parallel performance...")
    start_time = time.time()
    
    num_processes = min(mp.cpu_count(), 4)  # Use fewer processes for testing
    partition_size = sample_size // num_processes
    
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = []
        for i in range(num_processes):
            future = executor.submit(_generate_rectangles_sample, r, n, partition_size)
            futures.append(future)
        
        total_count = 0
        total_positive = 0
        for future in futures:
            part_count, part_positive, _ = future.result()
            total_count += part_count
            total_positive += part_positive
    
    parallel_time = time.time() - start_time
    parallel_rate = total_count / parallel_time if parallel_time > 0 else 0
    
    return {
        'sequential_time': sequential_time,
        'sequential_rate': sequential_rate,
        'parallel_time': parallel_time,
        'parallel_rate': parallel_rate,
        'speedup': parallel_rate / sequential_rate if sequential_rate > 0 else 0,
        'num_processes': num_processes,
        'sample_size': count,
        'efficiency': (parallel_rate / sequential_rate) / num_processes if sequential_rate > 0 else 0
    }


def should_use_parallel(r: int, n: int) -> bool:
    """
    Determine if parallel processing should be used for given dimensions.
    
    Args:
        r: Number of rows
        n: Number of columns
        
    Returns:
        True if parallel processing is recommended
    """
    return r != 2 and n >= 7


def count_rectangles_auto(r: int, n: int, num_processes: Optional[int] = None) -> CountResult:
    """
    Count rectangles with automatic parallel/sequential selection.
    
    This is the main entry point that automatically chooses the best approach
    based on problem size.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes (None = auto-detect)
        
    Returns:
        CountResult with computation results
    """
    if should_use_parallel(r, n):
        print(f"🚀 Large problem ({r},{n}) detected - using row-based parallel processing")
        return count_rectangles_parallel(r, n, num_processes)
    else:
        print(f"⚡ Standard problem ({r},{n}) - using optimized sequential processing")
        # Use the standard optimized sequential approach
        start_time = time.time()
        
        total_count = 0
        positive_count = 0
        negative_count = 0
        
        for rect in generate_normalized_rectangles_bitset_optimized(r, n):
            total_count += 1
            sign = rect.compute_sign()
            if sign > 0:
                positive_count += 1
            else:
                negative_count += 1
        
        computation_time = time.time() - start_time
        return CountResult(
            r=r, n=n,
            positive_count=positive_count,
            negative_count=negative_count,
            difference=positive_count - negative_count,
            from_cache=False,
            computation_time=computation_time
        )


if __name__ == "__main__":
    # Test the parallel implementation
    print("Testing automatic parallel/sequential selection...")
    
    # Test on n<7 (should use sequential)
    print("\n📊 Testing (4,6) - should use sequential:")
    result1 = count_rectangles_auto(4, 6)
    print(f"Result: {result1.positive_count + result1.negative_count:,} rectangles in {result1.computation_time:.2f}s")
    
    # Test on n≥7 (should use parallel)  
    print("\n📊 Testing (3,7) - should use parallel:")
    result2 = count_rectangles_auto(3, 7)
    print(f"Result: {result2.positive_count + result2.negative_count:,} rectangles in {result2.computation_time:.2f}s")