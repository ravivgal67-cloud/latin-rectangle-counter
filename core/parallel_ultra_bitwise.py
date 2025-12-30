"""
Parallel Latin rectangle counting using ultra-safe bitwise operations.

This module integrates the ultra-safe bitwise approach with parallel processing
by partitioning work across first-column choices for enhanced performance.
"""

import multiprocessing as mp
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from core.smart_derangement_cache import get_smart_derangements_with_signs, SmartDerangementCache
from core.counter import CountResult
from core.first_column_enumerator import FirstColumnEnumerator
from core.constrained_enumerator import ConstrainedEnumerator
from core.symmetry_calculator import SymmetryCalculator


def count_rectangles_first_column_sequential(r: int, n: int) -> Tuple[int, int, int]:
    """
    Sequential first-column optimization - the optimized baseline.
    
    This uses first-column optimization to achieve better performance than
    the main trunk sequential algorithm.
    
    Returns:
        Tuple of (total_count, positive_count, negative_count)
    """
    # Generate first column choices
    enumerator = FirstColumnEnumerator()
    first_columns = enumerator.enumerate_first_columns(r, n)
    symmetry_calculator = SymmetryCalculator()
    symmetry_factor = symmetry_calculator.get_symmetry_factor(r)
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Process each first column choice sequentially
    for first_column in first_columns:
        # Use the constrained enumerator for this first column
        from core.constrained_enumerator import ConstrainedEnumerator
        constrained_enumerator = ConstrainedEnumerator()
        
        pos, neg = constrained_enumerator.enumerate_with_fixed_first_column(r, n, first_column)
        
        # Apply symmetry factor
        pos_with_symmetry = pos * symmetry_factor
        neg_with_symmetry = neg * symmetry_factor
        
        total_count += pos_with_symmetry + neg_with_symmetry
        positive_count += pos_with_symmetry
        negative_count += neg_with_symmetry
    
    return total_count, positive_count, negative_count


def count_rectangles_first_column_worker(r: int, n: int, 
                                        first_column_indices: List[int],
                                        process_id: int = 0) -> Tuple[int, int, int, float]:
    """
    Worker function that processes a subset of first-column choices.
    
    This distributes first-column choices across processes for realistic
    parallel speedups while maintaining the first-column optimization benefits.
    
    Args:
        r: Number of rows
        n: Number of columns
        first_column_indices: Indices of first-column choices to process
        process_id: Process identifier
        
    Returns:
        Tuple of (total_count, positive_count, negative_count, elapsed_time)
    """
    start_time = time.time()
    
    # Generate all first column choices (same in each process)
    enumerator = FirstColumnEnumerator()
    all_first_columns = enumerator.enumerate_first_columns(r, n)
    symmetry_calculator = SymmetryCalculator()
    symmetry_factor = symmetry_calculator.get_symmetry_factor(r)
    
    # Initialize constrained enumerator
    from core.constrained_enumerator import ConstrainedEnumerator
    constrained_enumerator = ConstrainedEnumerator()
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Process only the assigned first column choices
    for idx in first_column_indices:
        first_column = all_first_columns[idx]
        
        # Count rectangles for this first column choice
        pos, neg = constrained_enumerator.enumerate_with_fixed_first_column(r, n, first_column)
        
        # Apply symmetry factor
        pos_with_symmetry = pos * symmetry_factor
        neg_with_symmetry = neg * symmetry_factor
        
        total_count += pos_with_symmetry + neg_with_symmetry
        positive_count += pos_with_symmetry
        negative_count += neg_with_symmetry
    
    elapsed_time = time.time() - start_time
    return total_count, positive_count, negative_count, elapsed_time


