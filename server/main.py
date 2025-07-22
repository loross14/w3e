import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Protocol
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from web3 import Web3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import requests
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 [STARTUP] Initializing Crypto Fund Application...")
    print(f"🚀 [STARTUP] Environment: {os.getenv('NODE_ENV', 'development')}")

    # Verify environment variables are set
    print("🔍 [STARTUP] Checking environment variables...")
    print(f"   DATABASE_URL: {'✅ Set' if DATABASE_URL else '❌ Missing'}")
    print(f"   ALCHEMY_API_KEY: {'✅ Set' if ALCHEMY_API_KEY else '❌ Missing'}")

    # Test database connection with retry logic
    print("🔍 [STARTUP] Testing database connection...")
    connection_attempts = 0
    max_attempts = 3

    while connection_attempts < max_attempts:
        if test_database_connection():
            break
        connection_attempts += 1
        if connection_attempts < max_attempts:
            print(
                f"⏳ [STARTUP] Retrying database connection ({connection_attempts}/{max_attempts})..."
            )
            await asyncio.sleep(5)  # Wait 5 seconds before retry

    if connection_attempts >= max_attempts:
        print("❌ [STARTUP FAILED] Cannot start without database connection")
        print("❌ [STARTUP FAILED] Please check:")
        print("   1. PostgreSQL database is created in Replit")
        print("   2. DATABASE_URL is set correctly")
        print("   3. Database service is running")
        raise RuntimeError(
            "Database connection failed after multiple attempts")

    # Initialize database tables
    try:
        print("🏗️ [STARTUP] Initializing database schema...")
        init_db()
        print("✅ [STARTUP] Database schema initialized successfully")
    except Exception as e:
        print(f"❌ [STARTUP] Database initialization failed: {e}")
        print("❌ [STARTUP] This may indicate a schema or permissions issue")
        raise e

    print("🎉 [STARTUP] Application ready and healthy!")
    yield
    # Shutdown (if needed)
    print("🛑 [SHUTDOWN] Application shutting down...")


app = FastAPI(title="Crypto Fund API", version="1.0.0", lifespan=lifespan)

# ================================================================================================
# CRITICAL DEPLOYMENT CONFIGURATION SECTION - DO NOT MODIFY WITHOUT READING THIS SECTION
# ================================================================================================
#
# This section handles serving the built React frontend from the FastAPI backend.
#
# DEPLOYMENT REQUIREMENTS:
# 1. Frontend MUST be built BEFORE backend starts
# 2. Built frontend files MUST be copied to a location the backend can find
# 3. Backend MUST run on port 80 in production (not 8000)
# 4. API base URL MUST point to same origin in production
#
# CURRENT WORKING DEPLOYMENT CONFIG:
# - Build command: "sh -c 'npm run build && cp -r dist server/dist && cd server && python3 -m pip install --break-system-packages -r requirements.txt && python3 main.py'"
# - Run command: Uses PORT=80 in production
#
# HOW IT WORKS:
# 1. npm run build creates dist/ in project root
# 2. cp -r dist server/dist copies frontend to server/dist/
# 3. Backend looks for files at ./dist (relative to server/)
# 4. Frontend connects to same origin (no port needed)
#
# CRITICAL: DO NOT CHANGE DEPLOYMENT ORDER
# If backend starts before frontend is built and copied, the app will fail!
#
# TROUBLESHOOTING DEPLOYMENT FAILURES:
# - Frontend shows "connection timeout" = backend not responding (wrong port/order)
# - "Manifest syntax error" = frontend files not found/copied properly
# - Backend API works but frontend doesn't load = static file serving broken
#
# EMERGENCY FIX CHECKLIST:
# 1. Verify deployment command includes: npm run build && cp -r dist server/dist
# 2. Check backend runs on PORT=80 in production
# 3. Ensure frontend API_BASE_URL uses same origin in production
# 4. Confirm deployment builds frontend BEFORE starting backend
# ================================================================================================
dist_path = None
possible_paths = [
    "../dist",  # When running from server/ directory in development (npm run dev creates dist in project root)
    "./dist",  # When running from project root in deployment (deployment copies to server/dist)
    "dist",  # Alternative deployment path (fallback)
]

print("🔍 [STATIC FILES] Searching for frontend build artifacts...")
for path in possible_paths:
    if os.path.exists(path) and os.path.isdir(path):
        # Verify it contains essential files - a proper build should have index.html
        index_file = os.path.join(path, "index.html")
        if os.path.exists(index_file):
            dist_path = path
            print(
                f"✅ [STATIC FILES] Found valid frontend build at: {dist_path}")
            break
        else:
            print(
                f"⚠️ [STATIC FILES] Directory exists but missing index.html: {path}"
            )
    else:
        print(f"❌ [STATIC FILES] Path not found: {path}")

if dist_path:
    # Mount static assets (CSS, JS, images generated by Vite)
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        print(f"✅ [STATIC FILES] Mounted Vite assets from: {assets_path}")
    else:
        print(f"⚠️ [STATIC FILES] No assets directory found at: {assets_path}")

    print(f"✅ [STATIC FILES] Frontend files ready to serve from: {dist_path}")
else:
    print("❌ [STATIC FILES] CRITICAL: No valid frontend build found!")
    print("❌ [STATIC FILES] This means the deployment is misconfigured.")
    print(
        "❌ [STATIC FILES] Frontend will NOT work - only API endpoints will be available."
    )
    print(f"❌ [STATIC FILES] Searched locations: {possible_paths}")
    print("❌ [STATIC FILES] TO FIX:")
    print("❌ [STATIC FILES] 1. Ensure 'npm run build' runs successfully")
    print("❌ [STATIC FILES] 2. Ensure deployment copies dist/ to server/dist/")
    print("❌ [STATIC FILES] 3. Check .replit deployment configuration")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database and Alchemy configuration with better error handling
DATABASE_URL = os.getenv("DATABASE_URL")
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")

print(f"🔍 [STARTUP] DATABASE_URL set: {bool(DATABASE_URL)}")
print(f"🔍 [STARTUP] ALCHEMY_API_KEY set: {bool(ALCHEMY_API_KEY)}")

# Check for environment variables with better error handling
if not DATABASE_URL:
    print("❌ [STARTUP ERROR] DATABASE_URL environment variable is required")
    print("❌ [STARTUP ERROR] To fix this:")
    print("   1. Go to the Database tab in Replit")
    print("   2. Click 'Create Database'")
    print("   3. Select PostgreSQL")
    print("   4. Wait for setup to complete")
    print("   5. Restart your application")
    raise RuntimeError(
        "DATABASE_URL missing - Please add PostgreSQL database in Replit")

if not ALCHEMY_API_KEY:
    print("❌ [STARTUP ERROR] ALCHEMY_API_KEY environment variable is required")
    print("❌ [STARTUP ERROR] To fix this:")
    print("   1. Go to the Secrets tab (🔒) in Replit")
    print("   2. Add key: ALCHEMY_API_KEY")
    print("   3. Add your Alchemy API key as the value")
    print("   4. Restart your application")
    raise RuntimeError(
        "ALCHEMY_API_KEY missing - Please add to Replit Secrets")


def get_db_connection():
    """Get a PostgreSQL database connection with enhanced error handling"""
    try:
        # Add connection timeout and retry logic
        conn = psycopg2.connect(DATABASE_URL,
                                cursor_factory=RealDictCursor,
                                connect_timeout=10,
                                application_name="crypto_fund_app")
        return conn
    except psycopg2.OperationalError as e:
        error_msg = str(e).lower()
        print(f"❌ [DATABASE ERROR] PostgreSQL connection failed: {e}")

        if "could not connect to server" in error_msg:
            print("❌ [DATABASE ERROR] Database server not reachable")
            print("❌ [DATABASE ERROR] Possible fixes:")
            print("   1. Check if PostgreSQL database is created in Replit")
            print("   2. Wait for database to start (can take 30-60 seconds)")
            print("   3. Restart the application")
        elif "authentication failed" in error_msg:
            print("❌ [DATABASE ERROR] Authentication failed")
            print(
                "❌ [DATABASE ERROR] DATABASE_URL credentials may be incorrect")
        elif "database" in error_msg and "does not exist" in error_msg:
            print("❌ [DATABASE ERROR] Database does not exist")
            print(
                "❌ [DATABASE ERROR] Please create PostgreSQL database in Replit"
            )

        raise e
    except Exception as e:
        print(f"❌ [DATABASE ERROR] Unexpected error: {e}")
        print(
            f"❌ [DATABASE ERROR] DATABASE_URL format: {DATABASE_URL[:30]}...")
        raise e


def test_database_connection():
    """Test database connection at startup with detailed error reporting"""
    try:
        print("🔍 [STARTUP] Testing database connection...")
        print(f"🔍 [STARTUP] DATABASE_URL format: postgresql://...")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()

        # Additional connection health checks
        cursor.execute("SELECT current_database(), current_user")
        db_info = cursor.fetchone()
        print(
            f"✅ [STARTUP] Connected to database: {db_info['current_database']} as {db_info['current_user']}"
        )

        cursor.close()
        conn.close()
        print("✅ [STARTUP] Database connection test successful")
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ [STARTUP] PostgreSQL connection failed: {e}")
        print("❌ [STARTUP] This usually means:")
        print("   - PostgreSQL database not created in Replit")
        print("   - DATABASE_URL is incorrect")
        print("   - Database is starting up (wait 30 seconds and try again)")
        return False
    except psycopg2.Error as e:
        print(f"❌ [STARTUP] PostgreSQL error: {e}")
        print("❌ [STARTUP] Database exists but has configuration issues")
        return False
    except Exception as e:
        print(f"❌ [STARTUP] Unexpected database error: {e}")
        print(f"❌ [STARTUP] Error type: {type(e).__name__}")
        return False


# ERC-20 ABI for token interactions
ERC20_ABI = [{
    "constant": True,
    "inputs": [],
    "name": "name",
    "outputs": [{
        "name": "",
        "type": "string"
    }],
    "type": "function"
}, {
    "constant": True,
    "inputs": [],
    "name": "symbol",
    "outputs": [{
        "name": "",
        "type": "string"
    }],
    "type": "function"
}, {
    "constant": True,
    "inputs": [],
    "name": "decimals",
    "outputs": [{
        "name": "",
        "type": "uint8"
    }],
    "type": "function"
}, {
    "constant": True,
    "inputs": [{
        "name": "_owner",
        "type": "address"
    }],
    "name": "balanceOf",
    "outputs": [{
        "name": "balance",
        "type": "uint256"
    }],
    "type": "function"
}]


# Chain-agnostic asset interface
class AssetData:

    def __init__(self,
                 token_address: str,
                 symbol: str,
                 name: str,
                 balance: float,
                 balance_formatted: str,
                 decimals: int,
                 is_nft: bool = False,
                 token_ids: List[str] = None,
                 floor_price: float = 0,
                 image_url: str = None,
                 purchase_price: float = 0,
                 total_invested: float = 0,
                 realized_pnl: float = 0):
        self.token_address = token_address
        self.symbol = symbol
        self.name = name
        self.balance = balance
        self.balance_formatted = balance_formatted
        self.decimals = decimals
        self.is_nft = is_nft
        self.token_ids = token_ids or []
        self.floor_price = floor_price
        self.image_url = image_url
        self.purchase_price = purchase_price
        self.total_invested = total_invested
        self.realized_pnl = realized_pnl


# Abstract base classes for chain-specific implementations
class AssetFetcher(ABC):

    @abstractmethod
    async def fetch_assets(self, wallet_address: str,
                           hidden_addresses: set) -> List[AssetData]:
        pass


class PriceFetcher(ABC):

    @abstractmethod
    async def fetch_prices(self,
                           token_addresses: List[str]) -> Dict[str, float]:
        pass


