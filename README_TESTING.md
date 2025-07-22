# Testing Documentation

This document describes the comprehensive testing suite for the Crypto Fund application.

## 🚨 IMPORTANT: Dependency Conflict Resolution

Our test suite has been specifically designed to avoid conflicts between `web3` blockchain libraries and `pytest`. The tests use isolated dependencies and mock external services to ensure reliable test execution.

## Overview

The testing suite covers:
- **Backend API tests** - HTTP endpoint testing with mocked dependencies
- **Frontend component tests** - Build validation and configuration checks
- **Integration tests** - Full stack workflows with realistic scenarios
- **Database tests** - SQLite in-memory testing for data operations

## Quick Start

```bash
# Run all tests
python test_runner.py

# Run specific test category
python test_runner.py --backend
python test_runner.py --frontend
python test_runner.py --integration
python test_runner.py --build
```

## Test Structure

```
tests/
├── requirements-test.txt       # Isolated test dependencies
├── conftest.py                # Test fixtures and configuration
├── backend/                   # Backend-specific tests
│   ├── test_api_endpoints.py  # HTTP endpoint testing
│   ├── test_asset_fetchers.py # Data processing logic
│   └── test_database.py       # Database operations
├── frontend/                  # Frontend-specific tests
│   └── test_components.py     # Build and configuration tests
├── integration/               # Full stack integration tests
│   └── test_full_workflow.py  # End-to-end scenarios
└── utils/                     # Test utilities
    └── test_helpers.py        # Helper functions
```

## Key Features

### ✅ Dependency Isolation
- Uses `tests/requirements-test.txt` for isolated dependencies
- Avoids `web3` conflicts with pytest
- Mock-based testing for external APIs

### ✅ Comprehensive Mocking
- Database operations use SQLite in-memory
- External APIs (Alchemy, CoinGecko) are mocked
- Blockchain libraries are avoided in tests

### ✅ HTTP-Based Testing
- Tests actual API endpoints via HTTP
- No direct import of server modules that cause conflicts
- Realistic request/response testing

### ✅ Fast Execution
- Tests run in under 30 seconds
- No external network dependencies
- Efficient mock data generation

## Test Categories

### Backend Tests (`tests/backend/`)

**API Endpoints** - Tests HTTP endpoints:
- `GET /health` - Health check
- `GET /wallets` - List wallets
- `POST /wallets` - Add wallet
- `DELETE /wallets/{id}` - Remove wallet
- `GET /portfolio` - Portfolio data
- `POST /portfolio/update` - Update portfolio

**Asset Fetchers** - Tests data processing logic:
- Address validation (Ethereum/Solana)
- Balance formatting
- Price calculations
- P&L calculations
- Error handling

**Database Operations** - Tests with SQLite:
- CRUD operations
- Data integrity
- Transaction handling
- Schema migrations

### Frontend Tests (`tests/frontend/`)
- Build process validation
- NPM dependency verification  
- Configuration file checks
- Asset compilation testing

### Integration Tests (`tests/integration/`)
- Full workflow testing
- API integration scenarios
- Error handling flows
- Performance benchmarks

## Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
addopts = 
    -v --tb=short --disable-warnings
    -p no:web3 -p no:ethereum
markers =
    backend: Backend API tests
    frontend: Frontend build tests
    integration: Full stack tests
    isolated: Unit tests with mocks
```

### Environment Variables
```bash
NODE_ENV=test
DATABASE_URL=sqlite:///:memory:
ALCHEMY_API_KEY=test_key
```

## Troubleshooting

### Common Issues

**1. Import Errors with web3**
```bash
# Solution: Use isolated test dependencies
pip install -r tests/requirements-test.txt
```

**2. Database Connection Errors**  
```bash
# Tests use in-memory SQLite by default
export DATABASE_URL=sqlite:///:memory:
```

**3. Node.js Dependencies**
```bash
# Install frontend dependencies
npm install
```

**4. Test Timeout Issues**
```bash
# Run with increased timeout
pytest --timeout=60
```

### Debug Mode
```bash
# Verbose output
python test_runner.py --backend -v

# Run specific test
pytest tests/backend/test_api_endpoints.py::TestHealthEndpoint::test_health_endpoint_accessible -v
```

## Mock Data

Our tests use realistic mock data:
- **Portfolio Data**: $142K total value with 6 assets
- **Wallet Data**: Ethereum and Solana addresses
- **Price Data**: Current market prices
- **API Responses**: Realistic JSON structures

## Best Practices

### Writing Tests
1. Use descriptive test names
2. Mock external dependencies
3. Test both success and error cases
4. Keep tests fast and focused
5. Use appropriate fixtures

### Performance
- Tests complete in < 30 seconds
- Use mocks instead of real API calls
- SQLite in-memory for database tests
- Parallel execution where possible

## Continuous Integration

### Pre-deployment Checklist
```bash
# Full test suite
python test_runner.py