def count_rectangles_ultra_bitwise_partition(r: int, n: int, 
                                             second_row_indices: List[int],
                                             process_id: int = 0,
                                             logger_session: str = None) -> Tuple[int, int, int, float]:
    """
    Count rectangles for a partition of second rows using ultra-safe bitwise.
    
    This function processes a subset of second-row derangements and counts
    all rectangles that start with those second rows.
    
    Args:
        r: Number of rows
        n: Number of columns
        second_row_indices: List of indices into the derangements array
        
    Returns:
        Tuple of (total_count, positive_count, negative_count, elapsed_time)
    """
    start_time = time.time()
    
    # Set up process-local logger (each process gets its own logger instance)
    from core.logging_config import ProgressLogger
    if logger_session:
        logger = ProgressLogger(f"{logger_session}_process_{process_id}")
    else:
        logger = ProgressLogger(f"parallel_{r}_{n}_process_{process_id}")
    
    # Register this process for progress tracking
    total_work = len(second_row_indices)
    logger.register_process(process_id, total_work, f"Processing {total_work:,} second-row derangements")
    
    # Progress tracking
    last_progress_time = start_time
    progress_interval = 30  # 30 seconds for production - reasonable progress updates
    inner_progress_counter = 0  # Track inner loop iterations
    processed_count = 0
    
    # Load smart derangements (cached, so fast)
    # Use get_smart_derangement_cache to avoid double-loading
    from core.smart_derangement_cache import get_smart_derangement_cache
    cache = get_smart_derangement_cache(n)
    derangements_with_signs = cache.get_all_derangements_with_signs()
    num_derangements = len(derangements_with_signs)
    
    # Get position-value index for conflict masks
    position_value_index = cache.position_value_index
    
    conflict_masks = {}
    for pos in range(n):
        for val in range(1, n + 1):
            conflict_key = (pos, val)
            if conflict_key in position_value_index:
                mask = 0
                for conflict_idx in position_value_index[conflict_key]:
                    mask |= (1 << conflict_idx)
                conflict_masks[conflict_key] = mask
            else:
                conflict_masks[conflict_key] = 0
    
    all_valid_mask = (1 << num_derangements) - 1
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    first_sign = 1  # Identity permutation
    
    # Process each second row in this partition
    for second_idx in second_row_indices:
        processed_count += 1
        
        # Log start of processing this second row
        logger.info(f"🔄 Process {process_id}: Starting second row {processed_count}/{len(second_row_indices)} (index {second_idx})")
        
        second_row, second_sign = derangements_with_signs[second_idx]
        
        if r == 2:
            # Just count this one rectangle
            rectangle_sign = first_sign * second_sign
            total_count += 1
            if rectangle_sign > 0:
                positive_count += 1
            else:
                negative_count += 1
            continue
        
        # Calculate valid mask for third row
        third_row_valid = all_valid_mask
        for pos in range(n):
            third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
        
        if r == 3:
            # Just iterate through valid third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                _, third_sign = derangements_with_signs[third_idx]
                
                rectangle_sign = first_sign * second_sign * third_sign
                total_count += 1
                if rectangle_sign > 0:
                    positive_count += 1
                else:
                    negative_count += 1
            continue
        
        # For r > 3, use iterative stack-based approach
        stack = [(2, third_row_valid, first_sign * second_sign)]
        
        while stack:
            level, valid_mask, accumulated_sign = stack.pop()
            
            # Inner loop progress reporting (every 1000 iterations for production)
            inner_progress_counter += 1
            if inner_progress_counter % 1000 == 0:
                current_time = time.time()
                if current_time - last_progress_time >= 30:  # Report every 30 seconds for inner loops
                    logger.info(f"📊 Process {process_id}: Second row {processed_count}/{len(second_row_indices)}, "
                               f"Inner iterations: {inner_progress_counter:,}, "
                               f"Stack depth: {len(stack)}, Level: {level}, "
                               f"Rectangles: {total_count:,}")
                    logger.update_process_progress(
                        process_id, 
                        processed_count,
                        {
                            "rectangles_found": total_count,
                            "positive_count": positive_count,
                            "negative_count": negative_count,
                            "inner_iterations": inner_progress_counter,
                            "current_second_row": f"{processed_count}/{len(second_row_indices)}",
                            "stack_depth": len(stack),
                            "current_level": level
                        }
                    )
                    last_progress_time = current_time
            
            if level == r - 1:
                # Last row - count all valid completions
                last_mask = valid_mask
                while last_mask:
                    last_idx = (last_mask & -last_mask).bit_length() - 1
                    last_mask &= last_mask - 1
                    _, last_sign = derangements_with_signs[last_idx]
                    
                    rectangle_sign = accumulated_sign * last_sign
                    total_count += 1
                    if rectangle_sign > 0:
                        positive_count += 1
                    else:
                        negative_count += 1
            else:
                # Not the last row - iterate and push to stack
                current_mask = valid_mask
                while current_mask:
                    current_idx = (current_mask & -current_mask).bit_length() - 1
                    current_mask &= current_mask - 1
                    current_row, current_sign = derangements_with_signs[current_idx]
                    
                    # Calculate valid mask for next row
                    next_valid = valid_mask
                    for pos in range(n):
                        next_valid &= ~conflict_masks[(pos, current_row[pos])]
                    
                    if next_valid != 0:
                        new_accumulated_sign = accumulated_sign * current_sign
                        stack.append((level + 1, next_valid, new_accumulated_sign))
        
        # Update progress after completing this second row (outer loop progress)
        current_time = time.time()
        if current_time - last_progress_time >= progress_interval:
            logger.update_process_progress(
                process_id, 
                processed_count,
                {
                    "rectangles_found": total_count,
                    "positive_count": positive_count,
                    "negative_count": negative_count
                }
            )
            last_progress_time = current_time
    
    elapsed_time = time.time() - start_time
    
    # Final progress update
    logger.update_process_progress(
        process_id, 
        processed_count,
        {
            "rectangles_found": total_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "status": "completed"
        }
    )
    
    return total_count, positive_count, negative_count, elapsed_time


