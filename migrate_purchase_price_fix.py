
#!/usr/bin/env python3

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def migrate_database():
    """Apply database migrations for purchase price override fixes"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found. Please set up PostgreSQL database first.")
        sys.exit(1)

    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cursor = conn.cursor()

        print("🔧 Starting database migration for purchase price override fixes...")

        # 1. Create purchase price overrides table if it doesn't exist
        print("📋 Creating purchase_price_overrides table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_price_overrides (
                id SERIAL PRIMARY KEY,
                token_address TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                override_price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Add unique constraint to asset_cost_basis table if it doesn't exist
        print("🔧 Adding unique constraint to asset_cost_basis table...")
        try:
            cursor.execute('''
                ALTER TABLE asset_cost_basis 
                ADD CONSTRAINT asset_cost_basis_token_address_unique 
                UNIQUE (token_address)
            ''')
            print("✅ Added unique constraint to asset_cost_basis table")
        except psycopg2.errors.DuplicateTable:
            print("ℹ️ Unique constraint already exists on asset_cost_basis table")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️ Unique constraint already exists on asset_cost_basis table")
            else:
                print(f"⚠️ Could not add unique constraint: {e}")

        # 3. Migrate any existing manual purchase prices to overrides table
        print("🔄 Migrating existing manual purchase prices to overrides...")
        cursor.execute('''
            INSERT INTO purchase_price_overrides (token_address, symbol, override_price)
            SELECT a.token_address, a.symbol, a.purchase_price
            FROM assets a
            WHERE a.purchase_price > 0 
            AND a.token_address NOT IN (SELECT token_address FROM purchase_price_overrides)
            AND a.purchase_price != (
                CASE 
                    WHEN a.symbol = 'ETH' THEN a.price_usd * 0.65
                    WHEN a.symbol = 'WBTC' THEN a.price_usd * 0.55
                    WHEN a.symbol = 'SOL' THEN a.price_usd * 0.45
                    WHEN a.symbol = 'PENDLE' THEN a.price_usd * 0.4
                    WHEN a.symbol IN ('USDC', 'USDT', 'DAI') THEN 1.0
                    ELSE a.price_usd * 0.5
                END
            )
            ON CONFLICT (token_address) DO NOTHING
        ''')
        
        migrated_count = cursor.rowcount
        print(f"✅ Migrated {migrated_count} existing manual purchase prices to overrides")

        # 4. Verify tables are working
        cursor.execute("SELECT COUNT(*) as count FROM purchase_price_overrides")
        override_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM asset_cost_basis")
        cost_basis_count = cursor.fetchone()['count']

        print(f"📊 Database migration summary:")
        print(f"   - Purchase price overrides: {override_count}")
        print(f"   - Cost basis records: {cost_basis_count}")

        conn.commit()
        print("✅ Database migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_database()
