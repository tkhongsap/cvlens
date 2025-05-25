#!/usr/bin/env python3
"""Generate AES encryption key for CVLens-Agent."""

import base64
from cryptography.fernet import Fernet


def generate_aes_key():
    """Generate a new AES encryption key."""
    # Generate key
    key = Fernet.generate_key()
    
    # Encode to base64 for .env file
    key_b64 = base64.b64encode(key).decode('utf-8')
    
    print("=" * 60)
    print("CVLens-Agent AES Key Generator")
    print("=" * 60)
    print()
    print("Generated AES Key (base64 encoded):")
    print(key_b64)
    print()
    print("Add this to your .env file:")
    print(f"AES_KEY={key_b64}")
    print()
    print("⚠️  IMPORTANT: Keep this key secure!")
    print("    - Do not commit it to version control")
    print("    - Back it up in a secure location")
    print("    - Losing this key means losing access to encrypted data")
    print("=" * 60)


if __name__ == "__main__":
    generate_aes_key() 