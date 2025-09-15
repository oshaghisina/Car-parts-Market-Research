#!/usr/bin/env python3
"""
CLI Enhancer for Torob Scraper.
Provides rich CLI interface with better prompts, validation, and user experience.
"""

import os
import sys
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import shutil

from core.config_manager import get_config


class CLIEnhancer:
    """Enhanced CLI interface with rich formatting and validation."""
    
    def __init__(self):
        """Initialize the CLI enhancer."""
        self.config = get_config()
        self.terminal_width = self._get_terminal_width()
        
        # Colors and formatting
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bg_red': '\033[41m',
            'bg_green': '\033[42m',
            'bg_yellow': '\033[43m',
            'bg_blue': '\033[44m',
        }
    
    def _get_terminal_width(self) -> int:
        """Get terminal width for proper formatting."""
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text."""
        if not sys.stdout.isatty():  # No colors if not a terminal
            return text
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def _center_text(self, text: str, width: int = None) -> str:
        """Center text within given width."""
        if width is None:
            width = self.terminal_width
        return text.center(width)
    
    def _create_border(self, char: str = "=", width: int = None) -> str:
        """Create a border line."""
        if width is None:
            width = self.terminal_width
        return char * width
    
    def print_header(self, title: str, subtitle: str = None) -> None:
        """Print a formatted header."""
        print()
        print(self._colorize(self._create_border("="), "cyan"))
        print(self._colorize(self._center_text(title), "bold"))
        if subtitle:
            print(self._colorize(self._center_text(subtitle), "dim"))
        print(self._colorize(self._create_border("="), "cyan"))
        print()
    
    def print_section(self, title: str) -> None:
        """Print a section header."""
        print()
        print(self._colorize(f"📋 {title}", "bold"))
        print(self._colorize(self._create_border("-", len(title) + 4), "dim"))
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        print(self._colorize(f"✅ {message}", "green"))
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        print(self._colorize(f"⚠️  {message}", "yellow"))
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        print(self._colorize(f"❌ {message}", "red"))
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        print(self._colorize(f"ℹ️  {message}", "blue"))
    
    def print_progress(self, current: int, total: int, message: str = "") -> None:
        """Print progress information."""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        progress_text = f"🔄 {message} [{bar}] {current}/{total} ({percentage:.1f}%)"
        print(f"\r{self._colorize(progress_text, 'cyan')}", end="", flush=True)
    
    def print_table(self, headers: List[str], rows: List[List[str]], title: str = None) -> None:
        """Print a formatted table."""
        if not rows:
            return
        
        if title:
            print(f"\n{self._colorize(title, 'bold')}")
        
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print header
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        print(self._colorize(header_row, "bold"))
        print(self._colorize("-" * len(header_row), "dim"))
        
        # Print rows
        for row in rows:
            row_text = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(row_text)
    
    def get_user_input(self, prompt: str, 
                      required: bool = True, 
                      validator: callable = None,
                      default: str = None,
                      choices: List[str] = None) -> str:
        """
        Get user input with validation.
        
        Args:
            prompt: Input prompt
            required: Whether input is required
            validator: Validation function
            default: Default value if input is empty
            choices: List of valid choices
            
        Returns:
            User input string
        """
        while True:
            # Format prompt
            if choices:
                choices_text = f" ({'/'.join(choices)})"
            else:
                choices_text = ""
            
            if default:
                prompt_text = f"{prompt}{choices_text} [{default}]: "
            else:
                prompt_text = f"{prompt}{choices_text}: "
            
            # Get input
            try:
                user_input = input(self._colorize(prompt_text, "cyan")).strip()
            except (KeyboardInterrupt, EOFError):
                print(self._colorize("\n\n👋 Goodbye!", "yellow"))
                sys.exit(0)
            
            # Handle empty input
            if not user_input:
                if default:
                    return default
                elif not required:
                    return ""
                else:
                    self.print_error("This field is required. Please enter a value.")
                    continue
            
            # Validate choices
            if choices and user_input not in choices:
                self.print_error(f"Invalid choice. Please select from: {', '.join(choices)}")
                continue
            
            # Validate with custom validator
            if validator:
                try:
                    if not validator(user_input):
                        continue
                except Exception as e:
                    self.print_error(f"Validation error: {e}")
                    continue
            
            return user_input
    
    def get_yes_no(self, prompt: str, default: bool = None) -> bool:
        """
        Get yes/no input from user.
        
        Args:
            prompt: Input prompt
            default: Default value (True/False/None)
            
        Returns:
            Boolean value
        """
        while True:
            if default is True:
                prompt_text = f"{prompt} [Y/n]: "
            elif default is False:
                prompt_text = f"{prompt} [y/N]: "
            else:
                prompt_text = f"{prompt} [y/n]: "
            
            try:
                user_input = input(self._colorize(prompt_text, "cyan")).strip().lower()
            except (KeyboardInterrupt, EOFError):
                print(self._colorize("\n\n👋 Goodbye!", "yellow"))
                sys.exit(0)
            
            if not user_input and default is not None:
                return default
            
            if user_input in ['y', 'yes']:
                return True
            elif user_input in ['n', 'no']:
                return False
            else:
                self.print_error("Please enter 'y' for yes or 'n' for no.")
    
    def get_multiple_inputs(self, prompts: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Get multiple inputs from user.
        
        Args:
            prompts: List of prompt dictionaries
            
        Returns:
            Dictionary of user inputs
        """
        results = {}
        
        for prompt_config in prompts:
            key = prompt_config['key']
            prompt = prompt_config['prompt']
            required = prompt_config.get('required', True)
            validator = prompt_config.get('validator')
            default = prompt_config.get('default')
            choices = prompt_config.get('choices')
            
            value = self.get_user_input(
                prompt=prompt,
                required=required,
                validator=validator,
                default=default,
                choices=choices
            )
            
            results[key] = value
        
        return results
    
    def validate_filename(self, filename: str) -> bool:
        """Validate filename for Excel export."""
        if not filename:
            return False
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Ensure it ends with .xlsx
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        return True
    
    def validate_part_name(self, part_name: str) -> bool:
        """Validate part name."""
        if not part_name or len(part_name.strip()) < 2:
            self.print_error("Part name must be at least 2 characters long.")
            return False
        return True
    
    def validate_part_code(self, part_code: str) -> bool:
        """Validate part code (optional)."""
        if not part_code:
            return True  # Optional field
        
        if len(part_code.strip()) < 2:
            self.print_error("Part code must be at least 2 characters long.")
            return False
        return True
    
    def validate_keywords(self, keywords: str) -> bool:
        """Validate keywords."""
        if not keywords or len(keywords.strip()) < 2:
            self.print_error("Keywords must be at least 2 characters long.")
            return False
        return True
    
    def show_configuration_summary(self, config_data: Dict[str, Any]) -> None:
        """Show configuration summary."""
        self.print_section("Configuration Summary")
        
        # Scraping settings
        scraping = config_data.get('scraping', {})
        print(f"🌐 Base URL: {scraping.get('base_url', 'N/A')}")
        print(f"⏱️  Delay Range: {scraping.get('delay_range', {}).get('min', 'N/A')}-{scraping.get('delay_range', {}).get('max', 'N/A')}s")
        print(f"📜 Max Scroll Attempts: {scraping.get('scroll', {}).get('max_attempts', 'N/A')}")
        
        # Caching settings
        caching = config_data.get('caching', {})
        print(f"💾 Caching: {'Enabled' if caching.get('enabled') else 'Disabled'}")
        print(f"⏰ Cache TTL: {caching.get('ttl_hours', 'N/A')} hours")
        print(f"📦 Max Cache Size: {caching.get('max_size_mb', 'N/A')} MB")
        
        # Performance settings
        performance = config_data.get('performance', {})
        parallel = performance.get('parallel', {})
        print(f"🚀 Parallel Processing: {'Enabled' if parallel.get('enabled') else 'Disabled'}")
        print(f"👥 Max Workers: {parallel.get('max_workers', 'N/A')}")
        print(f"📦 Batch Size: {parallel.get('batch_size', 'N/A')}")
        
        print()
    
    def show_part_summary(self, parts_data: List[Dict[str, Any]]) -> None:
        """Show parts summary before processing."""
        self.print_section("Parts to Process")
        
        headers = ["#", "Part Name", "Part Code", "Keywords"]
        rows = []
        
        for i, part in enumerate(parts_data, 1):
            rows.append([
                str(i),
                part.get('part_name', 'N/A'),
                part.get('part_code', 'N/A') or 'None',
                part.get('keywords', 'N/A')[:50] + '...' if len(part.get('keywords', '')) > 50 else part.get('keywords', 'N/A')
            ])
        
        self.print_table(headers, rows)
        print()
    
    def show_processing_stats(self, stats: Dict[str, Any]) -> None:
        """Show processing statistics."""
        self.print_section("Processing Statistics")
        
        # Basic stats
        print(f"📊 Parts Processed: {stats.get('parts_processed', 0)}")
        print(f"🔍 Search Results: {stats.get('search_results', 0)}")
        print(f"✅ Final Offers: {stats.get('final_offers', 0)}")
        
        # Timing
        if stats.get('start_time') and stats.get('end_time'):
            duration = stats['end_time'] - stats['start_time']
            print(f"⏱️  Total Time: {duration:.2f} seconds")
        
        # Cache stats
        cache_stats = stats.get('cache_stats', {})
        if cache_stats:
            print(f"💾 Cache Hits: {cache_stats.get('hits', 0)}")
            print(f"💾 Cache Misses: {cache_stats.get('misses', 0)}")
            print(f"💾 Hit Rate: {cache_stats.get('hit_rate', 0):.1f}%")
        
        print()
    
    def show_export_summary(self, export_info: Dict[str, Any]) -> None:
        """Show export summary."""
        self.print_section("Export Summary")
        
        print(f"📄 Excel File: {export_info.get('filename', 'N/A')}")
        print(f"📊 Total Rows: {export_info.get('total_rows', 0)}")
        print(f"🏪 Unique Sellers: {export_info.get('unique_sellers', 0)}")
        print(f"🔧 Unique Parts: {export_info.get('unique_parts', 0)}")
        
        if export_info.get('file_size'):
            print(f"📦 File Size: {export_info.get('file_size', 'N/A')}")
        
        print()
    
    def confirm_processing(self, parts_count: int, estimated_time: str = None) -> bool:
        """Ask user to confirm processing."""
        self.print_section("Confirmation")
        
        print(f"📋 Ready to process {parts_count} part(s)")
        if estimated_time:
            print(f"⏱️  Estimated time: {estimated_time}")
        
        print()
        return self.get_yes_no("Do you want to start processing?", default=True)
    
    def show_help(self) -> None:
        """Show help information."""
        self.print_header("Torob Scraper Help", "Automotive Parts Price Scraper")
        
        print(self._colorize("Usage:", "bold"))
        print("  python main_torob_cli.py")
        print()
        
        print(self._colorize("Features:", "bold"))
        print("  • Search Torob.com for automotive parts")
        print("  • Extract prices from multiple sellers")
        print("  • Export results to Excel with formatting")
        print("  • Caching for faster repeated searches")
        print("  • Parallel processing for multiple parts")
        print("  • Real-time progress tracking")
        print()
        
        print(self._colorize("Configuration:", "bold"))
        print("  • Edit config.yaml to customize settings")
        print("  • Enable/disable caching and parallel processing")
        print("  • Adjust delays and timeouts")
        print("  • Configure Excel export formatting")
        print()
        
        print(self._colorize("Output:", "bold"))
        print("  • Excel file with multiple sheets:")
        print("    - offers_raw: All individual offers")
        print("    - sellers_summary: Seller statistics")
        print("    - part_summary: Part statistics")
        print("  • Hyperlinks for manual validation")
        print("  • Conditional formatting for outliers")
        print()


# Global CLI enhancer instance
cli_enhancer = CLIEnhancer()

def get_cli_enhancer() -> CLIEnhancer:
    """Get the global CLI enhancer instance."""
    return cli_enhancer
