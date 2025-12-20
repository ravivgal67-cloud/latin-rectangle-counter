"""
Parallel completion optimization for Latin rectangle counting.

This module combines the completion optimization (computing r,n and r+1,n together)
with parallel processing for maximum performance on large problems.
"""

import multiprocessing as mp
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from core.smart_derangement_cache import get_smart_derangements_with_signs, SmartDerangementCache
from core.counter import CountResult


def count_rectangles_completion_partition(r: int, n: int, 
                                        second_row_indices: List[int],
                                        process_id: int = 0,
                                        logger_session: str = None) -> Tuple[int, int, int, int, int, int, float]:
    """
    Count rectangles for a partition of second rows using completion optimization.
    
    This function processes a subset of second-row derangements and counts
    both (r,n) and (r+1,n) rectangles that start with those second rows.
    
    Args:
        r: Number of rows (must equal n-1)
        n: Number of columns
        second_row_indices: List of indices into the derangements array
        process_id: Process identifier for logging
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
        logger = ProgressLogger(f"parallel_completion_{r}_{n}_process_{process_id}")
    
    # Register this process for progress tracking
    total_work = len(second_row_indices)
    logger.register_process(process_id, total_work, f"Processing {total_work:,} second-row derangements with completion optimization")
    
    # Progress tracking
    last_progress_time = start_time
    progress_interval = 30  # 30 seconds
    processed_count = 0
    
    # Load smart derangements (cached, so fast)
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
    
    # Counters for (r, n)
    total_r = 0
    positive_r = 0
    negative_r = 0
    
    # Counters for (r+1, n)
    total_r_plus_1 = 0
    positive_r_plus_1 = 0
    negative_r_plus_1 = 0
    
    first_sign = 1  # Identity permutation
    
    logger.info(f"🔄 Starting parallel completion optimization for r={r}")
    logger.info(f"   Processing {len(second_row_indices):,} second-row derangements...")
    
    # Process only the assigned second-row indices
    for idx, second_idx in enumerate(second_row_indices):
        processed_count += 1
        
        # Progress reporting
        current_time = time.time()
        if current_time - last_progress_time >= progress_interval:
            progress_pct = (processed_count / total_work) * 100
            rate_r = total_r / (current_time - start_time) if current_time > start_time else 0
            rate_r_plus_1 = total_r_plus_1 / (current_time - start_time) if current_time > start_time else 0
            
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
                    "rate_r_rectangles_per_sec": rate_r,
                    "rate_r_plus_1_rectangles_per_sec": rate_r_plus_1,
                    "status": "running"
                }
            )
            last_progress_time = current_time
        
        second_row, second_sign = derangements_with_signs[second_idx]
        
        # Implement completion optimization for all supported r values
        if r == 2:
            # For r=2, computing (2,3) and (3,3)
            # Count for (2, 3) - this is a complete (2,3) rectangle
            rectangle_sign_r = first_sign * second_sign
            total_r += 1
            if rectangle_sign_r > 0:
                positive_r += 1
            else:
                negative_r += 1
            
            # Now compute valid third rows (for completion to (3,3))
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            # Count all valid third rows
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                _, third_sign = derangements_with_signs[third_idx]
                
                # Count for (3, 3) - this is the completed rectangle
                rectangle_sign_r_plus_1 = rectangle_sign_r * third_sign
                total_r_plus_1 += 1
                if rectangle_sign_r_plus_1 > 0:
                    positive_r_plus_1 += 1
                else:
                    negative_r_plus_1 += 1
        
        elif r == 3:
            # For r=3, computing (3,4) and (4,4)
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                # Count for (3, 4) - this is a complete (3,4) rectangle
                rectangle_sign_r = first_sign * second_sign * third_sign
                total_r += 1
                if rectangle_sign_r > 0:
                    positive_r += 1
                else:
                    negative_r += 1
                
                # Now compute valid fourth rows (for completion to (4,4))
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                # Count all valid fourth rows
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    _, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    # Count for (4, 4) - this is the completed rectangle
                    rectangle_sign_r_plus_1 = rectangle_sign_r * fourth_sign
                    total_r_plus_1 += 1
                    if rectangle_sign_r_plus_1 > 0:
                        positive_r_plus_1 += 1
                    else:
                        negative_r_plus_1 += 1
        
        elif r == 4:
            # For r=4, computing (4,5) and (5,5)
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    # Count for (4, 5) - this is a complete (4,5) rectangle
                    rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign
                    total_r += 1
                    if rectangle_sign_r > 0:
                        positive_r += 1
                    else:
                        negative_r += 1
                    
                    # Now compute valid fifth rows (for completion to (5,5))
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    
                    # Count all valid fifth rows
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        _, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        # Count for (5, 5) - this is the completed rectangle
                        rectangle_sign_r_plus_1 = rectangle_sign_r * fifth_sign
                        total_r_plus_1 += 1
                        if rectangle_sign_r_plus_1 > 0:
                            positive_r_plus_1 += 1
                        else:
                            negative_r_plus_1 += 1
        
        elif r == 5:
            # For r=5, computing (5,6) and (6,6)
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    
                    if fifth_row_valid == 0:
                        continue
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_row, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        # Count for (5, 6) - this is a complete (5,6) rectangle
                        rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign
                        total_r += 1
                        if rectangle_sign_r > 0:
                            positive_r += 1
                        else:
                            negative_r += 1
                        
                        # Now compute valid sixth rows (for completion to (6,6))
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        
                        # Count all valid sixth rows
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            _, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            # Count for (6, 6) - this is the completed rectangle
                            rectangle_sign_r_plus_1 = rectangle_sign_r * sixth_sign
                            total_r_plus_1 += 1
                            if rectangle_sign_r_plus_1 > 0:
                                positive_r_plus_1 += 1
                            else:
                                negative_r_plus_1 += 1
        
        elif r == 6:  # pragma: no cover
            # For r=6, computing (6,7) and (7,7)
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    
                    if fifth_row_valid == 0:
                        continue
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_row, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        
                        if sixth_row_valid == 0:
                            continue
                        
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            sixth_row, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            # Count for (6, 7) - this is a complete (6,7) rectangle
                            rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign
                            total_r += 1
                            if rectangle_sign_r > 0:
                                positive_r += 1
                            else:
                                negative_r += 1
                            
                            # Now compute valid seventh rows (for completion to (7,7))
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            
                            # Count all valid seventh rows
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                _, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                # Count for (7, 7) - this is the completed rectangle
                                rectangle_sign_r_plus_1 = rectangle_sign_r * seventh_sign
                                total_r_plus_1 += 1
                                if rectangle_sign_r_plus_1 > 0:
                                    positive_r_plus_1 += 1
                                else:
                                    negative_r_plus_1 += 1
        
        elif r == 7:  # pragma: no cover
            # For r=7, computing (7,8) and (8,8)
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    if fifth_row_valid == 0:
                        continue
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_row, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        if sixth_row_valid == 0:
                            continue
                        
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            sixth_row, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            if seventh_row_valid == 0:
                                continue
                            
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                seventh_row, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                # Count for (7, 8) - this is a complete (7,8) rectangle
                                rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign * seventh_sign
                                total_r += 1
                                if rectangle_sign_r > 0:
                                    positive_r += 1
                                else:
                                    negative_r += 1
                                
                                # Now compute valid eighth rows (for completion to (8,8))
                                eighth_row_valid = seventh_row_valid
                                for pos in range(n):
                                    eighth_row_valid &= ~conflict_masks[(pos, seventh_row[pos])]
                                
                                # Count all valid eighth rows
                                eighth_mask = eighth_row_valid
                                while eighth_mask:
                                    eighth_idx = (eighth_mask & -eighth_mask).bit_length() - 1
                                    eighth_mask &= eighth_mask - 1
                                    _, eighth_sign = derangements_with_signs[eighth_idx]
                                    
                                    # Count for (8, 8) - this is the completed rectangle
                                    rectangle_sign_r_plus_1 = rectangle_sign_r * eighth_sign
                                    total_r_plus_1 += 1
                                    if rectangle_sign_r_plus_1 > 0:
                                        positive_r_plus_1 += 1
                                    else:
                                        negative_r_plus_1 += 1
        
        elif r == 8:  # pragma: no cover
            # For r=8, computing (8,9) and (9,9)
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    if fifth_row_valid == 0:
                        continue
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_row, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        if sixth_row_valid == 0:
                            continue
                        
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            sixth_row, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            if seventh_row_valid == 0:
                                continue
                            
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                seventh_row, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                eighth_row_valid = seventh_row_valid
                                for pos in range(n):
                                    eighth_row_valid &= ~conflict_masks[(pos, seventh_row[pos])]
                                if eighth_row_valid == 0:
                                    continue
                                
                                eighth_mask = eighth_row_valid
                                while eighth_mask:
                                    eighth_idx = (eighth_mask & -eighth_mask).bit_length() - 1
                                    eighth_mask &= eighth_mask - 1
                                    eighth_row, eighth_sign = derangements_with_signs[eighth_idx]
                                    
                                    # Count for (8, 9) - this is a complete (8,9) rectangle
                                    rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign * seventh_sign * eighth_sign
                                    total_r += 1
                                    if rectangle_sign_r > 0:
                                        positive_r += 1
                                    else:
                                        negative_r += 1
                                    
                                    # Now compute valid ninth rows (for completion to (9,9))
                                    ninth_row_valid = eighth_row_valid
                                    for pos in range(n):
                                        ninth_row_valid &= ~conflict_masks[(pos, eighth_row[pos])]
                                    
                                    # Count all valid ninth rows
                                    ninth_mask = ninth_row_valid
                                    while ninth_mask:
                                        ninth_idx = (ninth_mask & -ninth_mask).bit_length() - 1
                                        ninth_mask &= ninth_mask - 1
                                        _, ninth_sign = derangements_with_signs[ninth_idx]
                                        
                                        # Count for (9, 9) - this is the completed rectangle
                                        rectangle_sign_r_plus_1 = rectangle_sign_r * ninth_sign
                                        total_r_plus_1 += 1
                                        if rectangle_sign_r_plus_1 > 0:
                                            positive_r_plus_1 += 1
                                        else:
                                            negative_r_plus_1 += 1
        
        elif r == 9:  # pragma: no cover
            # For r=9, computing (9,10) and (10,10)
            third_row_valid = all_valid_mask
            for pos in range(n):
                third_row_valid &= ~conflict_masks[(pos, second_row[pos])]
            if third_row_valid == 0:
                continue
            
            third_mask = third_row_valid
            while third_mask:
                third_idx = (third_mask & -third_mask).bit_length() - 1
                third_mask &= third_mask - 1
                third_row, third_sign = derangements_with_signs[third_idx]
                
                fourth_row_valid = third_row_valid
                for pos in range(n):
                    fourth_row_valid &= ~conflict_masks[(pos, third_row[pos])]
                if fourth_row_valid == 0:
                    continue
                
                fourth_mask = fourth_row_valid
                while fourth_mask:
                    fourth_idx = (fourth_mask & -fourth_mask).bit_length() - 1
                    fourth_mask &= fourth_mask - 1
                    fourth_row, fourth_sign = derangements_with_signs[fourth_idx]
                    
                    fifth_row_valid = fourth_row_valid
                    for pos in range(n):
                        fifth_row_valid &= ~conflict_masks[(pos, fourth_row[pos])]
                    if fifth_row_valid == 0:
                        continue
                    
                    fifth_mask = fifth_row_valid
                    while fifth_mask:
                        fifth_idx = (fifth_mask & -fifth_mask).bit_length() - 1
                        fifth_mask &= fifth_mask - 1
                        fifth_row, fifth_sign = derangements_with_signs[fifth_idx]
                        
                        sixth_row_valid = fifth_row_valid
                        for pos in range(n):
                            sixth_row_valid &= ~conflict_masks[(pos, fifth_row[pos])]
                        if sixth_row_valid == 0:
                            continue
                        
                        sixth_mask = sixth_row_valid
                        while sixth_mask:
                            sixth_idx = (sixth_mask & -sixth_mask).bit_length() - 1
                            sixth_mask &= sixth_mask - 1
                            sixth_row, sixth_sign = derangements_with_signs[sixth_idx]
                            
                            seventh_row_valid = sixth_row_valid
                            for pos in range(n):
                                seventh_row_valid &= ~conflict_masks[(pos, sixth_row[pos])]
                            if seventh_row_valid == 0:
                                continue
                            
                            seventh_mask = seventh_row_valid
                            while seventh_mask:
                                seventh_idx = (seventh_mask & -seventh_mask).bit_length() - 1
                                seventh_mask &= seventh_mask - 1
                                seventh_row, seventh_sign = derangements_with_signs[seventh_idx]
                                
                                eighth_row_valid = seventh_row_valid
                                for pos in range(n):
                                    eighth_row_valid &= ~conflict_masks[(pos, seventh_row[pos])]
                                if eighth_row_valid == 0:
                                    continue
                                
                                eighth_mask = eighth_row_valid
                                while eighth_mask:
                                    eighth_idx = (eighth_mask & -eighth_mask).bit_length() - 1
                                    eighth_mask &= eighth_mask - 1
                                    eighth_row, eighth_sign = derangements_with_signs[eighth_idx]
                                    
                                    ninth_row_valid = eighth_row_valid
                                    for pos in range(n):
                                        ninth_row_valid &= ~conflict_masks[(pos, eighth_row[pos])]
                                    if ninth_row_valid == 0:
                                        continue
                                    
                                    ninth_mask = ninth_row_valid
                                    while ninth_mask:
                                        ninth_idx = (ninth_mask & -ninth_mask).bit_length() - 1
                                        ninth_mask &= ninth_mask - 1
                                        ninth_row, ninth_sign = derangements_with_signs[ninth_idx]
                                        
                                        # Count for (9, 10) - this is a complete (9,10) rectangle
                                        rectangle_sign_r = first_sign * second_sign * third_sign * fourth_sign * fifth_sign * sixth_sign * seventh_sign * eighth_sign * ninth_sign
                                        total_r += 1
                                        if rectangle_sign_r > 0:
                                            positive_r += 1
                                        else:
                                            negative_r += 1
                                        
                                        # Now compute valid tenth rows (for completion to (10,10))
                                        tenth_row_valid = ninth_row_valid
                                        for pos in range(n):
                                            tenth_row_valid &= ~conflict_masks[(pos, ninth_row[pos])]
                                        
                                        # Count all valid tenth rows
                                        tenth_mask = tenth_row_valid
                                        while tenth_mask:
                                            tenth_idx = (tenth_mask & -tenth_mask).bit_length() - 1
                                            tenth_mask &= tenth_mask - 1
                                            _, tenth_sign = derangements_with_signs[tenth_idx]
                                            
                                            # Count for (10, 10) - this is the completed rectangle
                                            rectangle_sign_r_plus_1 = rectangle_sign_r * tenth_sign
                                            total_r_plus_1 += 1
                                            if rectangle_sign_r_plus_1 > 0:
                                                positive_r_plus_1 += 1
                                            else:
                                                negative_r_plus_1 += 1
        
        else:  # pragma: no cover
            # For r >= 10, not supported in completion optimization
            raise NotImplementedError(f"Parallel completion optimization only supports r <= 9, got r={r}")
    
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
    
    logger.close_session()
    
    return total_r, positive_r, negative_r, total_r_plus_1, positive_r_plus_1, negative_r_plus_1, elapsed_time


def count_rectangles_with_completion_parallel(r: int, n: int, 
                                             num_processes: Optional[int] = None) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """
    Count (r,n) and (r+1,n) rectangles using parallel completion optimization.
    
    Combines the efficiency of completion optimization with the speed of parallel processing.
    
    Args:
        r: Number of rows (must equal n-1)
        n: Number of columns
        num_processes: Number of processes to use (None = auto-detect)
        
    Returns:
        Tuple of ((total_r, pos_r, neg_r), (total_r_plus_1, pos_r_plus_1, neg_r_plus_1))
    """
    if r != n - 1:
        raise ValueError(f"Parallel completion optimization requires r = n-1, got r={r}, n={n}")
    
    start_time = time.time()
    
    # Set up main session logger
    from core.logging_config import ProgressLogger
    logger = ProgressLogger(f"parallel_completion_{r}_{n}")
    
    # Start progress monitoring for aggregate updates every 2 minutes
    logger.start_progress_monitoring(interval_minutes=2)
    
    # Auto-detect optimal process count
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)
    
    logger.info(f"🚀 Using parallel completion optimization with {num_processes} processes")
    logger.info(f"   Computing ({r},{n}) and ({r+1},{n}) together in parallel")
    print(f"🚀 Using parallel completion optimization with {num_processes} processes")
    print(f"   Computing ({r},{n}) and ({r+1},{n}) together in parallel")
    
    # Get all derangements
    from core.smart_derangement_cache import get_smart_derangement_cache
    cache = get_smart_derangement_cache(n)
    derangements_with_signs = cache.get_all_derangements_with_signs()
    total_derangements = len(derangements_with_signs)
    
    logger.info(f"📊 Total second-row derangements: {total_derangements:,}")
    logger.info(f"🔢 Using {total_derangements}-bit bitsets for ultra-fast operations")
    print(f"📊 Total second-row derangements: {total_derangements:,}")
    print(f"🔢 Using {total_derangements}-bit bitsets for ultra-fast operations")
    
    # Partition work across processes
    derangement_indices = list(range(total_derangements))
    chunk_size = len(derangement_indices) // num_processes
    partitions = []
    
    for i in range(num_processes):
        start_idx = i * chunk_size
        if i == num_processes - 1:
            # Last process gets any remaining work
            end_idx = len(derangement_indices)
        else:
            end_idx = (i + 1) * chunk_size
        
        partition = derangement_indices[start_idx:end_idx]
        partitions.append(partition)
        
        logger.info(f"   Process {i+1}: {len(partition)} second rows (indices {start_idx}-{end_idx-1})")
        print(f"   Process {i+1}: {len(partition)} second rows (indices {start_idx}-{end_idx-1})")
    
    # Execute parallel computation
    total_r = 0
    positive_r = 0
    negative_r = 0
    total_r_plus_1 = 0
    positive_r_plus_1 = 0
    negative_r_plus_1 = 0
    
    completed = 0
    process_results = {}
    
    # For single process, just run directly to avoid ProcessPoolExecutor overhead
    if num_processes == 1:
        logger.info(f"🔧 Running single-process mode (avoiding ProcessPoolExecutor)")
        print(f"🔧 Running single-process mode (avoiding ProcessPoolExecutor)")
        
        partition = partitions[0]
        part_total_r, part_pos_r, part_neg_r, part_total_r_plus_1, part_pos_r_plus_1, part_neg_r_plus_1, part_time = \
            count_rectangles_completion_partition(r, n, partition, 0, f"parallel_completion_{r}_{n}")
        
        total_r = part_total_r
        positive_r = part_pos_r
        negative_r = part_neg_r
        total_r_plus_1 = part_total_r_plus_1
        positive_r_plus_1 = part_pos_r_plus_1
        negative_r_plus_1 = part_neg_r_plus_1
        
        completed = 1
        process_results[0] = {
            'total_r': part_total_r,
            'total_r_plus_1': part_total_r_plus_1,
            'time': part_time
        }
        
        logger.info(f"✅ Process 1/1: ({r},{n})={part_total_r:,} ({r+1},{n})={part_total_r_plus_1:,} in {part_time:.2f}s")
        print(f"✅ Process 1/1: ({r},{n})={part_total_r:,} ({r+1},{n})={part_total_r_plus_1:,} in {part_time:.2f}s")
    else:
        # Use ProcessPoolExecutor for multiple processes
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # Submit all tasks
            futures = []
            for i, partition in enumerate(partitions):
                future = executor.submit(
                    count_rectangles_completion_partition,
                    r, n, partition, i, f"parallel_completion_{r}_{n}"
                )
                futures.append((i, future))
            
            # Collect results as they complete
            for process_id, future in futures:
                try:
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
                    logger.info(f"✅ Process {process_id+1}/{num_processes}: ({r},{n})={part_total_r:,} ({r+1},{n})={part_total_r_plus_1:,} in {part_time:.2f}s")
                    print(f"✅ Process {process_id+1}/{num_processes}: ({r},{n})={part_total_r:,} ({r+1},{n})={part_total_r_plus_1:,} in {part_time:.2f}s")
                    
                    # Show overall progress
                    progress_pct = (completed / num_processes) * 100
                    elapsed_time = time.time() - start_time
                    logger.info(f"📊 Progress: {completed}/{num_processes} ({progress_pct:.0f}%) - ({r},{n})={total_r:,} ({r+1},{n})={total_r_plus_1:,} - {elapsed_time:.1f}s elapsed")
                    print(f"📊 Progress: {completed}/{num_processes} ({progress_pct:.0f}%) - ({r},{n})={total_r:,} ({r+1},{n})={total_r_plus_1:,}")
                    
                except Exception as e:
                    print(f"❌ Process {process_id} failed: {e}")
                    import traceback
                    traceback.print_exc()
    
    computation_time = time.time() - start_time
    
    # Show final summary
    logger.info(f"\n✅ PARALLEL COMPLETION OPTIMIZATION COMPLETE!")
    logger.info(f"   Total time: {computation_time:.2f}s")
    logger.info(f"   ({r},{n}): {total_r:,} rectangles (+{positive_r:,} -{negative_r:,})")
    logger.info(f"   ({r+1},{n}): {total_r_plus_1:,} rectangles (+{positive_r_plus_1:,} -{negative_r_plus_1:,})")
    logger.info(f"   Combined rate: {(total_r + total_r_plus_1)/computation_time:,.0f} rect/s")
    
    print(f"\n✅ PARALLEL COMPLETION OPTIMIZATION COMPLETE!")
    print(f"   Total time: {computation_time:.2f}s")
    print(f"   ({r},{n}): {total_r:,} rectangles (+{positive_r:,} -{negative_r:,})")
    print(f"   ({r+1},{n}): {total_r_plus_1:,} rectangles (+{positive_r_plus_1:,} -{negative_r_plus_1:,})")
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
    
    return ((total_r, positive_r, negative_r), (total_r_plus_1, positive_r_plus_1, negative_r_plus_1))