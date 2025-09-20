"""
Test Runner for Online Learning System Unit Tests
Runs all unit tests with proper organization and reporting

Usage:
    python unittest/run_tests.py
    python unittest/run_tests.py --ticket OLS-US-001
    python unittest/run_tests.py --api-only
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_pytest_tests(test_pattern=None):
    """Run pytest unit tests"""
    print("🧪 Running Unit Tests with pytest...")
    
    cmd = ['pytest', '-v', '--tb=short']
    
    if test_pattern:
        cmd.extend(['-k', test_pattern])
    
    # Add unittest directory
    cmd.append('unittest/')
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_api_tests():
    """Run API integration tests"""
    print("🌐 Running API Integration Tests...")
    
    try:
        result = subprocess.run([
            sys.executable, 'unittest/OLS_US_001_UserRegistration_API_Test.py'
        ], capture_output=True, text=True, timeout=120)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ API tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running API tests: {e}")
        return False

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Run Online Learning System Tests')
    parser.add_argument('--ticket', help='Run tests for specific ticket (e.g., OLS-US-001)')
    parser.add_argument('--api-only', action='store_true', help='Run only API tests')
    parser.add_argument('--unit-only', action='store_true', help='Run only unit tests')
    
    args = parser.parse_args()
    
    print("🚀 Online Learning System - Test Runner")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = []
    
    # Run unit tests
    if not args.api_only:
        print("\n📋 UNIT TESTS")
        print("-" * 30)
        
        test_pattern = None
        if args.ticket:
            test_pattern = args.ticket.replace('-', '_')
        
        unit_success = run_pytest_tests(test_pattern)
        results.append(('Unit Tests', unit_success))
    
    # Run API tests
    if not args.unit_only:
        print("\n📋 API INTEGRATION TESTS")
        print("-" * 30)
        
        api_success = run_api_tests()
        results.append(('API Tests', api_success))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_type, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_type}")
        if not success:
            all_passed = False
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("⚠️  Some tests failed.")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Testing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)