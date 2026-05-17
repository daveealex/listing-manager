#!/usr/bin/env python3
import yaml

with open("config/settings.yaml", 'r') as f:
    raw = f.read()
    
print("="*60)
print("RAW CONFIG FILE CONTENT:")
print("="*60)
print(raw)
print("="*60 + "\n")

# Now parse it
config = yaml.safe_load(raw)
print(f"\nparsed ai_parser['lmstudio_url'] = {config.get('ai_parser', {}).get('lmstudio_url')}")