def count_rectangles_first_column_partition(r: int, n: int, 
                                           first_columns: List[List[int]],
                                           process_id: int = 0,
                                           logger_session: Optional[str] = None) -> Tuple[int, int, int, float]:
    """
    Worker function that processes a subset of first-column choices.
    
    This distributes first-column choices across processes for realistic
    parallel speedups while maintaining the first-column optimization benefits.
    
    Args:
        r: Number of rows
        n: Number of columns
        first_columns: List of first-column choices to process
        process_id: Process identifier
        logger_session: Session name for logging
        
    Returns:
        Tuple of (total_count, positive_count, negative_count, elapsed_time)
    """
    start_time = time.time()
    
    # Set up process-local logger
    from core.logging_config import ProgressLogger
    if logger_session:
        logger = ProgressLogger(f"{logger_session}_process_{process_id}")
    else:
        logger = ProgressLogger(f"parallel_{r}_{n}_process_{process_id}")  # Use parallel_ prefix for consistency
    
    # Register this process for progress tracking
    total_work = len(first_columns)
    logger.register_process(process_id, total_work, f"Processing {total_work:,} first-column choices")
    
    # Initialize constrained enumerator and symmetry calculator
    from core.constrained_enumerator import ConstrainedEnumerator
    constrained_enumerator = ConstrainedEnumerator()
    symmetry_calculator = SymmetryCalculator()
    symmetry_factor = symmetry_calculator.get_symmetry_factor(r)
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    processed_count = 0
    
    # Progress tracking with time-based updates
    last_progress_time = start_time
    progress_interval = 30  # 30 seconds for production - reasonable progress updates
    
    # Process each first column choice in this partition
    for first_column in first_columns:
        processed_count += 1
        
        logger.info(f"🔄 Process {process_id}: Starting first-column choice {processed_count}/{total_work}")
        
        # Count rectangles for this first column choice
        pos, neg = constrained_enumerator.enumerate_with_fixed_first_column(r, n, first_column)
        
        # Apply symmetry factor
        pos_with_symmetry = pos * symmetry_factor
        neg_with_symmetry = neg * symmetry_factor
        
        total_count += pos_with_symmetry + neg_with_symmetry
        positive_count += pos_with_symmetry
        negative_count += neg_with_symmetry
        
        logger.info(f"✅ Process {process_id}: Completed first-column choice {processed_count}/{total_work} - "
                   f"{pos_with_symmetry + neg_with_symmetry:,} rectangles (+{pos_with_symmetry:,} -{neg_with_symmetry:,})")
        
        # Always update progress after each first-column choice (for long-running computations)
        logger.update_process_progress(
            process_id, 
            processed_count,
            {
                "rectangles_found": total_count,
                "positive_count": positive_count,
                "negative_count": negative_count
            }
        )
        last_progress_time = time.time()
    
    elapsed_time = time.time() - start_time
    
    # Final progress update
    logger.update_process_progress(
        process_id, 
        processed_count,
        {
            "rectangles_found": total_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "status": "completed"
        }
    )
    
    return total_count, positive_count, negative_count, elapsed_time


