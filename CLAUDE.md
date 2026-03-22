# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**fizgig-api-extractor** is a Python CLI tool that parses Postman collections and OpenAPI specifications, extracts API endpoints, and exports them in multiple formats (Markdown, CSV, JSON, HTML).

## Common Commands

### Development Setup
```bash
# Install package in editable mode with dev dependencies
pip install -e .
pip install -e ".[dev]"
```

### Running the CLI
```bash
# Main CLI command
fizgig-api-extractor --help

# Extract and display as tree (default)
fizgig-api-extractor extract <input_file>

# Extract and export to file
fizgig-api-extractor extract <input_file> -o <output_file> -f <format>
# Formats: markdown, csv, json, html

# Display tree view with parameters
fizgig-api-extractor tree <input_file> --params

# Convert OpenAPI to Postman
fizgig-api-extractor convert <openapi_file> <output_postman_file>
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=api_extractor

# Run specific test file
pytest tests/test_loader.py

# Run specific test
pytest tests/test_loader.py::TestDetectFormat::test_detect_postman_by_schema
```

## Architecture

### Two-Stage Parsing Pipeline

The tool uses a two-stage parsing approach:

1. **Loader Stage** (`loader.py`):
   - `load_api_file()` loads JSON/YAML files
   - `detect_format()` automatically identifies format type (Postman vs OpenAPI)
   - Detection logic:
     - **Postman**: checks for `info.schema` containing "collection" or presence of `item` list
     - **OpenAPI**: checks for `openapi` field with version 3.x or presence of `paths` object

2. **Parser Stage**:
   - `parse_postman_collection()` in `parser_postman.py` for Postman collections
   - `parse_openapi_spec()` in `parser_openapi.py` for OpenAPI specs
   - Both produce a common endpoint data structure

### Common Endpoint Data Structure

All parsers normalize to this unified structure:

```python
{
    "group": str,          # Category/folder/tag name
    "name": str,           # Endpoint name/summary
    "method": str,         # HTTP method (GET, POST, etc.)
    "path": str,           # Full URL path
    "description": str,    # Detailed description
    "params": [            # Normalized parameters
        {
            "name": str,
            "in": str,     # "path", "query", "header", "body"
            "required": bool,
            "type": str,
            "description": str
        }
    ],
    "metadata": {}         # Format-specific additional data
}
```

This common structure enables:
- Format-agnostic export functions in `exporter.py`
- Unified tree view display in `treeview.py`
- Easy extension to new input/output formats

### Module Responsibilities

- **cli.py**: Typer-based CLI interface with three commands (extract, convert, tree)
- **loader.py**: File I/O and automatic format detection
- **parser_postman.py**: Recursively walks Postman folder/item hierarchy
- **parser_openapi.py**: Walks OpenAPI paths and operations, extracts parameters from multiple locations
- **exporter.py**: Exports to markdown, csv, json, html formats
- **converter.py**: OpenAPI → Postman collection conversion
- **treeview.py**: Rich-based tree display with color-coded HTTP methods
- **utils.py**: Helper functions like `safe_get()` for nested dict access

### Windows Unicode Handling

The CLI includes Windows console encoding fixes (cli.py:34-37):
```python
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
```
This ensures Rich's Unicode characters display correctly on Windows.

## Testing

Tests use **pytest** with the following structure:
- Each module has a corresponding test file (e.g., `loader.py` → `test_loader.py`)
- Tests are organized into classes by functionality
- Uses `tempfile` for file-based tests to avoid filesystem pollution
- Fixture files in `tests/fixtures/`: `sample_postman.json`, `sample_openapi.yaml`
