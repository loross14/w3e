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
                                application_name="w3e")
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


class NFTData:
    def __init__(self,
                 contract_address: str,
                 symbol: str,
                 name: str,
                 item_count: int,
                 token_ids: List[str] = None,
                 floor_price_usd: float = 0,
                 image_url: str = None):
        self.contract_address = contract_address
        self.symbol = symbol
        self.name = name
        self.item_count = item_count
        self.token_ids = token_ids or []
        self.floor_price_usd = floor_price_usd
        self.image_url = image_url


# Abstract base classes for chain-specific implementations
class AssetFetcher(ABC):

    @abstractmethod
    async def fetch_assets(self, wallet_address: str,
                           hidden_addresses: set) -> List[AssetData]:
        pass

    @abstractmethod
    async def fetch_nfts(self, wallet_address: str, hidden_addresses: set) -> List[NFTData]:
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

    def _is_legitimate_nft(self, contract_name: str,
                           contract_address: str) -> bool:
        """
        Validate if an NFT collection is legitimate based on name and contract address.
        Returns True for known legitimate collections, False for obvious spam.
        """
        if not contract_name:
            return False

        contract_name_lower = contract_name.lower()
        contract_address_lower = contract_address.lower()

        # Known legitimate collections
        legitimate_collections = [
            "mutant ape yacht club", "mayc", "boredapeyachtclub",
            "bored ape yacht club", "bayc", "cryptopunks", "azuki", "doodles",
            "pudgypenguins", "0n1 force", "cool cats"
        ]

        # Known legitimate contract addresses
        legitimate_contracts = [
            "0x60e4d786628fea6478f785a6d7e704777c86a7c6",  # MAYC
            "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",  # BAYC
            "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb",  # CryptoPunks
            "0xed5af388653567af2f388e6224dc7c4b3241c544",  # Azuki
        ]

        # Check for legitimate collections
        is_legitimate = (any(legit in contract_name_lower
                             for legit in legitimate_collections)
                         or contract_address_lower
                         in [addr.lower() for addr in legitimate_contracts])

        # Spam indicators
        spam_indicators = [
            "visit ", "claim ", "access ", ".com", ".net", ".org", "award",
            "gift", "airdrop", "mysterybox", "recipient", "rewards"
        ]

        is_spam = any(indicator in contract_name_lower
                      for indicator in spam_indicators)

        # Return True only if legitimate and not spam
        return is_legitimate or (not is_spam and len(contract_name) >= 3)

    def _validate_nft_data(self, nft_data: dict) -> bool:
        """
        Validate NFT data structure to ensure it has required fields.
        """
        try:
            contract = nft_data.get("contract", {})
            return (isinstance(contract, dict) and contract.get("address")
                    and contract.get("name")
                    and nft_data.get("tokenId") is not None)
        except Exception:
            return False

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

        except Exception as e:
            print(f"❌ Ethereum asset fetching error: {e}")

        return assets

    async def fetch_nfts(self, wallet_address: str, hidden_addresses: set) -> List[NFTData]:
        nfts = []

        try:
            print(f"🖼️ [ETH NFT] Starting NFT query for wallet: {wallet_address[:10]}...")

            api_key = self.alchemy_url.split("/v2/")[-1]
            nft_url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api_key}/getNFTsForOwner"

            params = {
                "owner": wallet_address,
                "withMetadata": "true",
                "pageSize": "100"
            }

            import requests

            response = requests.get(nft_url, params=params, headers={"accept": "application/json"}, timeout=30.0)

            if response.status_code != 200:
                print(f"❌ [ETH NFT] API failed with status: {response.status_code}")
                return nfts

            data = response.json()

            if "error" in data:
                print(f"❌ [ETH NFT] API error: {data['error']}")
                return nfts

            owned_nfts = data.get("ownedNfts", [])

            if not owned_nfts:
                print(f"🖼️ [ETH NFT] No NFTs found for wallet")
                return nfts

            print(f"🖼️ [ETH NFT] Found {len(owned_nfts)} NFTs, processing collections...")

            # Group NFTs by collection
            collections = {}

            for nft in owned_nfts:
                try:
                    if not self._validate_nft_data(nft):
                        continue

                    contract = nft.get("contract", {})
                    contract_address = contract.get("address", "").lower()
                    contract_name = contract.get("name", "")

                    if not contract_address:
                        continue

                    if contract_address in [addr.lower() for addr in hidden_addresses]:
                        continue

                    if not self._is_legitimate_nft(contract_name, contract_address):
                        continue

                    if contract_address not in collections:
                        collections[contract_address] = {
                            "name": contract.get("name", "Unknown Collection"),
                            "symbol": contract.get("symbol", "NFT"),
                            "count": 0,
                            "token_ids": [],
                            "image_url": None
                        }

                    collection = collections[contract_address]
                    collection["count"] += 1

                    token_id = nft.get("tokenId")
                    if token_id and len(collection["token_ids"]) < 10:
                        try:
                            if isinstance(token_id, str) and token_id.startswith("0x"):
                                token_id_decimal = str(int(token_id, 16))
                            else:
                                token_id_decimal = str(token_id)
                            collection["token_ids"].append(token_id_decimal)
                        except ValueError:
                            pass

                    if not collection["image_url"]:
                        image_sources = [
                            nft.get("image", {}).get("originalUrl") if isinstance(nft.get("image"), dict) else nft.get("image"),
                            nft.get("metadata", {}).get("image")
                        ]

                        for img_url in image_sources:
                            if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                                collection["image_url"] = img_url
                                break

                except Exception as nft_error:
                    print(f"⚠️ [ETH NFT] Error processing NFT: {nft_error}")
                    continue

            # Convert collections to NFTData objects
            for contract_address, collection_data in collections.items():
                try:
                    floor_price_usd = await self._fetch_floor_price(contract_address)

                    nft_asset = NFTData(
                        contract_address=contract_address,
                        symbol=collection_data["symbol"],
                        name=collection_data["name"],
                        item_count=collection_data["count"],
                        token_ids=collection_data["token_ids"],
                        floor_price_usd=floor_price_usd,
                        image_url=collection_data.get("image_url"))

                    nfts.append(nft_asset)

                    print(f"✅ [ETH NFT] Added collection: {collection_data['name']} ({collection_data['count']} items, floor: ${floor_price_usd})")

                except Exception as asset_error:
                    print(f"❌ [ETH NFT] Error creating NFT for {contract_address}: {asset_error}")
                    continue

        except Exception as e:
            print(f"❌ [ETH NFT] Unexpected error: {e}")

        return nfts

    async def _fetch_floor_price(self, contract_address: str) -> float:
        try:
            api_key = self.alchemy_url.split("/v2/")[-1]
            floor_price_url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api_key}/getFloorPrice"

            params = {"contractAddress": contract_address}

            import requests

            response = requests.get(floor_price_url, params=params, headers={"accept": "application/json"}, timeout=15.0)

            if response.status_code == 200:
                try:
                    data = response.json()
                    floor_price_usd = 0.0
                    eth_price_usd = 3750.0  # Current approximate ETH price

                    # Try OpenSea first
                    if ("openSea" in data and isinstance(data["openSea"], dict)
                            and "floorPrice" in data["openSea"] and data["openSea"]["floorPrice"] is not None):
                        try:
                            floor_price_eth = float(data["openSea"]["floorPrice"])
                            if floor_price_eth > 0:
                                floor_price_usd = floor_price_eth * eth_price_usd
                                return floor_price_usd
                        except (ValueError, TypeError):
                            pass

                    # Try LooksRare as backup
                    if ("looksRare" in data and isinstance(data["looksRare"], dict)
                            and "floorPrice" in data["looksRare"] and data["looksRare"]["floorPrice"] is not None):
                        try:
                            floor_price_eth = float(data["looksRare"]["floorPrice"])
                            if floor_price_eth > 0:
                                floor_price_usd = floor_price_eth * eth_price_usd
                                return floor_price_usd
                        except (ValueError, TypeError):
                            pass

                    return 0.0

                except (ValueError, TypeError, KeyError) as parse_error:
                    print(f"❌ [FLOOR PRICE] JSON parsing error: {parse_error}")
                    return 0.0

            return 0.0

        except Exception as e:
            print(f"❌ [FLOOR PRICE] Error fetching floor price: {e}")
            return 0.0

    async def _fetch_erc20_tokens(self, wallet_address: str, hidden_addresses: set) -> List[AssetData]:
        assets = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.alchemy_url,
                                             json={
                                                 "id": 1,
                                                 "jsonrpc": "2.0",
                                                 "method": "alchemy_getTokenBalances",
                                                 "params": [wallet_address]
                                             })

                if response.status_code == 200:
                    data = response.json()
                    token_balances = data.get("result", {}).get("tokenBalances", [])

                    for token_balance in token_balances:
                        if token_balance.get("tokenBalance") and int(token_balance["tokenBalance"], 16) > 0:
                            try:
                                contract_address = token_balance["contractAddress"].lower()

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
                                    metadata = metadata_response.json().get("result", {})
                                    balance_int = int(token_balance["tokenBalance"], 16)
                                    decimals = metadata.get("decimals", 18)
                                    balance_formatted = balance_int / (10**decimals)

                                    if balance_formatted > 0.001:  # Filter out dust
                                        assets.append(AssetData(
                                            token_address=contract_address,
                                            symbol=metadata.get("symbol", "UNKNOWN"),
                                            name=metadata.get("name", "Unknown Token"),
                                            balance=balance_formatted,
                                            balance_formatted=f"{balance_formatted:.6f}",
                                            decimals=decimals))
                            except Exception as e:
                                print(f"❌ Error processing Ethereum token {contract_address}: {e}")
        except Exception as e:
            print(f"❌ Error fetching Ethereum ERC-20 tokens: {e}")

        return assets


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

    async def fetch_assets(self, wallet_address: str,
                           hidden_addresses: set) -> List[AssetData]:
        assets = []

        if not self._is_valid_solana_address(wallet_address):
            return assets

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get SOL balance
                if "solana" not in hidden_addresses:
                    sol_asset = await self._fetch_sol_balance(
                        client, wallet_address)
                    if sol_asset:
                        assets.append(sol_asset)

                # Get SPL tokens
                spl_assets = await self._fetch_spl_tokens(
                    client, wallet_address, hidden_addresses)
                assets.extend(spl_assets)

        except Exception as e:
            print(f"❌ Error fetching Solana assets: {e}")

        return assets

    async def fetch_nfts(self, wallet_address: str, hidden_addresses: set) -> List[NFTData]:
        # Solana NFT implementation would go here
        # For now, return empty list
        return []

    def _is_valid_solana_address(self, address: str) -> bool:
        try:
            import base58
            if not address or len(address) < 32 or len(address) > 44:
                return False
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except:
            import re
            if not address or len(address) < 32 or len(address) > 44:
                return False
            base58_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
            return bool(re.match(base58_pattern, address))

    async def _fetch_sol_balance(self, client: httpx.AsyncClient,
                                 wallet_address: str) -> Optional[AssetData]:
        try:
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address, {
                    "commitment": "confirmed"
                }]
            }

            response = await client.post(self.solana_url, json=rpc_payload, timeout=30.0)

            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return None

                if "result" in data:
                    result = data["result"]
                    if isinstance(result, dict) and "value" in result:
                        sol_balance_lamports = result["value"]
                    elif isinstance(result, int):
                        sol_balance_lamports = result
                    else:
                        return None

                    sol_balance = sol_balance_lamports / 1_000_000_000

                    if sol_balance > 0:
                        return AssetData(
                            token_address="solana",
                            symbol="SOL",
                            name="Solana",
                            balance=sol_balance,
                            balance_formatted=f"{sol_balance:.6f}",
                            decimals=9)
            return None
        except Exception:
            return None

    async def _fetch_spl_tokens(self, client: httpx.AsyncClient,
                                wallet_address: str,
                                hidden_addresses: set) -> List[AssetData]:
        assets = []
        program_ids = [self.spl_token_program, self.spl_token_2022_program]

        for program_id in program_ids:
            try:
                rpc_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [
                        wallet_address,
                        {"programId": program_id},
                        {"encoding": "jsonParsed", "commitment": "confirmed"}
                    ]
                }

                response = await client.post(self.solana_url, json=rpc_payload, timeout=30.0)

                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        continue

                    if "result" in data and "value" in data["result"]:
                        token_accounts = data["result"]["value"]

                        for token_account in token_accounts:
                            try:
                                account_info = token_account.get("account", {})
                                if not account_info:
                                    continue

                                account_data = account_info.get("data", {})
                                if not isinstance(account_data, dict):
                                    continue

                                parsed_data = account_data.get("parsed", {})
                                if not parsed_data:
                                    continue

                                token_info = parsed_data.get("info", {})
                                if not token_info:
                                    continue

                                mint_address = token_info.get("mint", "")
                                token_amount = token_info.get("tokenAmount", {})

                                if not mint_address:
                                    continue

                                if mint_address.lower() in hidden_addresses:
                                    continue

                                ui_amount = token_amount.get("uiAmount")
                                amount_string = token_amount.get("amount", "0")
                                decimals = token_amount.get("decimals", 0)

                                if ui_amount is not None and ui_amount != 0:
                                    balance = float(ui_amount)
                                elif amount_string and amount_string != "0":
                                    raw_amount = int(amount_string)
                                    balance = raw_amount / (10**decimals) if decimals > 0 else raw_amount
                                else:
                                    balance = 0

                                if balance > 0:
                                    if mint_address in self.known_tokens:
                                        symbol = self.known_tokens[mint_address]["symbol"]
                                        name = self.known_tokens[mint_address]["name"]
                                    else:
                                        symbol, name = await self._fetch_token_metadata(client, mint_address)

                                    asset = AssetData(
                                        token_address=mint_address,
                                        symbol=symbol,
                                        name=name,
                                        balance=balance,
                                        balance_formatted=f"{balance:.6f}",
                                        decimals=decimals)
                                    assets.append(asset)

                            except Exception:
                                continue

            except Exception:
                continue
        return assets

    async def _fetch_token_metadata(self, client: httpx.AsyncClient,
                                    mint_address: str) -> tuple[str, str]:
        try:
            # Try DexScreener API
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
            dex_response = await client.get(dex_url, timeout=15.0)
            if dex_response.status_code == 200:
                dex_data = dex_response.json()
                if 'pairs' in dex_data and len(dex_data['pairs']) > 0:
                    for pair in dex_data['pairs']:
                        base_token = pair.get('baseToken', {})
                        if base_token.get('address', '').lower() == mint_address.lower():
                            symbol = base_token.get('symbol', '')
                            name = base_token.get('name', '')
                            if symbol and name and symbol != 'unknown':
                                return symbol, name
        except Exception:
            pass

        fallback_symbol = f"SPL-{mint_address[:6]}"
        fallback_name = f"SPL Token ({mint_address[:8]}...)"
        return fallback_symbol, fallback_name