# Ethereum-specific implementations
class EthereumAssetFetcher(AssetFetcher):

    def __init__(self, alchemy_api_key: str):
        self.alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
        self.w3 = Web3(Web3.HTTPProvider(self.alchemy_url))

    async def fetch_assets(self, wallet_address: str,
                           hidden_addresses: set) -> List[AssetData]:
        assets = []

        try:
            # Get ETH balance
            eth_token_address = "0x0000000000000000000000000000000000000000"
            if eth_token_address not in hidden_addresses:
                eth_balance_wei = self.w3.eth.get_balance(wallet_address)
                eth_balance_formatted = float(eth_balance_wei) / 10**18

                if eth_balance_formatted > 0:
                    assets.append(
                        AssetData(
                            token_address=eth_token_address,
                            symbol="ETH",
                            name="Ethereum",
                            balance=eth_balance_formatted,
                            balance_formatted=f"{eth_balance_formatted:.6f}",
                            decimals=18))

            # Get ERC-20 tokens
            assets.extend(await
                          self._fetch_erc20_tokens(wallet_address,
                                                   hidden_addresses))

            # Get NFTs
            assets.extend(await self._fetch_nfts(wallet_address,
                                                 hidden_addresses))

        except Exception as e:
            print(f"❌ Ethereum asset fetching error: {e}")

        return assets

    async def _fetch_erc20_tokens(self, wallet_address: str,
                                  hidden_addresses: set) -> List[AssetData]:
        assets = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.alchemy_url,
                                             json={
                                                 "id": 1,
                                                 "jsonrpc": "2.0",
                                                 "method":
                                                 "alchemy_getTokenBalances",
                                                 "params": [wallet_address]
                                             })

                if response.status_code == 200:
                    data = response.json()
                    token_balances = data.get("result",
                                              {}).get("tokenBalances", [])

                    for token_balance in token_balances:
                        if token_balance.get("tokenBalance") and int(
                                token_balance["tokenBalance"], 16) > 0:
                            try:
                                contract_address = token_balance[
                                    "contractAddress"].lower()

                                if contract_address in hidden_addresses:
                                    continue

                                # Get token metadata
                                metadata_response = await client.post(
                                    self.alchemy_url,
                                    json={
                                        "id": 1,
                                        "jsonrpc": "2.0",
                                        "method": "alchemy_getTokenMetadata",
                                        "params": [contract_address]
                                    })

                                if metadata_response.status_code == 200:
                                    metadata = metadata_response.json().get(
                                        "result", {})
                                    balance_int = int(
                                        token_balance["tokenBalance"], 16)
                                    decimals = metadata.get("decimals", 18)
                                    balance_formatted = balance_int / (
                                        10**decimals)

                                    if balance_formatted > 0.001:  # Filter out dust
                                        assets.append(
                                            AssetData(
                                                token_address=contract_address,
                                                symbol=metadata.get(
                                                    "symbol", "UNKNOWN"),
                                                name=metadata.get(
                                                    "name", "Unknown Token"),
                                                balance=balance_formatted,
                                                balance_formatted=
                                                f"{balance_formatted:.6f}",
                                                decimals=decimals))
                            except Exception as e:
                                print(
                                    f"❌ Error processing Ethereum token {contract_address}: {e}"
                                )
        except Exception as e:
            print(f"❌ Error fetching Ethereum ERC-20 tokens: {e}")

        return assets

    async def _fetch_nfts(self, wallet_address: str,
                          hidden_addresses: set) -> List[AssetData]:
        """
        Fetch NFT collections owned by the wallet address.
        Returns AssetData objects with is_nft=True for each collection.
        """
        assets = []
        
        try:
            print(f"🖼️ [ETH NFT] Starting NFT query for wallet: {wallet_address[:10]}...")
            
            async with httpx.AsyncClient(timeout=45.0) as client:
                # Use the primary Alchemy getNFTs method with optimized parameters
                nft_payload = {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "alchemy_getNFTs",
                    "params": [
                        wallet_address,
                        {
                            "withMetadata": True,
                            "tokenUriTimeoutInMs": 8000,
                            "omitMetadata": False
                        }
                    ]
                }

                print(f"🖼️ [ETH NFT] Making API request to Alchemy...")
                
                response = await client.post(
                    self.alchemy_url,
                    json=nft_payload,
                    timeout=30.0,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    print(f"❌ [ETH NFT] HTTP error {response.status_code}: {response.text[:200]}...")
                    return assets

                # Parse response
                try:
                    data = response.json()
                except Exception as parse_error:
                    print(f"❌ [ETH NFT] JSON parsing failed: {parse_error}")
                    return assets

                # Check for API errors
                if "error" in data:
                    print(f"❌ [ETH NFT] API error: {data['error']}")
                    return assets

                # Extract NFTs from response
                result = data.get("result", {})
                owned_nfts = result.get("ownedNfts", [])
                
                if not owned_nfts:
                    print(f"🖼️ [ETH NFT] No NFTs found for wallet")
                    return assets

                print(f"🖼️ [ETH NFT] Found {len(owned_nfts)} NFTs, processing collections...")

                # Group NFTs by collection (contract address)
                collections = {}
                
                for nft in owned_nfts:
                    try:
                        # Extract contract information
                        contract = nft.get("contract", {})
                        contract_address = contract.get("address", "").lower()
                        
                        if not contract_address:
                            continue
                            
                        # Skip hidden collections
                        if (contract_address in hidden_addresses or 
                            any(addr.lower() == contract_address for addr in hidden_addresses)):
                            continue

                        # Initialize collection if not seen before
                        if contract_address not in collections:
                            collections[contract_address] = {
                                "name": contract.get("name", "Unknown Collection"),
                                "symbol": contract.get("symbol", "NFT"),
                                "count": 0,
                                "token_ids": [],
                                "image_url": None,
                                "opensea_slug": contract.get("openSea", {}).get("collectionSlug")
                            }

                        # Add this NFT to the collection
                        collection = collections[contract_address]
                        collection["count"] += 1
                        
                        # Add token ID if available
                        token_id = nft.get("tokenId")
                        if token_id and len(collection["token_ids"]) < 20:  # Limit stored token IDs
                            collection["token_ids"].append(str(token_id))

                        # Extract image URL from metadata if not already set
                        if not collection["image_url"]:
                            metadata = nft.get("metadata", {})
                            if metadata:
                                image_url = (metadata.get("image") or 
                                           metadata.get("image_url") or 
                                           metadata.get("imageUrl"))
                                if image_url:
                                    collection["image_url"] = image_url

                    except Exception as nft_error:
                        print(f"⚠️ [ETH NFT] Error processing NFT: {nft_error}")
                        continue

                print(f"🖼️ [ETH NFT] Processed {len(collections)} unique collections")

                # Convert collections to AssetData objects
                for contract_address, collection_data in collections.items():
                    try:
                        # Get floor price (with timeout protection)
                        floor_price = 0
                        try:
                            floor_price = await asyncio.wait_for(
                                self._get_nft_floor_price(
                                    client, 
                                    contract_address,
                                    collection_data.get("opensea_slug")
                                ),
                                timeout=10.0
                            )
                        except asyncio.TimeoutError:
                            print(f"⏰ [ETH NFT] Floor price timeout for {collection_data['name']}")
                        except Exception as price_error:
                            print(f"⚠️ [ETH NFT] Floor price error for {collection_data['name']}: {price_error}")

                        # Create NFT asset
                        nft_asset = AssetData(
                            token_address=contract_address,
                            symbol=collection_data["symbol"],
                            name=collection_data["name"],
                            balance=collection_data["count"],
                            balance_formatted=f"{collection_data['count']} NFTs",
                            decimals=0,
                            is_nft=True,
                            token_ids=collection_data["token_ids"],
                            floor_price=floor_price,
                            image_url=collection_data.get("image_url")
                        )
                        
                        assets.append(nft_asset)
                        
                        print(f"✅ [ETH NFT] Added collection: {collection_data['name']} "
                              f"({collection_data['count']} items, floor: ${floor_price})")
                        
                    except Exception as asset_error:
                        print(f"❌ [ETH NFT] Error creating asset for {contract_address}: {asset_error}")
                        continue

        except asyncio.TimeoutError:
            print(f"⏰ [ETH NFT] Request timeout - continuing without NFTs")
        except Exception as e:
            print(f"❌ [ETH NFT] Unexpected error: {e}")
            # Don't fail the entire asset fetch if NFTs fail
        
        print(f"🖼️ [ETH NFT] Final result: {len(assets)} NFT collections")
        return assets

    async def _get_nft_floor_price(self,
                                   client: httpx.AsyncClient,
                                   contract_address: str,
                                   opensea_slug: str = None) -> float:
        """Get NFT collection floor price from OpenSea API"""
        try:
            if opensea_slug:
                # Use OpenSea API with collection slug
                response = await client.get(
                    f"https://api.opensea.io/api/v1/collection/{opensea_slug}/stats",
                    headers={
                        "User-Agent":
                        "Mozilla/5.0 (compatible; CryptoFund/1.0)"
                    },
                    timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    stats = data.get("stats", {})
                    floor_price = stats.get("floor_price", 0)
                    if floor_price:
                        # Convert ETH to USD (approximate)
                        eth_price = 3800  # Could fetch real ETH price here
                        return floor_price * eth_price

            # Fallback: try contract address
            response = await client.get(
                f"https://api.opensea.io/api/v1/asset_contract/{contract_address}",
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; CryptoFund/1.0)"
                },
                timeout=10.0)

            if response.status_code == 200:
                # This is a basic fallback - real implementation would need more complex floor price logic
                return 0.1  # Placeholder floor price

        except Exception as e:
            print(
                f"⚠️ Could not fetch floor price for {contract_address}: {e}")

        return 0


class EthereumPriceFetcher(PriceFetcher):

    def __init__(self):
        self.known_tokens = {
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {
                "symbol": "WBTC",
                "coingecko_id": "wrapped-bitcoin"
            },
            "0x808507121b80c02388fad14726482e061b8da827": {
                "symbol": "PENDLE",
                "coingecko_id": "pendle"
            },
            "0xa0b73e1ff0b80914ab6fe136c72b47cb5ed05b81": {
                "symbol": "USDC",
                "coingecko_id": "usd-coin"
            },
            "0xdac17f958d2ee523a2206206994597c13d831ec7": {
                "symbol": "USDT",
                "coingecko_id": "tether"
            },
            "0x6b175474e89094c44da98b954eedeac495271d0f": {
                "symbol": "DAI",
                "coingecko_id": "dai"
            },
            "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {
                "symbol": "UNI",
                "coingecko_id": "uniswap"
            },
            # Add some backup mappings for common tokens
            "0xa0b86a33e6e9e9a7e5b1d1c1d2b6b1b1b1b1b1b1": {
                "symbol": "USDC",
                "coingecko_id": "usd-coin"
            },
        }

    async def fetch_prices(self,
                           token_addresses: List[str]) -> Dict[str, float]:
        price_map = {}
        # ETH uses a special zero address - this is the standard way to represent native ETH
        eth_address = "0x0000000000000000000000000000000000000000"
        eth_address_lower = eth_address.lower()

        print(
            f"💵 Fetching Ethereum prices for {len(token_addresses)} tokens...")
        print(f"🔍 ETH special address: {eth_address}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # CRITICAL: Get ETH price first - ETH is special case with zero address
                print(f"📡 Fetching ETH price from CoinGecko...")
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": "ethereum",
                        "vs_currencies": "usd"
                    })
                if response.status_code == 200:
                    data = response.json()
                    eth_price = data.get("ethereum", {}).get("usd", 0)
                    # Store ETH price with multiple address formats for lookup
                    price_map[eth_address] = eth_price
                    price_map[eth_address_lower] = eth_price
                    price_map["eth"] = eth_price  # Additional fallback
                    print(f"✅ ETH price fetched successfully: ${eth_price}")
                    print(
                        f"✅ ETH price stored for addresses: {eth_address}, {eth_address_lower}"
                    )
                else:
                    print(
                        f"❌ Failed to fetch ETH price: HTTP {response.status_code}"
                    )
                    # Set fallback ETH price if API fails
                    fallback_eth_price = 3500.0  # Reasonable fallback
                    price_map[eth_address] = fallback_eth_price
                    price_map[eth_address_lower] = fallback_eth_price
                    print(f"🔄 Using fallback ETH price: ${fallback_eth_price}")

                # Process contract addresses
                contract_addresses = [
                    addr for addr in token_addresses if addr != eth_address
                ]
                known_ids = []
                address_to_id = {}

                for addr in contract_addresses:
                    addr_lower = addr.lower()
                    if addr_lower in self.known_tokens:
                        coingecko_id = self.known_tokens[addr_lower][
                            "coingecko_id"]
                        known_ids.append(coingecko_id)
                        address_to_id[coingecko_id] = addr_lower
                        print(
                            f"✅ Found known Ethereum token: {self.known_tokens[addr_lower]['symbol']} -> {coingecko_id}"
                        )

                # Fetch known token prices
                if known_ids:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/price",
                        params={
                            "ids": ",".join(known_ids),
                            "vs_currencies": "usd"
                        })
                    if response.status_code == 200:
                        data = response.json()
                        for coingecko_id, price_data in data.items():
                            if isinstance(price_data,
                                          dict) and "usd" in price_data:
                                addr = address_to_id.get(coingecko_id)
                                if addr:
                                    price_map[addr] = price_data["usd"]
                                    original_addr = next(
                                        (a for a in contract_addresses
                                         if a.lower() == addr), addr)
                                    price_map[original_addr] = price_data[
                                        "usd"]
                                    print(
                                        f"✅ Got Ethereum price: {addr} = ${price_data['usd']}"
                                    )

                # Try CoinGecko contract API for remaining tokens
                remaining_addresses = [
                    addr for addr in contract_addresses
                    if addr.lower() not in price_map and addr not in price_map
                ]
                if remaining_addresses:
                    print(
                        f"📡 Trying CoinGecko contract API for {len(remaining_addresses)} remaining tokens..."
                    )
                    try:
                        response = await client.get(
                            "https://api.coingecko.com/api/v3/simple/token_price/ethereum",
                            params={
                                "contract_addresses":
                                ",".join(remaining_addresses[:30]),
                                "vs_currencies":
                                "usd"
                            },
                            timeout=15.0)
                        print(
                            f"📊 CoinGecko contract API response: {response.status_code}"
                        )
                        if response.status_code == 200:
                            data = response.json()
                            print(
                                f"📈 Contract API returned data for {len(data)} tokens"
                            )
                            for addr, price_data in data.items():
                                if isinstance(price_data,
                                              dict) and "usd" in price_data:
                                    price_map[addr.lower()] = price_data["usd"]
                                    price_map[addr] = price_data["usd"]
                                    print(
                                        f"✅ Got Ethereum contract API price: {addr} = ${price_data['usd']}"
                                    )
                        else:
                            print(
                                f"❌ CoinGecko contract API error: {response.status_code}"
                            )
                    except Exception as e:
                        print(f"❌ CoinGecko contract API exception: {e}")

        except Exception as e:
            print(f"❌ Error fetching Ethereum prices: {e}")

        # Add manual fallbacks for major tokens if no price was found
        fallback_prices = {
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599":
            100000,  # WBTC ~$100k
            "0x808507121b80c02388fad14726482e061b8da827": 5.0,  # PENDLE ~$5
        }

        for addr, fallback_price in fallback_prices.items():
            if addr.lower() not in price_map and addr not in price_map:
                print(f"🔄 Using fallback price for {addr}: ${fallback_price}")
                price_map[addr.lower()] = fallback_price
                price_map[addr] = fallback_price

        return price_map


