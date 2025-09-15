#!/usr/bin/env python3
"""
Cache Manager for Torob Scraper.
Handles caching of search results and product data to improve performance.
"""

import json
import hashlib
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.config_manager import get_config


class CacheManager:
    """Manages caching of search results and product data."""

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.config = get_config()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Cache settings from config
        self.enabled = self.config.get("caching.enabled", True)
        self.ttl_hours = self.config.get("caching.ttl_hours", 24)
        self.max_cache_size_mb = self.config.get("caching.max_size_mb", 100)

        # Cache statistics
        self.stats = {"hits": 0, "misses": 0, "expired": 0, "size_mb": 0}

    def _generate_cache_key(self, query: str, cache_type: str = "search") -> str:
        """
        Generate a cache key for the given query.

        Args:
            query: Search query or identifier
            cache_type: Type of cache (search, product, etc.)

        Returns:
            Cache key string
        """
        # Normalize query for consistent keys
        normalized_query = query.strip().lower()

        # Create hash of the query
        query_hash = hashlib.md5(normalized_query.encode("utf-8")).hexdigest()

        return f"{cache_type}_{query_hash}"

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_data: Dict[str, Any]) -> bool:
        """
        Check if cache data is still valid.

        Args:
            cache_data: Cached data dictionary

        Returns:
            True if cache is valid, False if expired
        """
        if not cache_data:
            return False

        # Check if cache has timestamp
        if "cached_at" not in cache_data:
            return False

        # Check if cache is expired
        cached_time = datetime.fromisoformat(cache_data["cached_at"])
        expiry_time = cached_time + timedelta(hours=self.ttl_hours)

        return datetime.now() < expiry_time

    def _cleanup_expired_cache(self) -> None:
        """Remove expired cache files."""
        if not self.cache_dir.exists():
            return

        current_time = datetime.now()
        removed_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                if not self._is_cache_valid(cache_data):
                    cache_file.unlink()
                    removed_count += 1
                    self.stats["expired"] += 1

            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                # Remove corrupted cache files
                cache_file.unlink()
                removed_count += 1

        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} expired cache files")

    def _check_cache_size(self) -> None:
        """Check and manage cache size."""
        if not self.cache_dir.exists():
            return

        # Calculate current cache size
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        size_mb = total_size / (1024 * 1024)
        self.stats["size_mb"] = size_mb

        # If cache is too large, remove oldest files
        if size_mb > self.max_cache_size_mb:
            print(
                f"⚠️  Cache size ({size_mb:.1f}MB) exceeds limit ({self.max_cache_size_mb}MB)"
            )
            self._cleanup_oldest_cache()

    def _cleanup_oldest_cache(self) -> None:
        """Remove oldest cache files to stay under size limit."""
        cache_files = []

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                if "cached_at" in cache_data:
                    cached_time = datetime.fromisoformat(cache_data["cached_at"])
                    cache_files.append((cached_time, cache_file))

            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                continue

        # Sort by cached time (oldest first)
        cache_files.sort(key=lambda x: x[0])

        # Remove oldest files until under limit
        current_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        target_size = self.max_cache_size_mb * 1024 * 1024 * 0.8  # 80% of limit

        for cached_time, cache_file in cache_files:
            if current_size <= target_size:
                break

            file_size = cache_file.stat().st_size
            cache_file.unlink()
            current_size -= file_size
            print(f"🗑️  Removed old cache file: {cache_file.name}")

    def get(self, query: str, cache_type: str = "search") -> Optional[Dict[str, Any]]:
        """
        Get cached data for a query.

        Args:
            query: Search query or identifier
            cache_type: Type of cache (search, product, etc.)

        Returns:
            Cached data if valid, None if not found or expired
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(query, cache_type)
        cache_file = self._get_cache_file_path(cache_key)

        if not cache_file.exists():
            self.stats["misses"] += 1
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            if self._is_cache_valid(cache_data):
                self.stats["hits"] += 1
                print(f"💾 Cache hit for {cache_type}: {query[:50]}...")
                return cache_data.get("data")
            else:
                # Remove expired cache
                cache_file.unlink()
                self.stats["expired"] += 1
                self.stats["misses"] += 1
                return None

        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            # Remove corrupted cache
            cache_file.unlink()
            self.stats["misses"] += 1
            return None

    def set(self, query: str, data: Any, cache_type: str = "search") -> None:
        """
        Cache data for a query.

        Args:
            query: Search query or identifier
            data: Data to cache
            cache_type: Type of cache (search, product, etc.)
        """
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(query, cache_type)
        cache_file = self._get_cache_file_path(cache_key)

        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "cache_type": cache_type,
            "query": query,
            "data": data,
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            print(f"💾 Cached {cache_type}: {query[:50]}...")

            # Check cache size and cleanup if needed
            self._check_cache_size()

        except Exception as e:
            print(f"❌ Error caching data: {e}")

    def get_search_results(self, keywords: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results.

        Args:
            keywords: Search keywords

        Returns:
            Cached search results if valid, None otherwise
        """
        return self.get(keywords, "search")

    def set_search_results(self, keywords: str, results: List[Dict[str, Any]]) -> None:
        """
        Cache search results.

        Args:
            keywords: Search keywords
            results: Search results to cache
        """
        self.set(keywords, results, "search")

    def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached product details.

        Args:
            product_url: Product URL

        Returns:
            Cached product details if valid, None otherwise
        """
        return self.get(product_url, "product")

    def set_product_details(self, product_url: str, details: Dict[str, Any]) -> None:
        """
        Cache product details.

        Args:
            product_url: Product URL
            details: Product details to cache
        """
        self.set(product_url, details, "product")

    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """
        Clear cache files.

        Args:
            cache_type: Specific cache type to clear, or None for all
        """
        if not self.cache_dir.exists():
            return

        if cache_type:
            pattern = f"{cache_type}_*.json"
        else:
            pattern = "*.json"

        removed_count = 0
        for cache_file in self.cache_dir.glob(pattern):
            cache_file.unlink()
            removed_count += 1

        print(f"🗑️  Cleared {removed_count} cache files")

        # Reset stats
        self.stats = {"hits": 0, "misses": 0, "expired": 0, "size_mb": 0}

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._check_cache_size()

        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "enabled": self.enabled,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "expired": self.stats["expired"],
            "hit_rate": round(hit_rate, 2),
            "size_mb": round(self.stats["size_mb"], 2),
            "max_size_mb": self.max_cache_size_mb,
            "ttl_hours": self.ttl_hours,
        }

    def cleanup(self) -> None:
        """Clean up expired cache files."""
        self._cleanup_expired_cache()


# Global cache instance
cache = CacheManager()


def get_cache() -> CacheManager:
    """Get the global cache instance."""
    return cache