class SolanaPriceFetcher(PriceFetcher):

    def __init__(self):
        self.known_tokens = {
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
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {
                "symbol": "BONK",
                "coingecko_id": "bonk"
            },
            "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": {
                "symbol": "ETH",
                "coingecko_id": "ethereum"
            },
            "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": {
                "symbol": "mSOL",
                "coingecko_id": "marinade-staked-sol"
            },
        }

    async def fetch_prices(self,
                           token_addresses: List[str]) -> Dict[str, float]:
        price_map = {}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Get SOL price first
                try:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/price",
                        params={"ids": "solana", "vs_currencies": "usd"},
                        timeout=15.0)
                    if response.status_code == 200:
                        data = response.json()
                        sol_price = data.get("solana", {}).get("usd", 0)
                        price_map["solana"] = sol_price
                except Exception:
                    pass

                # Process mint addresses
                mint_addresses = [
                    addr for addr in token_addresses if addr != "solana"
                ]

                # Method 1: Known tokens
                await self._fetch_known_token_prices(client, mint_addresses, price_map)

                # Method 2: DexScreener API
                await self._fetch_dexscreener_prices(client, mint_addresses, price_map)

                # Final fallback
                for addr in mint_addresses:
                    if addr.lower() not in price_map and addr not in price_map:
                        price_map[addr.lower()] = 0
                        price_map[addr] = 0

        except Exception:
            pass

        return price_map

    async def _fetch_known_token_prices(self, client: httpx.AsyncClient, mint_addresses: List[str], price_map: Dict[str, float]):
        known_ids = []
        address_to_id = {}

        for addr in mint_addresses:
            addr_lower = addr.lower()
            if addr_lower in self.known_tokens:
                coingecko_id = self.known_tokens[addr_lower]["coingecko_id"]
                known_ids.append(coingecko_id)
                address_to_id[coingecko_id] = addr_lower

        if known_ids:
            try:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": ",".join(known_ids), "vs_currencies": "usd"})
                if response.status_code == 200:
                    data = response.json()
                    for coingecko_id, price_data in data.items():
                        if isinstance(price_data, dict) and "usd" in price_data:
                            addr = address_to_id.get(coingecko_id)
                            if addr:
                                price_map[addr] = price_data["usd"]
                                original_addr = next((a for a in mint_addresses if a.lower() == addr), addr)
                                price_map[original_addr] = price_data["usd"]
            except Exception:
                pass

    async def _fetch_dexscreener_prices(self, client: httpx.AsyncClient, mint_addresses: List[str], price_map: Dict[str, float]):
        try:
            remaining_mints = [addr for addr in mint_addresses
                               if addr.lower() not in price_map and addr not in price_map]
            if not remaining_mints:
                return

            for i in range(0, len(remaining_mints), 30):
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

                await asyncio.sleep(0.1)

        except Exception:
            pass


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
    """Initialize PostgreSQL database with separated assets and NFTs tables"""
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

        # Assets table (regular tokens only)
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
                price_change_24h REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # NFT collections table (separate from assets)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nft_collections (
                id SERIAL PRIMARY KEY,
                wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
                contract_address TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                item_count INTEGER NOT NULL DEFAULT 1,
                token_ids TEXT,
                floor_price_usd REAL DEFAULT 0,
                total_value_usd REAL DEFAULT 0,
                image_url TEXT,
                collection_url TEXT,
                marketplace_data TEXT,
                purchase_price REAL DEFAULT 0,
                total_invested REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                unrealized_pnl REAL DEFAULT 0,
                total_return_pct REAL DEFAULT 0,
                notes TEXT DEFAULT '',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Purchase history table
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

        # Asset cost basis table
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

        # Purchase price overrides table
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

        # Wallet status table
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