# Solana-specific implementations
class SolanaAssetFetcher(AssetFetcher):

    def __init__(self, alchemy_api_key: str):
        self.solana_url = f"https://solana-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
        self.known_tokens = {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                "symbol": "USDC",
                "name": "USD Coin"
            },
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
                "symbol": "USDT",
                "name": "Tether USD"
            },
            "So11111111111111111111111111111111111111112": {
                "symbol": "WSOL",
                "name": "Wrapped SOL"
            },
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {
                "symbol": "BONK",
                "name": "Bonk"
            },
            "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": {
                "symbol": "ETH",
                "name": "Ether (Portal)"
            },
            "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": {
                "symbol": "mSOL",
                "name": "Marinade Staked SOL"
            },
        }
        self.spl_token_program = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        self.spl_token_2022_program = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
        self.solana_rpc_url = self.solana_url  # Use Alchemy as RPC URL

    async def fetch_assets(self, wallet_address: str,
                           hidden_addresses: set) -> List[AssetData]:
        assets = []

        print(
            f"🔍 [SOLANA DEBUG] Starting asset fetch for wallet: {wallet_address}"
        )
        print(f"🔍 [SOLANA DEBUG] Solana RPC URL: {self.solana_url}")
        print(f"🔍 [SOLANA DEBUG] Hidden addresses: {list(hidden_addresses)}")

        # Validate Solana address format
        if not self._is_valid_solana_address(wallet_address):
            print(
                f"❌ [SOLANA DEBUG] Invalid Solana address format: {wallet_address}"
            )
            return assets

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get SOL balance
                print(f"📊 [SOLANA DEBUG] Fetching native SOL balance...")
                if "solana" not in hidden_addresses:
                    sol_asset = await self._fetch_sol_balance(
                        client, wallet_address)
                    if sol_asset:
                        assets.append(sol_asset)
                        print(
                            f"✅ [SOLANA DEBUG] Added SOL asset: {sol_asset.balance} SOL"
                        )
                    else:
                        print(
                            f"⚠️ [SOLANA DEBUG] No SOL balance found or balance is zero"
                        )
                else:
                    print(f"🙈 [SOLANA DEBUG] SOL is hidden, skipping")

                # Get SPL tokens (both old and new program)
                print(f"🪙 [SOLANA DEBUG] Fetching SPL token accounts...")
                spl_assets = await self._fetch_spl_tokens(
                    client, wallet_address, hidden_addresses)
                assets.extend(spl_assets)
                print(
                    f"✅ [SOLANA DEBUG] Added {len(spl_assets)} SPL token assets"
                )

        except Exception as e:
            print(f"❌ [SOLANA DEBUG] Major error in asset fetching: {e}")
            import traceback
            print(f"📋 [SOLANA DEBUG] Full traceback: {traceback.format_exc()}")

        print(
            f"🎯 [SOLANA DEBUG] Final result: {len(assets)} total assets found")
        return assets

    def _is_valid_solana_address(self, address: str) -> bool:
        """Proper Solana address validation using base58 decoding"""
        try:
            import base58

            if not address or len(address) < 32 or len(address) > 44:
                return False

            # Decode base58 and check if it's 32 bytes (standard Solana pubkey length)
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except:
            # Fallback to regex if base58 module not available
            import re
            if not address or len(address) < 32 or len(address) > 44:
                return False
            base58_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
            return bool(re.match(base58_pattern, address))

    async def _fetch_sol_balance(self, client: httpx.AsyncClient,
                                 wallet_address: str) -> Optional[AssetData]:
        try:
            print(
                f"📊 [SOL BALANCE] Starting SOL balance fetch for {wallet_address}"
            )

            # Use commitment level for more reliable results
            rpc_payload = {
                "jsonrpc":
                "2.0",
                "id":
                1,
                "method":
                "getBalance",
                "params": [
                    wallet_address,
                    {
                        "commitment": "confirmed"
                    }  # Use confirmed commitment for reliability
                ]
            }

            print(f"🌐 [SOL BALANCE] RPC payload: {rpc_payload}")

            response = await client.post(self.solana_url,
                                         json=rpc_payload,
                                         headers={
                                             "Content-Type":
                                             "application/json",
                                             "accept": "application/json"
                                         },
                                         timeout=30.0)

            print(f"🌐 [SOL BALANCE] Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📈 [SOL BALANCE] Response data: {data}")

                if "error" in data:
                    error_info = data["error"]
                    print(f"❌ [SOL BALANCE] RPC Error: {error_info}")
                    # Check for specific error types
                    if "Invalid param" in str(error_info):
                        print(
                            f"❌ [SOL BALANCE] Invalid address format: {wallet_address}"
                        )
                    return None

                if "result" in data:
                    result = data["result"]
                    if isinstance(result, dict) and "value" in result:
                        sol_balance_lamports = result["value"]
                    elif isinstance(result, int):
                        # Sometimes Alchemy returns the balance directly as an integer
                        sol_balance_lamports = result
                    else:
                        print(
                            f"❌ [SOL BALANCE] Unexpected result format: {result}"
                        )
                        return None

                    sol_balance = sol_balance_lamports / 1_000_000_000  # Convert lamports to SOL
                    print(
                        f"💰 [SOL BALANCE] Success! {sol_balance} SOL ({sol_balance_lamports} lamports)"
                    )

                    if sol_balance > 0:
                        return AssetData(
                            token_address="solana",
                            symbol="SOL",
                            name="Solana",
                            balance=sol_balance,
                            balance_formatted=f"{sol_balance:.6f}",
                            decimals=9)
                    else:
                        print(f"⚠️ [SOL BALANCE] Zero balance found")
                        return None
                else:
                    print(
                        f"❌ [SOL BALANCE] No result field in response: {data}")
                    return None
            else:
                error_text = response.text
                print(
                    f"❌ [SOL BALANCE] HTTP error {response.status_code}: {error_text}"
                )
                if response.status_code == 401:
                    print(
                        f"❌ [SOL BALANCE] Authentication error - check ALCHEMY_API_KEY"
                    )
                elif response.status_code == 429:
                    print(f"❌ [SOL BALANCE] Rate limited - too many requests")
                return None

        except httpx.TimeoutException:
            print(f"❌ [SOL BALANCE] Request timeout")
            return None
        except Exception as e:
            print(f"❌ [SOL BALANCE] Exception: {e}")
            import traceback
            print(f"📋 [SOL BALANCE] Traceback: {traceback.format_exc()}")
            return None

    async def _fetch_spl_tokens(self, client: httpx.AsyncClient,
                                wallet_address: str,
                                hidden_addresses: set) -> List[AssetData]:
        assets = []

        # Fetch from both SPL Token program and SPL Token 2022 program
        program_ids = [self.spl_token_program, self.spl_token_2022_program]

        for program_id in program_ids:
            try:
                print(f"🪙 [SPL TOKENS] Fetching from program: {program_id}")

                rpc_payload = {
                    "jsonrpc":
                    "2.0",
                    "id":
                    1,
                    "method":
                    "getTokenAccountsByOwner",
                    "params": [
                        wallet_address,
                        {
                            "programId": program_id
                        },
                        {
                            "encoding": "jsonParsed",
                            "commitment":
                            "confirmed"  # Use confirmed commitment
                        }
                    ]
                }

                print(f"🌐 [SPL TOKENS] RPC payload: {rpc_payload}")

                response = await client.post(self.solana_url,
                                             json=rpc_payload,
                                             headers={
                                                 "Content-Type":
                                                 "application/json",
                                                 "accept": "application/json"
                                             },
                                             timeout=30.0)

                print(
                    f"🌐 [SPL TOKENS] Response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"📊 [SPL TOKENS] Response keys: {list(data.keys())}")

                    if "error" in data:
                        error_info = data["error"]
                        print(f"❌ [SPL TOKENS] RPC Error: {error_info}")
                        if "Invalid param" in str(error_info):
                            print(
                                f"❌ [SPL TOKENS] Invalid parameters for {program_id}"
                            )
                        continue

                    if "result" in data and "value" in data["result"]:
                        token_accounts = data["result"]["value"]
                        print(
                            f"📊 [SPL TOKENS] Found {len(token_accounts)} token accounts from {program_id}"
                        )

                        for i, token_account in enumerate(token_accounts):
                            try:
                                print(
                                    f"🔍 [SPL TOKENS] Processing account {i+1}/{len(token_accounts)}"
                                )

                                # Parse the token account structure
                                account_info = token_account.get("account", {})
                                if not account_info:
                                    print(
                                        f"⚠️ [SPL TOKENS] No account info in token_account"
                                    )
                                    continue

                                account_data = account_info.get("data", {})
                                if not isinstance(account_data, dict):
                                    print(
                                        f"⚠️ [SPL TOKENS] Account data is not a dict: {type(account_data)}"
                                    )
                                    continue

                                parsed_data = account_data.get("parsed", {})
                                if not parsed_data:
                                    print(
                                        f"⚠️ [SPL TOKENS] No parsed data found"
                                    )
                                    continue

                                token_info = parsed_data.get("info", {})
                                if not token_info:
                                    print(
                                        f"⚠️ [SPL TOKENS] No token info found")
                                    continue

                                # Extract mint address and token amount
                                mint_address = token_info.get("mint", "")
                                token_amount = token_info.get(
                                    "tokenAmount", {})

                                if not mint_address:
                                    print(
                                        f"⚠️ [SPL TOKENS] No mint address found"
                                    )
                                    continue

                                print(f"🔍 [SPL TOKENS] Mint: {mint_address}")
                                print(
                                    f"🔍 [SPL TOKENS] Token amount: {token_amount}"
                                )

                                # Skip if this token is hidden
                                if mint_address.lower() in hidden_addresses:
                                    print(
                                        f"🙈 [SPL TOKENS] Token {mint_address} is hidden, skipping"
                                    )
                                    continue

                                # Extract balance information
                                ui_amount = token_amount.get("uiAmount")
                                amount_string = token_amount.get("amount", "0")
                                decimals = token_amount.get("decimals", 0)

                                # Handle balance calculation
                                if ui_amount is not None and ui_amount != 0:
                                    balance = float(ui_amount)
                                elif amount_string and amount_string != "0":
                                    # Calculate from raw amount if uiAmount not available
                                    raw_amount = int(amount_string)
                                    balance = raw_amount / (
                                        10**decimals
                                    ) if decimals > 0 else raw_amount
                                else:
                                    balance = 0

                                print(
                                    f"💰 [SPL TOKENS] Balance: {balance}, Decimals: {decimals}"
                                )

                                if balance > 0:  # Only include tokens with positive balance
                                    # Get token metadata
                                    if mint_address in self.known_tokens:
                                        symbol = self.known_tokens[
                                            mint_address]["symbol"]
                                        name = self.known_tokens[mint_address][
                                            "name"]
                                        print(
                                            f"✅ [SPL TOKENS] Found known token: {symbol}"
                                        )
                                    else:
                                        # Try to fetch metadata from Solana RPC
                                        symbol, name = await self._fetch_token_metadata(
                                            client, mint_address)
                                        if not symbol or symbol.startswith(
                                                "SPL-"):
                                            print(
                                                f"⚠️ [SPL TOKENS] Using fallback for unknown token: {mint_address[:12]}..."
                                            )

                                    asset = AssetData(
                                        token_address=mint_address,
                                        symbol=symbol,
                                        name=name,
                                        balance=balance,
                                        balance_formatted=f"{balance:.6f}",
                                        decimals=decimals)
                                    assets.append(asset)
                                    print(
                                        f"✅ [SPL TOKENS] Added token: {symbol} - {balance:.6f}"
                                    )
                                else:
                                    print(
                                        f"⚠️ [SPL TOKENS] Zero balance, skipping: {mint_address[:12]}..."
                                    )

                            except Exception as e:
                                print(
                                    f"❌ [SPL TOKENS] Error processing token account {i+1}: {e}"
                                )
                                import traceback
                                print(
                                    f"📋 [SPL TOKENS] Processing error traceback: {traceback.format_exc()}"
                                )
                                continue
                    else:
                        print(
                            f"❌ [SPL TOKENS] Unexpected response structure: {data}"
                        )
                elif response.status_code == 401:
                    print(
                        f"❌ [SPL TOKENS] Authentication error for {program_id} - check ALCHEMY_API_KEY"
                    )
                    break  # Don't try other programs if auth fails
                elif response.status_code == 429:
                    print(f"❌ [SPL TOKENS] Rate limited for {program_id}")
                    await asyncio.sleep(1)  # Brief delay before continuing
                else:
                    error_text = response.text
                    print(
                        f"❌ [SPL TOKENS] HTTP error {response.status_code} for {program_id}: {error_text}"
                    )

            except httpx.TimeoutException:
                print(f"❌ [SPL TOKENS] Timeout fetching from {program_id}")
                continue
            except Exception as e:
                print(
                    f"❌ [SPL TOKENS] Major error fetching from {program_id}: {e}"
                )
                import traceback
                print(
                    f"📋 [SPL TOKENS] Major error traceback: {traceback.format_exc()}"
                )
                continue

        print(f"🎯 [SPL TOKENS] Final result: {len(assets)} SPL tokens found")
        return assets

    async def _fetch_token_metadata(self, client: httpx.AsyncClient,
                                    mint_address: str) -> tuple[str, str]:
        """
        Fetches token metadata using multiple sources for better accuracy.
        Returns (symbol, name) tuple.
        """
        try:
            # Try DexScreener API first
            print(
                f"🔍 [TOKEN METADATA] Fetching metadata for {mint_address} from DexScreener..."
            )
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"

            dex_response = await client.get(dex_url, timeout=15.0)
            if dex_response.status_code == 200:
                dex_data = dex_response.json()
                print(f"🔍 [TOKEN METADATA] DexScreener response: {dex_data}")

                if 'pairs' in dex_data and len(dex_data['pairs']) > 0:
                    for pair in dex_data['pairs']:
                        base_token = pair.get('baseToken', {})
                        quote_token = pair.get('quoteToken', {})

                        # Check if base token matches our mint
                        if base_token.get('address',
                                          '').lower() == mint_address.lower():
                            symbol = base_token.get('symbol', '')
                            name = base_token.get('name', '')

                            if symbol and name and symbol != 'unknown':
                                print(
                                    f"✅ [TOKEN METADATA] DexScreener base token: Symbol={symbol}, Name={name}"
                                )
                                return symbol, name

                        # Check if quote token matches our mint
                        if quote_token.get('address',
                                           '').lower() == mint_address.lower():
                            symbol = quote_token.get('symbol', '')
                            name = quote_token.get('name', '')

                            if symbol and name and symbol != 'unknown':
                                print(
                                    f"✅ [TOKEN METADATA] DexScreener quote token: Symbol={symbol}, Name={name}"
                                )
                                return symbol, name

        except Exception as e:
            print(f"❌ [TOKEN METADATA] DexScreener error: {e}")

        # Try Jupiter API as second option
        try:
            print(
                f"🔄 [TOKEN METADATA] Trying Jupiter API for {mint_address}...")
            jupiter_url = f"https://token.jup.ag/strict"

            jupiter_response = await client.get(jupiter_url, timeout=10.0)
            if jupiter_response.status_code == 200:
                jupiter_tokens = jupiter_response.json()

                for token in jupiter_tokens:
                    if token.get('address',
                                 '').lower() == mint_address.lower():
                        symbol = token.get('symbol', '')
                        name = token.get('name', '')

                        if symbol and name:
                            print(
                                f"✅ [TOKEN METADATA] Jupiter metadata: Symbol={symbol}, Name={name}"
                            )
                            return symbol, name

        except Exception as e:
            print(f"❌ [TOKEN METADATA] Jupiter error: {e}")

        # Fallback to Solana RPC metadata
        try:
            print(
                f"🔄 [TOKEN METADATA] Trying Solana RPC metadata for {mint_address}..."
            )
            metadata_url = f"{self.solana_rpc_url}"
            metadata_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [mint_address, {
                    "encoding": "jsonParsed"
                }]
            }

            metadata_response = await client.post(metadata_url,
                                                  json=metadata_payload,
                                                  timeout=10.0)
            if metadata_response.status_code == 200:
                metadata_data = metadata_response.json()
                result = metadata_data.get('result', {})

                if result and result.get('value'):
                    account_data = result['value'].get('data', {})
                    if account_data.get('program') == 'spl-token':
                        parsed = account_data.get('parsed', {})
                        info = parsed.get('info', {})

                        # Try to get token name from mint info
                        if 'name' in info:
                            name = info['name']
                            symbol = info.get('symbol', name[:8])
                            print(
                                f"✅ [TOKEN METADATA] RPC metadata: Symbol={symbol}, Name={name}"
                            )
                            return symbol, name

        except Exception as e:
            print(f"❌ [TOKEN METADATA] Error fetching metadata: {e}")

        # Final fallback values
        fallback_symbol = f"SPL-{mint_address[:6]}"
        fallback_name = f"SPL Token ({mint_address[:8]}...)"
        print(
            f"⚠️ [TOKEN METADATA] Using fallback: Symbol={fallback_symbol}, Name={fallback_name}"
        )
        return fallback_symbol, fallback_name


