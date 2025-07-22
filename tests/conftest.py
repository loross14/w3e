
import pytest
import asyncio
import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2.extras import RealDictCursor

# Set test environment variables
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_crypto_fund"
os.environ["ALCHEMY_API_KEY"] = "test_api_key_12345"
os.environ["NODE_ENV"] = "test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    with patch('server.main.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = None
        mock_cursor.rowcount = 0
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        
        mock_conn.return_value = mock_connection
        yield mock_connection, mock_cursor

@pytest.fixture
def test_client(mock_database):
    """Create FastAPI test client with mocked dependencies."""
    from server.main import app
    client = TestClient(app)
    yield client

@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        "total_value": 142481.64,
        "assets": [
            {
                "id": "0x0000000000000000000000000000000000000000",
                "symbol": "ETH",
                "name": "Ethereum",
                "balance": 18.349432,
                "balance_formatted": "18.349432",
                "price_usd": 3717.32,
                "value_usd": 68210.71,
                "purchase_price": 2416.258,
                "total_invested": 44336.96,
                "realized_pnl": 0,
                "unrealized_pnl": 23873.748,
                "total_return_pct": 53.846153,
                "notes": "",
                "is_nft": False,
                "floor_price": 0,
                "image_url": None,
                "nft_metadata": None
            }
        ],
        "wallet_count": 2,
        "performance_24h": 2.5
    }

@pytest.fixture
def sample_wallet_data():
    """Sample wallet data for testing."""
    return [
        {
            "id": 1,
            "address": "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
            "label": "Ethereum Safe Multisig",
            "network": "ETH"
        },
        {
            "id": 2,
            "address": "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb",
            "label": "Solana EOA",
            "network": "SOL"
        }
    ]

@pytest.fixture
def mock_alchemy_responses():
    """Mock Alchemy API responses."""
    eth_balance_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "0x1043561a8829300000"  # 18.35 ETH in wei
    }
    
    token_balances_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tokenBalances": [
                {
                    "contractAddress": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                    "tokenBalance": "0x21e19e0c9bab2400000"
                }
            ]
        }
    }
    
    return {
        "eth_balance": eth_balance_response,
        "token_balances": token_balances_response
    }

@pytest.fixture
def mock_price_responses():
    """Mock price API responses."""
    return {
        "ethereum": {"usd": 3717.32},
        "wrapped-bitcoin": {"usd": 118870},
        "solana": {"usd": 202.84}
    }
