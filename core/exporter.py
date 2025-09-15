"""
Excel exporter module for generating structured reports.
Creates multi-sheet Excel files with offers, seller summaries, and part analytics.
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from statistics import median, stdev
import numpy as np

from utils.text import convert_toman_to_rial, format_price


class ExcelExporter:
    """
    Handles Excel export with multiple sheets and formatting.
    """

    def __init__(self, output_file: str = "torob_prices.xlsx"):
        """
        Initialize Excel exporter.

        Args:
            output_file: Output Excel file path
        """
        self.output_file = output_file
        self.writer = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.writer:
            self.writer.close()

    def _prepare_offers_data(self, offers: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare offers data for the raw offers sheet.

        Args:
            offers: List of offer dictionaries

        Returns:
            DataFrame with offers data
        """
        if not offers:
            return pd.DataFrame()

        # Prepare data rows
        rows = []

        for offer in offers:
            # Calculate prices in both Toman and Rial
            price_toman = offer.get("price_raw", 0) or 0

            # Detect if price is in Rial and convert to Toman
            currency_unit = offer.get("currency_unit", "unknown")
            if currency_unit == "rial" and price_toman > 0:
                price_toman = price_toman // 10

            price_rial = convert_toman_to_rial(price_toman)

            row = {
                "part_id": offer.get("part_id", ""),
                "part_name": offer.get("part_name", ""),
                "part_code": offer.get("part_code", ""),
                "part_key": offer.get("part_key", ""),
                "part_name_norm": offer.get("part_name_norm", ""),
                "title_raw": offer.get("title_raw", ""),
                "seller_name_norm": offer.get("seller_name_norm", ""),
                "price_toman": price_toman,
                "price_rial": price_rial,
                "product_url": offer.get("product_url", ""),
                "seller_url": offer.get("seller_url", ""),
                "availability": offer.get("availability", ""),
                "snapshot_ts": offer.get("snapshot_ts", datetime.now().isoformat()),
            }

            rows.append(row)

        df = pd.DataFrame(rows)

        # Sort by part_id and price
        df = df.sort_values(["part_id", "price_toman"])

        return df

    def _prepare_sellers_summary(self, offers: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare seller summary data.

        Args:
            offers: List of offer dictionaries

        Returns:
            DataFrame with seller summary
        """
        if not offers:
            return pd.DataFrame()

        # Group by seller
        seller_groups = {}

        for offer in offers:
            seller_norm = offer.get("seller_name_norm", "UNKNOWN_SELLER")

            if seller_norm not in seller_groups:
                seller_groups[seller_norm] = {"offers": [], "prices": [], "urls": set()}

            seller_groups[seller_norm]["offers"].append(offer)

            # Add price if valid
            price_toman = offer.get("price_raw", 0) or 0
            currency_unit = offer.get("currency_unit", "unknown")
            if currency_unit == "rial" and price_toman > 0:
                price_toman = price_toman // 10

            if price_toman > 0:
                seller_groups[seller_norm]["prices"].append(price_toman)

            # Add URL if available
            if offer.get("product_url"):
                seller_groups[seller_norm]["urls"].add(offer["product_url"])

        # Build summary rows
        rows = []

        for seller_norm, data in seller_groups.items():
            prices = data["prices"]

            row = {
                "seller_name_norm": seller_norm,
                "offers_count": len(data["offers"]),
                "avg_price_toman": int(np.mean(prices)) if prices else 0,
                "min_price_toman": int(np.min(prices)) if prices else 0,
                "max_price_toman": int(np.max(prices)) if prices else 0,
                "sample_urls": "\n".join(list(data["urls"])[:3]),  # First 3 URLs
            }

            rows.append(row)

        df = pd.DataFrame(rows)

        # Sort by offers count (most active sellers first)
        df = df.sort_values("offers_count", ascending=False)

        return df

    def _prepare_parts_summary(self, offers: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare parts summary with analytics.

        Args:
            offers: List of offer dictionaries

        Returns:
            DataFrame with parts summary
        """
        if not offers:
            return pd.DataFrame()

        # Group by part
        part_groups = {}

        for offer in offers:
            part_key = offer.get("part_key", "UNKNOWN")
            part_id = offer.get("part_id", 0)

            if part_id not in part_groups:
                part_groups[part_id] = {
                    "part_key": part_key,
                    "part_name_norm": offer.get("part_name_norm", ""),
                    "offers": [],
                    "prices": [],
                    "sellers": set(),
                    "urls": set(),
                }

            part_groups[part_id]["offers"].append(offer)

            # Add price if valid
            price_toman = offer.get("price_raw", 0) or 0
            currency_unit = offer.get("currency_unit", "unknown")
            if currency_unit == "rial" and price_toman > 0:
                price_toman = price_toman // 10

            if price_toman > 0:
                part_groups[part_id]["prices"].append(price_toman)

            # Add seller
            seller_norm = offer.get("seller_name_norm", "UNKNOWN_SELLER")
            part_groups[part_id]["sellers"].add(seller_norm)

            # Add URL
            if offer.get("product_url"):
                part_groups[part_id]["urls"].add(offer["product_url"])

        # Build summary rows
        rows = []

        for part_id, data in part_groups.items():
            prices = data["prices"]

            if prices:
                amp_toman = int(np.mean(prices))  # Average Market Price
                median_price = int(median(prices))
                min_price = int(np.min(prices))
                max_price = int(np.max(prices))

                # Calculate outlier threshold (2 standard deviations)
                if len(prices) > 2:
                    std_dev = stdev(prices)
                    outlier_threshold = 2 * std_dev
                else:
                    outlier_threshold = 0
            else:
                amp_toman = 0
                median_price = 0
                min_price = 0
                max_price = 0
                outlier_threshold = 0

            row = {
                "part_key": data["part_key"],
                "part_name_norm": data["part_name_norm"],
                "offers_count": len(data["offers"]),
                "seller_count": len(data["sellers"]),
                "AMP_toman": amp_toman,
                "median_price_toman": median_price,
                "min_price_toman": min_price,
                "max_price_toman": max_price,
                "price_std_dev": (
                    int(outlier_threshold / 2) if outlier_threshold > 0 else 0
                ),
                "sample_urls": "\n".join(list(data["urls"])[:3]),  # First 3 URLs
            }

            rows.append(row)

        df = pd.DataFrame(rows)

        # Sort by AMP (most expensive parts first)
        df = df.sort_values("AMP_toman", ascending=False)

        return df

    def _apply_formatting(self, workbook, worksheet, sheet_name: str):
        """
        Apply formatting to Excel worksheet.

        Args:
            workbook: xlsxwriter workbook
            worksheet: xlsxwriter worksheet
            sheet_name: Name of the sheet
        """
        # Define formats
        header_format = workbook.add_format(
            {"bold": True, "font_color": "white", "bg_color": "#366092", "border": 1}
        )

        currency_format = workbook.add_format({"num_format": "#,##0", "border": 1})

        url_format = workbook.add_format(
            {"font_color": "blue", "underline": 1, "border": 1}
        )

        outlier_format = workbook.add_format({"bg_color": "#ffcccc", "border": 1})

        # Format headers
        for col_num, value in enumerate(worksheet.table.columns):
            worksheet.write(0, col_num, value.header, header_format)

        # Apply specific formatting based on sheet
        if sheet_name == "offers_raw":
            # Format price columns
            price_cols = ["price_toman", "price_rial"]
            for col_name in price_cols:
                if col_name in [col.header for col in worksheet.table.columns]:
                    col_idx = [col.header for col in worksheet.table.columns].index(
                        col_name
                    )
                    worksheet.set_column(col_idx, col_idx, 12, currency_format)

            # Format URL columns
            url_cols = ["product_url", "seller_url"]
            for col_name in url_cols:
                if col_name in [col.header for col in worksheet.table.columns]:
                    col_idx = [col.header for col in worksheet.table.columns].index(
                        col_name
                    )
                    worksheet.set_column(col_idx, col_idx, 40, url_format)

        elif sheet_name == "part_summary":
            # Format price columns
            price_cols = [
                "AMP_toman",
                "median_price_toman",
                "min_price_toman",
                "max_price_toman",
            ]
            for col_name in price_cols:
                if col_name in [col.header for col in worksheet.table.columns]:
                    col_idx = [col.header for col in worksheet.table.columns].index(
                        col_name
                    )
                    worksheet.set_column(col_idx, col_idx, 15, currency_format)

    def export_to_excel(self, offers: List[Dict[str, Any]]) -> str:
        """
        Export offers data to Excel with multiple sheets.

        Args:
            offers: List of offer dictionaries

        Returns:
            Path to the created Excel file
        """
        print(f"Exporting {len(offers)} offers to Excel: {self.output_file}")

        # Prepare data for each sheet
        offers_df = self._prepare_offers_data(offers)
        sellers_df = self._prepare_sellers_summary(offers)
        parts_df = self._prepare_parts_summary(offers)

        # Create Excel file with multiple sheets
        with pd.ExcelWriter(self.output_file, engine="xlsxwriter") as writer:
            # Write sheets
            if not offers_df.empty:
                offers_df.to_excel(writer, sheet_name="offers_raw", index=False)

            if not sellers_df.empty:
                sellers_df.to_excel(writer, sheet_name="sellers_summary", index=False)

            if not parts_df.empty:
                parts_df.to_excel(writer, sheet_name="part_summary", index=False)

            # Get workbook and worksheets for formatting
            workbook = writer.book

            # Apply formatting to each sheet
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]

                # Auto-adjust column widths
                if sheet_name == "offers_raw" and not offers_df.empty:
                    for i, col in enumerate(offers_df.columns):
                        max_len = max(
                            offers_df[col].astype(str).str.len().max(), len(str(col))
                        )
                        worksheet.set_column(i, i, min(max_len + 2, 50))

                elif sheet_name == "sellers_summary" and not sellers_df.empty:
                    for i, col in enumerate(sellers_df.columns):
                        max_len = max(
                            sellers_df[col].astype(str).str.len().max(), len(str(col))
                        )
                        worksheet.set_column(i, i, min(max_len + 2, 40))

                elif sheet_name == "part_summary" and not parts_df.empty:
                    for i, col in enumerate(parts_df.columns):
                        max_len = max(
                            parts_df[col].astype(str).str.len().max(), len(str(col))
                        )
                        worksheet.set_column(i, i, min(max_len + 2, 30))

                # Format headers
                header_format = workbook.add_format(
                    {
                        "bold": True,
                        "font_color": "white",
                        "bg_color": "#366092",
                        "border": 1,
                    }
                )

                # Apply header format
                if sheet_name == "offers_raw" and not offers_df.empty:
                    for col_num, value in enumerate(offers_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                elif sheet_name == "sellers_summary" and not sellers_df.empty:
                    for col_num, value in enumerate(sellers_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                elif sheet_name == "part_summary" and not parts_df.empty:
                    for col_num, value in enumerate(parts_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)

                # Freeze header row
                worksheet.freeze_panes(1, 0)

        print(f"Excel file created successfully: {self.output_file}")

        # Print summary statistics
        print(f"\nExport Summary:")
        print(f"- Raw offers: {len(offers_df)} rows")
        print(f"- Unique sellers: {len(sellers_df)} sellers")
        print(f"- Unique parts: {len(parts_df)} parts")

        return self.output_file


def test_exporter():
    """Test the Excel exporter with sample data."""

    # Sample offers data
    sample_offers = [
        {
            "part_id": 1,
            "part_name": "چراغ جلو چپ تیگو 8 پرو مکس",
            "part_code": "T8-HL-L-PM",
            "part_key": "BODY:HEADLAMP:LEFT:PRO_MAX",
            "part_name_norm": "Tiggo8 Headlamp Left Pro_Max",
            "title_raw": "چراغ جلو چپ تیگو 8 پرو مکس اصل",
            "seller_name_norm": "پارت سنتر",
            "price_raw": 1500000,
            "currency_unit": "toman",
            "product_url": "https://torob.com/p/product1",
            "availability": "موجود",
            "snapshot_ts": datetime.now().isoformat(),
        },
        {
            "part_id": 1,
            "part_name": "چراغ جلو چپ تیگو 8 پرو مکس",
            "part_code": "T8-HL-L-PM",
            "part_key": "BODY:HEADLAMP:LEFT:PRO_MAX",
            "part_name_norm": "Tiggo8 Headlamp Left Pro_Max",
            "title_raw": "چراغ جلو چپ تیگو 8 پرو مکس",
            "seller_name_norm": "یدک شاپ",
            "price_raw": 1450000,
            "currency_unit": "toman",
            "product_url": "https://torob.com/p/product2",
            "availability": "موجود",
            "snapshot_ts": datetime.now().isoformat(),
        },
        {
            "part_id": 2,
            "part_name": "سپر جلو تیگو 8 کلاسیک",
            "part_code": "T8-FB-CL",
            "part_key": "BODY:BUMPER:FRONT:CLASSIC",
            "part_name_norm": "Tiggo8 Bumper Front Classic",
            "title_raw": "سپر جلو تیگو 8 کلاسیک",
            "seller_name_norm": "پارت سنتر",
            "price_raw": 2500000,
            "currency_unit": "toman",
            "product_url": "https://torob.com/p/product3",
            "availability": "موجود",
            "snapshot_ts": datetime.now().isoformat(),
        },
    ]

    print("Testing Excel Exporter:")
    print("=" * 60)

    exporter = ExcelExporter("test_output.xlsx")
    output_file = exporter.export_to_excel(sample_offers)

    print(f"Test complete. Output file: {output_file}")


if __name__ == "__main__":
    test_exporter()