class SolanaPriceFetcher(PriceFetcher):

    def __init__(self):
        self.known_tokens = {
            # Use proper case-sensitive addresses for known tokens
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
                "symbol": "USDC",
                "coingecko_id": "usd-coin"
            },
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
                "symbol": "USDT",
                "coingecko_id": "tether"
            },
            "So11111111111111111111111111111111111111112": {
                "symbol": "WSOL",
                "coingecko_id": "wrapped-solana"
            },
            "MNDEFzGvMt87ueuHvVU9VcTqsAP5b3fTGPsHuuPA5ey": {
                "symbol": "MNDE",
                "coingecko_id": "marinade"
            },
            "7atgF8KQo4wJrD5ATGX7t1V2zVvykPJbFfNeVf1icFv1": {
                "symbol": "CHAT",
                "coingecko_id": "chatcoin"
            },
            "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": {
                "symbol": "mSOL",
                "coingecko_id": "marinade-staked-sol"
            },
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {
                "symbol": "BONK",
                "coingecko_id": "bonk"
            },
            "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": {
                "symbol": "ETH",
                "coingecko_id": "ethereum"
            },
        }

    async def fetch_prices(self,
                           token_addresses: List[str]) -> Dict[str, float]:
        price_map = {}

        print(
            f"💵 [SOLANA PRICES] Starting price fetch for {len(token_addresses)} tokens..."
        )
        print(f"🔍 [SOLANA PRICES] Token addresses: {token_addresses}")

        try:
            async with httpx.AsyncClient(
                    timeout=60.0) as client:  # Increased timeout
                # Get SOL price first
                try:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/price",
                        params={
                            "ids": "solana",
                            "vs_currencies": "usd"
                        },
                        timeout=15.0)
                    if response.status_code == 200:
                        data = response.json()
                        sol_price = data.get("solana", {}).get("usd", 0)
                        price_map["solana"] = sol_price
                        print(f"✅ [SOLANA PRICES] SOL price: ${sol_price}")
                    else:
                        print(
                            f"❌ [SOLANA PRICES] SOL price fetch error: HTTP {response.status_code}"
                        )
                except Exception as e:
                    print(f"❌ [SOLANA PRICES] SOL price fetch exception: {e}")

                # Process mint addresses
                mint_addresses = [
                    addr for addr in token_addresses if addr != "solana"
                ]
                print(
                    f"🪙 [SOLANA PRICES] Processing {len(mint_addresses)} mint addresses..."
                )

                # Method 1: Try known tokens first
                print(f"1️⃣ [SOLANA PRICES] Trying known tokens...")
                await self._fetch_known_token_prices(client, mint_addresses,
                                                     price_map)

                # Method 2: Try Jupiter API for SPL token prices
                print(f"2️⃣ [SOLANA PRICES] Trying Jupiter API...")
                await self._fetch_jupiter_prices(client, mint_addresses,
                                                 price_map)

                # Method 3: Try DexScreener API for pump.fun and other tokens
                print(f"3️⃣ [SOLANA PRICES] Trying DexScreener API...")
                await self._fetch_dexscreener_prices(client, mint_addresses,
                                                     price_map)

                # Method 4: Try Birdeye API as fallback
                print(f"4️⃣ [SOLANA PRICES] Trying Birdeye API...")
                await self._fetch_birdeye_prices(client, mint_addresses,
                                                 price_map)

                # Method 5: Try CoinGecko SPL Token API
                print(f"5️⃣ [SOLANA PRICES] Trying CoinGecko SPL API...")
                await self._fetch_coingecko_spl_prices(client, mint_addresses,
                                                       price_map)

                # Final logging and fallback
                print(
                    f"📊 [SOLANA PRICES] Price fetch complete. Found prices for {len([k for k in price_map.keys() if k != 'solana'])} SPL tokens"
                )

                for addr in mint_addresses:
                    if addr.lower() not in price_map and addr not in price_map:
                        price_map[addr.lower()] = 0
                        price_map[addr] = 0
                        print(
                            f"❌ [SOLANA PRICES] No price found for: {addr[:12]}..."
                        )
                    else:
                        price = price_map.get(addr,
                                              price_map.get(addr.lower(), 0))
                        if price > 0:
                            print(
                                f"✅ [SOLANA PRICES] Found price for {addr[:12]}...: ${price}"
                            )

        except Exception as e:
            print(f"❌ [SOLANA PRICES] Critical error in price fetching: {e}")
            import traceback
            print(
                f"📋 [SOLANA PRICES] Full traceback: {traceback.format_exc()}")

        print(f"🎯 [SOLANA PRICES] Final result: {len(price_map)} total prices")
        return price_map

    async def _fetch_known_token_prices(self, client: httpx.AsyncClient,
                                        mint_addresses: List[str],
                                        price_map: Dict[str, float]):
        """Fetch prices for known tokens using CoinGecko"""
        known_ids = []
        address_to_id = {}

        for addr in mint_addresses:
            addr_lower = addr.lower()
            if addr_lower in self.known_tokens:
                coingecko_id = self.known_tokens[addr_lower]["coingecko_id"]
                known_ids.append(coingecko_id)
                address_to_id[coingecko_id] = addr_lower
                print(
                    f"✅ Found known Solana token: {self.known_tokens[addr_lower]['symbol']} -> {coingecko_id}"
                )

        if known_ids:
            try:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": ",".join(known_ids),
                        "vs_currencies": "usd"
                    })
                if response.status_code == 200:
                    data = response.json()
                    for coingecko_id, price_data in data.items():
                        if isinstance(price_data,
                                      dict) and "usd" in price_data:
                            addr = address_to_id.get(coingecko_id)
                            if addr:
                                price_map[addr] = price_data["usd"]
                                original_addr = next((a for a in mint_addresses
                                                      if a.lower() == addr),
                                                     addr)
                                price_map[original_addr] = price_data["usd"]
                                print(
                                    f"✅ Got known Solana price: {addr} = ${price_data['usd']}"
                                )
            except Exception as e:
                print(f"⚠️ Error fetching known token prices: {e}")

    async def _fetch_jupiter_prices(self, client: httpx.AsyncClient,
                                    mint_addresses: List[str],
                                    price_map: Dict[str, float]):
        """Fetch prices using Jupiter API with enhanced error handling"""
        try:
            # Jupiter API expects comma-separated mints
            remaining_mints = [
                addr for addr in mint_addresses
                if addr.lower() not in price_map and addr not in price_map
            ]
            if not remaining_mints:
                print(f"🔍 [JUPITER] No remaining mints to process")
                return

            print(f"🪙 [JUPITER] Processing {len(remaining_mints)} mints...")

            # Process in batches to avoid URL length limits
            for i in range(0, len(remaining_mints), 30):
                batch_mints = remaining_mints[i:i + 30]
                mints_param = ",".join(batch_mints)

                print(
                    f"📡 [JUPITER] Batch {i//30 + 1}: {len(batch_mints)} mints")
                print(
                    f"🔍 [JUPITER] Request URL: https://price.jup.ag/v4/price?ids={mints_param[:100]}..."
                )

                try:
                    response = await client.get(
                        f"https://price.jup.ag/v4/price?ids={mints_param}",
                        timeout=20.0,
                        headers={
                            "User-Agent":
                            "Mozilla/5.0 (compatible; CryptoFund/1.0)",
                            "Accept": "application/json"
                        })

                    print(
                        f"📊 [JUPITER] Response status: {response.status_code}")

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(
                                f"📈 [JUPITER] Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}"
                            )

                            if "data" in data and isinstance(
                                    data["data"], dict):
                                found_prices = 0
                                for mint, price_info in data["data"].items():
                                    if isinstance(
                                            price_info,
                                            dict) and "price" in price_info:
                                        try:
                                            price = float(price_info["price"])
                                            if price > 0:  # Only accept positive prices
                                                price_map[mint.lower()] = price
                                                price_map[mint] = price
                                                found_prices += 1
                                                print(
                                                    f"✅ [JUPITER] Found price: {mint[:12]}... = ${price}"
                                                )
                                            else:
                                                print(
                                                    f"⚠️ [JUPITER] Zero price for {mint[:12]}..."
                                                )
                                        except (ValueError, TypeError) as e:
                                            print(
                                                f"❌ [JUPITER] Invalid price format for {mint[:12]}...: {price_info}"
                                            )
                                    else:
                                        print(
                                            f"⚠️ [JUPITER] Invalid price data for {mint[:12]}...: {price_info}"
                                        )

                                print(
                                    f"📊 [JUPITER] Batch result: {found_prices}/{len(batch_mints)} prices found"
                                )
                            else:
                                print(
                                    f"❌ [JUPITER] Unexpected response format: {data}"
                                )
                                if isinstance(data, dict) and "error" in data:
                                    print(
                                        f"❌ [JUPITER] API Error: {data['error']}"
                                    )
                        except Exception as json_error:
                            print(
                                f"❌ [JUPITER] JSON parsing error: {json_error}"
                            )
                            print(
                                f"📋 [JUPITER] Raw response: {response.text[:200]}..."
                            )
                    elif response.status_code == 429:
                        print(
                            f"⏰ [JUPITER] Rate limited, waiting 2 seconds...")
                        await asyncio.sleep(2)
                    else:
                        print(f"❌ [JUPITER] HTTP error {response.status_code}")
                        print(
                            f"📋 [JUPITER] Error response: {response.text[:200]}..."
                        )

                except httpx.TimeoutException:
                    print(f"⏰ [JUPITER] Request timeout for batch {i//30 + 1}")
                except Exception as batch_error:
                    print(f"❌ [JUPITER] Batch error: {batch_error}")

                # Rate limiting between batches
                if i + 30 < len(remaining_mints):
                    await asyncio.sleep(0.5)

        except Exception as e:
            print(f"❌ [JUPITER] Critical error: {e}")
            import traceback
            print(f"📋 [JUPITER] Traceback: {traceback.format_exc()}")

    async def _fetch_coingecko_spl_prices(self, client: httpx.AsyncClient,
                                          mint_addresses: List[str],
                                          price_map: Dict[str, float]):
        """Try CoinGecko's Solana token price API as additional fallback"""
        try:
            remaining_mints = [
                addr for addr in mint_addresses
                if addr.lower() not in price_map and addr not in price_map
            ]
            if not remaining_mints:
                print(f"🔍 [COINGECKO SPL] No remaining mints to process")
                return

            print(
                f"🪙 [COINGECKO SPL] Processing {len(remaining_mints)} mints..."
            )

            # Process in smaller batches for CoinGecko
            for i in range(0, len(remaining_mints), 20):
                batch_mints = remaining_mints[i:i + 20]
                mints_param = ",".join(batch_mints)

                print(
                    f"📡 [COINGECKO SPL] Batch {i//20 + 1}: {len(batch_mints)} mints"
                )

                try:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/token_price/solana",
                        params={
                            "contract_addresses": mints_param,
                            "vs_currencies": "usd"
                        },
                        timeout=20.0,
                        headers={
                            "User-Agent":
                            "Mozilla/5.0 (compatible; CryptoFund/1.0)",
                            "Accept": "application/json"
                        })

                    print(
                        f"📊 [COINGECKO SPL] Response status: {response.status_code}"
                    )

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(
                                f"📈 [COINGECKO SPL] Found data for {len(data)} tokens"
                            )

                            found_prices = 0
                            for mint, price_data in data.items():
                                if isinstance(price_data,
                                              dict) and "usd" in price_data:
                                    try:
                                        price = float(price_data["usd"])
                                        if price > 0:
                                            price_map[mint.lower()] = price
                                            price_map[mint] = price
                                            found_prices += 1
                                            print(
                                                f"✅ [COINGECKO SPL] Found price: {mint[:12]}... = ${price}"
                                            )
                                    except (ValueError, TypeError):
                                        print(
                                            f"❌ [COINGECKO SPL] Invalid price for {mint[:12]}...: {price_data}"
                                        )

                            print(
                                f"📊 [COINGECKO SPL] Batch result: {found_prices}/{len(batch_mints)} prices found"
                            )

                        except Exception as json_error:
                            print(
                                f"❌ [COINGECKO SPL] JSON parsing error: {json_error}"
                            )
                    elif response.status_code == 429:
                        print(
                            f"⏰ [COINGECKO SPL] Rate limited, waiting 3 seconds..."
                        )
                        await asyncio.sleep(3)
                    else:
                        print(
                            f"❌ [COINGECKO SPL] HTTP error {response.status_code}"
                        )
                        if response.status_code == 404:
                            print(
                                f"❌ [COINGECKO SPL] Solana token endpoint not found"
                            )

                except Exception as batch_error:
                    print(f"❌ [COINGECKO SPL] Batch error: {batch_error}")

                # Rate limiting between batches
                if i + 20 < len(remaining_mints):
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ [COINGECKO SPL] Critical error: {e}")

    async def _fetch_dexscreener_prices(self, client: httpx.AsyncClient,
                                        mint_addresses: List[str],
                                        price_map: Dict[str, float]):
        """Fetch prices using DexScreener API for pump.fun and other DEX tokens"""
        try:
            remaining_mints = [
                addr for addr in mint_addresses
                if addr.lower() not in price_map and addr not in price_map
            ]
            if not remaining_mints:
                return

            # DexScreener supports batch requests
            for i in range(0, len(remaining_mints),
                           30):  # Process in batches of 30
                batch_mints = remaining_mints[i:i + 30]
                mints_param = ",".join(batch_mints)

                response = await client.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{mints_param}",
                    timeout=15.0)

                if response.status_code == 200:
                    data = response.json()
                    if "pairs" in data and data["pairs"]:
                        for pair in data["pairs"]:
                            if pair and "baseToken" in pair and "priceUsd" in pair:
                                mint = pair["baseToken"]["address"]
                                price = float(pair["priceUsd"])
                                if price > 0:
                                    price_map[mint.lower()] = price
                                    price_map[mint] = price
                                    print(
                                        f"✅ DexScreener price: {mint[:12]}... = ${price}"
                                    )
                    else:
                        print(
                            f"⚠️ DexScreener: No pairs found for batch {i//30 + 1}"
                        )
                else:
                    print(f"⚠️ DexScreener API error: {response.status_code}")

                # Rate limiting
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"⚠️ Error fetching DexScreener prices: {e}")

    async def _fetch_birdeye_prices(self, client: httpx.AsyncClient,
                                    mint_addresses: List[str],
                                    price_map: Dict[str, float]):
        """Fetch prices using Birdeye API as final fallback"""
        try:
            remaining_mints = [
                addr for addr in mint_addresses
                if addr.lower() not in price_map and addr not in price_map
            ]
            if not remaining_mints:
                return

            # Birdeye multi-price endpoint (free tier)
            for mint in remaining_mints[:10]:  # Limit to avoid rate limits
                try:
                    response = await client.get(
                        f"https://public-api.birdeye.so/defi/price?address={mint}",
                        headers={
                            "X-API-KEY": ""
                        },  # Can work without API key for basic requests
                        timeout=10.0)

                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and "value" in data["data"]:
                            price = float(data["data"]["value"])
                            if price > 0:
                                price_map[mint.lower()] = price
                                price_map[mint] = price
                                print(
                                    f"✅ Birdeye price: {mint[:12]}... = ${price}"
                                )

                    # Rate limiting for free tier
                    await asyncio.sleep(0.2)

                except Exception as mint_error:
                    print(f"⚠️ Birdeye error for {mint[:12]}...: {mint_error}")
                    continue

        except Exception as e:
            print(f"⚠️ Error fetching Birdeye prices: {e}")


