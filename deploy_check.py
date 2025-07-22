
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
    
    print("🔍 Checking environment variables...")
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ Missing: {var}")
        else:
            # Show partial value for security
            if var == 'DATABASE_URL':
                masked_value = value[:20] + "..." + value[-10:] if len(value) > 30 else value[:10] + "..."
            else:
                masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ Found: {var} = {masked_value}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n📋 To fix this in Replit:")
        if 'DATABASE_URL' in missing_vars:
            print("  1. Go to the Database tab in Replit")
            print("  2. Click 'Create Database' and select PostgreSQL")
            print("  3. The DATABASE_URL will be automatically set")
        if 'ALCHEMY_API_KEY' in missing_vars:
            print("  4. Go to the Secrets tab (🔒) in Replit")
            print("  5. Add a new secret: ALCHEMY_API_KEY = your_alchemy_key")
        return False
    else:
        print("\n✅ All required environment variables are set")
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
