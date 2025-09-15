# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline
- Docker support with multi-stage builds
- Comprehensive test suite
- Code quality tools (Black, isort, flake8, mypy)
- Security scanning with Trivy
- Automated releases to PyPI

### Changed
- Improved error handling and logging
- Enhanced configuration management
- Better documentation structure

## [1.0.0] - 2024-09-15

### Added
- **Two-Stage Scraping Pipeline**
  - Search page scraping with JSON extraction
  - Product page drill-down for detailed offers
  - Relevance filtering and scoring
  - Smart negative category filtering

- **Modern Web Interface**
  - Responsive Bootstrap 5 design
  - Real-time progress tracking
  - Live log viewer with terminal-style display
  - File upload support for CSV files
  - Task management and history
  - Direct Excel download functionality

- **Advanced Performance Features**
  - Parallel processing for multiple parts
  - Intelligent file-based caching system
  - Memory optimization and cleanup
  - Progress tracking with ETA calculations

- **Rich Data Export**
  - Multi-sheet Excel reports
  - Conditional formatting for outliers
  - Hyperlinks for manual validation
  - Comprehensive statistics and analytics
  - Seller and part summaries

- **Developer Tools**
  - Command-line interface with rich formatting
  - RESTful API endpoints
  - Comprehensive configuration system
  - Docker and Docker Compose support
  - Extensive documentation

- **Data Processing**
  - Persian/Arabic digit normalization
  - Currency detection and conversion
  - Seller name normalization
  - Part attribute classification
  - Offer deduplication

### Technical Details
- **Web Scraping**: Playwright with headless Chrome
- **Data Processing**: Pandas for data manipulation
- **Web Framework**: Flask with Jinja2 templates
- **Export**: OpenPyXL and XlsxWriter for Excel
- **Caching**: File-based with TTL support
- **Configuration**: YAML-based configuration
- **Testing**: Pytest with coverage reporting

### Performance
- **Single Part**: 2-3 minutes average
- **Multiple Parts**: 1-2 minutes per part (parallel)
- **Memory Usage**: 100-200MB per task
- **Cache Hit Rate**: ~80% for repeated searches

## [0.9.0] - 2024-09-10

### Added
- Initial prototype with basic scraping
- Simple CLI interface
- Basic Excel export functionality

### Changed
- Improved data extraction accuracy
- Enhanced error handling

## [0.8.0] - 2024-09-05

### Added
- First working version
- Basic Torob.com scraping
- Simple data export

---

## Legend

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
