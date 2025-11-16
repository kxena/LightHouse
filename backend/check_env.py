#!/usr/bin/env python3
"""
Environment Variable Diagnostic Tool
=====================================
Checks if your .env file is properly configured for MongoDB connection.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def check_env():
    print("=" * 70)
    print("LightHouse Environment Diagnostic")
    print("=" * 70)
    print()
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ ERROR: .env file not found!")
        print()
        print("Expected location:", env_file.absolute())
        print()
        print("Solution:")
        print("1. Create a .env file in the same directory as this script")
        print("2. Add your MongoDB URI: MDB_URI=mongodb+srv://...")
        print("3. See .env.template for an example")
        print()
        return False
    
    print(f"✓ Found .env file at: {env_file.absolute()}")
    print()
    
    # Load environment variables
    load_dotenv()
    
    # Check MDB_URI
    print("Checking environment variables:")
    print("-" * 70)
    
    mdb_uri = os.getenv('MDB_URI')
    
    if not mdb_uri:
        print("❌ MDB_URI: NOT SET")
        print()
        print("Your .env file should contain:")
        print("MDB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0")
        print()
        print("Common mistakes:")
        print("  ✗ MDB_URI = mongodb+srv://...  (space before =)")
        print("  ✗ MDB_URI= mongodb+srv://...   (space after =)")
        print('  ✗ MDB_URI="mongodb+srv://..."  (has quotes)')
        print("  ✗ MONGODB_URI=...              (wrong variable name)")
        print()
        print("Correct format:")
        print("  ✓ MDB_URI=mongodb+srv://...")
        print()
        return False
    
    print(f"✓ MDB_URI: SET ({len(mdb_uri)} characters)")
    
    # Check if it looks like a valid MongoDB URI
    if not mdb_uri.startswith('mongodb'):
        print("⚠️  WARNING: MDB_URI doesn't start with 'mongodb' - may be invalid")
        print(f"   First 20 chars: {mdb_uri[:20]}")
        print()
    
    # Check for common issues
    issues = []
    
    if mdb_uri.startswith(' ') or mdb_uri.endswith(' '):
        issues.append("URI has leading or trailing spaces")
    
    if mdb_uri.startswith('"') or mdb_uri.startswith("'"):
        issues.append("URI is wrapped in quotes (should not be)")
    
    if ',,' in mdb_uri:
        issues.append("URI contains double commas")
    
    if '@,' in mdb_uri or ',@' in mdb_uri:
        issues.append("URI has comma near @ symbol")
    
    if issues:
        print()
        print("⚠️  Potential issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("Your URI (first 50 chars):", repr(mdb_uri[:50]))
        print()
    else:
        print("✓ URI format looks good")
        print()
    
    # Check other variables
    print("Other environment variables:")
    print("-" * 70)
    
    other_vars = {
        'BLUESKY_USER': os.getenv('BLUESKY_USER'),
        'BLUESKY_PWD': os.getenv('BLUESKY_PWD'),
        'HF_TOKEN': os.getenv('HF_TOKEN')
    }
    
    for var_name, var_value in other_vars.items():
        if var_value:
            # Don't print passwords/tokens, just confirm they exist
            print(f"✓ {var_name}: SET ({len(var_value)} characters)")
        else:
            print(f"⚠️  {var_name}: NOT SET")
    
    print()
    
    # Try to connect
    print("=" * 70)
    print("Testing MongoDB Connection")
    print("=" * 70)
    print()
    
    try:
        from mongodb_handler import MongoDBHandler
        
        handler = MongoDBHandler()
        if handler.connect():
            print("✅ SUCCESS! MongoDB connection works!")
            print()
            
            # Get stats
            try:
                stats = handler.get_statistics()
                print(f"Database statistics:")
                print(f"  Total incidents: {stats['total_incidents']}")
                print(f"  Active incidents: {stats['active_incidents']}")
            except Exception as e:
                print(f"(Could not fetch stats: {e})")
            
            handler.close()
            print()
            print("Your setup is ready! You can now run:")
            print("  python regenerate_incidents_mongodb.py")
            print()
            return True
        else:
            print("❌ MongoDB connection failed")
            print()
            print("Check the error message above for details.")
            print()
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import mongodb_handler: {e}")
        print()
        print("Make sure you've installed dependencies:")
        print("  pip install pymongo python-dotenv")
        print()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        return False


if __name__ == "__main__":
    success = check_env()
    
    if not success:
        print("=" * 70)
        print("Next Steps:")
        print("=" * 70)
        print()
        print("1. Fix the issues identified above")
        print("2. Run this diagnostic again: python check_env.py")
        print("3. Once it passes, run: python regenerate_incidents_mongodb.py")
        print()