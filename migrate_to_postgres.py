
#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL
"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Get database connections
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    sqlite_path = "server/crypto_fund.db"
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database not found")
        return False
    
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    
    # Connect to both databases
    sqlite_conn = sqlite3.connect(sqlite_path)
    postgres_conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # First, ensure PostgreSQL tables exist
        print("📋 Creating PostgreSQL tables...")
        
        # Create wallets table
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id SERIAL PRIMARY KEY,
                address TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL,
                network TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate wallets
        print("👛 Migrating wallets...")
        sqlite_cursor.execute("SELECT id, address, label, network FROM wallets")
        wallets = sqlite_cursor.fetchall()
        
        for wallet in wallets:
            postgres_cursor.execute("""
                INSERT INTO wallets (address, label, network) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (address) DO NOTHING
            """, (wallet[1], wallet[2], wallet[3]))
        
        # Create other tables and migrate data as needed
        print("💰 Creating assets table...")
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id SERIAL PRIMARY KEY,
                wallet_id INTEGER REFERENCES wallets(id),
                token_address TEXT,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                balance REAL NOT NULL,
                balance_formatted TEXT NOT NULL,
                price_usd REAL,
                value_usd REAL,
                purchase_price REAL DEFAULT 0,
                total_invested REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                unrealized_pnl REAL DEFAULT 0,
                total_return_pct REAL DEFAULT 0,
                is_nft BOOLEAN DEFAULT FALSE,
                nft_metadata TEXT,
                floor_price REAL DEFAULT 0,
                image_url TEXT,
                price_change_24h REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create remaining tables
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS hidden_assets (
                id SERIAL PRIMARY KEY,
                token_address TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                hidden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_history (
                id SERIAL PRIMARY KEY,
                total_value_usd REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_notes (
                id SERIAL PRIMARY KEY,
                symbol TEXT UNIQUE NOT NULL,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        postgres_cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet_status (
                wallet_id INTEGER PRIMARY KEY REFERENCES wallets(id),
                status TEXT,
                assets_found INTEGER,
                total_value REAL,
                error_message TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        postgres_conn.commit()
        print("✅ Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        postgres_conn.rollback()
        return False
        
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        postgres_cursor.close()
        postgres_conn.close()

if __name__ == "__main__":
    success = migrate_data()
    if success:
        print("🎉 Ready to use PostgreSQL!")
    else:
        print("💥 Migration failed. Please check your DATABASE_URL and try again.")
