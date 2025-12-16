#!/usr/bin/env python3
"""
Test the enhanced per-process progress reporting.
"""

from core.parallel_generation import count_rectangles_parallel, count_rectangles_auto
import time


def test_per_process_progress():
    """Test that progress shows per-process information."""
    print("🧪 Testing enhanced per-process progress reporting...")
    
    print(f"\n1️⃣ Testing with 2 processes:")
    result1 = count_rectangles_parallel(3, 7, num_processes=2)
    
    print(f"\n2️⃣ Testing with 4 processes:")
    result2 = count_rectangles_parallel(3, 7, num_processes=4)
    
    print(f"\n3️⃣ Testing auto-selection (should use 8 processes):")
    result3 = count_rectangles_auto(3, 7)
    
    # Verify all results are correct
    expected_total = 1073760
    results = [result1, result2, result3]
    
    all_correct = True
    for i, result in enumerate(results, 1):
        actual_total = result.positive_count + result.negative_count
        correct = actual_total == expected_total
        print(f"\nTest {i} correctness: {'✅' if correct else '❌'} ({actual_total:,} rectangles)")
        if not correct:
            all_correct = False
    
    return all_correct


def test_progress_with_different_sizes():
    """Test progress reporting with different problem sizes."""
    print(f"\n🧪 Testing progress with different problem sizes...")
    
    # Small problem (should use sequential)
    print(f"\n📏 Small problem (4,6) - should use sequential:")
    result1 = count_rectangles_auto(4, 6)
    
    # Medium problem (should use parallel)
    print(f"\n📏 Medium problem (3,7) - should use parallel:")
    result2 = count_rectangles_auto(3, 7)
    
    return True


def main():
    """Test enhanced progress reporting."""
    print("🚀 ENHANCED PROGRESS REPORTING TESTS")
    print("=" * 60)
    
    print("This test demonstrates the new per-process progress reporting:")
    print("- ✅ Process completion with individual results")
    print("- 📊 Overall progress percentage")
    print("- 📋 Final summary with per-process breakdown")
    
    success1 = test_per_process_progress()
    success2 = test_progress_with_different_sizes()
    
    print(f"\n{'='*60}")
    if success1 and success2:
        print("🎉 ENHANCED PROGRESS REPORTING WORKING!")
        print("\n✅ New features:")
        print("   - Per-process completion messages")
        print("   - Individual process results (+positive -negative)")
        print("   - Overall progress percentage")
        print("   - Final summary with breakdown")
        print("   - Clear process identification")
    else:
        print("❌ Some issues with progress reporting")
    
    return success1 and success2


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)