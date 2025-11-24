# Contributing to Browser Isolation System

First off, thank you for considering contributing to Browser Isolation! It's people like you that make this project a great tool for secure web browsing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Security Vulnerabilities](#security-vulnerabilities)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for containerized development)
- Git
- Basic understanding of web security concepts

### Development Setup

1. **Fork and clone the repository**

```bash
git clone <repository-url>
cd browser_isolation
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Install pre-commit hooks**

```bash
pre-commit install
```

5. **Install Playwright browsers**

```bash
playwright install chromium
```

6. **Run tests to verify setup**

```bash
pytest tests/ -v
```

## Development Process

### Branching Strategy

We use a simplified Git Flow:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Urgent production fixes

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with these specifications:

- **Line length**: 100 characters (max 120 for complex lines)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Type hints**: Required for all function signatures
- **Docstrings**: Required for all public functions, classes, and modules

### Code Style Example

```python
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExampleComponent:
    """
    Brief description of the component.
    
    Longer description explaining the purpose, behavior,
    and usage patterns of this component.
    
    Attributes:
        attribute_name: Description of the attribute
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the component.
        
        Args:
            config: Configuration dictionary containing settings
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self._validate_config()
    
    def process_data(
        self,
        data: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Process input data according to specified options.
        
        Args:
            data: Input data to process
            options: Optional processing configuration
            
        Returns:
            List of processed data items
            
        Raises:
            ProcessingError: If processing fails
        """
        try:
            # Implementation here
            result = self._internal_process(data)
            logger.info(f"Processed {len(result)} items")
            return result
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise ProcessingError(f"Failed to process data: {e}")
    
    def _internal_process(self, data: str) -> List[str]:
        """Internal processing method (private)."""
        # Implementation
        pass
```

### Documentation Standards

- **Module docstrings**: Every Python file must have a module-level docstring
- **Class docstrings**: Describe purpose, attributes, and usage
- **Function docstrings**: Include Args, Returns, Raises sections
- **Inline comments**: For complex logic only (code should be self-documenting)

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Module names**: lowercase with underscores

## Testing Guidelines

### Test Requirements

- All new features must include tests
- Bug fixes must include regression tests
- Aim for >80% code coverage
- Tests must be isolated and repeatable

### Test Structure

```python
"""
Tests for ExampleComponent

Comprehensive test suite covering normal operation,
edge cases, and error conditions.
"""

import pytest
from unittest.mock import Mock, patch

from engine.example_component import ExampleComponent


class TestExampleComponent:
    """Test suite for ExampleComponent."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.config = {"key": "value"}
        self.component = ExampleComponent(self.config)
    
    def test_initialization(self):
        """Test component initialization."""
        assert self.component.config == self.config
    
    def test_process_data_success(self):
        """Test successful data processing."""
        data = "test data"
        result = self.component.process_data(data)
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_process_data_with_invalid_input(self):
        """Test processing with invalid input."""
        with pytest.raises(ValueError):
            self.component.process_data("")
    
    @patch('engine.example_component.external_service')
    def test_process_data_with_mock(self, mock_service):
        """Test processing with mocked external service."""
        mock_service.return_value = ["result"]
        result = self.component.process_data("data")
        
        assert result == ["result"]
        mock_service.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=engine --cov=api --cov=client tests/

# Run specific test file
pytest tests/test_dom_sanitizer.py -v

# Run specific test
pytest tests/test_dom_sanitizer.py::TestDOMSanitizer::test_remove_script_tags -v
```

## Commit Guidelines

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates

**Examples:**

```bash
feat(engine): add support for WebSocket isolation

Implements WebSocket connection isolation in the remote fetcher
to prevent real-time communication threats.

Closes #123
```

```bash
fix(sanitizer): correctly handle nested event handlers

Fixed issue where nested onclick handlers in SVG elements
were not being removed during sanitization.

Fixes #456
```

```bash
docs(readme): update installation instructions

Added troubleshooting section for common Playwright
installation issues on Windows.
```

## Pull Request Process

### Before Submitting

1. **Update your branch**

```bash
git checkout develop
git pull origin develop
git checkout feature/your-feature
git rebase develop
```

2. **Run the full test suite**

```bash
pytest tests/ -v
```

3. **Check code quality**

```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy engine/ api/ client/
```

4. **Update documentation**
   - Update README.md if adding features
   - Add docstrings to new functions
   - Update ARCHITECTURE.md for design changes

### Pull Request Template

When creating a PR, include:

**Title:** Clear, descriptive title following commit message format

**Description:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Closes #issue_number
```

### Review Process

1. At least one maintainer must approve
2. All CI checks must pass
3. Code coverage must not decrease
4. No merge conflicts with target branch

## Security Vulnerabilities

**Do NOT open public issues for security vulnerabilities.**

Please report security issues to: security@example.com

See [SECURITY.md](SECURITY.md) for full security policy.

## Project Structure

When adding new components, follow this structure:

```
browser_isolation/
├── engine/              # Core isolation logic
├── api/                 # REST API endpoints
├── client/              # Dashboard UI
├── cli/                 # Command-line interface
├── headless/            # Browser management
├── logging_mod/         # Audit logging
├── reporting/           # Report generation
├── config/              # Configuration files
├── tests/               # Test suite
└── examples/            # Example data
```

## Development Tips

### Local Testing with Docker

```bash
# Build and run containers
docker-compose up --build

# Run tests in container
docker-compose run api pytest tests/ -v

# Access logs
docker-compose logs -f api
```

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python api/server.py
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Getting Help

- **Documentation**: Check README.md and ARCHITECTURE.md
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Chat**: Join our community chat (if available)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in project documentation

Thank you for contributing to making the web safer! 🛡️

