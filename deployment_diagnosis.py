
#!/usr/bin/env python3
"""
Advanced deployment diagnosis script to identify root causes
"""
import os
import sys
import subprocess
import json
import time
from pathlib import Path

def check_build_artifacts():
    """Check if build artifacts exist and are valid"""
    print("🔍 Checking build artifacts...")
    
    dist_paths = ["dist", "../dist", "./dist"]
    found_dist = None
    
    for path in dist_paths:
        if os.path.exists(path):
            found_dist = path
            print(f"✅ Found dist directory: {path}")
            
            # Check essential files
            index_path = os.path.join(path, "index.html")
            if os.path.exists(index_path):
                file_size = os.path.getsize(index_path)
                print(f"✅ index.html exists: {file_size} bytes")
                
                # Check if it's a proper HTML file
                with open(index_path, 'r') as f:
                    content = f.read(500)  # First 500 chars
                    if "<!doctype" in content.lower() or "<html" in content.lower():
                        print("✅ index.html appears to be valid HTML")
                    else:
                        print("❌ index.html doesn't look like proper HTML")
                        print(f"Content preview: {content[:100]}...")
            else:
                print(f"❌ index.html missing in {path}")
            
            # Check assets directory
            assets_path = os.path.join(path, "assets")
            if os.path.exists(assets_path):
                asset_files = os.listdir(assets_path)
                print(f"✅ Assets directory has {len(asset_files)} files")
            else:
                print("❌ Assets directory missing")
        else:
            print(f"❌ No dist directory at: {path}")
    
    return found_dist

def check_deployment_config():
    """Check deployment configuration"""
    print("\n🔧 Checking deployment configuration...")
    
    # Check .replit file
    if os.path.exists(".replit"):
        with open(".replit", "r") as f:
            replit_content = f.read()
            print("✅ .replit file exists")
            
            if "deployment" in replit_content:
                print("✅ Deployment configuration found in .replit")
                
                # Extract deployment config
                lines = replit_content.split('\n')
                in_deployment = False
                for line in lines:
                    if '[deployment]' in line:
                        in_deployment = True
                    elif in_deployment and line.strip().startswith('['):
                        in_deployment = False
                    elif in_deployment and line.strip():
                        print(f"  {line.strip()}")
            else:
                print("❌ No deployment configuration in .replit")
    else:
        print("❌ .replit file missing")

def check_memory_usage():
    """Check current memory usage"""
    print("\n💾 Checking memory usage...")
    try:
        # Check available memory
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'Mem:' in line:
                    print(f"Memory: {line}")
        
        # Check disk usage
        result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"Disk: {lines[1]}")
                
    except Exception as e:
        print(f"⚠️ Could not check memory: {e}")

def test_build_process():
    """Test the build process"""
    print("\n🔨 Testing build process...")
    
    try:
        print("Running npm run build...")
        start_time = time.time()
        
        result = subprocess.run(
            ['npm', 'run', 'build'], 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        build_time = time.time() - start_time
        print(f"Build completed in {build_time:.1f} seconds")
        
        if result.returncode == 0:
            print("✅ Build successful")
            return True
        else:
            print("❌ Build failed")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Build timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def check_port_conflicts():
    """Check for port conflicts"""
    print("\n🔌 Checking port configuration...")
    
    # Check what ports are in use
    try:
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            port_80_used = any(':80 ' in line for line in lines)
            port_8000_used = any(':8000 ' in line for line in lines)
            
            print(f"Port 80 in use: {port_80_used}")
            print(f"Port 8000 in use: {port_8000_used}")
            
            if port_80_used:
                print("⚠️ Port 80 is already in use - this could cause deployment issues")
                
    except Exception as e:
        print(f"⚠️ Could not check ports: {e}")

def check_environment():
    """Check environment variables and configuration"""
    print("\n🌍 Checking environment...")
    
    # Check NODE_ENV
    node_env = os.environ.get('NODE_ENV', 'not set')
    print(f"NODE_ENV: {node_env}")
    
    # Check PORT
    port = os.environ.get('PORT', 'not set')
    print(f"PORT: {port}")
    
    # Check if we're in Replit
    replit_slug = os.environ.get('REPL_SLUG', 'not set')
    print(f"REPL_SLUG: {replit_slug}")
    
    # Check database and API keys
    db_url = os.environ.get('DATABASE_URL')
    api_key = os.environ.get('ALCHEMY_API_KEY')
    
    print(f"DATABASE_URL: {'✅ Set' if db_url else '❌ Missing'}")
    print(f"ALCHEMY_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")

def main():
    print("🔍 Advanced Deployment Diagnosis")
    print("=" * 50)
    
    # Run all checks
    dist_found = check_build_artifacts()
    check_deployment_config()
    check_memory_usage()
    
    # Test build process
    build_success = test_build_process()
    
    check_port_conflicts()
    check_environment()
    
    # Summary
    print("\n📋 DIAGNOSIS SUMMARY")
    print("=" * 30)
    
    if dist_found:
        print(f"✅ Build artifacts found in: {dist_found}")
    else:
        print("❌ No build artifacts found")
    
    if build_success:
        print("✅ Build process works")
    else:
        print("❌ Build process has issues")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 20)
    
    if not dist_found or not build_success:
        print("1. Build process issues detected - check build logs")
        print("2. Try clearing node_modules and reinstalling: rm -rf node_modules && npm install")
        print("3. Check if build process runs out of memory")
    
    print("4. Verify deployment configuration matches actual setup")
    print("5. Test deployment with minimal configuration first")

if __name__ == "__main__":
    main()
