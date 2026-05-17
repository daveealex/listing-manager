#!/usr/bin/env python3
"""
Main Entry Point - Marine Proof Edition
Tracey can just double-click this file!
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*60)
print("  📦 Listings Manager - Marine Proof Edition")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60 + "\n")

# Import and run marine-proof dashboard
from dashboard.marine_proof_ui import app, logger
import uvicorn

def main():
    """Launch the marine-proof web dashboard"""
    
    print("🚀 Starting Marine-Proof Dashboard...")
    print("\nThis is a simplified interface for non-technical users.")
    print("All settings are accessible in the browser!\n")
    
    # Create necessary directories
    for folder in ["./inventory/uploaded", "./logs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
