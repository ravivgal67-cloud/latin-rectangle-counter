#!/usr/bin/env python3
"""
Test parallel initialization performance with optimized cache.
"""

import time
import multiprocessing as mp
from core.smart_derangement_cache import SmartDerangementCache

def worker_load_cache(n):
    """Worker function to load cache and measure time."""
    start_time = time.time()
    cache = SmartDerangementCache(n)
    load_time = time.time() - start_time
    return {
        'process_id': mp.current_process().pid,
        'load_time': load_time,
        'derangements_count': len(cache.derangements_with_signs),
        'multi_prefix_entries': len(cache.multi_prefix_index)
    }

def test_parallel_initialization():
    """Test parallel cache loading performance."""
    n = 7
    num_processes = 4
    
    print(f"🚀 Testing parallel initialization for n={n} with {num_processes} processes")
    print("=" * 70)
    
    # Test parallel loading
    start_time = time.time()
    
    with mp.Pool(num_processes) as pool:
        results = pool.map(worker_load_cache, [n] * num_processes)
    
    total_time = time.time() - start_time
    
    print(f"\n📊 Results:")
    print(f"   Total parallel initialization time: {total_time:.3f}s")
    print(f"   Number of processes: {num_processes}")
    
    for i, result in enumerate(results):
        print(f"   Process {i+1} (PID {result['process_id']}): {result['load_time']:.3f}s")
        print(f"     Derangements: {result['derangements_count']:,}")
        print(f"     Multi-prefix entries: {result['multi_prefix_entries']}")
    
    avg_load_time = sum(r['load_time'] for r in results) / len(results)
    max_load_time = max(r['load_time'] for r in results)
    
    print(f"\n📈 Summary:")
    print(f"   Average load time per process: {avg_load_time:.3f}s")
    print(f"   Maximum load time (bottleneck): {max_load_time:.3f}s")
    print(f"   Total overhead: {total_time:.3f}s")
    
    # Estimate for n=8
    print(f"\n🔮 Estimated impact for n=8:")
    print(f"   Current n=7 load time: {avg_load_time:.3f}s")
    print(f"   Estimated n=8 load time: {avg_load_time * 8:.3f}s (8x more derangements)")
    print(f"   Without optimization: >10s per process (rebuilding indices)")

if __name__ == "__main__":
    test_parallel_initialization()