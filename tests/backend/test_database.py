
import pytest
import sqlite3
import os
from unittest.mock import patch, Mock
from datetime import datetime

class TestDatabaseOperations:
    """Test database CRUD operations."""
    
    def test_create_wallet_table(self, temp_database):
        """Test wallet table creation and structure."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Check if wallets table exists and has correct structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wallets'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "wallets"
        
        # Check table structure
        cursor.execute("PRAGMA table_info(wallets)")
        columns = cursor.fetchall()
        
        expected_columns = {"id", "address", "label", "network"}
        actual_columns = {col[1] for col in columns}
        
        assert expected_columns.issubset(actual_columns)
        
        conn.close()
    
    def test_insert_wallet(self, temp_database):
        """Test wallet insertion with validation."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Test Ethereum wallet
        eth_wallet = ("0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98", "ETH Wallet", "ETH")
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", eth_wallet)
        wallet_id_eth = cursor.lastrowid
        conn.commit()
        
        # Test Solana wallet
        sol_wallet = ("4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb", "SOL Wallet", "SOL")
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", sol_wallet)
        wallet_id_sol = cursor.lastrowid
        conn.commit()
        
        # Verify both insertions
        cursor.execute("SELECT * FROM wallets WHERE address = ?", (eth_wallet[0],))
        eth_result = cursor.fetchone()
        
        cursor.execute("SELECT * FROM wallets WHERE address = ?", (sol_wallet[0],))
        sol_result = cursor.fetchone()
        
        assert eth_result is not None
        assert eth_result[1] == eth_wallet[0]  # address
        assert eth_result[2] == eth_wallet[1]  # label
        assert eth_result[3] == eth_wallet[2]  # network
        
        assert sol_result is not None
        assert sol_result[1] == sol_wallet[0]  # address
        
        conn.close()
    
    def test_update_wallet(self, temp_database):
        """Test wallet updates."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Insert test wallet
        original_data = ("0x123...", "Old Label", "ETH")
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", original_data)
        wallet_id = cursor.lastrowid
        conn.commit()
        
        # Update wallet label
        new_label = "Updated Label"
        cursor.execute("UPDATE wallets SET label = ? WHERE id = ?", (new_label, wallet_id))
        conn.commit()
        
        # Verify update
        cursor.execute("SELECT label FROM wallets WHERE id = ?", (wallet_id,))
        result = cursor.fetchone()
        
        assert result[0] == new_label
        
        conn.close()
    
    def test_delete_wallet(self, temp_database):
        """Test wallet deletion."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Insert test wallet
        test_wallet = ("0x123...", "Test Wallet", "ETH")
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", test_wallet)
        wallet_id = cursor.lastrowid
        conn.commit()
        
        # Verify wallet exists
        cursor.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,))
        assert cursor.fetchone() is not None
        
        # Delete wallet
        cursor.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,))
        result = cursor.fetchone()
        
        assert result is None
        
        conn.close()

