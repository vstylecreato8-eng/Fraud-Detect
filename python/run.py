"""
Application runner script
Starts the Flask development server
"""
import os
import sys
from dotenv import load_dotenv
from App_Flask import app

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Get configuration from environment
    env = os.getenv('FLASK_ENV', 'development')
    host = os.getenv('FLASK_HOST', '127.0.0.1')  # Changed from 0.0.0.0 to 127.0.0.1
    port = int(os.getenv('FLASK_PORT', 5000))
    
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
