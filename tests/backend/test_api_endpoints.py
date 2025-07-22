
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi import status

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, test_client, mock_database):
        """Test successful health check."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = {"count": 5}
        
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "tables" in data

    def test_health_check_database_error(self, test_client):
        """Test health check with database error."""
        with patch('server.main.get_db_connection', side_effect=Exception("Database error")):
            response = test_client.get("/health")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data

class TestWalletEndpoints:
    """Test wallet management endpoints."""
    
    def test_create_wallet_success(self, test_client, mock_database):
        """Test successful wallet creation."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = {"id": 1}
        
        wallet_data = {
            "address": "0x1234567890123456789012345678901234567890",
            "label": "Test Wallet",
            "network": "ETH"
        }
        
        response = test_client.post("/api/wallets", json=wallet_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["address"] == wallet_data["address"]
        assert data["label"] == wallet_data["label"]
        assert data["network"] == wallet_data["network"]

    def test_create_wallet_duplicate(self, test_client, mock_database):
        """Test creating duplicate wallet."""
        mock_conn, mock_cursor = mock_database
        
        import psycopg2
        mock_cursor.execute.side_effect = psycopg2.IntegrityError("Duplicate key")
        
        wallet_data = {
            "address": "0x1234567890123456789012345678901234567890",
            "label": "Test Wallet",
            "network": "ETH"
        }
        
        response = test_client.post("/api/wallets", json=wallet_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_wallets(self, test_client, mock_database, sample_wallet_data):
        """Test retrieving wallets."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = sample_wallet_data
        
        response = test_client.get("/api/wallets")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["label"] == "Ethereum Safe Multisig"

    def test_delete_wallet_success(self, test_client, mock_database):
        """Test successful wallet deletion."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.rowcount = 1
        
        response = test_client.delete("/api/wallets/1")
        assert response.status_code == status.HTTP_200_OK

    def test_delete_wallet_not_found(self, test_client, mock_database):
        """Test deleting non-existent wallet."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.rowcount = 0
        
        response = test_client.delete("/api/wallets/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

class TestPortfolioEndpoints:
    """Test portfolio-related endpoints."""
    
    def test_get_portfolio_success(self, test_client, mock_database, sample_portfolio_data):
        """Test successful portfolio retrieval."""
        mock_conn, mock_cursor = mock_database
        
        # Mock database responses
        mock_cursor.fetchone.side_effect = [
            {"count": 6},  # total assets count
            [],  # hidden assets debug
            {"total_value_usd": sample_portfolio_data["total_value"]},  # saved total value
            {"count": 2},  # wallet count
        ]
        
        mock_cursor.fetchall.side_effect = [
            [],  # all assets debug
            sample_portfolio_data["assets"],  # assets data
            [{"total_value_usd": sample_portfolio_data["total_value"]}] * 2,  # performance history
        ]
        
        response = test_client.get("/api/portfolio")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_value" in data
        assert "assets" in data
        assert "wallet_count" in data

    @patch('server.main.update_portfolio_data_new')
    def test_update_portfolio_trigger(self, mock_update, test_client):
        """Test portfolio update trigger."""
        response = test_client.post("/api/portfolio/update")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Portfolio update started"

class TestAssetEndpoints:
    """Test asset management endpoints."""
    
    def test_update_asset_notes(self, test_client, mock_database):
        """Test updating asset notes."""
        mock_conn, mock_cursor = mock_database
        
        response = test_client.put("/api/assets/ETH/notes?notes=Test%20notes")
        assert response.status_code == status.HTTP_200_OK

    def test_update_purchase_price_success(self, test_client, mock_database):
        """Test successful purchase price update."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = {
            "symbol": "ETH",
            "balance": 10.0,
            "value_usd": 37173.2,
            "old_purchase_price": 2000.0
        }
        
        price_data = {"purchase_price": 2500.0}
        response = test_client.put("/api/assets/ETH/purchase_price", json=price_data)
        assert response.status_code == status.HTTP_200_OK

    def test_update_purchase_price_invalid(self, test_client, mock_database):
        """Test purchase price update with invalid data."""
        price_data = {"purchase_price": -100.0}
        response = test_client.put("/api/assets/ETH/purchase_price", json=price_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_hide_asset(self, test_client, mock_database):
        """Test hiding an asset."""
        params = {
            "token_address": "0x1234567890123456789012345678901234567890",
            "symbol": "TEST",
            "name": "Test Token"
        }
        
        response = test_client.post("/api/assets/hide", params=params)
        assert response.status_code == status.HTTP_200_OK

    def test_unhide_asset(self, test_client, mock_database):
        """Test unhiding an asset."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.rowcount = 1
        
        response = test_client.delete("/api/assets/hide/0x1234567890123456789012345678901234567890")
        assert response.status_code == status.HTTP_200_OK

    def test_get_hidden_assets(self, test_client, mock_database):
        """Test retrieving hidden assets."""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            {
                "token_address": "0x1234567890123456789012345678901234567890",
                "symbol": "TEST",
                "name": "Test Token",
                "hidden_at": "2024-01-01T00:00:00"
            }
        ]
        
        response = test_client.get("/api/assets/hidden")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "TEST"
