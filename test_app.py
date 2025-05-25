#!/usr/bin/env python3
"""Test script to verify CVLens-Agent components."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing CVLens-Agent imports...")
    print("-" * 40)
    
    modules_to_test = [
        ("Configuration", "src.config"),
        ("Authentication", "src.auth.graph_auth"),
        ("Database", "src.models.database"),
        ("Email Ingestion", "src.services.ingest"),
        ("Resume Parser", "src.services.parse"),
        ("Candidate Scorer", "src.services.score"),
    ]
    
    failed = []
    
    for name, module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: FAILED - {str(e)}")
            failed.append((name, str(e)))
        except Exception as e:
            print(f"⚠️  {name}: ERROR - {str(e)}")
            failed.append((name, str(e)))
    
    print("-" * 40)
    
    if failed:
        print(f"\n❌ {len(failed)} modules failed to import:")
        for name, error in failed:
            print(f"   - {name}: {error}")
        print("\nPlease check:")
        print("1. All dependencies are installed (run: pip install -r requirements.txt)")
        print("2. Environment variables are set (.env file exists)")
        print("3. Required files exist (settings.json, job_profile.yml)")
    else:
        print("\n✅ All modules imported successfully!")
        print("\nYou can now run the application with:")
        print("   Windows: run_local.bat")
        print("   Linux/Mac: ./run_local.sh")
    
    return len(failed) == 0


if __name__ == "__main__":
    # Check for required files
    required_files = [
        ("settings.json", "Configuration file"),
        ("job_profile.yml", "Job profile configuration"),
        ("env.example", "Environment template"),
    ]
    
    print("Checking required files...")
    print("-" * 40)
    
    missing_files = []
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"✅ {filename}: Found")
        else:
            print(f"❌ {filename}: Missing ({description})")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n⚠️  Please ensure all required files exist before running the application.")
        sys.exit(1)
    
    print()
    
    # Test imports
    success = test_imports()
    sys.exit(0 if success else 1) 