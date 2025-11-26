# Latin Rectangle Counter Web API

This module provides a Flask-based web API for counting normalized Latin rectangles.

## Running the API

To run the development server:

```bash
python -m flask --app web.app run
```

Or with debug mode:

```bash
python -m flask --app web.app run --debug
```

The API will be available at `http://localhost:5000`

## API Endpoints

### POST /api/count

Count normalized Latin rectangles for specified dimensions.

**Request Body (JSON):**

Three modes are supported:

1. **Single (r, n) pair:**
```json
{
  "r": 2,
  "n": 3
}
```

2. **All r for a given n:**
```json
{
  "n": 4
}
```

3. **Range of n values:**
```json
{
  "n_start": 3,
  "n_end": 5
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "r": 2,
      "n": 3,
      "positive_count": 1,
      "negative_count": 2,
      "difference": -1,
      "from_cache": false
    }
  ]
}
```

### GET /api/cache

Get all cached dimension pairs.

**Response:**
```json
{
  "status": "success",
  "dimensions": [[2, 3], [2, 4], [3, 4]]
}
```

### GET /api/cache/results

Get cached results for a specified dimension range.

**Query Parameters:**
- `r_min` (int, optional): Minimum row count (default: 2)
- `r_max` (int, optional): Maximum row count (default: 100)
- `n_min` (int, optional): Minimum column count (default: 2)
- `n_max` (int, optional): Maximum column count (default: 100)

**Example:**
```
GET /api/cache/results?r_min=2&r_max=3&n_min=3&n_max=5
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "r": 2,
      "n": 3,
      "positive_count": 1,
      "negative_count": 2,
      "difference": -1,
      "from_cache": true
    }
  ]
}
```

## Error Handling

All endpoints return errors in the following format:

```json
{
  "status": "error",
  "error": "Error message description"
}
```

Common error codes:
- `400`: Invalid input (e.g., r > n, invalid dimensions)
- `500`: Internal server error

## CORS

CORS is enabled for all `/api/*` endpoints, allowing requests from any origin.

## Testing

Run the API tests:

```bash
python -m pytest tests/test_web_api.py -v
```
