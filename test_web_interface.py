#!/usr/bin/env python3
"""
Test script for the web interface.
"""

import requests
import time
import json
from pathlib import Path


def test_web_interface():
    """Test the web interface endpoints."""
    print("🔧 Testing Web Interface")
    print("=" * 50)

    base_url = "http://localhost:8080"

    try:
        # Test main page
        print("📱 Testing main page...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Main page accessible")
        else:
            print(f"❌ Main page error: {response.status_code}")
            return False

        # Test configuration API
        print("⚙️  Testing configuration API...")
        response = requests.get(f"{base_url}/api/config")
        if response.status_code == 200:
            config = response.json()
            print("✅ Configuration API working")
            print(f"   - Base URL: {config.get('scraping', {}).get('base_url', 'N/A')}")
            print(f"   - Caching: {config.get('caching', {}).get('enabled', 'N/A')}")
        else:
            print(f"❌ Configuration API error: {response.status_code}")
            return False

        # Test tasks API
        print("📋 Testing tasks API...")
        response = requests.get(f"{base_url}/api/tasks")
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Tasks API working (found {len(tasks)} tasks)")
        else:
            print(f"❌ Tasks API error: {response.status_code}")
            return False

        print("\n🎉 Web interface is working correctly!")
        print("📱 Access at: http://localhost:5000")
        return True

    except requests.exceptions.ConnectionError:
        print("❌ Web server not running. Start with: python3 web_app.py")
        return False
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        return False


if __name__ == "__main__":
    test_web_interface()
