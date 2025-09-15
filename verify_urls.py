#!/usr/bin/env python3
"""
Verify that URL columns are properly populated in the Excel file.
"""

import pandas as pd


def verify_urls():
    """Check URL columns in the Excel file."""
    print("🔍 Verifying URL Columns in Excel File")
    print("=" * 50)

    try:
        # Read the Excel file
        excel_file = "torob_prices.xlsx"

        # Read all sheets
        offers_df = pd.read_excel(excel_file, sheet_name="offers_raw")
        sellers_df = pd.read_excel(excel_file, sheet_name="sellers_summary")
        parts_df = pd.read_excel(excel_file, sheet_name="part_summary")

        print(f"📊 Excel file loaded successfully!")
        print(f"   - Offers: {len(offers_df)} rows")
        print(f"   - Sellers: {len(sellers_df)} rows")
        print(f"   - Parts: {len(parts_df)} rows")

        # Check offers_raw sheet
        print(f"\n🔍 Checking 'offers_raw' sheet:")
        print(f"   Columns: {list(offers_df.columns)}")

        # Check URL columns
        url_columns = ["product_url", "seller_url", "validation_urls"]
        for col in url_columns:
            if col in offers_df.columns:
                non_empty = offers_df[col].notna().sum()
                total = len(offers_df)
                print(f"   ✅ {col}: {non_empty}/{total} rows have data")

                # Show sample data
                sample_data = offers_df[col].dropna().head(3)
                for i, data in enumerate(sample_data):
                    print(f"      [{i+1}] {str(data)[:80]}...")
            else:
                print(f"   ❌ {col}: Column not found")

        # Check sellers_summary sheet
        print(f"\n🔍 Checking 'sellers_summary' sheet:")
        url_columns = ["sample_urls", "validation_urls"]
        for col in url_columns:
            if col in sellers_df.columns:
                non_empty = sellers_df[col].notna().sum()
                total = len(sellers_df)
                print(f"   ✅ {col}: {non_empty}/{total} rows have data")
            else:
                print(f"   ❌ {col}: Column not found")

        # Check part_summary sheet
        print(f"\n🔍 Checking 'part_summary' sheet:")
        url_columns = ["sample_urls", "validation_urls"]
        for col in url_columns:
            if col in parts_df.columns:
                non_empty = parts_df[col].notna().sum()
                total = len(parts_df)
                print(f"   ✅ {col}: {non_empty}/{total} rows have data")
            else:
                print(f"   ❌ {col}: Column not found")

        print(f"\n🎉 URL verification complete!")
        return True

    except Exception as e:
        print(f"❌ Error verifying URLs: {e}")
        return False


if __name__ == "__main__":
    verify_urls()
