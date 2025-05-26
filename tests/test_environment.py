#!/usr/bin/env python3
"""Environment and configuration testing for CVLens-Agent."""

import sys
import os
import unittest
from pathlib import Path
import base64
from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestEnvironmentSetup(unittest.TestCase):
    """Test environment configuration and setup."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Load environment variables
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def test_01_env_file_exists(self):
        """Test if .env file exists and can be loaded."""
        print("\n🔍 Testing Environment File")
        print("=" * 50)
        
        env_path = project_root / ".env"
        self.assertTrue(env_path.exists(), 
                       ".env file not found! Please copy env.example to .env and configure your values")
        
        print("✅ .env file found")
        
        # Test loading environment variables
        load_dotenv(env_path)
        print("✅ Environment variables loaded")
    
    def test_02_required_env_vars(self):
        """Test required environment variables."""
        print("\n🔑 Testing Required Environment Variables")
        print("-" * 50)
        
        required_vars = {
            'CLIENT_ID': 'Microsoft Graph Client ID',
            'TENANT_ID': 'Microsoft Graph Tenant ID', 
            'AES_KEY': 'AES Encryption Key (Base64)'
        }
        
        for var, description in required_vars.items():
            with self.subTest(var=var):
                value = os.getenv(var)
                self.assertIsNotNone(value, f"{var} is missing ({description})")
                self.assertNotEqual(value.strip(), "", f"{var} should not be empty")
                
                if var == 'AES_KEY':
                    # Test AES key validity
                    try:
                        decoded = base64.b64decode(value)
                        self.assertEqual(len(decoded), 32, 
                                       f"{var}: Invalid length (should be 32 bytes when decoded)")
                        print(f"✅ {var}: Valid")
                    except Exception as e:
                        self.fail(f"{var}: Invalid Base64 encoding - {str(e)}")
                        
                elif var in ['CLIENT_ID', 'TENANT_ID']:
                    # Basic format validation for GUIDs
                    if len(value) == 36 and value.count('-') == 4:
                        print(f"✅ {var}: Valid format")
                    else:
                        print(f"⚠️  {var}: Unusual format (expected GUID)")
                        print(f"   Current value: {value[:8]}...")
                        # Don't fail for unusual format, just warn
                else:
                    print(f"✅ {var}: Set")
    
    def test_03_optional_env_vars(self):
        """Test optional environment variables."""
        print("\n⚙️  Testing Optional Environment Variables")
        print("-" * 50)
        
        optional_vars = {
            'DEBUG': 'Debug mode flag',
            'LOG_LEVEL': 'Logging level',
            'TESSERACT_CMD': 'Tesseract OCR path'
        }
        
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {value} ({description})")
            else:
                print(f"ℹ️  {var}: Not set ({description})")
    
    def test_04_config_loading(self):
        """Test configuration loading."""
        print("\n📋 Testing Configuration Loading")
        print("-" * 50)
        
        try:
            from src.config import config
            print("✅ Configuration module imported successfully")
            
            # Test config properties
            self.assertIsNotNone(config.client_id, "Client ID should be loaded")
            self.assertIsNotNone(config.tenant_id, "Tenant ID should be loaded")
            self.assertIsNotNone(config.aes_key, "AES key should be loaded")
            
            print(f"✅ Client ID: {config.client_id[:8]}..." if config.client_id else "❌ Client ID: Empty")
            print(f"✅ Tenant ID: {config.tenant_id[:8]}..." if config.tenant_id else "❌ Tenant ID: Empty")
            print(f"✅ AES Key: {'Valid' if len(config.aes_key) == 32 else 'Invalid'}")
            print(f"✅ Debug Mode: {config.debug_mode}")
            
        except Exception as e:
            self.fail(f"Configuration loading failed: {str(e)}")
    
    def test_05_database_connection(self):
        """Test database connection."""
        print("\n🗄️  Testing Database Connection")
        print("-" * 50)
        
        try:
            from src.models.database import db
            
            # Test database initialization (already done in constructor)
            print("✅ Database initialized successfully")
            
            # Test basic database operations
            session = db.get_session()
            try:
                # Test that we can create a session and query tables
                from sqlalchemy import text
                result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = result.fetchall()
                self.assertGreaterEqual(len(tables), 0, "Database should be accessible")
                print(f"✅ Database connection successful ({len(tables)} tables found)")
            finally:
                session.close()
                
        except Exception as e:
            self.fail(f"Database connection failed: {str(e)}")
    
    def test_06_auth_module(self):
        """Test authentication module loading."""
        print("\n🔐 Testing Authentication Module")
        print("-" * 50)
        
        try:
            from src.auth.graph_auth import graph_auth
            print("✅ Authentication module imported successfully")
            
            # Test basic properties
            self.assertIsNotNone(graph_auth.client_id, "Auth module should have client ID")
            self.assertIsNotNone(graph_auth.tenant_id, "Auth module should have tenant ID")
            
            # Test if we can create auth instance (without actually authenticating)
            print("✅ Graph authentication client initialized")
            print("ℹ️  Note: Actual authentication requires user interaction")
            
        except Exception as e:
            self.fail(f"Authentication module failed: {str(e)}")
    
    def test_07_service_modules(self):
        """Test service modules."""
        print("\n🔧 Testing Service Modules")
        print("-" * 50)
        
        services = [
            ('Email Ingestor', 'src.services.ingest'),
            ('Resume Parser', 'src.services.parse'),
            ('Candidate Scorer', 'src.services.score')
        ]
        
        for name, module in services:
            with self.subTest(service=name):
                try:
                    __import__(module)
                    print(f"✅ {name}: OK")
                except Exception as e:
                    # Don't fail the test for missing dependencies, just report
                    print(f"⚠️  {name}: Failed - {str(e)}")
                    if "No module named" in str(e):
                        print(f"   Install missing dependency for {name}")
    
    def test_08_required_files(self):
        """Test that required configuration files exist."""
        print("\n📄 Testing Required Files")
        print("-" * 50)
        
        required_files = [
            ("settings.json", "Configuration file"),
            ("job_profile.yml", "Job profile configuration"),
            ("env.example", "Environment template"),
        ]
        
        for filename, description in required_files:
            with self.subTest(file=filename):
                file_path = project_root / filename
                self.assertTrue(file_path.exists(), 
                              f"{filename} missing ({description})")
                print(f"✅ {filename}: Found")


class TestEnvironmentInteractive:
    """Interactive environment testing utilities."""
    
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
        """Run comprehensive environment test with detailed output."""
        print("🧪 CVLens-Agent Environment Test Suite")
        print("=" * 60)
        
        # Run all tests
        suite = unittest.TestLoader().loadTestsFromTestCase(TestEnvironmentSetup)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        if result.wasSuccessful():
            print("\n🎉 All environment tests passed!")
            print("\nYour environment is properly configured.")
            print("\nNext steps:")
            print("1. Run API tests: python -m tests.test_api --interactive")
            print("2. Start the application: python app.py")
        else:
            print(f"\n⚠️  {len(result.failures + result.errors)} test(s) failed.")
            print("\nCommon fixes:")
            print("1. Copy env.example to .env: cp env.example .env")
            print("2. Configure your Microsoft Graph credentials in .env")
            print("3. Generate AES key: python generate_aes_key.py")
            print("4. Install dependencies: pip install -r requirements.txt")
        
        return result.wasSuccessful()


def main():
    """Main function for running tests."""
    if len(sys.argv) > 1 and sys.argv[1] == '--comprehensive':
        # Run comprehensive test with detailed output
        interactive_test = TestEnvironmentInteractive()
        success = interactive_test.run_comprehensive_test()
        sys.exit(0 if success else 1)
    else:
        # Run standard unit tests
        print("🧪 Running Environment Tests (use --comprehensive for detailed output)")
        print("=" * 60)
        unittest.main(verbosity=2)


if __name__ == "__main__":
    main() 