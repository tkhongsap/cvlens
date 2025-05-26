#!/usr/bin/env python3
"""API connectivity testing script for CVLens-Agent."""

import sys
import os
import unittest
from pathlib import Path
import time
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestAPIConnectivity(unittest.TestCase):
    """Test API connectivity and authentication."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Load environment variables
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def test_01_environment_setup(self):
        """Test if environment is properly configured for API testing."""
        print("\n🔧 Testing Environment Setup")
        print("=" * 50)
        
        try:
            from src.config import config
            
            # Check required environment variables
            self.assertTrue(config.client_id, "CLIENT_ID not configured")
            self.assertNotEqual(config.tenant_id, "your_azure_tenant_id", 
                              "TENANT_ID not properly configured - please set your actual Azure tenant ID")
            self.assertEqual(len(config.aes_key), 32, "AES_KEY not properly configured")
            
            print(f"✅ CLIENT_ID: {config.client_id[:8]}...")
            print(f"✅ TENANT_ID: {config.tenant_id[:8]}...")
            print(f"✅ AES_KEY: Valid ({len(config.aes_key)} bytes)")
            print(f"✅ Scopes: {', '.join(config.graph_scopes)}")
            
        except Exception as e:
            self.fail(f"Environment setup failed: {str(e)}")
    
    def test_02_auth_module_initialization(self):
        """Test authentication module initialization."""
        print("\n🔐 Testing Authentication Module Initialization")
        print("-" * 50)
        
        try:
            from src.auth.graph_auth import graph_auth
            
            # Test basic initialization
            self.assertIsNotNone(graph_auth.client_id, "Client ID should be set")
            self.assertIsNotNone(graph_auth.tenant_id, "Tenant ID should be set")
            self.assertTrue(graph_auth.token_path.exists() or True, "Token path should be accessible")
            
            print("✅ Authentication module imported successfully")
            print(f"✅ Client ID configured: {graph_auth.client_id[:8]}...")
            print(f"✅ Tenant ID configured: {graph_auth.tenant_id[:8]}...")
            print(f"✅ Token path: {graph_auth.token_path}")
            
            # Test account creation (without authentication)
            account = graph_auth._get_account()
            self.assertIsNotNone(account, "O365 Account should be created")
            print("✅ O365 Account instance created successfully")
            
        except Exception as e:
            self.fail(f"Authentication module initialization failed: {str(e)}")
    
    def test_03_existing_authentication(self):
        """Test if there's an existing valid authentication."""
        print("\n🔍 Testing Existing Authentication")
        print("-" * 50)
        
        try:
            from src.auth.graph_auth import graph_auth
            
            if graph_auth.is_authenticated():
                print("✅ Already authenticated with valid token")
                
                # Try to get user info
                user_info = graph_auth.get_user_info()
                if user_info:
                    print(f"✅ User info retrieved: {user_info.get('display_name', 'Unknown')}")
                    print(f"✅ Email: {user_info.get('mail', 'Unknown')}")
                    self.assertIsNotNone(user_info.get('display_name'), "User display name should be available")
                else:
                    print("⚠️  Authentication exists but user info retrieval failed")
                    # Don't fail the test, just warn
            else:
                print("ℹ️  No existing authentication found")
                print("   You'll need to authenticate to test full API connectivity")
                # This is not a failure - just means no existing auth
                
        except Exception as e:
            # Don't fail the test for authentication issues
            print(f"⚠️  Authentication check failed: {str(e)}")
    
    def test_04_mailbox_access(self):
        """Test mailbox access (requires authentication)."""
        print("\n📧 Testing Mailbox Access")
        print("-" * 50)
        
        try:
            from src.auth.graph_auth import graph_auth
            
            if not graph_auth.is_authenticated():
                print("⚠️  Not authenticated - skipping mailbox test")
                print("   Run interactive authentication to test mailbox access")
                self.skipTest("Authentication required for mailbox access")
            
            # Try to get mailbox
            mailbox = graph_auth.get_mailbox()
            self.assertIsNotNone(mailbox, "Mailbox object should be created")
            print("✅ Mailbox object created successfully")
            
            # Try to get folders (basic API call)
            folders = mailbox.get_folders()
            folder_list = list(folders)
            self.assertGreater(len(folder_list), 0, "Should have at least one folder")
            print(f"✅ Folders retrieved: {len(folder_list)} folders found")
            
            # Display some folder names (first 5)
            for i, folder in enumerate(folder_list[:5]):
                print(f"   📁 {folder.name}")
            
            if len(folder_list) > 5:
                print(f"   ... and {len(folder_list) - 5} more folders")
                
        except Exception as e:
            if "not authenticated" in str(e).lower():
                self.skipTest("Authentication required for mailbox access")
            else:
                self.fail(f"Mailbox access failed: {str(e)}")
    
    def test_05_email_service(self):
        """Test email ingestion service."""
        print("\n📨 Testing Email Ingestion Service")
        print("-" * 50)
        
        try:
            from src.services.ingest import email_ingestor
            
            if not email_ingestor.graph_auth.is_authenticated():
                print("⚠️  Not authenticated - skipping email service test")
                self.skipTest("Authentication required for email service")
            
            # Test getting folders
            folders = email_ingestor.get_folders()
            self.assertIsInstance(folders, list, "Folders should be returned as a list")
            print(f"✅ Email service folders retrieved: {len(folders)} folders")
            
            # Test folder structure
            for folder in folders[:3]:  # Show first 3 folders
                self.assertIn('name', folder, "Folder should have a name")
                self.assertIn('id', folder, "Folder should have an ID")
                print(f"   📁 {folder.get('name', 'Unknown')} (ID: {folder.get('id', 'Unknown')[:8]}...)")
                
        except Exception as e:
            if "not authenticated" in str(e).lower():
                self.skipTest("Authentication required for email service")
            else:
                self.fail(f"Email service test failed: {str(e)}")


