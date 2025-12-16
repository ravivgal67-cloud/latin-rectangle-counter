#!/usr/bin/env python3
"""
Test checkpoint validation for configuration mismatches.

This demonstrates why we need to validate that checkpoint configuration
matches the current run configuration.
"""

from core.parallel_generation import count_rectangles_parallel
from cache.cache_manager import CacheManager
import json


def test_process_count_mismatch():
    """Test what happens when checkpoint process count differs from current run."""
    print("🧪 Testing process count mismatch...")
    
    cache = CacheManager()
    r, n = 3, 7
    
    # Clean up
    cache.delete_checkpoint_counters(r, n)
    
    print(f"\n1️⃣ Create checkpoint with 2 processes...")
    
    # Simulate a checkpoint saved with 2 processes
    # Each process would handle ~927 derangements (1854 / 2)
    checkpoint_data = {
        'partition_method': 'row_based',
        'total_partitions': 2,
        'num_processes': 2,
        'completed_partitions': [0],  # Process 0 completed
        'partition_results': {
            0: {'positive': 268000, 'negative': 268000, 'total': 536000}
        },
        'derangement_count': 1854,
        'rows_per_process': 927
    }
    
    # Save a manual checkpoint
    cache.save_checkpoint_counters(r, n, [0]*r, 268000, 268000, 536000, 60.0)
    print(f"   Saved checkpoint: 2 processes, 1 completed")
    
    print(f"\n2️⃣ Try to resume with 4 processes...")
    
    # Now try to resume with 4 processes
    # Each process would handle ~463 derangements (1854 / 4)
    # This creates a partition mismatch!
    
    result = count_rectangles_parallel(r, n, num_processes=4, use_checkpoints=True)
    print(f"   Result: +{result.positive_count:,} -{result.negative_count:,}")
    
    # This will likely give wrong results because:
    # - Checkpoint thinks process 0 handled derangements 0-926
    # - But with 4 processes, process 0 only handles 0-462
    # - We get overlap and missing coverage!
    
    return result


def test_partition_method_mismatch():
    """Test what happens when partition method changes."""
    print(f"\n🧪 Testing partition method mismatch...")
    
    cache = CacheManager()
    r, n = 3, 8
    
    # Clean up
    cache.delete_checkpoint_counters(r, n)
    
    print(f"   Simulating checkpoint with 'counter_based' method...")
    print(f"   But current implementation uses 'row_based' method...")
    print(f"   This would be completely incompatible!")
    
    # In a real implementation, we'd have different partition methods
    # that are completely incompatible
    
    return True


