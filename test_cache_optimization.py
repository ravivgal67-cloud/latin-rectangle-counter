#!/usr/bin/env python3
"""
Test script to measure cache optimization impact for n=7.
"""

import time
import json
from pathlib import Path
from core.smart_derangement_cache import SmartDerangementCache

def test_cache_optimization():
    """Test the cache optimization for n=7."""
    n = 7
    cache_file = Path(f"cache/smart_derangements/smart_derangements_n{n}.json")
    
    print(f"🧪 Testing cache optimization for n={n}")
    print("=" * 60)
    
    # Backup original cache if it exists
    backup_file = cache_file.with_suffix('.json.backup')
    if cache_file.exists():
        print(f"📋 Backing up original cache to {backup_file}")
        cache_file.rename(backup_file)
    
    try:
        # Test 1: Build new cache with multi-prefix index
        print(f"\n1️⃣ Building new cache with multi-prefix index...")
        start_time = time.time()
        cache = SmartDerangementCache(n)
        build_time = time.time() - start_time
        
        # Check new cache size
        new_size_kb = cache_file.stat().st_size / 1024
        print(f"   New cache size: {new_size_kb:.1f} KB")
        print(f"   Build time: {build_time:.3f}s")
        
        # Test 2: Load the new cache (should be faster)
        print(f"\n2️⃣ Testing load time with pre-computed indices...")
        start_time = time.time()
        cache2 = SmartDerangementCache(n)
        load_time = time.time() - start_time
        print(f"   Load time: {load_time:.3f}s")
        
        # Test 3: Compare with backup (if available)
        if backup_file.exists():
            print(f"\n3️⃣ Comparing with original cache...")
            
            # Load original cache data
            with open(backup_file, 'r') as f:
                original_data = json.load(f)
            
            original_size_kb = backup_file.stat().st_size / 1024
            
            # Load new cache data
            with open(cache_file, 'r') as f:
                new_data = json.load(f)
            
            print(f"   Original size: {original_size_kb:.1f} KB")
            print(f"   New size: {new_size_kb:.1f} KB")
            print(f"   Size increase: {new_size_kb - original_size_kb:.1f} KB ({((new_size_kb / original_size_kb - 1) * 100):.1f}%)")
            
            # Check what's new
            original_keys = set(original_data.keys())
            new_keys = set(new_data.keys())
            added_keys = new_keys - original_keys
            
            if added_keys:
                print(f"   Added indices: {list(added_keys)}")
                for key in added_keys:
                    if key in new_data:
                        print(f"     {key}: {len(new_data[key])} entries")
        
        print(f"\n✅ Cache optimization test completed!")
        print(f"   Final cache size: {new_size_kb:.1f} KB")
        print(f"   Load time: {load_time:.3f}s")
        
    finally:
        # Restore backup if something went wrong
        if backup_file.exists():
            choice = input(f"\n🔄 Restore original cache? (y/N): ").lower()
            if choice == 'y':
                if cache_file.exists():
                    cache_file.unlink()
                backup_file.rename(cache_file)
                print("✅ Original cache restored")
            else:
                backup_file.unlink()
                print("✅ Backup removed, keeping optimized cache")

if __name__ == "__main__":
    test_cache_optimization()