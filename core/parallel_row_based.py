"""
Row-based parallel Latin rectangle generation.

This module implements parallel processing by partitioning on the second row.
Each process handles a subset of second-row permutations and completes
all rectangles for those second rows.
"""

import multiprocessing as mp
from typing import List, Iterator, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from core.latin_rectangle import generate_normalized_rectangles_bitset_optimized, LatinRectangle
from core.counter import CountResult
from core.bitset_constraints import BitsetConstraints, generate_constrained_permutations_bitset_optimized


def get_valid_second_rows(n: int) -> List[List[int]]:
    """
    Get all valid second row permutations for normalized Latin rectangles.
    
    Args:
        n: Number of columns
        
    Returns:
        List of all valid second row permutations
    """
    # Build constraints from identity first row [1,2,3,...,n]
    constraints = BitsetConstraints(n)
    constraints.add_row_constraints(list(range(1, n + 1)))
    
    # Generate all valid second row permutations
    valid_rows = list(generate_constrained_permutations_bitset_optimized(n, constraints))
    return valid_rows


def count_rectangles_with_fixed_second_row(r: int, n: int, second_row: List[int]) -> Tuple[int, int, int]:
    """
    Count all rectangles with a fixed first and second row.
    
    This function completes all possible rectangles starting with:
    - First row: [1, 2, 3, ..., n] (identity)
    - Second row: given second_row permutation
    
    Args:
        r: Number of rows
        n: Number of columns  
        second_row: Fixed second row permutation
        
    Returns:
        Tuple of (total_count, positive_count, negative_count)
    """
    if r == 2:
        # For r=2, we just have the two-row rectangle
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
        
        # Generate valid next rows
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


def count_rectangles_parallel_row_based(r: int, n: int, num_processes: Optional[int] = None,
                                       min_n: int = 7) -> CountResult:
    """
    Count Latin rectangles using row-based parallel processing.
    
    This implementation partitions work by second-row permutations, ensuring
    complete coverage with no overlap between processes.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        min_n: Minimum n value to justify parallel processing (default: 7)
        
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
        # Fall back to sequential processing
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
    
    # Auto-detect optimal process count
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)
    
    print(f"🚀 Using row-based parallel processing with {num_processes} processes")
    
    # Get all valid second rows
    second_rows = get_valid_second_rows(n)
    print(f"Found {len(second_rows):,} valid second-row permutations")
    
    # Create work partitions by distributing second rows across processes
    rows_per_process = len(second_rows) // num_processes
    if rows_per_process == 0:
        rows_per_process = 1
        num_processes = len(second_rows)
    
    partitions = []
    for i in range(num_processes):
        start_idx = i * rows_per_process
        if i == num_processes - 1:
            # Last process gets remaining rows
            end_idx = len(second_rows)
        else:
            end_idx = (i + 1) * rows_per_process
        
        partition_rows = second_rows[start_idx:end_idx]
        partitions.append(partition_rows)
        print(f"Process {i+1}: {len(partition_rows):,} second-row permutations (indices {start_idx}-{end_idx-1})")
    
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
        
        # Collect results as they complete
        completed = 0
        for i, future in futures:
            try:
                part_total, part_positive, part_negative = future.result()
                total_count += part_total
                positive_count += part_positive
                negative_count += part_negative
                
                completed += 1
                print(f"Process {completed}/{num_processes} complete: {part_total:,} rectangles")
                
            except Exception as e:
                print(f"Process {i+1} failed: {e}")
                # Continue with other processes
    
    computation_time = time.time() - start_time
    
    print(f"✅ Row-based parallel computation complete: {total_count:,} total rectangles in {computation_time:.2f}s")
    
    return CountResult(
        r=r, n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=positive_count - negative_count,
        from_cache=False,
        computation_time=computation_time
    )


def process_second_row_partition(r: int, n: int, second_rows: List[List[int]]) -> Tuple[int, int, int]:
    """
    Process a partition of second-row permutations.
    
    This function is designed to be run in a separate process.
    
    Args:
        r: Number of rows
        n: Number of columns
        second_rows: List of second-row permutations to process
        
    Returns:
        Tuple of (total_count, positive_count, negative_count)
    """
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    for second_row in second_rows:
        part_total, part_positive, part_negative = count_rectangles_with_fixed_second_row(r, n, second_row)
        total_count += part_total
        positive_count += part_positive
        negative_count += part_negative
    
    return total_count, positive_count, negative_count


if __name__ == "__main__":
    # Test the row-based parallel implementation
    print("Testing row-based parallel implementation...")
    
    # Test on (3,7)
    print("\n📊 Testing (3,7) with row-based parallel:")
    result = count_rectangles_parallel_row_based(3, 7)
    print(f"Result: +{result.positive_count:,} -{result.negative_count:,} diff={result.difference:,} in {result.computation_time:.2f}s")
    
    # Compare with cached result
    from cache.cache_manager import CacheManager
    cache = CacheManager()
    cached = cache.get(3, 7)
    if cached:
        cached_total = cached.positive_count + cached.negative_count
        result_total = result.positive_count + result.negative_count
        print(f"\nComparison with cached result:")
        print(f"Cached:    +{cached.positive_count:,} -{cached.negative_count:,} total={cached_total:,}")
        print(f"Parallel:  +{result.positive_count:,} -{result.negative_count:,} total={result_total:,}")
        
        if (result.positive_count == cached.positive_count and 
            result.negative_count == cached.negative_count):
            print("✅ Perfect match!")
        else:
            print("❌ Mismatch detected!")