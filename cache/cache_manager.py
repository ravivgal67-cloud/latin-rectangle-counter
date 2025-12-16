"""
Cache manager for Latin Rectangle Counter.

This module provides the CacheManager class for storing and retrieving
computed results using SQLite as the persistence layer.
"""

import sqlite3
from typing import Optional, List, Tuple
from pathlib import Path
from core.counter import CountResult


class CacheManager:
    """
    Manages caching of Latin rectangle counting results using SQLite.
    
    The cache stores results in a SQLite database with the following schema:
    - results table: (r, n, positive_count, negative_count, difference)
    - Indexes on r and n for efficient queries
    
    Attributes:
        db_path: Path to the SQLite database file
        connection: SQLite database connection (created on demand)
    """
    
    def __init__(self, db_path: str = "latin_rectangles.db"):
        """
        Initialize the cache manager.
        
        Args:
            db_path: Path to the SQLite database file (default: "latin_rectangles.db")
        """
        self.db_path = db_path
        self._connection = None
        self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get or create a database connection.
        
        Returns:
            SQLite connection object
        """
        if self._connection is None:
            # Use check_same_thread=False to allow connection sharing across threads
            # This is safe because we're using SQLite's default serialized mode
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def _initialize_database(self):
        """
        Initialize the database schema if it doesn't exist.
        
        Creates the results table with columns:
        - r: Number of rows (INTEGER, NOT NULL)
        - n: Number of columns (INTEGER, NOT NULL)
        - positive_count: Count of positive rectangles (INTEGER, NOT NULL)
        - negative_count: Count of negative rectangles (INTEGER, NOT NULL)
        - difference: positive_count - negative_count (INTEGER, NOT NULL)
        - computed_at: Timestamp of computation (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
        
        Primary key: (r, n)
        Indexes: r, n
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                r INTEGER NOT NULL,
                n INTEGER NOT NULL,
                positive_count INTEGER NOT NULL,
                negative_count INTEGER NOT NULL,
                difference INTEGER NOT NULL,
                computation_time REAL DEFAULT 0.0,
                computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (r, n)
            )
        """)
        
        # Add computation_time column if it doesn't exist (for existing databases)
        try:
            cursor.execute("""
                ALTER TABLE results ADD COLUMN computation_time REAL DEFAULT 0.0
            """)
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Update existing NULL values to 0.0
        try:
            cursor.execute("""
                UPDATE results SET computation_time = 0.0 WHERE computation_time IS NULL
            """)
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_r ON results(r)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_n ON results(n)
        """)
        
        # Create progress table for tracking ongoing computations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                r INTEGER NOT NULL,
                n INTEGER NOT NULL,
                rectangles_scanned INTEGER NOT NULL,
                positive_count INTEGER NOT NULL,
                negative_count INTEGER NOT NULL,
                is_complete INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (r, n)
            )
        """)
        
        # Create checkpoints table for resumable computations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                r INTEGER NOT NULL,
                n INTEGER NOT NULL,
                partial_rows TEXT NOT NULL,
                positive_count INTEGER NOT NULL,
                negative_count INTEGER NOT NULL,
                rectangles_scanned INTEGER NOT NULL,
                elapsed_time REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (r, n)
            )
        """)
        
        # Create counter_checkpoints table for counter-based resumable computations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS counter_checkpoints (
                r INTEGER NOT NULL,
                n INTEGER NOT NULL,
                counters TEXT NOT NULL,
                positive_count INTEGER NOT NULL,
                negative_count INTEGER NOT NULL,
                rectangles_scanned INTEGER NOT NULL,
                elapsed_time REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (r, n)
            )
        """)
        
        conn.commit()
    
    def get(self, r: int, n: int) -> Optional[CountResult]:
        """
        Retrieve a cached result for the given dimensions.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            CountResult if found in cache, None otherwise
            
        Examples:
            >>> cache = CacheManager(":memory:")
            >>> result = cache.get(2, 3)
            >>> result is None
            True
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r, n, positive_count, negative_count, difference, computation_time, computed_at
            FROM results
            WHERE r = ? AND n = ?
        """, (r, n))
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return CountResult(
            r=row['r'],
            n=row['n'],
            positive_count=row['positive_count'],
            negative_count=row['negative_count'],
            difference=row['difference'],
            from_cache=True,
            computation_time=row['computation_time'],
            computed_at=row['computed_at']
        )
    
    def put(self, result: CountResult) -> None:
        """
        Store a result in the cache.
        
        If a result for the same (r, n) already exists, it will be replaced.
        
        Args:
            result: CountResult to store
            
        Examples:
            >>> cache = CacheManager(":memory:")
            >>> result = CountResult(2, 3, 1, 2, -1, False)
            >>> cache.put(result)
            >>> cached = cache.get(2, 3)
            >>> cached.positive_count
            1
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO results (r, n, positive_count, negative_count, difference, computation_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (result.r, result.n, result.positive_count, result.negative_count, result.difference, result.computation_time))
        
        conn.commit()
    
    def get_all_cached_dimensions(self) -> List[Tuple[int, int]]:
        """
        Get all (r, n) dimension pairs that exist in the cache.
        
        Returns:
            List of (r, n) tuples representing all cached dimensions
            
        Examples:
            >>> cache = CacheManager(":memory:")
            >>> cache.put(CountResult(2, 3, 1, 2, -1, False))
            >>> cache.put(CountResult(3, 4, 5, 6, -1, False))
            >>> dimensions = cache.get_all_cached_dimensions()
            >>> (2, 3) in dimensions
            True
            >>> (3, 4) in dimensions
            True
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r, n FROM results ORDER BY n, r
        """)
        
        return [(row['r'], row['n']) for row in cursor.fetchall()]
    
    def get_range(self, r_min: int, r_max: int, n_min: int, n_max: int) -> List[CountResult]:
        """
        Retrieve all cached results within the specified dimension range.
        
        Args:
            r_min: Minimum row count (inclusive)
            r_max: Maximum row count (inclusive)
            n_min: Minimum column count (inclusive)
            n_max: Maximum column count (inclusive)
            
        Returns:
            List of CountResults for all cached dimensions in the range
            
        Examples:
            >>> cache = CacheManager(":memory:")
            >>> cache.put(CountResult(2, 3, 1, 2, -1, False))
            >>> cache.put(CountResult(2, 4, 3, 6, -3, False))
            >>> cache.put(CountResult(3, 4, 5, 6, -1, False))
            >>> results = cache.get_range(2, 3, 3, 4)
            >>> len(results)
            3
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r, n, positive_count, negative_count, difference, computation_time, computed_at
            FROM results
            WHERE r >= ? AND r <= ? AND n >= ? AND n <= ?
            ORDER BY n, r
        """, (r_min, r_max, n_min, n_max))
        
        results = []
        for row in cursor.fetchall():
            results.append(CountResult(
                r=row['r'],
                n=row['n'],
                positive_count=row['positive_count'],
                negative_count=row['negative_count'],
                difference=row['difference'],
                from_cache=True,
                computation_time=row['computation_time'],
                computed_at=row['computed_at']
            ))
        
        return results
    
    def update_progress(self, r: int, n: int, rectangles_scanned: int, 
                       positive_count: int, negative_count: int, is_complete: bool = False):
        """
        Update progress for a computation.
        
        Args:
            r: Number of rows
            n: Number of columns
            rectangles_scanned: Number of rectangles scanned so far
            positive_count: Count of positive rectangles found
            negative_count: Count of negative rectangles found
            is_complete: Whether computation is complete
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO progress 
            (r, n, rectangles_scanned, positive_count, negative_count, is_complete, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (r, n, rectangles_scanned, positive_count, negative_count, 1 if is_complete else 0))
        
        conn.commit()
    
    def get_all_progress(self):
        """
        Get all current progress entries.
        
        Returns:
            List of dictionaries with progress information
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r, n, rectangles_scanned, positive_count, negative_count, is_complete
            FROM progress
            ORDER BY n, r
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'r': row['r'],
                'n': row['n'],
                'rectangles_scanned': row['rectangles_scanned'],
                'positive_count': row['positive_count'],
                'negative_count': row['negative_count'],
                'is_complete': bool(row['is_complete'])
            })
        
        return results
    
    def clear_progress(self):
        """Clear all progress entries."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM progress")
        conn.commit()
    
    def save_checkpoint(self, r: int, n: int, partial_rows: List[List[int]], 
                       positive_count: int, negative_count: int, 
                       rectangles_scanned: int, elapsed_time: float):
        """
        Save a computation checkpoint (legacy method for partial rows).
        
        Args:
            r: Number of rows
            n: Number of columns
            partial_rows: List of completed rows so far
            positive_count: Count of positive rectangles found
            negative_count: Count of negative rectangles found
            rectangles_scanned: Total rectangles scanned
            elapsed_time: Time spent so far in seconds
        """
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        partial_rows_json = json.dumps(partial_rows)
        
        cursor.execute("""
            INSERT OR REPLACE INTO checkpoints 
            (r, n, partial_rows, positive_count, negative_count, 
             rectangles_scanned, elapsed_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (r, n, partial_rows_json, positive_count, negative_count, 
              rectangles_scanned, elapsed_time))
        
        conn.commit()
    
    def load_checkpoint(self, r: int, n: int) -> Optional[dict]:
        """
        Load a computation checkpoint (legacy method for partial rows).
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            Dictionary with checkpoint data or None if no checkpoint exists
        """
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT partial_rows, positive_count, negative_count, 
                   rectangles_scanned, elapsed_time, created_at
            FROM checkpoints
            WHERE r = ? AND n = ?
        """, (r, n))
        
        row = cursor.fetchone()
        if row is None:
            return None
        
        return {
            'partial_rows': json.loads(row['partial_rows']),
            'positive_count': row['positive_count'],
            'negative_count': row['negative_count'],
            'rectangles_scanned': row['rectangles_scanned'],
            'elapsed_time': row['elapsed_time'],
            'created_at': row['created_at']
        }
    
    def delete_checkpoint(self, r: int, n: int):
        """
        Delete a computation checkpoint (legacy method).
        
        Args:
            r: Number of rows
            n: Number of columns
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM checkpoints WHERE r = ? AND n = ?
        """, (r, n))
        
        conn.commit()
    
    def save_checkpoint_counters(self, r: int, n: int, counters: List[int], 
                                positive_count: int, negative_count: int, 
                                rectangles_scanned: int, elapsed_time: float):
        """
        Save a computation checkpoint using counter state.
        
        Args:
            r: Number of rows
            n: Number of columns
            counters: List of counter values for each row level
            positive_count: Count of positive rectangles found
            negative_count: Count of negative rectangles found
            rectangles_scanned: Total rectangles scanned
            elapsed_time: Time spent so far in seconds
        """
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create counter_checkpoints table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS counter_checkpoints (
                r INTEGER NOT NULL,
                n INTEGER NOT NULL,
                counters TEXT NOT NULL,
                positive_count INTEGER NOT NULL,
                negative_count INTEGER NOT NULL,
                rectangles_scanned INTEGER NOT NULL,
                elapsed_time REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (r, n)
            )
        """)
        
        counters_json = json.dumps(counters)
        
        cursor.execute("""
            INSERT OR REPLACE INTO counter_checkpoints 
            (r, n, counters, positive_count, negative_count, 
             rectangles_scanned, elapsed_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (r, n, counters_json, positive_count, negative_count, 
              rectangles_scanned, elapsed_time))
        
        conn.commit()
    
    def load_checkpoint_counters(self, r: int, n: int) -> Optional[dict]:
        """
        Load a computation checkpoint using counter state.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            Dictionary with checkpoint data or None if no checkpoint exists
        """
        import json
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if counter_checkpoints table exists
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='counter_checkpoints'
        """)
        
        if cursor.fetchone() is None:
            return None  # Table doesn't exist, no checkpoint
        
        cursor.execute("""
            SELECT counters, positive_count, negative_count, 
                   rectangles_scanned, elapsed_time, created_at
            FROM counter_checkpoints
            WHERE r = ? AND n = ?
        """, (r, n))
        
        row = cursor.fetchone()
        if row is None:
            return None
        
        return {
            'counters': json.loads(row['counters']),
            'positive_count': row['positive_count'],
            'negative_count': row['negative_count'],
            'rectangles_scanned': row['rectangles_scanned'],
            'elapsed_time': row['elapsed_time'],
            'created_at': row['created_at']
        }
    
    def delete_checkpoint_counters(self, r: int, n: int):
        """
        Delete a computation checkpoint using counter state.
        
        Args:
            r: Number of rows
            n: Number of columns
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if table exists first
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='counter_checkpoints'
        """)
        
        if cursor.fetchone() is not None:
            cursor.execute("""
                DELETE FROM counter_checkpoints WHERE r = ? AND n = ?
            """, (r, n))
            
            conn.commit()
    
    def checkpoint_counters_exists(self, r: int, n: int) -> bool:
        """
        Check if a counter-based checkpoint exists for the given dimensions.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            True if checkpoint exists, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if table exists first
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='counter_checkpoints'
        """)
        
        if cursor.fetchone() is None:
            return False
        
        cursor.execute("""
            SELECT 1 FROM counter_checkpoints WHERE r = ? AND n = ? LIMIT 1
        """, (r, n))
        
        return cursor.fetchone() is not None
    
    def checkpoint_exists(self, r: int, n: int) -> bool:
        """
        Check if a checkpoint exists for the given dimensions.
        
        Args:
            r: Number of rows
            n: Number of columns
            
        Returns:
            True if checkpoint exists, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 1 FROM checkpoints WHERE r = ? AND n = ? LIMIT 1
        """, (r, n))
        
        return cursor.fetchone() is not None

    def close(self):
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
