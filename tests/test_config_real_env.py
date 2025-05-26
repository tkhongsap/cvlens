"""Test configuration with real .env file values."""

import unittest
import os
from pathlib import Path
from dotenv import load_dotenv


class TestConfigWithRealEnv(unittest.TestCase):
    """Test Config class with real environment variables from .env file."""
    
    def setUp(self):
        """Set up test environment."""
        # Load the real .env file
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            self.skipTest("No .env file found - cannot test with real environment variables")
    
    def test_env_file_exists(self):
        """Test that .env file exists."""
        env_path = Path(__file__).parent.parent / ".env"
        self.assertTrue(env_path.exists(), ".env file should exist")
    
    def test_required_env_vars_present(self):
        """Test that all required environment variables are present."""
        required_vars = ['CLIENT_ID', 'TENANT_ID', 'AES_KEY']
        
        for var in required_vars:
            with self.subTest(var=var):
                value = os.getenv(var)
                self.assertIsNotNone(value, f"{var} should be set in .env file")
                self.assertNotEqual(value.strip(), "", f"{var} should not be empty")
    
    def test_config_initialization_with_real_env(self):
        """Test Config initialization with real environment variables."""
        try:
            from src.config import Config
            config = Config()
            
            # Test that config loads successfully
            self.assertIsNotNone(config.client_id)
            self.assertIsNotNone(config.tenant_id)
            self.assertIsNotNone(config.aes_key)
            
            # Test that values are not empty
            self.assertNotEqual(config.client_id.strip(), "")
            self.assertNotEqual(config.tenant_id.strip(), "")
            
            # Test AES key is valid bytes
            self.assertIsInstance(config.aes_key, bytes)
            self.assertGreater(len(config.aes_key), 0)
            
            print(f"✅ CLIENT_ID: {config.client_id[:8]}...")
            print(f"✅ TENANT_ID: {config.tenant_id[:8]}...")
            print(f"✅ AES_KEY: {len(config.aes_key)} bytes")
            
        except Exception as e:
            self.fail(f"Config initialization failed: {str(e)}")
    
    def test_aes_key_format(self):
        """Test that AES key is properly base64 encoded."""
        import base64
        from cryptography.fernet import Fernet
        
        aes_key_str = os.getenv('AES_KEY')
        self.assertIsNotNone(aes_key_str, "AES_KEY should be set")
        
        try:
            # Should be able to decode from base64
            decoded_key = base64.b64decode(aes_key_str)
            
            # Should be valid for Fernet
            cipher = Fernet(decoded_key)
            
            # Test encryption/decryption
            test_message = "test message"
            encrypted = cipher.encrypt(test_message.encode())
            decrypted = cipher.decrypt(encrypted).decode()
            
            self.assertEqual(test_message, decrypted)
            print(f"✅ AES key is valid and functional")
            
        except Exception as e:
            self.fail(f"AES key validation failed: {str(e)}")
    
    def test_settings_file_exists(self):
        """Test that settings.json file exists."""
        settings_path = Path(__file__).parent.parent / "settings.json"
        self.assertTrue(settings_path.exists(), "settings.json file should exist")
    
    def test_job_profile_exists(self):
        """Test that job_profile.yml file exists."""
        job_profile_path = Path(__file__).parent.parent / "job_profile.yml"
        self.assertTrue(job_profile_path.exists(), "job_profile.yml file should exist")


if __name__ == '__main__':
    unittest.main(verbosity=2) 