class NFTResponse(BaseModel):
    id: str
    contract_address: str
    symbol: str
    name: str
    item_count: int
    token_ids: List[str]
    floor_price_usd: float
    total_value_usd: float
    image_url: Optional[str] = None
    purchase_price: Optional[float] = 0
    total_invested: Optional[float] = 0
    realized_pnl: Optional[float] = 0
    unrealized_pnl: Optional[float] = 0
    total_return_pct: Optional[float] = 0
    notes: Optional[str] = ""


class PortfolioResponse(BaseModel):
    total_value: float
    assets: List[AssetResponse]
    nfts: List[NFTResponse]
    wallet_count: int
    performance_24h: float


class WalletDetailsResponse(BaseModel):
    wallet: WalletResponse
    assets: List[AssetResponse]
    nfts: List[NFTResponse]
    total_value: float
    performance_24h: float


# Asset fetching functions
async def get_wallet_assets_new(wallet_address: str, network: str) -> tuple[List[AssetData], List[NFTData]]:
    """Fetch both assets and NFTs for a wallet"""
    hidden_addresses = set()

    try:
        asset_fetcher = ChainFactory.create_asset_fetcher(network, ALCHEMY_API_KEY)

        # Fetch regular assets
        assets = await asset_fetcher.fetch_assets(wallet_address, hidden_addresses)

        # Fetch NFTs
        nfts = await asset_fetcher.fetch_nfts(wallet_address, hidden_addresses)

        print(f"✅ Fetched {len(assets)} assets and {len(nfts)} NFT collections for {network} wallet {wallet_address}")
        return assets, nfts

    except Exception as e:
        print(f"❌ Error fetching assets for {network} wallet {wallet_address}: {e}")
        return [], []


