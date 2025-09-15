#!/usr/bin/env python3
"""
Test script to verify all imports work and URL extraction is functional.
"""


def test_imports():
    """Test all required imports."""
    print("🔍 Testing Imports...")

    try:
        import playwright.async_api

        print("✅ playwright.async_api imported successfully")
    except ImportError as e:
        print(f"❌ playwright.async_api import failed: {e}")
        return False

    try:
        import pandas

        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False

    try:
        import numpy

        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ numpy import failed: {e}")
        return False

    try:
        from adapters.torob_search import TorobScraper

        print("✅ TorobScraper imported successfully")
    except ImportError as e:
        print(f"❌ TorobScraper import failed: {e}")
        return False

    try:
        from core.exporter_excel import ExcelExporter

        print("✅ ExcelExporter imported successfully")
    except ImportError as e:
        print(f"❌ ExcelExporter import failed: {e}")
        return False

    print("\n🎉 All imports successful!")
    return True


def test_url_extraction():
    """Test URL extraction functionality."""
    print("\n🔍 Testing URL Extraction...")

    try:
        import asyncio
        from adapters.torob_search import TorobScraper

        async def test_scraper():
            async with TorobScraper(headless=True) as scraper:
                # Test search
                results = await scraper.search_parts(
                    "چراغ سمت راست تیگو ۸ پرو", max_scroll_attempts=1
                )

                print(f"📊 Found {len(results)} products")

                if results:
                    print("\n📋 Sample results:")
                    for i, result in enumerate(results[:3]):  # Show first 3
                        print(
                            f"   {i+1}. Title: {result.get('title_raw', 'N/A')[:50]}..."
                        )
                        print(f"      URL: {result.get('product_url', 'N/A')}")
                        print(f"      Price: {result.get('price_raw', 'N/A')}")
                        print(f"      Seller: {result.get('seller_name', 'N/A')}")
                        print()

                return len(results) > 0

        result = asyncio.run(test_scraper())
        if result:
            print("✅ URL extraction working!")
        else:
            print("❌ No products found")
        return result

    except Exception as e:
        print(f"❌ URL extraction test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing Torob Scraper Environment")
    print("=" * 50)

    # Test imports
    imports_ok = test_imports()

    if imports_ok:
        # Test URL extraction
        url_ok = test_url_extraction()

        if url_ok:
            print("\n🎉 All tests passed! The scraper is ready to use.")
        else:
            print("\n⚠️  Imports work but URL extraction needs attention.")
    else:
        print("\n❌ Import issues need to be resolved first.")
