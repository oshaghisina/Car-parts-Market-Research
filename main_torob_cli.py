#!/usr/bin/env python3
"""
Enhanced Interactive CLI for Torob Two-Stage Scraper
Prompts user for part information and runs the enhanced scraping pipeline.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from core.pipeline_torob import TorobTwoStagePipeline
from core.cli_enhancer import get_cli_enhancer
from core.config_manager import get_config


def get_user_input():
    """Get part information from user interactively."""
    cli = get_cli_enhancer()
    config = get_config()

    # Show header
    cli.print_header(
        "Torob Two-Stage Automotive Parts Scraper",
        "Advanced Price Scraping with Caching & Parallel Processing",
    )

    # Show configuration summary
    cli.show_configuration_summary(config.config)

    # Get user inputs
    prompts = [
        {
            "key": "excel_filename",
            "prompt": '📄 Excel filename (e.g., "tiggo8_headlights.xlsx")',
            "required": True,
            "validator": cli.validate_filename,
            "default": "torob_prices.xlsx",
        },
        {
            "key": "part_name",
            "prompt": "📝 Part name (press Enter to use Excel filename)",
            "required": False,
            "validator": cli.validate_part_name,
            "default": None,
        },
        {
            "key": "part_code",
            "prompt": "🔢 Part code (optional)",
            "required": False,
            "validator": cli.validate_part_code,
            "default": "",
        },
        {
            "key": "custom_keywords",
            "prompt": "🔍 Custom keywords (press Enter to auto-generate)",
            "required": False,
            "validator": cli.validate_keywords,
            "default": "",
        },
    ]

    inputs = cli.get_multiple_inputs(prompts)

    # Process inputs
    excel_filename = inputs["excel_filename"]
    part_name = inputs["part_name"]
    part_code = inputs["part_code"]
    custom_keywords = inputs["custom_keywords"]

    # Use Excel filename as part name if not provided
    if not part_name:
        part_name = Path(excel_filename).stem.replace("_", " ").title()
        cli.print_info(f"Using Excel filename as part name: {part_name}")

    # Generate keywords if not provided
    if not custom_keywords:
        custom_keywords = f"{part_name} automotive part"
        cli.print_info(f"Auto-generated keywords: {custom_keywords}")

    # Create part data
    part_data = {
        "part_id": f"part_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "part_name": part_name,
        "part_code": part_code,
        "keywords": custom_keywords,
    }

    # Show part summary
    cli.show_part_summary([part_data])

    return excel_filename, part_data


def get_multiple_parts_input():
    """Get multiple parts information from user."""
    cli = get_cli_enhancer()
    config = get_config()

    # Show header
    cli.print_header(
        "Torob Multi-Part Scraper", "Process Multiple Parts with Parallel Processing"
    )

    # Show configuration summary
    cli.show_configuration_summary(config.config)

    # Get number of parts
    num_parts = int(
        cli.get_user_input(
            "📊 Number of parts to process",
            required=True,
            validator=lambda x: x.isdigit() and int(x) > 0,
            default="1",
        )
    )

    parts_data = []
    excel_filename = None

    for i in range(num_parts):
        cli.print_section(f"Part {i+1} of {num_parts}")

        prompts = [
            {
                "key": "part_name",
                "prompt": f"📝 Part name {i+1}",
                "required": True,
                "validator": cli.validate_part_name,
            },
            {
                "key": "part_code",
                "prompt": f"🔢 Part code {i+1} (optional)",
                "required": False,
                "validator": cli.validate_part_code,
                "default": "",
            },
            {
                "key": "custom_keywords",
                "prompt": f"🔍 Custom keywords {i+1} (press Enter to auto-generate)",
                "required": False,
                "validator": cli.validate_keywords,
                "default": "",
            },
        ]

        inputs = cli.get_multiple_inputs(prompts)

        # Generate keywords if not provided
        if not inputs["custom_keywords"]:
            inputs["custom_keywords"] = f"{inputs['part_name']} automotive part"
            cli.print_info(f"Auto-generated keywords: {inputs['custom_keywords']}")

        # Create part data
        part_data = {
            "part_id": f"part_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "part_name": inputs["part_name"],
            "part_code": inputs["part_code"],
            "keywords": inputs["custom_keywords"],
        }

        parts_data.append(part_data)

        # Set Excel filename from first part
        if i == 0:
            excel_filename = (
                f"{inputs['part_name'].replace(' ', '_').lower()}_prices.xlsx"
            )

    # Show parts summary
    cli.show_part_summary(parts_data)

    return excel_filename, parts_data


async def run_pipeline(parts_data, excel_filename):
    """Run the scraping pipeline."""
    cli = get_cli_enhancer()

    # Create pipeline
    pipeline = TorobTwoStagePipeline(parts_data, excel_filename)

    # Estimate processing time
    estimated_time = (
        f"{len(parts_data) * 2} minutes" if len(parts_data) > 1 else "2 minutes"
    )

    # Confirm processing
    if not cli.confirm_processing(len(parts_data), estimated_time):
        cli.print_info("Processing cancelled by user.")
        return False

    # Run pipeline
    cli.print_section("Starting Pipeline")
    cli.print_info("Initializing scraper and starting processing...")

    try:
        results = await pipeline.run_pipeline()

        # Show processing stats
        cli.show_processing_stats(pipeline.stats)

        # Show export summary
        export_info = {
            "filename": excel_filename,
            "total_rows": pipeline.stats.get("final_offers", 0),
            "unique_sellers": pipeline.stats.get("unique_sellers", 0),
            "unique_parts": pipeline.stats.get("unique_parts", 0),
        }

        cli.show_export_summary(export_info)

        cli.print_success(
            f"Pipeline completed successfully! Results saved to {excel_filename}"
        )
        return True

    except Exception as e:
        cli.print_error(f"Pipeline failed: {e}")
        return False


def show_main_menu():
    """Show main menu options."""
    cli = get_cli_enhancer()

    cli.print_header("Torob Scraper Main Menu")

    print("Select an option:")
    print("1. 🚗 Process Single Part")
    print("2. 📊 Process Multiple Parts")
    print("3. ⚙️  Show Configuration")
    print("4. ❓ Show Help")
    print("5. 🚪 Exit")
    print()

    choice = cli.get_user_input(
        "Enter your choice", required=True, choices=["1", "2", "3", "4", "5"]
    )

    return choice


async def main():
    """Main CLI function."""
    cli = get_cli_enhancer()

    try:
        while True:
            choice = show_main_menu()

            if choice == "1":
                # Single part processing
                excel_filename, part_data = get_user_input()
                await run_pipeline([part_data], excel_filename)

            elif choice == "2":
                # Multiple parts processing
                excel_filename, parts_data = get_multiple_parts_input()
                await run_pipeline(parts_data, excel_filename)

            elif choice == "3":
                # Show configuration
                config = get_config()
                cli.show_configuration_summary(config.config)

            elif choice == "4":
                # Show help
                cli.show_help()

            elif choice == "5":
                # Exit
                cli.print_info("Thank you for using Torob Scraper!")
                break

            # Ask if user wants to continue
            if choice in ["1", "2"]:
                if not cli.get_yes_no(
                    "Do you want to process another part?", default=False
                ):
                    cli.print_info("Thank you for using Torob Scraper!")
                    break

            print()  # Add spacing between iterations

    except KeyboardInterrupt:
        cli.print_warning("\n\nOperation cancelled by user.")
    except Exception as e:
        cli.print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if help was requested
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        cli = get_cli_enhancer()
        cli.show_help()
        sys.exit(0)

    # Run the main CLI
    asyncio.run(main())