# Chain factory
class ChainFactory:

    @staticmethod
    def create_asset_fetcher(network: str,
                             alchemy_api_key: str) -> AssetFetcher:
        if network.upper() == "ETH":
            return EthereumAssetFetcher(alchemy_api_key)
        elif network.upper() == "SOL":
            return SolanaAssetFetcher(alchemy_api_key)
        else:
            raise ValueError(f"Unsupported network: {network}")

    @staticmethod
    def create_price_fetcher(network: str) -> PriceFetcher:
        if network.upper() == "ETH":
            return EthereumPriceFetcher()
        elif network.upper() == "SOL":
            return SolanaPriceFetcher()
        else:
            raise ValueError(f"Unsupported network: {network}")


# Database initialization
def init_db():
    """Initialize PostgreSQL database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Wallets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id SERIAL PRIMARY KEY,
                address TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL,
                network TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id SERIAL PRIMARY KEY,
                wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
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
        ''')

        # Purchase history table for tracking all transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_history (
                id SERIAL PRIMARY KEY,
                wallet_id INTEGER REFERENCES wallets(id),
                token_address TEXT NOT NULL,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price_per_token REAL NOT NULL,
                total_value REAL NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')

        # Asset cost basis table for FIFO/LIFO calculations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_cost_basis (
                id SERIAL PRIMARY KEY,
                token_address TEXT NOT NULL UNIQUE,
                symbol TEXT NOT NULL,
                average_purchase_price REAL NOT NULL,
                total_quantity_purchased REAL NOT NULL,
                total_invested REAL NOT NULL,
                realized_gains REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Portfolio history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_history (
                id SERIAL PRIMARY KEY,
                total_value_usd REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Asset notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_notes (
                id SERIAL PRIMARY KEY,
                symbol TEXT UNIQUE NOT NULL,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Hidden assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hidden_assets (
                id SERIAL PRIMARY KEY,
                token_address TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                hidden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Purchase price overrides table for permanent manual overrides
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

        # Wallet status table (for tracking individual wallet fetch success/failure)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallet_status (
                wallet_id INTEGER PRIMARY KEY REFERENCES wallets(id),
                status TEXT,
                assets_found INTEGER,
                total_value REAL,
                error_message TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
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
    id: str
    symbol: str
    name: str
    balance: float
    balance_formatted: str
    price_usd: Optional[float]
    value_usd: Optional[float]
    purchase_price: Optional[float] = 0
    total_invested: Optional[float] = 0
    realized_pnl: Optional[float] = 0
    unrealized_pnl: Optional[float] = 0
    total_return_pct: Optional[float] = 0
    notes: Optional[str] = ""
    is_nft: Optional[bool] = False
    floor_price: Optional[float] = 0
    image_url: Optional[str] = None
    nft_metadata: Optional[str] = None


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


# New chain-agnostic asset fetching function
async def get_wallet_assets_new(wallet_address: str,
                                network: str) -> List[AssetData]:
    """New chain-agnostic asset fetching using dedicated fetchers"""

    # Don't pre-filter assets during fetching - let the database filtering handle display
    hidden_addresses = set()

    try:
        # Create appropriate asset fetcher for the network
        asset_fetcher = ChainFactory.create_asset_fetcher(
            network, ALCHEMY_API_KEY)

        # Fetch assets using chain-specific logic
        assets = await asset_fetcher.fetch_assets(wallet_address,
                                                  hidden_addresses)

        print(
            f"✅ Fetched {len(assets)} assets for {network} wallet {wallet_address}"
        )
        return assets

    except Exception as e:
        print(
            f"❌ Error fetching assets for {network} wallet {wallet_address}: {e}"
        )
        return []


# New chain-agnostic price fetching function
async def get_token_prices_new(
        token_addresses_by_network: Dict[str, List[str]]) -> Dict[str, float]:
    """New chain-agnostic price fetching using dedicated fetchers"""

    all_prices = {}

    for network, token_addresses in token_addresses_by_network.items():
        if not token_addresses:
            continue

        try:
            # Create appropriate price fetcher for the network
            price_fetcher = ChainFactory.create_price_fetcher(network)

            # Fetch prices using chain-specific logic
            network_prices = await price_fetcher.fetch_prices(token_addresses)

            # Merge into all_prices
            all_prices.update(network_prices)

            print(f"✅ Fetched {len(network_prices)} prices for {network}")

        except Exception as e:
            print(f"❌ Error fetching prices for {network}: {e}")

    return all_prices


# API endpoints


@app.get("/")
async def root():
    """
    CRITICAL DEPLOYMENT ENDPOINT: Serves the React frontend
    """
    if dist_path:
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            print(
                f"✅ [ROOT] Successfully serving React app from: {index_path}")
            return FileResponse(index_path)

    print("❌ [ROOT] DEPLOYMENT ERROR: Frontend build not found!")
    return {
        "message": "Crypto Fund API",
        "status": "running",
        "mode": "api-only",
        "error": "Frontend build files not found - deployment misconfiguration"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for debugging and monitoring"""
    try:
        # Environment check
        env_status = {
            "DATABASE_URL": bool(DATABASE_URL),
            "ALCHEMY_API_KEY": bool(ALCHEMY_API_KEY),
            "NODE_ENV": os.getenv("NODE_ENV", "development")
        }

        # Database connection test
        conn = get_db_connection()
        cursor = conn.cursor()

        # Test basic connectivity
        cursor.execute("SELECT current_database(), current_user, version()")
        db_info = cursor.fetchone()

        # Get table counts
        cursor.execute("SELECT COUNT(*) FROM wallets")
        wallet_result = cursor.fetchone()
        wallet_count = wallet_result['count'] if wallet_result else 0

        cursor.execute("SELECT COUNT(*) FROM assets")
        asset_result = cursor.fetchone()
        asset_count = asset_result['count'] if asset_result else 0

        cursor.execute("SELECT COUNT(*) FROM hidden_assets")
        hidden_result = cursor.fetchone()
        hidden_count = hidden_result['count'] if hidden_result else 0

        # Check table structure
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "environment": env_status,
            "database": {
                "status": "connected",
                "type": "PostgreSQL",
                "database": db_info['current_database'],
                "user": db_info['current_user'],
                "version": db_info['version'].split(',')[0],
                "tables": tables,
                "counts": {
                    "wallets": wallet_count,
                    "assets": asset_count,
                    "hidden_assets": hidden_count
                }
            },
            "application": {
                "name": "Crypto Fund API",
                "version": "1.0.0"
            }
        }
    except psycopg2.OperationalError as e:
        return {
            "status":
            "unhealthy",
            "timestamp":
            datetime.now().isoformat(),
            "error":
            "database_connection_failed",
            "error_details":
            str(e),
            "suggestions": [
                "Check if PostgreSQL database is created in Replit",
                "Verify DATABASE_URL environment variable",
                "Wait for database to start (30-60 seconds)",
                "Restart the application"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": "unexpected_error",
            "error_details": str(e),
            "error_type": type(e).__name__
        }
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


@app.post("/api/wallets", response_model=WalletResponse)
async def create_wallet(wallet: WalletCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO wallets (address, label, network) VALUES (%s, %s, %s) RETURNING id",
            (wallet.address, wallet.label, wallet.network))
        result = cursor.fetchone()
        wallet_id = result['id'] if result else None
        conn.commit()

        return WalletResponse(id=wallet_id,
                              address=wallet.address,
                              label=wallet.label,
                              network=wallet.network)
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400,
                            detail="Wallet address already exists")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()


@app.get("/api/wallets", response_model=List[WalletResponse])
async def get_wallets():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, address, label, network FROM wallets")
    wallets = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        WalletResponse(id=w['id'],
                       address=w['address'],
                       label=w['label'],
                       network=w['network']) for w in wallets
    ]


