"""
Two-stage Torob pipeline orchestrator.
Handles search page scraping, product page drill-down, and data processing.
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from adapters.torob_search import TorobScraper
from core.filtering import RelevanceFilter
from core.exporter_excel import ExcelExporter
from core.parallel_processor import get_parallel_processor
from core.progress_tracker import get_progress_tracker
from utils.text import (
    convert_rial_to_toman,
    detect_currency_unit,
    normalize_seller_name,
)


class TorobTwoStagePipeline:
    """
    Two-stage pipeline for Torob scraping with relevance filtering.
    """

    def __init__(
        self,
        input_data: List[Dict[str, Any]],
        output_file: str = "torob_prices.xlsx",
        max_cards_per_search: int = 200,
        headless: bool = True,
        delay_range: tuple = (1.5, 3.0),
    ):
        """
        Initialize the two-stage pipeline.

        Args:
            input_data: List of part dictionaries
            output_file: Output Excel file path
            max_cards_per_search: Maximum cards to process per search
            headless: Run browser in headless mode
            delay_range: Random delay range between requests
        """
        self.input_data = input_data
        self.output_file = output_file
        self.max_cards_per_search = max_cards_per_search
        self.headless = headless
        self.delay_range = delay_range

        # Initialize components
        self.filter = RelevanceFilter()
        self.exporter = ExcelExporter(output_file)
        self.parallel_processor = get_parallel_processor()
        self.progress_tracker = get_progress_tracker()

        # Statistics
        self.stats = {
            "start_time": None,
            "end_time": None,
            "parts_processed": 0,
            "search_results": 0,
            "product_pages": 0,
            "total_offers": 0,
            "filtered_offers": 0,
            "unique_sellers": 0,
            "avg_relevance": 0.0,
            "errors": [],
        }

    async def run_pipeline(self) -> bool:
        """
        Run the complete two-stage pipeline.

        Returns:
            True if successful, False otherwise
        """
        self.stats["start_time"] = datetime.now()

        try:
            print("🚀 Starting Two-Stage Torob Pipeline")
            print("=" * 60)

            # Start progress tracking
            total_tasks = len(self.input_data) * 2  # Search + drill down for each part
            self.progress_tracker.start(total_tasks, "Initializing pipeline...")

            all_offers = []

            async with TorobScraper(
                headless=self.headless, delay_range=self.delay_range
            ) as scraper:
                for i, part_data in enumerate(self.input_data):
                    part_name = part_data["part_name"]
                    print(
                        f"\n🔍 Processing part {i+1}/{len(self.input_data)}: {part_name}"
                    )

                    # Update progress for search stage
                    self.progress_tracker.update_task(
                        f"Searching for {part_name}", f"search_{i}"
                    )

                    # Stage A: Search page scraping
                    search_offers = await self._stage_a_search(scraper, part_data)
                    self.stats["search_results"] += len(search_offers)
                    self.progress_tracker.complete_task(f"search_{i}")

                    if not search_offers:
                        print(
                            f"   ⚠️  No search results found for {part_data['part_name']}"
                        )
                        continue

                    # Enhance search results with part metadata
                    enhanced_search_offers = []
                    for offer in search_offers:
                        enhanced_offer = offer.copy()
                        enhanced_offer.update(
                            {
                                "part_id": part_data["part_id"],
                                "part_name": part_data["part_name"],
                                "part_code": part_data["part_code"],
                                "query": part_data["keywords"],
                                "snapshot_ts": datetime.now().isoformat(),
                            }
                        )
                        enhanced_search_offers.append(enhanced_offer)

                    # Filter and score results
                    filtered_offers = self.filter.filter_search_results(
                        enhanced_search_offers, part_data["keywords"]
                    )
                    print(
                        f"   ✓ {len(filtered_offers)} relevant results after filtering"
                    )

                    if not filtered_offers:
                        print(
                            f"   ⚠️  No relevant results after filtering for {part_data['part_name']}"
                        )
                        continue

                    # Stage B: Product page drill-down
                    self.progress_tracker.update_task(
                        f"Drilling down for {part_name}", f"drill_{i}"
                    )
                    product_offers = await self._stage_b_drill_down(
                        scraper, filtered_offers, part_data
                    )
                    self.stats["product_pages"] += len(
                        [o for o in product_offers if o.get("drilled_down", False)]
                    )
                    self.progress_tracker.complete_task(f"drill_{i}")

                    all_offers.extend(product_offers)
                    self.stats["parts_processed"] += 1

                    print(
                        f"   ✓ {len(product_offers)} offers found for {part_data['part_name']}"
                    )

                    # Add delay between parts
                    if i < len(self.input_data) - 1:
                        await asyncio.sleep(2)

            self.stats["total_offers"] = len(all_offers)

            if not all_offers:
                print("❌ No offers found. Pipeline complete but no data to export.")
                return False

            # Process and clean offers
            print(f"\n🧹 Processing {len(all_offers)} offers...")
            self.progress_tracker.update_task("Processing offers", "process")
            processed_offers = self._process_offers(all_offers)
            self.progress_tracker.complete_task("process")

            # Calculate statistics
            self._calculate_statistics(processed_offers)

            # Export to Excel
            print(f"📊 Exporting to Excel...")
            self.progress_tracker.update_task("Exporting to Excel", "export")
            self.exporter.export_to_excel(processed_offers)
            self.progress_tracker.complete_task("export")

            self.stats["end_time"] = datetime.now()
            duration = self.stats["end_time"] - self.stats["start_time"]

            # Finish progress tracking
            self.progress_tracker.finish("Pipeline completed successfully!")

            print(f"\n🎉 Pipeline completed successfully!")
            print(f"⏱️  Duration: {duration}")

            return True

        except Exception as e:
            error_msg = f"Critical error in pipeline: {e}"
            print(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return False

        finally:
            if not self.stats["end_time"]:
                self.stats["end_time"] = datetime.now()

    async def _stage_a_search(
        self, scraper: TorobScraper, part_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Stage A: Search page scraping.

        Args:
            scraper: TorobScraper instance
            part_data: Part data dictionary

        Returns:
            List of search result offers
        """
        try:
            print(f"   🔍 Stage A: Searching for '{part_data['keywords']}'")

            # Search with limited cards
            search_results = await scraper.search_parts(
                part_data["keywords"], max_scroll_attempts=3  # Limit scroll attempts
            )

            # Limit to max_cards_per_search
            if len(search_results) > self.max_cards_per_search:
                search_results = search_results[: self.max_cards_per_search]
                print(f"   📊 Limited to {self.max_cards_per_search} results")

            return search_results

        except Exception as e:
            error_msg = f"Error in Stage A for {part_data['part_name']}: {e}"
            print(f"   ❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return []

    async def _stage_b_drill_down(
        self,
        scraper: TorobScraper,
        filtered_offers: List[Dict[str, Any]],
        part_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Stage B: Product page drill-down.

        Args:
            scraper: TorobScraper instance
            filtered_offers: Filtered search results
            part_data: Part data dictionary

        Returns:
            List of offers with product page data
        """
        print(f"   🔍 Stage B: Drilling down to product pages")

        all_offers = []

        # Process top relevant offers (limit to avoid too many requests)
        max_drill_down = min(20, len(filtered_offers))
        top_offers = filtered_offers[:max_drill_down]

        for i, offer in enumerate(top_offers):
            try:
                if not offer.get("product_url"):
                    # Use card data if no product URL
                    enhanced_offer = offer.copy()
                    enhanced_offer.update(
                        {
                            "part_id": part_data["part_id"],
                            "part_name": part_data["part_name"],
                            "part_code": part_data["part_code"],
                            "query": part_data["keywords"],
                            "drilled_down": False,
                            "seller_url": offer.get(
                                "seller_url", ""
                            ),  # Preserve seller URL if available
                        }
                    )
                    all_offers.append(enhanced_offer)
                    continue

                print(
                    f"     📄 Drilling down {i+1}/{max_drill_down}: {offer['title_raw'][:50]}..."
                )

                # Get product page details
                product_details = await scraper.get_product_details(
                    offer["product_url"]
                )

                if product_details and product_details.get("offers"):
                    # Use product page offers
                    for product_offer in product_details["offers"]:
                        enhanced_offer = {
                            "part_id": part_data["part_id"],
                            "part_name": part_data["part_name"],
                            "part_code": part_data["part_code"],
                            "query": part_data["keywords"],
                            "title_raw": offer["title_raw"],
                            "seller_name_norm": normalize_seller_name(
                                product_offer.get("seller_name", "")
                            ),
                            "price_raw": product_offer.get("price_raw"),
                            "price_text": product_offer.get("price_text", ""),
                            "currency_unit": product_offer.get(
                                "currency_unit", "unknown"
                            ),
                            "product_url": offer["product_url"],
                            "seller_url": product_offer.get("seller_url", ""),
                            "availability": product_offer.get("availability", ""),
                            "relevance": offer.get("relevance", 0.0),
                            "part_key": offer.get("part_key", ""),
                            "part_name_norm": offer.get("part_name_norm", ""),
                            "drilled_down": True,
                            "snapshot_ts": datetime.now().isoformat(),
                        }
                        all_offers.append(enhanced_offer)
                else:
                    # Use card data if product page failed
                    enhanced_offer = offer.copy()
                    enhanced_offer.update(
                        {
                            "part_id": part_data["part_id"],
                            "part_name": part_data["part_name"],
                            "part_code": part_data["part_code"],
                            "query": part_data["keywords"],
                            "drilled_down": False,
                            "seller_url": offer.get(
                                "seller_url", ""
                            ),  # Preserve seller URL if available
                        }
                    )
                    all_offers.append(enhanced_offer)

                # Add delay between product page requests
                await asyncio.sleep(1.0)

            except Exception as e:
                error_msg = f"Error drilling down offer {i+1}: {e}"
                print(f"     ❌ {error_msg}")
                self.stats["errors"].append(error_msg)
                continue

        return all_offers

    def _process_offers(self, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and clean offers.

        Args:
            offers: List of offer dictionaries

        Returns:
            List of processed offers
        """
        processed_offers = []

        for offer in offers:
            try:
                # Normalize prices
                price_raw = offer.get("price_raw", 0) or 0
                currency_unit = offer.get("currency_unit", "unknown")

                # Convert Rial to Toman if needed
                if currency_unit == "rial" and price_raw > 0:
                    price_toman = convert_rial_to_toman(price_raw)
                    offer["price_toman"] = price_toman
                    offer["price_rial"] = price_raw
                else:
                    offer["price_toman"] = price_raw
                    offer["price_rial"] = price_raw * 10 if price_raw > 0 else 0

                # Mark missing prices
                offer["price_missing"] = 1 if price_raw <= 0 else 0

                processed_offers.append(offer)

            except Exception as e:
                error_msg = f"Error processing offer: {e}"
                self.stats["errors"].append(error_msg)
                continue

        return processed_offers

    def _calculate_statistics(self, offers: List[Dict[str, Any]]):
        """Calculate pipeline statistics."""
        if not offers:
            return

        # Count unique sellers
        unique_sellers = set(offer.get("seller_name_norm", "") for offer in offers)
        self.stats["unique_sellers"] = len(unique_sellers)

        # Calculate average relevance
        relevance_scores = [
            offer.get("relevance", 0.0) for offer in offers if offer.get("relevance")
        ]
        if relevance_scores:
            self.stats["avg_relevance"] = sum(relevance_scores) / len(relevance_scores)

        # Count filtered offers (those with relevance > 0)
        filtered_count = len([o for o in offers if o.get("relevance", 0) > 0])
        self.stats["filtered_offers"] = filtered_count

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


async def test_pipeline():
    """Test the two-stage pipeline with sample data."""
    input_data = [
        {
            "part_id": 1,
            "part_name": "چراغ جلو راست تیگو 8 پرو",
            "part_code": "T8-HL-R-P",
            "keywords": "چراغ جلو راست تیگو 8 پرو headlight right tiggo",
        }
    ]

    pipeline = TorobTwoStagePipeline(
        input_data=input_data,
        output_file="test_torob_prices.xlsx",
        max_cards_per_search=50,
        headless=True,
    )

    success = await pipeline.run_pipeline()

    if success:
        print("✅ Test pipeline completed successfully!")
        stats = pipeline.get_statistics()
        print(f"Statistics: {stats}")
    else:
        print("❌ Test pipeline failed!")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
