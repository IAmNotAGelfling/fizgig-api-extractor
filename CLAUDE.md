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

# Extract with plain text descriptions (strips markdown)
fizgig-api-extractor extract <input_file> -o output.json -f json --plain-text

# Extract with custom HTML template
fizgig-api-extractor extract <input_file> -o output.html -f html --template custom.html

# Fetch from URL
fizgig-api-extractor extract https://api.example.com/openapi.json

# Fetch with authentication headers
fizgig-api-extractor extract https://api.example.com/spec.json \
  --header "Authorization: Bearer token123" \
  --header "X-API-Version: v2"

# Fetch and save locally
fizgig-api-extractor extract https://api.example.com/spec.yaml --save-url
fizgig-api-extractor extract https://api.example.com/spec --save-url custom.json

# Use config file for batch exports
fizgig-api-extractor extract --config .fizgig-config.json

# Use config with CLI overrides
fizgig-api-extractor extract --config myconfig.json \
  --header "Authorization: Bearer token" \
  -o override-output.html

# Display tree view with parameters
fizgig-api-extractor tree <input_file> --params

# Convert OpenAPI to Postman
fizgig-api-extractor convert <openapi_file> <output_postman_file>

# Initialize with example config and template
fizgig-api-extractor init
fizgig-api-extractor init --config-only
fizgig-api-extractor init --template-only
fizgig-api-extractor init --output-dir ./my-project

# Validate config file
fizgig-api-extractor validate-config .fizgig-config.json
fizgig-api-extractor validate-config  # Auto-discovers .fizgig-config.json
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

- **cli.py**: Typer-based CLI interface with five commands (extract, convert, tree, init, validate-config)
- **loader.py**: File I/O and automatic format detection, URL support
- **fetcher.py**: HTTP client for fetching API specs from URLs with custom headers
- **parser_postman.py**: Recursively walks Postman folder/item hierarchy
- **parser_openapi.py**: Walks OpenAPI paths and operations, extracts parameters from multiple locations
- **exporter.py**: Exports to markdown, csv, json, html formats with field mapping support
- **field_mapper.py**: Field selection, renaming, and nested field access for CSV/JSON exports
- **templating.py**: Mustache template rendering for HTML exports
- **config.py**: JSON config file handling, validation, and batch export execution
- **converter.py**: OpenAPI → Postman collection conversion
- **treeview.py**: Rich-based tree display with color-coded HTTP methods
- **utils.py**: Helper functions like `safe_get()` for nested dict access
- **resources/templates/default.html**: Default Mustache template for HTML exports

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
- Uses `responses` library for mocking HTTP requests in URL tests
- Fixture files in `tests/fixtures/`: `sample_postman.json`, `sample_openapi.yaml`
- Test coverage: 212+ tests across all modules

## New Features (v1.0.1+)

### URL Support (fetcher.py)

Fetch API specifications directly from URLs:
- Supports HTTP/HTTPS with custom headers for authentication
- Auto-detects JSON/YAML from content-type or URL extension
- Optional save functionality to persist fetched specs locally
- Configurable timeout (default 30s)
- Uses `requests` library for HTTP operations

```python
from api_extractor.fetcher import fetch_from_url, load_from_url

# Fetch with custom headers
content, format_type = fetch_from_url(
    "https://api.example.com/spec.json",
    headers={"Authorization": "Bearer token"}
)

# Fetch and load as dict
data, format_type = load_from_url("https://api.example.com/spec.yaml")
```

### Field Mapping (field_mapper.py)

Customize output fields for CSV and JSON exports:
- **Field selection** - Only export specified fields
- **Field renaming** - Custom output names (e.g., `method` → `HTTP Method`)
- **Nested field access** - Dot notation for metadata (e.g., `metadata.deprecated`)
- **Format-specific** - Different mappings per export format

```python
from api_extractor.field_mapper import apply_field_mapping

field_map = {
    "method": "HTTP Method",
    "path": "Endpoint",
    "metadata.deprecated": "Deprecated"
}
transformed = apply_field_mapping(endpoints, field_map)
```

### HTML Templating (templating.py)

Mustache/Handlebars templating for HTML exports:
- Custom templates with full control over styling
- Default template included in package resources
- Template data includes: total_endpoints, groups, endpoints
- Markdown-to-HTML conversion for descriptions
- Path cleaning (removes Postman template variables)

Template variables available:
- `{{total_endpoints}}` - Total endpoint count
- `{{source_file}}` - Input file name
- `{{source_format}}` - Detected format (postman/openapi)
- `{{generated_at}}` - Timestamp
- `{{#groups}}...{{/groups}}` - Iterate over endpoint groups
- `{{#endpoints}}...{{/endpoints}}` - Iterate over endpoints in group

### Configuration Files (config.py)

JSON-based configuration for batch processing:
- **Auto-discovery** - Looks for `.fizgig-config.json` in CWD
- **Multiple exports** - Single input, multiple output formats
- **Field mapping** - Per-export field customization
- **CLI overrides** - Command-line flags override config values
- **Validation** - Deep validation of config structure and file references
- **Path resolution** - Relative paths resolved from config directory

Config structure:
```json
{
  "input": "api.json",
  "headers": {"Authorization": "Bearer token"},
  "exports": [
    {
      "format": "markdown",
      "output": "docs/api.md"
    },
    {
      "format": "csv",
      "output": "data.csv",
      "delimiter": ",",
      "quoting": "minimal",
      "fields": {"method": "Method", "path": "Path"}
    },
    {
      "format": "json",
      "output": "data.json",
      "plain_text": false,
      "fields": {"name": "endpoint_name"}
    },
    {
      "format": "html",
      "output": "docs.html",
      "template": "templates/custom.html"
    }
  ]
}
```

See [docs/CONFIG.md](docs/CONFIG.md) for comprehensive documentation.

### CSV Customization

CSV exports now support:
- **Delimiters**: `,`, `;`, `\t`, or any custom string
- **Quoting modes**: `minimal`, `all`, `nonnumeric`, `none`
- **Field mapping**: Select and rename columns

### Init and Validate Commands

**init command** - Initialize project with example config and template:
```bash
fizgig-api-extractor init                    # Both config and template
fizgig-api-extractor init --config-only      # Only config
fizgig-api-extractor init --template-only    # Only template
fizgig-api-extractor init --output-dir ./dir # Custom directory
```

**validate-config command** - Validate config without running exports:
```bash
fizgig-api-extractor validate-config myconfig.json  # Specific file
fizgig-api-extractor validate-config                # Auto-discover
```

Validation checks:
- JSON syntax and structure
- Required fields (input, exports)
- Export format validity
- Input file existence (local files)
- Template file existence
- Provides detailed error messages with suggestions
