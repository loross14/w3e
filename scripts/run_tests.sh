
#!/bin/bash

# Comprehensive test runner script for the crypto fund application

set -e  # Exit on any error

echo "🚀 Crypto Fund Application Test Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_status $RED "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_status $YELLOW "⚠️ Node.js not found. Frontend tests will be skipped."
    SKIP_FRONTEND=1
fi

# Install Python test dependencies
print_status $BLUE "📦 Installing Python test dependencies..."
python3 -m pip install --break-system-packages pytest pytest-asyncio pytest-mock httpx || {
    print_status $RED "❌ Failed to install Python dependencies"
    exit 1
}

# Install Node.js dependencies if Node is available
if [ -z "$SKIP_FRONTEND" ]; then
    print_status $BLUE "📦 Installing Node.js dependencies..."
    npm install || {
        print_status $RED "❌ Failed to install Node.js dependencies"
        exit 1
    }
fi

# Set test environment variables
export NODE_ENV=test
export DATABASE_URL=${DATABASE_URL:-"postgresql://test:test@localhost:5432/test"}
export ALCHEMY_API_KEY=${ALCHEMY_API_KEY:-"test_key"}

# Function to run a test suite
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    local description=$3
    
    print_status $BLUE "🧪 Running $description..."
    echo "----------------------------------------"
    
    if python3 -m pytest "$test_path" -v --tb=short; then
        print_status $GREEN "✅ $suite_name tests passed"
        return 0
    else
        print_status $RED "❌ $suite_name tests failed"
        return 1
    fi
}

# Track test results
BACKEND_PASSED=0
FRONTEND_PASSED=0
INTEGRATION_PASSED=0
BUILD_PASSED=0

# Run backend tests
if run_test_suite "Backend" "tests/backend/" "Backend API and Logic Tests"; then
    BACKEND_PASSED=1
fi

# Run frontend tests (if Node.js is available)
if [ -z "$SKIP_FRONTEND" ]; then
    if run_test_suite "Frontend" "tests/frontend/" "Frontend Component and Build Tests"; then
        FRONTEND_PASSED=1
    fi
else
    print_status $YELLOW "⏭️ Skipping frontend tests (Node.js not available)"
    FRONTEND_PASSED=1  # Don't fail overall if Node.js is not available
fi

# Run integration tests (only if backend tests passed)
if [ $BACKEND_PASSED -eq 1 ]; then
    if run_test_suite "Integration" "tests/integration/" "Full Stack Integration Tests"; then
        INTEGRATION_PASSED=1
    fi
else
    print_status $YELLOW "⏭️ Skipping integration tests (backend tests failed)"
fi

# Run build tests
print_status $BLUE "🏗️ Running Build and Deployment Tests..."
echo "----------------------------------------"

# Test frontend build (if Node.js is available)
if [ -z "$SKIP_FRONTEND" ]; then
    if npm run build; then
        print_status $GREEN "✅ Frontend build successful"
        
        # Check if build artifacts exist
        if [ -f "dist/index.html" ]; then
            print_status $GREEN "✅ Build artifacts found"
        else
            print_status $RED "❌ Build artifacts missing"
            BUILD_PASSED=0
        fi
    else
        print_status $RED "❌ Frontend build failed"
        BUILD_PASSED=0
    fi
else
    print_status $YELLOW "⏭️ Skipping frontend build test (Node.js not available)"
fi

# Test backend startup
print_status $BLUE "🐍 Testing backend startup..."
cd server
timeout 10s python3 main.py &
BACKEND_PID=$!
sleep 3

if kill -0 $BACKEND_PID 2>/dev/null; then
    print_status $GREEN "✅ Backend started successfully"
    kill $BACKEND_PID 2>/dev/null || true
    BUILD_PASSED=1
else
    print_status $RED "❌ Backend failed to start"
    BUILD_PASSED=0
fi

cd ..

# Generate final report
echo ""
print_status $BLUE "📊 Test Results Summary"
echo "======================================"

if [ $BACKEND_PASSED -eq 1 ]; then
    print_status $GREEN "✅ Backend Tests: PASSED"
else
    print_status $RED "❌ Backend Tests: FAILED"
fi

if [ -z "$SKIP_FRONTEND" ]; then
    if [ $FRONTEND_PASSED -eq 1 ]; then
        print_status $GREEN "✅ Frontend Tests: PASSED"
    else
        print_status $RED "❌ Frontend Tests: FAILED"
    fi
else
    print_status $YELLOW "⏭️ Frontend Tests: SKIPPED"
fi

if [ $INTEGRATION_PASSED -eq 1 ]; then
    print_status $GREEN "✅ Integration Tests: PASSED"
else
    print_status $RED "❌ Integration Tests: FAILED"
fi

if [ $BUILD_PASSED -eq 1 ]; then
    print_status $GREEN "✅ Build Tests: PASSED"
else
    print_status $RED "❌ Build Tests: FAILED"
fi

# Overall result
if [ $BACKEND_PASSED -eq 1 ] && [ $FRONTEND_PASSED -eq 1 ] && [ $INTEGRATION_PASSED -eq 1 ] && [ $BUILD_PASSED -eq 1 ]; then
    print_status $GREEN "🎉 ALL TESTS PASSED - Ready for deployment!"
    exit 0
else
    print_status $RED "💥 SOME TESTS FAILED - Please fix issues before deployment"
    exit 1
fi