async def get_token_prices_new(token_addresses_by_network: Dict[str, List[str]]) -> Dict[str, float]:
    """Fetch prices for tokens across networks"""
    all_prices = {}

    for network, token_addresses in token_addresses_by_network.items():
        if not token_addresses:
            continue

        try:
            price_fetcher = ChainFactory.create_price_fetcher(network)
            network_prices = await price_fetcher.fetch_prices(token_addresses)
            all_prices.update(network_prices)
            print(f"✅ Fetched {len(network_prices)} prices for {network}")

        except Exception as e:
            print(f"❌ Error fetching prices for {network}: {e}")

    return all_prices


async def estimate_asset_purchase_price(symbol: str, name: str, current_price: float) -> float:
    """Estimate purchase price based on asset characteristics"""
    if symbol == "ETH":
        return current_price * 0.65
    elif symbol == "WBTC" or "Bitcoin" in name:
        return current_price * 0.55
    elif symbol == "SOL":
        return current_price * 0.45
    elif symbol == "PENDLE":
        return current_price * 0.4
    elif symbol in ["USDC", "USDT", "DAI"]:
        return 1.0
    elif "PENGU" in symbol or "Pudgy" in name:
        return current_price * 0.2
    elif "Fartcoin" in name or symbol.startswith("SPL-"):
        if current_price > 1:
            return current_price * 0.15
        else:
            return current_price * 0.25
    elif symbol in ["UNI", "LINK", "AAVE", "CRV"]:
        return current_price * 0.6
    else:
        return current_price * 0.5


