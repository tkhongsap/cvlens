"""Unit tests for configuration module."""

import unittest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = Path(self.temp_dir) / "settings.json"
        self.job_profile_file = Path(self.temp_dir) / "job_profile.yml"
        
        # Create test settings
        test_settings = {
            "folder_id": "test_folder",
            "max_attachment_size_mb": 25,
            "logging": {
                "level": "INFO",
                "file": "test.log"
            }
        }
        
        with open(self.settings_file, 'w') as f:
            json.dump(test_settings, f)
        
        # Set environment variables
        os.environ['CLIENT_ID'] = 'test_client_id'
        os.environ['TENANT_ID'] = 'test_tenant_id'
        os.environ['AES_KEY'] = 'dGVzdF9hZXNfa2V5X2Jhc2U2NF9lbmNvZGVk'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
        
        # Clean environment variables
        for key in ['CLIENT_ID', 'TENANT_ID', 'AES_KEY']:
            if key in os.environ:
                del os.environ[key]
    
    @patch('src.config.BASE_DIR')
    def test_config_initialization(self, mock_base_dir):
        """Test Config initialization."""
        mock_base_dir.return_value = Path(self.temp_dir)
        
        from src.config import Config
        
        with patch.object(Config, 'settings_path', self.settings_file):
            with patch.object(Config, 'job_profile_path', self.job_profile_file):
                config = Config()
                
                self.assertEqual(config.client_id, 'test_client_id')
                self.assertEqual(config.tenant_id, 'test_tenant_id')
                self.assertIsNotNone(config.aes_key)
    
    def test_get_setting(self):
        """Test getting settings."""
        from src.config import Config
        
        with patch.object(Config, 'settings_path', self.settings_file):
            with patch.object(Config, 'job_profile_path', self.job_profile_file):
                config = Config()
                
                # Test simple setting
                self.assertEqual(config.get_setting('folder_id'), 'test_folder')
                
                # Test nested setting
                self.assertEqual(config.get_setting('logging.level'), 'INFO')
                
                # Test default value
                self.assertEqual(config.get_setting('non_existent', 'default'), 'default')
    
    def test_update_setting(self):
        """Test updating settings."""
        from src.config import Config
        
        with patch.object(Config, 'settings_path', self.settings_file):
            with patch.object(Config, 'job_profile_path', self.job_profile_file):
                config = Config()
                
                # Update setting
                config.update_setting('folder_id', 'new_folder')
                self.assertEqual(config.get_setting('folder_id'), 'new_folder')
                
                # Verify saved to file
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.assertEqual(saved_settings['folder_id'], 'new_folder')
    
    def test_missing_env_vars(self):
        """Test behavior with missing environment variables."""
        del os.environ['CLIENT_ID']
        
        from src.config import Config
        
        with patch.object(Config, 'settings_path', self.settings_file):
            with patch.object(Config, 'job_profile_path', self.job_profile_file):
                with self.assertRaises(ValueError) as context:
                    config = Config()
                
                self.assertIn('CLIENT_ID', str(context.exception))


if __name__ == '__main__':
    unittest.main() 