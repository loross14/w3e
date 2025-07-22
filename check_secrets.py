
#!/usr/bin/env python3
"""
Quick script to check if deployment secrets are properly set
"""
import os

def check_secrets():
    print("🔍 Checking deployment secrets...")
    
    database_url = os.environ.get('DATABASE_URL')
    alchemy_key = os.environ.get('ALCHEMY_API_KEY')
    
    if database_url:
        # Mask sensitive info
        masked_db = database_url[:20] + "..." + database_url[-10:] if len(database_url) > 30 else "***"
        print(f"✅ DATABASE_URL is set: {masked_db}")
    else:
        print("❌ DATABASE_URL is missing")
    
    if alchemy_key:
        masked_key = alchemy_key[:8] + "..." if len(alchemy_key) > 8 else "***"
        print(f"✅ ALCHEMY_API_KEY is set: {masked_key}")
    else:
        print("❌ ALCHEMY_API_KEY is missing")
    
    if database_url and alchemy_key:
        print("\n🎉 All secrets are properly configured!")
        return True
    else:
        print(f"\n❌ Missing secrets. Please add them in the Secrets tab.")
        return False

if __name__ == "__main__":
    check_secrets()
