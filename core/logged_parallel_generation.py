"""
Logged parallel Latin rectangle generation with comprehensive progress tracking.

This module wraps the parallel generation functionality with detailed logging
and progress monitoring for long-running computations.
"""

import time
import multiprocessing as mp
from typing import Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

from core.parallel_generation import (
    process_second_row_partition, 
    get_valid_second_rows,
    should_use_parallel
)
from core.counter import CountResult
from core.logging_config import get_logger


def logged_process_second_row_partition(r: int, n: int, second_rows_data, 
                                      process_id: int, logger_session: str) -> Tuple[int, int, int, float]:
    """
    Process a partition with detailed logging and progress updates.
    
    This function runs in a separate process and provides periodic progress updates.
    """
    # Set up process-local logger
    from core.logging_config import ProgressLogger
    logger = ProgressLogger(f"{logger_session}_process_{process_id}")
    
    start_time = time.time()
    total_work = len(second_rows_data)
    
    logger.register_process(process_id, total_work, f"Processing {total_work} second-row permutations")
    
    total_count = 0
    positive_count = 0
    negative_count = 0
    
    # Progress tracking
    last_progress_time = start_time
    progress_interval = 30  # 30 seconds - better for web monitoring
    
    try:
        # Handle both legacy format and new format with pre-computed signs
        if second_rows_data and isinstance(second_rows_data[0], tuple):
            # New format: List[Tuple[List[int], int]] with pre-computed signs
            for i, (second_row, precomputed_sign) in enumerate(second_rows_data):
                from core.parallel_generation import count_rectangles_with_fixed_second_row
                part_total, part_positive, part_negative = count_rectangles_with_fixed_second_row(
                    r, n, second_row, precomputed_sign
                )
                total_count += part_total
                positive_count += part_positive
                negative_count += part_negative
                
                # Periodic progress updates
                current_time = time.time()
                if current_time - last_progress_time >= progress_interval:
                    logger.update_process_progress(
                        process_id, i + 1,
                        {
                            "rectangles_found": total_count,
                            "positive_count": positive_count,
                            "negative_count": negative_count,
                            "rate_rectangles_per_sec": total_count / (current_time - start_time)
                        }
                    )
                    last_progress_time = current_time
        else:
            # Legacy format: List[List[int]] without signs
            for i, second_row in enumerate(second_rows_data):
                from core.parallel_generation import count_rectangles_with_fixed_second_row
                part_total, part_positive, part_negative = count_rectangles_with_fixed_second_row(r, n, second_row)
                total_count += part_total
                positive_count += part_positive
                negative_count += part_negative
                
                # Periodic progress updates
                current_time = time.time()
                if current_time - last_progress_time >= progress_interval:
                    logger.update_process_progress(
                        process_id, i + 1,
                        {
                            "rectangles_found": total_count,
                            "positive_count": positive_count,
                            "negative_count": negative_count,
                            "rate_rectangles_per_sec": total_count / (current_time - start_time)
                        }
                    )
                    last_progress_time = current_time
        
        elapsed_time = time.time() - start_time
        
        # Final progress update
        logger.complete_process(process_id, {
            "total_rectangles": total_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "elapsed_time": elapsed_time,
            "rate_rectangles_per_sec": total_count / elapsed_time if elapsed_time > 0 else 0
        })
        
        logger.close_session()
        return total_count, positive_count, negative_count, elapsed_time
        
    except Exception as e:
        logger.error(f"Process {process_id} failed", error=str(e), process_id=process_id)
        logger.close_session()
        raise