def count_rectangles_parallel_first_column(r: int, n: int, 
                                          num_processes: Optional[int] = None,
                                          logger_session: Optional[str] = None) -> CountResult:
    """
    Count Latin rectangles using parallel first column optimization.
    
    Uses first-column-based parallelization with enhanced constraint propagation
    for improved performance and work distribution.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        logger_session: Custom session name for logging (None = auto-generate)
        
    Returns:
        CountResult with computation results
    """
    start_time = time.time()
    
    # Validate num_processes
    if num_processes is not None and num_processes <= 0:
        raise ValueError(f"num_processes must be positive, got {num_processes}")
    
    # Set up main session logger
    from core.logging_config import ProgressLogger
    if logger_session is None:
        logger_session = f"parallel_{r}_{n}"  # Use parallel_ prefix for consistency with tests
    logger = ProgressLogger(logger_session)
    
    # Auto-detect optimal process count
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)
    
    logger.info(f"🚀 Using parallel first column optimization with {num_processes} processes")
    print(f"🚀 Using parallel first column optimization with {num_processes} processes")
    
    # Generate first column choices
    enumerator = FirstColumnEnumerator()
    first_columns = enumerator.enumerate_first_columns(r, n)
    symmetry_calculator = SymmetryCalculator()
    symmetry_factor = symmetry_calculator.get_symmetry_factor(r)
    
    logger.info(f"   📊 Total first-column choices: {len(first_columns):,}")
    logger.info(f"   🔢 Symmetry factor: {symmetry_factor} (each choice represents {symmetry_factor} rectangles)")
    print(f"   📊 Total first-column choices: {len(first_columns):,}")
    print(f"   🔢 Symmetry factor: {symmetry_factor} (each choice represents {symmetry_factor} rectangles)")
    
    # Create balanced work partitions by distributing first column choices
    # Use round-robin distribution for better load balancing
    if len(first_columns) < num_processes:
        num_processes = len(first_columns)
    
    # Ensure we have at least 1 process
    if num_processes <= 0:
        num_processes = 1
    
    partitions = [[] for _ in range(num_processes)]
    
    # Distribute first columns in round-robin fashion for balanced load
    for i, first_column in enumerate(first_columns):
        process_idx = i % num_processes
        partitions[process_idx].append(first_column)
    
    # Log the distribution
    for i, partition_choices in enumerate(partitions):
        logger.info(f"   Process {i+1}: {len(partition_choices):,} first column choices")
        print(f"   Process {i+1}: {len(partition_choices):,} first column choices")
    
    # Initialize counts
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Execute in parallel
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit all tasks
        futures = []
        for i, partition_choices in enumerate(partitions):
            future = executor.submit(
                count_rectangles_first_column_partition,
                r, n, partition_choices, i, logger_session
            )
            futures.append((i, future))
        
        # Collect results as they complete
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
                
                # Show per-process completion
                rate = part_total / part_time if part_time > 0 else 0
                logger.info(f"✅ Process {process_id+1}/{num_processes}: {part_total:,} rectangles in {part_time:.2f}s ({rate:,.0f} rect/s)")
                print(f"✅ Process {process_id+1}/{num_processes}: {part_total:,} rectangles in {part_time:.2f}s ({rate:,.0f} rect/s)")
                
                # Show overall progress
                progress_pct = (completed / num_processes) * 100
                elapsed_time = time.time() - start_time
                logger.info(f"📊 Progress: {completed}/{num_processes} ({progress_pct:.0f}%) - {total_count:,} total - {elapsed_time:.1f}s elapsed")
                print(f"📊 Progress: {completed}/{num_processes} ({progress_pct:.0f}%) - {total_count:,} total")
                
            except Exception as e:
                print(f"❌ Process failed: {e}")
                import traceback
                traceback.print_exc()
    
    computation_time = time.time() - start_time
    
    # Show final summary
    logger.info(f"\n✅ PARALLEL FIRST COLUMN OPTIMIZATION COMPLETE!")
    logger.info(f"   Total time: {computation_time:.2f}s")
    logger.info(f"   Total rectangles: {total_count:,}")
    logger.info(f"   Result: +{positive_count:,} -{negative_count:,}")
    logger.info(f"   Overall rate: {total_count/computation_time:,.0f} rect/s")
    
    print(f"\n✅ PARALLEL FIRST COLUMN OPTIMIZATION COMPLETE!")
    print(f"   Total time: {computation_time:.2f}s")
    print(f"   Total rectangles: {total_count:,}")
    print(f"   Result: +{positive_count:,} -{negative_count:,}")
    print(f"   Overall rate: {total_count/computation_time:,.0f} rect/s")
    
    if process_results:
        avg_time = sum(r['time'] for r in process_results.values()) / len(process_results)
        speedup = avg_time / computation_time if computation_time > 0 else 0
        efficiency = speedup / num_processes * 100 if num_processes > 0 else 0
        logger.info(f"   Parallel speedup: {speedup:.2f}x")
        logger.info(f"   Parallel efficiency: {efficiency:.1f}%")
        print(f"   Parallel speedup: {speedup:.2f}x")
        print(f"   Parallel efficiency: {efficiency:.1f}%")
    
    # Close the logger session
    logger.close_session()
    
    return CountResult(
        r=r, n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=positive_count - negative_count,
        from_cache=False,
        computation_time=computation_time
    )


