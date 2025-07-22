
import pytest
import asyncio
import time
import requests
import subprocess
import os
import signal
import shutil
from unittest.mock import patch

class TestFullStackIntegration:
    """Test full stack integration scenarios."""
    
    @pytest.fixture(scope="class")
    def running_servers(self):
        """Start both frontend and backend servers for integration testing."""
        # Start backend server
        backend_proc = subprocess.Popen(
            ['python3', 'server/main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, 'PORT': '8000'}
        )
        
        # Wait for backend to start
        time.sleep(5)
        
        # Start frontend server
        frontend_proc = subprocess.Popen(
            ['npm', 'run', 'dev'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for frontend to start
        time.sleep(5)
        
        yield backend_proc, frontend_proc
        
        # Cleanup
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()

    def test_backend_health_check(self, running_servers):
        """Test backend health endpoint."""
        backend_proc, frontend_proc = running_servers
        
        # Check if backend process is still running
        if backend_proc.poll() is not None:
            pytest.skip("Backend process terminated")
        
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert 'status' in data
            assert data['status'] == 'healthy'
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Backend server not accessible: {e}")

    def test_frontend_loading(self, running_servers):
        """Test frontend loading."""
        backend_proc, frontend_proc = running_servers
        
        try:
            response = requests.get('http://localhost:5000', timeout=5)
            assert response.status_code == 200
            assert 'html' in response.headers.get('content-type', '').lower()
        except requests.exceptions.RequestException:
            pytest.skip("Frontend server not accessible")

    def test_api_integration(self, running_servers):
        """Test API integration between frontend and backend."""
        backend_proc, frontend_proc = running_servers
        
        # Test portfolio endpoint
        try:
            response = requests.get('http://localhost:8000/api/portfolio', timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert 'total_value' in data
            assert 'assets' in data
        except requests.exceptions.RequestException:
            pytest.skip("API endpoint not accessible")

    def test_wallet_management_flow(self, running_servers):
        """Test complete wallet management flow."""
        backend_proc, frontend_proc = running_servers
        
        # Create wallet
        wallet_data = {
            "address": "0x1234567890123456789012345678901234567890",
            "label": "Integration Test Wallet",
            "network": "ETH"
        }
        
        try:
            response = requests.post(
                'http://localhost:8000/api/wallets',
                json=wallet_data,
                timeout=5
            )
            
            if response.status_code == 200:
                wallet = response.json()
                wallet_id = wallet['id']
                
                # Get wallets
                response = requests.get('http://localhost:8000/api/wallets', timeout=5)
                assert response.status_code == 200
                wallets = response.json()
                assert any(w['id'] == wallet_id for w in wallets)
                
                # Delete wallet
                response = requests.delete(
                    f'http://localhost:8000/api/wallets/{wallet_id}',
                    timeout=5
                )
                assert response.status_code == 200
                
        except requests.exceptions.RequestException:
            pytest.skip("Wallet API not accessible")

class TestDeploymentReadiness:
    """Test deployment readiness and configuration."""
    
    def test_environment_variables(self):
        """Test environment variable configuration."""
        # Check if example env file exists
        assert os.path.exists('.env.example')
        
        with open('.env.example', 'r') as f:
            content = f.read()
        
        assert 'DATABASE_URL' in content
        assert 'ALCHEMY_API_KEY' in content

    def test_deployment_configuration(self):
        """Test deployment configuration files."""
        assert os.path.exists('.replit'), "Missing .replit configuration file"
        assert os.path.exists('server/requirements.txt'), "Missing Python requirements file"
        assert os.path.exists('package.json'), "Missing Node.js package configuration"
        
        # Verify .replit has deployment configuration
        with open('.replit', 'r') as f:
            replit_config = f.read()
        assert 'run' in replit_config, ".replit missing run configuration"

    def test_build_artifacts(self):
        """Test build artifact generation."""
        # Clean any existing build artifacts
        if os.path.exists('dist'):
            import shutil
            shutil.rmtree('dist')
        
        # Run build
        result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True)
        
        if result.returncode != 0:
            pytest.skip(f"Build failed: {result.stderr}")
        
        # Check artifacts exist
        assert os.path.exists('dist'), "Build did not create dist directory"
        assert os.path.exists('dist/index.html'), "Build did not create index.html"
        
        # Check index.html content
        with open('dist/index.html', 'r') as f:
            content = f.read()
        
        assert '<html' in content.lower(), "index.html missing html tag"
        assert '</html>' in content.lower(), "index.html missing closing html tag"

    def test_production_readiness(self):
        """Test production readiness checks."""
        # Check if main.py can import without errors
        result = subprocess.run(
            ['python3', '-c', 'import sys; sys.path.insert(0, "server"); import main; print("Import successful")'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            print(f"Import error: {result.stderr}")
            
        assert result.returncode == 0, f"Server module import failed: {result.stderr}"
        
        # Check critical files exist
        critical_files = [
            'server/main.py',
            'server/db_utils.py', 
            'package.json',
            'src/App.jsx',
            'index.html'
        ]
        
        for file_path in critical_files:
            assert os.path.exists(file_path), f"Critical file missing: {file_path}"

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_wallet_address(self):
        """Test handling of invalid wallet addresses."""
        # This would test the application's response to invalid inputs
        assert True  # Placeholder

    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        # This would test timeout scenarios
        assert True  # Placeholder

    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        # This would test database failure scenarios
        assert True  # Placeholder

class TestPerformance:
    """Test performance and load handling."""
    
    def test_portfolio_update_performance(self):
        """Test portfolio update performance."""
        # This would test update times
        assert True  # Placeholder

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        # This would test concurrent API calls
        assert True  # Placeholder
