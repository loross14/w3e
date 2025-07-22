
#!/usr/bin/env python3
"""
Comprehensive test runner for the crypto fund application.
This script runs all tests and provides detailed reporting.
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class TestRunner:
    """Main test runner class."""
    
    def __init__(self):
        self.test_results = {
            "start_time": datetime.now(),
            "backend_tests": {},
            "frontend_tests": {},
            "integration_tests": {},
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0
        }

    def install_test_dependencies(self):
        """Install isolated test dependencies."""
        print("📦 Installing test dependencies...")
        
        # Install from test requirements file
        if os.path.exists("tests/requirements-test.txt"):
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "--break-system-packages", 
                "-r", "tests/requirements-test.txt"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ Failed to install test dependencies:")
                print(result.stderr)
                return False
        else:
            # Fallback to individual packages
            packages = [
                "pytest==7.4.4", 
                "pytest-asyncio==0.21.1", 
                "pytest-mock==3.14.1",
                "httpx==0.25.2"
            ]
            
            for package in packages:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "--break-system-packages", package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ Failed to install {package}")
                    print(result.stderr)
                    return False
        
        print("✅ Test dependencies installed successfully")
        return True

    def run_backend_tests(self):
        """Run backend Python tests."""
        print("🐍 Running Backend Tests...")
        print("=" * 50)
        
        if not self.install_test_dependencies():
            return False
        
        # Set environment variables to avoid conflicts
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["NODE_ENV"] = "test"
        env["DATABASE_URL"] = "sqlite:///:memory:"
        
        # Run pytest with specific configuration to avoid web3 conflicts
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/backend/", 
            "tests/utils/",
            "-v", 
            "--tb=short",
            "--disable-warnings",
            "-p", "no:cacheprovider",
            "--maxfail=5"  # Stop after 5 failures
        ], capture_output=True, text=True, env=env)
        
        self.test_results["backend_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0

    def run_frontend_tests(self):
        """Run frontend tests."""
        print("\n⚛️ Running Frontend Tests...")
        print("=" * 50)
        
        # Check if Node.js is available
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Node.js not found. Skipping frontend tests.")
            self.test_results["frontend_tests"] = {
                "exit_code": 0,
                "stdout": "Skipped - Node.js not available",
                "stderr": ""
            }
            return True
        
        # Install dependencies if needed
        if not os.path.exists("node_modules"):
            print("📦 Installing npm dependencies...")
            result = subprocess.run(["npm", "install"], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Failed to install npm dependencies")
                print(result.stderr)
                return False
        
        # Run frontend tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/frontend/",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ], capture_output=True, text=True)
        
        self.test_results["frontend_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0

    def run_integration_tests(self):
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        print("=" * 50)
        
        # Set test environment
        env = os.environ.copy()
        env["NODE_ENV"] = "test"
        env["DATABASE_URL"] = "sqlite:///:memory:"
        
        # Run integration tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "--disable-warnings",
            "-x"  # Stop on first failure for integration tests
        ], capture_output=True, text=True, env=env)
        
        self.test_results["integration_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0

    def run_build_tests(self):
        """Run build and deployment tests."""
        print("\n🏗️ Running Build Tests...")
        print("=" * 50)
        
        # Test frontend build
        print("Testing frontend build...")
        try:
            build_result = subprocess.run(["npm", "run", "build"], 
                                        capture_output=True, text=True, timeout=60)
            
            if build_result.returncode == 0:
                print("✅ Frontend build successful")
                
                # Check build artifacts
                if os.path.exists("dist/index.html"):
                    print("✅ Build artifacts found")
                else:
                    print("❌ Build artifacts missing")
                    return False
            else:
                print("❌ Frontend build failed:")
                print(build_result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Frontend build timed out")
            return False
        except FileNotFoundError:
            print("⚠️ npm not available, skipping build test")
            return True
        
        # Test backend startup (quick test)
        print("\nTesting backend startup...")
        try:
            # Quick syntax check
            result = subprocess.run([
                sys.executable, "-c", 
                "import sys; sys.path.append('server'); import main; print('✅ Backend imports successfully')"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Backend syntax check passed")
            else:
                print("❌ Backend syntax check failed:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Backend syntax check timed out")
            return False
        except Exception as e:
            print(f"❌ Backend test error: {e}")
            return False
        
        return True

    def generate_report(self):
        """Generate test report."""
        print("\n📊 Test Report")
        print("=" * 50)
        
        # Extract test counts from pytest output
        backend_passed = 0
        backend_failed = 0
        backend_skipped = 0
        
        if self.test_results["backend_tests"].get("stdout"):
            output = self.test_results["backend_tests"]["stdout"]
            if "passed" in output:
                try:
                    # Try to extract numbers from pytest summary
                    lines = output.split('\n')
                    for line in lines:
                        if " passed" in line and "failed" not in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "passed":
                                    backend_passed = int(parts[i-1])
                                    break
                        elif " failed" in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "failed":
                                    backend_failed = int(parts[i-1])
                                    break
                except (ValueError, IndexError):
                    pass
        
        self.test_results["total_passed"] = backend_passed
        self.test_results["total_failed"] = backend_failed
        self.test_results["total_skipped"] = backend_skipped
        
        # Print summary
        print(f"✅ Passed: {backend_passed}")
        print(f"❌ Failed: {backend_failed}")
        print(f"⏭️ Skipped: {backend_skipped}")
        print(f"📊 Total: {backend_passed + backend_failed + backend_skipped}")
        
        # Test categories
        backend_status = "✅ PASS" if self.test_results["backend_tests"].get("exit_code") == 0 else "❌ FAIL"
        frontend_status = "✅ PASS" if self.test_results["frontend_tests"].get("exit_code") == 0 else "❌ FAIL"
        integration_status = "✅ PASS" if self.test_results["integration_tests"].get("exit_code") == 0 else "❌ FAIL"
        
        print(f"\n🐍 Backend Tests: {backend_status}")
        print(f"⚛️ Frontend Tests: {frontend_status}")
        print(f"🔗 Integration Tests: {integration_status}")
        
        # Overall status
        all_passed = all([
            self.test_results["backend_tests"].get("exit_code") == 0,
            self.test_results["frontend_tests"].get("exit_code") == 0,
            self.test_results["integration_tests"].get("exit_code") == 0
        ])
        
        print(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        # Save detailed report
        self.test_results["end_time"] = datetime.now()
        self.test_results["duration"] = str(self.test_results["end_time"] - self.test_results["start_time"])
        
        try:
            with open("test_report.json", "w") as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"📄 Detailed report saved to: test_report.json")
        except Exception as e:
            print(f"⚠️ Could not save detailed report: {e}")
        
        return all_passed

    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 50)
        
        # Setup test environment
        os.environ["NODE_ENV"] = "test"
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        os.environ.setdefault("ALCHEMY_API_KEY", "test_key")
        
        success = True
        
        # Run test suites
        try:
            # Backend tests
            if not self.run_backend_tests():
                print("⚠️ Backend tests failed, but continuing...")
                success = False
            
            # Frontend tests
            if not self.run_frontend_tests():
                print("⚠️ Frontend tests failed, but continuing...")
                success = False
            
            # Integration tests (only if backend tests pass)
            if self.test_results["backend_tests"].get("exit_code") == 0:
                if not self.run_integration_tests():
                    success = False
            else:
                print("⏭️ Skipping integration tests due to backend test failures")
                self.test_results["integration_tests"] = {
                    "exit_code": -1,
                    "stdout": "Skipped due to backend failures",
                    "stderr": ""
                }
            
            # Build tests
            if not self.run_build_tests():
                success = False
            
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
            success = False
        except Exception as e:
            print(f"\n❌ Test runner error: {e}")
            success = False
        
        # Generate report
        return self.generate_report()

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Crypto Fund Test Runner")
        print("Usage: python test_runner.py [options]")
        print("\nOptions:")
        print("  --backend    Run only backend tests")
        print("  --frontend   Run only frontend tests")
        print("  --integration Run only integration tests")
        print("  --build      Run only build tests")
        print("  --help       Show this help message")
        return
    
    runner = TestRunner()
    
    # Check for specific test type
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "--backend":
            success = runner.run_backend_tests()
        elif test_type == "--frontend":
            success = runner.run_frontend_tests()
        elif test_type == "--integration":
            success = runner.run_integration_tests()
        elif test_type == "--build":
            success = runner.run_build_tests()
        else:
            print(f"Unknown option: {test_type}")
            return 1
        
        return 0 if success else 1
    
    # Run all tests
    success = runner.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
