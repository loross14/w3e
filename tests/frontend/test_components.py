
import pytest
import os
import subprocess
import json
import tempfile

class TestFrontendBuild:
    """Test frontend build and compilation."""
    
    def test_npm_install(self):
        """Test npm package installation."""
        result = subprocess.run(['npm', 'list'], capture_output=True, text=True)
        assert result.returncode == 0 or "ELSPROBLEMS" in result.stderr

    def test_build_process(self):
        """Test frontend build process."""
        result = subprocess.run(['npm', 'run', 'build'], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Check if dist directory exists
        assert os.path.exists('dist')
        assert os.path.exists('dist/index.html')

    def test_dev_server_start(self):
        """Test if dev server can start (quick test)."""
        # Start dev server in background for quick test
        proc = subprocess.Popen(
            ['npm', 'run', 'dev'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a few seconds for server to start
        import time
        time.sleep(3)
        
        # Check if process is still running
        assert proc.poll() is None
        
        # Terminate the process
        proc.terminate()
        proc.wait()

class TestFrontendAPI:
    """Test frontend API integration."""
    
    def test_api_configuration(self):
        """Test API base URL configuration."""
        # Read the main App.jsx file
        with open('src/App.jsx', 'r') as f:
            content = f.read()
        
        # Check if API_BASE_URL is properly configured
        assert 'API_BASE_URL' in content
        assert 'localhost' in content or 'replit.dev' in content

    def test_component_structure(self):
        """Test React component structure."""
        with open('src/App.jsx', 'r') as f:
            content = f.read()
        
        # Check for main components
        assert 'MetricCard' in content
        assert 'AssetCard' in content
        assert 'WalletCard' in content
        assert 'PortfolioChart' in content

    def test_error_handling(self):
        """Test error handling in components."""
        with open('src/App.jsx', 'r') as f:
            content = f.read()
        
        # Check for error handling patterns
        assert 'try' in content and 'catch' in content
        assert 'updateError' in content
        assert 'setUpdateError' in content

class TestFrontendAssets:
    """Test frontend asset management."""
    
    def test_static_assets(self):
        """Test static asset files."""
        assert os.path.exists('public/favicon.svg')
        assert os.path.exists('public/manifest.json')

    def test_css_compilation(self):
        """Test CSS compilation with Tailwind."""
        assert os.path.exists('tailwind.config.js')
        assert os.path.exists('postcss.config.js')
        
        with open('src/index.css', 'r') as f:
            content = f.read()
        
        assert '@tailwind' in content

    def test_package_dependencies(self):
        """Test package.json dependencies."""
        with open('package.json', 'r') as f:
            package_data = json.load(f)
        
        # Check for critical dependencies
        deps = package_data.get('dependencies', {})
        dev_deps = package_data.get('devDependencies', {})
        
        assert 'react' in dev_deps
        assert 'chart.js' in deps
        assert 'jspdf' in deps
