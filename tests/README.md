# MediaWiki Migration Tools - Test Suite

This directory contains comprehensive tests for all MediaWiki migration tools. The test suite uses pytest and includes unit tests, integration tests, and mocked API interactions.

## Quick Start

### Install Test Dependencies

```bash
# Install test-specific dependencies
pip install -r tests/requirements-test.txt

# Or install all dependencies including main project deps
pip install -r requirements.txt -r migration/requirements.txt -r tests/requirements-test.txt
```

### Run All Tests

```bash
# Simple test run
python tests/run_tests.py

# Or use pytest directly
python -m pytest tests/ -v
```

## Test Structure

### Test Files

- `conftest.py` - Shared fixtures and pytest configuration
- `test_getting_started.py` - Tests for interactive setup script
- `test_migration_planner.py` - Tests for migration analysis tool
- `test_azure_devops_migrator.py` - Tests for main migration script
- `test_content_previewer.py` - Tests for content preview tool
- `test_validation_tool.py` - Tests for post-migration validation
- `test_mediawiki_import.py` - Tests for template import tool

### Test Categories

Tests are marked with categories for selective execution:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests with multiple components
- `@pytest.mark.slow` - Longer-running tests
- `@pytest.mark.network` - Tests requiring network access (disabled in CI)
- `@pytest.mark.cli` - Command-line interface tests
- `@pytest.mark.api` - API interaction tests

## Running Specific Tests

### Run Tests by Category

```bash
# Run only fast unit tests
python -m pytest tests/ -m "unit"

# Run integration tests
python -m pytest tests/ -m "integration"

# Exclude slow tests
python -m pytest tests/ -m "not slow"
```

### Run Tests for Specific Module

```bash
# Test only the migration planner
python -m pytest tests/test_migration_planner.py -v

# Test only API-related functionality
python -m pytest tests/ -m "api" -v
```

### Run Tests with Coverage

```bash
# Generate coverage report
python -m pytest tests/ --cov=migration --cov=templates --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=migration --cov=templates --cov-report=html
```

## Test Features

### Comprehensive Mocking

All tests use mocked APIs and external dependencies:

- **Azure DevOps API**: Fully mocked with realistic response data
- **MediaWiki API**: Complete login/edit/query flow simulation
- **File Operations**: Temporary directories and mocked file I/O
- **Network Requests**: No actual HTTP requests made during testing
- **Environment Variables**: Isolated test environments

### Fixtures Available

The `conftest.py` provides many useful fixtures:

- `mock_env_vars` - Complete set of environment variables
- `mock_azure_api_response` - Azure DevOps API response data
- `mock_mediawiki_api_response` - MediaWiki API response data
- `sample_markdown_content` - Example markdown for conversion testing
- `sample_mediawiki_content` - Example MediaWiki content for validation
- `temp_directory` - Temporary directory for file operations
- `temp_template_files` - Pre-created template files for testing
- `complex_wiki_structure` - Multi-page wiki structure for comprehensive testing

### Error Handling Tests

All tools include comprehensive error handling tests:

- Network connectivity issues
- API authentication failures
- Rate limiting scenarios
- Malformed responses
- File permission errors
- Invalid configuration
- Edge cases and boundary conditions

## Writing New Tests

### Test File Template

```python
#!/usr/bin/env python3
"""
Tests for new_module.py - Description of the module.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the module to test
from new_module import SomeClass


@pytest.mark.unit
class TestSomeClass:
    """Test SomeClass functionality."""
    
    def test_some_method_success(self):
        """Test successful method execution."""
        instance = SomeClass()
        result = instance.some_method("test_input")
        assert result == "expected_output"
    
    def test_some_method_error_handling(self):
        """Test method error handling."""
        instance = SomeClass()
        with pytest.raises(ValueError, match="Invalid input"):
            instance.some_method("invalid_input")


@pytest.mark.integration
class TestSomeClassIntegration:
    """Test SomeClass integration scenarios."""
    
    def test_integration_with_other_components(self, mock_env_vars):
        """Test integration with other system components."""
        # Integration test code here
        pass
```

### Mock Usage Patterns

```python
# Mock environment variables
with patch.dict(os.environ, mock_env_vars):
    result = function_that_uses_env()

# Mock API requests
with patch.object(client, '_make_request') as mock_request:
    mock_request.return_value = {"success": True}
    result = client.some_api_call()

# Mock file operations
with patch('builtins.open', mock_open(read_data='file content')):
    result = function_that_reads_file()
```

## Continuous Integration

The test suite is designed to run in CI environments:

- All external dependencies are mocked
- No network access required
- Temporary files are properly cleaned up
- Exit codes indicate success/failure
- Coverage reports can be generated

### CI Command

```bash
# Recommended CI test command
python -m pytest tests/ -v --tb=short --cov=migration --cov=templates --cov-report=xml
```

## Troubleshooting

### Common Issues

**ImportError for migration modules**
```bash
# Make sure you're in the project root directory
cd /path/to/development-toolbox-mediawiki-tools
python -m pytest tests/
```

**Missing test dependencies**
```bash
pip install -r tests/requirements-test.txt
```

**Tests failing due to path issues**
```bash
# Use the test runner which handles paths correctly
python tests/run_tests.py
```

**Coverage not including all files**
```bash
# Run from project root with explicit coverage paths
python -m pytest tests/ --cov=migration --cov=templates --cov=getting_started.py
```

### Debug Mode

Run tests with more verbose output:

```bash
# Maximum verbosity
python -m pytest tests/ -vvv --tb=long

# Stop on first failure
python -m pytest tests/ -x

# Run specific test with output
python -m pytest tests/test_migration_planner.py::TestMigrationPlanner::test_init_success -v -s
```

## Contributing

When adding new functionality:

1. **Write tests first** (TDD approach recommended)
2. **Mock all external dependencies** (APIs, file system, network)
3. **Test error conditions** as well as success paths
4. **Use appropriate test markers** (`@pytest.mark.unit`, etc.)
5. **Update this README** if adding new test patterns or fixtures
6. **Ensure all tests pass** before submitting changes

### Test Coverage Goals

- **Unit tests**: >95% line coverage
- **Integration tests**: All major workflows covered  
- **Error handling**: All exception paths tested
- **Edge cases**: Boundary conditions and corner cases covered