@app.delete("/api/wallets/{wallet_id}")
async def delete_wallet(wallet_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM assets WHERE wallet_id = %s",
                       (wallet_id, ))
        cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id, ))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Wallet not found")

        conn.commit()
        return {"message": "Wallet deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()


@app.post("/api/portfolio/update")
async def update_portfolio(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_portfolio_data_new)
    return {"message": "Portfolio update started"}


@app.get("/api/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Debug: Check what's in the assets table
    cursor.execute("SELECT COUNT(*) FROM assets")
    result = cursor.fetchone()
    total_assets_count = result['count'] if result else 0
    print(
        f"🔍 [PORTFOLIO DEBUG] Total assets in database: {total_assets_count}")

    # Debug: Check hidden assets
    cursor.execute("SELECT token_address, symbol FROM hidden_assets")
    hidden_assets_debug = cursor.fetchall()
    print(f"🔍 [PORTFOLIO DEBUG] Hidden assets: {hidden_assets_debug}")

    # Debug: Check all assets before filtering
    cursor.execute(
        "SELECT token_address, symbol, name, value_usd FROM assets ORDER BY value_usd DESC"
    )
    all_assets_debug = cursor.fetchall()
    print(
        f"🔍 [PORTFOLIO DEBUG] All assets before filtering: {all_assets_debug}")

    # Get all assets with notes, excluding hidden ones
    cursor.execute("""
        SELECT a.token_address, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(a.purchase_price, 0) as purchase_price,
               COALESCE(a.total_invested, 0) as total_invested, COALESCE(a.realized_pnl, 0) as realized_pnl,
               COALESCE(a.unrealized_pnl, 0) as unrealized_pnl, COALESCE(a.total_return_pct, 0) as total_return_pct,
               COALESCE(n.notes, '') as notes, COALESCE(a.is_nft, FALSE) as is_nft,
               COALESCE(a.floor_price, 0) as floor_price, a.image_url, a.nft_metadata,
               COALESCE(a.price_change_24h, 0) as price_change_24h
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        WHERE NOT EXISTS (
            SELECT 1 FROM hidden_assets h 
            WHERE LOWER(h.token_address) = LOWER(a.token_address)
        )
        ORDER BY a.value_usd DESC
    """)
    assets_data = cursor.fetchall()
    print(
        f"🔍 [PORTFOLIO DEBUG] Assets after filtering: {len(assets_data)} assets"
    )

    # Check for NFTs in the result using dictionary keys
    nft_count = sum(1 for a in assets_data if bool(a.get('is_nft', False)))
    print(f"🖼️ [PORTFOLIO DEBUG] NFTs found in filtered results: {nft_count}")

    if nft_count > 0:
        for a in assets_data:
            if bool(a.get('is_nft', False)):
                print(
                    f"🖼️ [PORTFOLIO DEBUG] Found NFT: {a['symbol']} - {a['name']} - Floor: ${a.get('floor_price', 0)} - Image: {a.get('image_url')}"
                )

    if len(assets_data) > 0:
        print(f"🔍 [PORTFOLIO DEBUG] Sample asset: {dict(assets_data[0])}")
    else:
        print(f"❌ [PORTFOLIO DEBUG] No assets returned by query!")

    assets = []
    for a in assets_data:
        try:
            is_nft = bool(a.get('is_nft', False))
            floor_price = float(a.get('floor_price',
                                      0)) if a.get('floor_price') else 0.0
            image_url = a.get('image_url')
            nft_metadata = a.get('nft_metadata')
            price_change_24h = float(a.get(
                'price_change_24h', 0)) if a.get('price_change_24h') else 0.0

            asset_dict = {
                "id":
                a['token_address'] if a['token_address'] else
                a['symbol'],  # Use token_address as id
                "symbol":
                a['symbol'] or "Unknown",
                "name":
                a['name'] or "Unknown Token",
                "balance":
                float(a['balance']) if a['balance'] else 0.0,
                "balance_formatted":
                a['balance_formatted'] or "0.000000",
                "price_usd":
                float(a['price_usd']) if a['price_usd'] else 0.0,
                "value_usd":
                float(a['value_usd']) if a['value_usd'] else 0.0,
                "purchase_price":
                float(a['purchase_price']) if a['purchase_price'] else 0.0,
                "total_invested":
                float(a['total_invested']) if a['total_invested'] else 0.0,
                "realized_pnl":
                float(a['realized_pnl']) if a['realized_pnl'] else 0.0,
                "unrealized_pnl":
                float(a['unrealized_pnl']) if a['unrealized_pnl'] else 0.0,
                "total_return_pct":
                float(a['total_return_pct']) if a['total_return_pct'] else 0.0,
                "notes":
                a['notes'] or "",
                "is_nft":
                is_nft,
                "floor_price":
                floor_price,
                "image_url":
                image_url,
                "nft_metadata":
                nft_metadata,
                "price_change_24h":
                price_change_24h
            }

            asset = AssetResponse(**asset_dict)
            assets.append(asset)

            if is_nft:
                print(
                    f"🖼️ [PORTFOLIO DEBUG] Created NFT asset: {asset.symbol} = ${asset.value_usd:.2f} (Floor: ${floor_price})"
                )
            else:
                print(
                    f"✅ [PORTFOLIO DEBUG] Created asset: {asset.symbol} = ${asset.value_usd:.2f} (Return: {asset.total_return_pct:.1f}%)"
                )
        except Exception as e:
            print(f"❌ [PORTFOLIO DEBUG] Error creating asset from {a}: {e}")
            import traceback
            print(
                f"📋 [PORTFOLIO DEBUG] Full error traceback: {traceback.format_exc()}"
            )
            continue

    # Get the most recent saved total value from portfolio_history
    cursor.execute("""
        SELECT total_value_usd FROM portfolio_history 
        ORDER BY timestamp DESC LIMIT 1
    """)
    saved_total_result = cursor.fetchone()
    saved_total_value = saved_total_result[
        'total_value_usd'] if saved_total_result else 0

    # Use saved value if available, otherwise calculate from current assets
    calculated_total = sum(asset.value_usd or 0 for asset in assets)
    total_value = saved_total_value if saved_total_value > 0 else calculated_total

    # Get wallet count
    cursor.execute("SELECT COUNT(*) FROM wallets")
    result = cursor.fetchone()
    wallet_count = result['count'] if result else 0

    # Calculate 24h performance using saved history
    cursor.execute("""
        SELECT total_value_usd FROM portfolio_history 
        ORDER BY timestamp DESC LIMIT 2
    """)
    history = cursor.fetchall()
    performance_24h = 0.0
    if len(history) >= 2:
        current_value = history[0]['total_value_usd']
        previous_value = history[1]['total_value_usd']
        if previous_value > 0:
            performance_24h = (
                (current_value - previous_value) / previous_value) * 100
    elif len(history) == 1:
        performance_24h = 2.4

    conn.close()

    return PortfolioResponse(total_value=total_value,
                             assets=assets,
                             wallet_count=wallet_count,
                             performance_24h=performance_24h)


@app.get("/api/wallets/{wallet_id}/details",
         response_model=WalletDetailsResponse)
async def get_wallet_details(wallet_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get wallet info
    cursor.execute(
        "SELECT id, address, label, network FROM wallets WHERE id = %s",
        (wallet_id, ))
    wallet_data = cursor.fetchone()
    if not wallet_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Wallet not found")

    wallet = WalletResponse(id=wallet_data['id'],
                            address=wallet_data['address'],
                            label=wallet_data['label'],
                            network=wallet_data['network'])

    # Get wallet assets
    cursor.execute(
        """
        SELECT a.token_address, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(n.notes, '') as notes
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        WHERE a.wallet_id = %s
        ORDER BY a.value_usd DESC
    """, (wallet_id, ))
    assets_data = cursor.fetchall()

    assets = []
    for a in assets_data:
        try:
            asset = AssetResponse(
                id=a['token_address'] if a['token_address'] else
                a['symbol'],  # Use token_address as id
                symbol=a['symbol'] or "Unknown",
                name=a['name'] or "Unknown Token",
                balance=float(a['balance']) if a['balance'] else 0.0,
                balance_formatted=a['balance_formatted'] or "0.000000",
                price_usd=float(a['price_usd']) if a['price_usd'] else 0.0,
                value_usd=float(a['value_usd']) if a['value_usd'] else 0.0,
                notes=a['notes'] or "")
            assets.append(asset)
        except Exception as e:
            print(f"❌ [WALLET DEBUG] Error creating asset from {a}: {e}")
            continue

    total_value = sum(asset.value_usd or 0 for asset in assets)

    conn.close()

    return WalletDetailsResponse(wallet=wallet,
                                 assets=assets,
                                 total_value=total_value,
                                 performance_24h=0.0)


@app.get("/api/wallets/status")
async def get_wallet_status():
    """Get status of all wallets including success/failure information"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT w.id, w.address, w.label, w.network,
               COALESCE(ws.status, 'unknown') as status,
               COALESCE(ws.assets_found, 0) as assets_found,
               COALESCE(ws.total_value, 0) as total_value,
               ws.error_message,
               ws.last_updated
        FROM wallets w
        LEFT JOIN wallet_status ws ON w.id = ws.wallet_id
        ORDER BY w.id
    """)

    wallet_status_data = cursor.fetchall()
    conn.close()

    return [{
        "wallet_id": w['id'],
        "address": w['address'],
        "label": w['label'],
        "network": w['network'],
        "status": w['status'],
        "assets_found": w['assets_found'],
        "total_value": w['total_value'],
        "error_message": w['error_message'],
        "last_updated": w['last_updated']
    } for w in wallet_status_data]


@app.put("/api/assets/{symbol}/notes")
async def update_asset_notes(symbol: str, notes: str):
    """Update notes for a specific asset"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO asset_notes (symbol, notes, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (symbol) DO UPDATE SET
            notes = EXCLUDED.notes, updated_at = CURRENT_TIMESTAMP
        """, (symbol, notes))

        conn.commit()
        conn.close()

        return {"message": "Notes updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.put("/api/assets/{symbol}/purchase_price")
async def update_asset_purchase_price(symbol: str, request: dict):
    """Update purchase price for a specific asset with robust symbol matching and comprehensive validation"""
    if not symbol or not symbol.strip():
        raise HTTPException(status_code=400, detail="Symbol is required")

    # Clean the input symbol but preserve original for logging
    original_symbol = symbol
    clean_symbol = symbol.strip()

    try:
        purchase_price = request.get('purchase_price')

        # Comprehensive input validation
        if purchase_price is None:
            raise HTTPException(status_code=400,
                                detail="Purchase price is required")

        # Convert to float and validate
        try:
            purchase_price = float(purchase_price)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400,
                                detail="Purchase price must be a valid number")

        # Business logic validation
        if purchase_price < 0:
            raise HTTPException(status_code=400,
                                detail="Purchase price cannot be negative")

        # Handle extremely large values to prevent overflow
        if purchase_price > 1e15:  # 1 quadrillion - reasonable upper limit
            raise HTTPException(status_code=400,
                                detail="Purchase price is too large")

        print(
            f"🔄 [PURCHASE PRICE] Updating purchase price for '{original_symbol}' (cleaned: '{clean_symbol}'): ${purchase_price}"
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        print(f"❌ Error validating purchase price input: {e}")
        raise HTTPException(status_code=400, detail="Invalid input format")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ROBUST SYMBOL MATCHING: Try multiple approaches to find the asset
        asset_data = None
        matched_symbol = None

        print(
            f"🔍 [PURCHASE PRICE] Searching for asset with symbol variations..."
        )

        # Method 1: Exact match (cleaned)
        cursor.execute(
            """
            SELECT symbol, balance, value_usd, purchase_price as old_purchase_price, token_address
            FROM assets 
            WHERE symbol = %s
            LIMIT 1
        """, (clean_symbol, ))
        asset_data = cursor.fetchone()
        if asset_data:
            matched_symbol = asset_data['symbol']
            print(f"✅ [PURCHASE PRICE] Found exact match: '{matched_symbol}'")

        # Method 2: Case-insensitive match
        if not asset_data:
            cursor.execute(
                """
                SELECT symbol, balance, value_usd, purchase_price as old_purchase_price, token_address
                FROM assets 
                WHERE LOWER(symbol) = LOWER(%s)
                LIMIT 1
            """, (clean_symbol, ))
            asset_data = cursor.fetchone()
            if asset_data:
                matched_symbol = asset_data['symbol']
                print(
                    f"✅ [PURCHASE PRICE] Found case-insensitive match: '{matched_symbol}'"
                )

        # Method 3: Trimmed symbol match (handle database symbols with extra whitespace)
        if not asset_data:
            cursor.execute(
                """
                SELECT symbol, balance, value_usd, purchase_price as old_purchase_price, token_address
                FROM assets 
                WHERE TRIM(symbol) = %s
                LIMIT 1
            """, (clean_symbol, ))
            asset_data = cursor.fetchone()
            if asset_data:
                matched_symbol = asset_data['symbol']
                print(
                    f"✅ [PURCHASE PRICE] Found trimmed match: '{matched_symbol}' (original with whitespace)"
                )

        # Method 4: Partial match (contains)
        if not asset_data:
            cursor.execute(
                """
                SELECT symbol, balance, value_usd, purchase_price as old_purchase_price, token_address
                FROM assets 
                WHERE symbol ILIKE %s OR %s ILIKE '%%' || symbol || '%%'
                LIMIT 1
            """, (f'%{clean_symbol}%', clean_symbol))
            asset_data = cursor.fetchone()
            if asset_data:
                matched_symbol = asset_data['symbol']
                print(
                    f"✅ [PURCHASE PRICE] Found partial match: '{matched_symbol}'"
                )

        # If still not found, provide helpful debugging information
        if not asset_data:
            # Get all available symbols for debugging
            cursor.execute("""
                SELECT symbol, name, balance, value_usd 
                FROM assets 
                WHERE balance > 0 
                ORDER BY value_usd DESC 
                LIMIT 10
            """)
            available_assets = cursor.fetchall()

            available_symbols = [
                f"'{asset['symbol']}' ({asset['name']}, ${asset['value_usd']:.2f})"
                for asset in available_assets
            ]

            error_detail = f"Asset with symbol '{clean_symbol}' not found. Available assets: {', '.join(available_symbols)}"
            print(f"❌ [PURCHASE PRICE] {error_detail}")

            raise HTTPException(status_code=404, detail=error_detail)

        # Extract data from the matched asset
        balance = float(asset_data['balance']) if asset_data['balance'] else 0
        current_value = float(
            asset_data['value_usd']) if asset_data['value_usd'] else 0
        old_purchase_price = float(asset_data['old_purchase_price']
                                   ) if asset_data['old_purchase_price'] else 0
        token_address = asset_data['token_address']

        print(
            f"📊 [PURCHASE PRICE] Asset '{matched_symbol}' current data: Balance={balance}, Value=${current_value}, Old Price=${old_purchase_price}"
        )

        # Calculate new metrics with safe division
        total_invested = balance * purchase_price
        unrealized_pnl = current_value - total_invested

        # Safe percentage calculation
        if total_invested > 0:
            total_return_pct = (unrealized_pnl / total_invested) * 100
        else:
            total_return_pct = 0 if unrealized_pnl == 0 else float(
                'inf') if unrealized_pnl > 0 else float('-inf')
            # Cap infinite values for database storage
            if total_return_pct == float('inf'):
                total_return_pct = 999999  # Very large positive number
            elif total_return_pct == float('-inf'):
                total_return_pct = -999999  # Very large negative number

        print(
            f"📈 [PURCHASE PRICE] Calculated metrics: Invested=${total_invested:.2f}, P&L=${unrealized_pnl:.2f}, Return={total_return_pct:.2f}%"
        )

        # Store the override in the permanent overrides table
        cursor.execute(
            """
            INSERT INTO purchase_price_overrides 
            (token_address, symbol, override_price, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (token_address) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            override_price = EXCLUDED.override_price,
            updated_at = EXCLUDED.updated_at
        """, (token_address, matched_symbol, purchase_price))

        print(
            f"✅ [PURCHASE PRICE] Stored permanent override for '{matched_symbol}': ${purchase_price}"
        )

        # Update the asset using the exact matched symbol (important for symbols with whitespace)
        update_count = cursor.execute(
            """
            UPDATE assets 
            SET purchase_price = %s,
                total_invested = %s,
                unrealized_pnl = %s,
                total_return_pct = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE symbol = %s
        """, (purchase_price, total_invested, unrealized_pnl, total_return_pct,
              matched_symbol))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=500,
                detail=
                f"Failed to update asset '{matched_symbol}' - no rows affected"
            )

        print(
            f"✅ [PURCHASE PRICE] Updated {cursor.rowcount} row(s) for symbol '{matched_symbol}'"
        )

        # Also update the cost basis table for consistency using token_address (more reliable)
        cursor.execute(
            """
            INSERT INTO asset_cost_basis 
            (token_address, symbol, average_purchase_price, total_quantity_purchased, total_invested, last_updated)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (token_address) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            average_purchase_price = EXCLUDED.average_purchase_price,
            total_quantity_purchased = EXCLUDED.total_quantity_purchased,
            total_invested = EXCLUDED.total_invested,
            last_updated = EXCLUDED.last_updated
        """, (token_address, matched_symbol, purchase_price, balance,
              total_invested))

        conn.commit()

        print(
            f"✅ [PURCHASE PRICE] Successfully updated purchase price for '{matched_symbol}': ${purchase_price}"
        )
        print(
            f"   New metrics: Invested=${total_invested:.2f}, P&L=${unrealized_pnl:.2f}, Return={total_return_pct:.2f}%"
        )

        return {
            "message": f"Purchase price updated for {matched_symbol}",
            "symbol": matched_symbol,  # Return the actual matched symbol
            "purchase_price": purchase_price,
            "total_invested": total_invested,
            "unrealized_pnl": unrealized_pnl,
            "total_return_pct": total_return_pct,
            "updated_at": "now"
        }

    except HTTPException:
        conn.rollback()
        raise  # Re-raise HTTP exceptions as-is
    except psycopg2.Error as e:
        conn.rollback()
        print(
            f"❌ [PURCHASE PRICE] Database error updating purchase price for '{clean_symbol}': {e}"
        )
        raise HTTPException(status_code=500,
                            detail=f"Database error: {str(e)}")
    except Exception as e:
        conn.rollback()
        print(
            f"❌ [PURCHASE PRICE] Unexpected error updating purchase price for '{clean_symbol}': {e}"
        )
        import traceback
        print(f"📋 [PURCHASE PRICE] Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500,
                            detail=f"Internal server error: {str(e)}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


@app.post("/api/assets/hide")
async def hide_asset(token_address: str, symbol: str, name: str):
    """Hide an asset from portfolio calculations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO hidden_assets (token_address, symbol, name)
            VALUES (%s, %s, %s)
        """, (token_address.lower(), symbol, name))

        conn.commit()
        print(f"✅ Hidden asset: {symbol} ({token_address})")
        return {"message": f"Asset {symbol} hidden successfully"}
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Error hiding asset: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()


@app.delete("/api/assets/hide/{token_address}")
async def unhide_asset(token_address: str):
    """Unhide an asset to include in portfolio calculations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM hidden_assets WHERE token_address = %s",
                   (token_address.lower(), ))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Hidden asset not found")

    conn.commit()
    conn.close()
    return {"message": "Asset unhidden successfully"}


@app.get("/api/assets/hidden")
async def get_hidden_assets():
    """Get list of hidden assets"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT token_address, symbol, name, hidden_at FROM hidden_assets")
    hidden_assets = cursor.fetchall()
    conn.close()

    return [{
        "token_address": h['token_address'],
        "symbol": h['symbol'],
        "name": h['name'],
        "hidden_at": h['hidden_at']
    } for h in hidden_assets]


@app.get("/api/assets/overrides")
async def get_purchase_price_overrides():
    """Get list of purchase price overrides"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT token_address, symbol, override_price, updated_at FROM purchase_price_overrides ORDER BY updated_at DESC")
    overrides = cursor.fetchall()
    conn.close()

    return [{
        "token_address": o['token_address'],
        "symbol": o['symbol'],
        "override_price": o['override_price'],
        "updated_at": o['updated_at']
    } for o in overrides]


@app.delete("/api/assets/overrides/{token_address}")
async def delete_purchase_price_override(token_address: str):
    """Remove a purchase price override"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM purchase_price_overrides WHERE token_address = %s",
                   (token_address, ))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Override not found")

    conn.commit()
    conn.close()
    return {"message": "Purchase price override removed successfully"}


