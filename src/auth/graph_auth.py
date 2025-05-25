"""Microsoft Graph authentication using device code flow."""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from O365 import Account, FileSystemTokenBackend
from O365.connection import Connection, MSGraphProtocol
from src.config import config, BASE_DIR

logger = logging.getLogger(__name__)


class GraphAuthenticator:
    """Handle Microsoft Graph authentication using device code flow."""
    
    def __init__(self):
        self.client_id = config.client_id
        self.tenant_id = config.tenant_id
        self.scopes = config.graph_scopes
        self.token_path = BASE_DIR / "data" / ".token"
        self.token_filename = "o365_token.txt"
        self._account: Optional[Account] = None
        
    def _get_account(self) -> Account:
        """Get or create O365 Account instance."""
        if self._account is None:
            # Create token backend
            token_backend = FileSystemTokenBackend(
                token_path=self.token_path,
                token_filename=self.token_filename
            )
            
            # Create account with tenant
            self._account = Account(
                credentials=(self.client_id, None),  # No client secret for device flow
                tenant_id=self.tenant_id,
                token_backend=token_backend,
                scopes=self.scopes,
                auth_flow_type='device'
            )
            
        return self._account
    
    def authenticate(self) -> bool:
        """
        Authenticate using device code flow.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            account = self._get_account()
            
            if account.is_authenticated:
                logger.info("Already authenticated with valid token")
                return True
            
            # Start device code flow
            logger.info("Starting device code authentication flow")
            
            # This will print the device code URL and code
            result = account.authenticate()
            
            if result:
                logger.info("Authentication successful")
                return True
            else:
                logger.error("Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        try:
            account = self._get_account()
            return account.is_authenticated
        except Exception:
            return False
    
    def get_mailbox(self):
        """Get mailbox object for email operations."""
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated. Please authenticate first.")
        
        account = self._get_account()
        return account.mailbox()
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information."""
        try:
            if not self.is_authenticated():
                return None
                
            account = self._get_account()
            # Get user details from the account
            user = account.get_current_user()
            
            if user:
                return {
                    'display_name': user.display_name,
                    'mail': user.mail,
                    'id': user.object_id
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
    def logout(self):
        """Clear authentication tokens."""
        try:
            # Remove token file
            token_file = self.token_path / self.token_filename
            if token_file.exists():
                token_file.unlink()
                logger.info("Authentication tokens cleared")
            
            # Clear account instance
            self._account = None
            
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
    
    def get_device_code_info(self) -> Optional[Dict[str, str]]:
        """
        Get device code information for manual display.
        
        Returns:
            Dict with 'user_code' and 'verification_url' or None
        """
        try:
            account = self._get_account()
            
            # Get connection to trigger device code flow
            con = account.connection
            
            # This is a workaround to get device code info
            # The O365 library doesn't expose this directly
            # In production, you might need to extend the library
            
            return {
                'user_code': 'Check console output',
                'verification_url': 'https://microsoft.com/devicelogin'
            }
            
        except Exception as e:
            logger.error(f"Error getting device code: {str(e)}")
            return None


# Global authenticator instance
graph_auth = GraphAuthenticator() 