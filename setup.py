#!/usr/bin/env python3
"""
Setup script for Torob Scraper package.
"""

from setuptools import setup, find_packages
import os


# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Torob Scraper - Advanced Automotive Parts Price Scraper"


# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


setup(
    name="torob-scraper",
    version="1.0.0",
    author="Torob Scraper Team",
    author_email="contact@torobscraper.com",
    description="Advanced Automotive Parts Price Scraper with Web Interface",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/oshaghisina/Car-parts-Market-Research",
    project_urls={
        "Bug Reports": "https://github.com/oshaghisina/Car-parts-Market-Research/issues",
        "Source": "https://github.com/oshaghisina/Car-parts-Market-Research",
        "Documentation": "https://github.com/oshaghisina/Car-parts-Market-Research/wiki",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: Flask",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "httpx>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "torob-scraper-cli=main_torob_cli:main",
            "torob-scraper-web=web_app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt", "*.md"],
        "templates": ["*.html"],
        "static": ["*.css", "*.js"],
    },
    zip_safe=False,
    keywords="scraping, automotive, parts, prices, torob, web-scraping, playwright, flask",
)
