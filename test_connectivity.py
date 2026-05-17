#!/usr/bin/env python3
"""Quick connectivity test for Listing Manager"""

import requests
from pathlib import Path

def test_lm_studio():
    """Test connection to LM Studio server on AMD machine"""
    print("🔌 Testing connection to LM Studio (AMD: 192.168.1.137)")
    
    try:
        response = requests.get("http://192.168.1.137:1234/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()["data"]
            print(f"✅ Connected! Server has {len(models)} models loaded")
            
            # Check for our model
            model_names = [m["id"] for m in models]
            target_model = "llama3-llava-next-8b-gguf"
            
            if any(target_model in name for name in model_names):
                print(f"✅ Target model '{target_model}' found!")
            else:
                print(f"⚠️  Model '{target_model}' NOT found. Available:")
                for name in model_names[:5]:
                    print(f"   - {name}")
            
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_dashboard():
    """Test if dashboard can start"""
    print("\n🚀 Testing Dashboard startup...")
    
    try:
        from dashboard.web_app import app
        print("✅ Dashboard module loads successfully!")
        
        # Check FastAPI routes
        routes = [r.path for r in app.routes]
        print(f"   Available routes: {', '.join(routes[:5])}")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Validate configuration"""
    print("\n📋 Validating config...")
    
    try:
        import yaml
        with open("config/settings.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        ai_parser = config.get("ai_parser", {})
        lm_url = ai_parser.get("lmstudio_url", "")
        model = ai_parser.get("models", {}).get("primary", "")
        
        print(f"   LM Studio URL: {lm_url}")
        print(f"   Primary Model: {model}")
        
        if "192.168.1.137" in lm_url:
            print("✅ Config points to AMD machine correctly")
        else:
            print("⚠️  LM Studio URL may need adjustment")
            
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("  Listing Manager - Connectivity Test")
    print("="*60 + "\n")
    
    results = []
    results.append(("LM Studio Server", test_lm_studio()))
    results.append(("Config", test_config()))
    results.append(("Dashboard Module", test_dashboard()))
    
    print("\n" + "="*60)
    print("  Results:")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Ready to run.")
        print("\nNext steps:")
        print("  1. Ensure llama3-llava-next-8b-gguf is loaded in LM Studio on AMD machine")
        print("  2. Run: python main.py dashboard")
        print("  3. Open http://localhost:8000 in browser")
    else:
        print("\n⚠️  Some tests failed. Check output above.")