def count_rectangles_first_column_partition_with_completion(r: int, n: int, 
                                                        first_columns: List[List[int]],
                                                        process_id: int = 0,
                                                        logger_session: Optional[str] = None) -> Tuple[int, int, int, int, int, int, float]:
    """
    Worker function that processes first-column choices with (n-1, n) completion optimization.
    
    When r = n-1, this computes both (r, n) and (r+1, n) = (n, n) rectangles together
    by completing each (n-1, n) rectangle to its unique (n, n) completion.
    
    Args:
        r: Number of rows (should be n-1 for completion optimization)
        n: Number of columns
        first_columns: List of first-column choices to process
        process_id: Process identifier
        logger_session: Session name for logging
        
    Returns:
        Tuple of (total_r, positive_r, negative_r, total_r_plus_1, positive_r_plus_1, negative_r_plus_1, elapsed_time)
    """
    start_time = time.time()
    
    # Set up process-local logger
    from core.logging_config import ProgressLogger
    if logger_session:
        logger = ProgressLogger(f"{logger_session}_process_{process_id}")
    else:
        logger = ProgressLogger(f"first_column_completion_{r}_{n}_process_{process_id}")
    
    # Register this process for progress tracking
    total_work = len(first_columns)
    logger.register_process(process_id, total_work, f"Processing {total_work:,} first-column choices with completion")
    
    # Initialize constrained enumerator and symmetry calculator
    from core.constrained_enumerator import ConstrainedEnumerator
    constrained_enumerator = ConstrainedEnumerator()
    symmetry_calculator = SymmetryCalculator()
    symmetry_factor = symmetry_calculator.get_symmetry_factor(r)
    
    # Counters for (r, n)
    total_r = 0
    positive_r = 0
    negative_r = 0
    
    # Counters for (r+1, n) = (n, n)
    total_r_plus_1 = 0
    positive_r_plus_1 = 0
    negative_r_plus_1 = 0
    
    processed_count = 0
    
    # Process each first column choice in this partition
    for first_column in first_columns:
        processed_count += 1
        
        # Count rectangles for this first column choice with completion
        pos_r, neg_r, pos_r_plus_1, neg_r_plus_1 = constrained_enumerator.enumerate_with_fixed_first_column_completion(r, n, first_column)
        
        # Apply symmetry factor
        pos_r_with_symmetry = pos_r * symmetry_factor
        neg_r_with_symmetry = neg_r * symmetry_factor
        pos_r_plus_1_with_symmetry = pos_r_plus_1 * symmetry_factor
        neg_r_plus_1_with_symmetry = neg_r_plus_1 * symmetry_factor
        
        total_r += pos_r_with_symmetry + neg_r_with_symmetry
        positive_r += pos_r_with_symmetry
        negative_r += neg_r_with_symmetry
        
        total_r_plus_1 += pos_r_plus_1_with_symmetry + neg_r_plus_1_with_symmetry
        positive_r_plus_1 += pos_r_plus_1_with_symmetry
        negative_r_plus_1 += neg_r_plus_1_with_symmetry
        
        # Update progress periodically
        if processed_count % 10 == 0 or processed_count == total_work:
            logger.update_process_progress(
                process_id, 
                processed_count,
                {
                    "rectangles_r_found": total_r,
                    "rectangles_r_plus_1_found": total_r_plus_1,
                    "positive_r_count": positive_r,
                    "negative_r_count": negative_r,
                    "positive_r_plus_1_count": positive_r_plus_1,
                    "negative_r_plus_1_count": negative_r_plus_1
                }
            )
    
    elapsed_time = time.time() - start_time
    
    # Final progress update
    logger.update_process_progress(
        process_id, 
        processed_count,
        {
            "rectangles_r_found": total_r,
            "rectangles_r_plus_1_found": total_r_plus_1,
            "positive_r_count": positive_r,
            "negative_r_count": negative_r,
            "positive_r_plus_1_count": positive_r_plus_1,
            "negative_r_plus_1_count": negative_r_plus_1,
            "status": "completed"
        }
    )
    
    return total_r, positive_r, negative_r, total_r_plus_1, positive_r_plus_1, negative_r_plus_1, elapsed_time