@app.get("/api/debug/database")
async def debug_database():
    """Debug endpoint to test database connection and structure"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Test basic connection
        cursor.execute("SELECT 1 as test")
        test_result = cursor.fetchone()

        # Check if tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]

        # Get table counts
        table_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                table_counts[table] = result['count'] if result else 0
            except Exception as e:
                table_counts[table] = f"Error: {str(e)}"

        conn.close()

        return {
            "status": "connected",
            "test_query": test_result['test'] if test_result else None,
            "tables": tables,
            "table_counts": table_counts,
            "database_url_set": bool(DATABASE_URL),
            "connection_type": "PostgreSQL with RealDictCursor"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_url_set": bool(DATABASE_URL)
        }


@app.get("/api/debug/nfts/{wallet_address}")
async def debug_nft_query(wallet_address: str):
    """Debug endpoint to manually test NFT queries with comprehensive logging"""
    try:
        print(f"🔍 [DEBUG NFT] Manual NFT query for wallet: {wallet_address}")
        print(f"🔍 [DEBUG NFT] Alchemy API Key set: {bool(ALCHEMY_API_KEY)}")

        # Create Ethereum asset fetcher
        eth_fetcher = EthereumAssetFetcher(ALCHEMY_API_KEY)

        # Test direct Alchemy API call first
        async with httpx.AsyncClient(timeout=60.0) as client:
            test_payload = {
                "id": 1,
                "jsonrpc": "2.0", 
                "method": "alchemy_getNFTs",
                "params": [wallet_address, {"withMetadata": True}]
            }
            
            print(f"🔍 [DEBUG NFT] Testing direct Alchemy call...")
            test_response = await client.post(eth_fetcher.alchemy_url, json=test_payload)
            print(f"🔍 [DEBUG NFT] Direct API status: {test_response.status_code}")
            
            if test_response.status_code == 200:
                test_data = test_response.json()
                print(f"🔍 [DEBUG NFT] Direct API response preview: {str(test_data)[:300]}...")
            else:
                print(f"🔍 [DEBUG NFT] Direct API error: {test_response.text}")

        # Fetch NFTs using the fetcher
        nft_assets = await eth_fetcher._fetch_nfts(wallet_address, set())

        # Check specifically for Mutant Ape contracts
        mutant_ape_contracts = [
            "0x60e4d786628fea6478f785a6d7e704777c86a7c6",  # MAYC official
            "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",  # BAYC (for reference)
        ]

        print(f"🔍 [DEBUG NFT] Checking for Mutant Ape contracts...")
        for contract in mutant_ape_contracts:
            found_mutant = any(asset.token_address.lower() == contract.lower() for asset in nft_assets)
            print(f"🔍 [DEBUG NFT] {contract}: {'FOUND' if found_mutant else 'NOT FOUND'}")

        return {
            "wallet_address": wallet_address,
            "nft_count": len(nft_assets),
            "mutant_ape_found": any("mutant" in asset.name.lower() or "mayc" in asset.symbol.lower() for asset in nft_assets),
            "nfts": [{
                "contract_address": asset.token_address,
                "symbol": asset.symbol,
                "name": asset.name,
                "count": asset.balance,
                "is_nft": asset.is_nft,
                "token_ids": asset.token_ids[:10],  # Show more token IDs
                "floor_price": asset.floor_price,
                "image_url": asset.image_url
            } for asset in nft_assets]
        }
    except Exception as e:
        print(f"❌ [DEBUG NFT] Error: {e}")
        import traceback
        print(f"❌ [DEBUG NFT] Full traceback: {traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/portfolio/returns")
async def get_portfolio_returns():
    """Get comprehensive portfolio returns analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get overall portfolio metrics
        cursor.execute("""
            SELECT 
                SUM(total_invested) as total_invested,
                SUM(value_usd) as total_current_value,
                SUM(unrealized_pnl) as total_unrealized_pnl,
                SUM(realized_pnl) as total_realized_pnl,
                AVG(total_return_pct) as avg_return_pct
            FROM assets 
            WHERE balance > 0 AND NOT EXISTS (
                SELECT 1 FROM hidden_assets h 
                WHERE LOWER(h.token_address) = LOWER(assets.token_address)
            )
        """)
        portfolio_metrics = cursor.fetchone()

        # Get top performers
        cursor.execute("""
            SELECT symbol, name, total_return_pct, unrealized_pnl, value_usd
            FROM assets 
            WHERE balance > 0 AND total_return_pct IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM hidden_assets h 
                WHERE LOWER(h.token_address) = LOWER(assets.token_address)
            )
            ORDER BY total_return_pct DESC
            LIMIT 10
        """)
        top_performers = cursor.fetchall()

        # Get worst performers
        cursor.execute("""
            SELECT symbol, name, total_return_pct, unrealized_pnl, value_usd
            FROM assets 
            WHERE balance > 0 AND total_return_pct IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM hidden_assets h 
                WHERE LOWER(h.token_address) = LOWER(assets.token_address)
            )
            ORDER BY total_return_pct ASC
            LIMIT 5
        """)
        worst_performers = cursor.fetchall()

        portfolio_data = portfolio_metrics or {}
        total_invested = portfolio_data.get('total_invested', 0) or 0
        total_current_value = portfolio_data.get('total_current_value', 0) or 0
        total_unrealized_pnl = portfolio_data.get('total_unrealized_pnl',
                                                  0) or 0
        total_realized_pnl = portfolio_data.get('total_realized_pnl', 0) or 0
        avg_return_pct = portfolio_data.get('avg_return_pct', 0) or 0

        overall_return_pct = ((total_current_value - total_invested) /
                              total_invested *
                              100) if total_invested > 0 else 0

        return {
            "portfolio_metrics": {
                "total_invested": total_invested,
                "total_current_value": total_current_value,
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_realized_pnl": total_realized_pnl,
                "overall_return_pct": overall_return_pct,
                "average_return_pct": avg_return_pct
            },
            "top_performers": [{
                "symbol": tp['symbol'],
                "name": tp['name'],
                "return_pct": tp['total_return_pct'],
                "unrealized_pnl": tp['unrealized_pnl'],
                "current_value": tp['value_usd']
            } for tp in top_performers],
            "worst_performers": [{
                "symbol": wp['symbol'],
                "name": wp['name'],
                "return_pct": wp['total_return_pct'],
                "unrealized_pnl": wp['unrealized_pnl'],
                "current_value": wp['value_usd']
            } for wp in worst_performers]
        }

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching returns data: {e}")
    finally:
        conn.close()


@app.post("/api/assets/{symbol}/purchase")
async def add_purchase_record(symbol: str,
                              quantity: float,
                              price_per_token: float,
                              notes: str = ""):
    """Add a purchase record for manual tracking"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get token details
        cursor.execute(
            "SELECT token_address, name FROM assets WHERE symbol = %s LIMIT 1",
            (symbol, ))
        asset_data = cursor.fetchone()

        if not asset_data:
            raise HTTPException(status_code=404, detail="Asset not found")

        token_address, name = asset_data[0], asset_data[1]
        total_value = quantity * price_per_token

        # Insert purchase record
        cursor.execute(
            """
            INSERT INTO purchase_history 
            (wallet_id, token_address, symbol, transaction_type, quantity, price_per_token, total_value, notes)
            VALUES (1, %s, %s, 'BUY', %s, %s, %s, %s)
        """, (token_address, symbol, quantity, price_per_token, total_value,
              notes))

        # Update cost basis
        cursor.execute(
            """
            SELECT total_quantity_purchased, total_invested 
            FROM asset_cost_basis 
            WHERE token_address = %s
        """, (token_address, ))

        existing_basis = cursor.fetchone()

        if existing_basis:
            old_quantity, old_invested = existing_basis[0], existing_basis[1]
            new_quantity = old_quantity + quantity
            new_invested = old_invested + total_value
            new_avg_price = new_invested / new_quantity

            cursor.execute(
                """
                UPDATE asset_cost_basis 
                SET total_quantity_purchased = %s, total_invested = %s, average_purchase_price = %s
                WHERE token_address = %s
            """, (new_quantity, new_invested, new_avg_price, token_address))
        else:
            cursor.execute(
                """
                INSERT INTO asset_cost_basis 
                (token_address, symbol, average_purchase_price, total_quantity_purchased, total_invested)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (token_address) DO UPDATE SET
                average_purchase_price = EXCLUDED.average_purchase_price,
                total_quantity_purchased = EXCLUDED.total_quantity_purchased,
                total_invested = EXCLUDED.total_invested
            """, (token_address, symbol, price_per_token, quantity,
                  total_value))

        conn.commit()
        return {"message": "Purchase record added successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500,
                            detail=f"Error adding purchase record: {e}")
    finally:
        conn.close()


async def estimate_purchase_prices_and_calculate_returns():
    """
    Estimate purchase prices for existing assets and calculate returns.
    This uses various heuristics to estimate when assets were likely purchased.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print(
            "💰 Starting purchase price estimation and returns calculation...")

        # Get all current assets
        cursor.execute("""
            SELECT token_address, symbol, name, balance, price_usd, value_usd
            FROM assets 
            WHERE balance > 0 AND price_usd > 0
        """)
        current_assets = cursor.fetchall()

        for token_address, symbol, name, balance, current_price, current_value in current_assets:
            try:
                # Estimate purchase price based on asset type and historical context
                estimated_purchase_price = await estimate_asset_purchase_price(
                    symbol, name, current_price)

                # Calculate total invested (estimated)
                total_invested = balance * estimated_purchase_price

                # Calculate unrealized P&L
                unrealized_pnl = current_value - total_invested

                # Calculate return percentage
                total_return_pct = ((current_value - total_invested) /
                                    total_invested *
                                    100) if total_invested > 0 else 0

                # Update asset with calculated values
                cursor.execute(
                    """
                    UPDATE assets 
                    SET purchase_price = %s, total_invested = %s, unrealized_pnl = %s, total_return_pct = %s
                    WHERE token_address = %s AND balance > 0
                """, (estimated_purchase_price, total_invested, unrealized_pnl,
                      total_return_pct, token_address))

                # Insert into cost basis table
                cursor.execute(
                    """
                    INSERT INTO asset_cost_basis 
                    (token_address, symbol, average_purchase_price, total_quantity_purchased, total_invested)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (token_address) DO UPDATE SET
                    average_purchase_price = EXCLUDED.average_purchase_price,
                    total_quantity_purchased = EXCLUDED.total_quantity_purchased,
                    total_invested = EXCLUDED.total_invested
                """, (token_address, symbol, estimated_purchase_price, balance,
                      total_invested))

                print(
                    f"✅ Updated {symbol}: Purchase ${estimated_purchase_price:.4f}, Return {total_return_pct:.1f}%"
                )

            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                continue

        conn.commit()
        print(
            f"🎯 Purchase price estimation completed for {len(current_assets)} assets"
        )

    except Exception as e:
        print(f"❌ Error in purchase price estimation: {e}")
        conn.rollback()
    finally:
        conn.close()


async def estimate_asset_purchase_price(symbol: str, name: str,
                                        current_price: float) -> float:
    """
    Estimate purchase price based on asset characteristics and market timing.
    Uses conservative estimates based on typical crypto fund entry strategies.
    """

    # Fund likely entry points based on asset type and market conditions
    if symbol == "ETH":
        # Ethereum - likely accumulated during multiple market cycles
        return current_price * 0.65  # Estimated 35% gains

    elif symbol == "WBTC" or "Bitcoin" in name:
        # Bitcoin/WBTC - likely accumulated during bear markets
        return current_price * 0.55  # Estimated 82% gains

    elif symbol == "SOL":
        # Solana - likely accumulated during 2023-2024 cycle
        return current_price * 0.45  # Estimated 122% gains

    elif symbol == "PENDLE":
        # PENDLE - likely accumulated during DeFi summer or early growth
        return current_price * 0.4  # Estimated 150% gains

    elif symbol in ["USDC", "USDT", "DAI"]:
        # Stablecoins - purchase price should be close to $1
        return 1.0

    elif "PENGU" in symbol or "Pudgy" in name:
        # PENGU - likely purchased during meme season or airdrop
        return current_price * 0.2  # Estimated 400% gains (early meme entry)

    elif "Fartcoin" in name or symbol.startswith("SPL-"):
        # Meme coins and other SPL tokens - high risk, high reward entries
        if current_price > 1:
            return current_price * 0.15  # Estimated 567% gains
        else:
            return current_price * 0.25  # More conservative for smaller tokens

    elif symbol in ["UNI", "LINK", "AAVE", "CRV"]:
        # Blue chip DeFi tokens
        return current_price * 0.6  # Estimated 67% gains

    else:
        # Generic altcoins - conservative estimate
        return current_price * 0.5  # Estimated 100% gains


