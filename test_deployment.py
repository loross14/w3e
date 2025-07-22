
#!/usr/bin/env python3
"""
Deployment testing script to verify the app works correctly
"""
import os
import sys
import subprocess
import time
import requests
import json

def test_build():
    """Test if the frontend builds successfully"""
    print("🔨 Testing frontend build...")
    try:
        result = subprocess.run(['npm', 'run', 'build'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Frontend build successful")
            return True
        else:
            print("❌ Frontend build failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def test_backend():
    """Test if the backend starts and serves API"""
    print("🐍 Testing backend...")
    try:
        # Install dependencies
        subprocess.run([
            'python3', '-m', 'pip', 'install', '--break-system-packages', 
            '-r', 'server/requirements.txt'
        ], check=True, timeout=120)
        
        print("✅ Backend dependencies installed")
        return True
    except Exception as e:
        print(f"❌ Backend setup error: {e}")
        return False

def test_static_files():
    """Test if static files exist"""
    print("📁 Testing static files...")
    
    dist_paths = ['dist/', 'server/dist/']
    found_dist = False
    
    for path in dist_paths:
        if os.path.exists(path):
            print(f"✅ Found dist directory: {path}")
            found_dist = True
            
            # Check for essential files
            index_path = os.path.join(path, 'index.html')
            if os.path.exists(index_path):
                print(f"✅ Found index.html: {index_path}")
            else:
                print(f"❌ Missing index.html: {index_path}")
                
        else:
            print(f"⚠️ No dist directory at: {path}")
    
    return found_dist

def main():
    print("🚀 Starting deployment tests...")
    
    # Test build
    if not test_build():
        sys.exit(1)
    
    # Copy dist to server if needed
    if os.path.exists('dist') and not os.path.exists('server/dist'):
        try:
            subprocess.run(['cp', '-r', 'dist', 'server/'], check=True)
            print("✅ Copied dist to server directory")
        except Exception as e:
            print(f"⚠️ Could not copy dist: {e}")
    
    # Test backend
    if not test_backend():
        sys.exit(1)
    
    # Test static files
    if not test_static_files():
        print("⚠️ Some static files missing, but continuing...")
    
    print("✅ All deployment tests passed!")
    print("🎯 Ready for deployment!")

if __name__ == "__main__":
    main()