def count_rectangles_parallel_first_column_with_completion(r: int, n: int, 
                                                          num_processes: Optional[int] = None,
                                                          logger_session: Optional[str] = None) -> Tuple[CountResult, CountResult]:
    """
    Count Latin rectangles using parallel first column optimization with (n-1, n) completion.
    
    When r = n-1, this efficiently computes both (r, n) and (n, n) rectangles together
    by exploiting the mathematical fact that every (n-1, n) rectangle has exactly one
    completion to an (n, n) rectangle.
    
    Args:
        r: Number of rows (must equal n-1)
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        logger_session: Custom session name for logging (None = auto-generate)
        
    Returns:
        Tuple of (CountResult for (r,n), CountResult for (n,n))
    """
    if r != n - 1:
        raise ValueError(f"Completion optimization requires r = n-1, got r={r}, n={n}")
    
    start_time = time.time()
    
    # Set up main session logger
    from core.logging_config import ProgressLogger
    if logger_session is None:
        logger_session = f"first_column_completion_{r}_{n}"
    logger = ProgressLogger(logger_session)
    
    # Auto-detect optimal process count
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)
    
    logger.info(f"🚀 Using parallel first column optimization with completion ({num_processes} processes)")
    logger.info(f"   Computing ({r},{n}) and ({n},{n}) together using completion optimization")
    print(f"🚀 Using parallel first column optimization with completion ({num_processes} processes)")
    print(f"   Computing ({r},{n}) and ({n},{n}) together using completion optimization")
    
    # Generate first column choices
    enumerator = FirstColumnEnumerator()
    first_columns = enumerator.enumerate_first_columns(r, n)
    symmetry_calculator = SymmetryCalculator()
    symmetry_factor = symmetry_calculator.get_symmetry_factor(r)
    
    logger.info(f"   📊 Total first-column choices: {len(first_columns):,}")
    logger.info(f"   🔢 Symmetry factor: {symmetry_factor} (each choice represents {symmetry_factor} rectangles)")
    print(f"   📊 Total first-column choices: {len(first_columns):,}")
    print(f"   🔢 Symmetry factor: {symmetry_factor} (each choice represents {symmetry_factor} rectangles)")
    
    # Create balanced work partitions by distributing first column choices
    if len(first_columns) < num_processes:
        num_processes = len(first_columns)
    
    partitions = [[] for _ in range(num_processes)]
    
    # Distribute first columns in round-robin fashion for balanced load
    for i, first_column in enumerate(first_columns):
        process_idx = i % num_processes
        partitions[process_idx].append(first_column)
    
    # Log the distribution
    for i, partition_choices in enumerate(partitions):
        logger.info(f"   Process {i+1}: {len(partition_choices):,} first column choices")
        print(f"   Process {i+1}: {len(partition_choices):,} first column choices")
    
    # Initialize counts for both (r,n) and (n,n)
    total_r = 0
    positive_r = 0
    negative_r = 0
    total_r_plus_1 = 0
    positive_r_plus_1 = 0
    negative_r_plus_1 = 0
    
    # Execute in parallel
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit all tasks
        futures = []
        for i, partition_choices in enumerate(partitions):
            future = executor.submit(
                count_rectangles_first_column_partition_with_completion,
                r, n, partition_choices, i, logger_session
            )
            futures.append((i, future))
        
        # Collect results as they complete
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
                
                part_total_r, part_pos_r, part_neg_r, part_total_r_plus_1, part_pos_r_plus_1, part_neg_r_plus_1, part_time = future.result()
                
                total_r += part_total_r
                positive_r += part_pos_r
                negative_r += part_neg_r
                total_r_plus_1 += part_total_r_plus_1
                positive_r_plus_1 += part_pos_r_plus_1
                negative_r_plus_1 += part_neg_r_plus_1
                
                completed += 1
                process_results[process_id] = {
                    'total_r': part_total_r,
                    'total_r_plus_1': part_total_r_plus_1,
                    'time': part_time
                }
                
                # Show per-process completion
                rate_r = part_total_r / part_time if part_time > 0 else 0
                rate_r_plus_1 = part_total_r_plus_1 / part_time if part_time > 0 else 0
                logger.info(f"✅ Process {process_id+1}/{num_processes}: ({r},{n})={part_total_r:,} ({n},{n})={part_total_r_plus_1:,} in {part_time:.2f}s")
                print(f"✅ Process {process_id+1}/{num_processes}: ({r},{n})={part_total_r:,} ({n},{n})={part_total_r_plus_1:,} in {part_time:.2f}s")
                
                # Show overall progress
                progress_pct = (completed / num_processes) * 100
                elapsed_time = time.time() - start_time
                logger.info(f"📊 Progress: {completed}/{num_processes} ({progress_pct:.0f}%) - ({r},{n})={total_r:,} ({n},{n})={total_r_plus_1:,} - {elapsed_time:.1f}s elapsed")
                print(f"📊 Progress: {completed}/{num_processes} ({progress_pct:.0f}%) - ({r},{n})={total_r:,} ({n},{n})={total_r_plus_1:,}")
                
            except Exception as e:
                print(f"❌ Process failed: {e}")
                import traceback
                traceback.print_exc()
    
    computation_time = time.time() - start_time
    
    # Show final summary
    logger.info(f"\n✅ PARALLEL FIRST COLUMN COMPLETION OPTIMIZATION COMPLETE!")
    logger.info(f"   Total time: {computation_time:.2f}s")
    logger.info(f"   ({r},{n}): {total_r:,} rectangles (+{positive_r:,} -{negative_r:,})")
    logger.info(f"   ({n},{n}): {total_r_plus_1:,} rectangles (+{positive_r_plus_1:,} -{negative_r_plus_1:,})")
    logger.info(f"   Combined rate: {(total_r + total_r_plus_1)/computation_time:,.0f} rect/s")
    
    print(f"\n✅ PARALLEL FIRST COLUMN COMPLETION OPTIMIZATION COMPLETE!")
    print(f"   Total time: {computation_time:.2f}s")
    print(f"   ({r},{n}): {total_r:,} rectangles (+{positive_r:,} -{negative_r:,})")
    print(f"   ({n},{n}): {total_r_plus_1:,} rectangles (+{positive_r_plus_1:,} -{negative_r_plus_1:,})")
    print(f"   Combined rate: {(total_r + total_r_plus_1)/computation_time:,.0f} rect/s")
    
    if process_results:
        avg_time = sum(r['time'] for r in process_results.values()) / len(process_results)
        speedup = avg_time / computation_time if computation_time > 0 else 0
        efficiency = speedup / num_processes * 100 if num_processes > 0 else 0
        logger.info(f"   Parallel speedup: {speedup:.2f}x")
        logger.info(f"   Parallel efficiency: {efficiency:.1f}%")
        print(f"   Parallel speedup: {speedup:.2f}x")
        print(f"   Parallel efficiency: {efficiency:.1f}%")
    
    # Close the logger session
    logger.close_session()
    
    # Create CountResult objects
    result_r = CountResult(
        r=r, n=n,
        positive_count=positive_r,
        negative_count=negative_r,
        difference=positive_r - negative_r,
        from_cache=False,
        computation_time=computation_time
    )
    
    result_r_plus_1 = CountResult(
        r=n, n=n,
        positive_count=positive_r_plus_1,
        negative_count=negative_r_plus_1,
        difference=positive_r_plus_1 - negative_r_plus_1,
        from_cache=False,
        computation_time=computation_time
    )
    
    return result_r, result_r_plus_1
