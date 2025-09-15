"""
Text utilities for normalizing Persian/Arabic text and extracting prices.
"""

import re
from typing import Optional, Union


# Persian and Arabic digit mappings
PERSIAN_DIGITS = {
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
}

ARABIC_DIGITS = {
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
}

# Common price separators and currency indicators
PRICE_SEPARATORS = [",", "،", ".", " "]
CURRENCY_INDICATORS = ["تومان", "ریال", "ﺗﻮﻣﺎﻥ", "ﺭﯾﺎﻝ", "تومن", "ریل"]


def normalize_digits(text: str) -> str:
    """
    Convert Persian and Arabic digits to Latin digits.

    Args:
        text: Input text containing Persian/Arabic digits

    Returns:
        Text with normalized Latin digits
    """
    if not text:
        return text

    # Replace Persian digits
    for persian, latin in PERSIAN_DIGITS.items():
        text = text.replace(persian, latin)

    # Replace Arabic digits
    for arabic, latin in ARABIC_DIGITS.items():
        text = text.replace(arabic, latin)

    return text


def clean_whitespace(text: str) -> str:
    """
    Clean and normalize whitespace in text.

    Args:
        text: Input text

    Returns:
        Text with normalized whitespace
    """
    if not text:
        return text

    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_price(text: str) -> Optional[int]:
    """
    Extract price from text and return as integer (in smallest currency unit).

    Args:
        text: Text containing price information

    Returns:
        Price as integer or None if no valid price found
    """
    if not text:
        return None

    # Normalize digits first
    text = normalize_digits(text)

    # Remove currency indicators
    for indicator in CURRENCY_INDICATORS:
        text = text.replace(indicator, "")

    # Find all numeric sequences (with potential separators)
    price_patterns = [
        r"(\d{1,3}(?:[,،]\d{3})*(?:\.\d{2})?)",  # 1,000,000 or 1,000.50
        r"(\d+)",  # Simple number
    ]

    potential_prices = []

    for pattern in price_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Clean separators
            clean_price = match
            for sep in PRICE_SEPARATORS:
                clean_price = clean_price.replace(sep, "")

            try:
                price = int(clean_price)
                if price > 0:
                    potential_prices.append(price)
            except ValueError:
                continue

    if not potential_prices:
        return None

    # Return the largest price found (assuming it's the main price)
    return max(potential_prices)


def normalize_seller_name(seller_name: str) -> str:
    """
    Normalize seller name for deduplication.

    Args:
        seller_name: Raw seller name

    Returns:
        Normalized seller name
    """
    if not seller_name:
        return ""

    # Convert to lowercase
    name = seller_name.lower()

    # Clean whitespace
    name = clean_whitespace(name)

    # Remove common prefixes/suffixes
    prefixes_to_remove = ["فروشگاه", "شرکت", "گروه", "مجموعه"]
    suffixes_to_remove = ["store", "shop", "group", "co"]

    for prefix in prefixes_to_remove:
        if name.startswith(prefix):
            name = name[len(prefix) :].strip()

    for suffix in suffixes_to_remove:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()

    return name


def normalize_part_title(title: str) -> str:
    """
    Normalize part title for comparison and deduplication.

    Args:
        title: Raw part title

    Returns:
        Normalized part title
    """
    if not title:
        return ""

    # Clean whitespace
    title = clean_whitespace(title)

    # Convert to lowercase for comparison
    title = title.lower()

    # Remove common words that don't add value
    noise_words = ["اصل", "اصلی", "یدکی", "قطعه", "پارت", "part", "oem", "original"]

    for word in noise_words:
        title = re.sub(rf"\b{re.escape(word)}\b", "", title, flags=re.IGNORECASE)

    # Clean up multiple spaces
    title = clean_whitespace(title)

    return title


def convert_rial_to_toman(rial_amount: int) -> int:
    """
    Convert Rial to Toman (divide by 10).

    Args:
        rial_amount: Amount in Rial

    Returns:
        Amount in Toman
    """
    return rial_amount // 10


def convert_toman_to_rial(toman_amount: int) -> int:
    """
    Convert Toman to Rial (multiply by 10).

    Args:
        toman_amount: Amount in Toman

    Returns:
        Amount in Rial
    """
    return toman_amount * 10


def detect_currency_unit(text: str) -> str:
    """
    Detect if price is in Toman or Rial based on context.

    Args:
        text: Text containing price and currency info

    Returns:
        'toman' or 'rial' or 'unknown'
    """
    text_lower = text.lower()

    toman_indicators = ["تومان", "تومن", "ﺗﻮﻣﺎﻥ"]
    rial_indicators = ["ریال", "ریل", "ﺭﯾﺎﻝ"]

    for indicator in toman_indicators:
        if indicator in text_lower:
            return "toman"

    for indicator in rial_indicators:
        if indicator in text_lower:
            return "rial"

    return "unknown"


def format_price(price: int, currency: str = "toman") -> str:
    """
    Format price with proper thousand separators.

    Args:
        price: Price amount
        currency: Currency unit ('toman' or 'rial')

    Returns:
        Formatted price string
    """
    if price is None:
        return ""

    # Add thousand separators
    formatted = f"{price:,}"

    # Add currency suffix
    if currency == "toman":
        formatted += " تومان"
    elif currency == "rial":
        formatted += " ریال"

    return formatted


if __name__ == "__main__":
    # Test the functions
    test_texts = [
        "قیمت: ۱۲۳,۴۵۶ تومان",
        "Price: ٩٨٧.٦٥٤ ریال",
        "فروشگاه پارت سنتر",
        "چراغ جلو اصلی تیگو ۸",
    ]

    for text in test_texts:
        print(f"Original: {text}")
        print(f"Normalized digits: {normalize_digits(text)}")
        print(f"Extracted price: {extract_price(text)}")
        print(f"Currency: {detect_currency_unit(text)}")
        print("-" * 40)
