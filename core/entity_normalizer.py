"""
Entity normalizer for automotive parts classification and standardization.
Generates normalized keys: BODY:<PART_TYPE>:<SIDE/VARIANT>:<TRIM>
"""

import re
from typing import Dict, Optional, Tuple

from utils.text import clean_whitespace, normalize_digits


class PartNormalizer:
    """
    Normalizes automotive part names and generates standardized keys.
    """

    def __init__(self):
        self.part_types = {
            "bumper": ["سپر", "bumper", "بامپر"],
            "headlamp": ["چراغ", "چراغ جلو", "headlight", "headlamp", "lamp"],
            "fender": ["گلگیر", "fender", "wing"],
            "hood": ["کاپوت", "hood", "bonnet"],
            "grille": ["جلوپنجره", "grille", "گریل", "جلو پنجره"],
            "mirror": ["آینه", "mirror", "آیینه"],
            "door": ["درب", "door", "در"],
            "taillight": ["چراغ عقب", "taillight", "tail light", "rear light"],
            "spoiler": ["اسپویلر", "spoiler", "بال عقب"],
            "running_board": ["رکاب", "running board", "side step"],
        }

        self.trims = {
            "classic": ["کلاسیک", "classic", "کلاسیک"],
            "pro": ["پرو", "pro"],
            "pro_max": ["پرو مکس", "pro max", "promax", "پروماکس"],
            "eplus": ["e+", "ای پلاس", "eplus", "e plus"],
        }

        self.sides = {
            "left": ["چپ", "left", "lh", "l"],
            "right": ["راست", "right", "rh", "r"],
            "front": ["جلو", "front", "f"],
            "rear": ["عقب", "rear", "back", "r"],
            "center": ["وسط", "center", "middle", "c"],
        }

        self.variants = {
            "led": ["led", "ال ای دی", "ال‌ای‌دی"],
            "halogen": ["halogen", "هالوژن", "هالوژن"],
            "matrix": ["matrix", "مکس", "matrix"],
            "xenon": ["xenon", "زنون", "کسنون"],
            "standard": ["استاندارد", "standard", "معمولی"],
            "oem": ["oem", "اصل", "اصلی", "اورجینال", "original"],
            "aftermarket": ["aftermarket", "am", "یدکی", "جایگزین"],
        }

        self.car_models = {
            "tiggo8": ["تیگو 8", "tiggo 8", "tiggo8", "tigo 8"],
            "tiggo7": ["تیگو 7", "tiggo 7", "tiggo7", "tigo 7"],
            "tiggo5": ["تیگو 5", "tiggo 5", "tiggo5", "tigo 5"],
            "arrizo6": ["آریزو 6", "arrizo 6", "arrizo6"],
            "arrizo5": ["آریزو 5", "arrizo 5", "arrizo5"],
        }

    def _extract_feature(self, text: str, feature_dict: Dict[str, list]) -> str:
        """
        Extract a feature (part type, trim, side, etc.) from text using dictionary matching.

        Args:
            text: Input text to search
            feature_dict: Dictionary mapping normalized keys to search terms

        Returns:
            Normalized feature key or "unknown"
        """
        text_lower = text.lower()
        text_normalized = normalize_digits(text_lower)

        for key, terms in feature_dict.items():
            for term in terms:
                term_normalized = normalize_digits(term.lower())
                if term_normalized in text_normalized:
                    return key.upper()

        return "UNKNOWN"

    def _extract_part_type(self, text: str) -> str:
        """Extract part type from text."""
        return self._extract_feature(text, self.part_types)

    def _extract_trim(self, text: str) -> str:
        """Extract trim level from text."""
        return self._extract_feature(text, self.trims)

    def _extract_side(self, text: str) -> str:
        """Extract side/position from text."""
        return self._extract_feature(text, self.sides)

    def _extract_variant(self, text: str) -> str:
        """Extract variant (LED, Halogen, etc.) from text."""
        return self._extract_feature(text, self.variants)

    def _extract_car_model(self, text: str) -> str:
        """Extract car model from text."""
        return self._extract_feature(text, self.car_models)

    def normalize_part_name(
        self, part_name: str, part_code: Optional[str] = None
    ) -> str:
        """
        Generate a normalized, human-readable part name.

        Args:
            part_name: Original part name
            part_code: Optional part code for additional context

        Returns:
            Normalized part name
        """
        if not part_name:
            return ""

        # Combine part name and code for analysis
        combined_text = part_name
        if part_code:
            combined_text += f" {part_code}"

        # Clean and normalize
        normalized = clean_whitespace(normalize_digits(combined_text))

        # Extract components
        car_model = self._extract_car_model(normalized)
        part_type = self._extract_part_type(normalized)
        trim = self._extract_trim(normalized)
        side = self._extract_side(normalized)
        variant = self._extract_variant(normalized)

        # Build normalized name
        parts = []

        if car_model != "UNKNOWN":
            parts.append(car_model.title())

        if part_type != "UNKNOWN":
            parts.append(part_type.title())

        if side != "UNKNOWN":
            parts.append(side.upper())

        if trim != "UNKNOWN":
            parts.append(trim.title())

        if variant != "UNKNOWN":
            parts.append(variant.upper())

        return " ".join(parts) if parts else normalized

    def generate_part_key(self, part_name: str, part_code: Optional[str] = None) -> str:
        """
        Generate a standardized part key in format: BODY:<PART_TYPE>:<SIDE/VARIANT>:<TRIM>

        Args:
            part_name: Original part name
            part_code: Optional part code for additional context

        Returns:
            Standardized part key
        """
        if not part_name:
            return "BODY:UNKNOWN:UNKNOWN:UNKNOWN"

        # Combine part name and code for analysis
        combined_text = part_name
        if part_code:
            combined_text += f" {part_code}"

        # Normalize text
        normalized = clean_whitespace(normalize_digits(combined_text.lower()))

        # Extract components
        part_type = self._extract_part_type(normalized)
        side = self._extract_side(normalized)
        variant = self._extract_variant(normalized)
        trim = self._extract_trim(normalized)

        # Build side/variant component
        side_variant_parts = []
        if side != "UNKNOWN":
            side_variant_parts.append(side)
        if variant != "UNKNOWN":
            side_variant_parts.append(variant)

        side_variant = ":".join(side_variant_parts) if side_variant_parts else "UNKNOWN"

        return f"BODY:{part_type}:{side_variant}:{trim}"

    def extract_metadata(
        self, part_name: str, part_code: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Extract all metadata components from part name.

        Args:
            part_name: Original part name
            part_code: Optional part code

        Returns:
            Dictionary with extracted metadata
        """
        if not part_name:
            return {
                "car_model": "UNKNOWN",
                "part_type": "UNKNOWN",
                "side": "UNKNOWN",
                "variant": "UNKNOWN",
                "trim": "UNKNOWN",
                "part_key": "BODY:UNKNOWN:UNKNOWN:UNKNOWN",
                "normalized_name": "",
            }

        # Combine part name and code for analysis
        combined_text = part_name
        if part_code:
            combined_text += f" {part_code}"

        # Normalize text
        normalized = clean_whitespace(normalize_digits(combined_text.lower()))

        # Extract all components
        car_model = self._extract_car_model(normalized)
        part_type = self._extract_part_type(normalized)
        side = self._extract_side(normalized)
        variant = self._extract_variant(normalized)
        trim = self._extract_trim(normalized)

        # Generate key and normalized name
        part_key = self.generate_part_key(part_name, part_code)
        normalized_name = self.normalize_part_name(part_name, part_code)

        return {
            "car_model": car_model,
            "part_type": part_type,
            "side": side,
            "variant": variant,
            "trim": trim,
            "part_key": part_key,
            "normalized_name": normalized_name,
        }

    def validate_extraction(
        self, part_name: str, part_code: Optional[str] = None
    ) -> Tuple[bool, list]:
        """
        Validate if extraction was successful and return any issues.

        Args:
            part_name: Original part name
            part_code: Optional part code

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        metadata = self.extract_metadata(part_name, part_code)
        issues = []

        if metadata["part_type"] == "UNKNOWN":
            issues.append("Could not identify part type")

        if metadata["car_model"] == "UNKNOWN":
            issues.append("Could not identify car model")

        if metadata["side"] == "UNKNOWN" and metadata["part_type"] in [
            "HEADLAMP",
            "FENDER",
            "MIRROR",
        ]:
            issues.append(
                "Could not identify side for part that typically has left/right variants"
            )

        if metadata["trim"] == "UNKNOWN":
            issues.append("Could not identify trim level")

        is_valid = len(issues) <= 2  # Allow up to 2 missing pieces of information

        return is_valid, issues


def test_normalizer():
    """Test the normalizer with sample data."""
    normalizer = PartNormalizer()

    test_cases = [
        ("چراغ جلو چپ تیگو 8 پرو مکس", "T8-HL-L-PM"),
        ("سپر جلو تیگو 8 کلاسیک", "T8-FB-CL"),
        ("گلگیر جلو راست تیگو 8 پرو", "T8-FF-R-PR"),
        ("کاپوت تیگو 8", "T8-HD"),
        ("جلوپنجره تیگو 8 پرو مکس", "T8-GR-PM"),
    ]

    print("Testing PartNormalizer:")
    print("=" * 60)

    for part_name, part_code in test_cases:
        print(f"Input: {part_name} ({part_code})")

        metadata = normalizer.extract_metadata(part_name, part_code)
        is_valid, issues = normalizer.validate_extraction(part_name, part_code)

        print(f"  Part Key: {metadata['part_key']}")
        print(f"  Normalized: {metadata['normalized_name']}")
        print(f"  Metadata: {metadata}")
        print(f"  Valid: {is_valid}")
        if issues:
            print(f"  Issues: {', '.join(issues)}")
        print("-" * 60)


if __name__ == "__main__":
    test_normalizer()
