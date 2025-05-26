#!/usr/bin/env python3
"""Direct Azure AD connection test."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path, override=True)  # Force reload
    print("✅ Loaded .env file")

# Print current values
print("\n📋 Current Configuration:")
print(f"CLIENT_ID: {os.getenv('CLIENT_ID')}")
print(f"TENANT_ID: {os.getenv('TENANT_ID')}")
print(f"AES_KEY: {os.getenv('AES_KEY')[:20]}..." if os.getenv('AES_KEY') else "AES_KEY: Not set")

# Test O365 authentication
print("\n🔐 Testing Azure AD Authentication...")
print("-" * 50)

try:
    from O365 import Account, FileSystemTokenBackend
    
    client_id = os.getenv('CLIENT_ID')
    tenant_id = os.getenv('TENANT_ID')
    
    if not client_id or not tenant_id:
        print("❌ CLIENT_ID or TENANT_ID not set!")
        sys.exit(1)
    
    # Create token backend
    token_path = Path("data/.token")
    token_path.mkdir(parents=True, exist_ok=True)
    
    token_backend = FileSystemTokenBackend(
        token_path=token_path,
        token_filename="o365_token.txt"
    )
    
    # Create account
    print(f"\n🔧 Creating O365 Account...")
    print(f"   Client ID: {client_id}")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   Auth Type: public (device code flow)")
    
    account = Account(
        credentials=client_id,  # Just client_id for public flow
        tenant_id=tenant_id,
        token_backend=token_backend,
        scopes=['Mail.Read', 'offline_access'],
        auth_flow_type='public'
    )
    
    print("✅ Account created successfully!")
    
    # Check if already authenticated
    if account.is_authenticated:
        print("\n✅ Already authenticated with valid token!")
        
        # Try to get user info
        print("\n👤 Getting user information...")
        user = account.get_current_user()
        if user:
            print(f"   Name: {user.display_name}")
            print(f"   Email: {user.mail}")
            print(f"   ID: {user.object_id}")
        
        # Try to access mailbox
        print("\n📧 Testing mailbox access...")
        mailbox = account.mailbox()
        
        # Get folders
        print("   Getting mail folders...")
        folders = list(mailbox.get_folders())
        print(f"   ✅ Found {len(folders)} folders")
        
        # Show first 5 folders
        for i, folder in enumerate(folders[:5]):
            print(f"      📁 {folder.name}")
        
        if len(folders) > 5:
            print(f"      ... and {len(folders) - 5} more folders")
            
    else:
        print("\n🔐 Not authenticated. Starting device code flow...")
        print("\nInstructions:")
        print("1. Visit: https://microsoft.com/devicelogin")
        print("2. Enter the code shown below")
        print("3. Sign in with: totrakool.k@thaibev.com")
        print("4. Return here and wait for completion\n")
        
        # Start authentication
        result = account.authenticate()
        
        if result:
            print("\n✅ Authentication successful!")
            
            # Get user info
            user = account.get_current_user()
            if user:
                print(f"\n👤 Logged in as: {user.display_name}")
                print(f"   Email: {user.mail}")
        else:
            print("\n❌ Authentication failed!")
            
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test completed!") 