def show_proper_validation_design():
    """Show what proper checkpoint validation should look like."""
    print(f"\n" + "="*70)
    print("💡 PROPER CHECKPOINT VALIDATION DESIGN")
    print("=" * 70)
    
    print("""
🎯 Checkpoint Configuration Validation:

1. **Enhanced Checkpoint Metadata**:
   ```python
   checkpoint = {
       # Core computation info
       'r': 3, 'n': 7,
       'partition_method': 'row_based',
       
       # Partition configuration
       'num_processes': 4,
       'total_partitions': 4,
       'derangement_count': 1854,
       'rows_per_process': 463,
       
       # Partition boundaries (critical!)
       'partition_boundaries': [
           {'start_idx': 0, 'end_idx': 463},
           {'start_idx': 463, 'end_idx': 926},
           {'start_idx': 926, 'end_idx': 1389},
           {'start_idx': 1389, 'end_idx': 1854}
       ],
       
       # Completed work
       'completed_partitions': [0, 1],
       'partition_results': {...},
       
       # Validation info
       'checkpoint_version': '1.0',
       'created_by': 'parallel_generation.py',
       'timestamp': '2024-12-16T10:30:00Z'
   }
   ```

2. **Validation Logic**:
   ```python
   def validate_checkpoint_compatibility(checkpoint, current_config):
       # Check basic dimensions
       if checkpoint['r'] != current_config['r'] or checkpoint['n'] != current_config['n']:
           return False, "Dimension mismatch"
       
       # Check partition method
       if checkpoint['partition_method'] != current_config['partition_method']:
           return False, "Partition method mismatch"
       
       # Check process count
       if checkpoint['num_processes'] != current_config['num_processes']:
           return False, f"Process count mismatch: saved={checkpoint['num_processes']}, current={current_config['num_processes']}"
       
       # Check derangement count (should be same for same n)
       if checkpoint['derangement_count'] != current_config['derangement_count']:
           return False, "Derangement count mismatch - data corruption?"
       
       # Check partition boundaries match
       if checkpoint['partition_boundaries'] != current_config['partition_boundaries']:
           return False, "Partition boundary mismatch"
       
       return True, "Compatible"
   ```

3. **Mismatch Handling**:
   ```python
   def handle_checkpoint_mismatch(checkpoint, current_config, mismatch_reason):
       print(f"⚠️  Checkpoint incompatible: {mismatch_reason}")
       print(f"   Saved config: {checkpoint['num_processes']} processes")
       print(f"   Current config: {current_config['num_processes']} processes")
       
       # Options:
       # 1. Delete incompatible checkpoint and start fresh
       # 2. Try to convert checkpoint to new configuration (complex)
       # 3. Ask user what to do
       
       print(f"   Deleting incompatible checkpoint and starting fresh...")
       return "start_fresh"
   ```

4. **Configuration Scenarios**:

   ✅ **Compatible Resume**:
   - Same r, n, partition_method, num_processes
   - Same partition boundaries
   - Can safely skip completed partitions
   
   ❌ **Incompatible - Different Process Count**:
   - Checkpoint: 2 processes, partitions [0-926, 927-1853]  
   - Current: 4 processes, partitions [0-463, 464-926, 927-1389, 1390-1853]
   - Partition boundaries completely different!
   
   ❌ **Incompatible - Different Method**:
   - Checkpoint: row_based partitioning
   - Current: counter_based partitioning  
   - Completely different partition schemes!
   
   ❌ **Incompatible - Different Dimensions**:
   - Checkpoint: (3,7)
   - Current: (4,7) or (3,8)
   - Wrong problem entirely!

5. **User Experience**:
   ```
   🚀 Using row-based parallel processing with 4 processes
   📍 Found checkpoint for (3,7)...
   ⚠️  Checkpoint incompatible: Process count mismatch (saved=2, current=4)
   🧹 Deleting incompatible checkpoint and starting fresh...
   Found 1,854 valid second-row permutations
   Process 1: 463 second-row permutations...
   ```
""")


def demonstrate_boundary_mismatch():
    """Show how partition boundaries change with different process counts."""
    print(f"\n🧪 Demonstrating partition boundary mismatches...")
    
    derangement_count = 1854  # For n=7
    
    configs = [
        {'processes': 2, 'per_process': 927},
        {'processes': 4, 'per_process': 463}, 
        {'processes': 8, 'per_process': 231}
    ]
    
    print(f"\nPartition boundaries for {derangement_count} derangements:")
    
    for config in configs:
        processes = config['processes']
        per_process = derangement_count // processes
        
        print(f"\n   {processes} processes ({per_process} derangements each):")
        
        for i in range(processes):
            start_idx = i * per_process
            if i == processes - 1:
                end_idx = derangement_count  # Last process gets remainder
            else:
                end_idx = (i + 1) * per_process
            
            print(f"     Process {i}: derangements {start_idx}-{end_idx-1}")
    
    print(f"\n❌ **Problem**: If checkpoint saved with 2 processes but resume with 4:")
    print(f"   - Checkpoint thinks process 0 did derangements 0-926")  
    print(f"   - But with 4 processes, process 0 only does 0-462")
    print(f"   - Derangements 463-926 would be missing or double-counted!")


def main():
    """Run all checkpoint validation tests."""
    print("🚀 CHECKPOINT CONFIGURATION VALIDATION TESTS")
    print("=" * 70)
    
    # Test 1: Process count mismatch
    print("\n" + "="*50)
    result1 = test_process_count_mismatch()
    
    # Test 2: Partition method mismatch  
    print("\n" + "="*50)
    result2 = test_partition_method_mismatch()
    
    # Show boundary mismatch
    print("\n" + "="*50)
    demonstrate_boundary_mismatch()
    
    # Show proper design
    show_proper_validation_design()
    
    print(f"\n🎯 CONCLUSION:")
    print(f"✅ Checkpoint validation is CRITICAL for parallel processing")
    print(f"❌ Current implementation lacks proper validation")
    print(f"🔧 Need to implement comprehensive checkpoint compatibility checking")


if __name__ == "__main__":
    main()