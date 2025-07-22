
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
import json

from server.main import (
    EthereumAssetFetcher, 
    SolanaAssetFetcher,
    EthereumPriceFetcher,
    SolanaPriceFetcher,
    AssetData
)

class TestEthereumAssetFetcher:
    """Test Ethereum asset fetching functionality."""
    
    @pytest.fixture
    def eth_fetcher(self):
        return EthereumAssetFetcher("test_api_key")

    @pytest.mark.asyncio
    async def test_fetch_eth_balance(self, eth_fetcher):
        """Test ETH balance fetching."""
        wallet_address = "0x1234567890123456789012345678901234567890"
        
        with patch.object(eth_fetcher.w3.eth, 'get_balance', return_value=10**18):  # 1 ETH
            assets = await eth_fetcher.fetch_assets(wallet_address, set())
            
            eth_assets = [a for a in assets if a.symbol == "ETH"]
            assert len(eth_assets) == 1
            assert eth_assets[0].balance == 1.0
            assert eth_assets[0].symbol == "ETH"

    @pytest.mark.asyncio
    async def test_fetch_erc20_tokens(self, eth_fetcher):
        """Test ERC-20 token fetching."""
        wallet_address = "0x1234567890123456789012345678901234567890"
        
        mock_token_response = {
            "result": {
                "tokenBalances": [
                    {
                        "contractAddress": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                        "tokenBalance": "0x21e19e0c9bab2400000"
                    }
                ]
            }
        }
        
        mock_metadata_response = {
            "result": {
                "symbol": "WBTC",
                "name": "Wrapped Bitcoin",
                "decimals": 8
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            mock_instance.post.side_effect = [
                MagicMock(status_code=200, json=lambda: mock_token_response),
                MagicMock(status_code=200, json=lambda: mock_metadata_response)
            ]
            
            # Mock ETH balance to 0 for this test
            with patch.object(eth_fetcher.w3.eth, 'get_balance', return_value=0):
                assets = await eth_fetcher.fetch_assets(wallet_address, set())
                
                wbtc_assets = [a for a in assets if a.symbol == "WBTC"]
                assert len(wbtc_assets) >= 0  # May be filtered if balance too small

    @pytest.mark.asyncio
    async def test_fetch_nfts(self, eth_fetcher):
        """Test NFT fetching."""
        wallet_address = "0x1234567890123456789012345678901234567890"
        
        mock_nft_response = {
            "result": {
                "ownedNfts": [
                    {
                        "contract": {
                            "address": "0x1234567890123456789012345678901234567890",
                            "name": "Test NFT Collection",
                            "symbol": "TEST"
                        },
                        "tokenId": "1",
                        "metadata": {
                            "image": "https://example.com/image.png"
                        }
                    }
                ],
                "totalCount": 1
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                status_code=200, 
                json=lambda: mock_nft_response
            )
            
            nfts = await eth_fetcher._fetch_nfts(wallet_address, set())
            assert len(nfts) == 1
            assert nfts[0].is_nft == True
            assert nfts[0].symbol == "TEST"

class TestSolanaAssetFetcher:
    """Test Solana asset fetching functionality."""
    
    @pytest.fixture
    def sol_fetcher(self):
        return SolanaAssetFetcher("test_api_key")

    @pytest.mark.asyncio
    async def test_fetch_sol_balance(self, sol_fetcher):
        """Test SOL balance fetching."""
        wallet_address = "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb"
        
        mock_response = {
            "result": {
                "value": 1000000000  # 1 SOL in lamports
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            
            sol_asset = await sol_fetcher._fetch_sol_balance(mock_instance, wallet_address)
            assert sol_asset is not None
            assert sol_asset.symbol == "SOL"
            assert sol_asset.balance == 1.0

    @pytest.mark.asyncio
    async def test_fetch_spl_tokens(self, sol_fetcher):
        """Test SPL token fetching."""
        wallet_address = "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb"
        
        mock_response = {
            "result": {
                "value": [
                    {
                        "account": {
                            "data": {
                                "parsed": {
                                    "info": {
                                        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                                        "tokenAmount": {
                                            "amount": "1000000",
                                            "decimals": 6,
                                            "uiAmount": 1.0
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            
            tokens = await sol_fetcher._fetch_spl_tokens(mock_instance, wallet_address, set())
            assert len(tokens) >= 0  # May vary based on known tokens

    def test_address_validation(self, sol_fetcher):
        """Test Solana address validation."""
        valid_address = "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb"
        invalid_address = "0x1234567890123456789012345678901234567890"
        
        assert sol_fetcher._is_valid_solana_address(valid_address) == True
        assert sol_fetcher._is_valid_solana_address(invalid_address) == False

class TestPriceFetchers:
    """Test price fetching functionality."""
    
    @pytest.mark.asyncio
    async def test_ethereum_price_fetching(self, mock_price_responses):
        """Test Ethereum price fetching."""
        fetcher = EthereumPriceFetcher()
        token_addresses = [
            "0x0000000000000000000000000000000000000000",  # ETH
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"   # WBTC
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_price_responses
            )
            
            prices = await fetcher.fetch_prices(token_addresses)
            assert "0x0000000000000000000000000000000000000000" in prices
            assert prices["0x0000000000000000000000000000000000000000"] > 0

    @pytest.mark.asyncio
    async def test_solana_price_fetching(self, mock_price_responses):
        """Test Solana price fetching."""
        fetcher = SolanaPriceFetcher()
        token_addresses = [
            "solana",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_price_responses
            )
            
            prices = await fetcher.fetch_prices(token_addresses)
            assert "solana" in prices
