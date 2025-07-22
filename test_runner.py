
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

    def run_backend_tests(self):
        """Run backend Python tests."""
        print("🐍 Running Backend Tests...")
        print("=" * 50)
        
        # Install test dependencies
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--break-system-packages",
            "pytest", "pytest-asyncio", "pytest-mock", "httpx"
        ], check=True)
        
        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/backend/", 
            "tests/utils/",
            "-v", 
            "--tb=short",
            "--json-report",
            "--json-report-file=test_results_backend.json"
        ], capture_output=True, text=True)
        
        self.test_results["backend_tests"] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        # Parse JSON report if available
        if os.path.exists("test_results_backend.json"):
            with open("test_results_backend.json") as f:
                report = json.load(f)
                self.test_results["backend_tests"]["summary"] = report.get("summary", {})
        
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
        except subprocess.CalledProcessError:
            print("❌ Node.js not found. Skipping frontend tests.")
            return False
        
        # Install dependencies if needed
        if not os.path.exists("node_modules"):
            print("📦 Installing npm dependencies...")
            subprocess.run(["npm", "install"], check=True)
        
        # Run frontend tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/frontend/",
            "-v",
            "--tb=short"
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
        
        # Run integration tests
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "-x"  # Stop on first failure for integration tests
        ], capture_output=True, text=True)
        
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
        build_result = subprocess.run(["npm", "run", "build"], capture_output=True, text=True)
        
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
        
        # Test backend startup
        print("\nTesting backend startup...")
        backend_proc = subprocess.Popen([
            sys.executable, "server/main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a few seconds
        time.sleep(3)
        
        if backend_proc.poll() is None:
            print("✅ Backend started successfully")
            backend_proc.terminate()
            backend_proc.wait()
        else:
            print("❌ Backend failed to start")
            stdout, stderr = backend_proc.communicate()
            print("STDOUT:", stdout.decode())
            print("STDERR:", stderr.decode())
            return False
        
        return True

    def generate_report(self):
        """Generate test report."""
        print("\n📊 Test Report")
        print("=" * 50)
        
        # Calculate totals
        backend_summary = self.test_results.get("backend_tests", {}).get("summary", {})
        
        passed = backend_summary.get("passed", 0)
        failed = backend_summary.get("failed", 0)
        skipped = backend_summary.get("skipped", 0)
        
        self.test_results["total_passed"] = passed
        self.test_results["total_failed"] = failed
        self.test_results["total_skipped"] = skipped
        
        # Print summary
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️ Skipped: {skipped}")
        print(f"📊 Total: {passed + failed + skipped}")
        
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
        
        with open("test_report.json", "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"📄 Detailed report saved to: test_report.json")
        
        return all_passed

    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 50)
        
        # Setup test environment
        os.environ["NODE_ENV"] = "test"
        os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
        os.environ.setdefault("ALCHEMY_API_KEY", "test_key")
        
        success = True
        
        # Run test suites
        try:
            # Backend tests
            if not self.run_backend_tests():
                success = False
            
            # Frontend tests
            if not self.run_frontend_tests():
                success = False
            
            # Integration tests (only if backend and frontend pass)
            if success:
                if not self.run_integration_tests():
                    success = False
            else:
                print("⏭️ Skipping integration tests due to earlier failures")
            
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
