
"""
Minimal test to verify testing infrastructure works
"""
import pytest
import sqlite3
from unittest.mock import Mock

class TestMinimal:
    """Minimal tests to verify setup works."""
    
    def test_basic_assertion(self):
        """Test that basic assertions work."""
        assert 1 + 1 == 2
        assert "hello".upper() == "HELLO"
    
    def test_sqlite_works(self):
        """Test that sqlite3 works."""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        cursor.execute("INSERT INTO test (id, name) VALUES (?, ?)", (1, "test"))
        
        cursor.execute("SELECT * FROM test WHERE id = ?", (1,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 1
        assert result[1] == "test"
        
        conn.close()
    
    def test_mocking_works(self):
        """Test that mocking works."""
        mock_obj = Mock()
        mock_obj.method.return_value = "mocked"
        
        result = mock_obj.method()
        assert result == "mocked"
        mock_obj.method.assert_called_once()
    
    def test_environment_variables(self):
        """Test that test environment is set up."""
        import os
        assert os.environ.get("NODE_ENV") == "test"
        assert "sqlite" in os.environ.get("DATABASE_URL", "")
