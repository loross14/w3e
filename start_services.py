
#!/usr/bin/env python3
import subprocess
import os
import sys

def main():
    print("Starting Crypto Fund Backend...")
    
    # Change to server directory and install dependencies
    try:
        os.chdir('server')
        print("Installing Python dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        
        print("Starting FastAPI server on port 8000...")
        subprocess.run([sys.executable, 'main.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting backend: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
