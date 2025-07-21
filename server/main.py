
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from web3 import Web3
import sqlite3
import json
import requests

app = FastAPI(title="Crypto Fund API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alchemy configuration
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
if not ALCHEMY_API_KEY:
    raise RuntimeError("ALCHEMY_API_KEY environment variable is required")

# Initialize Web3 with Alchemy endpoint
ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

# ERC-20 ABI for token interactions
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

# Database initialization
def init_db():
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    # Wallets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE NOT NULL,
            label TEXT NOT NULL,
            network TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id INTEGER,
            token_address TEXT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            balance REAL NOT NULL,
            balance_formatted TEXT NOT NULL,
            price_usd REAL,
            value_usd REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallets (id)
        )
    ''')
    
    # Portfolio history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_value_usd REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Asset notes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class WalletCreate(BaseModel):
    address: str
    label: str
    network: str

class WalletResponse(BaseModel):
    id: int
    address: str
    label: str
    network: str

class AssetResponse(BaseModel):
    id: int
    symbol: str
    name: str
    balance: float
    balance_formatted: str
    price_usd: Optional[float]
    value_usd: Optional[float]
    notes: Optional[str] = ""

class PortfolioResponse(BaseModel):
    total_value: float
    assets: List[AssetResponse]
    wallet_count: int
    performance_24h: float

class WalletDetailsResponse(BaseModel):
    wallet: WalletResponse
    assets: List[AssetResponse]
    total_value: float
    performance_24h: float

# Utility functions
async def get_token_prices(token_addresses: List[str]) -> Dict[str, float]:
    """Get token prices from CoinGecko API"""
    if not token_addresses:
        return {}
    
    # Filter out ETH and known stablecoins
    eth_address = "0x0000000000000000000000000000000000000000"
    usdc_address = "0xa0b86a33e6d6dbf0c73809f0c7d6c0d5c0b9c5c1"
    
    price_map = {}
    
    try:
        async with httpx.AsyncClient() as client:
            # Get ETH price
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "ethereum", "vs_currencies": "usd"}
            )
            if response.status_code == 200:
                data = response.json()
                price_map[eth_address] = data.get("ethereum", {}).get("usd", 0)
            
            # Get other token prices if any
            if len(token_addresses) > 1:
                contract_addresses = [addr for addr in token_addresses if addr != eth_address]
                if contract_addresses:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/token_price/ethereum",
                        params={
                            "contract_addresses": ",".join(contract_addresses),
                            "vs_currencies": "usd"
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for addr, price_data in data.items():
                            price_map[addr] = price_data.get("usd", 0)
    
    except Exception as e:
        print(f"Error fetching prices: {e}")
    
    return price_map

async def get_wallet_assets(wallet_address: str, network: str) -> List[Dict]:
    """Fetch assets for a wallet using Web3 and Alchemy API"""
    assets = []
    
    try:
        if network.upper() == "ETH":
            # Get ETH balance
            eth_balance_wei = w3.eth.get_balance(wallet_address)
            eth_balance_formatted = float(eth_balance_wei) / 10**18
            
            if eth_balance_formatted > 0:
                assets.append({
                    "token_address": "0x0000000000000000000000000000000000000000",
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "balance": eth_balance_formatted,
                    "balance_formatted": f"{eth_balance_formatted:.6f}",
                    "decimals": 18
                })
            
            # Get ERC-20 token balances using Alchemy API
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        ALCHEMY_URL,
                        json={
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "alchemy_getTokenBalances",
                            "params": [wallet_address]
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        token_balances = data.get("result", {}).get("tokenBalances", [])
                        
                        for token_balance in token_balances:
                            if token_balance.get("tokenBalance") and int(token_balance["tokenBalance"], 16) > 0:
                                try:
                                    contract_address = token_balance["contractAddress"]
                                    
                                    # Get token metadata using Alchemy API
                                    metadata_response = await client.post(
                                        ALCHEMY_URL,
                                        json={
                                            "id": 1,
                                            "jsonrpc": "2.0",
                                            "method": "alchemy_getTokenMetadata",
                                            "params": [contract_address]
                                        }
                                    )
                                    
                                    if metadata_response.status_code == 200:
                                        metadata = metadata_response.json().get("result", {})
                                        balance_int = int(token_balance["tokenBalance"], 16)
                                        decimals = metadata.get("decimals", 18)
                                        balance_formatted = balance_int / (10 ** decimals)
                                        
                                        if balance_formatted > 0.001:  # Filter out dust
                                            assets.append({
                                                "token_address": contract_address,
                                                "symbol": metadata.get("symbol", "UNKNOWN"),
                                                "name": metadata.get("name", "Unknown Token"),
                                                "balance": balance_formatted,
                                                "balance_formatted": f"{balance_formatted:.6f}",
                                                "decimals": decimals
                                            })
                                except Exception as e:
                                    print(f"Error getting metadata for {contract_address}: {e}")
                                    
            except Exception as e:
                print(f"Error fetching token balances: {e}")
        
        elif network.upper() == "SOL":
            # For Solana, we would need a different API
            # For now, return placeholder - you'd integrate with Solana RPC
            pass
            
    except Exception as e:
        print(f"Error fetching wallet assets for {wallet_address}: {e}")
    
    return assets

# API endpoints
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "Crypto Fund API", "status": "running"}

@app.post("/wallets", response_model=WalletResponse)
async def create_wallet(wallet: WalletCreate):
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO wallets (address, label, network) VALUES (?, ?, ?)",
            (wallet.address, wallet.label, wallet.network)
        )
        wallet_id = cursor.lastrowid
        conn.commit()
        
        return WalletResponse(
            id=wallet_id,
            address=wallet.address,
            label=wallet.label,
            network=wallet.network
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Wallet address already exists")
    finally:
        conn.close()

@app.get("/wallets", response_model=List[WalletResponse])
async def get_wallets():
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, address, label, network FROM wallets")
    wallets = cursor.fetchall()
    conn.close()
    
    return [
        WalletResponse(id=w[0], address=w[1], label=w[2], network=w[3])
        for w in wallets
    ]

@app.delete("/wallets/{wallet_id}")
async def delete_wallet(wallet_id: int):
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM assets WHERE wallet_id = ?", (wallet_id,))
    cursor.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    conn.commit()
    conn.close()
    return {"message": "Wallet deleted successfully"}

@app.post("/portfolio/update")
async def update_portfolio(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_portfolio_data)
    return {"message": "Portfolio update started"}

@app.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    # Get all assets with notes
    cursor.execute("""
        SELECT a.id, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(n.notes, '') as notes
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        ORDER BY a.value_usd DESC
    """)
    assets_data = cursor.fetchall()
    
    assets = [
        AssetResponse(
            id=a[0], symbol=a[1], name=a[2], balance=a[3],
            balance_formatted=a[4], price_usd=a[5], value_usd=a[6], notes=a[7]
        )
        for a in assets_data
    ]
    
    total_value = sum(asset.value_usd or 0 for asset in assets)
    
    # Get wallet count
    cursor.execute("SELECT COUNT(*) FROM wallets")
    wallet_count = cursor.fetchone()[0]
    
    # Calculate 24h performance (simplified)
    cursor.execute("""
        SELECT total_value_usd FROM portfolio_history 
        ORDER BY timestamp DESC LIMIT 2
    """)
    history = cursor.fetchall()
    performance_24h = 0.0
    if len(history) >= 2:
        current_value = history[0][0]
        previous_value = history[1][0]
        if previous_value > 0:
            performance_24h = ((current_value - previous_value) / previous_value) * 100
    
    conn.close()
    
    return PortfolioResponse(
        total_value=total_value,
        assets=assets,
        wallet_count=wallet_count,
        performance_24h=performance_24h
    )

@app.get("/wallets/{wallet_id}/details", response_model=WalletDetailsResponse)
async def get_wallet_details(wallet_id: int):
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    # Get wallet info
    cursor.execute("SELECT id, address, label, network FROM wallets WHERE id = ?", (wallet_id,))
    wallet_data = cursor.fetchone()
    if not wallet_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallet = WalletResponse(
        id=wallet_data[0], address=wallet_data[1], 
        label=wallet_data[2], network=wallet_data[3]
    )
    
    # Get wallet assets
    cursor.execute("""
        SELECT a.id, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(n.notes, '') as notes
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        WHERE a.wallet_id = ?
        ORDER BY a.value_usd DESC
    """, (wallet_id,))
    assets_data = cursor.fetchall()
    
    assets = [
        AssetResponse(
            id=a[0], symbol=a[1], name=a[2], balance=a[3],
            balance_formatted=a[4], price_usd=a[5], value_usd=a[6], notes=a[7]
        )
        for a in assets_data
    ]
    
    total_value = sum(asset.value_usd or 0 for asset in assets)
    
    conn.close()
    
    return WalletDetailsResponse(
        wallet=wallet,
        assets=assets,
        total_value=total_value,
        performance_24h=0.0  # Simplified for now
    )

@app.put("/assets/{symbol}/notes")
async def update_asset_notes(symbol: str, notes: str):
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO asset_notes (symbol, notes, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (symbol, notes))
    
    conn.commit()
    conn.close()
    
    return {"message": "Notes updated successfully"}

async def update_portfolio_data():
    """Background task to update portfolio data"""
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    try:
        # Clear existing assets
        cursor.execute("DELETE FROM assets")
        
        # Get all wallets
        cursor.execute("SELECT id, address, network FROM wallets")
        wallets = cursor.fetchall()
        
        all_token_addresses = set()
        all_assets = []
        
        # Fetch assets for each wallet
        for wallet_id, address, network in wallets:
            assets = await get_wallet_assets(address, network)
            for asset in assets:
                asset['wallet_id'] = wallet_id
                all_assets.append(asset)
                all_token_addresses.add(asset['token_address'])
        
        # Get prices for all tokens
        price_map = await get_token_prices(list(all_token_addresses))
        
        # Insert assets with prices
        total_portfolio_value = 0
        for asset in all_assets:
            price_usd = price_map.get(asset['token_address'], 0)
            value_usd = asset['balance'] * price_usd
            total_portfolio_value += value_usd
            
            cursor.execute("""
                INSERT INTO assets 
                (wallet_id, token_address, symbol, name, balance, balance_formatted, price_usd, value_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset['wallet_id'], asset['token_address'], asset['symbol'], 
                asset['name'], asset['balance'], asset['balance_formatted'], 
                price_usd, value_usd
            ))
        
        # Record portfolio history
        cursor.execute(
            "INSERT INTO portfolio_history (total_value_usd) VALUES (?)",
            (total_portfolio_value,)
        )
        
        conn.commit()
        print(f"Portfolio updated: {len(all_assets)} assets, ${total_portfolio_value:,.2f} total value")
        
    except Exception as e:
        print(f"Error updating portfolio: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
