#!/usr/bin/env python3
"""Quick setup and verification script for Listing Manager"""

import os
from pathlib import Path

print("="*60)
print("  📦 Listing Manager - Setup Verification")
print("="*60 + "\n")

# Check directory structure
required_dirs = [
    "listing-manager/config",
    "listing-manager/core", 
    "listing-manager/platforms",
    "listing-manager/dashboard",
    "listing-manager/scanner",
    "listing-manager/data",
    "listing-manager/logs",
    "listing-manager/inventory/input",
    "listing-manager/inventory/processed",
    "listing-manager/inventory/failed",
]

print("1. Checking directory structure...")
all_good = True
for d in required_dirs:
    if Path(d).exists():
        print(f"   {d} - OK")
    else:
        print(f"   MISSING: {d}")
        all_good = False

if all_good:
    print("\n✅ All directories created successfully!\n")
else:
    print("\n⚠️  Some directories missing. Run setup again.\n")

# Check config file
print("2. Checking configuration...")
config_path = Path("listing-manager/config/settings.yaml")
if config_path.exists():
    print(f"   settings.yaml - OK")
else:
    print(f"   MISSING: settings.yaml")

# Summary
print("\n" + "="*60)
print("  Next Steps:")
print("="*60)
print("""
1. Install dependencies:
   cd listing-manager
   pip install -r requirements.txt

2. Start LM Server (open LM Studio UI first):
   python main.py dashboard

3. Open browser to http://localhost:8000

4. Drop product photos in inventory/input/ folder
""")
print("="*60 + "\n")
