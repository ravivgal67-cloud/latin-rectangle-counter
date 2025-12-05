# Computation Time Tracking Feature

## Summary

Added computation time tracking and timestamp display to the Latin Rectangle Counter application.

## Changes Made

### 1. Database Schema
- **Added column**: `computation_time REAL` to store computation duration in seconds
- **Existing column**: `computed_at TIMESTAMP` already existed, now displayed in UI
- **Migration**: Automatic ALTER TABLE for existing databases

### 2. Data Model
- **Updated `CountResult`**: Added `computation_time` and `computed_at` fields
- Both fields are Optional (None for fresh computations, populated from cache)

### 3. Backend
- **`count_rectangles()`**: Now tracks computation time using `time.time()`
- **`CacheManager.put()`**: Stores computation_time in database
- **`CacheManager.get()`**: Retrieves computation_time and computed_at
- **`CacheManager.get_range()`**: Retrieves timing info for all results
- **`format_for_web()`**: Includes timing fields in JSON response

### 4. Frontend
- **Table columns**: Added "Time" and "Computed At" columns
- **Time formatting**: 
  - < 1ms: "<1ms"
  - < 1s: "123ms"
  - < 60s: "1.23s"
  - < 1h: "5m 30s"
  - ≥ 1h: "2h 15m"
- **Date formatting**:
  - < 1min: "Just now"
  - < 1h: "15m ago"
  - < 24h: "3h ago"
  - < 7d: "2d ago"
  - ≥ 7d: "12/05/2025 3:32 PM"

### 5. Display
- Computation time shows how long the calculation took
- Computed At shows when the result was cached (relative or absolute time)
- Both show "—" for results not yet cached or missing data

## Example Output

| r | n | Positive | Negative | Difference | Time | Computed At | Source |
|---|---|----------|----------|------------|------|-------------|--------|
| 2 | 3 | 2 | 0 | 2 | <1ms | Just now | Computed |
| 3 | 4 | 12 | 12 | 0 | 1.23ms | 5m ago | Cached |
| 5 | 5 | 384 | 960 | -576 | 33.45ms | 2h ago | Cached |
| 6 | 6 | 10,752 | 10,752 | 0 | 52.18ms | 12/04/2025 2:15 PM | Cached |

## Benefits

1. **Performance insights**: Users can see how long computations take
2. **Cache age**: Users know when results were computed
3. **Optimization validation**: Can verify that optimizations improve timing
4. **Historical tracking**: Database stores timing for all computations

## Testing

- ✅ All existing tests pass (24/24)
- ✅ Database migration works for existing databases
- ✅ Timing is tracked correctly
- ✅ Timestamps are set by database on insert
- ✅ Values retrieved correctly from cache

## Files Modified

- `core/counter.py` - Added timing tracking
- `cache/cache_manager.py` - Added computation_time column and retrieval
- `core/formatting.py` - Added timing fields to JSON output
- `web/templates/index.html` - Added Time and Computed At columns
- `web/static/app.js` - Added formatting functions and display logic
