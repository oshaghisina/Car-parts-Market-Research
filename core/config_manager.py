#!/usr/bin/env python3
"""
Configuration Manager for Torob Scraper.
Handles loading and managing configuration settings from YAML files.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration settings for the Torob scraper."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as file:
                    self.config = yaml.safe_load(file) or {}
                print(f"✅ Configuration loaded from {self.config_path}")
            else:
                print(
                    f"⚠️  Configuration file {self.config_path} not found, using defaults"
                )
                self.config = self._get_default_config()
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            print("Using default configuration")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings."""
        return {
            "scraping": {
                "base_url": "https://torob.com",
                "delay_range": {"min": 1.5, "max": 3.0},
                "scroll": {"max_attempts": 3, "scroll_delay": 2.0, "scroll_pause": 1.0},
                "timeouts": {"page_load": 30, "element_wait": 10, "network_idle": 5},
            },
            "processing": {
                "price": {"default_currency": "toman", "convert_rial_to_toman": True},
                "text": {"normalize_digits": True, "clean_whitespace": True},
                "dedupe": {
                    "enabled": True,
                    "key_fields": ["seller_name_norm", "part_key", "title_norm"],
                },
            },
            "filtering": {
                "relevance": {"min_score": 0.0, "max_results": 50},
                "negative_keywords": [
                    "عقب",
                    "مه‌شکن",
                    "راهنما",
                    "روز روشن",
                    "DRL",
                    "daylight",
                    "indicator",
                    "rear",
                    "tail",
                    "fog",
                ],
            },
            "export": {
                "excel": {
                    "filename_template": "{part_name}.xlsx",
                    "sheets": {
                        "offers_raw": "offers_raw",
                        "sellers_summary": "sellers_summary",
                        "part_summary": "part_summary",
                    },
                    "formatting": {
                        "freeze_headers": True,
                        "add_filters": True,
                        "conditional_formatting": True,
                        "url_columns": True,
                        "column_widths": {
                            "title_raw": 50,
                            "product_url": 50,
                            "seller_url": 50,
                            "validation_urls": 60,
                            "sample_urls": 60,
                        },
                    },
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "console": {"enabled": True, "show_progress": True, "show_stats": True},
                "file": {
                    "enabled": False,
                    "filename": "torob_scraper.log",
                    "max_size": "10MB",
                    "backup_count": 5,
                },
            },
            "browser": {
                "headless": True,
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "options": {
                    "disable_images": True,
                    "disable_css": False,
                    "disable_javascript": False,
                },
            },
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the configuration value (e.g., 'scraping.delay_range.min')
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration."""
        return self.get("scraping", {})

    def get_processing_config(self) -> Dict[str, Any]:
        """Get data processing configuration."""
        return self.get("processing", {})

    def get_filtering_config(self) -> Dict[str, Any]:
        """Get filtering configuration."""
        return self.get("filtering", {})

    def get_export_config(self) -> Dict[str, Any]:
        """Get export configuration."""
        return self.get("export", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get("logging", {})

    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration."""
        return self.get("browser", {})

    def get_delay_range(self) -> tuple:
        """Get delay range as tuple."""
        delay_config = self.get("scraping.delay_range", {})
        return (delay_config.get("min", 1.5), delay_config.get("max", 3.0))

    def get_scroll_config(self) -> Dict[str, Any]:
        """Get scroll configuration."""
        return self.get("scraping.scroll", {})

    def get_timeout_config(self) -> Dict[str, Any]:
        """Get timeout configuration."""
        return self.get("scraping.timeouts", {})

    def get_negative_keywords(self) -> list:
        """Get negative keywords for filtering."""
        return self.get("filtering.negative_keywords", [])

    def get_relevance_config(self) -> Dict[str, Any]:
        """Get relevance scoring configuration."""
        return self.get("filtering.relevance", {})

    def get_excel_config(self) -> Dict[str, Any]:
        """Get Excel export configuration."""
        return self.get("export.excel", {})

    def get_excel_formatting_config(self) -> Dict[str, Any]:
        """Get Excel formatting configuration."""
        return self.get("export.excel.formatting", {})

    def get_column_widths(self) -> Dict[str, int]:
        """Get column width configuration."""
        return self.get("export.excel.formatting.column_widths", {})

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    def save(self, output_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            output_path: Optional output path, defaults to config_path
        """
        save_path = output_path or self.config_path
        try:
            with open(save_path, "w", encoding="utf-8") as file:
                yaml.dump(
                    self.config,
                    file,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )
            print(f"✅ Configuration saved to {save_path}")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")

    def update(self, key_path: str, value: Any) -> None:
        """
        Update a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the configuration value
            value: New value to set
        """
        keys = key_path.split(".")
        config = self.config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

    def validate(self) -> bool:
        """
        Validate the current configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check required sections
            required_sections = [
                "scraping",
                "processing",
                "filtering",
                "export",
                "logging",
                "browser",
            ]
            for section in required_sections:
                if section not in self.config:
                    print(f"❌ Missing required configuration section: {section}")
                    return False

            # Validate scraping config
            scraping = self.config["scraping"]
            if "base_url" not in scraping:
                print("❌ Missing base_url in scraping config")
                return False

            if "delay_range" not in scraping:
                print("❌ Missing delay_range in scraping config")
                return False

            # Validate delay range
            delay_range = scraping["delay_range"]
            if not isinstance(delay_range.get("min"), (int, float)) or not isinstance(
                delay_range.get("max"), (int, float)
            ):
                print("❌ Invalid delay_range values")
                return False

            if delay_range["min"] >= delay_range["max"]:
                print("❌ delay_range min must be less than max")
                return False

            print("✅ Configuration validation passed")
            return True

        except Exception as e:
            print(f"❌ Configuration validation error: {e}")
            return False


# Global configuration instance
config = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration instance."""
    return config