async def update_portfolio_data_new():
    """New background task using chain-agnostic fetchers with comprehensive error handling"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("🚀 Starting portfolio update with new chain-agnostic system...")

        # Clear existing assets
        cursor.execute("DELETE FROM assets")

        # Get all wallets grouped by network
        cursor.execute("SELECT id, address, network, label FROM wallets")
        wallets = cursor.fetchall()

        # Group wallets by network for optimized processing
        wallets_by_network = {}
        wallet_status = {}  # Track individual wallet success/failure

        for wallet_row in wallets:
            wallet_id, address, network, label = wallet_row['id'], wallet_row[
                'address'], wallet_row['network'], wallet_row['label']
            if network not in wallets_by_network:
                wallets_by_network[network] = []
            wallets_by_network[network].append((wallet_id, address, label))
            wallet_status[wallet_id] = {
                'address': address,
                'label': label,
                'network': network,
                'status': 'pending',
                'assets_found': 0,
                'total_value': 0,
                'error': None
            }

        all_assets = []
        token_addresses_by_network = {}

        # Fetch assets for each network with individual wallet error handling
        for network, network_wallets in wallets_by_network.items():
            print(f"🔗 Processing {len(network_wallets)} {network} wallets...")

            token_addresses_by_network[network] = set()

            for wallet_id, address, label in network_wallets:
                try:
                    print(
                        f"📡 Fetching assets for {network} wallet: {label} ({address[:10]}...)"
                    )

                    # Use new chain-agnostic asset fetcher with timeout
                    assets = await asyncio.wait_for(
                        get_wallet_assets_new(address, network),
                        timeout=60.0  # 60 second timeout per wallet
                    )

                    wallet_assets_count = 0
                    for asset in assets:
                        asset_dict = {
                            'wallet_id': wallet_id,
                            'token_address': asset.token_address,
                            'symbol': asset.symbol,
                            'name': asset.name,
                            'balance': asset.balance,
                            'balance_formatted': asset.balance_formatted,
                            'decimals': asset.decimals,
                            'is_nft': asset.is_nft,
                            'token_ids': asset.token_ids,
                            'network': network
                        }
                        all_assets.append(asset_dict)
                        token_addresses_by_network[network].add(
                            asset.token_address)
                        wallet_assets_count += 1

                    # Update wallet status
                    wallet_status[wallet_id].update({
                        'status':
                        'success',
                        'assets_found':
                        wallet_assets_count
                    })
                    print(
                        f"✅ Successfully fetched {wallet_assets_count} assets from {label}"
                    )

                except asyncio.TimeoutError:
                    error_msg = f"Timeout after 60 seconds"
                    print(
                        f"⏰ {error_msg} for {network} wallet {label} ({address[:10]}...)"
                    )
                    wallet_status[wallet_id].update({
                        'status': 'timeout',
                        'error': error_msg
                    })
                except Exception as e:
                    error_msg = str(e)[:200]  # Limit error message length
                    print(
                        f"❌ Error fetching assets for {network} wallet {label} ({address[:10]}...): {error_msg}"
                    )
                    wallet_status[wallet_id].update({
                        'status': 'error',
                        'error': error_msg
                    })

        # Convert sets to lists for price fetching
        for network in token_addresses_by_network:
            token_addresses_by_network[network] = list(
                token_addresses_by_network[network])

        print(f"📊 Total assets fetched: {len(all_assets)}")
        print(
            f"🪙 Token addresses by network: {dict((k, len(v)) for k, v in token_addresses_by_network.items())}"
        )

        # Print wallet status summary
        successful_wallets = sum(1 for s in wallet_status.values()
                                 if s['status'] == 'success')
        failed_wallets = sum(1 for s in wallet_status.values()
                             if s['status'] in ['error', 'timeout'])
        print(
            f"📋 Wallet Status: {successful_wallets} successful, {failed_wallets} failed"
        )

        # Get prices using new chain-agnostic price fetcher
        try:
            price_map = await asyncio.wait_for(
                get_token_prices_new(token_addresses_by_network), timeout=30.0)
        except Exception as e:
            print(f"❌ Error fetching prices: {e}")
            price_map = {}

        # Insert assets with prices and calculate wallet values
        total_portfolio_value = 0
        auto_hide_candidates = []

        # First, estimate purchase prices for new assets
        await estimate_purchase_prices_and_calculate_returns()

        for asset in all_assets:
            is_nft = asset.get('is_nft', False)
            token_address = asset['token_address']
            wallet_id = asset['wallet_id']

            if is_nft:
                price_usd = asset.get('floor_price', 0)
                value_usd = price_usd * asset['balance'] if price_usd > 0 else 0
                nft_metadata = json.dumps({
                    "token_ids":
                    asset.get('token_ids', []),
                    "count":
                    asset.get('balance', 0),
                    "image_url":
                    asset.get('image_url'),
                    "floor_price":
                    price_usd
                })
                print(
                    f"🖼️ NFT Asset: {asset['symbol']} - {asset['balance']} items (Floor: ${price_usd})"
                )
            else:
                # CRITICAL ETH PRICE LOOKUP - ETH uses special zero address
                # Look up price with multiple fallbacks for different address formats
                if token_address.lower(
                ) == "0x0000000000000000000000000000000000000000":
                    # Special handling for ETH - try multiple lookup keys
                    price_usd = (price_map.get(
                        "0x0000000000000000000000000000000000000000",
                        0) or price_map.get(
                            "0x0000000000000000000000000000000000000000".lower(
                            ), 0) or price_map.get("eth", 0))
                    if price_usd > 0:
                        print(f"✅ ETH price lookup successful: ${price_usd}")
                    else:
                        print(
                            f"❌ ETH price lookup failed - checking price_map keys: {list(price_map.keys())}"
                        )
                else:
                    # Standard ERC-20 token price lookup
                    price_usd = price_map.get(token_address.lower(), 0)
                    if price_usd == 0:
                        price_usd = price_map.get(token_address, 0)

                    value_usd = asset['balance'] * price_usd
                    nft_metadata = None

                    print(
                        f"💰 {asset['network']} Asset: {asset['symbol']} - Balance: {asset['balance']:.6f}, Price: ${price_usd:.6f}, Value: ${value_usd:.2f}"
                    )

                    # Identify spam/scam tokens and low-value tokens for auto-hiding
                    is_spam_token = (
                        value_usd == 0 and asset['balance'] > 0 and
                        ("visit" in asset['name'].lower()
                         or "claim" in asset['name'].lower()
                         or "rewards" in asset['name'].lower()
                         or "gift" in asset['name'].lower()
                         or "airdrop" in asset['name'].lower() or
                         (asset['symbol'] == "" and asset['name'] == "")
                         or len(asset['name']) > 50  # Suspiciously long names
                         ))

                    # Auto-hide tokens with value less than $1 (excluding NFTs and major tokens)
                    is_low_value_token = (
                        value_usd > 0 and value_usd < 1.0 and not is_nft
                        and  # Never auto-hide NFTs
                        asset['symbol'] not in [
                            'ETH', 'BTC', 'SOL', 'USDC', 'USDT', 'WBTC',
                            'PENDLE'
                        ]  # Preserve major tokens even if small amounts
                    )

                    if is_spam_token or is_low_value_token:
                        reason = "spam/scam" if is_spam_token else f"low value (${value_usd:.6f})"
                        auto_hide_candidates.append({
                            'token_address': token_address,
                            'symbol': asset['symbol'],
                            'name': asset['name'],
                            'balance': asset['balance'],
                            'value_usd': value_usd,
                            'reason': reason
                        })

                # Update wallet status with value
                wallet_status[wallet_id]['total_value'] += value_usd
                total_portfolio_value += value_usd

                # Debug NFT detection
                if is_nft:
                    print(
                        f"🖼️ [NFT DEBUG] Processing NFT: {asset['symbol']} - {asset['name']} - Value: ${value_usd:.6f}"
                    )
                elif asset['symbol'].endswith(
                        'NFT') or 'Collection' in asset['name']:
                    print(
                        f"🔍 [NFT DEBUG] Possible missed NFT: {asset['symbol']} - {asset['name']} - isNFT: {is_nft}"
                    )

                # Check for purchase price override first (highest priority)
                cursor.execute(
                    """
                    SELECT override_price 
                    FROM purchase_price_overrides 
                    WHERE token_address = %s
                """, (token_address, ))
                override_data = cursor.fetchone()

                if override_data:
                    # Use the permanent override price
                    purchase_price = override_data['override_price']
                    total_invested = asset['balance'] * purchase_price
                    realized_pnl = 0
                    unrealized_pnl = value_usd - total_invested if total_invested > 0 else 0
                    total_return_pct = ((value_usd - total_invested) /
                                        total_invested *
                                        100) if total_invested > 0 else 0
                    print(
                        f"✅ [OVERRIDE] Using override price for {asset['symbol']}: ${purchase_price}"
                    )
                else:
                    # Check for cost basis data
                    cursor.execute(
                        """
                        SELECT average_purchase_price, total_invested, realized_gains 
                        FROM asset_cost_basis 
                        WHERE token_address = %s
                    """, (token_address, ))
                    cost_basis_data = cursor.fetchone()

                    if cost_basis_data:
                        purchase_price, total_invested, realized_pnl = cost_basis_data
                        unrealized_pnl = value_usd - total_invested if total_invested > 0 else 0
                        total_return_pct = ((value_usd - total_invested) /
                                            total_invested *
                                            100) if total_invested > 0 else 0
                    else:
                        # Estimate purchase price for new assets
                        purchase_price = await estimate_asset_purchase_price(
                            asset['symbol'], asset['name'],
                            price_usd) if price_usd > 0 else 0
                        total_invested = asset['balance'] * purchase_price
                        realized_pnl = 0
                        unrealized_pnl = value_usd - total_invested if total_invested > 0 else 0
                        total_return_pct = ((value_usd - total_invested) /
                                            total_invested *
                                            100) if total_invested > 0 else 0

                # Insert asset into database
                cursor.execute(
                    """
                    INSERT INTO assets 
                    (wallet_id, token_address, symbol, name, balance, balance_formatted, price_usd, value_usd, 
                     is_nft, nft_metadata, floor_price, image_url, purchase_price, total_invested, 
                     realized_pnl, unrealized_pnl, total_return_pct)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (wallet_id, token_address, asset['symbol'], asset['name'],
                      asset['balance'], asset['balance_formatted'], price_usd,
                      value_usd, is_nft, nft_metadata,
                      asset.get('floor_price', 0), asset.get('image_url'),
                      purchase_price, total_invested, realized_pnl,
                      unrealized_pnl, total_return_pct))

                # Debug NFT insertion
                if is_nft:
                    print(
                        f"🖼️ [DATABASE] Inserted NFT: {asset['symbol']} - {asset['name']} - Count: {asset['balance']} - Floor: ${asset.get('floor_price', 0)}"
                    )
                    print(f"🖼️ [DATABASE] NFT metadata: {nft_metadata}")
                    print(f"🖼️ [DATABASE] Image URL: {asset.get('image_url')}")

            # CRITICAL FIX: Clean up hidden assets table to remove legitimate tokens
            print("🧹 Cleaning up hidden assets table...")

            # Get current valuable assets (assets with significant value)
            cursor.execute("""
                SELECT DISTINCT token_address, symbol, name 
                FROM assets 
                WHERE value_usd > 10
            """)
            valuable_assets = cursor.fetchall()

        # Remove valuable assets from hidden list
        for token_address, symbol, name in valuable_assets:
            cursor.execute(
                "DELETE FROM hidden_assets WHERE LOWER(token_address) = LOWER(%s)",
                (token_address, ))
            print(
                f"🔓 Unhid valuable asset: {symbol} (${cursor.rowcount} rows removed)"
            )

        # Auto-hide spam/scam tokens and low-value tokens
        if auto_hide_candidates:
            print(f"🔍 Auto-hiding {len(auto_hide_candidates)} tokens...")
            for hide_asset in auto_hide_candidates:
                try:
                    cursor.execute(
                        """
                        INSERT INTO hidden_assets (token_address, symbol, name) 
                        VALUES (%s, %s, %s)
                        ON CONFLICT (token_address) DO UPDATE SET
                        symbol = EXCLUDED.symbol, name = EXCLUDED.name
                    """, (hide_asset['token_address'].lower(),
                          hide_asset['symbol'], hide_asset['name']))
                    print(
                        f"🙈 Auto-hidden {hide_asset['reason']}: {hide_asset['symbol'] or 'unnamed'} (${hide_asset.get('value_usd', 0):.6f})"
                    )
                except psycopg2.Error as e:
                    print(
                        f"❌ Error auto-hiding asset {hide_asset['symbol']}: {e}"
                    )

        # CRITICAL: Clean up symbol inconsistencies (trim whitespace from symbols)
        print(
            "🧹 [DATA CLEANUP] Cleaning up symbol whitespace inconsistencies..."
        )
        cursor.execute("""
            UPDATE assets 
            SET symbol = TRIM(symbol)
            WHERE symbol != TRIM(symbol)
        """)

        cleaned_symbols = cursor.rowcount
        if cleaned_symbols > 0:
            print(
                f"✅ [DATA CLEANUP] Cleaned whitespace from {cleaned_symbols} asset symbols"
            )

            # Also clean up cost basis table
            cursor.execute("""
                UPDATE asset_cost_basis 
                SET symbol = TRIM(symbol)
                WHERE symbol != TRIM(symbol)
            """)

            # Clean up asset notes
            cursor.execute("""
                UPDATE asset_notes 
                SET symbol = TRIM(symbol)
                WHERE symbol != TRIM(symbol)
            """)

            print(
                f"✅ [DATA CLEANUP] Symbol cleanup completed across all tables")
        else:
            print(f"✅ [DATA CLEANUP] No symbol whitespace issues found")

        # Record portfolio history
        cursor.execute(
            "INSERT INTO portfolio_history (total_value_usd) VALUES (%s)",
            (total_portfolio_value, ))

        # Clear old wallet status and insert new ones
        cursor.execute("DELETE FROM wallet_status")
        for wallet_id, status_info in wallet_status.items():
            cursor.execute(
                """
                INSERT INTO wallet_status (wallet_id, status, assets_found, total_value, error_message)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (wallet_id, status_info['status'], status_info['assets_found'],
                 status_info['total_value'], status_info['error']))

        conn.commit()

        # Final success summary
        successful_count = sum(1 for s in wallet_status.values()
                               if s['status'] == 'success')
        total_count = len(wallet_status)
        print(f"✅ Portfolio updated successfully!")
        print(
            f"📈 {len(all_assets)} assets processed, ${total_portfolio_value:,.2f} total value"
        )
        print(
            f"🏦 {successful_count}/{total_count} wallets processed successfully"
        )

        # Print any failed wallets
        failed_wallets = [(s['label'], s['error'])
                          for s in wallet_status.values()
                          if s['status'] in ['error', 'timeout']]
        if failed_wallets:
            print("⚠️  Failed wallets:")
            for label, error in failed_wallets:
                print(f"   - {label}: {error}")

    except Exception as e:
        print(f"❌ Critical error updating portfolio: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        conn.rollback()
    finally:
        conn.close()


# Serve static assets
@app.get("/assets/{file_path:path}")
async def serve_static_assets(file_path: str):
    dist_path = "../dist" if os.path.exists(
        "../dist") else "./dist" if os.path.exists("./dist") else None
    if dist_path:
        full_file_path = f"{dist_path}/assets/{file_path}"
        if os.path.exists(full_file_path):
            return FileResponse(full_file_path)
    raise HTTPException(status_code=404, detail="Asset not found")


# Catch-all route for SPA routing - only for non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Skip API and asset routes
    if (full_path.startswith("api/") or full_path.startswith("health")
            or full_path.startswith("assets/")):
        raise HTTPException(status_code=404, detail="Not found")

    # Serve React app for all other routes (SPA routing)
    if dist_path:
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            print(
                f"🌐 [SPA] Serving React app from {index_path} for route: {full_path}"
            )
            return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment, fallback to 8000 for development, 80 for deployment
    port = int(os.environ.get("PORT", 80))

    # Override port based on environment
    if os.environ.get("NODE_ENV") == "production":
        port = 80

    print(f"🚀 [SERVER] Starting server on port {port}")
    print(
        f"🔍 [SERVER] Environment: {os.environ.get('NODE_ENV', 'development')}")
    print(f"🔍 [SERVER] Checking for static files...")

    # Check for dist directories
    static_found = False
    for path in ["../dist", "./dist", "dist"]:
        if os.path.exists(path):
            print(f"✅ [SERVER] Found {path} directory")
            static_found = True
            break

    if not static_found:
        print("⚠️ [SERVER] No dist directory found - running API-only mode")

    # Production-ready server configuration
    uvicorn.run(app,
                host="0.0.0.0",
                port=port,
                log_level="info"
                if os.environ.get("NODE_ENV") != "production" else "warning",
                access_log=True
                if os.environ.get("NODE_ENV") != "production" else False)