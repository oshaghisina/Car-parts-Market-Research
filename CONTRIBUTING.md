# Contributing to Torob Scraper

Thank you for your interest in contributing to Torob Scraper! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### **Reporting Bugs**

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating issues
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Error messages and logs

### **Suggesting Features**

1. **Check existing feature requests** first
2. **Use the feature request template**
3. **Describe the use case** and benefits
4. **Consider implementation complexity**

### **Code Contributions**

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Add tests** for new functionality
5. **Ensure all tests pass**
6. **Submit a pull request**

## 🛠️ Development Setup

### **Prerequisites**

- Python 3.8+
- Git
- Docker (optional)

### **Local Development**

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/torob-scraper.git
cd torob-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Install Playwright browsers
playwright install

# Install pre-commit hooks
pre-commit install
```

### **Docker Development**

```bash
# Build development image
docker build -t torob-scraper-dev .

# Run with volume mounting
docker run -v $(pwd):/app -p 5001:5001 torob-scraper-dev
```

## 📝 Code Style

We maintain high code quality standards:

### **Formatting**
- **Black** for code formatting (line length: 88)
- **isort** for import sorting
- **Pre-commit hooks** for automatic formatting

### **Linting**
- **flake8** for code linting
- **mypy** for type checking
- **pylint** for additional checks

### **Testing**
- **pytest** for testing framework
- **pytest-cov** for coverage reporting
- **pytest-asyncio** for async testing

### **Running Quality Checks**

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Run tests
pytest
pytest --cov=. --cov-report=html
```

## 🧪 Testing

### **Test Structure**

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test fixtures
└── conftest.py     # Pytest configuration
```

### **Writing Tests**

```python
# Example unit test
def test_normalize_digits():
    from utils.text import normalize_digits
    
    assert normalize_digits("۱۲۳۴۵") == "12345"
    assert normalize_digits("12345") == "12345"

# Example integration test
@pytest.mark.asyncio
async def test_scraping_pipeline():
    pipeline = TorobTwoStagePipeline(test_data)
    result = await pipeline.run_pipeline()
    assert result is True
```

### **Test Categories**

- **Unit Tests**: Fast, isolated tests
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Full workflow testing

### **Running Tests**

```bash
# Run all tests
pytest

# Run specific categories
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with coverage
pytest --cov=. --cov-report=html
```

## 📚 Documentation

### **Code Documentation**

- **Docstrings**: Use Google style docstrings
- **Type Hints**: Add type hints for all functions
- **Comments**: Explain complex logic

```python
def normalize_digits(text: str) -> str:
    """
    Normalize Persian/Arabic digits to Latin digits.
    
    Args:
        text: Input text containing digits
        
    Returns:
        Text with normalized digits
        
    Example:
        >>> normalize_digits("۱۲۳۴۵")
        "12345"
    """
    # Implementation here
    pass
```

### **API Documentation**

- **REST API**: Document all endpoints
- **CLI**: Document all commands and options
- **Configuration**: Document all config options

## 🚀 Pull Request Process

### **Before Submitting**

1. **Run all tests**: `pytest`
2. **Check code style**: `black . && isort . && flake8 .`
3. **Update documentation** if needed
4. **Add tests** for new features
5. **Update CHANGELOG.md**

### **Pull Request Template**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### **Review Process**

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** in different environments
4. **Documentation** review
5. **Approval** and merge

## 🏗️ Architecture Guidelines

### **Project Structure**

```
torob_scraper/
├── adapters/       # External service adapters
├── core/          # Core business logic
├── utils/         # Utility functions
├── templates/     # Web templates
├── static/        # Static assets
└── tests/         # Test files
```

### **Design Principles**

- **Single Responsibility**: Each module has one purpose
- **Dependency Injection**: Use dependency injection
- **Interface Segregation**: Small, focused interfaces
- **Open/Closed**: Open for extension, closed for modification

### **Error Handling**

```python
# Use specific exceptions
class ScrapingError(Exception):
    """Raised when scraping fails."""
    pass

# Handle errors gracefully
try:
    result = await scraper.scrape(url)
except ScrapingError as e:
    logger.error(f"Scraping failed: {e}")
    return None
```

## 🔒 Security

### **Security Guidelines**

- **No hardcoded secrets** in code
- **Validate all inputs** from external sources
- **Use environment variables** for configuration
- **Regular dependency updates**
- **Security scanning** in CI/CD

### **Reporting Security Issues**

- **Email**: security@torobscraper.com
- **Do not** create public issues for security vulnerabilities
- **Include** detailed reproduction steps

## 📋 Issue Templates

### **Bug Report**

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.9.0]
- Torob Scraper version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

### **Feature Request**

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or workarounds.

**Additional context**
Any other context about the feature request.
```

## 🎯 Roadmap

### **Current Priorities**

1. **Performance optimization**
2. **Enhanced error handling**
3. **Additional data sources**
4. **Mobile app development**

### **Future Features**

- Multi-language support
- Advanced analytics dashboard
- Machine learning price predictions
- API rate limiting

## 📞 Getting Help

- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bugs and feature requests
- **Email**: contact@torobscraper.com
- **Documentation**: [Wiki](https://github.com/yourusername/torob-scraper/wiki)

## 🙏 Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md** file
- **Release notes**
- **Project documentation**

Thank you for contributing to Torob Scraper! 🚀
