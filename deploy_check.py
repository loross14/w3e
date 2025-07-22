
#!/usr/bin/env python3
"""
Deployment readiness check script
"""
import os
import sys
import subprocess
import json

def check_environment_variables():
    """Check required environment variables"""
    required_vars = ['DATABASE_URL', 'ALCHEMY_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_build_files():
    """Check if build files exist"""
    if not os.path.exists('dist'):
        print("❌ dist directory not found - run 'npm run build' first")
        return False
    
    if not os.path.exists('dist/index.html'):
        print("❌ dist/index.html not found - build failed")
        return False
    
    print("✅ Build files found")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        # Check Python dependencies
        subprocess.run([sys.executable, '-c', 'import fastapi, uvicorn, psycopg2'], check=True)
        print("✅ Python dependencies available")
        
        # Check if npm packages are installed
        if os.path.exists('node_modules'):
            print("✅ Node.js dependencies installed")
        else:
            print("⚠️ node_modules not found - run 'npm install'")
            return False
        
        return True
    except subprocess.CalledProcessError:
        print("❌ Some Python dependencies are missing")
        return False

def main():
    print("🔍 Checking deployment readiness...")
    
    checks = [
        check_environment_variables(),
        check_build_files(),
        check_dependencies()
    ]
    
    if all(checks):
        print("✅ Deployment ready!")
        return True
    else:
        print("❌ Deployment not ready - fix the issues above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
