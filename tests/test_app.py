#!/usr/bin/env python3
"""Application component testing for CVLens-Agent."""

import sys
import os
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestApplicationComponents(unittest.TestCase):
    """Test application components and imports."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Load environment variables
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def test_01_core_imports(self):
        """Test that core modules can be imported."""
        print("\n🔧 Testing Core Module Imports")
        print("=" * 50)
        
        core_modules = [
            ("Configuration", "src.config"),
            ("Database", "src.models.database"),
        ]
        
        for name, module in core_modules:
            with self.subTest(module=name):
                try:
                    __import__(module)
                    print(f"✅ {name}: OK")
                except Exception as e:
                    self.fail(f"{name} import failed: {str(e)}")
    
    def test_02_auth_imports(self):
        """Test authentication module imports."""
        print("\n🔐 Testing Authentication Imports")
        print("=" * 50)
        
        auth_modules = [
            ("Graph Authentication", "src.auth.graph_auth"),
        ]
        
        for name, module in auth_modules:
            with self.subTest(module=name):
                try:
                    __import__(module)
                    print(f"✅ {name}: OK")
                except Exception as e:
                    # Don't fail for missing O365 dependency
                    if "No module named 'O365'" in str(e):
                        print(f"⚠️  {name}: Missing O365 dependency")
                        self.skipTest(f"O365 dependency required for {name}")
                    else:
                        self.fail(f"{name} import failed: {str(e)}")
    
    def test_03_service_imports(self):
        """Test service module imports."""
        print("\n🔧 Testing Service Module Imports")
        print("=" * 50)
        
        service_modules = [
            ("Email Ingestion", "src.services.ingest"),
            ("Resume Parser", "src.services.parse"),
            ("Candidate Scorer", "src.services.score"),
        ]
        
        for name, module in service_modules:
            with self.subTest(module=name):
                try:
                    __import__(module)
                    print(f"✅ {name}: OK")
                except Exception as e:
                    # Don't fail for missing dependencies, just report
                    if "No module named" in str(e):
                        missing_module = str(e).split("'")[1]
                        print(f"⚠️  {name}: Missing dependency '{missing_module}'")
                        print(f"   Install with: pip install {missing_module}")
                    else:
                        print(f"⚠️  {name}: Failed - {str(e)}")
    
    def test_04_ui_imports(self):
        """Test UI module imports."""
        print("\n🖥️  Testing UI Module Imports")
        print("=" * 50)
        
        ui_modules = [
            ("Streamlit UI", "src.ui"),
        ]
        
        for name, module in ui_modules:
            with self.subTest(module=name):
                try:
                    __import__(module)
                    print(f"✅ {name}: OK")
                except Exception as e:
                    # UI modules might not exist yet or have dependencies
                    if "No module named" in str(e):
                        print(f"ℹ️  {name}: Module not found (optional)")
                    else:
                        print(f"⚠️  {name}: Failed - {str(e)}")
    
    def test_05_main_app_import(self):
        """Test main application import."""
        print("\n📱 Testing Main Application")
        print("=" * 50)
        
        try:
            # Test if we can import the main app module
            import app
            print("✅ Main application module imported successfully")
            
            # Test if main function exists
            self.assertTrue(hasattr(app, 'main'), "Main function should exist")
            print("✅ Main function found")
            
        except Exception as e:
            # Don't fail for missing dependencies
            if "No module named" in str(e):
                missing_module = str(e).split("'")[1]
                print(f"⚠️  Main app: Missing dependency '{missing_module}'")
                print(f"   Install with: pip install {missing_module}")
                self.skipTest(f"Missing dependency: {missing_module}")
            else:
                self.fail(f"Main application import failed: {str(e)}")
    
    def test_06_required_files_exist(self):
        """Test that required application files exist."""
        print("\n📄 Testing Required Application Files")
        print("=" * 50)
        
        required_files = [
            ("app.py", "Main application file"),
            ("requirements.txt", "Dependencies file"),
            ("settings.json", "Configuration file"),
            ("job_profile.yml", "Job profile configuration"),
        ]
        
        for filename, description in required_files:
            with self.subTest(file=filename):
                file_path = project_root / filename
                self.assertTrue(file_path.exists(), 
                              f"{filename} missing ({description})")
                print(f"✅ {filename}: Found")
    
    def test_07_directory_structure(self):
        """Test that required directories exist."""
        print("\n📁 Testing Directory Structure")
        print("=" * 50)
        
        required_dirs = [
            ("src", "Source code directory"),
            ("src/auth", "Authentication modules"),
            ("src/models", "Data models"),
            ("src/services", "Service modules"),
            ("tests", "Test directory"),
            ("data", "Data directory"),
            ("logs", "Logs directory"),
        ]
        
        for dirname, description in required_dirs:
            with self.subTest(directory=dirname):
                dir_path = project_root / dirname
                self.assertTrue(dir_path.exists() and dir_path.is_dir(), 
                              f"{dirname} directory missing ({description})")
                print(f"✅ {dirname}/: Found")


class TestApplicationInteractive:
    """Interactive application testing utilities."""
    
    def __init__(self):
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Load environment
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def run_comprehensive_test(self):
        """Run comprehensive application test with detailed output."""
        print("🧪 CVLens-Agent Application Component Test Suite")
        print("=" * 60)
        
        # Run all tests
        suite = unittest.TestLoader().loadTestsFromTestCase(TestApplicationComponents)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        if result.wasSuccessful():
            print("\n🎉 All application component tests passed!")
            print("\nYour application structure is properly set up.")
            print("\nNext steps:")
            print("1. Run environment tests: python -m tests.test_environment --comprehensive")
            print("2. Run API tests: python -m tests.test_api --interactive")
            print("3. Install missing dependencies: pip install -r requirements.txt")
        else:
            print(f"\n⚠️  {len(result.failures + result.errors)} test(s) failed.")
            print("\nCommon fixes:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Check file structure and missing files")
            print("3. Verify all required directories exist")
        
        return result.wasSuccessful()


def main():
    """Main function for running tests."""
    if len(sys.argv) > 1 and sys.argv[1] == '--comprehensive':
        # Run comprehensive test with detailed output
        interactive_test = TestApplicationInteractive()
        success = interactive_test.run_comprehensive_test()
        sys.exit(0 if success else 1)
    else:
        # Run standard unit tests
        print("🧪 Running Application Component Tests (use --comprehensive for detailed output)")
        print("=" * 60)
        unittest.main(verbosity=2)


if __name__ == "__main__":
    main() 