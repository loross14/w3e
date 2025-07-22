
# Testing Documentation

This document describes the comprehensive testing suite for the Crypto Fund application.

## Overview

The testing suite covers:
- **Backend API tests** - FastAPI endpoints, database operations, blockchain integrations
- **Frontend component tests** - React components, build process, asset management
- **Integration tests** - Full stack workflows, API integration, deployment readiness
- **Performance tests** - Load testing, response times, resource usage

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── backend/                    # Backend-specific tests
│   ├── test_api_endpoints.py   # API endpoint testing
│   ├── test_asset_fetchers.py  # Blockchain data fetching
│   └── test_database.py        # Database operations
├── frontend/                   # Frontend-specific tests
│   └── test_components.py      # React components and build
├── integration/                # Full stack integration tests
│   └── test_full_workflow.py   # End-to-end workflows
└── utils/                      # Test utilities and helpers
    └── test_helpers.py         # Test data generators and helpers
```

## Running Tests

### Quick Start
```bash
# Run all tests
python test_runner.py

# Run specific test suite
python test_runner.py --backend
python test_runner.py --frontend
python test_runner.py --integration
python test_runner.py --build
```

### Using Shell Script
```bash
# Make executable and run
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

### Using pytest directly
```bash
# Install dependencies
pip install pytest pytest-asyncio pytest-mock httpx

# Run specific test categories
pytest tests/backend/ -v
pytest tests/frontend/ -v
pytest tests/integration/ -v
```

## Test Categories

### Backend Tests (`tests/backend/`)

#### API Endpoints (`test_api_endpoints.py`)
- Health check endpoint
- Wallet CRUD operations
- Portfolio data retrieval
- Asset management (notes, purchase prices, hiding)
- Error handling and validation

#### Asset Fetchers (`test_asset_fetchers.py`)
- Ethereum asset fetching (ETH, ERC-20, NFTs)
- Solana asset fetching (SOL, SPL tokens)
- Price fetching from multiple APIs
- Network error handling
- Address validation

#### Database Operations (`test_database.py`)
- Database initialization
- CRUD operations
- Migration testing
- Connection error handling

### Frontend Tests (`tests/frontend/`)

#### Component Tests (`test_components.py`)
- Build process validation
- NPM dependency checking
- Component structure verification
- Asset compilation (CSS, JS)
- Configuration validation

### Integration Tests (`tests/integration/`)

#### Full Workflow (`test_full_workflow.py`)
- Complete wallet management flow
- Portfolio update workflow
- API integration between frontend and backend
- Deployment readiness checks
- Error handling scenarios
- Performance benchmarks

### Test Utilities (`tests/utils/`)

#### Test Helpers (`test_helpers.py`)
- Test data generators
- Mock API response builders
- Environment setup/teardown
- Async test helpers
- Database test utilities

## Test Configuration

### Environment Variables
```bash
# Required for testing
export NODE_ENV=test
export DATABASE_URL=postgresql://test:test@localhost:5432/test
export ALCHEMY_API_KEY=test_key
```

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Async test support
- Custom markers for test categorization
- Output formatting

## Mock Data and Fixtures

### Sample Data Generation
The test suite includes generators for:
- Wallet data (Ethereum and Solana addresses)
- Asset data (tokens, NFTs, prices)
- API responses (Alchemy, CoinGecko, etc.)
- Database records

### Fixtures
- `mock_database` - Mocked database connections
- `test_client` - FastAPI test client
- `sample_portfolio_data` - Portfolio test data
- `mock_alchemy_responses` - Blockchain API mocks

## Continuous Integration

### Pre-deployment Checklist
Run the full test suite before any deployment:

```bash
# Full test suite with detailed reporting
python test_runner.py

# Check exit code
echo $?  # Should be 0 for success
```

### Test Reports
- JSON test reports generated in `test_report.json`
- Console output with color-coded results
- Failure details and stack traces
- Performance metrics

## Test Coverage

### Backend Coverage
- ✅ API endpoints (all routes)
- ✅ Database operations
- ✅ Blockchain integrations
- ✅ Error handling
- ✅ Data validation

### Frontend Coverage
- ✅ Build process
- ✅ Component structure
- ✅ Configuration validation
- ✅ Asset compilation

### Integration Coverage
- ✅ API integration
- ✅ Wallet management flow
- ✅ Portfolio updates
- ✅ Deployment readiness

## Best Practices

### Writing New Tests
1. Use descriptive test names
2. Include both positive and negative test cases
3. Mock external dependencies
4. Test error conditions
5. Use appropriate fixtures

### Test Data
1. Use generators for consistent test data
2. Clean up test data after tests
3. Avoid hardcoded values
4. Use realistic data scenarios

### Performance
1. Keep tests fast and focused
2. Use mocks for external APIs
3. Parallel test execution where possible
4. Clean up resources properly

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check if PostgreSQL is available
# Tests use mocked database by default
export DATABASE_URL=postgresql://test:test@localhost:5432/test
```

#### Node.js Dependencies
```bash
# Install Node.js dependencies
npm install

# Clear cache if needed
npm ci
```

#### Python Dependencies
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock httpx
```

### Debug Mode
```bash
# Run with verbose output
pytest -v -s

# Run specific test
pytest tests/backend/test_api_endpoints.py::TestHealthEndpoint::test_health_check_success -v
```

## Extending Tests

### Adding New Tests
1. Choose appropriate test category
2. Use existing fixtures and helpers
3. Follow naming conventions
4. Update documentation

### Adding New Fixtures
1. Add to `conftest.py`
2. Use appropriate scope
3. Include cleanup logic
4. Document usage

### Adding Mock Responses
1. Add to `tests/utils/test_helpers.py`
2. Use realistic data structures
3. Include error scenarios
4. Keep data consistent

## Integration with Development

### Pre-commit Testing
```bash
# Quick tests before committing
python test_runner.py --backend

# Full suite before major changes
python test_runner.py
```

### Development Workflow
1. Write tests for new features
2. Run relevant test suite
3. Fix any failures
4. Run full suite before deployment

This testing suite ensures robust validation of all application components and provides confidence for deployments and feature changes.
