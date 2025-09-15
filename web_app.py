#!/usr/bin/env python3
"""
Web Interface for Torob Scraper.
Provides a modern web UI for easy scraping without command line.
"""

import asyncio
import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from core.cli_enhancer import get_cli_enhancer
from core.config_manager import get_config
from core.pipeline_torob import TorobTwoStagePipeline

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "torob_scraper_secret_key_2024"

# Configuration
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "results"
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Global state for running tasks
running_tasks = {}
task_results = {}
task_logs = {}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse CSV file and return parts data."""
    import pandas as pd

    try:
        df = pd.read_csv(file_path)
        parts_data = []

        for index, row in df.iterrows():
            part_data = {
                "part_id": f"part_{index+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "part_name": str(row.get("part_name", "")).strip(),
                "part_code": str(row.get("part_code", "")).strip(),
                "keywords": str(row.get("keywords", "")).strip(),
            }

            # Generate keywords if not provided
            if not part_data["keywords"]:
                part_data["keywords"] = f"{part_data['part_name']} automotive part"

            parts_data.append(part_data)

        return parts_data
    except Exception as e:
        raise Exception(f"Error parsing CSV file: {e}")


def add_log(task_id: str, message: str, level: str = "info"):
    """Add log message to task."""
    global task_logs
    task_logs = task_logs  # Explicit assignment for flake8

    if task_id not in task_logs:
        task_logs[task_id] = []

    task_logs[task_id].append(
        {"message": message, "level": level, "timestamp": datetime.now().isoformat()}
    )


def run_scraping_task(
    task_id: str, parts_data: List[Dict[str, Any]], excel_filename: str
):
    """Run scraping task in background thread."""
    global running_tasks, task_results, task_logs
    # Explicit assignments for flake8
    running_tasks = running_tasks
    task_results = task_results
    task_logs = task_logs

    try:
        running_tasks[task_id] = {
            "status": "running",
            "start_time": datetime.now(),
            "progress": 0,
            "message": "Initializing...",
        }

        # Initialize logs
        task_logs[task_id] = []
        add_log(task_id, "🚀 Starting Torob Scraper Pipeline", "info")
        add_log(task_id, f"📋 Processing {len(parts_data)} part(s)", "info")

        # Create pipeline
        add_log(task_id, "⚙️ Initializing scraper components...", "processing")
        pipeline = TorobTwoStagePipeline(parts_data, excel_filename)

        # Add custom log handler to pipeline
        original_print = print

        def log_print(*args, **kwargs):
            message = " ".join(str(arg) for arg in args)
            if "🔍" in message:
                add_log(task_id, message, "search")
            elif "📄" in message:
                add_log(task_id, message, "drill")
            elif "✅" in message or "✓" in message:
                add_log(task_id, message, "success")
            elif "⚠️" in message:
                add_log(task_id, message, "warning")
            elif "❌" in message:
                add_log(task_id, message, "error")
            elif "🔄" in message:
                add_log(task_id, message, "processing")
            elif "📊" in message or "Found" in message:
                add_log(task_id, message, "found")
            else:
                add_log(task_id, message, "info")
            original_print(*args, **kwargs)

        # Temporarily replace print function
        import builtins

        builtins.print = log_print

        try:
            # Run pipeline
            add_log(task_id, "🌐 Starting web scraping...", "processing")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(pipeline.run_pipeline())

            # Restore original print
            builtins.print = original_print

            # Store results
            task_results[task_id] = {
                "status": "completed" if result else "failed",
                "end_time": datetime.now(),
                "excel_file": excel_filename,
                "stats": pipeline.stats,
            }

            # Update running task
            if task_id in running_tasks:
                running_tasks[task_id]["status"] = "completed" if result else "failed"
                running_tasks[task_id]["progress"] = 100
                running_tasks[task_id]["message"] = (
                    "Completed successfully!" if result else "Failed!"
                )

            if result:
                add_log(task_id, "🎉 Scraping completed successfully!", "success")
                add_log(
                    task_id,
                    f'📊 Found {pipeline.stats.get("final_offers", 0)} offers',
                    "found",
                )
                add_log(
                    task_id,
                    f'🏪 From {pipeline.stats.get("unique_sellers", 0)} unique sellers',
                    "found",
                )
            else:
                add_log(task_id, "❌ Scraping failed!", "error")

        finally:
            # Always restore original print
            builtins.print = original_print

    except Exception as e:
        # Handle errors
        add_log(task_id, f"❌ Critical error: {str(e)}", "error")

        if task_id in running_tasks:
            running_tasks[task_id]["status"] = "failed"
            running_tasks[task_id]["message"] = f"Error: {str(e)}"

        task_results[task_id] = {
            "status": "failed",
            "end_time": datetime.now(),
            "error": str(e),
        }


@app.route("/")
def index():
    """Main page."""
    return render_template("index.html")


@app.route("/api/config")
def get_config_api():
    """Get current configuration."""
    config = get_config()
    return jsonify(
        {
            "scraping": config.get_scraping_config(),
            "caching": config.get("caching", {}),
            "performance": config.get("performance", {}),
            "browser": config.get_browser_config(),
        }
    )


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file upload."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        try:
            parts_data = parse_csv_file(file_path)
            return jsonify(
                {
                    "success": True,
                    "filename": filename,
                    "parts_count": len(parts_data),
                    "parts_data": parts_data,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/api/start_scraping", methods=["POST"])
def start_scraping():
    """Start scraping task."""
    data = request.get_json()

    if not data or "parts_data" not in data:
        return jsonify({"error": "No parts data provided"}), 400

    # Generate task ID
    task_id = str(uuid.uuid4())

    # Get parts data
    parts_data = data["parts_data"]
    excel_filename = data.get(
        "excel_filename",
        f'torob_prices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
    )

    # Start background task
    thread = threading.Thread(
        target=run_scraping_task, args=(task_id, parts_data, excel_filename)
    )
    thread.daemon = True
    thread.start()

    return jsonify(
        {
            "success": True,
            "task_id": task_id,
            "message": "Scraping started successfully",
        }
    )


@app.route("/api/task_status/<task_id>")
def get_task_status(task_id):
    """Get task status."""
    if task_id in running_tasks:
        return jsonify(running_tasks[task_id])
    elif task_id in task_results:
        return jsonify(task_results[task_id])
    else:
        return jsonify({"error": "Task not found"}), 404


@app.route("/api/download/<task_id>")
def download_results(task_id):
    """Download results file."""
    if task_id not in task_results:
        return jsonify({"error": "Task not found"}), 404

    result = task_results[task_id]
    if result["status"] != "completed":
        return jsonify({"error": "Task not completed"}), 400

    excel_file = result.get("excel_file")
    if not excel_file or not os.path.exists(excel_file):
        return jsonify({"error": "Results file not found"}), 404

    return send_file(excel_file, as_attachment=True)


@app.route("/api/tasks")
def list_tasks():
    """List all tasks."""
    all_tasks = {}
    all_tasks.update(running_tasks)
    all_tasks.update(task_results)
    return jsonify(all_tasks)


@app.route("/api/task_logs/<task_id>")
def get_task_logs(task_id):
    """Get task logs."""
    if task_id not in task_logs:
        return jsonify({"logs": []})

    logs = task_logs[task_id]
    return jsonify({"logs": logs})


@app.route("/api/clear_tasks", methods=["POST"])
def clear_tasks():
    """Clear completed tasks."""
    global running_tasks, task_results, task_logs
    # Explicit assignments for flake8
    task_results = task_results
    task_logs = task_logs

    # Keep only running tasks
    running_tasks = {k: v for k, v in running_tasks.items() if v["status"] == "running"}

    # Clear completed tasks
    task_results.clear()
    task_logs.clear()

    return jsonify({"success": True, "message": "Tasks cleared"})


if __name__ == "__main__":
    print("🌐 Starting Torob Scraper Web Interface")
    print("=" * 50)
    print("📱 Web Interface: http://localhost:5001")
    print("🔧 API Endpoints: http://localhost:5001/api/")
    print("📊 Configuration: http://localhost:5001/api/config")
    print("=" * 50)

    app.run(debug=True, host="0.0.0.0", port=5001)
