"""
Main pipeline orchestrator for the Torob scraper.
Coordinates CSV input, scraping, normalization, deduplication, and Excel export.
"""

import asyncio
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from adapters.torob_search import TorobScraper
from core.dedupe import OfferDeduplicator
from core.entity_normalizer import PartNormalizer
from core.exporter import ExcelExporter
from utils.text import convert_rial_to_toman, detect_currency_unit


class ScrapingPipeline:
    """
    Main pipeline for orchestrating the entire scraping workflow.
    """

    def __init__(
        self,
        input_file: str = "parts_input.csv",
        output_file: str = "torob_prices.xlsx",
        headless: bool = True,
        delay_range: tuple = (1.5, 3.0),
    ):
        """
        Initialize the scraping pipeline.

        Args:
            input_file: Path to CSV input file
            output_file: Path to Excel output file
            headless: Run browser in headless mode
            delay_range: Random delay range between requests
        """
        self.input_file = input_file
        self.output_file = output_file
        self.headless = headless
        self.delay_range = delay_range

        # Initialize components
        self.normalizer = PartNormalizer()
        self.deduplicator = OfferDeduplicator()
        self.exporter = ExcelExporter(output_file)

        # Statistics
        self.stats = {
            "start_time": None,
            "end_time": None,
            "parts_processed": 0,
            "total_offers_found": 0,
            "offers_after_dedup": 0,
            "unique_sellers": 0,
            "errors": [],
        }

    def load_input_parts(self) -> List[Dict[str, Any]]:
        """
        Load parts from CSV input file.

        Returns:
            List of part dictionaries
        """
        if not Path(self.input_file).exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        parts = []

        try:
            with open(self.input_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                for row in reader:
                    part = {
                        "part_id": int(row.get("part_id", 0)),
                        "part_name": row.get("part_name", "").strip(),
                        "part_code": row.get("part_code", "").strip(),
                        "keywords": row.get("keywords", "").strip(),
                    }

                    if part["part_id"] and part["part_name"] and part["keywords"]:
                        parts.append(part)
                    else:
                        print(f"Warning: Skipping incomplete part: {part}")

            print(f"Loaded {len(parts)} parts from {self.input_file}")
            return parts

        except Exception as e:
            error_msg = f"Error loading input file: {e}"
            print(error_msg)
            self.stats["errors"].append(error_msg)
            return []

    def normalize_part_metadata(self, part: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add normalized metadata to a part.

        Args:
            part: Part dictionary

        Returns:
            Part dictionary with added metadata
        """
        try:
            metadata = self.normalizer.extract_metadata(
                part["part_name"], part.get("part_code")
            )

            part.update(
                {
                    "part_key": metadata["part_key"],
                    "part_name_norm": metadata["normalized_name"],
                    "car_model": metadata["car_model"],
                    "part_type": metadata["part_type"],
                    "side": metadata["side"],
                    "variant": metadata["variant"],
                    "trim": metadata["trim"],
                }
            )

            # Validate extraction
            is_valid, issues = self.normalizer.validate_extraction(
                part["part_name"], part.get("part_code")
            )

            if not is_valid:
                warning_msg = (
                    f"Part {part['part_id']} normalization issues: {', '.join(issues)}"
                )
                print(f"Warning: {warning_msg}")
                self.stats["errors"].append(warning_msg)

            return part

        except Exception as e:
            error_msg = f"Error normalizing part {part.get('part_id', 'unknown')}: {e}"
            print(f"Error: {error_msg}")
            self.stats["errors"].append(error_msg)
            return part

    async def scrape_part_offers(
        self, scraper: TorobScraper, part: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Scrape offers for a single part.

        Args:
            scraper: TorobScraper instance
            part: Part dictionary

        Returns:
            List of offer dictionaries
        """
        try:
            offers = await scraper.scrape_part(
                part["part_id"], part["part_name"], part["part_code"], part["keywords"]
            )

            # Add part metadata to each offer
            for offer in offers:
                offer.update(
                    {
                        "part_key": part.get("part_key", ""),
                        "part_name_norm": part.get("part_name_norm", ""),
                        "car_model": part.get("car_model", ""),
                        "part_type": part.get("part_type", ""),
                        "side": part.get("side", ""),
                        "variant": part.get("variant", ""),
                        "trim": part.get("trim", ""),
                    }
                )

            return offers

        except Exception as e:
            error_msg = f"Error scraping part {part.get('part_id', 'unknown')}: {e}"
            print(f"Error: {error_msg}")
            self.stats["errors"].append(error_msg)
            return []

    def normalize_offer_prices(
        self, offers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Normalize prices to Toman for all offers.

        Args:
            offers: List of offer dictionaries

        Returns:
            List of offers with normalized prices
        """
        normalized_offers = []

        for offer in offers:
            try:
                price_raw = offer.get("price_raw", 0) or 0
                currency_unit = offer.get("currency_unit", "unknown")

                # Convert Rial to Toman if needed
                if currency_unit == "rial" and price_raw > 0:
                    price_toman = convert_rial_to_toman(price_raw)
                    offer["price_raw"] = price_toman
                    offer["currency_unit"] = "toman"

                # Skip offers without valid prices
                if price_raw <= 0:
                    continue

                normalized_offers.append(offer)

            except Exception as e:
                error_msg = f"Error normalizing price for offer: {e}"
                print(f"Warning: {error_msg}")
                continue

        return normalized_offers

    def setup_seller_mappings(self):
        """Setup known seller name mappings for better deduplication."""
        # Add common seller name variations
        mappings = [
            (["فروشگاه پارت سنتر", "پارت سنتر", "partcenter"], "پارت سنتر"),
            (["یدک شاپ", "yadakshop", "یدک‌شاپ"], "یدک شاپ"),
            (["اتو پارت", "autopart", "auto part"], "اتو پارت"),
            (["کری پارت", "carrypart", "carry part"], "کری پارت"),
            (["ایران پارت", "iranpart", "iran part"], "ایران پارت"),
        ]

        for variations, canonical in mappings:
            self.deduplicator.add_seller_mapping(variations, canonical)

    async def run_pipeline(self) -> bool:
        """
        Run the complete scraping pipeline.

        Returns:
            True if successful, False otherwise
        """
        self.stats["start_time"] = datetime.now()

        try:
            print("🚀 Starting Torob Automotive Parts Scraper Pipeline")
            print("=" * 60)

            # Step 1: Load input parts
            print("📁 Step 1: Loading input parts...")
            parts = self.load_input_parts()

            if not parts:
                print("❌ No valid parts found in input file")
                return False

            # Step 2: Normalize part metadata
            print("🔧 Step 2: Normalizing part metadata...")
            for i, part in enumerate(parts):
                parts[i] = self.normalize_part_metadata(part)
                print(f"   ✓ Part {part['part_id']}: {part.get('part_key', 'UNKNOWN')}")

            # Step 3: Setup seller mappings
            print("👥 Step 3: Setting up seller mappings...")
            self.setup_seller_mappings()

            # Step 4: Scrape offers
            print("🕷️  Step 4: Scraping offers from Torob...")
            all_offers = []

            async with TorobScraper(
                headless=self.headless, delay_range=self.delay_range
            ) as scraper:
                for i, part in enumerate(parts):
                    print(
                        f"\n🔍 Processing part {i+1}/{len(parts)}: {part['part_name']}"
                    )

                    offers = await self.scrape_part_offers(scraper, part)
                    all_offers.extend(offers)

                    self.stats["parts_processed"] += 1

                    print(f"   ✓ Found {len(offers)} offers for part {part['part_id']}")

                    # Add delay between parts to be respectful
                    if i < len(parts) - 1:  # Don't delay after last part
                        await asyncio.sleep(2)

            self.stats["total_offers_found"] = len(all_offers)
            print(f"\n📊 Total offers found: {len(all_offers)}")

            if not all_offers:
                print("❌ No offers found. Pipeline complete but no data to export.")
                return False

            # Step 5: Normalize prices
            print("💰 Step 5: Normalizing prices...")
            all_offers = self.normalize_offer_prices(all_offers)
            print(f"   ✓ {len(all_offers)} offers with valid prices")

            # Step 6: Normalize and deduplicate offers
            print("🧹 Step 6: Normalizing and deduplicating offers...")
            normalized_offers = self.deduplicator.normalize_offers(all_offers)
            deduplicated_offers = self.deduplicator.deduplicate_offers(
                normalized_offers
            )

            self.stats["offers_after_dedup"] = len(deduplicated_offers)
            print(f"   ✓ {len(deduplicated_offers)} offers after deduplication")

            # Calculate unique sellers
            unique_sellers = set(
                offer.get("seller_name_norm", "") for offer in deduplicated_offers
            )
            self.stats["unique_sellers"] = len(unique_sellers)
            print(f"   ✓ {len(unique_sellers)} unique sellers found")

            # Step 7: Export to Excel
            print("📊 Step 7: Exporting to Excel...")
            output_file = self.exporter.export_to_excel(deduplicated_offers)
            print(f"   ✓ Excel file created: {output_file}")

            # Final statistics
            self.stats["end_time"] = datetime.now()
            duration = self.stats["end_time"] - self.stats["start_time"]

            print("\n🎉 Pipeline completed successfully!")
            print("=" * 60)
            print("📈 Final Statistics:")
            print(f"   • Duration: {duration}")
            print(f"   • Parts processed: {self.stats['parts_processed']}")
            print(f"   • Total offers found: {self.stats['total_offers_found']}")
            print(f"   • After deduplication: {self.stats['offers_after_dedup']}")
            print(f"   • Unique sellers: {self.stats['unique_sellers']}")
            print(f"   • Output file: {output_file}")

            if self.stats["errors"]:
                print(f"   • Warnings/Errors: {len(self.stats['errors'])}")
                for error in self.stats["errors"][-5:]:  # Show last 5 errors
                    print(f"     - {error}")

            return True

        except Exception as e:
            error_msg = f"Critical error in pipeline: {e}"
            print(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return False

        finally:
            if not self.stats["end_time"]:
                self.stats["end_time"] = datetime.now()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get pipeline execution statistics.

        Returns:
            Dictionary with execution statistics
        """
        stats = self.stats.copy()

        if stats["start_time"] and stats["end_time"]:
            stats["duration_seconds"] = (
                stats["end_time"] - stats["start_time"]
            ).total_seconds()

        return stats


async def main():
    """Main entry point for testing the pipeline."""
    pipeline = ScrapingPipeline(
        input_file="parts_input.csv",
        output_file="torob_prices.xlsx",
        headless=True,  # Set to False for debugging
        delay_range=(1.5, 3.0),
    )

    success = await pipeline.run_pipeline()

    if success:
        print("\n✅ Pipeline execution completed successfully!")
        stats = pipeline.get_statistics()
        print(f"Total execution time: {stats.get('duration_seconds', 0):.1f} seconds")
    else:
        print("\n❌ Pipeline execution failed!")
        stats = pipeline.get_statistics()
        if stats["errors"]:
            print("Errors encountered:")
            for error in stats["errors"]:
                print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