async def update_portfolio_data_new():
    """Background task to update portfolio data with separated assets and NFTs"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("🚀 Starting portfolio update with separated assets and NFTs...")

        # Clear existing data
        cursor.execute("DELETE FROM assets")
        cursor.execute("DELETE FROM nft_collections")

        # Get all wallets
        cursor.execute("SELECT id, address, network, label FROM wallets")
        wallets = cursor.fetchall()

        # Group wallets by network
        wallets_by_network = {}
        wallet_status = {}

        for wallet_row in wallets:
            wallet_id, address, network, label = wallet_row['id'], wallet_row['address'], wallet_row['network'], wallet_row['label']
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
        all_nfts = []
        token_addresses_by_network = {}

        # Fetch assets and NFTs for each network
        for network, network_wallets in wallets_by_network.items():
            print(f"🔗 Processing {len(network_wallets)} {network} wallets...")

            token_addresses_by_network[network] = set()

            for wallet_id, address, label in network_wallets:
                try:
                    print(f"📡 Fetching assets for {network} wallet: {label} ({address[:10]}...)")

                    # Fetch both assets and NFTs
                    assets, nfts = await asyncio.wait_for(
                        get_wallet_assets_new(address, network),
                        timeout=60.0
                    )

                    wallet_assets_count = 0

                    # Process regular assets
                    for asset in assets:
                        asset_dict = {
                            'wallet_id': wallet_id,
                            'asset_data': asset,  # Store the AssetData object
                            'network': network
                        }
                        all_assets.append(asset_dict)
                        token_addresses_by_network[network].add(asset.token_address)
                        wallet_assets_count += 1

                    # Process NFTs
                    for nft in nfts:
                        nft_dict = {
                            'wallet_id': wallet_id,
                            'nft_data': nft,  # Store the NFTData object
                            'network': network
                        }
                        all_nfts.append(nft_dict)
                        wallet_assets_count += 1

                    wallet_status[wallet_id].update({
                        'status': 'success',
                        'assets_found': wallet_assets_count
                    })
                    print(f"✅ Successfully fetched {wallet_assets_count} items from {label}")

                except asyncio.TimeoutError:
                    error_msg = f"Timeout after 60 seconds"
                    print(f"⏰ {error_msg} for {network} wallet {label}")
                    wallet_status[wallet_id].update({'status': 'timeout', 'error': error_msg})
                except Exception as e:
                    error_msg = str(e)[:200]
                    print(f"❌ Error fetching assets for {network} wallet {label}: {error_msg}")
                    wallet_status[wallet_id].update({'status': 'error', 'error': error_msg})

        # Convert sets to lists for price fetching
        for network in token_addresses_by_network:
            token_addresses_by_network[network] = list(token_addresses_by_network[network])

        print(f"📊 Total items fetched: {len(all_assets)} assets, {len(all_nfts)} NFT collections")

        # Get prices
        try:
            price_map = await asyncio.wait_for(
                get_token_prices_new(token_addresses_by_network), timeout=30.0)
        except Exception as e:
            print(f"❌ Error fetching prices: {e}")
            price_map = {}

        # Insert assets with prices
        total_portfolio_value = 0
        auto_hide_candidates = []

        # Process regular assets
        for asset_item in all_assets:
            asset = asset_item['asset_data']  # Get the AssetData object
            wallet_id = asset_item['wallet_id']
            network = asset_item['network']

            # Get price
            if asset.token_address.lower() == "0x0000000000000000000000000000000000000000":
                price_usd = (price_map.get("0x0000000000000000000000000000000000000000", 0) or 
                           price_map.get("eth", 0))
            else:
                price_usd = price_map.get(asset.token_address.lower(), 0)
                if price_usd == 0:
                    price_usd = price_map.get(asset.token_address, 0)

            value_usd = asset.balance * price_usd

            # Check for purchase price override
            cursor.execute(
                "SELECT override_price FROM purchase_price_overrides WHERE token_address = %s",
                (asset.token_address,))
            override_data = cursor.fetchone()

            if override_data:
                purchase_price = override_data['override_price']
                total_invested = asset.balance * purchase_price
                realized_pnl = 0
                unrealized_pnl = value_usd - total_invested if total_invested > 0 else 0
                total_return_pct = ((value_usd - total_invested) / total_invested * 100) if total_invested > 0 else 0
            else:
                # Estimate purchase price
                purchase_price = await estimate_asset_purchase_price(asset.symbol, asset.name, price_usd) if price_usd > 0 else 0
                total_invested = asset.balance * purchase_price
                realized_pnl = 0
                unrealized_pnl = value_usd - total_invested if total_invested > 0 else 0
                total_return_pct = ((value_usd - total_invested) / total_invested * 100) if total_invested > 0 else 0

            # Check for spam/low value assets
            spam_indicators = ["visit", "claim", "rewards", "gift", "airdrop", ".com", ".net", ".org"]
            is_spam_token = (value_usd == 0 and asset.balance > 0 and
                           any(indicator in asset.name.lower() for indicator in spam_indicators))
            is_low_value_token = (value_usd > 0 and value_usd < 1.0 and
                                asset.symbol not in ['ETH', 'BTC', 'SOL', 'USDC', 'USDT', 'WBTC', 'PENDLE'])

            if is_spam_token or is_low_value_token:
                reason = "spam/scam" if is_spam_token else f"low value (${value_usd:.6f})"
                auto_hide_candidates.append({
                    'token_address': asset.token_address,
                    'symbol': asset.symbol,
                    'name': asset.name,
                    'reason': reason
                })

            # Insert asset
            try:
                cursor.execute(
                    """
                    INSERT INTO assets 
                    (wallet_id, token_address, symbol, name, balance, balance_formatted, price_usd, value_usd,
                     purchase_price, total_invested, realized_pnl, unrealized_pnl, total_return_pct, price_change_24h)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (wallet_id, asset.token_address, asset.symbol, asset.name, asset.balance,
                      asset.balance_formatted, price_usd, value_usd, purchase_price, total_invested,
                      realized_pnl, unrealized_pnl, total_return_pct, 0))

                wallet_status[wallet_id]['total_value'] += value_usd
                total_portfolio_value += value_usd

                print(f"💰 {network} Asset: {asset.symbol} = ${value_usd:.2f}")

            except Exception as db_error:
                print(f"❌ [DATABASE ERROR] Failed to insert {asset.symbol}: {db_error}")
                continue

        # Process NFTs
        for nft_item in all_nfts:
            nft = nft_item['nft_data']  # Get the NFTData object
            wallet_id = nft_item['wallet_id']
            network = nft_item['network']

            total_value_usd = nft.floor_price_usd * nft.item_count

            # Estimate purchase price for NFTs
            purchase_price = nft.floor_price_usd * 0.5 if nft.floor_price_usd > 0 else 0
            total_invested = purchase_price * nft.item_count
            unrealized_pnl = total_value_usd - total_invested if total_invested > 0 else 0
            total_return_pct = ((total_value_usd - total_invested) / total_invested * 100) if total_invested > 0 else 0

            # Insert NFT collection
            try:
                cursor.execute(
                    """
                    INSERT INTO nft_collections 
                    (wallet_id, contract_address, symbol, name, item_count, token_ids, floor_price_usd, 
                     total_value_usd, image_url, purchase_price, total_invested, realized_pnl, 
                     unrealized_pnl, total_return_pct)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (wallet_id, nft.contract_address, nft.symbol, nft.name, nft.item_count,
                      json.dumps(nft.token_ids), nft.floor_price_usd, total_value_usd, nft.image_url,
                      purchase_price, total_invested, 0, unrealized_pnl, total_return_pct))

                wallet_status[wallet_id]['total_value'] += total_value_usd
                total_portfolio_value += total_value_usd

                print(f"🖼️ {network} NFT: {nft.name} ({nft.item_count} items) = ${total_value_usd:.2f}")

            except Exception as db_error:
                print(f"❌ [DATABASE ERROR] Failed to insert NFT {nft.name}: {db_error}")
                continue

        # Auto-hide spam/low value tokens
        if auto_hide_candidates:
            print(f"🔍 Auto-hiding {len(auto_hide_candidates)} tokens...")
            for hide_asset in auto_hide_candidates:
                try:
                    if hide_asset['token_address'].lower() == "0x0000000000000000000000000000000000000000":
                        continue
                    if hide_asset['symbol'] in ['ETH', 'SOL', 'WBTC', 'PENDLE', 'USDC', 'USDT']:
                        continue

                    cursor.execute(
                        """
                        INSERT INTO hidden_assets (token_address, symbol, name) 
                        VALUES (%s, %s, %s)
                        ON CONFLICT (token_address) DO UPDATE SET
                        symbol = EXCLUDED.symbol, name = EXCLUDED.name
                    """, (hide_asset['token_address'].lower(), hide_asset['symbol'], hide_asset['name']))

                    print(f"🙈 Auto-hidden {hide_asset['reason']}: {hide_asset['symbol'] or 'unnamed'}")
                except Exception as e:
                    print(f"❌ Error auto-hiding asset {hide_asset['symbol']}: {e}")

        # Record portfolio history
        cursor.execute("INSERT INTO portfolio_history (total_value_usd) VALUES (%s)", (total_portfolio_value,))

        # Update wallet status
        cursor.execute("DELETE FROM wallet_status")
        for wallet_id, status_info in wallet_status.items():
            cursor.execute(
                """
                INSERT INTO wallet_status (wallet_id, status, assets_found, total_value, error_message)
                VALUES (%s, %s, %s, %s, %s)
            """, (wallet_id, status_info['status'], status_info['assets_found'],
                  status_info['total_value'], status_info['error']))

        conn.commit()

        # Final success summary
        successful_count = sum(1 for s in wallet_status.values() if s['status'] == 'success')
        total_count = len(wallet_status)
        print(f"✅ Portfolio updated successfully!")
        print(f"📈 {len(all_assets)} assets and {len(all_nfts)} NFT collections processed")
        print(f"💰 ${total_portfolio_value:,.2f} total value")
        print(f"🏦 {successful_count}/{total_count} wallets processed successfully")

    except Exception as e:
        print(f"❌ Critical error updating portfolio: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        conn.rollback()
    finally:
        conn.close()


# API endpoints

@app.get("/")
async def root():
    """Serve the React frontend"""
    if dist_path:
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

    return {
        "message": "Crypto Fund API",
        "status": "running",
        "mode": "api-only",
        "error": "Frontend build files not found - deployment misconfiguration"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT current_database(), current_user, version()")
        db_info = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM wallets")
        wallet_result = cursor.fetchone()
        wallet_count = wallet_result['count'] if wallet_result else 0

        cursor.execute("SELECT COUNT(*) FROM assets")
        asset_result = cursor.fetchone()
        asset_count = asset_result['count'] if asset_result else 0

        cursor.execute("SELECT COUNT(*) FROM nft_collections")
        nft_result = cursor.fetchone()
        nft_count = nft_result['count'] if nft_result else 0

        cursor.execute("SELECT COUNT(*) FROM hidden_assets")
        hidden_result = cursor.fetchone()
        hidden_count = hidden_result['count'] if hidden_result else 0

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
            "environment": {
                "DATABASE_URL": bool(DATABASE_URL),
                "ALCHEMY_API_KEY": bool(ALCHEMY_API_KEY),
                "NODE_ENV": os.getenv("NODE_ENV", "development")
            },
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
                    "nft_collections": nft_count,
                    "hidden_assets": hidden_count
                }
            },
            "application": {
                "name": "Crypto Fund API",
                "version": "1.0.0"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": "unexpected_error",
            "error_details": str(e)
        }


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

        return WalletResponse(id=wallet_id, address=wallet.address, label=wallet.label, network=wallet.network)
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Wallet address already exists")
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

    return [WalletResponse(id=w['id'], address=w['address'], label=w['label'], network=w['network']) for w in wallets]


@app.delete("/api/wallets/{wallet_id}")
async def delete_wallet(wallet_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM assets WHERE wallet_id = %s", (wallet_id,))
        cursor.execute("DELETE FROM nft_collections WHERE wallet_id = %s", (wallet_id,))
        cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))

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

    # Get assets
    cursor.execute("""
        SELECT a.token_address, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(a.purchase_price, 0) as purchase_price,
               COALESCE(a.total_invested, 0) as total_invested, COALESCE(a.realized_pnl, 0) as realized_pnl,
               COALESCE(a.unrealized_pnl, 0) as unrealized_pnl, COALESCE(a.total_return_pct, 0) as total_return_pct,
               COALESCE(n.notes, '') as notes, COALESCE(a.price_change_24h, 0) as price_change_24h
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        WHERE NOT EXISTS (
            SELECT 1 FROM hidden_assets h 
            WHERE LOWER(h.token_address) = LOWER(a.token_address)
        )
        ORDER BY a.value_usd DESC
    """)
    assets_data = cursor.fetchall()

    assets = []
    for a in assets_data:
        try:
            asset = AssetResponse(
                id=a['token_address'] if a['token_address'] else a['symbol'],
                symbol=a['symbol'] or "Unknown",
                name=a['name'] or "Unknown Token",
                balance=float(a['balance']) if a['balance'] else 0.0,
                balance_formatted=a['balance_formatted'] or "0.000000",
                price_usd=float(a['price_usd']) if a['price_usd'] else 0.0,
                value_usd=float(a['value_usd']) if a['value_usd'] else 0.0,
                purchase_price=float(a['purchase_price']) if a['purchase_price'] else 0.0,
                total_invested=float(a['total_invested']) if a['total_invested'] else 0.0,
                realized_pnl=float(a['realized_pnl']) if a['realized_pnl'] else 0.0,
                unrealized_pnl=float(a['unrealized_pnl']) if a['unrealized_pnl'] else 0.0,
                total_return_pct=float(a['total_return_pct']) if a['total_return_pct'] else 0.0,
                notes=a['notes'] or "",
                is_nft=False,
                floor_price=0,
                image_url=None,
                nft_metadata=None,
                price_change_24h = float(a['price_change_24h']) if a['price_change_24h'] else 0.0
                )
            assets.append(asset)
        except Exception as e:
            print(f"❌ Error creating asset from {a}: {e}")
            continue

    # Get NFTs
    cursor.execute("""
        SELECT contract_address, symbol, name, item_count, token_ids, floor_price_usd,
               total_value_usd, image_url, COALESCE(purchase_price, 0) as purchase_price,
               COALESCE(total_invested, 0) as total_invested, COALESCE(realized_pnl, 0) as realized_pnl,
               COALESCE(unrealized_pnl, 0) as unrealized_pnl, COALESCE(total_return_pct, 0) as total_return_pct,
               COALESCE(notes, '') as notes
        FROM nft_collections
        WHERE total_value_usd > 0
        ORDER BY total_value_usd DESC
    """)
    nfts_data = cursor.fetchall()

    nfts = []
    for n in nfts_data:
        try:
            token_ids = []
            if n['token_ids']:
                try:
                    token_ids = json.loads(n['token_ids'])
                except:
                    token_ids = []

            nft = NFTResponse(
                id=n['contract_address'],
                contract_address=n['contract_address'],
                symbol=n['symbol'] or "NFT",
                name=n['name'] or "Unknown Collection",
                item_count=int(n['item_count']) if n['item_count'] else 0,
                token_ids=token_ids,
                floor_price_usd=float(n['floor_price_usd']) if n['floor_price_usd'] else 0.0,
                total_value_usd=float(n['total_value_usd']) if n['total_value_usd'] else 0.0,
                image_url=n['image_url'],
                purchase_price=float(n['purchase_price']) if n['purchase_price'] else 0.0,
                total_invested=float(n['total_invested']) if n['total_invested'] else 0.0,
                realized_pnl=float(n['realized_pnl']) if n['realized_pnl'] else 0.0,
                unrealized_pnl=float(n['unrealized_pnl']) if n['unrealized_pnl'] else 0.0,
                total_return_pct=float(n['total_return_pct']) if n['total_return_pct'] else 0.0,
                notes=n['notes'] or "")
            nfts.append(nft)
        except Exception as e:
            print(f"❌ Error creating NFT from {n}: {e}")
            continue

    # Calculate total value
    total_value = sum(asset.value_usd or 0 for asset in assets) + sum(nft.total_value_usd or 0 for nft in nfts)

    # Get wallet count
    cursor.execute("SELECT COUNT(*) FROM wallets")
    result = cursor.fetchone()
    wallet_count = result['count'] if result else 0

    # Calculate 24h performance
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
            performance_24h = ((current_value - previous_value) / previous_value) * 100

    conn.close()

    return PortfolioResponse(
        total_value=total_value,
        assets=assets,
        nfts=nfts,
        wallet_count=wallet_count,
        performance_24h=performance_24h)


@app.get("/api/wallets/{wallet_id}/details", response_model=WalletDetailsResponse)
async def get_wallet_details(wallet_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get wallet info
    cursor.execute("SELECT id, address, label, network FROM wallets WHERE id = %s", (wallet_id,))
    wallet_data = cursor.fetchone()
    if not wallet_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Wallet not found")

    wallet = WalletResponse(id=wallet_data['id'], address=wallet_data['address'], 
                           label=wallet_data['label'], network=wallet_data['network'])

    # Get wallet assets
    cursor.execute("""
        SELECT a.token_address, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(n.notes, '') as notes
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        WHERE a.wallet_id = %s
        ORDER BY a.value_usd DESC
    """, (wallet_id,))
    assets_data = cursor.fetchall()

    assets = []
    for a in assets_data:
        try:
            asset = AssetResponse(
                id=a['token_address'] if a['token_address'] else a['symbol'],
                symbol=a['symbol'] or "Unknown",
                name=a['name'] or "Unknown Token",
                balance=float(a['balance']) if a['balance'] else 0.0,
                balance_formatted=a['balance_formatted'] or "0.000000",
                price_usd=float(a['price_usd']) if a['price_usd'] else 0.0,
                value_usd=float(a['value_usd']) if a['value_usd'] else 0.0,
                notes=a['notes'] or "")
            assets.append(asset)
        except Exception as e:
            print(f"❌ Error creating asset from {a}: {e}")
            continue

    # Get wallet NFTs
    cursor.execute("""
        SELECT contract_address, symbol, name, item_count, token_ids, floor_price_usd,
               total_value_usd, image_url
        FROM nft_collections
        WHERE wallet_id = %s
        ORDER BY total_value_usd DESC
    """, (wallet_id,))
    nfts_data = cursor.fetchall()

    nfts = []
    for n in nfts_data:
        try:
            token_ids = []
            if n['token_ids']:
                try:
                    token_ids = json.loads(n['token_ids'])
                except:
                    token_ids = []

            nft = NFTResponse(
                id=n['contract_address'],
                contract_address=n['contract_address'],
                symbol=n['symbol'] or "NFT",
                name=n['name'] or "Unknown Collection",
                item_count=int(n['item_count']) if n['item_count'] else 0,
                token_ids=token_ids,
                floor_price_usd=float(n['floor_price_usd']) if n['floor_price_usd'] else 0.0,
                total_value_usd=float(n['total_value_usd']) if n['total_value_usd'] else 0.0,
                image_url=n['image_url'])
            nfts.append(nft)
        except Exception as e:
            print(f"❌ Error creating NFT from {n}: {e}")
            continue

    total_value = sum(asset.value_usd or 0 for asset in assets) + sum(nft.total_value_usd or 0 for nft in nfts)

    conn.close()

    return WalletDetailsResponse(
        wallet=wallet,
        assets=assets,
        nfts=nfts,
        total_value=total_value,
        performance_24h=0.0)


@app.put("/api/assets/{symbol}/notes")
async def update_asset_notes(symbol: str, notes: str):
    """Update notes for a specific asset"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO asset_notes (symbol, notes, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (symbol) DO UPDATE SET
            notes = EXCLUDED.notes, updated_at = CURRENT_TIMESTAMP
        """, (symbol, notes))

        conn.commit()
        return {"message": "Notes updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()


@app.put("/api/assets/{symbol}/purchase_price")
async def update_asset_purchase_price(symbol: str, request: dict):
    """Update purchase price for a specific asset"""
    if not symbol or not symbol.strip():
        raise HTTPException(status_code=400, detail="Symbol is required")

    clean_symbol = symbol.strip()

    try:
        purchase_price = request.get('purchase_price')
        if purchase_price is None:
            raise HTTPException(status_code=400, detail="Purchase price is required")

        try:
            purchase_price = float(purchase_price)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Purchase price must be a valid number")

        if purchase_price < 0:
            raise HTTPException(status_code=400, detail="Purchase price cannot be negative")

        if purchase_price > 1e15:
            raise HTTPException(status_code=400, detail="Purchase price is too large")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input format")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Find the asset with robust symbol matching
        asset_data = None
        matched_symbol = None

        # Try exact match first
        cursor.execute("""
            SELECT symbol, balance, value_usd, purchase_price as old_purchase_price, token_address
            FROM assets 
            WHERE symbol = %s
            LIMIT 1
        """, (clean_symbol,))
        asset_data = cursor.fetchone()

        if asset_data:
            matched_symbol = asset_data['symbol']
        else:
            # Try case-insensitive match
            cursor.execute("""
                SELECT symbol, balance, value_usd, purchase_price as old_purchase_price, token_address
                FROM assets 
                WHERE LOWER(symbol) = LOWER(%s)
                LIMIT 1
            """, (clean_symbol,))
            asset_data = cursor.fetchone()

            if asset_data:
                matched_symbol = asset_data['symbol']

        if not asset_data:
            cursor.execute("""
                SELECT symbol, name, balance, value_usd 
                FROM assets 
                WHERE balance > 0 
                ORDER BY value_usd DESC 
                LIMIT 10
            """)
            available_assets = cursor.fetchall()

            available_symbols = [f"'{asset['symbol']}'" for asset in available_assets]
            error_detail = f"Asset with symbol '{clean_symbol}' not found. Available assets: {', '.join(available_symbols)}"
            raise HTTPException(status_code=404, detail=error_detail)

        # Calculate new metrics
        balance = float(asset_data['balance']) if asset_data['balance'] else 0
        current_value = float(asset_data['value_usd']) if asset_data['value_usd'] else 0
        token_address = asset_data['token_address']

        total_invested = balance * purchase_price
        unrealized_pnl = current_value - total_invested
        total_return_pct = ((unrealized_pnl / total_invested) * 100) if total_invested > 0 else 0

        # Store the override
        cursor.execute("""
            INSERT INTO purchase_price_overrides 
            (token_address, symbol, override_price, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (token_address) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            override_price = EXCLUDED.override_price,
            updated_at = EXCLUDED.updated_at
        """, (token_address, matched_symbol, purchase_price))

        # Update the asset
        cursor.execute("""
            UPDATE assets 
            SET purchase_price = %s,
                total_invested = %s,
                unrealized_pnl = %s,
                total_return_pct = %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE symbol = %s
        """, (purchase_price, total_invested, unrealized_pnl, total_return_pct, matched_symbol))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=500, detail=f"Failed to update asset '{matched_symbol}'")

        conn.commit()

        return {
            "message": f"Purchase price updated for {matched_symbol}",
            "symbol": matched_symbol,
            "purchase_price": purchase_price,
            "total_invested": total_invested,
            "unrealized_pnl": unrealized_pnl,
            "total_return_pct": total_return_pct
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.post("/api/assets/hide")
async def hide_asset(token_address: str, symbol: str, name: str):
    """Hide an asset from portfolio calculations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO hidden_assets (token_address, symbol, name)
            VALUES (%s, %s, %s)
        """, (token_address.lower(), symbol, name))

        conn.commit()
        return {"message": f"Asset {symbol} hidden successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()


@app.delete("/api/assets/hide/{token_address}")
async def unhide_asset(token_address: str):
    """Unhide an asset"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM hidden_assets WHERE token_address = %s", (token_address.lower(),))

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

    cursor.execute("SELECT token_address, symbol, name, hidden_at FROM hidden_assets")
    hidden_assets = cursor.fetchall()
    conn.close()

    return [{
        "token_address": h['token_address'],
        "symbol": h['symbol'],
        "name": h['name'],
        "hidden_at": h['hidden_at']
    } for h in hidden_assets]


# Serve static assets
@app.get("/assets/{file_path:path}")
async def serve_static_assets(file_path: str):
    if dist_path:
        full_file_path = f"{dist_path}/assets/{file_path}"
        if os.path.exists(full_file_path):
            return FileResponse(full_file_path)
    raise HTTPException(status_code=404, detail="Asset not found")


# Catch-all route for SPA routing
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if (full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("assets/")):
        raise HTTPException(status_code=404, detail="Not found")

    if dist_path:
        index_path = os.path.join(dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 80))

    if os.environ.get("NODE_ENV") == "production":
        port = 80

    print(f"🚀 [SERVER] Starting server on port {port}")

    uvicorn.run(app,
                host="0.0.0.0",
                port=port,
                log_level="info" if os.environ.get("NODE_ENV") != "production" else "warning",
                access_log=True if os.environ.get("NODE_ENV") != "production" else False)