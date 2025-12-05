"""
Flask application for Latin Rectangle Counter web API.

This module provides the web API endpoints for counting Latin rectangles
and managing cached results.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from typing import Dict, Any
import traceback
import os

from core.counter import count_rectangles, count_for_n, count_range
from core.validation import parse_input, validate_dimensions, DimensionType, ValidationResult
from core.formatting import format_for_web
from cache.cache_manager import CacheManager
from core.progress import ProgressTracker


def create_app(cache_manager: CacheManager = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        cache_manager: Optional CacheManager instance. If None, creates a new one.
        
    Returns:
        Configured Flask application
    """
    # Get the directory where this file is located
    web_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__, 
                template_folder=os.path.join(web_dir, 'templates'),
                static_folder=os.path.join(web_dir, 'static'))
    
    # Configure CORS for frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Suppress logging for progress endpoint
    import logging
    log = logging.getLogger('werkzeug')
    
    class ProgressFilter(logging.Filter):
        def filter(self, record):
            # Don't log /api/progress requests
            return '/api/progress' not in record.getMessage()
    
    log.addFilter(ProgressFilter())
    
    # Initialize cache manager
    if cache_manager is None:
        cache_manager = CacheManager()
    
    # Store cache_manager in app config for access in routes
    app.config['CACHE_MANAGER'] = cache_manager
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "status": "error",
            "error": str(error)
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors silently."""
        # Don't log 404s to reduce noise
        return jsonify({
            "status": "error",
            "error": "Not found"
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            "status": "error",
            "error": "Method not allowed"
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        return jsonify({
            "status": "error",
            "error": "Internal server error",
            "details": str(error)
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all uncaught exceptions."""
        # Don't log 404 errors to reduce noise
        from werkzeug.exceptions import NotFound
        if not isinstance(error, NotFound):
            app.logger.error(f"Unhandled exception: {error}")
            app.logger.error(traceback.format_exc())
        
        return jsonify({
            "status": "error",
            "error": "An unexpected error occurred",
            "details": str(error)
        }), 500
    
    # Frontend Routes
    @app.route('/')
    def index():
        """Serve the main application page."""
        return render_template('index.html')
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files."""
        return send_from_directory(app.static_folder, filename)
    
    # API Routes
    @app.route('/api/count', methods=['POST'])
    def api_count():
        """
        Count normalized Latin rectangles for specified dimensions.
        
        Request body (JSON):
            - r (int, optional): Number of rows
            - n (int, optional): Number of columns
            - n_start (int, optional): Start of n range
            - n_end (int, optional): End of n range
            
        Supports three modes:
        1. Single (r, n) pair: Provide both r and n
        2. All for n: Provide only n (counts all r from 2 to n)
        3. Range: Provide n_start and n_end (counts all n in range, all r for each n)
        
        Returns:
            JSON response with results or error
            
        Examples:
            POST /api/count
            {"r": 2, "n": 3}
            
            POST /api/count
            {"n": 4}
            
            POST /api/count
            {"n_start": 3, "n_end": 5}
        """
        try:
            # Parse request body
            data = request.get_json()
            
            if data is None:
                return jsonify({
                    "status": "error",
                    "error": "Request body must be JSON"
                }), 400
            
            # Extract parameters
            r = data.get('r')
            n = data.get('n')
            n_start = data.get('n_start')
            n_end = data.get('n_end')
            
            cache_manager = app.config['CACHE_MANAGER']
            
            # Clear old progress and set up progress tracking
            cache_manager.clear_progress()
            from core.progress import ProgressTracker
            progress_tracker = ProgressTracker(cache_manager)
            
            # Determine which mode and validate
            if r is not None and n is not None:
                # Single (r, n) mode
                validation = validate_dimensions(r=r, n=n)
                if not validation.is_valid:
                    return jsonify({
                        "status": "error",
                        "error": validation.error_message
                    }), 400
                
                result = count_rectangles(r, n, cache_manager, progress_tracker, enable_progress_db=True)
                results = [result]
                
            elif n is not None and r is None:
                # All for n mode
                validation = validate_dimensions(n=n)
                if not validation.is_valid:
                    return jsonify({
                        "status": "error",
                        "error": validation.error_message
                    }), 400
                
                results = count_for_n(n, cache_manager, progress_tracker, enable_progress_db=True)
                
            elif n_start is not None and n_end is not None:
                # Range mode
                validation = validate_dimensions(n_start=n_start, n_end=n_end)
                if not validation.is_valid:
                    return jsonify({
                        "status": "error",
                        "error": validation.error_message
                    }), 400
                
                results = count_range(n_start, n_end, cache_manager, progress_tracker, enable_progress_db=True)
                
            else:
                return jsonify({
                    "status": "error",
                    "error": "Invalid input: must specify either (r, n), n, or (n_start, n_end)"
                }), 400
            
            # Format results for web
            response = format_for_web(results)
            response["status"] = "success"
            
            return jsonify(response), 200
            
        except Exception as e:
            app.logger.error(f"Error in /api/count: {e}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/api/cache', methods=['GET'])
    def api_cache():
        """
        Get all cached dimension pairs.
        
        Returns:
            JSON response with list of (r, n) pairs that exist in the cache
            
        Example response:
            {
                "status": "success",
                "dimensions": [[2, 3], [2, 4], [3, 4]]
            }
        """
        try:
            cache_manager = app.config['CACHE_MANAGER']
            dimensions = cache_manager.get_all_cached_dimensions()
            
            return jsonify({
                "status": "success",
                "dimensions": dimensions
            }), 200
            
        except Exception as e:
            app.logger.error(f"Error in /api/cache: {e}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/api/progress', methods=['GET'])
    def api_progress():
        """
        Get current progress for ongoing computations.
        
        Returns:
            JSON with list of progress entries
        """
        try:
            cache_manager = app.config['CACHE_MANAGER']
            progress_data = cache_manager.get_all_progress()
            
            return jsonify({
                'status': 'success',
                'progress': progress_data
            }), 200
        except Exception as e:
            app.logger.error(f"Error in /api/progress: {e}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.route('/api/count/stream', methods=['POST'])
    def api_count_stream():
        """
        Stream counting progress using Server-Sent Events.
        
        This endpoint streams progress updates as the counting operation proceeds.
        Each event contains information about the current dimension being computed
        and the progress so far.
        
        Request body (JSON): Same as /api/count
        
        Response: text/event-stream with progress updates
        """
        from flask import Response, stream_with_context
        import json
        import time
        
        # Parse request body BEFORE creating generator (must be in request context)
        data = request.get_json()
        
        if data is None:
            error_event = f"data: {json.dumps({'status': 'error', 'error': 'Request body must be JSON'})}\n\n"
            return Response(error_event, mimetype='text/event-stream'), 400
        
        # Extract parameters
        r = data.get('r')
        n = data.get('n')
        n_start = data.get('n_start')
        n_end = data.get('n_end')
        
        cache_manager = app.config['CACHE_MANAGER']
        progress_tracker = ProgressTracker()
        
        try:
            # Generator function to stream results  
            def generate():
                # Collect all events
                all_events = []
                
                def collect_update(update):
                    event_data = {
                        'type': 'progress',
                        'data': update.to_dict()
                    }
                    all_events.append(f"data: {json.dumps(event_data)}\n\n")
                
                progress_tracker.set_callback(collect_update)
                
                try:
                    # Determine which mode and validate
                    if r is not None and n is not None:
                        validation = validate_dimensions(r=r, n=n)
                        if not validation.is_valid:
                            yield f"data: {json.dumps({'status': 'error', 'error': validation.error_message})}\n\n"
                            return
                        
                        result = count_rectangles(r, n, cache_manager, progress_tracker)
                        results = [result]
                        
                    elif n is not None and r is None:
                        validation = validate_dimensions(n=n)
                        if not validation.is_valid:
                            yield f"data: {json.dumps({'status': 'error', 'error': validation.error_message})}\n\n"
                            return
                        
                        results = count_for_n(n, cache_manager, progress_tracker)
                        
                    elif n_start is not None and n_end is not None:
                        validation = validate_dimensions(n_start=n_start, n_end=n_end)
                        if not validation.is_valid:
                            yield f"data: {json.dumps({'status': 'error', 'error': validation.error_message})}\n\n"
                            return
                        
                        results = count_range(n_start, n_end, cache_manager, progress_tracker)
                        
                    else:
                        yield f"data: {json.dumps({'status': 'error', 'error': 'Invalid input'})}\n\n"
                        return
                    
                    # Yield all collected events
                    print(f"Yielding {len(all_events)} progress events", flush=True)
                    for event in all_events:
                        print(f"Yielding event: {event[:100]}", flush=True)  # Log first 100 chars
                        yield event
                    
                    # Send final results
                    response_data = format_for_web(results)
                    response_data["status"] = "success"
                    response_data["type"] = "complete"
                    yield f"data: {json.dumps(response_data)}\n\n"
                    
                except Exception as e:
                    app.logger.error(f"Error in streaming: {e}")
                    yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
            
            return Response(stream_with_context(generate()), mimetype='text/event-stream')
            
        except Exception as e:
            app.logger.error(f"Error in /api/count/stream: {e}")
            import traceback
            app.logger.error(traceback.format_exc())
            # Return error as SSE event
            error_event = f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
            return Response(error_event, mimetype='text/event-stream'), 500
    
    @app.route('/api/cache/results', methods=['GET'])
    def api_cache_results():
        """
        Get cached results for a specified dimension range.
        
        Query parameters:
            - r_min (int, optional): Minimum row count (default: 2)
            - r_max (int, optional): Maximum row count (default: 100)
            - n_min (int, optional): Minimum column count (default: 2)
            - n_max (int, optional): Maximum column count (default: 100)
            
        Returns:
            JSON response with cached results in the specified range
            
        Example:
            GET /api/cache/results?r_min=2&r_max=3&n_min=3&n_max=5
            
            Response:
            {
                "status": "success",
                "results": [
                    {"r": 2, "n": 3, "positive_count": 1, "negative_count": 2, "difference": -1, "from_cache": true},
                    {"r": 2, "n": 4, "positive_count": 3, "negative_count": 6, "difference": -3, "from_cache": true}
                ]
            }
        """
        try:
            # Parse query parameters with defaults
            r_min = request.args.get('r_min', default=2, type=int)
            r_max = request.args.get('r_max', default=100, type=int)
            n_min = request.args.get('n_min', default=2, type=int)
            n_max = request.args.get('n_max', default=100, type=int)
            
            # Validate parameters
            if r_min < 2:
                return jsonify({
                    "status": "error",
                    "error": "r_min must be at least 2"
                }), 400
            
            if n_min < 2:
                return jsonify({
                    "status": "error",
                    "error": "n_min must be at least 2"
                }), 400
            
            if r_min > r_max:
                return jsonify({
                    "status": "error",
                    "error": "r_min must be <= r_max"
                }), 400
            
            if n_min > n_max:
                return jsonify({
                    "status": "error",
                    "error": "n_min must be <= n_max"
                }), 400
            
            # Retrieve cached results
            cache_manager = app.config['CACHE_MANAGER']
            results = cache_manager.get_range(r_min, r_max, n_min, n_max)
            
            # Format results for web
            response = format_for_web(results)
            response["status"] = "success"
            
            return jsonify(response), 200
            
        except Exception as e:
            app.logger.error(f"Error in /api/cache/results: {e}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    return app


# Create the default app instance
app = create_app()
