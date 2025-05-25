"""Configuration management for CVLens-Agent."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import base64

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_DIR = DATA_DIR / "db"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for dir_path in [DATA_DIR, CACHE_DIR, DB_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class Config:
    """Application configuration manager."""
    
    def __init__(self):
        self.settings_path = BASE_DIR / "settings.json"
        self.job_profile_path = BASE_DIR / "job_profile.yml"
        self._settings = self._load_settings()
        self._setup_logging()
        self._validate_env_vars()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file."""
        if not self.settings_path.exists():
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")
        
        with open(self.settings_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self):
        """Configure logging based on settings."""
        log_config = self._settings.get('logging', {})
        log_level = os.getenv('LOG_LEVEL', log_config.get('level', 'INFO'))
        log_file = BASE_DIR / log_config.get('file', 'logs/cvlens.log')
        
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
    def _validate_env_vars(self):
        """Validate required environment variables."""
        required_vars = ['CLIENT_ID', 'TENANT_ID', 'AES_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    @property
    def client_id(self) -> str:
        """Get Microsoft Graph client ID."""
        return os.getenv('CLIENT_ID', '')
    
    @property
    def tenant_id(self) -> str:
        """Get Microsoft Graph tenant ID."""
        return os.getenv('TENANT_ID', '')
    
    @property
    def aes_key(self) -> bytes:
        """Get AES encryption key."""
        key_str = os.getenv('AES_KEY', '')
        try:
            # Decode base64 key
            return base64.b64decode(key_str)
        except Exception:
            # Generate a new key if invalid
            return Fernet.generate_key()
    
    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return os.getenv('DEBUG', 'False').lower() == 'true'
    
    @property
    def tesseract_cmd(self) -> Optional[str]:
        """Get Tesseract OCR command path."""
        return os.getenv('TESSERACT_CMD')
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
                
        return value if value is not None else default
    
    def update_setting(self, key: str, value: Any):
        """Update a setting value."""
        keys = key.split('.')
        settings = self._settings
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        # Set the value
        settings[keys[-1]] = value
        
        # Save to file
        self.save_settings()
    
    def save_settings(self):
        """Save current settings to file."""
        with open(self.settings_path, 'w') as f:
            json.dump(self._settings, f, indent=2)
    
    @property
    def graph_scopes(self) -> list:
        """Get Microsoft Graph API scopes."""
        return ['Mail.Read', 'offline_access']


# Global config instance
config = Config() 