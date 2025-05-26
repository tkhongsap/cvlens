#!/usr/bin/env python3
"""Test runner for CVLens-Agent test suites."""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unit_tests(verbose=False):
    """Run unit tests."""
    print("🔧 Running Unit Tests")
    print("=" * 60)
    
    try:
        cmd = [sys.executable, "-m", "pytest", "tests/unit/", "-v" if verbose else "-q"]
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Unit tests passed")
            if verbose:
                print(result.stdout)
            return True
        else:
            print("❌ Unit tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running unit tests: {str(e)}")
        return False


def run_integration_tests(verbose=False, auth_required=False):
    """Run integration tests."""
    print("🌐 Running Integration Tests")
    print("=" * 60)
    
    try:
        cmd = [sys.executable, "-m", "pytest", "tests/integration/", "-v" if verbose else "-q"]
        if auth_required:
            cmd.append("--auth-required")
            
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Integration tests passed")
            if verbose:
                print(result.stdout)
            return True
        else:
            print("❌ Integration tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running integration tests: {str(e)}")
        return False


def run_system_tests(verbose=False):
    """Run system tests."""
    print("🖥️  Running System Tests")
    print("=" * 60)
    
    try:
        cmd = [sys.executable, "-m", "pytest", "tests/system/", "-v" if verbose else "-q"]
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ System tests passed")
            if verbose:
                print(result.stdout)
            return True
        else:
            print("❌ System tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running system tests: {str(e)}")
        return False


def run_performance_tests(verbose=False):
    """Run performance tests."""
    print("⚡ Running Performance Tests")
    print("=" * 60)
    
    try:
        cmd = [sys.executable, "-m", "pytest", "tests/performance/", "-v" if verbose else "-q", "--benchmark-only"]
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Performance tests passed")
            if verbose:
                print(result.stdout)
            return True
        else:
            print("❌ Performance tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running performance tests: {str(e)}")
        return False


def run_legacy_tests():
    """Run legacy test files for backward compatibility."""
    print("🔄 Running Legacy Tests")
    print("=" * 60)
    
    # Check if pytest is available
    try:
        import pytest
        pytest_available = True
    except ImportError:
        pytest_available = False
    
    if not pytest_available:
        print("⚠️  pytest not available, falling back to unittest")
        # Run individual test files
        success = True
        
        # Run unit tests
        try:
            from tests.unit.test_config_real_env import TestConfigWithRealEnv
            import unittest
            
            suite = unittest.TestLoader().loadTestsFromTestCase(TestConfigWithRealEnv)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            success &= result.wasSuccessful()
        except Exception as e:
            print(f"❌ Error running config tests: {str(e)}")
            success = False
        
        return success
    else:
        # Use pytest for all tests
        return run_all_tests_with_pytest()


def run_all_tests_with_pytest(verbose=False, auth_required=False, include_performance=False):
    """Run all tests using pytest."""
    print("🧪 CVLens-Agent Complete Test Suite (pytest)")
    print("=" * 60)
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v" if verbose else "-q"]
    
    if auth_required:
        cmd.append("--auth-required")
    
    if not include_performance:
        cmd.extend(["--ignore=tests/performance/"])
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running pytest: {str(e)}")
        return False


def run_all_tests(verbose=False, auth_required=False, include_performance=False):
    """Run all test suites."""
    print("🧪 CVLens-Agent Complete Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests in order
    test_suites = [
        ("Unit Tests", lambda: run_unit_tests(verbose)),
        ("Integration Tests", lambda: run_integration_tests(verbose, auth_required)),
        ("System Tests", lambda: run_system_tests(verbose)),
    ]
    
    if include_performance:
        test_suites.append(("Performance Tests", lambda: run_performance_tests(verbose)))
    
    for test_name, test_func in test_suites:
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            print(f"\n{test_name}: ❌ CRASHED - {str(e)}")
            results.append((test_name, False))
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 Final Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\nOverall Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All test suites passed!")
        print("\nYour CVLens-Agent setup is ready!")
        print("\nNext steps:")
        print("1. Start the application: python app.py")
        print("2. Or use the run scripts: run_local.bat (Windows) / ./run_local.sh (Linux/Mac)")
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed.")
        print("\nRecommended fixes:")
        print("1. Check environment configuration (.env file)")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Run individual test suites for detailed error information")
    
    return passed == total


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="CVLens-Agent Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py                    # Run all tests
  python tests/run_tests.py --unit             # Run unit tests only
  python tests/run_tests.py --integration      # Run integration tests only
  python tests/run_tests.py --system           # Run system tests only
  python tests/run_tests.py --performance      # Run performance tests only
  python tests/run_tests.py --all --verbose    # Run all tests with verbose output
  python tests/run_tests.py --integration --auth-required # Run integration tests with auth
        """
    )
    
    # Test suite selection
    parser.add_argument('--all', action='store_true', 
                       help='Run all test suites')
    parser.add_argument('--unit', action='store_true',
                       help='Run unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests')
    parser.add_argument('--system', action='store_true',
                       help='Run system tests')
    parser.add_argument('--performance', action='store_true',
                       help='Run performance tests')
    parser.add_argument('--legacy', action='store_true',
                       help='Run legacy tests for backward compatibility')
    
    # Test options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Run tests with verbose output')
    parser.add_argument('--auth-required', action='store_true',
                       help='Run tests that require authentication')
    
    args = parser.parse_args()
    
    # If no specific test is selected, run all tests
    if not any([args.all, args.unit, args.integration, args.system, args.performance, args.legacy]):
        print("No specific test selected. Running all tests...")
        success = run_all_tests(args.verbose, args.auth_required, False)
        sys.exit(0 if success else 1)
    
    success = True
    
    if args.all:
        success = run_all_tests(args.verbose, args.auth_required, True)
    else:
        if args.unit:
            success &= run_unit_tests(args.verbose)
        
        if args.integration:
            success &= run_integration_tests(args.verbose, args.auth_required)
        
        if args.system:
            success &= run_system_tests(args.verbose)
        
        if args.performance:
            success &= run_performance_tests(args.verbose)
        
        if args.legacy:
            success &= run_legacy_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 