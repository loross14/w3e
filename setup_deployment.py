
#!/usr/bin/env python3
"""
Deployment setup script for Replit
"""
import os
import sys

def main():
    print("🚀 Setting up deployment for Replit...")
    
    # Check if we're in a Replit environment
    if not os.path.exists('.replit'):
        print("❌ This doesn't appear to be a Replit environment")
        return False
    
    # Check environment variables
    database_url = os.environ.get('DATABASE_URL')
    alchemy_key = os.environ.get('ALCHEMY_API_KEY')
    
    print("\n📋 Environment Check:")
    if database_url:
        print("✅ DATABASE_URL is set (PostgreSQL configured)")
    else:
        print("❌ DATABASE_URL not found")
        print("   → Go to Database tab and create PostgreSQL database")
    
    if alchemy_key:
        print("✅ ALCHEMY_API_KEY is set")
    else:
        print("❌ ALCHEMY_API_KEY not found")
        print("   → Go to Secrets tab (🔒) and add ALCHEMY_API_KEY")
    
    if database_url and alchemy_key:
        print("\n🎉 Environment is ready for deployment!")
        
        # Test database connection
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            conn.close()
            print("✅ Database connection test passed")
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False
            
        return True
    else:
        print("\n❌ Please fix the missing environment variables above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
