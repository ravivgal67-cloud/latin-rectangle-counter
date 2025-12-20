#!/usr/bin/env python3
"""
Simple script to run the Latin Rectangle Counter web application.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

if __name__ == "__main__":
    app = create_app()
    print("🚀 Starting Latin Rectangle Counter Web Application...")
    print("📱 Open your browser to: http://localhost:5001")
    print("🔗 API documentation: http://localhost:5001/api/docs")
    print("⏹️  Press Ctrl+C to stop")
    
    app.run(debug=True, host='0.0.0.0', port=5001)