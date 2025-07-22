
import pytest
import asyncio
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, Mock
import sqlite3
from pathlib import Path

# Set test environment variables
os.environ["NODE_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ALCHEMY_API_KEY"] = "test_api_key_12345"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    mock_connection = Mock()
    mock_cursor = Mock()
    
    # Configure cursor methods
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    mock_cursor.rowcount = 0
    mock_cursor.description = []
    
    # Configure connection methods
    mock_connection.cursor.return_value = mock_cursor
    mock_connection.commit.return_value = None
    mock_connection.rollback.return_value = None
    mock_connection.close.return_value = None
    
    # Context manager support
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.__exit__.return_value = None
    
    return mock_connection, mock_cursor

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for API testing."""
    client = Mock()
    
    # Mock successful responses
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_response.text = '{"status": "ok"}'
    mock_response.headers = {"content-type": "application/json"}
    
    client.get.return_value = mock_response
    client.post.return_value = mock_response
    client.put.return_value = mock_response
    client.delete.return_value = mock_response
    
    return client

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
def mock_api_responses():
    """Mock external API responses."""
    return {
        "alchemy_eth_balance": {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "0x1043561a8829300000"
        },
        "coingecko_prices": {
            "ethereum": {"usd": 3717.32},
            "wrapped-bitcoin": {"usd": 118870},
            "solana": {"usd": 202.84}
        },
        "portfolio_data": {
            "total_value": 142481.64,
            "assets": [],
            "wallet_count": 2
        }
    }

@pytest.fixture
def temp_database():
    """Create temporary SQLite database for testing."""
    db_fd, db_path = tempfile.mkstemp()
    
    # Create basic table structure
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE wallets (
            id INTEGER PRIMARY KEY,
            address TEXT NOT NULL,
            label TEXT,
            network TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE assets (
            id INTEGER PRIMARY KEY,
            wallet_id INTEGER,
            symbol TEXT,
            name TEXT,
            balance REAL,
            price_usd REAL,
            FOREIGN KEY (wallet_id) REFERENCES wallets (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": "sqlite:///:memory:",
        "ALCHEMY_API_KEY": "test_key_123",
        "NODE_ENV": "test"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars
