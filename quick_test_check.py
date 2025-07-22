
#!/usr/bin/env python3
"""
Quick test to verify our testing setup works
"""
import sys
import os
import subprocess

def main():
    print("🚀 Quick Test Setup Validation")
    print("=" * 40)
    
    # Test 1: Python sqlite3 availability
    try:
        import sqlite3
        print("✅ sqlite3 module available (built-in)")
    except ImportError:
        print("❌ sqlite3 not available")
        return False
    
    # Test 2: Basic pytest availability
    try:
        result = subprocess.run([sys.executable, "-c", "import pytest; print('pytest available')"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pytest can be imported")
        else:
            print("❌ pytest import failed")
            return False
    except Exception:
        print("❌ pytest test failed")
        return False
    
    # Test 3: Basic database operations
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO test (id) VALUES (1)")
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 1:
            print("✅ Database operations work")
        else:
            print("❌ Database test failed")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Test 4: Mock imports work
    try:
        from unittest.mock import Mock, patch
        print("✅ Mock utilities available")
    except ImportError:
        print("❌ Mock utilities failed")
        return False
    
    print("\n🎉 All basic tests passed! Testing setup should work.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
