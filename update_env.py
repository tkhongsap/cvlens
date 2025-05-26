#!/usr/bin/env python3
"""Helper script to update .env file with correct Azure AD values."""

import os
from pathlib import Path

def update_env_file():
    """Update .env file with correct Azure AD configuration."""
    
    # Values from Azure portal
    client_id = "9a1e2246-8131-4893-a1ef-87280e20cf49"
    tenant_id = "1d8f5d85-9109-4cda-abcf-3fa469cbf8f9"
    aes_key = "anZ3ZGtDSW9TR29uVFpZUDZEdElKdGs1S1VVUEF3MXhYc0JGdFpXeFQ0RT0="
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found!")
        print("Creating .env file from template...")
        
        # Copy from env.example
        example_path = Path("env.example")
        if example_path.exists():
            content = example_path.read_text()
        else:
            # Create basic content
            content = """# Microsoft Graph API Configuration
CLIENT_ID=your_client_id
TENANT_ID=your_tenant_id

# Security
AES_KEY=your_aes_key

# Optional: Tesseract OCR path (if not in system PATH)
# TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe

# Optional: Debug mode
DEBUG=False

# Optional: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
"""
    else:
        content = env_path.read_text()
    
    # Update values
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('CLIENT_ID='):
            updated_lines.append(f'CLIENT_ID={client_id}')
            print(f"✅ Updated CLIENT_ID: {client_id}")
        elif line.startswith('TENANT_ID='):
            updated_lines.append(f'TENANT_ID={tenant_id}')
            print(f"✅ Updated TENANT_ID: {tenant_id}")
        elif line.startswith('AES_KEY='):
            updated_lines.append(f'AES_KEY={aes_key}')
            print(f"✅ Updated AES_KEY: {aes_key[:20]}...")
        else:
            updated_lines.append(line)
    
    # Write back
    env_path.write_text('\n'.join(updated_lines))
    
    print("\n✅ .env file updated successfully!")
    print("\nYour Azure AD configuration:")
    print(f"  Email: totrakool.k@thaibev.com")
    print(f"  Tenant: Thai Beverage Public Company")
    print(f"  App: CVLens - Agent")
    
    print("\n🔐 Next steps:")
    print("1. Run API connectivity test:")
    print("   python tests/run_tests.py --api --interactive")
    print("\n2. When prompted, authenticate with your corporate account:")
    print("   totrakool.k@thaibev.com")


if __name__ == "__main__":
    update_env_file() 