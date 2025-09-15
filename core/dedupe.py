"""
Deduplication and seller normalization module.
Handles offer deduplication and seller name standardization.
"""

import hashlib
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

from utils.text import normalize_seller_name, normalize_part_title, clean_whitespace


class OfferDeduplicator:
    """
    Handles deduplication of offers and seller normalization.
    """

    def __init__(self):
        self.seller_mappings = {}  # Maps variations to canonical seller names
        self.seen_offers = set()  # Tracks unique offer signatures

    def _normalize_seller(self, seller_name: str) -> str:
        """
        Normalize seller name and apply mappings.

        Args:
            seller_name: Raw seller name

        Returns:
            Normalized seller name
        """
        if not seller_name:
            return "UNKNOWN_SELLER"

        # Basic normalization
        normalized = normalize_seller_name(seller_name)

        # Apply known mappings
        if normalized in self.seller_mappings:
            return self.seller_mappings[normalized]

        return normalized

    def _create_offer_signature(self, offer: Dict[str, Any]) -> str:
        """
        Create a unique signature for an offer to detect duplicates.

        Args:
            offer: Offer dictionary

        Returns:
            Unique signature string
        """
        # Components for signature
        seller_norm = self._normalize_seller(offer.get("seller_name", ""))
        title_norm = normalize_part_title(offer.get("title_raw", ""))
        price = offer.get("price_raw", 0) or 0
        part_id = offer.get("part_id", 0)

        # Create signature from key components
        signature_data = f"{part_id}:{seller_norm}:{title_norm}:{price}"
        signature = hashlib.md5(signature_data.encode()).hexdigest()

        return signature

    def _is_similar_offer(self, offer1: Dict[str, Any], offer2: Dict[str, Any]) -> bool:
        """
        Check if two offers are similar enough to be considered duplicates.

        Args:
            offer1: First offer
            offer2: Second offer

        Returns:
            True if offers are similar
        """
        # Must be for the same part
        if offer1.get("part_id") != offer2.get("part_id"):
            return False

        # Normalize seller names
        seller1 = self._normalize_seller(offer1.get("seller_name", ""))
        seller2 = self._normalize_seller(offer2.get("seller_name", ""))

        # Same seller check
        if seller1 != seller2:
            return False

        # Normalize titles for comparison
        title1 = normalize_part_title(offer1.get("title_raw", ""))
        title2 = normalize_part_title(offer2.get("title_raw", ""))

        # Check title similarity (simple approach)
        if len(title1) > 0 and len(title2) > 0:
            # Calculate basic similarity
            shorter = min(len(title1), len(title2))
            longer = max(len(title1), len(title2))

            if shorter / longer < 0.7:  # Titles too different in length
                return False

            # Check word overlap
            words1 = set(title1.split())
            words2 = set(title2.split())

            if len(words1) > 0 and len(words2) > 0:
                overlap = len(words1.intersection(words2))
                union = len(words1.union(words2))
                similarity = overlap / union

                if similarity < 0.6:  # Not enough word overlap
                    return False

        # Check price similarity (within 5% or exact match)
        price1 = offer1.get("price_raw", 0) or 0
        price2 = offer2.get("price_raw", 0) or 0

        if price1 > 0 and price2 > 0:
            price_diff = abs(price1 - price2) / max(price1, price2)
            if price_diff > 0.05:  # More than 5% difference
                return False

        return True

    def add_seller_mapping(self, variations: List[str], canonical_name: str):
        """
        Add seller name mappings for normalization.

        Args:
            variations: List of seller name variations
            canonical_name: The canonical/preferred seller name
        """
        canonical_norm = normalize_seller_name(canonical_name)

        for variation in variations:
            variation_norm = normalize_seller_name(variation)
            self.seller_mappings[variation_norm] = canonical_norm

    def deduplicate_offers(self, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate offers from the list.

        Args:
            offers: List of offer dictionaries

        Returns:
            List of deduplicated offers
        """
        if not offers:
            return []

        print(f"Deduplicating {len(offers)} offers...")

        deduplicated = []
        offer_signatures = {}  # signature -> offer mapping

        for offer in offers:
            # Create signature
            signature = self._create_offer_signature(offer)

            # Check if we've seen this exact signature
            if signature in offer_signatures:
                existing_offer = offer_signatures[signature]

                # Keep the offer with more complete information
                current_score = self._score_offer_completeness(offer)
                existing_score = self._score_offer_completeness(existing_offer)

                if current_score > existing_score:
                    # Replace with current offer
                    offer_signatures[signature] = offer
                    # Remove old offer from deduplicated list
                    deduplicated = [
                        o
                        for o in deduplicated
                        if self._create_offer_signature(o) != signature
                    ]
                    deduplicated.append(offer)
                # If existing is better or equal, skip current offer

            else:
                # Check for similar offers (more complex deduplication)
                is_duplicate = False

                for existing_offer in list(offer_signatures.values()):
                    if self._is_similar_offer(offer, existing_offer):
                        # Found a similar offer
                        current_score = self._score_offer_completeness(offer)
                        existing_score = self._score_offer_completeness(existing_offer)

                        if current_score > existing_score:
                            # Replace existing with current
                            old_signature = self._create_offer_signature(existing_offer)
                            del offer_signatures[old_signature]
                            offer_signatures[signature] = offer

                            # Update deduplicated list
                            deduplicated = [
                                o
                                for o in deduplicated
                                if not self._is_similar_offer(o, existing_offer)
                            ]
                            deduplicated.append(offer)

                        is_duplicate = True
                        break

                if not is_duplicate:
                    # New unique offer
                    offer_signatures[signature] = offer
                    deduplicated.append(offer)

        print(f"After deduplication: {len(deduplicated)} offers")
        return deduplicated

    def _score_offer_completeness(self, offer: Dict[str, Any]) -> int:
        """
        Score an offer based on completeness of information.

        Args:
            offer: Offer dictionary

        Returns:
            Completeness score (higher = more complete)
        """
        score = 0

        # Basic required fields
        if offer.get("title_raw"):
            score += 2
        if offer.get("price_raw"):
            score += 3
        if offer.get("seller_name"):
            score += 2

        # Additional useful fields
        if offer.get("product_url"):
            score += 1
        if offer.get("seller_url"):
            score += 1
        if offer.get("availability"):
            score += 1
        if offer.get("currency_unit") and offer.get("currency_unit") != "unknown":
            score += 1

        return score

    def normalize_offers(self, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize seller names and other fields in offers.

        Args:
            offers: List of offer dictionaries

        Returns:
            List of offers with normalized fields
        """
        normalized_offers = []

        for offer in offers:
            normalized_offer = offer.copy()

            # Normalize seller name
            normalized_offer["seller_name_norm"] = self._normalize_seller(
                offer.get("seller_name", "")
            )

            # Normalize part title
            normalized_offer["title_norm"] = normalize_part_title(
                offer.get("title_raw", "")
            )

            # Clean other text fields
            for field in ["title_raw", "availability"]:
                if field in normalized_offer and normalized_offer[field]:
                    normalized_offer[field] = clean_whitespace(normalized_offer[field])

            normalized_offers.append(normalized_offer)

        return normalized_offers

    def get_seller_statistics(
        self, offers: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate statistics for each seller.

        Args:
            offers: List of normalized offers

        Returns:
            Dictionary with seller statistics
        """
        seller_stats = defaultdict(
            lambda: {
                "offers_count": 0,
                "prices": [],
                "sample_urls": set(),
                "parts_offered": set(),
            }
        )

        for offer in offers:
            seller_norm = offer.get("seller_name_norm", "UNKNOWN_SELLER")

            seller_stats[seller_norm]["offers_count"] += 1

            if offer.get("price_raw"):
                seller_stats[seller_norm]["prices"].append(offer["price_raw"])

            if offer.get("product_url"):
                seller_stats[seller_norm]["sample_urls"].add(offer["product_url"])

            if offer.get("part_id"):
                seller_stats[seller_norm]["parts_offered"].add(offer["part_id"])

        # Calculate derived statistics
        final_stats = {}
        for seller, stats in seller_stats.items():
            prices = stats["prices"]
            final_stats[seller] = {
                "offers_count": stats["offers_count"],
                "avg_price_toman": sum(prices) // len(prices) if prices else 0,
                "min_price_toman": min(prices) if prices else 0,
                "max_price_toman": max(prices) if prices else 0,
                "sample_urls": ", ".join(
                    list(stats["sample_urls"])[:3]
                ),  # First 3 URLs
                "parts_count": len(stats["parts_offered"]),
            }

        return final_stats


def test_deduplicator():
    """Test the deduplicator with sample data."""
    deduplicator = OfferDeduplicator()

    # Sample offers with duplicates
    sample_offers = [
        {
            "part_id": 1,
            "title_raw": "چراغ جلو چپ تیگو 8 پرو مکس",
            "seller_name": "فروشگاه پارت سنتر",
            "price_raw": 1500000,
            "product_url": "https://torob.com/p/product1",
        },
        {
            "part_id": 1,
            "title_raw": "چراغ جلو چپ تیگو ۸ پرو مکس اصل",
            "seller_name": "پارت سنتر",  # Similar to above
            "price_raw": 1500000,
            "product_url": "https://torob.com/p/product1",
        },
        {
            "part_id": 1,
            "title_raw": "چراغ جلو چپ تیگو 8 پرو مکس",
            "seller_name": "یدک شاپ",
            "price_raw": 1450000,
            "product_url": "https://torob.com/p/product2",
        },
        {
            "part_id": 2,
            "title_raw": "سپر جلو تیگو 8",
            "seller_name": "فروشگاه پارت سنتر",
            "price_raw": 2500000,
            "product_url": "https://torob.com/p/product3",
        },
    ]

    print("Testing OfferDeduplicator:")
    print("=" * 60)

    print(f"Original offers: {len(sample_offers)}")

    # Add seller mappings
    deduplicator.add_seller_mapping(["فروشگاه پارت سنتر", "پارت سنتر"], "پارت سنتر")

    # Normalize
    normalized = deduplicator.normalize_offers(sample_offers)
    print(f"Normalized offers: {len(normalized)}")

    # Deduplicate
    deduplicated = deduplicator.deduplicate_offers(normalized)
    print(f"Deduplicated offers: {len(deduplicated)}")

    # Show results
    for i, offer in enumerate(deduplicated):
        print(f"\n{i+1}. Part {offer['part_id']}: {offer['title_raw']}")
        print(f"   Seller: {offer.get('seller_name_norm', 'N/A')}")
        print(f"   Price: {offer['price_raw']:,} Toman")

    # Seller statistics
    seller_stats = deduplicator.get_seller_statistics(deduplicated)
    print(f"\nSeller Statistics:")
    for seller, stats in seller_stats.items():
        print(
            f"  {seller}: {stats['offers_count']} offers, avg price: {stats['avg_price_toman']:,}"
        )


if __name__ == "__main__":
    test_deduplicator()
