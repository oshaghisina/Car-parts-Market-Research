"""
Relevance scoring and filtering module for Torob scraper.
Handles negative filtering and relevance scoring for search results.
"""

import re
from typing import Any, Dict, List, Tuple

from core.config_manager import get_config
from utils.text import clean_whitespace, normalize_digits


class RelevanceFilter:
    """
    Handles relevance scoring and filtering of search results.
    Filters out non-front body parts and scores relevance.
    """

    def __init__(self):
        self.config = get_config()
        # Negative categories to filter out
        self.negative_patterns = {
            "rear_lights": [
                r"چراغ عقب",
                r"چراغ پشت",
                r"tail light",
                r"taillight",
                r"rear light",
                r"چراغ ترمز",
                r"brake light",
                r"stop light",
            ],
            "fog_lights": [
                r"مه‌شکن",
                r"مه شکن",
                r"fog light",
                r"foglamp",
                r"چراغ مه",
                r"چراغ مه‌شکن",
                r"چراغ مه شکن",
            ],
            "drl_lights": [
                r"چراغ روز",
                r"چراغ روشنایی روز",
                r"daylight",
                r"drl",
                r"day running",
                r"چراغ روشنایی",
                r"led strip",
            ],
            "indicators": [
                r"راهنما",
                r"چراغ راهنما",
                r"indicator",
                r"turn signal",
                r"blinker",
                r"چراغ چشمک زن",
                r"چراغ هشدار",
            ],
            "side_mirrors": [
                r"آینه",
                r"آیینه",
                r"mirror",
                r"side mirror",
                r"wing mirror",
                r"آینه جانبی",
                r"آینه کناری",
            ],
            "interior_parts": [
                r"داخل",
                r"interior",
                r"کابین",
                r"cabin",
                r"صندلی",
                r"seat",
                r"داشبورد",
                r"dashboard",
                r"کنسول",
                r"console",
            ],
        }

        # Positive patterns for front body parts
        self.positive_patterns = {
            "front_bumper": [
                r"سپر جلو",
                r"بامپر جلو",
                r"front bumper",
                r"bumper front",
                r"سپر جلو",
                r"بامپر جلو",
            ],
            "headlamp": [
                r"چراغ جلو",
                r"headlight",
                r"headlamp",
                r"چراغ جلو",
                r"چراغ اصلی",
                r"main light",
            ],
            "front_fender": [
                r"گلگیر جلو",
                r"fender front",
                r"front fender",
                r"wing front",
                r"گلگیر جلو",
                r"فندر جلو",
            ],
            "hood": [r"کاپوت", r"hood", r"bonnet", r"کاپوت", r"سقف موتور"],
            "grille": [
                r"جلوپنجره",
                r"grille",
                r"گریل",
                r"جلو پنجره",
                r"radiator grille",
                r"جلوپنجره",
                r"شبکه جلو",
            ],
        }

        # Car model patterns for relevance
        self.car_models = {
            "tiggo8": [r"تیگو 8", r"tiggo 8", r"tiggo8", r"tigo 8"],
            "tiggo7": [r"تیگو 7", r"tiggo 7", r"tiggo7", r"tigo 7"],
            "tiggo5": [r"تیگو 5", r"tiggo 5", r"tiggo5", r"tigo 5"],
            "arrizo6": [r"آریزو 6", r"arrizo 6", r"arrizo6"],
            "arrizo5": [r"آریزو 5", r"arrizo 5", r"arrizo5"],
        }

        # Trim patterns
        self.trim_patterns = {
            "classic": [r"کلاسیک", r"classic"],
            "pro": [r"پرو", r"pro"],
            "pro_max": [r"پرو مکس", r"pro max", r"promax", r"پروماکس"],
            "eplus": [r"e\+", r"ای پلاس", r"eplus", r"e plus"],
        }

        # Side patterns
        self.side_patterns = {
            "left": [r"چپ", r"left", r"lh", r"l"],
            "right": [r"راست", r"right", r"rh", r"r"],
            "front": [r"جلو", r"front", r"f"],
        }

        # Technology patterns
        self.tech_patterns = {
            "led": [r"led", r"ال ای دی", r"ال‌ای‌دی"],
            "halogen": [r"halogen", r"هالوژن"],
            "matrix": [r"matrix", r"مکس", r"matrix"],
            "xenon": [r"xenon", r"زنون", r"کسنون"],
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for pattern matching."""
        if not text:
            return ""
        return normalize_digits(clean_whitespace(text.lower()))

    def _check_negative_patterns(self, text: str) -> List[str]:
        """
        Check if text matches any negative patterns.

        Args:
            text: Text to check

        Returns:
            List of matched negative categories
        """
        normalized_text = self._normalize_text(text)
        matched_categories = []

        for category, patterns in self.negative_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    matched_categories.append(category)
                    break

        return matched_categories

    def _check_positive_patterns(self, text: str) -> List[str]:
        """
        Check if text matches any positive patterns.

        Args:
            text: Text to check

        Returns:
            List of matched positive categories
        """
        normalized_text = self._normalize_text(text)
        matched_categories = []

        for category, patterns in self.positive_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    matched_categories.append(category)
                    break

        return matched_categories

    def _extract_part_attributes(self, text: str) -> Dict[str, str]:
        """
        Extract part attributes from text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with extracted attributes
        """
        normalized_text = self._normalize_text(text)
        attributes = {
            "car_model": "UNKNOWN",
            "part_type": "UNKNOWN",
            "side": "UNKNOWN",
            "trim": "UNKNOWN",
            "tech": "UNKNOWN",
        }

        # Extract car model
        for model, patterns in self.car_models.items():
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    attributes["car_model"] = model.upper()
                    break

        # Extract part type from positive patterns
        for part_type, patterns in self.positive_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    attributes["part_type"] = part_type.upper()
                    break

        # Extract side
        for side, patterns in self.side_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    attributes["side"] = side.upper()
                    break

        # Extract trim
        for trim, patterns in self.trim_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    attributes["trim"] = trim.upper()
                    break

        # Extract technology
        for tech, patterns in self.tech_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    attributes["tech"] = tech.upper()
                    break

        return attributes

    def _calculate_relevance_score(
        self, title: str, query: str, attributes: Dict[str, str]
    ) -> float:
        """
        Calculate relevance score for a search result.

        Args:
            title: Product title
            query: Search query
            attributes: Extracted attributes

        Returns:
            Relevance score between 0 and 1
        """
        score = 0.0
        normalized_title = self._normalize_text(title)
        normalized_query = self._normalize_text(query)

        # Base score for having a part type
        if attributes["part_type"] != "UNKNOWN":
            score += 0.3

        # Score for car model match
        if attributes["car_model"] != "UNKNOWN":
            score += 0.2

        # Score for side specification
        if attributes["side"] != "UNKNOWN":
            score += 0.1

        # Score for trim specification
        if attributes["trim"] != "UNKNOWN":
            score += 0.1

        # Score for technology specification
        if attributes["tech"] != "UNKNOWN":
            score += 0.1

        # Word overlap score
        title_words = set(normalized_title.split())
        query_words = set(normalized_query.split())

        if query_words:
            overlap = len(title_words.intersection(query_words))
            word_score = overlap / len(query_words)
            score += word_score * 0.2

        # Ensure score is between 0 and 1
        return min(score, 1.0)

    def filter_and_score_result(
        self, title: str, query: str
    ) -> Tuple[bool, float, Dict[str, str]]:
        """
        Filter and score a search result.

        Args:
            title: Product title
            query: Search query

        Returns:
            Tuple of (is_valid, relevance_score, attributes)
        """
        # Check for negative patterns first
        negative_matches = self._check_negative_patterns(title)
        if negative_matches:
            return False, 0.0, {}

        # Check for positive patterns
        positive_matches = self._check_positive_patterns(title)
        if not positive_matches:
            return False, 0.0, {}

        # Extract attributes
        attributes = self._extract_part_attributes(title)

        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(title, query, attributes)

        # Only accept if relevance score is above threshold
        min_relevance = 0.3
        is_valid = relevance_score >= min_relevance

        return is_valid, relevance_score, attributes

    def generate_part_key(self, attributes: Dict[str, str]) -> str:
        """
        Generate part key from attributes.

        Args:
            attributes: Extracted attributes

        Returns:
            Part key in format: BODY:<PART_TYPE>:<SIDE>:<TECH>:<TRIM>
        """
        part_type = attributes.get("part_type", "UNKNOWN")
        side = attributes.get("side", "UNKNOWN")
        tech = attributes.get("tech", "UNKNOWN")
        trim = attributes.get("trim", "UNKNOWN")

        return f"BODY:{part_type}:{side}:{tech}:{trim}"

    def filter_search_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """
        Filter and score a list of search results.

        Args:
            results: List of search result dictionaries
            query: Search query

        Returns:
            List of filtered and scored results
        """
        filtered_results = []

        for result in results:
            title = result.get("title_raw", "")

            is_valid, relevance_score, attributes = self.filter_and_score_result(
                title, query
            )

            if is_valid:
                # Add relevance and attributes to result
                result["relevance"] = relevance_score
                result["attributes"] = attributes
                result["part_key"] = self.generate_part_key(attributes)

                # Generate normalized part name
                part_name_parts = []
                if attributes["car_model"] != "UNKNOWN":
                    part_name_parts.append(attributes["car_model"].title())
                if attributes["part_type"] != "UNKNOWN":
                    part_name_parts.append(attributes["part_type"].title())
                if attributes["side"] != "UNKNOWN":
                    part_name_parts.append(attributes["side"].upper())
                if attributes["trim"] != "UNKNOWN":
                    part_name_parts.append(attributes["trim"].title())
                if attributes["tech"] != "UNKNOWN":
                    part_name_parts.append(attributes["tech"].upper())

                result["part_name_norm"] = (
                    " ".join(part_name_parts) if part_name_parts else title
                )

                filtered_results.append(result)

        # Sort by relevance score (highest first)
        filtered_results.sort(key=lambda x: x["relevance"], reverse=True)

        return filtered_results


def test_filtering():
    """Test the relevance filter with sample data."""
    filter_obj = RelevanceFilter()

    test_cases = [
        ("چراغ جلو راست تیگو 8 پرو", "چراغ جلو راست تیگو 8"),
        ("چراغ عقب تیگو 8", "چراغ جلو تیگو 8"),  # Should be filtered out
        ("سپر جلو تیگو 8 کلاسیک", "سپر جلو تیگو 8"),
        ("مه‌شکن تیگو 8", "چراغ جلو تیگو 8"),  # Should be filtered out
        ("گلگیر جلو چپ تیگو 8 پرو مکس", "گلگیر جلو تیگو 8"),
        ("راهنما تیگو 8", "چراغ جلو تیگو 8"),  # Should be filtered out
    ]

    print("Testing RelevanceFilter:")
    print("=" * 60)

    for title, query in test_cases:
        is_valid, score, attributes = filter_obj.filter_and_score_result(title, query)
        part_key = filter_obj.generate_part_key(attributes) if is_valid else "FILTERED"

        print(f"Title: {title}")
        print(f"Query: {query}")
        print(f"Valid: {is_valid}")
        print(f"Score: {score:.2f}")
        print(f"Attributes: {attributes}")
        print(f"Part Key: {part_key}")
        print("-" * 40)


if __name__ == "__main__":
    test_filtering()
