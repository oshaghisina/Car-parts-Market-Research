"""
Enhanced Excel exporter with hyperlinks and conditional formatting.
Creates professional multi-sheet Excel files with advanced formatting.
"""

from datetime import datetime
from statistics import median, stdev
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from core.config_manager import get_config
from utils.text import convert_toman_to_rial, format_price


class ExcelExporter:
    """
    Enhanced Excel exporter with hyperlinks and conditional formatting.
    """

    def __init__(self, output_file: str = None):
        """
        Initialize Excel exporter.

        Args:
            output_file: Output Excel file path (overrides config)
        """
        self.config = get_config()
        self.output_file = output_file or self.config.get(
            "export.excel.filename_template", "torob_prices.xlsx"
        )

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
            # Prepare URLs for validation
            product_url = offer.get("product_url", "")
            seller_url = offer.get("seller_url", "")

            # Create validation URLs
            validation_urls = []
            if product_url:
                validation_urls.append(f"Product: {product_url}")
            if seller_url:
                validation_urls.append(f"Seller: {seller_url}")

            validation_url_text = (
                "\n".join(validation_urls) if validation_urls else "No URLs available"
            )

            row = {
                "part_id": offer.get("part_id", ""),
                "part_name": offer.get("part_name", ""),
                "part_code": offer.get("part_code", ""),
                "query": offer.get("query", ""),
                "part_key": offer.get("part_key", ""),
                "part_name_norm": offer.get("part_name_norm", ""),
                "title_raw": offer.get("title_raw", ""),
                "price_raw": offer.get("price_raw", 0),
                "price_text": offer.get("price_text", ""),
                "currency_unit": offer.get("currency_unit", ""),
                "seller_name": offer.get("seller_name", ""),
                "seller_name_norm": offer.get("seller_name_norm", ""),
                "price_toman": offer.get("price_toman", 0),
                "price_rial": offer.get("price_rial", 0),
                "product_url": product_url,
                "seller_url": seller_url,
                "validation_urls": validation_url_text,
                "relevance": offer.get("relevance", 0.0),
                "snapshot_ts": offer.get("snapshot_ts", datetime.now().isoformat()),
                "price_missing": offer.get("price_missing", 0),
                "drilled_down": offer.get("drilled_down", False),
            }

            rows.append(row)

        df = pd.DataFrame(rows)

        # Sort by relevance and price
        df = df.sort_values(["relevance", "price_toman"], ascending=[False, True])

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

            # Add price if valid (not missing)
            price_toman = offer.get("price_toman", 0) or 0
            price_missing = offer.get("price_missing", 0)

            if price_toman > 0 and not price_missing:
                seller_groups[seller_norm]["prices"].append(price_toman)

            # Add URL if available
            if offer.get("product_url"):
                seller_groups[seller_norm]["urls"].add(offer["product_url"])

        # Build summary rows
        rows = []

        for seller_norm, data in seller_groups.items():
            prices = data["prices"]

            # Prepare URLs for validation
            sample_urls = list(data["urls"])[:5]  # First 5 URLs for better validation
            validation_urls = [
                f"Product {i+1}: {url}" for i, url in enumerate(sample_urls)
            ]
            validation_url_text = (
                "\n".join(validation_urls) if validation_urls else "No URLs available"
            )

            row = {
                "seller_name_norm": seller_norm,
                "offers_count": len(data["offers"]),
                "avg_price_toman": int(np.mean(prices)) if prices else 0,
                "min_price_toman": int(np.min(prices)) if prices else 0,
                "max_price_toman": int(np.max(prices)) if prices else 0,
                "sample_urls": "\n".join(sample_urls),
                "validation_urls": validation_url_text,
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

            # Add price if valid (not missing)
            price_toman = offer.get("price_toman", 0) or 0
            price_missing = offer.get("price_missing", 0)

            if price_toman > 0 and not price_missing:
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

            # Prepare URLs for validation
            sample_urls = list(data["urls"])[:5]  # First 5 URLs for better validation
            validation_urls = [
                f"Offer {i+1}: {url}" for i, url in enumerate(sample_urls)
            ]
            validation_url_text = (
                "\n".join(validation_urls) if validation_urls else "No URLs available"
            )

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
                "sample_urls": "\n".join(sample_urls),
                "validation_urls": validation_url_text,
            }

            rows.append(row)

        df = pd.DataFrame(rows)

        # Sort by AMP (most expensive parts first)
        df = df.sort_values("AMP_toman", ascending=False)

        return df

    def _apply_conditional_formatting(self, workbook, worksheet, df, sheet_name: str):
        """
        Apply conditional formatting to Excel worksheet.

        Args:
            workbook: xlsxwriter workbook
            worksheet: xlsxwriter worksheet
            df: DataFrame being written
            sheet_name: Name of the sheet
        """
        if sheet_name == "part_summary" and not df.empty:
            # Define formats
            outlier_format = workbook.add_format({"bg_color": "#ffcccc", "border": 1})

            normal_format = workbook.add_format({"border": 1})

            # Get AMP column for outlier detection
            if "AMP_toman" in df.columns:
                amp_values = df["AMP_toman"].values
                valid_amps = amp_values[amp_values > 0]

                if len(valid_amps) > 2:
                    mean_amp = np.mean(valid_amps)
                    std_amp = np.std(valid_amps)
                    outlier_threshold = 2 * std_amp

                    # Apply conditional formatting to price columns
                    for col_idx, col_name in enumerate(df.columns):
                        if "price" in col_name.lower() and col_name != "price_std_dev":
                            for row_idx in range(1, len(df) + 1):  # Skip header
                                cell_value = df.iloc[row_idx - 1][col_name]
                                if (
                                    cell_value > 0
                                    and abs(cell_value - mean_amp) > outlier_threshold
                                ):
                                    worksheet.write(
                                        row_idx, col_idx, cell_value, outlier_format
                                    )
                                else:
                                    worksheet.write(
                                        row_idx, col_idx, cell_value, normal_format
                                    )

    def export_to_excel(self, offers: List[Dict[str, Any]]) -> str:
        """
        Export offers data to Excel with multiple sheets and advanced formatting.

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

            # Define formats
            header_format = workbook.add_format(
                {
                    "bold": True,
                    "font_color": "white",
                    "bg_color": "#366092",
                    "border": 1,
                    "align": "center",
                }
            )

            currency_format = workbook.add_format({"num_format": "#,##0", "border": 1})

            url_format = workbook.add_format(
                {"font_color": "blue", "underline": 1, "border": 1}
            )

            relevance_format = workbook.add_format({"num_format": "0.00", "border": 1})

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
                        # Special handling for URL columns
                        if col in ["sample_urls", "validation_urls"]:
                            worksheet.set_column(i, i, 60, url_format)
                        else:
                            worksheet.set_column(i, i, min(max_len + 2, 40))

                elif sheet_name == "part_summary" and not parts_df.empty:
                    for i, col in enumerate(parts_df.columns):
                        max_len = max(
                            parts_df[col].astype(str).str.len().max(), len(str(col))
                        )
                        # Special handling for URL columns
                        if col in ["sample_urls", "validation_urls"]:
                            worksheet.set_column(i, i, 60, url_format)
                        else:
                            worksheet.set_column(i, i, min(max_len + 2, 30))

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

                # Apply specific formatting
                if sheet_name == "offers_raw" and not offers_df.empty:
                    # Format price columns
                    for col_name in ["price_toman", "price_rial"]:
                        if col_name in offers_df.columns:
                            col_idx = list(offers_df.columns).index(col_name)
                            worksheet.set_column(col_idx, col_idx, 12, currency_format)

                    # Format URL columns with hyperlinks
                    for col_name in ["product_url", "seller_url"]:
                        if col_name in offers_df.columns:
                            col_idx = list(offers_df.columns).index(col_name)
                            worksheet.set_column(col_idx, col_idx, 50, url_format)

                            # Add hyperlinks for URLs
                            for row_idx in range(1, len(offers_df) + 1):
                                url_value = offers_df.iloc[row_idx - 1][col_name]
                                if url_value and str(url_value).startswith("http"):
                                    worksheet.write_url(
                                        row_idx,
                                        col_idx,
                                        url_value,
                                        url_format,
                                        string=str(url_value),
                                    )

                    # Format validation URLs column
                    if "validation_urls" in offers_df.columns:
                        col_idx = list(offers_df.columns).index("validation_urls")
                        worksheet.set_column(col_idx, col_idx, 60, url_format)

                    # Format relevance column
                    if "relevance" in offers_df.columns:
                        col_idx = list(offers_df.columns).index("relevance")
                        worksheet.set_column(col_idx, col_idx, 10, relevance_format)

                    # Format drilled_down column
                    if "drilled_down" in offers_df.columns:
                        col_idx = list(offers_df.columns).index("drilled_down")
                        worksheet.set_column(col_idx, col_idx, 12)

                elif sheet_name == "part_summary" and not parts_df.empty:
                    # Format price columns
                    for col_name in [
                        "AMP_toman",
                        "median_price_toman",
                        "min_price_toman",
                        "max_price_toman",
                    ]:
                        if col_name in parts_df.columns:
                            col_idx = list(parts_df.columns).index(col_name)
                            worksheet.set_column(col_idx, col_idx, 15, currency_format)

                    # Apply conditional formatting for outliers
                    self._apply_conditional_formatting(
                        workbook, worksheet, parts_df, sheet_name
                    )

                # Freeze header row
                worksheet.freeze_panes(1, 0)

                # Enable filters
                if sheet_name == "offers_raw" and not offers_df.empty:
                    worksheet.autofilter(
                        0, 0, len(offers_df), len(offers_df.columns) - 1
                    )
                elif sheet_name == "sellers_summary" and not sellers_df.empty:
                    worksheet.autofilter(
                        0, 0, len(sellers_df), len(sellers_df.columns) - 1
                    )
                elif sheet_name == "part_summary" and not parts_df.empty:
                    worksheet.autofilter(0, 0, len(parts_df), len(parts_df.columns) - 1)

        print(f"Excel file created successfully: {self.output_file}")

        # Print summary statistics
        print(f"\nExport Summary:")
        print(f"- Raw offers: {len(offers_df)} rows")
        print(f"- Unique sellers: {len(sellers_df)} sellers")
        print(f"- Unique parts: {len(parts_df)} parts")

        return self.output_file


def test_exporter():
    """Test the enhanced Excel exporter with sample data."""

    # Sample offers data
    sample_offers = [
        {
            "part_id": 1,
            "part_name": "چراغ جلو راست تیگو 8 پرو",
            "part_code": "T8-HL-R-P",
            "query": "چراغ جلو راست تیگو 8 پرو headlight right tiggo",
            "part_key": "BODY:HEADLAMP:RIGHT:UNKNOWN:PRO",
            "part_name_norm": "Tiggo8 Headlamp Right Pro",
            "title_raw": "چراغ جلو راست تیگو 8 پرو اصل",
            "seller_name_norm": "پارت سنتر",
            "price_toman": 1500000,
            "price_rial": 15000000,
            "product_url": "https://torob.com/p/product1",
            "seller_url": "https://torob.com/shop/partcenter",
            "relevance": 0.85,
            "snapshot_ts": datetime.now().isoformat(),
            "price_missing": 0,
        },
        {
            "part_id": 1,
            "part_name": "چراغ جلو راست تیگو 8 پرو",
            "part_code": "T8-HL-R-P",
            "query": "چراغ جلو راست تیگو 8 پرو headlight right tiggo",
            "part_key": "BODY:HEADLAMP:RIGHT:UNKNOWN:PRO",
            "part_name_norm": "Tiggo8 Headlamp Right Pro",
            "title_raw": "چراغ جلو راست تیگو 8 پرو",
            "seller_name_norm": "یدک شاپ",
            "price_toman": 1450000,
            "price_rial": 14500000,
            "product_url": "https://torob.com/p/product2",
            "seller_url": "https://torob.com/shop/yadakshop",
            "relevance": 0.78,
            "snapshot_ts": datetime.now().isoformat(),
            "price_missing": 0,
        },
    ]

    print("Testing Enhanced Excel Exporter:")
    print("=" * 60)

    exporter = ExcelExporter("test_enhanced_output.xlsx")
    output_file = exporter.export_to_excel(sample_offers)

    print(f"Test complete. Output file: {output_file}")


if __name__ == "__main__":
    test_exporter()
