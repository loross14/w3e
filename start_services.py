
#!/usr/bin/env python3
import subprocess
import time
import threading
import os

def start_backend():
    """Start the FastAPI backend server"""
    try:
        os.chdir('server')
        subprocess.run(['python3', '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        subprocess.run(['python3', 'main.py'], check=True)
    except Exception as e:
        print(f"Backend error: {e}")

def start_frontend():
    """Start the Vite frontend server"""
    try:
        time.sleep(3)  # Wait for backend to start
        os.chdir('..')
        subprocess.run(['npm', 'run', 'dev'], check=True)
    except Exception as e:
        print(f"Frontend error: {e}")

if __name__ == "__main__":
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Start frontend in main thread
    start_frontend()
