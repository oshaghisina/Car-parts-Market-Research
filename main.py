#!/usr/bin/env python3
"""
Torob Automotive Parts Price Scraper
Main entry point for the application.

Usage:
    python main.py [--input INPUT_FILE] [--output OUTPUT_FILE] [--headless] [--help]

Examples:
    python main.py
    python main.py --input my_parts.csv --output my_results.xlsx
    python main.py --no-headless  # Run with visible browser for debugging
"""

import argparse
import asyncio
import sys
from pathlib import Path

from core.pipeline import ScrapingPipeline


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Torob Automotive Parts Price Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --input my_parts.csv --output results.xlsx
  python main.py --no-headless --delay-min 2.0 --delay-max 4.0

Input CSV Format:
  part_id,part_name,part_code,keywords
  1,چراغ جلو چپ تیگو 8 پرو مکس,T8-HL-L-PM,چراغ جلو چپ تیگو 8 پرو مکس headlight left tiggo

Output:
  Excel file with three sheets:
  - offers_raw: All scraped offers
  - sellers_summary: Seller statistics  
  - part_summary: Part analysis with AMP (Average Market Price)
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        default="parts_input.csv",
        help="Input CSV file path (default: parts_input.csv)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="torob_prices.xlsx",
        help="Output Excel file path (default: torob_prices.xlsx)",
    )

    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with GUI (useful for debugging)",
    )

    parser.add_argument(
        "--delay-min",
        type=float,
        default=1.5,
        help="Minimum delay between requests in seconds (default: 1.5)",
    )

    parser.add_argument(
        "--delay-max",
        type=float,
        default=3.0,
        help="Maximum delay between requests in seconds (default: 3.0)",
    )

    parser.add_argument("--version", action="version", version="Torob Scraper v1.0.0")

    return parser.parse_args()


def validate_input_file(file_path: str) -> bool:
    """
    Validate that input CSV file exists and has required columns.

    Args:
        file_path: Path to input CSV file

    Returns:
        True if valid, False otherwise
    """
    if not Path(file_path).exists():
        print(f"❌ Error: Input file not found: {file_path}")
        return False

    try:
        import csv

        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            required_columns = {"part_id", "part_name", "keywords"}

            if not required_columns.issubset(set(reader.fieldnames or [])):
                missing = required_columns - set(reader.fieldnames or [])
                print(f"❌ Error: Missing required columns in {file_path}: {missing}")
                print(f"Required columns: {required_columns}")
                print(f"Found columns: {reader.fieldnames}")
                return False

            # Check if file has any data
            row_count = sum(1 for row in reader)
            if row_count == 0:
                print(f"❌ Error: Input file {file_path} contains no data rows")
                return False

            print(f"✅ Input file validated: {file_path} ({row_count} parts)")
            return True

    except Exception as e:
        print(f"❌ Error validating input file {file_path}: {e}")
        return False


def setup_environment():
    """Check and setup required environment."""
    print("🔧 Checking environment...")

    # Check if playwright is available
    try:
        from playwright.sync_api import sync_playwright

        print("✅ Playwright available")
    except ImportError as e:
        print("❌ Error: Playwright not installed")
        print("Please install with: pip install playwright")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # Check required packages
    required_packages = ["pandas", "openpyxl", "asyncio"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Error: Missing required packages: {missing_packages}")
        print("Please install with:")
        print("  pip install -r requirements.txt")
        return False

    print("✅ All required packages available")
    return True


async def main():
    """Main application entry point."""
    print("🚗 Torob Automotive Parts Price Scraper v1.0.0")
    print("=" * 60)

    # Parse arguments
    args = parse_arguments()

    # Validate environment
    if not setup_environment():
        sys.exit(1)

    # Validate input file
    if not validate_input_file(args.input):
        sys.exit(1)

    # Validate delay settings
    if args.delay_min < 0 or args.delay_max < args.delay_min:
        print("❌ Error: Invalid delay settings")
        print(
            f"delay-min ({args.delay_min}) must be >= 0 and <= delay-max ({args.delay_max})"
        )
        sys.exit(1)

    # Show configuration
    print("\n📋 Configuration:")
    print(f"   Input file: {args.input}")
    print(f"   Output file: {args.output}")
    print(f"   Browser mode: {'GUI' if args.no_headless else 'Headless'}")
    print(f"   Delay range: {args.delay_min}-{args.delay_max} seconds")

    # Confirm execution
    try:
        response = input("\n❓ Start scraping? [y/N]: ").strip().lower()
        if response not in ["y", "yes"]:
            print("❌ Scraping cancelled by user")
            sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Scraping cancelled by user")
        sys.exit(0)

    # Initialize and run pipeline
    try:
        pipeline = ScrapingPipeline(
            input_file=args.input,
            output_file=args.output,
            headless=not args.no_headless,
            delay_range=(args.delay_min, args.delay_max),
        )

        success = await pipeline.run_pipeline()

        if success:
            print(f"\n🎉 Success! Results saved to: {args.output}")

            # Show final statistics
            stats = pipeline.get_statistics()
            duration = stats.get("duration_seconds", 0)

            print(f"\n📊 Summary:")
            print(f"   ⏱️  Duration: {duration:.1f} seconds")
            print(f"   📦 Parts processed: {stats.get('parts_processed', 0)}")
            print(f"   🛒 Total offers: {stats.get('total_offers_found', 0)}")
            print(f"   🧹 After dedup: {stats.get('offers_after_dedup', 0)}")
            print(f"   🏪 Unique sellers: {stats.get('unique_sellers', 0)}")

            if stats.get("errors"):
                print(f"   ⚠️  Warnings: {len(stats['errors'])}")

            sys.exit(0)
        else:
            print("\n❌ Scraping failed. Check error messages above.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Handle Windows event loop policy issue
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Run the main function
    asyncio.run(main())
