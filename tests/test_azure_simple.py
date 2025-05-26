#!/usr/bin/env python3
"""Simple Azure AD connection test without Unicode characters."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path, override=True)
    print("[OK] Loaded .env file")

# Print current values
print("\nCurrent Configuration:")
print(f"CLIENT_ID: {os.getenv('CLIENT_ID')}")
print(f"TENANT_ID: {os.getenv('TENANT_ID')}")
print(f"AES_KEY: {os.getenv('AES_KEY')[:20]}..." if os.getenv('AES_KEY') else "AES_KEY: Not set")

# Test O365 authentication
print("\nTesting Azure AD Authentication...")
print("-" * 50)

try:
    from O365 import Account, FileSystemTokenBackend
    
    client_id = os.getenv('CLIENT_ID')
    tenant_id = os.getenv('TENANT_ID')
    
    if not client_id or not tenant_id:
        print("[ERROR] CLIENT_ID or TENANT_ID not set!")
        sys.exit(1)
    
    # Create token backend
    token_path = Path("data/.token")
    token_path.mkdir(parents=True, exist_ok=True)
    
    token_backend = FileSystemTokenBackend(
        token_path=token_path,
        token_filename="o365_token.txt"
    )
    
    # Create account
    print(f"\nCreating O365 Account...")
    print(f"   Client ID: {client_id}")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   Auth Type: public (device code flow)")
    
    account = Account(
        credentials=client_id,
        tenant_id=tenant_id,
        token_backend=token_backend,
        scopes=['Mail.Read', 'offline_access'],
        auth_flow_type='public'
    )
    
    print("[OK] Account created successfully!")
    
    # Check if already authenticated
    if account.is_authenticated:
        print("\n[OK] Already authenticated with valid token!")
        
        # Try to get user info
        print("\nGetting user information...")
        user = account.get_current_user()
        if user:
            print(f"   Name: {user.display_name}")
            print(f"   Email: {user.mail}")
            print(f"   ID: {user.object_id}")
        
        # Try to access mailbox
        print("\nTesting mailbox access...")
        mailbox = account.mailbox()
        
        # Get folders
        print("   Getting mail folders...")
        folders = list(mailbox.get_folders())
        print(f"   [OK] Found {len(folders)} folders")
        
        # Show first 5 folders
        for i, folder in enumerate(folders[:5]):
            print(f"      - {folder.name}")
        
        if len(folders) > 5:
            print(f"      ... and {len(folders) - 5} more folders")
            
    else:
        print("\n[INFO] Not authenticated. Starting device code flow...")
        print("\n" + "="*60)
        print("IMPORTANT: Device Code Authentication")
        print("="*60)
        print("\nYou should see a device code below.")
        print("If you don't see it, the URL might be too long.")
        print("\nAlternative: Go directly to:")
        print("   https://microsoft.com/devicelogin")
        print("\nThen enter the code manually.")
        print("="*60 + "\n")
        
        # Start authentication
        result = account.authenticate()
        
        if result:
            print("\n[OK] Authentication successful!")
            
            # Get user info
            user = account.get_current_user()
            if user:
                print(f"\nLogged in as: {user.display_name}")
                print(f"   Email: {user.mail}")
        else:
            print("\n[ERROR] Authentication failed!")
            
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test completed!") 