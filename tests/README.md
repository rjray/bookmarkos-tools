# BookmarkOS Tools Test Suite

This directory contains the test suite for BookmarkOS Tools, organized to support comprehensive testing of the bookmark processing and analysis functionality.

## Test Structure

```text
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared pytest fixtures and configuration
├── helpers.py                  # Test utilities and helper functions
├── fixtures/                   # Test data files
│   ├── sample_bookmarks.html   # Well-formed BookmarkOS HTML export
│   ├── malformed_bookmarks.html # Malformed HTML for error testing
│   ├── empty_bookmarks.html    # Empty bookmark file
│   └── sample_bookmarks.json   # Sample JSON bookmark data
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── bookmarkos/            # Tests for library modules
│   │   ├── __init__.py
│   │   ├── data/              # Tests for data classes
│   │   │   ├── __init__.py
│   │   │   ├── test_bookmarks.py    # (to be created)
│   │   │   └── test_metrics.py      # (to be created)
│   │   ├── test_parser.py           # (to be created)
│   │   ├── test_json_io.py          # (to be created)
│   │   └── test_metrics.py          # (to be created)
│   └── bin/                   # Tests for CLI tools
│       ├── __init__.py
│       ├── test_bookmarks2json.py   # (to be created)
│       ├── test_bookmarks_report.py # (to be created)
│       └── test_process_bookmarks.py # (to be created)
└── integration/               # Integration tests
    ├── __init__.py
    ├── test_full_workflow.py         # (to be created)
    └── test_cli_integration.py       # (to be created)
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
make install-test-deps

# Run all unit tests
make test

# Run all tests (unit + integration)
make test-all

# Run with coverage
make coverage
```

### Detailed Commands

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Tests with coverage
pytest tests/ --cov=bin/bookmarkos --cov-report=html

# Parallel execution
pytest tests/ -n auto

# Specific test categories
pytest tests/ -m parser    # Parser tests
pytest tests/ -m metrics   # Metrics tests
pytest tests/ -m io        # I/O tests
pytest tests/ -m cli       # CLI tests
```

## Test Categories (Markers)

- `unit`: Unit tests
- `integration`: Integration tests
- `slow`: Tests that take longer to run
- `parser`: HTML parser functionality
- `metrics`: Metrics calculation
- `io`: File input/output operations
- `cli`: Command-line tools

## Test Fixtures

### Available Fixtures (from conftest.py)

- `temp_dir`: Temporary directory for test files
- `sample_bookmark_html`: Well-formed BookmarkOS HTML content
- `malformed_bookmark_html`: Malformed HTML for error testing
- `sample_json_data`: Sample bookmark data in JSON format
- `mock_file_operations`: Mocked file operations
- `fixtures_dir`: Path to test fixtures directory

### Test Data Files

- `sample_bookmarks.html`: Complete, well-formed BookmarkOS export
- `malformed_bookmarks.html`: Invalid HTML for error handling tests
- `empty_bookmarks.html`: Empty bookmark file
- `sample_bookmarks.json`: JSON representation of bookmark data

## Test Helpers

The `helpers.py` module provides utilities for creating test data:

### TestDataGenerator

- `create_bookmark_dict()`: Generate bookmark dictionaries
- `create_folder_dict()`: Generate folder dictionaries
- `create_html_bookmark()`: Generate HTML bookmark markup
- `create_html_folder()`: Generate HTML folder markup

### TempFileHelper

- `create_temp_html()`: Create temporary HTML files (compressed/uncompressed)
- `create_temp_json()`: Create temporary JSON files (compressed/uncompressed)

### MockFactory

- `create_bookmark_mock()`: Create mock bookmark objects
- `create_folder_mock()`: Create mock folder objects
- `create_metrics_mock()`: Create mock metrics objects

### Assertion Helpers

- `assert_bookmark_equal()`: Assert bookmark objects match expected values
- `assert_folder_equal()`: Assert folder objects match expected values

## Writing Tests

### Example Unit Test

```python
import pytest
from bookmarkos.data.bookmarks import Bookmark
from tests.helpers import TestDataGenerator, assert_bookmark_equal

class TestBookmark:
    def test_bookmark_creation(self):
        bookmark_data = TestDataGenerator.create_bookmark_dict(
            name="Test Bookmark",
            url="https://example.com",
            tags=["test", "example"]
        )

        bookmark = Bookmark()
        # ... test bookmark functionality

        assert_bookmark_equal(bookmark, bookmark_data)
```

### Example Integration Test

```python
import pytest
from pathlib import Path
from tests.helpers import TempFileHelper

class TestFullWorkflow:
    def test_html_to_json_conversion(self, sample_bookmark_html):
        # Create temporary HTML file
        html_file = TempFileHelper.create_temp_html(sample_bookmark_html)
        json_file = html_file.with_suffix('.json')

        # Test the full conversion workflow
        # ... test implementation

        # Cleanup
        html_file.unlink()
        json_file.unlink()
```

## Configuration

### pytest Configuration (pyproject.toml)

The test suite is configured with:

- Coverage reporting (80% minimum)
- HTML coverage reports
- Test discovery patterns
- Marker definitions
- Warning filters

### CI/CD Integration

GitHub Actions workflow (`.github/workflows/tests.yml`) runs:

- Tests on multiple Python versions (3.9-3.12)
- Tests on multiple operating systems
- Code coverage reporting
- Linting and formatting checks

## Performance Testing

Use the `benchmark` marker for performance tests:

```python
@pytest.mark.benchmark
def test_large_file_parsing(benchmark):
    result = benchmark(parse_large_file, large_test_file)
    assert result is not None
```

Run benchmarks with: `make benchmark`

## Debugging Tests

```bash
# Run with debugging on failure
make test-debug

# Run with maximum verbosity
make test-verbose

# Run single test with debugging
pytest tests/unit/test_parser.py::test_specific_function -v --pdb
```

## Contributing Tests

1. Place unit tests in `tests/unit/` following the source structure
2. Place integration tests in `tests/integration/`
3. Add appropriate test markers (`@pytest.mark.parser`, etc.)
4. Use existing fixtures and helpers where possible
5. Add new fixtures to `conftest.py` if they'll be reused
6. Add test data files to `fixtures/` if needed
7. Update this README when adding new test categories or helpers
