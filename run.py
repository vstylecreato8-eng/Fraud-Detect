"""
Application runner script - Root level
Starts the Flask development server
"""
import os
import sys

# Add python directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from dotenv import load_dotenv
from App_Flask import app

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Get configuration from environment
    env = os.getenv('FLASK_ENV', 'development')
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    # Railway provides PORT environment variable, fallback to FLASK_PORT or 5000
    port = int(os.getenv('PORT') or os.getenv('FLASK_PORT', 5000))
    
    print(f"\n{'='*60}")
    print(f"Starting Transact Safe Check Backend")
    print(f"Environment: {env}")
    print(f"Server: http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/api/docs")
    print(f"Health Check: http://{host}:{port}/api/health")
    print(f"{'='*60}\n")
    
    # Run the development server
    app.run(
        host=host,
        port=port,
        debug=(env == 'development'),
        threaded=True,
        use_reloader=True
    )