def count_rectangles_parallel_logged(r: int, n: int, num_processes: Optional[int] = None,
                                   session_name: str = None) -> CountResult:
    """
    Count Latin rectangles with comprehensive logging and progress tracking.
    
    This function provides the same functionality as count_rectangles_parallel
    but with detailed logging, progress monitoring, and crash recovery information.
    
    Args:
        r: Number of rows
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        session_name: Custom session name for logging
        
    Returns:
        CountResult with computation results
    """
    logger = get_logger(session_name)
    
    start_time = time.time()
    
    logger.start_computation("parallel_latin_rectangles", 
                           r=r, n=n, num_processes=num_processes)
    
    # Smart heuristics for parallel processing
    if r == 2:
        logger.info("Using single-threaded processing (r=2 problems are always small)")
        use_parallel = False
    elif n < 7:
        logger.info(f"Using single-threaded processing (n={n} < 7)")
        use_parallel = False
    else:
        use_parallel = True
    
    if not use_parallel:
        logger.info("Running sequential computation")
        # Fall back to sequential processing
        from core.latin_rectangle import generate_normalized_rectangles_bitset_optimized
        
        total_count = 0
        positive_count = 0
        negative_count = 0
        
        logger.register_process(0, 1, "Sequential rectangle generation")
        
        for rect in generate_normalized_rectangles_bitset_optimized(r, n):
            total_count += 1
            sign = rect.compute_sign()
            if sign > 0:
                positive_count += 1
            else:
                negative_count += 1
        
        computation_time = time.time() - start_time
        
        logger.complete_process(0, {
            "total_rectangles": total_count,
            "positive_count": positive_count,
            "negative_count": negative_count
        })
        
        logger.info(f"Sequential computation completed in {computation_time:.2f}s")
        
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
    
    logger.info(f"🚀 Using row-based parallel processing with {num_processes} processes")
    
    # Start progress monitoring
    logger.start_progress_monitoring(interval_minutes=1)
    
    try:
        # Get all valid second rows with smart cache optimization
        try:
            from core.smart_derangement_cache import get_smart_derangements_with_signs
            second_rows_with_signs = get_smart_derangements_with_signs(n)
            logger.info(f"🚀 Using smart derangement cache: {len(second_rows_with_signs):,} derangements with pre-computed signs")
            use_smart_cache = True
        except (ImportError, ModuleNotFoundError):
            second_rows = get_valid_second_rows(n)
            second_rows_with_signs = [(row, None) for row in second_rows]
            logger.info(f"Found {len(second_rows):,} valid second-row permutations (dynamic generation)")
            use_smart_cache = False
        
        # Create work partitions
        total_rows = len(second_rows_with_signs)
        rows_per_process = total_rows // num_processes
        if rows_per_process == 0:
            rows_per_process = 1
            num_processes = total_rows
        
        partitions = []
        for i in range(num_processes):
            start_idx = i * rows_per_process
            if i == num_processes - 1:
                end_idx = total_rows
            else:
                end_idx = (i + 1) * rows_per_process
            
            if use_smart_cache:
                partition_data = second_rows_with_signs[start_idx:end_idx]
            else:
                partition_data = [row for row, _ in second_rows_with_signs[start_idx:end_idx]]
            
            partitions.append(partition_data)
            logger.info(f"Process {i+1}: {len(partition_data):,} second-row permutations (indices {start_idx}-{end_idx-1})")
        
        # Initialize counts
        total_count = 0
        positive_count = 0
        negative_count = 0
        
        # Execute in parallel with logging
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # Submit all tasks
            futures = []
            for i, partition_rows in enumerate(partitions):
                future = executor.submit(
                    logged_process_second_row_partition,
                    r, n, partition_rows, i, logger.session_name
                )
                futures.append((i, future))
            
            logger.info(f"Submitted {len(futures)} parallel tasks")
            
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
                    
                    # Log per-process completion
                    logger.info(f"✅ Process {process_id+1}/{num_processes} complete: {part_total:,} rectangles (+{part_positive:,} -{part_negative:,}) in {part_time:.2f}s",
                               process_id=process_id,
                               rectangles=part_total,
                               positive_count=part_positive,
                               negative_count=part_negative,
                               elapsed_time=part_time)
                    
                    # Show overall progress
                    progress_pct = (completed / num_processes) * 100
                    logger.info(f"📊 Overall progress: {completed}/{num_processes} processes ({progress_pct:.0f}%) - {total_count:,} total rectangles",
                               overall_progress_pct=progress_pct,
                               completed_processes=completed,
                               total_processes=num_processes,
                               total_rectangles=total_count)
                    
                except Exception as e:
                    logger.error(f"Process failed", error=str(e))
                    # Continue with other processes
        
        computation_time = time.time() - start_time
        
        # Final summary
        logger.info(f"📋 PARALLEL COMPUTATION SUMMARY:")
        logger.info(f"   Total time: {computation_time:.2f}s")
        logger.info(f"   Total rectangles: {total_count:,}")
        logger.info(f"   Result: +{positive_count:,} -{negative_count:,} (difference: {positive_count - negative_count:+,})")
        
        if process_results:
            logger.info(f"📊 Per-process breakdown:")
            for proc_id in sorted(process_results.keys()):
                result = process_results[proc_id]
                rate = result['total'] / result['time'] if result['time'] > 0 else 0
                logger.info(f"   Process {proc_id+1}: {result['total']:,} rectangles (+{result['positive']:,} -{result['negative']:,}) in {result['time']:.2f}s ({rate:,.0f} rect/s)")
        
        logger.info(f"✅ Row-based parallel computation complete!")
        
        return CountResult(
            r=r, n=n,
            positive_count=positive_count,
            negative_count=negative_count,
            difference=positive_count - negative_count,
            from_cache=False,
            computation_time=computation_time
        )
        
    except Exception as e:
        logger.error(f"Parallel computation failed", error=str(e))
        raise
    finally:
        logger.stop_progress_monitoring()


if __name__ == "__main__":
    # Test the logged parallel implementation
    print("Testing logged parallel processing...")
    
    # Test small problem
    result = count_rectangles_parallel_logged(3, 7, num_processes=2, session_name="test_logged_parallel")
    print(f"Result: {result.positive_count + result.negative_count:,} rectangles in {result.computation_time:.2f}s")
    
    # Close logger
    from core.logging_config import close_logger
    close_logger()