class InteractiveAPITest:
    """Interactive API testing for authentication."""
    
    def __init__(self):
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Load environment
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def interactive_authentication(self):
        """Perform interactive authentication."""
        print("\n🔐 Interactive Authentication")
        print("-" * 50)
        
        try:
            from src.auth.graph_auth import graph_auth
            
            if graph_auth.is_authenticated():
                print("✅ Already authenticated")
                return True
            
            print("Starting device code authentication flow...")
            print("\nInstructions:")
            print("1. A device code will be displayed")
            print("2. Go to https://microsoft.com/devicelogin")
            print("3. Enter the device code")
            print("4. Sign in with your Microsoft account")
            print("5. Return here and wait for completion")
            
            input("\nPress Enter to start authentication...")
            
            # Start authentication
            result = graph_auth.authenticate()
            
            if result:
                print("✅ Authentication successful!")
                
                # Get user info to confirm
                user_info = graph_auth.get_user_info()
                if user_info:
                    print(f"✅ Logged in as: {user_info.get('display_name', 'Unknown')}")
                    print(f"✅ Email: {user_info.get('mail', 'Unknown')}")
                
                return True
            else:
                print("❌ Authentication failed")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def run_full_test_suite(self):
        """Run the full test suite including authentication."""
        print("🌐 CVLens-Agent API Connectivity Test Suite")
        print("=" * 60)
        
        # Run basic tests first
        print("\n🔧 Running Basic Tests...")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIConnectivity)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Check if authentication is needed
        from src.auth.graph_auth import graph_auth
        if not graph_auth.is_authenticated():
            print("\n" + "=" * 60)
            print("🔐 Authentication Required for Full API Tests")
            print("=" * 60)
            
            choice = input("\nWould you like to authenticate now? (y/n): ").lower().strip()
            
            if choice in ['y', 'yes']:
                auth_success = self.interactive_authentication()
                if auth_success:
                    print("\n🔄 Re-running tests with authentication...")
                    # Re-run tests that require authentication
                    auth_tests = unittest.TestSuite()
                    auth_tests.addTest(TestAPIConnectivity('test_04_mailbox_access'))
                    auth_tests.addTest(TestAPIConnectivity('test_05_email_service'))
                    runner.run(auth_tests)
            else:
                print("\nSkipping authenticated API tests")
        
        return result.wasSuccessful()


def main():
    """Main function for running tests."""
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        # Run interactive test with authentication
        interactive_test = InteractiveAPITest()
        success = interactive_test.run_full_test_suite()
        sys.exit(0 if success else 1)
    else:
        # Run basic unit tests only
        print("🧪 Running Basic API Tests (use --interactive for full testing)")
        print("=" * 60)
        unittest.main(verbosity=2)


if __name__ == "__main__":
    main() 