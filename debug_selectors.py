#!/usr/bin/env python3
"""
Debug script to check CSS selectors and HTML structure.
"""

import asyncio
from urllib.parse import quote

from adapters.torob_search import TorobScraper


async def debug_selectors():
    """Debug CSS selectors."""
    print("🔍 Debugging CSS Selectors")
    print("=" * 50)

    async with TorobScraper(headless=True) as scraper:  # Set to True for headless
        # Test search
        keywords = "چراغ سمت راست تیگو ۸ پرو automotive part"
        encoded_keywords = quote(keywords.strip())
        search_url = f"{scraper.base_url}/search/?query={encoded_keywords}"

        print(f"🔍 Searching: {search_url}")
        await scraper.page.goto(search_url, wait_until="networkidle")
        await scraper._random_delay()

        # Check for product cards
        product_cards = scraper.page.locator(scraper.selectors["product_cards"])
        card_count = await product_cards.count()
        print(f"📊 Found {card_count} product cards")

        if card_count > 0:
            # Get first card
            first_card = product_cards.first

            # Check title selectors
            print("\n🔍 Testing title selectors:")
            for selector in [
                'a[href*="/p/"] span',
                'a[href*="/p/"]',
                ".ProductCard_desktop_title__3LVVm",
                "h3",
                "h4",
                ".title",
            ]:
                try:
                    element = first_card.locator(selector).first
                    count = await element.count()
                    if count > 0:
                        text = await element.text_content()
                        print(f"   ✅ {selector}: '{text[:50]}...'")
                    else:
                        print(f"   ❌ {selector}: No elements found")
                except Exception as e:
                    print(f"   ❌ {selector}: Error - {e}")

            # Check link selectors
            print("\n🔍 Testing link selectors:")
            for selector in ['a[href*="/p/"]', "a"]:
                try:
                    element = first_card.locator(selector).first
                    count = await element.count()
                    if count > 0:
                        href = await element.get_attribute("href")
                        print(f"   ✅ {selector}: '{href}'")
                    else:
                        print(f"   ❌ {selector}: No elements found")
                except Exception as e:
                    print(f"   ❌ {selector}: Error - {e}")

            # Check seller selectors
            print("\n🔍 Testing seller selectors:")
            for selector in [
                ".ProductCard_desktop_seller__3LVVm",
                ".seller-name",
                ".shop-name",
                ".store-name",
            ]:
                try:
                    element = first_card.locator(selector).first
                    count = await element.count()
                    if count > 0:
                        text = await element.text_content()
                        print(f"   ✅ {selector}: '{text}'")
                    else:
                        print(f"   ❌ {selector}: No elements found")
                except Exception as e:
                    print(f"   ❌ {selector}: Error - {e}")

            # Get page HTML for manual inspection
            print("\n🔍 Getting page HTML for inspection...")
            html = await scraper.page.content()
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("   📄 Saved page HTML to debug_page.html")

        # Keep browser open for manual inspection
        print("\n⏸️  Browser will stay open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(debug_selectors())
