#!/usr/bin/env python3
"""
Progress Tracker for Torob Scraper.
Provides rich progress indicators with real-time updates and ETA.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import sys

from core.config_manager import get_config


class ProgressTracker:
    """Tracks and displays progress with rich formatting."""

    def __init__(self):
        """Initialize the progress tracker."""
        self.config = get_config()
        self.performance_config = self.config.get("performance", {})
        self.progress_config = self.performance_config.get("progress", {})

        # Progress settings
        self.enabled = self.progress_config.get("enabled", True)
        self.update_interval = self.progress_config.get("update_interval", 1)
        self.show_eta = self.progress_config.get("show_eta", True)

        # Progress state
        self.current_task = None
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = None
        self.last_update = 0

        # Task details
        self.tasks = {}  # task_id -> task_info
        self.current_task_id = None

        # Threading
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._update_thread = None

        # Colors (if terminal supports it)
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
        }

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text."""
        if not sys.stdout.isatty():  # No colors if not a terminal
            return text
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def _get_terminal_width(self) -> int:
        """Get terminal width for progress bar."""
        try:
            import shutil

            return shutil.get_terminal_size().columns
        except:
            return 80

    def _format_time(self, seconds: float) -> str:
        """Format time in a human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

    def _calculate_eta(self) -> Optional[float]:
        """Calculate estimated time remaining."""
        if not self.start_time or self.completed_tasks == 0:
            return None

        elapsed = time.time() - self.start_time
        rate = self.completed_tasks / elapsed
        remaining = self.total_tasks - self.completed_tasks

        return remaining / rate if rate > 0 else None

    def _update_display(self):
        """Update the progress display."""
        if not self.enabled or not self.current_task:
            return

        with self._lock:
            current_time = time.time()

            # Only update if enough time has passed
            if current_time - self.last_update < self.update_interval:
                return

            self.last_update = current_time

            # Clear previous line
            print("\r", end="", flush=True)

            # Calculate progress
            total_processed = self.completed_tasks + self.failed_tasks
            percentage = (
                (total_processed / self.total_tasks * 100)
                if self.total_tasks > 0
                else 0
            )

            # Create progress bar
            bar_length = 30
            filled_length = (
                int(bar_length * total_processed // self.total_tasks)
                if self.total_tasks > 0
                else 0
            )
            bar = "█" * filled_length + "░" * (bar_length - filled_length)

            # Format progress text
            progress_text = f"🔄 {self.current_task} [{bar}] {total_processed}/{self.total_tasks} ({percentage:.1f}%)"

            # Add timing information
            if self.start_time:
                elapsed = current_time - self.start_time
                progress_text += f" | Elapsed: {self._format_time(elapsed)}"

                # Add ETA if enabled
                if self.show_eta and self.completed_tasks > 0:
                    eta = self._calculate_eta()
                    if eta:
                        progress_text += f" | ETA: {self._format_time(eta)}"

            # Add task details
            if self.current_task_id and self.current_task_id in self.tasks:
                task_info = self.tasks[self.current_task_id]
                if task_info.get("details"):
                    progress_text += f" | {task_info['details']}"

            # Truncate if too long
            max_width = self._get_terminal_width() - 10
            if len(progress_text) > max_width:
                progress_text = progress_text[: max_width - 3] + "..."

            # Print progress
            print(self._colorize(progress_text, "cyan"), end="", flush=True)

    def _update_loop(self):
        """Background thread for updating progress."""
        while not self._stop_event.is_set():
            self._update_display()
            time.sleep(0.5)  # Update every 500ms

    def start(self, total_tasks: int, initial_task: str = "Starting..."):
        """
        Start progress tracking.

        Args:
            total_tasks: Total number of tasks to process
            initial_task: Initial task description
        """
        if not self.enabled:
            return

        with self._lock:
            self.total_tasks = total_tasks
            self.completed_tasks = 0
            self.failed_tasks = 0
            self.start_time = time.time()
            self.last_update = 0
            self.current_task = initial_task
            self.tasks = {}
            self.current_task_id = None

        # Start update thread
        if not self._update_thread or not self._update_thread.is_alive():
            self._stop_event.clear()
            self._update_thread = threading.Thread(
                target=self._update_loop, daemon=True
            )
            self._update_thread.start()

    def update_task(
        self, task_description: str, task_id: str = None, details: str = None
    ):
        """
        Update current task description.

        Args:
            task_description: Description of current task
            task_id: Unique identifier for the task
            details: Additional details about the task
        """
        if not self.enabled:
            return

        with self._lock:
            self.current_task = task_description
            if task_id:
                self.current_task_id = task_id
                self.tasks[task_id] = {
                    "description": task_description,
                    "details": details,
                    "start_time": time.time(),
                }

    def complete_task(self, task_id: str = None, success: bool = True):
        """
        Mark a task as completed.

        Args:
            task_id: Task identifier (optional)
            success: Whether the task completed successfully
        """
        if not self.enabled:
            return

        with self._lock:
            if success:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1

            # Update task info if provided
            if task_id and task_id in self.tasks:
                self.tasks[task_id]["completed"] = True
                self.tasks[task_id]["success"] = success
                self.tasks[task_id]["end_time"] = time.time()

    def add_subtask(
        self, parent_task_id: str, subtask_description: str, subtask_id: str = None
    ):
        """
        Add a subtask to a parent task.

        Args:
            parent_task_id: Parent task identifier
            subtask_description: Description of the subtask
            subtask_id: Unique identifier for the subtask
        """
        if not self.enabled or parent_task_id not in self.tasks:
            return

        if not subtask_id:
            subtask_id = f"{parent_task_id}_sub_{len(self.tasks)}"

        with self._lock:
            self.tasks[subtask_id] = {
                "description": subtask_description,
                "parent": parent_task_id,
                "start_time": time.time(),
            }

    def update_subtask(self, subtask_id: str, details: str = None):
        """
        Update subtask details.

        Args:
            subtask_id: Subtask identifier
            details: Additional details
        """
        if not self.enabled or subtask_id not in self.tasks:
            return

        with self._lock:
            self.tasks[subtask_id]["details"] = details

    def complete_subtask(self, subtask_id: str, success: bool = True):
        """
        Mark a subtask as completed.

        Args:
            subtask_id: Subtask identifier
            success: Whether the subtask completed successfully
        """
        if not self.enabled or subtask_id not in self.tasks:
            return

        with self._lock:
            self.tasks[subtask_id]["completed"] = True
            self.tasks[subtask_id]["success"] = success
            self.tasks[subtask_id]["end_time"] = time.time()

    def finish(self, final_message: str = "Completed!"):
        """
        Finish progress tracking.

        Args:
            final_message: Final message to display
        """
        if not self.enabled:
            return

        # Stop update thread
        self._stop_event.set()
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=1)

        # Clear progress line and show final message
        print("\r" + " " * self._get_terminal_width() + "\r", end="", flush=True)

        # Show final statistics
        if self.start_time:
            total_time = time.time() - self.start_time
            print(self._colorize(f"✅ {final_message}", "green"))
            print(
                self._colorize(
                    f"   Completed: {self.completed_tasks}/{self.total_tasks}", "dim"
                )
            )
            print(self._colorize(f"   Failed: {self.failed_tasks}", "dim"))
            print(
                self._colorize(f"   Total Time: {self._format_time(total_time)}", "dim")
            )

            if self.completed_tasks > 0:
                avg_time = total_time / self.completed_tasks
                print(
                    self._colorize(
                        f"   Average per task: {self._format_time(avg_time)}", "dim"
                    )
                )
        else:
            print(self._colorize(f"✅ {final_message}", "green"))

    def get_stats(self) -> Dict[str, Any]:
        """Get current progress statistics."""
        with self._lock:
            total_processed = self.completed_tasks + self.failed_tasks
            percentage = (
                (total_processed / self.total_tasks * 100)
                if self.total_tasks > 0
                else 0
            )

            stats = {
                "total_tasks": self.total_tasks,
                "completed_tasks": self.completed_tasks,
                "failed_tasks": self.failed_tasks,
                "percentage": percentage,
                "current_task": self.current_task,
                "start_time": self.start_time,
            }

            if self.start_time:
                stats["elapsed_time"] = time.time() - self.start_time
                stats["eta"] = self._calculate_eta()

            return stats


# Global progress tracker instance
progress_tracker = ProgressTracker()


def get_progress_tracker() -> ProgressTracker:
    """Get the global progress tracker instance."""
    return progress_tracker