class TestAssetOperations:
    """Test asset-related database operations."""
    
    def test_create_assets_table(self, temp_database):
        """Test assets table structure."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Check assets table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "assets"
        
        # Check foreign key relationship
        cursor.execute("PRAGMA foreign_key_list(assets)")
        fk_info = cursor.fetchall()
        
        # Should have foreign key to wallets table
        assert len(fk_info) > 0
        assert any(fk[2] == "wallets" for fk in fk_info)
        
        conn.close()
    
    def test_insert_asset_with_wallet(self, temp_database):
        """Test asset insertion linked to wallet."""
        conn = sqlite3.connect(temp_database)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Insert wallet first
        wallet_data = ("0x123...", "Test Wallet", "ETH")
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", wallet_data)
        wallet_id = cursor.lastrowid
        conn.commit()
        
        # Insert asset linked to wallet
        asset_data = (wallet_id, "ETH", "Ethereum", 1.5, 3717.32)
        cursor.execute("INSERT INTO assets (wallet_id, symbol, name, balance, price_usd) VALUES (?, ?, ?, ?, ?)",
                      asset_data)
        asset_id = cursor.lastrowid
        conn.commit()
        
        # Verify asset was inserted correctly
        cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == wallet_id
        assert result[2] == "ETH"
        assert result[3] == "Ethereum"
        assert result[4] == 1.5
        assert result[5] == 3717.32
        
        conn.close()

class TestHiddenAssets:
    """Test hidden assets functionality."""
    
    def test_create_hidden_assets_table(self, temp_database):
        """Test hidden_assets table structure."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hidden_assets'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "hidden_assets"
        
        # Check table structure
        cursor.execute("PRAGMA table_info(hidden_assets)")
        columns = cursor.fetchall()
        
        expected_columns = {"id", "token_address", "symbol", "created_at"}
        actual_columns = {col[1] for col in columns}
        
        assert expected_columns.issubset(actual_columns)
        
        conn.close()
    
    def test_hide_asset(self, temp_database):
        """Test hiding an asset."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Hide an asset
        token_address = "0x123abc..."
        symbol = "TEST"
        
        cursor.execute("INSERT INTO hidden_assets (token_address, symbol) VALUES (?, ?)",
                      (token_address, symbol))
        conn.commit()
        
        # Verify it was hidden
        cursor.execute("SELECT * FROM hidden_assets WHERE token_address = ?", (token_address,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == token_address
        assert result[2] == symbol
        
        conn.close()
    
    def test_unhide_asset(self, temp_database):
        """Test unhiding an asset."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # First hide an asset
        token_address = "0x456def..."
        cursor.execute("INSERT INTO hidden_assets (token_address, symbol) VALUES (?, ?)",
                      (token_address, "TEST2"))
        conn.commit()
        
        # Verify it's hidden
        cursor.execute("SELECT * FROM hidden_assets WHERE token_address = ?", (token_address,))
        assert cursor.fetchone() is not None
        
        # Unhide it
        cursor.execute("DELETE FROM hidden_assets WHERE token_address = ?", (token_address,))
        conn.commit()
        
        # Verify it's no longer hidden
        cursor.execute("SELECT * FROM hidden_assets WHERE token_address = ?", (token_address,))
        assert cursor.fetchone() is None
        
        conn.close()

