#!/usr/bin/env python3
"""
Debug script to analyze the JSON structure in Torob's HTML.
"""

import asyncio
import re
import json
from adapters.torob_search import TorobScraper

async def debug_json_structure():
    """Analyze the JSON structure in Torob's HTML."""
    print("🔍 Analyzing JSON Structure in Torob HTML")
    print("=" * 50)
    
    async with TorobScraper(headless=True) as scraper:
        # Test with a simple search
        search_url = "https://torob.com/search/?query=چراغ%20تیگو"
        print(f"🔍 Testing URL: {search_url}")
        
        await scraper.page.goto(search_url, wait_until='networkidle')
        await scraper.page.wait_for_timeout(3000)  # Wait for dynamic content
        
        # Get page content
        content = await scraper.page.content()
        print(f"📄 Page content length: {len(content)} characters")
        
        # Look for different JSON patterns
        patterns = [
            r'__NEXT_DATA__.*?"props":\s*({.*?})',
            r'__NEXT_DATA__.*?({.*?})',
            r'"products":\s*(\[.*?\])',
            r'window\.__NEXT_DATA__\s*=\s*({.*?});',
            r'<script[^>]*>.*?__NEXT_DATA__.*?({.*?})</script>'
        ]
        
        for i, pattern in enumerate(patterns):
            print(f"\n🔍 Testing pattern {i+1}: {pattern[:50]}...")
            try:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    print(f"   ✅ Found JSON data! Length: {len(json_str)} characters")
                    
                    # Try to parse it
                    try:
                        json_data = json.loads(json_str)
                        print(f"   ✅ JSON is valid!")
                        
                        # Save to file for analysis
                        filename = f"debug_json_pattern_{i+1}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        print(f"   💾 Saved to {filename}")
                        
                        # Look for products in the JSON
                        if isinstance(json_data, dict):
                            products = find_products_in_json(json_data)
                            if products:
                                print(f"   🎯 Found {len(products)} products in JSON!")
                                print(f"   📋 Sample product keys: {list(products[0].keys()) if products else 'None'}")
                            else:
                                print(f"   ⚠️  No products found in JSON structure")
                        
                        break  # Use the first working pattern
                        
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON decode error: {e}")
                        print(f"   📄 First 200 chars: {json_str[:200]}")
                        
                else:
                    print(f"   ❌ No match found")
                    
            except Exception as e:
                print(f"   ❌ Pattern error: {e}")
        
        # Also look for any script tags with data
        print(f"\n🔍 Looking for script tags with data...")
        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        print(f"   Found {len(script_tags)} script tags")
        
        for i, script in enumerate(script_tags[:5]):  # Check first 5
            if 'products' in script or 'torob' in script.lower():
                print(f"   📜 Script {i+1} contains relevant data (length: {len(script)})")
                if len(script) < 1000:  # Only show short scripts
                    print(f"      Content: {script[:200]}...")

def find_products_in_json(data, path=""):
    """Recursively find products array in JSON data."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'products' and isinstance(value, list):
                return value
            elif isinstance(value, (dict, list)):
                result = find_products_in_json(value, f"{path}.{key}")
                if result:
                    return result
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                result = find_products_in_json(item, f"{path}[{i}]")
                if result:
                    return result
    return None

if __name__ == "__main__":
    asyncio.run(debug_json_structure())
