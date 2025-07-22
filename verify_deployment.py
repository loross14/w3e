
#!/usr/bin/env python3
"""
Deployment verification script to ensure everything is properly configured
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def check_environment():
    """Check environment variables"""
    print("🔍 Checking Environment Variables...")
    
    database_url = os.environ.get('DATABASE_URL')
    alchemy_key = os.environ.get('ALCHEMY_API_KEY')
    
    if database_url:
        # Mask sensitive info for display
        masked_url = database_url[:30] + "..." if len(database_url) > 30 else database_url
        print(f"✅ DATABASE_URL: {masked_url}")
    else:
        print("❌ DATABASE_URL: Missing")
        return False
    
    if alchemy_key:
        masked_key = alchemy_key[:8] + "..." if len(alchemy_key) > 8 else alchemy_key
        print(f"✅ ALCHEMY_API_KEY: {masked_key}")
    else:
        print("❌ ALCHEMY_API_KEY: Missing")
        return False
    
    return True

def test_database_connection():
    """Test database connectivity"""
    print("\n🔍 Testing Database Connection...")
    
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
        
        conn = psycopg2.connect(
            database_url, 
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        cursor = conn.cursor()
        
        # Basic connectivity test
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        
        # Get database info
        cursor.execute("SELECT current_database(), current_user, version()")
        db_info = cursor.fetchone()
        
        print(f"✅ Database: {db_info['current_database']}")
        print(f"✅ User: {db_info['current_user']}")
        print(f"✅ PostgreSQL Version: {db_info['version'].split(',')[0]}")
        
        # Check if our tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        print(f"✅ Tables found: {len(tables)}")
        if tables:
            print(f"   {', '.join(tables)}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Solutions:")
        print("   1. Create PostgreSQL database in Replit Database tab")
        print("   2. Wait 30-60 seconds for database to start")
        print("   3. Check DATABASE_URL format")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_file_structure():
    """Check required files exist"""
    print("\n🔍 Checking File Structure...")
    
    required_files = [
        'server/main.py',
        'server/requirements.txt',
        'package.json',
        'index.html',
        '.replit'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_exist = False
    
    return all_exist

def main():
    print("🚀 Crypto Fund Deployment Verification")
    print("=" * 50)
    
    # Run all checks
    env_ok = check_environment()
    db_ok = test_database_connection()
    files_ok = check_file_structure()
    
    print("\n📋 Verification Summary")
    print("=" * 30)
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"File Structure: {'✅ PASS' if files_ok else '❌ FAIL'}")
    
    if env_ok and db_ok and files_ok:
        print("\n🎉 Deployment verification PASSED!")
        print("✅ Your application should work correctly")
        return True
    else:
        print("\n❌ Deployment verification FAILED!")
        print("💥 Please fix the issues above before deploying")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
