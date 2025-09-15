"""
Torob marketplace adapter using Playwright for scraping automotive parts.
Handles search queries, pagination, and product detail extraction.
"""

import asyncio
import random
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import quote

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from utils.text import (
    extract_price, detect_currency_unit, normalize_seller_name, 
    normalize_part_title, clean_whitespace, normalize_digits
)
from core.config_manager import get_config
from core.cache_manager import get_cache


class TorobScraper:
    """
    Scraper for Torob.com marketplace.
    """
    
    def __init__(self, headless: bool = None, delay_range: tuple = None):
        """
        Initialize Torob scraper.
        
        Args:
            headless: Run browser in headless mode (overrides config)
            delay_range: Random delay range between requests (seconds) (overrides config)
        """
        self.config = get_config()
        self.cache = get_cache()
        self.headless = headless if headless is not None else self.config.get('browser.headless', True)
        self.delay_range = delay_range if delay_range is not None else self.config.get_delay_range()
        self.base_url = self.config.get('scraping.base_url', 'https://torob.com')
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # CSS selectors for Torob elements (updated based on actual page structure)
        self.selectors = {
            'product_cards': 'a[href*="/p/"]',  # Use the actual product links as cards
            'product_title': 'a[href*="/p/"] span, a[href*="/p/"], .ProductCard_desktop_title__3LVVm, h3, h4, .title',
            'product_price': '[class*="price"]',
            'product_link': 'a[href*="/p/"]',
            'seller_name': '.ProductCard_desktop_seller__3LVVm, .seller-name, .shop-name, .store-name',
            'seller_link': 'a[href*="/shop/"]',
            'availability': '.availability, .stock-status, .in-stock',
            'load_more': '.load-more, .show-more, [data-testid="load-more"]',
            'no_results': '.no-results, .empty-state, .no-products'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the browser and create context."""
        self.playwright = await async_playwright().start()
        # Get browser configuration
        browser_config = self.config.get_browser_config()
        viewport = browser_config.get('viewport', {'width': 1920, 'height': 1080})
        user_agent = browser_config.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport=viewport
        )
        self.page = await self.context.new_page()
    
    async def close(self):
        """Close the browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def _random_delay(self):
        """Add random delay between requests."""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)
    
    async def _scroll_to_load_more(self) -> bool:
        """
        Scroll to bottom and check if more content loads.
        
        Returns:
            True if new content was loaded, False otherwise
        """
        try:
            # Get current product count
            current_products = await self.page.locator(self.selectors['product_cards']).count()
            
            # Scroll to bottom
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Get scroll configuration
            scroll_config = self.config.get_scroll_config()
            scroll_delay = scroll_config.get('scroll_delay', 2.0)
            scroll_pause = scroll_config.get('scroll_pause', 1.0)
            
            # Wait for potential new content
            await asyncio.sleep(scroll_delay)
            
            # Check if load more button exists and click it
            load_more_button = self.page.locator(self.selectors['load_more'])
            if await load_more_button.count() > 0:
                await load_more_button.click()
                await asyncio.sleep(scroll_pause)
            
            # Check if new products loaded
            new_products = await self.page.locator(self.selectors['product_cards']).count()
            
            return new_products > current_products
            
        except Exception as e:
            print(f"Error during scrolling: {e}")
            return False
    
    async def _extract_product_data(self, product_element) -> Dict[str, Any]:
        """
        Extract data from a single product card element.
        
        Args:
            product_element: Playwright locator for product card (which is now the link itself)
            
        Returns:
            Dictionary with extracted product data
        """
        try:
            # Since product_element is now the link itself, extract URL first
            product_url = ""
            href = await product_element.get_attribute('href')
            if href:
                product_url = href if href.startswith('http') else f"{self.base_url}{href}"
            
            # Extract title from the link text
            title_raw = ""
            try:
                title_text = await product_element.text_content()
                if title_text and title_text.strip() and len(title_text.strip()) > 5:
                    title_raw = clean_whitespace(title_text)
            except:
                pass
            
            # Look for price in the parent container or nearby elements
            price_text = ""
            price_raw = None
            currency_unit = "unknown"
            
            try:
                # Try to find price in the parent container
                parent = product_element.locator('..')
                for price_selector in ['[class*="price"]', '.price', '.product-price', 'span']:
                    price_element = parent.locator(price_selector).first
                    if await price_element.count() > 0:
                        price_text = await price_element.text_content()
                        if price_text and price_text.strip():
                            # Check if this looks like a price
                            if any(char in price_text for char in ['تومان', 'ریال', '،', '.', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
                                price_text = clean_whitespace(price_text)
                                price_raw = extract_price(price_text)
                                currency_unit = detect_currency_unit(price_text)
                                break
            except:
                pass
            
            # Look for seller info in the parent container
            seller_name = ""
            seller_url = ""
            try:
                parent = product_element.locator('..')
                for seller_selector in ['.ProductCard_desktop_seller__3LVVm', '.seller-name', '.shop-name', '.store-name', 'span']:
                    seller_element = parent.locator(seller_selector).first
                    if await seller_element.count() > 0:
                        seller_text = await seller_element.text_content()
                        if seller_text and seller_text.strip():
                            # Check if this looks like a seller name (not a price)
                            if not any(char in seller_text for char in ['تومان', 'ریال', '،', '.', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
                                seller_name = clean_whitespace(seller_text)
                                
                                # Try to find seller URL
                                try:
                                    seller_link = seller_element.locator('a').first
                                    if await seller_link.count() > 0:
                                        href = await seller_link.get_attribute('href')
                                        if href:
                                            seller_url = href if href.startswith('http') else f"{self.base_url}{href}"
                                except:
                                    pass
                                break
            except:
                pass
            
            # Extract availability
            availability = ""
            try:
                parent = product_element.locator('..')
                availability_element = parent.locator(self.selectors['availability']).first
                if await availability_element.count() > 0:
                    availability_text = await availability_element.text_content()
                    if availability_text:
                        availability = clean_whitespace(availability_text)
            except:
                pass
            
            # Only return data if we have at least a title or price
            if title_raw or price_raw:
                return {
                    'title_raw': title_raw,
                    'price_raw': price_raw,
                    'price_text': price_text,
                    'currency_unit': currency_unit,
                    'seller_name': seller_name,
                    'product_url': product_url,
                    'seller_url': seller_url,
                    'availability': availability,
                    'snapshot_ts': datetime.now().isoformat()
                }
            else:
                return None  # Skip this product if no useful data
                
        except Exception as e:
            print(f"Error extracting product data: {e}")
            return None
    
    async def search_parts(self, keywords: str, max_scroll_attempts: int = None) -> List[Dict[str, Any]]:
        """
        Search for parts on Torob using keywords.
        
        Args:
            keywords: Search query string
            max_scroll_attempts: Maximum number of scroll attempts to load more results (overrides config)
            
        Returns:
            List of product dictionaries
        """
        if max_scroll_attempts is None:
            max_scroll_attempts = self.config.get('scraping.scroll.max_attempts', 5)
        if not keywords.strip():
            return []
        
        # Check cache first
        cached_results = self.cache.get_search_results(keywords)
        if cached_results is not None:
            print(f"💾 Using cached results for: {keywords[:50]}...")
            return cached_results
        
        try:
            # Build search URL
            encoded_keywords = quote(keywords.strip())
            search_url = f"{self.base_url}/search/?query={encoded_keywords}"
            
            print(f"Searching Torob: {keywords}")
            print(f"URL: {search_url}")
            
            # Navigate to search page
            await self.page.goto(search_url, wait_until='networkidle')
            await self._random_delay()
            
            # Wait for the page to load and extract data from JSON
            await self.page.wait_for_timeout(3000)  # Wait 3 seconds for dynamic content
            
            # Try to extract data from the embedded JSON
            try:
                # Get the page content and extract JSON data
                page_content = await self.page.content()
                
                # Look for the JSON data in script tags - use the working pattern
                import re
                json_match = re.search(r'<script[^>]*>.*?__NEXT_DATA__.*?({.*?})</script>', page_content, re.DOTALL)
                if json_match:
                    import json
                    try:
                        json_data = json.loads(json_match.group(1))
                        print(f"✅ Successfully parsed JSON data")
                        
                        # Extract products from the JSON data - correct path
                        products = json_data.get('props', {}).get('pageProps', {}).get('products', [])
                        
                        if products:
                            print(f"Found {len(products)} products in JSON data")
                            all_products = []
                            
                            for product in products:
                                try:
                                    # Extract data from JSON structure
                                    title_raw = product.get('name1', '') or product.get('name2', '')
                                    price_raw = product.get('price', 0)
                                    price_text = product.get('price_text', '')
                                    product_url = product.get('web_client_absolute_url', '')
                                    shop_text = product.get('shop_text', '')
                                    stock_status = product.get('stock_status', '')
                                    
                                    # Convert price to number
                                    if price_raw and price_raw > 0:
                                        price_raw = int(price_raw)
                                    else:
                                        price_raw = 0
                                    
                                    # Detect currency
                                    currency_unit = detect_currency_unit(price_text) if price_text else 'unknown'
                                    
                                    # Extract seller name from shop_text
                                    seller_name = ""
                                    if shop_text:
                                        # Extract seller name from "در فروشگاه" text
                                        seller_match = re.search(r'در\s+([^،]+)', shop_text)
                                        if seller_match:
                                            seller_name = seller_match.group(1).strip()
                                    
                                    # Build full URL
                                    if product_url and not product_url.startswith('http'):
                                        product_url = f"{self.base_url}{product_url}"
                                    
                                    if title_raw or price_raw:
                                        product_data = {
                                            'title_raw': title_raw,
                                            'price_raw': price_raw,
                                            'price_text': price_text,
                                            'currency_unit': currency_unit,
                                            'seller_name': seller_name,
                                            'product_url': product_url,
                                            'seller_url': '',  # Not available in search results
                                            'availability': stock_status,
                                            'snapshot_ts': datetime.now().isoformat()
                                        }
                                        all_products.append(product_data)
                                        
                                except Exception as e:
                                    print(f"Error processing product from JSON: {e}")
                                    continue
                            
                            print(f"Total products extracted from JSON: {len(all_products)}")
                            
                            # Cache the results
                            self.cache.set_search_results(keywords, all_products)
                            
                            return all_products
                    
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        # Fall back to CSS selectors
                        pass
                
            except Exception as e:
                print(f"Error extracting JSON data: {e}")
            
            # Fallback to CSS selector method
            print("Falling back to CSS selector method...")
            
            # Check for no results
            no_results = self.page.locator(self.selectors['no_results'])
            if await no_results.count() > 0:
                print("No results found")
                return []
            
            # Collect products with scrolling
            all_products = []
            scroll_attempts = 0
            
            while scroll_attempts < max_scroll_attempts:
                # Extract current products
                product_cards = self.page.locator(self.selectors['product_cards'])
                card_count = await product_cards.count()
                
                print(f"Found {card_count} product cards on page")
                
                # Extract data from each product card
                for i in range(card_count):
                    try:
                        card = product_cards.nth(i)
                        product_data = await self._extract_product_data(card)
                        
                        if product_data:  # Only add if we got valid data
                            all_products.append(product_data)
                    
                    except Exception as e:
                        print(f"Error extracting product {i}: {e}")
                        continue
                
                # Try to load more products
                print(f"Scroll attempt {scroll_attempts + 1}/{max_scroll_attempts}")
                more_loaded = await self._scroll_to_load_more()
                
                if not more_loaded:
                    print("No more products to load")
                    break
                
                scroll_attempts += 1
                await self._random_delay()
            
            print(f"Total products extracted: {len(all_products)}")
            
            # Cache the results
            self.cache.set_search_results(keywords, all_products)
            
            return all_products
            
        except Exception as e:
            print(f"Error during search: {e}")
            return []
    
    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Get detailed information from a product page.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with detailed product information
        """
        # Check cache first
        cached_details = self.cache.get_product_details(product_url)
        if cached_details is not None:
            print(f"💾 Using cached product details for: {product_url[:50]}...")
            return cached_details
        
        try:
            if not product_url:
                return {}
            
            print(f"Getting product details: {product_url}")
            
            # Navigate to product page
            await self.page.goto(product_url, wait_until='networkidle')
            await self._random_delay()
            
            # Extract detailed product information
            product_data = {
                'product_url': product_url,
                'offers': [],
                'snapshot_ts': datetime.now().isoformat()
            }
            
            # Look for seller offers on the product page
            # Try multiple selectors for seller offers
            offer_selectors = [
                '.offer-card', 
                '.seller-offer', 
                '.price-comparison-item',
                '[class*="offer"]',
                '[class*="seller"]',
                '[class*="price"]'
            ]
            
            offer_cards = None
            offer_count = 0
            
            for selector in offer_selectors:
                try:
                    cards = self.page.locator(selector)
                    count = await cards.count()
                    if count > 0:
                        offer_cards = cards
                        offer_count = count
                        print(f"Found {offer_count} offers using selector: {selector}")
                        break
                except:
                    continue
            
            if not offer_cards or offer_count == 0:
                print("No seller offers found on product page")
                return product_data
            
            for i in range(offer_count):
                try:
                    offer_card = offer_cards.nth(i)
                    
                    # Extract seller name - try multiple selectors
                    seller_name = ""
                    for seller_selector in ['.seller-name', '.shop-name', '.store-name', '[class*="seller"]', '[class*="shop"]']:
                        seller_element = offer_card.locator(seller_selector).first
                        if await seller_element.count() > 0:
                            seller_text = await seller_element.text_content()
                            if seller_text and seller_text.strip():
                                seller_name = clean_whitespace(seller_text)
                                break
                    
                    # Extract price - try multiple selectors
                    price_text = ""
                    price_raw = None
                    currency_unit = "unknown"
                    
                    for price_selector in ['.price', '.product-price', '[class*="price"]', '[class*="cost"]']:
                        price_element = offer_card.locator(price_selector).first
                        if await price_element.count() > 0:
                            price_text = await price_element.text_content()
                            if price_text and price_text.strip():
                                price_text = clean_whitespace(price_text)
                                price_raw = extract_price(price_text)
                                currency_unit = detect_currency_unit(price_text)
                                break
                    
                    # Extract seller URL
                    seller_url = ""
                    for link_selector in ['a[href*="/shop/"]', 'a[href*="/seller/"]', 'a']:
                        seller_link_element = offer_card.locator(link_selector).first
                        if await seller_link_element.count() > 0:
                            href = await seller_link_element.get_attribute('href')
                            if href and ('shop' in href or 'seller' in href):
                                seller_url = href if href.startswith('http') else f"{self.base_url}{href}"
                                break
                    
                    offer_data = {
                        'seller_name': seller_name,
                        'price_raw': price_raw,
                        'price_text': price_text,
                        'currency_unit': currency_unit,
                        'seller_url': seller_url,
                        'availability': "",  # Could extract if available
                    }
                    
                    if seller_name or price_raw:  # Only add if we got some valid data
                        product_data['offers'].append(offer_data)
                
                except Exception as e:
                    print(f"Error extracting offer {i}: {e}")
                    continue
            
            print(f"Successfully extracted {len(product_data['offers'])} offers from product page")
            return product_data
            
        except Exception as e:
            print(f"Error getting product details: {e}")
            return {}
    
    async def scrape_part(self, part_id: int, part_name: str, part_code: str, keywords: str) -> List[Dict[str, Any]]:
        """
        Scrape all offers for a single part.
        
        Args:
            part_id: Unique part identifier
            part_name: Human-readable part name
            part_code: Part code/OEM number
            keywords: Search keywords
            
        Returns:
            List of offer dictionaries
        """
        print(f"\n{'='*60}")
        print(f"Scraping Part ID {part_id}: {part_name}")
        print(f"Keywords: {keywords}")
        print(f"{'='*60}")
        
        all_offers = []
        
        try:
            # Search for the part
            search_results = await self.search_parts(keywords)
            
            if not search_results:
                print("No search results found")
                return []
            
            # Process each search result
            for result in search_results:
                offer = {
                    'part_id': part_id,
                    'part_name': part_name,
                    'part_code': part_code,
                    'keywords': keywords,
                    'title_raw': result['title_raw'],
                    'price_raw': result['price_raw'],
                    'price_text': result['price_text'],
                    'currency_unit': result['currency_unit'],
                    'seller_name': result['seller_name'],
                    'product_url': result['product_url'],
                    'seller_url': "",  # Will be filled if we drill down
                    'availability': result['availability'],
                    'snapshot_ts': result['snapshot_ts']
                }
                
                all_offers.append(offer)
            
            # Optionally drill down into product pages for additional seller offers
            # This is commented out to avoid being too aggressive, but can be enabled
            """
            for result in search_results[:3]:  # Limit to first 3 for efficiency
                if result['product_url']:
                    await self._random_delay()
                    product_details = await self.get_product_details(result['product_url'])
                    
                    for offer_detail in product_details.get('offers', []):
                        additional_offer = {
                            'part_id': part_id,
                            'part_name': part_name,
                            'part_code': part_code,
                            'keywords': keywords,
                            'title_raw': result['title_raw'],
                            'price_raw': offer_detail['price_raw'],
                            'price_text': offer_detail['price_text'],
                            'currency_unit': offer_detail['currency_unit'],
                            'seller_name': offer_detail['seller_name'],
                            'product_url': result['product_url'],
                            'seller_url': offer_detail['seller_url'],
                            'availability': offer_detail['availability'],
                            'snapshot_ts': offer_detail.get('snapshot_ts', datetime.now().isoformat())
                        }
                        
                        all_offers.append(additional_offer)
            """
            
            print(f"Total offers found: {len(all_offers)}")
            
            # Cache the product details
            self.cache.set_product_details(product_url, all_offers)
            
            return all_offers
            
        except Exception as e:
            print(f"Error scraping part {part_id}: {e}")
            return []


async def test_scraper():
    """Test the Torob scraper with sample data."""
    test_keywords = "چراغ جلو چپ تیگو 8 پرو مکس"
    
    async with TorobScraper(headless=False) as scraper:
        results = await scraper.search_parts(test_keywords, max_scroll_attempts=2)
        
        print(f"\nTest Results for '{test_keywords}':")
        print(f"Found {len(results)} products")
        
        for i, result in enumerate(results[:5]):  # Show first 5
            print(f"\n{i+1}. {result['title_raw']}")
            print(f"   Price: {result['price_text']} ({result['currency_unit']})")
            print(f"   Seller: {result['seller_name']}")
            print(f"   URL: {result['product_url']}")


if __name__ == "__main__":
    asyncio.run(test_scraper())
