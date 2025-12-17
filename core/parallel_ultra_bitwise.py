"""
Parallel Latin rectangle counting using ultra-safe bitwise operations.

This module integrates the ultra-safe bitwise approach with parallel processing
by partitioning work across second-row derangements.
"""

import multiprocessing as mp
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from core.smart_derangement_cache import get_smart_derangements_with_signs, SmartDerangementCache
from core.counter import CountResult


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
    progress_interval = 600  # 10 minutes
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
        
        # Periodic progress updates (every 10 minutes)
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


def count_rectangles_parallel_ultra_bitwise(r: int, n: int, 
                                            num_processes: Optional[int] = None) -> CountResult:
    """
    Count Latin rectangles using parallel ultra-safe bitwise processing.
    
    Combines the speed of ultra-safe bitwise operations with parallel processing
    for maximum performance on large problems.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        
    Returns:
        CountResult with computation results
    """
    start_time = time.time()
    
    # Set up main session logger
    from core.logging_config import get_logger
    logger = get_logger(f"parallel_{r}_{n}")
    
    # Auto-detect optimal process count
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)
    
    logger.info(f"🚀 Using parallel ultra-safe bitwise with {num_processes} processes")
    print(f"🚀 Using parallel ultra-safe bitwise with {num_processes} processes")
    
    # Get all derangements (use cache to avoid double-loading)
    from core.smart_derangement_cache import get_smart_derangement_cache
    cache = get_smart_derangement_cache(n)
    derangements_with_signs = cache.get_all_derangements_with_signs()
    total_derangements = len(derangements_with_signs)
    
    logger.info(f"   📊 Total second-row derangements: {total_derangements:,}")
    logger.info(f"   🔢 Using {total_derangements}-bit bitsets for ultra-fast operations")
    print(f"   📊 Total second-row derangements: {total_derangements:,}")
    print(f"   🔢 Using {total_derangements}-bit bitsets for ultra-fast operations")
    
    # Create work partitions by distributing second row indices
    derangements_per_process = total_derangements // num_processes
    if derangements_per_process == 0:
        derangements_per_process = 1
        num_processes = total_derangements
    
    partitions = []
    for i in range(num_processes):
        start_idx = i * derangements_per_process
        if i == num_processes - 1:
            end_idx = total_derangements
        else:
            end_idx = (i + 1) * derangements_per_process
        
        partition_indices = list(range(start_idx, end_idx))
        partitions.append(partition_indices)
        logger.info(f"   Process {i+1}: {len(partition_indices):,} second rows (indices {start_idx}-{end_idx-1})")
        print(f"   Process {i+1}: {len(partition_indices):,} second rows (indices {start_idx}-{end_idx-1})")
    
    # Initialize counts
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Execute in parallel
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit all tasks
        futures = []
        for i, partition_indices in enumerate(partitions):
            future = executor.submit(
                count_rectangles_ultra_bitwise_partition,
                r, n, partition_indices, i, f"parallel_{r}_{n}"
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
    logger.info(f"\n✅ PARALLEL ULTRA-SAFE BITWISE COMPLETE!")
    logger.info(f"   Total time: {computation_time:.2f}s")
    logger.info(f"   Total rectangles: {total_count:,}")
    logger.info(f"   Result: +{positive_count:,} -{negative_count:,}")
    logger.info(f"   Overall rate: {total_count/computation_time:,.0f} rect/s")
    
    print(f"\n✅ PARALLEL ULTRA-SAFE BITWISE COMPLETE!")
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
    
    return CountResult(
        r=r, n=n,
        positive_count=positive_count,
        negative_count=negative_count,
        difference=positive_count - negative_count,
        from_cache=False,
        computation_time=computation_time
    )
