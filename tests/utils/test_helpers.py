
import pytest
import asyncio
import json
import tempfile
import os
from typing import Dict, Any, List

class TestDataGenerator:
    """Generate test data for various scenarios."""
    
    @staticmethod
    def generate_wallet_data(count: int = 2) -> List[Dict[str, Any]]:
        """Generate sample wallet data."""
        wallets = []
        for i in range(count):
            wallet = {
                "id": i + 1,
                "address": f"0x{'1234567890123456789012345678901234567890'[:-len(str(i))]}{i}",
                "label": f"Test Wallet {i + 1}",
                "network": "ETH" if i % 2 == 0 else "SOL"
            }
            wallets.append(wallet)
        return wallets

    @staticmethod
    def generate_asset_data(count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample asset data."""
        assets = []
        sample_assets = [
            {"symbol": "ETH", "name": "Ethereum", "price": 3717.32},
            {"symbol": "WBTC", "name": "Wrapped Bitcoin", "price": 118870},
            {"symbol": "SOL", "name": "Solana", "price": 202.84},
            {"symbol": "PENDLE", "name": "Pendle", "price": 4.83},
            {"symbol": "PENGU", "name": "Pudgy Penguins", "price": 0.04073}
        ]
        
        for i in range(min(count, len(sample_assets))):
            sample = sample_assets[i]
            balance = 10.0 + i
            asset = {
                "id": f"0x{'0' * 39}{i}",
                "symbol": sample["symbol"],
                "name": sample["name"],
                "balance": balance,
                "balance_formatted": f"{balance:.6f}",
                "price_usd": sample["price"],
                "value_usd": balance * sample["price"],
                "purchase_price": sample["price"] * 0.6,  # 60% of current price
                "total_invested": balance * sample["price"] * 0.6,
                "realized_pnl": 0,
                "unrealized_pnl": balance * sample["price"] * 0.4,
                "total_return_pct": 66.67,
                "notes": f"Test notes for {sample['symbol']}",
                "is_nft": False,
                "floor_price": 0,
                "image_url": None,
                "nft_metadata": None
            }
            assets.append(asset)
        
        return assets

    @staticmethod
    def generate_nft_data(count: int = 2) -> List[Dict[str, Any]]:
        """Generate sample NFT data."""
        nfts = []
        for i in range(count):
            nft = {
                "id": f"0xnft{'0' * 35}{i}",
                "symbol": f"NFT{i}",
                "name": f"Test NFT Collection {i}",
                "balance": 5 + i,
                "balance_formatted": f"{5 + i} NFTs",
                "price_usd": 0,
                "value_usd": (5 + i) * 0.1,  # Floor price * count
                "purchase_price": 0,
                "total_invested": 0,
                "realized_pnl": 0,
                "unrealized_pnl": 0,
                "total_return_pct": 0,
                "notes": "",
                "is_nft": True,
                "floor_price": 0.1,
                "image_url": f"https://example.com/nft{i}.png",
                "nft_metadata": json.dumps({
                    "token_ids": [str(j) for j in range(1, 6 + i)],
                    "collection": f"Test Collection {i}",
                    "image_url": f"https://example.com/nft{i}.png"
                })
            }
            nfts.append(nft)
        
        return nfts

class MockAPIResponses:
    """Mock API responses for testing."""
    
    @staticmethod
    def ethereum_balance_response(balance_wei: int) -> Dict[str, Any]:
        """Generate Ethereum balance response."""
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": hex(balance_wei)
        }

    @staticmethod
    def alchemy_token_response(tokens: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate Alchemy token balance response."""
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tokenBalances": [
                    {
                        "contractAddress": token["address"],
                        "tokenBalance": token["balance"]
                    }
                    for token in tokens
                ]
            }
        }

    @staticmethod
    def coingecko_price_response(prices: Dict[str, float]) -> Dict[str, Any]:
        """Generate CoinGecko price response."""
        return {
            token: {"usd": price}
            for token, price in prices.items()
        }

    @staticmethod
    def solana_balance_response(balance_lamports: int) -> Dict[str, Any]:
        """Generate Solana balance response."""
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "value": balance_lamports
            }
        }

class TestEnvironment:
    """Manage test environment setup and teardown."""
    
    @staticmethod
    def setup_test_env():
        """Set up test environment variables."""
        test_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test_crypto_fund",
            "ALCHEMY_API_KEY": "test_api_key_12345",
            "NODE_ENV": "test",
            "PORT": "8000"
        }
        
        for key, value in test_env.items():
            os.environ[key] = value

    @staticmethod
    def cleanup_test_env():
        """Clean up test environment."""
        test_keys = ["DATABASE_URL", "ALCHEMY_API_KEY", "NODE_ENV", "PORT"]
        for key in test_keys:
            if key in os.environ:
                del os.environ[key]

    @staticmethod
    def create_temp_config(config_data: Dict[str, Any]) -> str:
        """Create temporary configuration file."""
        fd, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'w') as tmp_file:
                json.dump(config_data, tmp_file)
            return path
        except:
            os.close(fd)
            raise

class AsyncTestHelper:
    """Helper for async testing."""
    
    @staticmethod
    def run_async_test(coro):
        """Run async test function."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Wait for a condition to become true."""
        start_time = asyncio.get_event_loop().time()
        while True:
            if condition_func():
                return True
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            
            await asyncio.sleep(interval)

class DatabaseTestHelper:
    """Helper for database testing."""
    
    @staticmethod
    def reset_test_database(db_connection):
        """Reset test database to clean state."""
        cursor = db_connection.cursor()
        
        # Delete all data from test tables
        tables = ['assets', 'hidden_assets', 'asset_notes', 'purchase_history', 'portfolio_history', 'wallets']
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except:
                pass  # Table might not exist
        
        db_connection.commit()

    @staticmethod
    def insert_test_wallets(db_connection, wallets: List[Dict[str, Any]]):
        """Insert test wallets into database."""
        cursor = db_connection.cursor()
        
        for wallet in wallets:
            cursor.execute(
                "INSERT INTO wallets (address, label, network) VALUES (%s, %s, %s)",
                (wallet["address"], wallet["label"], wallet["network"])
            )
        
        db_connection.commit()
