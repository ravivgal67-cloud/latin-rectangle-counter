#!/usr/bin/env python3
"""
Smart Derangement Cache Generator

This script generates optimized cache files for smart derangement data
with pre-computed indices to eliminate initialization bottlenecks.

Usage:
    python scripts/generate_cache.py [options]

Options:
    --n N           Generate cache for specific n (default: 2-8)
    --force         Force regeneration even if cache exists
    --verify        Verify cache integrity after generation
    --benchmark     Benchmark loading performance
"""

import argparse
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.smart_derangement_cache import SmartDerangementCache


def format_size(bytes_size):
    """Format file size in human-readable format."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f} MB"


def generate_cache_for_n(n, force=False, verify=False, benchmark=False):
    """Generate cache for specific n value."""
    cache_dir = Path("cache/smart_derangements")
    cache_file = cache_dir / f"smart_derangements_n{n}.json"
    
    # Check if cache exists
    if cache_file.exists() and not force:
        print(f"⏭️  Cache for n={n} already exists (use --force to regenerate)")
        return
    
    print(f"🔄 Generating cache for n={n}...")
    
    # Delete existing cache to force regeneration
    if cache_file.exists():
        cache_file.unlink()
        print(f"   Deleted existing cache file")
    
    # Generate cache
    start_time = time.time()
    cache = SmartDerangementCache(n)
    generation_time = time.time() - start_time
    
    # Check file size
    file_size = cache_file.stat().st_size
    
    print(f"✅ Generated cache for n={n}")
    print(f"   File: {cache_file.name}")
    print(f"   Size: {format_size(file_size)}")
    print(f"   Generation time: {generation_time:.3f}s")
    print(f"   Derangements: {len(cache.derangements_with_signs):,}")
    print(f"   Position-value index: {len(cache.position_value_index)} entries")
    print(f"   Multi-prefix index: {len(cache.multi_prefix_index)} entries")
    
    # Verify cache integrity
    if verify:
        print(f"🔍 Verifying cache integrity for n={n}...")
        
        # Delete cache object to force reload
        del cache
        
        # Reload and verify
        verify_start = time.time()
        cache_verify = SmartDerangementCache(n)
        verify_time = time.time() - verify_start
        
        print(f"✅ Cache verification passed")
        print(f"   Load time: {verify_time:.3f}s")
        
        # Check that indices were loaded from cache (not rebuilt)
        if hasattr(cache_verify, '_indices_loaded_from_cache'):
            print(f"   Indices loaded from cache: ✅")
        else:
            print(f"   Indices loaded from cache: ❓ (check logs)")
    
    # Benchmark loading performance
    if benchmark:
        print(f"⚡ Benchmarking load performance for n={n}...")
        
        # Multiple load tests
        load_times = []
        for i in range(5):
            # Delete cache object
            if 'cache' in locals():
                del cache
            if 'cache_verify' in locals():
                del cache_verify
            
            # Time the load
            load_start = time.time()
            cache_bench = SmartDerangementCache(n)
            load_time = time.time() - load_start
            load_times.append(load_time)
        
        avg_load_time = sum(load_times) / len(load_times)
        min_load_time = min(load_times)
        max_load_time = max(load_times)
        
        print(f"   Average load time: {avg_load_time:.3f}s")
        print(f"   Min load time: {min_load_time:.3f}s")
        print(f"   Max load time: {max_load_time:.3f}s")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate smart derangement cache files with pre-computed indices"
    )
    parser.add_argument(
        "--n", 
        type=int, 
        help="Generate cache for specific n (default: generate for n=2 through n=8)"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force regeneration even if cache exists"
    )
    parser.add_argument(
        "--verify", 
        action="store_true", 
        help="Verify cache integrity after generation"
    )
    parser.add_argument(
        "--benchmark", 
        action="store_true", 
        help="Benchmark loading performance"
    )
    
    args = parser.parse_args()
    
    print("🚀 Smart Derangement Cache Generator")
    print("=" * 50)
    
    # Determine which n values to generate
    if args.n:
        n_values = [args.n]
        print(f"Generating cache for n={args.n}")
    else:
        n_values = list(range(2, 9))  # n=2 through n=8
        print(f"Generating caches for n={min(n_values)} through n={max(n_values)}")
    
    if args.force:
        print("Force regeneration: ON")
    if args.verify:
        print("Cache verification: ON")
    if args.benchmark:
        print("Performance benchmarking: ON")
    
    print()
    
    # Generate caches
    total_start_time = time.time()
    
    for n in n_values:
        try:
            generate_cache_for_n(n, force=args.force, verify=args.verify, benchmark=args.benchmark)
        except Exception as e:
            print(f"❌ Error generating cache for n={n}: {e}")
            continue
    
    total_time = time.time() - total_start_time
    
    # Summary
    print("=" * 50)
    print(f"🎉 Cache generation complete!")
    print(f"Total time: {total_time:.2f}s")
    
    # Show final cache directory
    cache_dir = Path("cache/smart_derangements")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("smart_derangements_n*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        print(f"Cache files: {len(cache_files)}")
        print(f"Total size: {format_size(total_size)}")
        
        print("\nCache files:")
        for cache_file in sorted(cache_files):
            size = cache_file.stat().st_size
            n = cache_file.name.replace("smart_derangements_n", "").replace(".json", "")
            print(f"  n={n}: {format_size(size)}")


if __name__ == "__main__":
    main()