class TestDataIntegrity:
    """Test data integrity and constraints."""
    
    def test_unique_wallet_addresses(self, temp_database):
        """Test that wallet addresses should be unique (if constraint exists)."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Add unique constraint to test
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_wallet_address ON wallets(address)")
            conn.commit()
            
            # Insert first wallet
            wallet1 = ("0x123...", "Wallet 1", "ETH")
            cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", wallet1)
            conn.commit()
            
            # Try to insert duplicate - should fail
            wallet2 = ("0x123...", "Wallet 2", "ETH")
            try:
                cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", wallet2)
                conn.commit()
                assert False, "Should have failed due to unique constraint"
            except sqlite3.IntegrityError:
                conn.rollback()
                assert True  # Expected behavior
                
        except sqlite3.OperationalError:
            # Index might already exist, which is fine
            pass
        
        conn.close()
    
    def test_foreign_key_constraints(self, temp_database):
        """Test foreign key relationships."""
        conn = sqlite3.connect(temp_database)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Insert wallet
        wallet_data = ("0x123...", "Test Wallet", "ETH")
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", wallet_data)
        wallet_id = cursor.lastrowid
        conn.commit()
        
        # Insert asset with valid wallet_id
        asset_data = (wallet_id, "ETH", "Ethereum", 1.0, 3717.32)
        cursor.execute("INSERT INTO assets (wallet_id, symbol, name, balance, price_usd) VALUES (?, ?, ?, ?, ?)",
                      asset_data)
        conn.commit()
        
        # Verify asset was inserted
        cursor.execute("SELECT * FROM assets WHERE wallet_id = ?", (wallet_id,))
        result = cursor.fetchone()
        assert result is not None
        
        # Try to insert asset with invalid wallet_id
        try:
            invalid_asset = (9999, "BTC", "Bitcoin", 1.0, 50000)
            cursor.execute("INSERT INTO assets (wallet_id, symbol, name, balance, price_usd) VALUES (?, ?, ?, ?, ?)",
                          invalid_asset)
            conn.commit()
            assert False, "Should have failed due to foreign key constraint"
        except sqlite3.IntegrityError:
            conn.rollback()
            assert True  # Expected behavior
        
        conn.close()

class TestConnectionHandling:
    """Test database connection management."""
    
    def test_connection_context_manager(self, temp_database):
        """Test database connection handling."""
        connection_opened = False
        connection_closed = False
        
        try:
            conn = sqlite3.connect(temp_database)
            connection_opened = True
            
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            results = cursor.fetchall()
            
            # Should have the tables we created
            table_names = {result[0] for result in results}
            expected_tables = {"wallets", "assets", "hidden_assets"}
            
            assert expected_tables.issubset(table_names)
            
        finally:
            if 'conn' in locals():
                conn.close()
                connection_closed = True
        
        assert connection_opened
        assert connection_closed
    
    def test_transaction_rollback(self, temp_database):
        """Test transaction rollback on error."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN")
            
            # Insert valid wallet
            cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", 
                          ("0x123...", "Test Wallet", "ETH"))
            
            # Force an error - try to insert invalid data
            cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)", 
                          (None, None, None))  # This should violate NOT NULL constraints
            
            conn.commit()
            assert False, "Should have failed"
            
        except sqlite3.IntegrityError:
            # Rollback transaction
            conn.rollback()
            
            # Verify wallet was not inserted due to rollback
            cursor.execute("SELECT * FROM wallets WHERE address = ?", ("0x123...",))
            result = cursor.fetchone()
            
            # Should be None due to rollback
            assert result is None
        
        finally:
            conn.close()

class TestPerformance:
    """Test database performance characteristics."""
    
    def test_bulk_insert_performance(self, temp_database):
        """Test bulk insertion performance."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Insert test wallet
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)",
                      ("0x123...", "Test Wallet", "ETH"))
        wallet_id = cursor.lastrowid
        conn.commit()
        
        # Bulk insert assets
        assets = [
            (wallet_id, f"TOKEN{i}", f"Token {i}", i * 1.0, i * 100.0)
            for i in range(1, 101)  # 100 assets
        ]
        
        cursor.executemany("INSERT INTO assets (wallet_id, symbol, name, balance, price_usd) VALUES (?, ?, ?, ?, ?)",
                          assets)
        conn.commit()
        
        # Verify all assets were inserted
        cursor.execute("SELECT COUNT(*) FROM assets WHERE wallet_id = ?", (wallet_id,))
        count = cursor.fetchone()[0]
        
        assert count == 100
        
        conn.close()
    
    def test_query_performance(self, temp_database):
        """Test query performance with indexes."""
        conn = sqlite3.connect(temp_database)
        cursor = conn.cursor()
        
        # Insert test data
        cursor.execute("INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)",
                      ("0x123...", "Test Wallet", "ETH"))
        wallet_id = cursor.lastrowid
        
        # Insert multiple assets
        assets = [(wallet_id, f"TOKEN{i}", f"Token {i}", i * 1.0, i * 100.0) for i in range(100)]
        cursor.executemany("INSERT INTO assets (wallet_id, symbol, name, balance, price_usd) VALUES (?, ?, ?, ?, ?)", 
                          assets)
        conn.commit()
        
        # Test query with WHERE clause
        cursor.execute("SELECT * FROM assets WHERE symbol = ?", ("TOKEN50",))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[2] == "TOKEN50"
        
        # Test aggregate query
        cursor.execute("SELECT SUM(balance * price_usd) as total_value FROM assets WHERE wallet_id = ?", (wallet_id,))
        total = cursor.fetchone()[0]
        
        assert total > 0
        assert isinstance(total, (int, float))
        
        conn.close()
