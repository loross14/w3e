import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Protocol
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from web3 import Web3
import sqlite3
import json
import requests
from abc import ABC, abstractmethod

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

# Chain-agnostic asset interface
class AssetData:
    def __init__(self, token_address: str, symbol: str, name: str, balance: float, 
                 balance_formatted: str, decimals: int, is_nft: bool = False, 
                 token_ids: List[str] = None):
        self.token_address = token_address
        self.symbol = symbol
        self.name = name
        self.balance = balance
        self.balance_formatted = balance_formatted
        self.decimals = decimals
        self.is_nft = is_nft
        self.token_ids = token_ids or []

# Abstract base classes for chain-specific implementations
class AssetFetcher(ABC):
    @abstractmethod
    async def fetch_assets(self, wallet_address: str, hidden_addresses: set) -> List[AssetData]:
        pass

class PriceFetcher(ABC):
    @abstractmethod
    async def fetch_prices(self, token_addresses: List[str]) -> Dict[str, float]:
        pass

# Ethereum-specific implementations
class EthereumAssetFetcher(AssetFetcher):
    def __init__(self, alchemy_api_key: str):
        self.alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
        self.w3 = Web3(Web3.HTTPProvider(self.alchemy_url))

    async def fetch_assets(self, wallet_address: str, hidden_addresses: set) -> List[AssetData]:
        assets = []

        try:
            # Get ETH balance
            eth_token_address = "0x0000000000000000000000000000000000000000"
            if eth_token_address not in hidden_addresses:
                eth_balance_wei = self.w3.eth.get_balance(wallet_address)
                eth_balance_formatted = float(eth_balance_wei) / 10**18

                if eth_balance_formatted > 0:
                    assets.append(AssetData(
                        token_address=eth_token_address,
                        symbol="ETH",
                        name="Ethereum",
                        balance=eth_balance_formatted,
                        balance_formatted=f"{eth_balance_formatted:.6f}",
                        decimals=18
                    ))

            # Get ERC-20 tokens
            assets.extend(await self._fetch_erc20_tokens(wallet_address, hidden_addresses))

            # Get NFTs
            assets.extend(await self._fetch_nfts(wallet_address, hidden_addresses))

        except Exception as e:
            print(f"❌ Ethereum asset fetching error: {e}")

        return assets

    async def _fetch_erc20_tokens(self, wallet_address: str, hidden_addresses: set) -> List[AssetData]:
        assets = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.alchemy_url,
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
                                    }
                                )

                                if metadata_response.status_code == 200:
                                    metadata = metadata_response.json().get("result", {})
                                    balance_int = int(token_balance["tokenBalance"], 16)
                                    decimals = metadata.get("decimals", 18)
                                    balance_formatted = balance_int / (10 ** decimals)

                                    if balance_formatted > 0.001:  # Filter out dust
                                        assets.append(AssetData(
                                            token_address=contract_address,
                                            symbol=metadata.get("symbol", "UNKNOWN"),
                                            name=metadata.get("name", "Unknown Token"),
                                            balance=balance_formatted,
                                            balance_formatted=f"{balance_formatted:.6f}",
                                            decimals=decimals
                                        ))
                            except Exception as e:
                                print(f"❌ Error processing Ethereum token {contract_address}: {e}")
        except Exception as e:
            print(f"❌ Error fetching Ethereum ERC-20 tokens: {e}")

        return assets

    async def _fetch_nfts(self, wallet_address: str, hidden_addresses: set) -> List[AssetData]:
        assets = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                nft_response = await client.post(
                    self.alchemy_url,
                    json={
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "alchemy_getNFTsForOwner",
                        "params": [wallet_address]
                    }
                )

                if nft_response.status_code == 200:
                    nft_data = nft_response.json()
                    owned_nfts = nft_data.get("result", {}).get("ownedNfts", [])

                    # Group NFTs by collection
                    nft_collections = {}
                    for nft in owned_nfts:
                        contract_address = nft.get("contract", {}).get("address", "").lower()

                        if contract_address in hidden_addresses:
                            continue

                        collection_name = nft.get("contract", {}).get("name", "Unknown NFT Collection")
                        collection_symbol = nft.get("contract", {}).get("symbol", "NFT")

                        if contract_address not in nft_collections:
                            nft_collections[contract_address] = {
                                "name": collection_name,
                                "symbol": collection_symbol,
                                "count": 0,
                                "token_ids": []
                            }

                        nft_collections[contract_address]["count"] += 1
                        token_id = nft.get("tokenId", "")
                        if token_id:
                            nft_collections[contract_address]["token_ids"].append(token_id)

                    # Add NFT collections as assets
                    for contract_address, collection_data in nft_collections.items():
                        assets.append(AssetData(
                            token_address=contract_address,
                            symbol=f"{collection_data['symbol']} NFT",
                            name=f"{collection_data['name']} (Collection)",
                            balance=collection_data["count"],
                            balance_formatted=f"{collection_data['count']} NFTs",
                            decimals=0,
                            is_nft=True,
                            token_ids=collection_data["token_ids"][:10]
                        ))
                        print(f"✅ Found {collection_data['count']} NFTs from {collection_data['name']}")

        except Exception as e:
            print(f"❌ Error fetching Ethereum NFTs: {e}")

        return assets

