#!/usr/bin/env python3
"""Direct test - bypass all imports, use LM Studio at AMD server directly"""

import requests
import json

# Use the EXACT URL from settings.yaml
LMSTUDIO_AMD_URL = "http://192.168.1.137:1234/v1"
TARGET_MODEL = "llama3-llava-next-8b"

print("="*60)
print("  Direct LM Studio Connection Test")
print(f"  Server: {LMSTUDIO_AMD_URL}")
print(f"  Target Model: {TARGET_MODEL}")
print("="*60 + "\n")

try:
    # Get list of models from AMD server
    response = requests.get(f"{LMSTUDIO_AMD_URL}/models", timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        models_list = [m["id"] for m in data.get("data", [])]
        
        print(f"✅ Successfully connected to AMD server")
        print(f"\nAvailable models on AMD server ({len(models_list)}):")
        for model in models_list:
            marker = " ← TARGET MODEL!" if model == TARGET_MODEL else ""
            print(f"   • {model}{marker}")
        
        # Check if target exists
        if TARGET_MODEL in models_list:
            print(f"\n✅ SUCCESS! Target model '{TARGET_MODEL}' is available on AMD server")
            
            # Try to use it for a simple completion test (without image)
            print(f"\n🧪 Testing model inference...")
            
            infer_payload = {
                "model": TARGET_MODEL,
                "messages": [
                    {"role": "system", "content": "You are helpful assistant."},
                    {"role": "user", "content": "What is 2+2? Respond with just the number."}
                ],
                "temperature": 0.3,
                "max_tokens": 10
            }
            
            resp = requests.post(
                f"{LMSTUDIO_AMD_URL}/chat/completions",
                json=infer_payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                result = resp.json()
                answer = result["choices"][0]["message"]["content"]
                print(f"✅ Model responds! Test query 'What is 2+2?' → '{answer}'")
            else:
                print(f"⚠️  Inference endpoint returned {resp.status_code}")
        else:
            print(f"\n❌ Target model NOT found on AMD server")
            
    else:
        print(f"❌ Failed to connect - status code: {response.status_code}")
        
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection refused! Check if LM Studio is running on 192.168.1.137")
    print(f"   Error: {e}")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "="*60)
print("Next steps:")
print("="*60)
print("""
If model is available on AMD server:
  ✅ Config in settings.yaml is correct (uses 192.168.1.137)
  ✅ Parser will use this server when running main.py

If you want to test locally instead:
  ⚠️  Change lmstudio_url to "http://localhost:1234/v1" in settings.yaml
  ⚠️  But note your local models don't include llama3-llava-next-8b
""")
