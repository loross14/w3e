
#!/usr/bin/env python3
import subprocess
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

def serve_frontend():
    """Serve the built frontend files"""
    try:
        # Change to the dist directory where Vite builds the frontend
        if os.path.exists('dist'):
            os.chdir('dist')
            port = 80  # Use port 80 for deployment
            
            class Handler(SimpleHTTPRequestHandler):
                def end_headers(self):
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    super().end_headers()
                
                def do_GET(self):
                    # Handle SPA routing - serve index.html for all routes
                    if not os.path.exists(self.path.lstrip('/')):
                        self.path = '/index.html'
                    return super().do_GET()
            
            with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
                print(f"✅ Frontend server running on port {port}")
                httpd.serve_forever()
        else:
            print("❌ No dist directory found. Make sure 'npm run build' was successful.")
    except Exception as e:
        print(f"❌ Frontend server error: {e}")

def serve_backend():
    """Start the FastAPI backend"""
    try:
        print("🚀 Starting FastAPI backend...")
        
        # Install dependencies first
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'server/requirements.txt'], check=True)
        
        # Set environment variables for production
        os.environ['NODE_ENV'] = 'production'
        os.environ['PORT'] = '8000'
        
        # Change to server directory and start the FastAPI server
        os.chdir('server')
        subprocess.run([sys.executable, 'main.py'], check=True)
    except Exception as e:
        print(f"❌ Backend server error: {e}")
        sys.exit(1)

def main():
    print("🌟 Starting Crypto Fund Full-Stack Application...")
    
    # Build the frontend first
    print("📦 Building frontend...")
    try:
        subprocess.run(['npm', 'run', 'build'], check=True, cwd='.')
        print("✅ Frontend build complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend build failed: {e}")
        sys.exit(1)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=serve_backend, daemon=True)
    backend_thread.start()
    
    # Give backend time to start
    time.sleep(3)
    
    # Start frontend server (this will block)
    print("🎯 Starting frontend server...")
    serve_frontend()

if __name__ == "__main__":
    main()