class EthereumPriceFetcher(PriceFetcher):
    def __init__(self):
        self.known_tokens = {
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {"symbol": "WBTC", "coingecko_id": "wrapped-bitcoin"},
            "0x808507121b80c02388fad14726482e061b8da827": {"symbol": "PENDLE", "coingecko_id": "pendle"},
            "0xa0b73e1ff0b80914ab6fe136c72b47cb5ed05b81": {"symbol": "USDC", "coingecko_id": "usd-coin"},
            "0xdac17f958d2ee523a2206206994597c13d831ec7": {"symbol": "USDT", "coingecko_id": "tether"},
            "0x6b175474e89094c44da98b954eedeac495271d0f": {"symbol": "DAI", "coingecko_id": "dai"},
            "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {"symbol": "UNI", "coingecko_id": "uniswap"},
        }

    async def fetch_prices(self, token_addresses: List[str]) -> Dict[str, float]:
        price_map = {}
        eth_address = "0x0000000000000000000000000000000000000000"

        print(f"💵 Fetching Ethereum prices for {len(token_addresses)} tokens...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get ETH price first
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": "ethereum", "vs_currencies": "usd"}
                )
                if response.status_code == 200:
                    data = response.json()
                    eth_price = data.get("ethereum", {}).get("usd", 0)
                    price_map[eth_address] = eth_price
                    print(f"✅ ETH price: ${eth_price}")

                # Process contract addresses
                contract_addresses = [addr for addr in token_addresses if addr != eth_address]
                known_ids = []
                address_to_id = {}

                for addr in contract_addresses:
                    addr_lower = addr.lower()
                    if addr_lower in self.known_tokens:
                        coingecko_id = self.known_tokens[addr_lower]["coingecko_id"]
                        known_ids.append(coingecko_id)
                        address_to_id[coingecko_id] = addr_lower
                        print(f"✅ Found known Ethereum token: {self.known_tokens[addr_lower]['symbol']} -> {coingecko_id}")

                # Fetch known token prices
                if known_ids:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/price",
                        params={"ids": ",".join(known_ids), "vs_currencies": "usd"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for coingecko_id, price_data in data.items():
                            if isinstance(price_data, dict) and "usd" in price_data:
                                addr = address_to_id.get(coingecko_id)
                                if addr:
                                    price_map[addr] = price_data["usd"]
                                    original_addr = next((a for a in contract_addresses if a.lower() == addr), addr)
                                    price_map[original_addr] = price_data["usd"]
                                    print(f"✅ Got Ethereum price: {addr} = ${price_data['usd']}")

                # Try CoinGecko contract API for remaining tokens
                remaining_addresses = [addr for addr in contract_addresses if addr.lower() not in price_map and addr not in price_map]
                if remaining_addresses:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/token_price/ethereum",
                        params={"contract_addresses": ",".join(remaining_addresses[:30]), "vs_currencies": "usd"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for addr, price_data in data.items():
                            if isinstance(price_data, dict) and "usd" in price_data:
                                price_map[addr.lower()] = price_data["usd"]
                                price_map[addr] = price_data["usd"]
                                print(f"✅ Got Ethereum contract API price: {addr} = ${price_data['usd']}")

        except Exception as e:
            print(f"❌ Error fetching Ethereum prices: {e}")

        return price_map

# Solana-specific implementations
class SolanaAssetFetcher(AssetFetcher):
    def __init__(self, alchemy_api_key: str):
        self.solana_url = f"https://solana-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
        self.known_tokens = {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {"symbol": "USDC", "name": "USD Coin"},
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {"symbol": "USDT", "name": "Tether USD"},
            "So11111111111111111111111111111111111111112": {"symbol": "WSOL", "name": "Wrapped SOL"},
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {"symbol": "BONK", "name": "Bonk"},
            "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": {"symbol": "ETH", "name": "Ether (Portal)"},
        }
        self.spl_token_program = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        self.spl_token_2022_program = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"

    async def fetch_assets(self, wallet_address: str, hidden_addresses: set) -> List[AssetData]:
        assets = []

        print(f"🔍 [SOLANA DEBUG] Starting asset fetch for wallet: {wallet_address}")
        print(f"🔍 [SOLANA DEBUG] Solana RPC URL: {self.solana_url}")
        print(f"🔍 [SOLANA DEBUG] Hidden addresses: {list(hidden_addresses)}")

        # Validate Solana address format
        if not self._is_valid_solana_address(wallet_address):
            print(f"❌ [SOLANA DEBUG] Invalid Solana address format: {wallet_address}")
            return assets

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get SOL balance
                print(f"📊 [SOLANA DEBUG] Fetching native SOL balance...")
                if "solana" not in hidden_addresses:
                    sol_asset = await self._fetch_sol_balance(client, wallet_address)
                    if sol_asset:
                        assets.append(sol_asset)
                        print(f"✅ [SOLANA DEBUG] Added SOL asset: {sol_asset.balance} SOL")
                    else:
                        print(f"⚠️ [SOLANA DEBUG] No SOL balance found or balance is zero")
                else:
                    print(f"🙈 [SOLANA DEBUG] SOL is hidden, skipping")

                # Get SPL tokens (both old and new program)
                print(f"🪙 [SOLANA DEBUG] Fetching SPL token accounts...")
                spl_assets = await self._fetch_spl_tokens(client, wallet_address, hidden_addresses)
                assets.extend(spl_assets)
                print(f"✅ [SOLANA DEBUG] Added {len(spl_assets)} SPL token assets")

        except Exception as e:
            print(f"❌ [SOLANA DEBUG] Major error in asset fetching: {e}")
            import traceback
            print(f"📋 [SOLANA DEBUG] Full traceback: {traceback.format_exc()}")

        print(f"🎯 [SOLANA DEBUG] Final result: {len(assets)} total assets found")
        return assets

    def _is_valid_solana_address(self, address: str) -> bool:
        """Basic Solana address validation - should be 32-44 chars, base58"""
        import re
        if not address or len(address) < 32 or len(address) > 44:
            return False
        # Check if it's valid base58 (no 0, O, I, l characters)
        base58_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
        return bool(re.match(base58_pattern, address))

    async def _fetch_sol_balance(self, client: httpx.AsyncClient, wallet_address: str) -> Optional[AssetData]:
        try:
            print(f"📊 [SOL BALANCE] Starting SOL balance fetch for {wallet_address}")

            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address]
            }

            print(f"🌐 [SOL BALANCE] RPC payload: {rpc_payload}")

            response = await client.post(
                self.solana_url,
                json=rpc_payload,
                headers={"Content-Type": "application/json"}
            )

            print(f"🌐 [SOL BALANCE] Response status: {response.status_code}")
            print(f"🌐 [SOL BALANCE] Response headers: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print(f"📈 [SOL BALANCE] Full response data: {data}")

                if "error" in data:
                    print(f"❌ [SOL BALANCE] RPC Error: {data['error']}")
                    return None

                if "result" in data and "value" in data["result"]:
                    sol_balance_lamports = data["result"]["value"]
                    sol_balance = sol_balance_lamports / 1_000_000_000  # Convert lamports to SOL
                    print(f"💰 [SOL BALANCE] Success! {sol_balance} SOL ({sol_balance_lamports} lamports)")

                    if sol_balance > 0:
                        return AssetData(
                            token_address="solana",
                            symbol="SOL",
                            name="Solana",
                            balance=sol_balance,
                            balance_formatted=f"{sol_balance:.6f}",
                            decimals=9
                        )
                    else:
                        print(f"⚠️ [SOL BALANCE] Zero balance found")
                else:
                    print(f"❌ [SOL BALANCE] Unexpected response format: {data}")
            else:
                error_text = response.text
                print(f"❌ [SOL BALANCE] HTTP error {response.status_code}: {error_text}")

        except Exception as e:
            print(f"❌ [SOL BALANCE] Exception: {e}")
            import traceback
            print(f"📋 [SOL BALANCE] Traceback: {traceback.format_exc()}")

        return None

    async def _fetch_spl_tokens(self, client: httpx.AsyncClient, wallet_address: str, hidden_addresses: set) -> List[AssetData]:
        assets = []

        # Fetch from both SPL Token program and SPL Token 2022 program
        program_ids = [self.spl_token_program, self.spl_token_2022_program]

        for program_id in program_ids:
            try:
                print(f"🪙 [SPL TOKENS] Fetching from program: {program_id}")

                rpc_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [
                        wallet_address,
                        {"programId": program_id},
                        {"encoding": "jsonParsed"}
                    ]
                }

                print(f"🌐 [SPL TOKENS] RPC payload: {rpc_payload}")

                response = await client.post(
                    self.solana_url,
                    json=rpc_payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"🌐 [SPL TOKENS] Response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"📊 [SPL TOKENS] Full response: {data}")

                    if "error" in data:
                        print(f"❌ [SPL TOKENS] RPC Error: {data['error']}")
                        continue

                    if "result" in data and "value" in data["result"]:
                        token_accounts = data["result"]["value"]
                        print(f"📊 [SPL TOKENS] Found {len(token_accounts)} token accounts from {program_id}")

                        for i, token_account in enumerate(token_accounts):
                            try:
                                print(f"🔍 [SPL TOKENS] Processing account {i+1}/{len(token_accounts)}")
                                print(f"🔍 [SPL TOKENS] Account data: {token_account}")

                                # Navigate through the nested structure
                                account_data = token_account.get("account", {})
                                parsed_data = account_data.get("data", {})
                                parsed_info = parsed_data.get("parsed", {})
                                token_info = parsed_info.get("info", {})

                                token_amount = token_info.get("tokenAmount", {})
                                mint_address = token_info.get("mint", "")

                                print(f"🔍 [SPL TOKENS] Mint: {mint_address}")
                                print(f"🔍 [SPL TOKENS] Token amount info: {token_amount}")

                                # Skip if this token is hidden
                                if mint_address.lower() in hidden_addresses:
                                    print(f"🙈 [SPL TOKENS] Token {mint_address} is hidden, skipping")
                                    continue

                                # Get balance and decimals
                                ui_amount = token_amount.get("uiAmount")
                                balance = float(ui_amount) if ui_amount is not None else 0
                                decimals = token_amount.get("decimals", 0)

                                print(f"💰 [SPL TOKENS] Balance: {balance}, Decimals: {decimals}")

                                if balance > 0:  # Include all non-zero balances
                                    # Get token metadata
                                    symbol = mint_address[:8] + "..."  # Fallback
                                    name = f"SPL Token {mint_address[:12]}..."

                                    if mint_address in self.known_tokens:
                                        symbol = self.known_tokens[mint_address]["symbol"]
                                        name = self.known_tokens[mint_address]["name"]
                                        print(f"✅ [SPL TOKENS] Found known token: {symbol}")
                                    else:
                                        print(f"⚠️ [SPL TOKENS] Unknown token, using fallback name")

                                    asset = AssetData(
                                        token_address=mint_address,
                                        symbol=symbol,
                                        name=name,
                                        balance=balance,
                                        balance_formatted=f"{balance:.6f}",
                                        decimals=decimals
                                    )
                                    assets.append(asset)
                                    print(f"✅ [SPL TOKENS] Added token: {symbol} - {balance:.6f} ({mint_address[:12]}...)")
                                else:
                                    print(f"⚠️ [SPL TOKENS] Zero balance, skipping: {mint_address}")

                            except Exception as e:
                                print(f"❌ [SPL TOKENS] Error processing token account {i+1}: {e}")
                                import traceback
                                print(f"📋 [SPL TOKENS] Token processing traceback: {traceback.format_exc()}")
                    else:
                        print(f"❌ [SPL TOKENS] Unexpected response format: {data}")
                else:
                    error_text = response.text
                    print(f"❌ [SPL TOKENS] HTTP error {response.status_code}: {error_text}")

            except Exception as e:
                print(f"❌ [SPL TOKENS] Major error fetching from {program_id}: {e}")
                import traceback
                print(f"📋 [SPL TOKENS] Major error traceback: {traceback.format_exc()}")

        print(f"🎯 [SPL TOKENS] Final result: {len(assets)} SPL tokens found")
        return assets

class SolanaPriceFetcher(PriceFetcher):
    def __init__(self):
        self.known_tokens = {
            "epjfwdd5aufqssqem2qn1xzybapC8g4wegghkzwytdt1v": {"symbol": "USDC", "coingecko_id": "usd-coin"},
            "es9vmfrzacermjfrf4h2fyd4kconky11mce8benwnyb": {"symbol": "USDT", "coingecko_id": "tether"},
            "so11111111111111111111111111111111111111112": {"symbol": "WSOL", "coingecko_id": "wrapped-solana"},
        }

    async def fetch_prices(self, token_addresses: List[str]) -> Dict[str, float]:
        price_map = {}

        print(f"💵 Fetching Solana prices for {len(token_addresses)} tokens...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get SOL price first
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": "solana", "vs_currencies": "usd"}
                )
                if response.status_code == 200:
                    data = response.json()
                    sol_price = data.get("solana", {}).get("usd", 0)
                    price_map["solana"] = sol_price
                    print(f"✅ SOL price: ${sol_price}")

                # Process mint addresses
                mint_addresses = [addr for addr in token_addresses if addr != "solana"]
                known_ids = []
                address_to_id = {}

                for addr in mint_addresses:
                    addr_lower = addr.lower()
                    if addr_lower in self.known_tokens:
                        coingecko_id = self.known_tokens[addr_lower]["coingecko_id"]
                        known_ids.append(coingecko_id)
                        address_to_id[coingecko_id] = addr_lower
                        print(f"✅ Found known Solana token: {self.known_tokens[addr_lower]['symbol']} -> {coingecko_id}")

                # Fetch known token prices
                if known_ids:
                    response = await client.get(
                        "https://api.coingecko.com/api/v3/simple/price",
                        params={"ids": ",".join(known_ids), "vs_currencies": "usd"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for coingecko_id, price_data in data.items():
                            if isinstance(price_data, dict) and "usd" in price_data:
                                addr = address_to_id.get(coingecko_id)
                                if addr:
                                    price_map[addr] = price_data["usd"]
                                    original_addr = next((a for a in mint_addresses if a.lower() == addr), addr)
                                    price_map[original_addr] = price_data["usd"]
                                    print(f"✅ Got Solana price: {addr} = ${price_data['usd']}")

                # Set fallback prices for unknown Solana tokens
                for addr in mint_addresses:
                    if addr.lower() not in price_map and addr not in price_map:
                        price_map[addr.lower()] = 0
                        price_map[addr] = 0
                        print(f"❌ No price found for Solana token: {addr}")

        except Exception as e:
            print(f"❌ Error fetching Solana prices: {e}")

        return price_map

# Chain factory
class ChainFactory:
    @staticmethod
    def create_asset_fetcher(network: str, alchemy_api_key: str) -> AssetFetcher:
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

    # Add missing columns if they don't exist
    try:
        cursor.execute('ALTER TABLE assets ADD COLUMN is_nft BOOLEAN DEFAULT FALSE')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE assets ADD COLUMN nft_metadata TEXT')
    except sqlite3.OperationalError:
        pass

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

    # Wallet status table (for tracking individual wallet fetch success/failure)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_status (
            wallet_id INTEGER PRIMARY KEY,
            status TEXT,
            assets_found INTEGER,
            total_value REAL,
            error_message TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wallet_id) REFERENCES wallets (id)
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
    id: str
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

# New chain-agnostic asset fetching function
async def get_wallet_assets_new(wallet_address: str, network: str) -> List[AssetData]:
    """New chain-agnostic asset fetching using dedicated fetchers"""

    # Don't pre-filter assets during fetching - let the database filtering handle display
    hidden_addresses = set()

    try:
        # Create appropriate asset fetcher for the network
        asset_fetcher = ChainFactory.create_asset_fetcher(network, ALCHEMY_API_KEY)

        # Fetch assets using chain-specific logic
        assets = await asset_fetcher.fetch_assets(wallet_address, hidden_addresses)

        print(f"✅ Fetched {len(assets)} assets for {network} wallet {wallet_address}")
        return assets

    except Exception as e:
        print(f"❌ Error fetching assets for {network} wallet {wallet_address}: {e}")
        return []

# New chain-agnostic price fetching function
async def get_token_prices_new(token_addresses_by_network: Dict[str, List[str]]) -> Dict[str, float]:
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
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "Crypto Fund API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for debugging"""
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()
    
    try:
        # Test database connection
        cursor.execute("SELECT COUNT(*) FROM wallets")
        wallet_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assets")
        asset_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM hidden_assets")
        hidden_count = cursor.fetchone()[0]
        
        return {
            "status": "healthy",
            "database": "connected",
            "tables": {
                "wallets": wallet_count,
                "assets": asset_count,
                "hidden_assets": hidden_count
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        conn.close()

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
    background_tasks.add_task(update_portfolio_data_new)
    return {"message": "Portfolio update started"}

@app.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    conn = sqlite3.connect('crypto_fund.db')
    cursor = conn.cursor()

    # Debug: Check what's in the assets table
    cursor.execute("SELECT COUNT(*) FROM assets")
    total_assets_count = cursor.fetchone()[0]
    print(f"🔍 [PORTFOLIO DEBUG] Total assets in database: {total_assets_count}")

    # Debug: Check hidden assets
    cursor.execute("SELECT token_address, symbol FROM hidden_assets")
    hidden_assets_debug = cursor.fetchall()
    print(f"🔍 [PORTFOLIO DEBUG] Hidden assets: {hidden_assets_debug}")

    # Debug: Check all assets before filtering
    cursor.execute("SELECT token_address, symbol, name, value_usd FROM assets ORDER BY value_usd DESC")
    all_assets_debug = cursor.fetchall()
    print(f"🔍 [PORTFOLIO DEBUG] All assets before filtering: {all_assets_debug}")

    # Get all assets with notes, excluding hidden ones
    cursor.execute("""
        SELECT a.token_address, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(n.notes, '') as notes
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        WHERE NOT EXISTS (
            SELECT 1 FROM hidden_assets h 
            WHERE LOWER(h.token_address) = LOWER(a.token_address)
        )
        ORDER BY a.value_usd DESC
    """)
    assets_data = cursor.fetchall()
    print(f"🔍 [PORTFOLIO DEBUG] Assets after filtering: {len(assets_data)} assets")
    
    if len(assets_data) > 0:
        print(f"🔍 [PORTFOLIO DEBUG] Sample asset: {assets_data[0]}")
    else:
        print(f"❌ [PORTFOLIO DEBUG] No assets returned by query!")

    assets = []
    for a in assets_data:
        try:
            asset = AssetResponse(
                id=a[0] if a[0] else a[1],  # Use token_address as id
                symbol=a[1] or "Unknown",
                name=a[2] or "Unknown Token",
                balance=float(a[3]) if a[3] else 0.0,
                balance_formatted=a[4] or "0.000000",
                price_usd=float(a[5]) if a[5] else 0.0,
                value_usd=float(a[6]) if a[6] else 0.0,
                notes=a[7] or ""
            )
            assets.append(asset)
            print(f"✅ [PORTFOLIO DEBUG] Created asset: {asset.symbol} = ${asset.value_usd:.2f}")
        except Exception as e:
            print(f"❌ [PORTFOLIO DEBUG] Error creating asset from {a}: {e}")
            continue

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
        SELECT a.token_address, a.symbol, a.name, a.balance, a.balance_formatted, 
               a.price_usd, a.value_usd, COALESCE(n.notes, '') as notes
        FROM assets a
        LEFT JOIN asset_notes n ON a.symbol = n.symbol
        WHERE a.wallet_id = ?
        ORDER BY a.value_usd DESC
    """, (wallet_id,))
    assets_data = cursor.fetchall()

    assets = []
    for a in assets_data:
        try:
            asset = AssetResponse(
                id=a[0] if a[0] else a[1],  # Use token_address as id
                symbol=a[1] or "Unknown",
                name=a[2] or "Unknown Token", 
                balance=float(a[3]) if a[3] else 0.0,
                balance_formatted=a[4] or "0.000000",
                price_usd=float(a[5]) if a[5] else 0.0,
                value_usd=float(a[6]) if a[6] else 0.0,
                notes=a[7] or ""
            )
            assets.append(asset)
        except Exception as e:
            print(f"❌ [WALLET DEBUG] Error creating asset from {a}: {e}")
            continue

    total_value = sum(asset.value_usd or 0 for asset in assets)

    conn.close()

    return WalletDetailsResponse(
        wallet=wallet,
        assets=assets,
        total_value=total_value,
        performance_24h=0.0
    )

@app.get("/wallets/status")
async def get_wallet_status():
    """Get status of all wallets including success/failure information"""
    conn = sqlite3.connect('crypto_fund.db')
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

    return [
        {
            "wallet_id": w[0],
            "address": w[1],
            "label": w[2],
            "network": w[3],
            "status": w[4],
            "assets_found": w[5],
            "total_value": w[6],
            "error_message": w[7],
            "last_updated": w[8]
        }
        for w in wallet_status_data
    ]

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
        print(f"✅ Hidden asset: {symbol} ({token_address})")
        return {"message": f"Asset {symbol} hidden successfully"}
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Error hiding asset: {e}")
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

async def update_portfolio_data_new():
    """New background task using chain-agnostic fetchers with comprehensive error handling"""
    conn = sqlite3.connect('crypto_fund.db')
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
        
        for wallet_id, address, network, label in wallets:
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
                    print(f"📡 Fetching assets for {network} wallet: {label} ({address[:10]}...)")
                    
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
                        token_addresses_by_network[network].add(asset.token_address)
                        wallet_assets_count += 1

                    # Update wallet status
                    wallet_status[wallet_id].update({
                        'status': 'success',
                        'assets_found': wallet_assets_count
                    })
                    print(f"✅ Successfully fetched {wallet_assets_count} assets from {label}")

                except asyncio.TimeoutError:
                    error_msg = f"Timeout after 60 seconds"
                    print(f"⏰ {error_msg} for {network} wallet {label} ({address[:10]}...)")
                    wallet_status[wallet_id].update({
                        'status': 'timeout',
                        'error': error_msg
                    })
                except Exception as e:
                    error_msg = str(e)[:200]  # Limit error message length
                    print(f"❌ Error fetching assets for {network} wallet {label} ({address[:10]}...): {error_msg}")
                    wallet_status[wallet_id].update({
                        'status': 'error',
                        'error': error_msg
                    })

        # Convert sets to lists for price fetching
        for network in token_addresses_by_network:
            token_addresses_by_network[network] = list(token_addresses_by_network[network])

        print(f"📊 Total assets fetched: {len(all_assets)}")
        print(f"🪙 Token addresses by network: {dict((k, len(v)) for k, v in token_addresses_by_network.items())}")

        # Print wallet status summary
        successful_wallets = sum(1 for s in wallet_status.values() if s['status'] == 'success')
        failed_wallets = sum(1 for s in wallet_status.values() if s['status'] in ['error', 'timeout'])
        print(f"📋 Wallet Status: {successful_wallets} successful, {failed_wallets} failed")

        # Get prices using new chain-agnostic price fetcher
        try:
            price_map = await asyncio.wait_for(
                get_token_prices_new(token_addresses_by_network), 
                timeout=30.0
            )
        except Exception as e:
            print(f"❌ Error fetching prices: {e}")
            price_map = {}

        # Insert assets with prices and calculate wallet values
        total_portfolio_value = 0
        auto_hide_candidates = []

        for asset in all_assets:
            is_nft = asset.get('is_nft', False)
            token_address = asset['token_address']
            wallet_id = asset['wallet_id']

            if is_nft:
                price_usd = 0
                value_usd = 0
                nft_metadata = json.dumps({
                    "token_ids": asset.get('token_ids', []),
                    "count": asset.get('balance', 0)
                })
                print(f"🖼️ NFT Asset: {asset['symbol']} - {asset['balance']} items")
            else:
                # Look up price with multiple fallbacks
                price_usd = price_map.get(token_address.lower(), 0)
                if price_usd == 0:
                    price_usd = price_map.get(token_address, 0)

                value_usd = asset['balance'] * price_usd
                nft_metadata = None

                print(f"💰 {asset['network']} Asset: {asset['symbol']} - Balance: {asset['balance']:.6f}, Price: ${price_usd:.6f}, Value: ${value_usd:.2f}")

                # Identify spam/scam tokens for auto-hiding (be very specific to avoid hiding legitimate assets)
                is_spam_token = (
                    value_usd == 0 and 
                    asset['balance'] > 0 and 
                    (
                        "visit" in asset['name'].lower() or 
                        "claim" in asset['name'].lower() or 
                        "rewards" in asset['name'].lower() or
                        "gift" in asset['name'].lower() or
                        "airdrop" in asset['name'].lower() or
                        (asset['symbol'] == "" and asset['name'] == "") or
                        len(asset['name']) > 50  # Suspiciously long names
                    )
                )

                if is_spam_token:
                    auto_hide_candidates.append({
                        'token_address': token_address,
                        'symbol': asset['symbol'],
                        'name': asset['name'],
                        'balance': asset['balance']
                    })

            # Update wallet status with value
            wallet_status[wallet_id]['total_value'] += value_usd
            total_portfolio_value += value_usd

            # Insert asset into database
            cursor.execute("""
                INSERT INTO assets 
                (wallet_id, token_address, symbol, name, balance, balance_formatted, price_usd, value_usd, is_nft, nft_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wallet_id, token_address, asset['symbol'], 
                asset['name'], asset['balance'], asset['balance_formatted'], 
                price_usd, value_usd, is_nft, nft_metadata
            ))

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
            cursor.execute("DELETE FROM hidden_assets WHERE LOWER(token_address) = LOWER(?)", (token_address,))
            print(f"🔓 Unhid valuable asset: {symbol} (${cursor.rowcount} rows removed)")

        # Auto-hide only confirmed spam/scam tokens
        if auto_hide_candidates:
            print(f"🔍 Auto-hiding {len(auto_hide_candidates)} confirmed spam tokens...")
            for spam_asset in auto_hide_candidates:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO hidden_assets (token_address, symbol, name)
                        VALUES (?, ?, ?)
                    """, (spam_asset['token_address'].lower(), spam_asset['symbol'], spam_asset['name']))
                    print(f"🙈 Auto-hidden spam: {spam_asset['symbol'] or 'unnamed'}")
                except sqlite3.Error as e:
                    print(f"❌ Error auto-hiding asset {spam_asset['symbol']}: {e}")

        # Record portfolio history
        cursor.execute(
            "INSERT INTO portfolio_history (total_value_usd) VALUES (?)",
            (total_portfolio_value,)
        )

        # Store wallet status for frontend consumption
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet_status (
                wallet_id INTEGER PRIMARY KEY,
                status TEXT,
                assets_found INTEGER,
                total_value REAL,
                error_message TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_id) REFERENCES wallets (id)
            )
        """)
        
        cursor.execute("DELETE FROM wallet_status")  # Clear old status
        for wallet_id, status_info in wallet_status.items():
            cursor.execute("""
                INSERT INTO wallet_status (wallet_id, status, assets_found, total_value, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                wallet_id, 
                status_info['status'],
                status_info['assets_found'],
                status_info['total_value'],
                status_info['error']
            ))

        conn.commit()
        
        # Final success summary
        successful_count = sum(1 for s in wallet_status.values() if s['status'] == 'success')
        total_count = len(wallet_status)
        print(f"✅ Portfolio updated successfully!")
        print(f"📈 {len(all_assets)} assets processed, ${total_portfolio_value:,.2f} total value")
        print(f"🏦 {successful_count}/{total_count} wallets processed successfully")
        
        # Print any failed wallets
        failed_wallets = [(s['label'], s['error']) for s in wallet_status.values() if s['status'] in ['error', 'timeout']]
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)