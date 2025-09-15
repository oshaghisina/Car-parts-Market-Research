"""
Tests for utility functions.
"""

import pytest

from utils.text import (
    clean_whitespace,
    detect_currency_unit,
    extract_price,
    normalize_digits,
)


class TestTextUtils:
    """Test text utility functions."""

    def test_normalize_digits(self):
        """Test Persian/Arabic digit normalization."""
        # Persian digits
        assert normalize_digits("۱۲۳۴۵") == "12345"
        assert normalize_digits("۰۱۲۳۴۵۶۷۸۹") == "0123456789"

        # Arabic digits
        assert normalize_digits("٠١٢٣٤٥٦٧٨٩") == "0123456789"

        # Mixed content
        assert normalize_digits("قیمت: ۱۲۳,۰۰۰ تومان") == "قیمت: 123,000 تومان"

        # No digits
        assert normalize_digits("hello world") == "hello world"

        # Empty string
        assert normalize_digits("") == ""

    def test_clean_whitespace(self):
        """Test whitespace cleaning."""
        assert clean_whitespace("  hello   world  ") == "hello world"
        assert clean_whitespace("hello\n\tworld") == "hello world"
        assert clean_whitespace("") == ""
        assert clean_whitespace("   ") == ""

    def test_extract_price(self):
        """Test price extraction."""
        # Valid prices
        assert extract_price("قیمت: 123,000 تومان") == 123000
        assert extract_price("۱۲۳,۰۰۰ تومان") == 123000
        assert extract_price("123000") == 123000

        # Invalid prices
        assert extract_price("تماس بگیرید") == 0
        assert extract_price("") == 0
        assert extract_price("قیمت نامشخص") == 0

    def test_detect_currency_unit(self):
        """Test currency unit detection."""
        assert detect_currency_unit("123,000 تومان") == "toman"
        assert detect_currency_unit("123,000 ریال") == "rial"
        assert detect_currency_unit("123,000") == "unknown"
        assert detect_currency_unit("") == "unknown"
