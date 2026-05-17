#!/usr/bin/env python3
"""Debug what's actually being passed to create_parser"""

import yaml

with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)

print("Full config['ai_parser']:")
for key, value in config['ai_parser'].items():
    print(f"  {key}: {value}")

print("\nCalling create_parser(config['ai_parser'])...")
from core.ai_parser import create_parser

# Add debug to the function
import core.ai_parser as ap

original_create = ap.create_parser

def debug_create(parser_config):
    print(f"\nDEBUG inside create_parser:")
    print(f"  parser_config type: {type(parser_config)}")
    if 'lmstudio_url' in parser_config:
        print(f"  lmstudio_url value: {parser_config['lmstudio_url']}")
    else:
        print("  ERROR: 'lmstudio_url' key not found!")
    return original_create(parser_config)

ap.create_parser = debug_create

parser = create_parser(config['ai_parser'])
print(f"\nParser created with base_url: {parser.lmstudio_client.base_url}")
