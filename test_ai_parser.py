#!/usr/bin/env python3
"""Test the actual AI product analyzer with LM Studio connection"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.ai_parser import create_parser, ProductParser
import yaml

# Load config
with open("config/settings.yaml", 'r') as f:
    config = yaml.safe_load(f)

print("="*60)
print("  AI Parser Connection Test")
print("="*60 + "\n")

try:
    parser = create_parser(config["ai_parser"])
    
    print(f"✅ Parser initialized successfully!")
    print(f"   Primary model: {parser.models['primary']}")
    print(f"   Fast fallback: {parser.models['fast']}")
    print(f"   LM Studio URL: {parser.lmstudio_client.base_url}")
    
    # Try to get list of available models from server
    import requests
    
    response = requests.get(
        f"{parser.lmstudio_client.base_url}/models",
        timeout=5
    )
    
    if response.status_code == 200:
        models_list = [m["id"] for m in response.json()["data"]]
        
        print(f"\n✅ Connected to LM Studio server")
        print(f"   Available models ({len(models_list)}):")
        for model in models_list[:10]:
            marker = " ← TARGET" if model == parser.models['primary'] else ""
            print(f"   - {model}{marker}")
        
        # Check if target model is available
        if parser.models['primary'] in models_list:
            print(f"\n✅ TARGET MODEL '{parser.models['primary']}' IS AVAILABLE!")
        else:
            # Find similar names
            import difflib
            matches = difflib.get_close_matches(parser.models['primary'], models_list, n=3)
            if matches:
                print(f"\n⚠️  Target model not found exactly, but these are close:")
                for match in matches:
                    print(f"   - {match}")
    else:
        print(f"❌ Could not fetch models list (status {response.status_code})")
        
except Exception as e:
    print(f"❌ Error initializing parser: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("  Next Steps:")
print("="*60 + "\n")

if "llama3-llava-next-8b" in str(config.get("ai_parser", {}).get("models", {})):
    print("✅ Model name is correctly configured as 'llama3-llava-next-8b'")
    print("\nTo test actual analysis:")
    print("  1. Drop a product photo in inventory/input/")
    print("  2. Run: python main.py monitor")
    print("  3. Watch logs for AI processing results\n")
