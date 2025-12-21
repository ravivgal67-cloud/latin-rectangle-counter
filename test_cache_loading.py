#!/usr/bin/env python3
"""
Quick test to check cache loading performance for n=8.
"""

import time
from core.smart_derangement_cache import get_smart_derangement_cache

def test_cache_loading():
    print("Testing cache loading for n=8...")
    
    start_time = time.time()
    cache = get_smart_derangement_cache(8)
    load_time = time.time() - start_time
    
    print(f"Cache loaded in {load_time:.3f}s")
    
    # Test getting derangements
    start_time = time.time()
    derangements = cache.get_all_derangements_with_signs()
    get_time = time.time() - start_time
    
    print(f"Got {len(derangements):,} derangements in {get_time:.3f}s")
    
    # Test position-value index access
    start_time = time.time()
    position_value_index = cache.position_value_index
    index_time = time.time() - start_time
    
    print(f"Accessed position-value index ({len(position_value_index)} entries) in {index_time:.3f}s")
    
    # Test conflict mask building (this is what happens in each worker)
    start_time = time.time()
    conflict_masks = {}
    for pos in range(8):
        for val in range(1, 9):
            conflict_key = (pos, val)
            if conflict_key in position_value_index:
                mask = 0
                for conflict_idx in position_value_index[conflict_key]:
                    mask |= (1 << conflict_idx)
                conflict_masks[conflict_key] = mask
            else:
                conflict_masks[conflict_key] = 0
    
    mask_time = time.time() - start_time
    print(f"Built {len(conflict_masks)} conflict masks in {mask_time:.3f}s")
    
    total_time = load_time + get_time + index_time + mask_time
    print(f"Total initialization time: {total_time:.3f}s")

if __name__ == "__main__":
    test_cache_loading()