# Check exit code
echo $? # Should be 0 for success
```

### Test Reports
- JSON reports in `test_report.json`
- Console output with status indicators
- Detailed failure information
- Performance metrics

## Success Criteria

After running tests, you should see:
- ✅ Backend Tests: PASS
- ✅ Frontend Tests: PASS  
- ✅ Integration Tests: PASS
- ✅ Build Tests: PASS
- 🎯 Overall Status: ALL TESTS PASSED

This indicates your application is ready for deployment with confidence that all major functionality works correctly.
```# Run all tests
python test_runner.py

# Run specific test category
python test_runner.py --backend
python test_runner.py --frontend
python test_runner.py --integration
python test_runner.py --build
```

## Test Structure

```
tests/
├── requirements-test.txt       # Isolated test dependencies
├── conftest.py                # Test fixtures and configuration
├── backend/                   # Backend-specific tests
│   ├── test_api_endpoints.py  # HTTP endpoint testing
│   ├── test_asset_fetchers.py # Data processing logic
│   └── test_database.py       # Database operations
├── frontend/                  # Frontend-specific tests
│   └── test_components.py     # Build and configuration tests
├── integration/               # Full stack integration tests
│   └── test_full_workflow.py  # End-to-end scenarios
└── utils/                     # Test utilities
    └── test_helpers.py        # Helper functions
```

## Key Features

### ✅ Dependency Isolation
- Uses `tests/requirements-test.txt` for isolated dependencies
- Avoids `web3` conflicts with pytest
- Mock-based testing for external APIs

### ✅ Comprehensive Mocking
- Database operations use SQLite in-memory
- External APIs (Alchemy, CoinGecko) are mocked
- Blockchain libraries are avoided in tests

### ✅ HTTP-Based Testing
- Tests actual API endpoints via HTTP
- No direct import of server modules that cause conflicts
- Realistic request/response testing

### ✅ Fast Execution
- Tests run in under 30 seconds
- No external network dependencies
- Efficient mock data generation

## Test Categories

### Backend Tests (`tests/backend/`)

**API Endpoints** - Tests HTTP endpoints:
- `GET /health` - Health check
- `GET /wallets` - List wallets
- `POST /wallets` - Add wallet
- `DELETE /wallets/{id}` - Remove wallet
- `GET /portfolio` - Portfolio data
- `POST /portfolio/update` - Update portfolio

**Asset Fetchers** - Tests data processing logic:
- Address validation (Ethereum/Solana)
- Balance formatting
- Price calculations
- P&L calculations
- Error handling

**Database Operations** - Tests with SQLite:
- CRUD operations
- Data integrity
- Transaction handling
- Schema migrations

### Frontend Tests (`tests/frontend/`)
- Build process validation
- NPM dependency verification  
- Configuration file checks
- Asset compilation testing

### Integration Tests (`tests/integration/`)
- Full workflow testing
- API integration scenarios
- Error handling flows
- Performance benchmarks

## Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
addopts = 
    -v --tb=short --disable-warnings
    -p no:web3 -p no:ethereum
markers =
    backend: Backend API tests
    frontend: Frontend build tests
    integration: Full stack tests
    isolated: Unit tests with mocks
```

### Environment Variables
```bash
NODE_ENV=test
DATABASE_URL=sqlite:///:memory:
ALCHEMY_API_KEY=test_key
```

## Troubleshooting

### Common Issues

**1. Import Errors with web3**
```bash
# Solution: Use isolated test dependencies
pip install -r tests/requirements-test.txt
```

**2. Database Connection Errors**  
```bash
# Tests use in-memory SQLite by default
export DATABASE_URL=sqlite:///:memory:
```

**3. Node.js Dependencies**
```bash
# Install frontend dependencies
npm install
```

**4. Test Timeout Issues**
```bash
# Run with increased timeout
pytest --timeout=60
```

### Debug Mode
```bash
# Verbose output
python test_runner.py --backend -v

# Run specific test
pytest tests/backend/test_api_endpoints.py::TestHealthEndpoint::test_health_endpoint_accessible -v
```

## Mock Data

Our tests use realistic mock data:
- **Portfolio Data**: $142K total value with 6 assets
- **Wallet Data**: Ethereum and Solana addresses
- **Price Data**: Current market prices
- **API Responses**: Realistic JSON structures

## Best Practices

### Writing Tests
1. Use descriptive test names
2. Mock external dependencies
3. Test both success and error cases
4. Keep tests fast and focused
5. Use appropriate fixtures

### Performance
- Tests complete in < 30 seconds
- Use mocks instead of real API calls
- SQLite in-memory for database tests
- Parallel execution where possible

## Continuous Integration

### Pre-deployment Checklist
```bash
# Full test suite
python test_runner.py

# Check exit code
echo $? # Should be 0 for success