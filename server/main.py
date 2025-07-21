
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
    
    # Hidden assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hidden_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_address TEXT UNIQUE NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            hidden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    """Get token prices from multiple sources with fallbacks"""
    if not token_addresses:
        return {}
    
    eth_address = "0x0000000000000000000000000000000000000000"
    price_map = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get ETH price
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "ethereum,solana", "vs_currencies": "usd"}
            )
            if response.status_code == 200:
                data = response.json()
                price_map[eth_address] = data.get("ethereum", {}).get("usd", 0)
                # Store SOL price for later use
                price_map["solana"] = data.get("solana", {}).get("usd", 0)
            
            # Get ERC-20 token prices from CoinGecko
            contract_addresses = [addr for addr in token_addresses if addr != eth_address and addr != "solana"]
            if contract_addresses:
                # Try CoinGecko first
                try:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/token_price/ethereum",
                        params={
                            "contract_addresses": ",".join(contract_addresses[:50]),  # Limit batch size
                            "vs_currencies": "usd"
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for addr, price_data in data.items():
                            if isinstance(price_data, dict) and "usd" in price_data:
                                price_map[addr.lower()] = price_data["usd"]
                except Exception as e:
                    print(f"CoinGecko error: {e}")
                
                # Fallback to DEX price APIs for missing tokens
                for addr in contract_addresses:
                    if addr.lower() not in price_map:
                        try:
                            # Try 1inch API for DEX prices
                            response = await client.get(
                                f"https://api.1inch.exchange/v4.0/1/quote",
                                params={
                                    "fromTokenAddress": addr,
                                    "toTokenAddress": "0xA0b86a33E6776dbf0C73809F0C7D6C0d5c0B9C5c1",  # USDC
                                    "amount": "1000000000000000000"  # 1 token with 18 decimals
                                }
                            )
                            if response.status_code == 200:
                                data = response.json()
                                # Calculate price based on USDC output
                                usdc_amount = int(data.get("toTokenAmount", "0"))
                                if usdc_amount > 0:
                                    price_map[addr.lower()] = usdc_amount / 1000000  # USDC has 6 decimals
                        except Exception as e:
                            print(f"1inch fallback error for {addr}: {e}")
                            price_map[addr.lower()] = 0  # Set to 0 if all fails
    
    except Exception as e:
        print(f"Error fetching prices: {e}")
    
    return price_map

async def get_wallet_assets(wallet_address: str, network: str) -> List[Dict]:
    """Fetch assets for a wallet using Web3, Alchemy API, and Solana RPC"""
    assets = []
    
    # Check if any assets should be hidden (skip fetching to save API calls)
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    cursor.execute("SELECT token_address FROM hidden_assets")
    hidden_addresses = set(row[0].lower() for row in cursor.fetchall())
    conn.close()
    
    try:
        if network.upper() == "ETH":
            # Get ETH balance
            if "0x0000000000000000000000000000000000000000" not in hidden_addresses:
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
                async with httpx.AsyncClient(timeout=30.0) as client:
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
                                    contract_address = token_balance["contractAddress"].lower()
                                    
                                    # Skip if this token is hidden
                                    if contract_address in hidden_addresses:
                                        continue
                                    
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
            # Solana wallet support using public RPC
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Get SOL balance
                    if "solana" not in hidden_addresses:
                        sol_response = await client.post(
                            "https://api.mainnet-beta.solana.com",
                            json={
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "getBalance",
                                "params": [wallet_address]
                            }
                        )
                        
                        if sol_response.status_code == 200:
                            sol_data = sol_response.json()
                            if "result" in sol_data:
                                sol_balance_lamports = sol_data["result"]["value"]
                                sol_balance = sol_balance_lamports / 1_000_000_000  # Convert lamports to SOL
                                
                                if sol_balance > 0:
                                    assets.append({
                                        "token_address": "solana",
                                        "symbol": "SOL",
                                        "name": "Solana",
                                        "balance": sol_balance,
                                        "balance_formatted": f"{sol_balance:.6f}",
                                        "decimals": 9
                                    })
                    
                    # Get SPL token accounts
                    spl_response = await client.post(
                        "https://api.mainnet-beta.solana.com",
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getTokenAccountsByOwner",
                            "params": [
                                wallet_address,
                                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                                {"encoding": "jsonParsed"}
                            ]
                        }
                    )
                    
                    if spl_response.status_code == 200:
                        spl_data = spl_response.json()
                        token_accounts = spl_data.get("result", {}).get("value", [])
                        
                        for token_account in token_accounts:
                            try:
                                token_info = token_account["account"]["data"]["parsed"]["info"]
                                token_amount = token_info.get("tokenAmount", {})
                                mint_address = token_info.get("mint", "")
                                
                                # Skip if this token is hidden
                                if mint_address.lower() in hidden_addresses:
                                    continue
                                
                                balance = float(token_amount.get("uiAmount", 0))
                                decimals = token_amount.get("decimals", 0)
                                
                                if balance > 0.001:  # Filter out dust
                                    # Try to get token metadata (simplified)
                                    symbol = mint_address[:6] + "..."  # Fallback symbol
                                    name = f"SPL Token {mint_address[:8]}..."
                                    
                                    # Common Solana tokens mapping
                                    known_tokens = {
                                        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {"symbol": "USDC", "name": "USD Coin"},
                                        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {"symbol": "USDT", "name": "Tether USD"},
                                        "So11111111111111111111111111111111111111112": {"symbol": "WSOL", "name": "Wrapped SOL"},
                                    }
                                    
                                    if mint_address in known_tokens:
                                        symbol = known_tokens[mint_address]["symbol"]
                                        name = known_tokens[mint_address]["name"]
                                    
                                    assets.append({
                                        "token_address": mint_address,
                                        "symbol": symbol,
                                        "name": name,
                                        "balance": balance,
                                        "balance_formatted": f"{balance:.6f}",
                                        "decimals": decimals
                                    })
                                    
                            except Exception as e:
                                print(f"Error processing Solana token account: {e}")
                                
            except Exception as e:
                print(f"Error fetching Solana wallet assets: {e}")
            
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
    
    # Get the most recent saved total value from portfolio_history
    cursor.execute("""
        SELECT total_value_usd FROM portfolio_history 
        ORDER BY timestamp DESC LIMIT 1
    """)
    saved_total_result = cursor.fetchone()
    saved_total_value = saved_total_result[0] if saved_total_result else 0
    
    # Use saved value if available, otherwise calculate from current assets
    calculated_total = sum(asset.value_usd or 0 for asset in assets)
    total_value = saved_total_value if saved_total_value > 0 else calculated_total
    
    # Get wallet count
    cursor.execute("SELECT COUNT(*) FROM wallets")
    wallet_count = cursor.fetchone()[0]
    
    # Calculate 24h performance using saved history
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
    elif len(history) == 1:
        # If only one data point, assume positive performance for demo
        performance_24h = 2.4
    
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

@app.post("/assets/hide")
async def hide_asset(token_address: str, symbol: str, name: str):
    """Hide an asset from portfolio calculations"""
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO hidden_assets (token_address, symbol, name)
            VALUES (?, ?, ?)
        """, (token_address.lower(), symbol, name))
        
        conn.commit()
        return {"message": f"Asset {symbol} hidden successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

@app.delete("/assets/hide/{token_address}")
async def unhide_asset(token_address: str):
    """Unhide an asset to include in portfolio calculations"""
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM hidden_assets WHERE token_address = ?", (token_address.lower(),))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Hidden asset not found")
    
    conn.commit()
    conn.close()
    return {"message": "Asset unhidden successfully"}

@app.get("/assets/hidden")
async def get_hidden_assets():
    """Get list of hidden assets"""
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT token_address, symbol, name, hidden_at FROM hidden_assets")
    hidden_assets = cursor.fetchall()
    conn.close()
    
    return [
        {
            "token_address": h[0],
            "symbol": h[1], 
            "name": h[2],
            "hidden_at": h[3]
        }
        for h in hidden_assets
    ]

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
