#!/usr/bin/env python3
"""Test runner for CVLens-Agent test suites."""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_environment_tests(comprehensive=False):
    """Run environment tests."""
    print("🔧 Running Environment Tests")
    print("=" * 60)
    
    if comprehensive:
        from tests.test_environment import TestEnvironmentInteractive
        interactive_test = TestEnvironmentInteractive()
        return interactive_test.run_comprehensive_test()
    else:
        import unittest
        from tests.test_environment import TestEnvironmentSetup
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestEnvironmentSetup)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()


def run_app_tests(comprehensive=False):
    """Run application component tests."""
    print("📱 Running Application Component Tests")
    print("=" * 60)
    
    if comprehensive:
        from tests.test_app import TestApplicationInteractive
        interactive_test = TestApplicationInteractive()
        return interactive_test.run_comprehensive_test()
    else:
        import unittest
        from tests.test_app import TestApplicationComponents
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestApplicationComponents)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()


def run_api_tests(interactive=False):
    """Run API connectivity tests."""
    print("🌐 Running API Connectivity Tests")
    print("=" * 60)
    
    if interactive:
        from tests.test_api import InteractiveAPITest
        interactive_test = InteractiveAPITest()
        return interactive_test.run_full_test_suite()
    else:
        import unittest
        from tests.test_api import TestAPIConnectivity
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIConnectivity)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()


def run_config_tests():
    """Run configuration tests."""
    print("⚙️  Running Configuration Tests")
    print("=" * 60)
    
    import unittest
    from tests.test_config import TestConfig
    from tests.test_config_real_env import TestConfigWithRealEnv
    
    # Create test suite
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestConfig))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestConfigWithRealEnv))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests(comprehensive=False, interactive=False):
    """Run all test suites."""
    print("🧪 CVLens-Agent Complete Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests in order
    test_suites = [
        ("Environment Tests", lambda: run_environment_tests(comprehensive)),
        ("Application Tests", lambda: run_app_tests(comprehensive)),
        ("Configuration Tests", run_config_tests),
        ("API Tests", lambda: run_api_tests(interactive)),
    ]
    
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
  python tests/run_tests.py                    # Run basic tests
  python tests/run_tests.py --all              # Run all test suites
  python tests/run_tests.py --environment      # Run environment tests only
  python tests/run_tests.py --api --interactive # Run interactive API tests
  python tests/run_tests.py --all --comprehensive --interactive # Full test suite
        """
    )
    
    # Test suite selection
    parser.add_argument('--all', action='store_true', 
                       help='Run all test suites')
    parser.add_argument('--environment', action='store_true',
                       help='Run environment tests')
    parser.add_argument('--app', action='store_true',
                       help='Run application component tests')
    parser.add_argument('--api', action='store_true',
                       help='Run API connectivity tests')
    parser.add_argument('--config', action='store_true',
                       help='Run configuration tests')
    
    # Test options
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run comprehensive tests with detailed output')
    parser.add_argument('--interactive', action='store_true',
                       help='Run interactive tests (includes authentication)')
    
    args = parser.parse_args()
    
    # If no specific test is selected, run basic environment tests
    if not any([args.all, args.environment, args.app, args.api, args.config]):
        print("No specific test selected. Running environment tests...")
        success = run_environment_tests(args.comprehensive)
        sys.exit(0 if success else 1)
    
    success = True
    
    if args.all:
        success = run_all_tests(args.comprehensive, args.interactive)
    else:
        if args.environment:
            success &= run_environment_tests(args.comprehensive)
        
        if args.app:
            success &= run_app_tests(args.comprehensive)
        
        if args.config:
            success &= run_config_tests()
        
        if args.api:
            success &= run_api_tests(args.interactive)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 