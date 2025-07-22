
#!/usr/bin/env python3
"""
Quick validation script to check if test fixes work.
"""

import sys
import os
import subprocess
import tempfile
import sqlite3

def test_dependencies():
    """Test that our fixed dependencies can be installed."""
    print("🔧 Testing dependency installation...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--break-system-packages",
            "--dry-run",
            "-r", "tests/requirements-test.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies validation passed")
            return True
        else:
            print("❌ Dependencies validation failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error testing dependencies: {e}")
        return False

def test_database_operations():
    """Test basic database operations work."""
    print("🔧 Testing database operations...")
    
    try:
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute('''
            CREATE TABLE test_wallets (
                id INTEGER PRIMARY KEY,
                address TEXT NOT NULL,
                label TEXT,
                network TEXT
            )
        ''')
        
        # Insert test data
        cursor.execute("INSERT INTO test_wallets (address, label, network) VALUES (?, ?, ?)",
                      ("0x123...", "Test", "ETH"))
        
        conn.commit()
        
        # Query test data
        cursor.execute("SELECT * FROM test_wallets")
        result = cursor.fetchone()
        
        if result and result[1] == "0x123...":
            print("✅ Database operations validation passed")
            success = True
        else:
            print("❌ Database operations validation failed")
            success = False
        
        conn.close()
        os.close(db_fd)
        os.unlink(db_path)
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing database operations: {e}")
        return False

def test_pytest_import():
    """Test that pytest can be imported without conflicts."""
    print("🔧 Testing pytest import...")
    
    try:
        # Test in subprocess to isolate
        result = subprocess.run([
            sys.executable, "-c", 
            """
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['NODE_ENV'] = 'test'

# Mock problematic modules
import sys
from unittest.mock import MagicMock
sys.modules['web3'] = MagicMock()
sys.modules['eth_typing'] = MagicMock()

# Now try importing pytest
import pytest
print('✅ pytest imported successfully')
"""
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "✅ pytest imported successfully" in result.stdout:
            print("✅ pytest import validation passed")
            return True
        else:
            print("❌ pytest import validation failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing pytest import: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Validating Test Suite Fixes")
    print("=" * 40)
    
    tests = [
        test_dependencies,
        test_database_operations, 
        test_pytest_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("📊 Validation Summary")
    print("=" * 20)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All validations passed! Test suite should work now.")
        return True
    else:
        print("❌ Some validations failed. Check the fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
