#!/usr/bin/env python3
"""
Script to list all available CyberEdu MCP tools and their descriptions.
"""

import sys
from pathlib import Path

# Add the src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Also add cyberedu-client
client_path = Path(__file__).parent.parent / "cyberedu-client" / "src"
sys.path.insert(0, str(client_path))

from cyberedu_mcp.server import CUSTOM_TOOLS, registry


def main():
    print("=" * 80)
    print("CyberEdu MCP Tools")
    print("=" * 80)
    
    # Session Management Tools
    print("\n## Session Management Tools\n")
    for name, info in CUSTOM_TOOLS.items():
        print(f"  cyberedu_{name}")
        print(f"    Description: {info['description']}")
        params = info['parameters'].get('properties', {})
        required = info['parameters'].get('required', [])
        if params:
            print(f"    Parameters:")
            for param_name, param_info in params.items():
                req = " (required)" if param_name in required else " (optional)"
                print(f"      - {param_name}: {param_info.get('type', 'any')}{req}")
                if 'description' in param_info:
                    print(f"        {param_info['description']}")
        print()
    
    # Discovered Tools from CyberEduClient
    print("\n## CyberEdu Client Tools\n")
    
    # Group by category
    categories = {}
    for metadata in registry.list_methods():
        cat = metadata.category or "general"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(metadata)
    
    for category, methods in sorted(categories.items()):
        print(f"### {category.title()}\n")
        for metadata in sorted(methods, key=lambda m: m.name):
            print(f"  cyberedu_{metadata.name}")
            print(f"    Description: {metadata.description}")
            params = metadata.parameters.get('properties', {})
            required = metadata.parameters.get('required', [])
            if params:
                print(f"    Parameters:")
                for param_name, param_info in params.items():
                    req = " (required)" if param_name in required else " (optional)"
                    print(f"      - {param_name}: {param_info.get('type', 'any')}{req}")
            print()
    
    # Summary
    total_custom = len(CUSTOM_TOOLS)
    total_client = len(registry.list_methods())
    print("=" * 80)
    print(f"Total: {total_custom + total_client} tools ({total_custom} session management + {total_client} client methods)")
    print("=" * 80)


if __name__ == "__main__":
    main()
