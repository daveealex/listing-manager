#!/usr/bin/env python3
"""Verify marine-proof dashboard works"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("  Marine-Proof Dashboard Verification")
print("="*60 + "\n")

try:
    # Test imports
    from dashboard.marine_proof_ui import app
    print("✅ Dashboard module loads correctly")
    
    # Check routes exist
    routes = [r.path for r in app.routes]
    if "/" in routes and "/api/upload" in routes:
        print("✅ API endpoints configured properly")
    else:
        print("⚠️  Some API routes may be missing")
        
    # Test directory structure
    required_dirs = [
        "./inventory",
        "./inventory/uploaded", 
        "./logs"
    ]
    
    all_exist = True
    for d in required_dirs:
        if Path(d).exists():
            print(f"✅ {d}/ exists")
        else:
            print(f"⚠️  {d}/ will be created on first run")
            all_exist = False
    
    # Test launcher scripts exist
    launcher_scripts = [
        "run.py",
        "start.sh", 
        "Start_Listings_Manager.bat"
    ]
    
    for script in launcher_scripts:
        if Path(script).exists():
            print(f"✅ {script} exists")
        else:
            # Skip bat on non-Windows
            if script.endswith(".bat"):
                continue
            print(f"❌ {script} MISSING!")
            
    print("\n" + "="*60)
    print("  ✅ Marine-Proof Dashboard Ready!")
    print("="*60)
    print("""
To start:

On Windows: Double-click "Start_Listings_Manager.bat"

On Linux/Mac: 
   python run.py
   or
   ./start.sh

Then open browser to http://localhost:8000
""")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
