# Design: URL Support, Config Files, Field Mapping, and HTML Templating

**Date:** 2026-03-24
**Status:** Approved
**Version:** 1.0.0

## Overview

This design adds four major features to fizgig-api-extractor whilst maintaining full backwards compatibility:

1. **URL Input Support** - Accept HTTP/HTTPS URLs as input with custom header support for authentication
2. **JSON Config Files** - Enable batch exports and reusable configurations with auto-discovery
3. **Field Mapping** - Allow custom field selection, renaming, and ordering for CSV/JSON exports
4. **HTML Templating** - Replace hardcoded HTML with Handlebars/Mustache templates for full customisation

## Design Principles

- **Backwards Compatible** - All existing CLI commands and Python API continue to work unchanged
- **Optional Configuration** - Config files are optional; CLI-only usage remains fully functional
- **CLI Precedence** - CLI flags override config file values
- **Simplicity** - One template file with inline CSS; avoid over-engineering
- **YAGNI** - Don't build abstractions we don't need yet

## Architecture Changes

### Current Architecture
```
loader.py → parser_*.py → exporter.py
                        → treeview.py
                        → converter.py
```

### Updated Architecture
```
fetcher.py (new) ─┐
                  ├→ loader.py → parser_*.py → field_mapper.py (new) → exporter.py
                  │                                                   → templating.py (new)
config.py (new) ──┘                                                   → treeview.py
                                                                      → converter.py
```

### New Modules

- **`fetcher.py`** - HTTP client for fetching specs from URLs
- **`config.py`** - Config file parsing and orchestration of multiple exports
- **`field_mapper.py`** - Field selection, renaming, and ordering for endpoints
- **`templating.py`** - Mustache/Handlebars template rendering for HTML

### Modified Modules

- **`loader.py`** - Add URL detection and integration with `fetcher.py`
- **`exporter.py`** - Integrate `field_mapper.py` for CSV/JSON, use `templating.py` for HTML
- **`cli.py`** - Add new flags (`--config`, `--header`, `--save-url`, `--template`) and `init` command

### Resources

- **`api_extractor/resources/templates/default.html`** - Default Mustache template with inline CSS

## Feature 1: URL Support

### Requirements

- Accept `http://` and `https://` URLs as input
- Support custom HTTP headers for authentication
- Optional: Save fetched content to local file
- Handle network errors gracefully

### Implementation

#### URL Detection (`loader.py`)

```python
def load_api_file(file_path: str, headers: dict = None, save_path: str = None) -> Tuple[Dict[str, Any], FormatType]:
    """
    Load an API specification file or URL and detect its format.

    Args:
        file_path: Path to file or HTTP(S) URL
        headers: Optional HTTP headers for URL requests
        save_path: Optional path to save URL content

    Returns:
        Tuple of (parsed_data, format_type)
    """
    if file_path.startswith('http://') or file_path.startswith('https://'):
        return load_from_url(file_path, headers, save_path)
    else:
        # Existing file loading logic
        path = Path(file_path)
        # ... rest of existing code
```

#### HTTP Fetching (`fetcher.py`)

New module for HTTP operations:

```python
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse

def fetch_from_url(url: str, headers: Optional[Dict[str, str]] = None,
                   timeout: int = 30) -> Tuple[str, str]:
    """
    Fetch content from URL.

    Args:
        url: HTTP(S) URL to fetch
        headers: Optional HTTP headers
        timeout: Request timeout in seconds

    Returns:
        Tuple of (content, detected_format)
        detected_format is 'json' or 'yaml' based on content-type or URL

    Raises:
        requests.RequestException: On network errors
        ValueError: On invalid content or status codes
    """

def save_url_content(content: str, save_path: Optional[str], url: str) -> str:
    """
    Save URL content to file.

    Args:
        content: Content to save
        save_path: Path to save to, or None to derive from URL
        url: Original URL (used to derive filename if save_path is None)

    Returns:
        Path where content was saved
    """

def load_from_url(url: str, headers: Optional[Dict[str, str]] = None,
                  save_path: Optional[str] = None) -> Tuple[Dict[str, Any], FormatType]:
    """
    Fetch, parse, and optionally save content from URL.

    Returns parsed data in same format as load_api_file.
    """
```

#### CLI Integration

New flags:
- `--header KEY:VALUE` (repeatable) - Add custom HTTP headers
- `--save-url [PATH]` - Save URL content to file (optional path)

Examples:
```bash
# Basic URL fetch
fizgig-api-extractor extract https://api.example.com/openapi.yaml

# With authentication header
fizgig-api-extractor extract https://api.example.com/spec.json \
  --header "Authorization: Bearer token123"

# Multiple headers
fizgig-api-extractor extract https://api.example.com/spec.json \
  --header "Authorization: Bearer token" \
  --header "X-API-Version: v2"

# Save to file (derives filename from URL)
fizgig-api-extractor extract https://api.example.com/openapi.yaml --save-url
# Saves to: ./openapi.yaml

# Save to specific path
fizgig-api-extractor extract https://api.example.com/spec --save-url custom.json
# Saves to: ./custom.json
```

#### Error Handling

- **Network errors**: "Failed to connect to URL: {error}"
- **HTTP errors**: "HTTP {status_code}: {reason}"
- **Invalid content**: "URL returned invalid JSON/YAML: {error}"
- **Timeout**: "Request timed out after {timeout}s"

## Feature 2: Config File System

### Requirements

- JSON config files for batch exports and reusable settings
- Auto-discovery from current directory (`.fizgig-config.json`)
- Manual specification via `--config` flag
- CLI flags override config values
- Support multiple exports in one run

### Config File Schema

```json
{
  "input": "api.json",           // File path or URL
  "headers": {                    // Optional: HTTP headers for URLs
    "Authorization": "Bearer token",
    "X-API-Key": "key123"
  },
  "exports": [                    // Array of export configurations
    {
      "format": "json",
      "output": "api.json",
      "plain_text": true,        // Format-specific: JSON
      "fields": {                 // Optional: field mapping
        "method": "HTTP Method",
        "path": "Endpoint",
        "description": "Description"
      }
    },
    {
      "format": "html",
      "output": "docs/api.html",
      "template": "templates/custom.html"  // Format-specific: HTML
    },
    {
      "format": "csv",
      "output": "api.csv"
      // No fields = all fields included
    },
    {
      "format": "markdown",
      "output": "API.md"
    }
  ]
}
```

### Implementation

#### Config Parser (`config.py`)

```python
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

class ConfigError(Exception):
    """Raised when config is invalid."""
    pass

def find_config_file() -> Optional[Path]:
    """
    Look for .fizgig-config.json in current directory.

    Returns:
        Path to config file or None if not found
    """

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load and validate config file.

    Args:
        config_path: Path to config file, or None for auto-discovery

    Returns:
        Validated config dict

    Raises:
        ConfigError: If config is invalid
        FileNotFoundError: If specified config not found
    """

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate config schema.

    Raises:
        ConfigError: With helpful message about what's wrong
    """

def run_exports(config: Dict[str, Any]) -> None:
    """
    Execute all exports defined in config.

    Loads input once, then runs each export sequentially.
    """
```

#### CLI Integration

Config discovery:
1. Check for `--config` flag → use specified path
2. Check for `.fizgig-config.json` in CWD → use if found
3. No config → use CLI flags only (existing behavior)

CLI flags override config:
```bash
# Config says format=csv, CLI overrides to json
fizgig-api-extractor extract api.json --format json
```

### Validation

Config validation checks:
- `input` field is present
- `exports` is an array with at least one item
- Each export has `format` and `output`
- Format is one of: markdown, csv, json, html
- Field mappings (if present) are valid objects
- Template paths (if present) exist

Error messages include:
- Field path (e.g., "exports[0].format")
- What's wrong (e.g., "must be one of: markdown, csv, json, html")
- Suggestion (e.g., "Did you mean 'markdown'?")

## Feature 3: Field Mapping

### Requirements

- Custom field selection (include only specified fields)
- Field renaming (change output field names)
- Field ordering (control order in output)
- Support nested field access (e.g., `metadata.deprecated`)
- Apply only to CSV and JSON formats

### Implementation

#### Field Mapper (`field_mapper.py`)

```python
from typing import Dict, Any, List, Optional

def apply_field_mapping(endpoints: List[Dict[str, Any]],
                       field_map: Optional[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Transform endpoints based on field mapping.

    Args:
        endpoints: List of endpoint dictionaries
        field_map: Mapping of original_field -> new_field_name
                   If None, returns endpoints unchanged

    Returns:
        Transformed endpoint list with only mapped fields

    Example:
        field_map = {
            "method": "HTTP Method",
            "path": "Endpoint",
            "metadata.deprecated": "Deprecated"
        }

        Result: Only includes those 3 fields with new names
    """

def get_nested_field(obj: Dict[str, Any], field_path: str) -> Any:
    """
    Get value from nested dict using dot notation.

    Args:
        obj: Dictionary to extract from
        field_path: Dot-separated path (e.g., "metadata.deprecated")

    Returns:
        Field value or None if not found
    """
```

#### Behavior

**If no field mapping specified:**
- Include all fields (current behavior)
- Fields appear in their natural order

**If field mapping specified:**
- Only include mapped fields
- Fields appear in order specified in mapping
- Rename fields to new names
- Support nested access with dot notation

**Examples:**

Minimal mapping:
```json
{
  "fields": {
    "method": "Method",
    "path": "Path"
  }
}
```
Output: Only method and path fields, renamed

Full mapping:
```json
{
  "fields": {
    "method": "HTTP Method",
    "path": "Endpoint",
    "name": "Name",
    "description": "Description",
    "metadata.deprecated": "Deprecated"
  }
}
```

#### Integration with Exporters

Modify `exporter.py`:

```python
def export_csv(endpoints: List[Dict[str, Any]], output_path: str,
               field_map: Optional[Dict[str, str]] = None) -> None:
    """Export with optional field mapping."""
    if field_map:
        endpoints = apply_field_mapping(endpoints, field_map)
    # ... rest of CSV export logic

def export_json(endpoints: List[Dict[str, Any]], output_path: str,
                pretty: bool = True, plain_text: bool = False,
                field_map: Optional[Dict[str, str]] = None) -> None:
    """Export with optional field mapping."""
    if field_map:
        endpoints = apply_field_mapping(endpoints, field_map)
    # ... rest of JSON export logic
```

**Note:** Field mapping does NOT apply to:
- HTML exports (templates have full data access)
- Markdown exports (fixed structure)
- Tree view (display only)

## Feature 4: HTML Templating

### Requirements

- Replace hardcoded HTML generation with templates
- Use Mustache/Handlebars for templating
- Support custom templates via config or CLI flag
- Include default template as resource
- CSS inline in template (one file, no external dependencies)

### Template Engine

Use **`pystache`** or **`chevron`** library:
- Simple Mustache implementation
- Logic-less templates
- No complex helpers needed
- Lightweight

Add to `requirements.txt`:
```
pystache>=0.6.5
```

### Template Data Structure

Templates receive:

```python
{
    "total_endpoints": 42,
    "generated_at": "2026-03-24T10:30:00Z",
    "source_file": "api.json",
    "source_format": "openapi",

    # Grouped structure (like current HTML)
    "groups": [
        {
            "name": "Users",
            "count": 4,
            "endpoints": [
                {
                    "name": "List all users",
                    "method": "GET",
                    "path": "/api/users",
                    "description": "<p>Retrieve paginated list...</p>",  # Already HTML
                    "deprecated": false,
                    "params": [
                        {
                            "name": "page",
                            "in": "query",
                            "type": "integer",
                            "required": false,
                            "description": "Page number"
                        }
                    ]
                }
            ]
        }
    ],

    # Flat structure (alternative view)
    "endpoints": [
        {
            "group": "Users",
            "name": "List all users",
            "method": "GET",
            # ... same fields as above
        }
    ]
}
```

Both grouped and flat structures provided - template chooses which to use.

### Default Template

Convert current `export_html()` output to Mustache template:

**`api_extractor/resources/templates/default.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Endpoints</title>
    <style>
        /* Current CSS from exporter.py */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            /* ... rest of current CSS ... */
        }
    </style>
</head>
<body>
    <h1>API Endpoints</h1>
    <div class="summary">
        <strong>Total endpoints:</strong> {{total_endpoints}}<br>
        <strong>Generated:</strong> {{generated_at}}<br>
        <strong>Source:</strong> {{source_file}} ({{source_format}})
    </div>

    {{#groups}}
    <h2>{{name}}</h2>
    <p><em>{{count}} endpoint(s)</em></p>

    {{#endpoints}}
    <div class="endpoint">
        <div class="endpoint-header">
            <span class="method {{method}}">{{method}}</span>
            <span class="path">{{path}}</span>
            {{#deprecated}}
            <span class="deprecated">DEPRECATED</span>
            {{/deprecated}}
        </div>
        <div class="endpoint-name">{{name}}</div>

        {{#description}}
        <div class="description">{{{description}}}</div>
        {{/description}}

        {{#params}}
        <table>
            <thead>
                <tr>
                    <th>Parameter</th>
                    <th>In</th>
                    <th>Type</th>
                    <th>Required</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {{#params}}
                <tr>
                    <td class="param-name">{{name}}</td>
                    <td><span class="badge {{in}}">{{in}}</span></td>
                    <td>{{type}}</td>
                    <td class="{{#required}}required{{/required}}{{^required}}optional{{/required}}">
                        {{#required}}Yes{{/required}}{{^required}}No{{/required}}
                    </td>
                    <td>{{description}}</td>
                </tr>
                {{/params}}
            </tbody>
        </table>
        {{/params}}
    </div>
    {{/endpoints}}
    {{/groups}}
</body>
</html>
```

### Implementation

#### Templating Module (`templating.py`)

```python
import pystache
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import importlib.resources

def load_default_template() -> str:
    """
    Load default template from package resources.

    Returns:
        Template content as string
    """

def load_custom_template(template_path: str, config_dir: Optional[Path] = None) -> str:
    """
    Load custom template with path resolution.

    Path resolution order:
    1. Relative to config file directory (if config_dir provided)
    2. Relative to current working directory
    3. Absolute path

    Args:
        template_path: Path to template file
        config_dir: Directory containing config file (for relative resolution)

    Returns:
        Template content

    Raises:
        FileNotFoundError: If template not found
    """

def prepare_template_data(endpoints: List[Dict[str, Any]],
                         source_file: str,
                         source_format: str) -> Dict[str, Any]:
    """
    Prepare data structure for template rendering.

    Creates both grouped and flat endpoint structures.
    """

def render_html_template(endpoints: List[Dict[str, Any]],
                        source_file: str,
                        source_format: str,
                        template_path: Optional[str] = None,
                        config_dir: Optional[Path] = None) -> str:
    """
    Render HTML using template.

    Args:
        endpoints: List of endpoints
        source_file: Input file name
        source_format: Format type (postman/openapi)
        template_path: Optional custom template path
        config_dir: Config directory for path resolution

    Returns:
        Rendered HTML string
    """
```

#### Exporter Integration

Modify `export_html()` in `exporter.py`:

```python
def export_html(endpoints: List[Dict[str, Any]],
                output_path: str,
                template_path: Optional[str] = None,
                config_dir: Optional[Path] = None) -> None:
    """
    Export endpoints to HTML format using template.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path
        template_path: Optional custom template path
        config_dir: Config directory for template resolution
    """
    from api_extractor.templating import render_html_template

    html = render_html_template(
        endpoints=endpoints,
        source_file=Path(output_path).stem,
        source_format="unknown",  # Could be passed through
        template_path=template_path,
        config_dir=config_dir
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
```

#### CLI Integration

New flag:
- `--template PATH` - Use custom template for HTML export

Example:
```bash
fizgig-api-extractor extract api.json -o api.html -f html \
  --template templates/custom.html
```

## Feature 5: Init Command

### Requirements

- Export default template and example config
- Help users get started with customisation
- Create necessary directories
- Prevent accidental overwrites

### Command Syntax

```bash
# Export everything (default)
fizgig-api-extractor init

# Export only config
fizgig-api-extractor init --config-only

# Export only template
fizgig-api-extractor init --template-only

# Specify output directory
fizgig-api-extractor init --output-dir path/to/dir
```

### Default Behavior

When run without flags, exports:
1. `.fizgig-config.json` → Current directory
2. `templates/default.html` → `./templates/` subdirectory

### Example Config Content

```json
{
  "// Description": "Example configuration for fizgig-api-extractor",
  "// Documentation": "https://github.com/IAmNotAGelfling/fizgig-api-extractor",

  "input": "api.json",

  "// headers": "Optional: Custom HTTP headers for URL inputs",
  "headers": {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
  },

  "exports": [
    {
      "// Export 1": "Markdown documentation",
      "format": "markdown",
      "output": "API.md"
    },
    {
      "// Export 2": "JSON with custom fields",
      "format": "json",
      "output": "api-summary.json",
      "plain_text": true,
      "fields": {
        "method": "HTTP Method",
        "path": "Endpoint",
        "name": "Name",
        "description": "Description"
      }
    },
    {
      "// Export 3": "CSV with all fields",
      "format": "csv",
      "output": "api-endpoints.csv"
    },
    {
      "// Export 4": "HTML with custom template",
      "format": "html",
      "output": "api.html",
      "template": "templates/default.html"
    }
  ]
}
```

### Implementation

Add to `cli.py`:

```python
@app.command()
def init(
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Output directory (default: current directory)"
    ),
    config_only: bool = typer.Option(
        False,
        "--config-only",
        help="Export only config file"
    ),
    template_only: bool = typer.Option(
        False,
        "--template-only",
        help="Export only template"
    )
) -> None:
    """
    Initialize customisation files (config and template).

    Examples:

        # Export everything
        fizgig-api-extractor init

        # Export to specific directory
        fizgig-api-extractor init --output-dir my-project

        # Export only config
        fizgig-api-extractor init --config-only
    """
```

### Behavior Details

1. **Check existing files**: Prompt before overwriting
2. **Create directories**: Create `templates/` if needed
3. **Show success messages**:
   ```
   ✓ Created .fizgig-config.json
   ✓ Created templates/default.html

   Next steps:
     1. Edit .fizgig-config.json to configure exports
     2. Customize templates/default.html for HTML styling
     3. Run: fizgig-api-extractor extract api.json
   ```

## Feature 6: Validate Config Command

### Requirements

- Validate config file without running exports
- Provide clear error messages for invalid configs
- Check that referenced files (templates, input) exist
- Useful for CI/CD and development workflows

### Command Syntax

```bash
# Validate auto-discovered config
fizgig-api-extractor validate-config

# Validate specific config file
fizgig-api-extractor validate-config path/to/config.json

# Alternative shorter alias
fizgig-api-extractor validate path/to/config.json
```

### Validation Checks

1. **JSON Syntax**: Valid JSON format
2. **Schema Validation**:
   - Required fields present (`input`, `exports`)
   - Exports is non-empty array
   - Each export has `format` and `output`
   - Format is valid (markdown, csv, json, html)
3. **Referenced Files**:
   - Input file exists (if local path, not URL)
   - Template files exist (for HTML exports)
4. **Field Mappings**: Valid objects with string keys/values
5. **Headers**: Valid object structure

### Output Examples

**Valid config:**
```bash
$ fizgig-api-extractor validate-config
✓ Config file is valid: .fizgig-config.json
✓ Input file exists: api.json
✓ All templates found (1)
✓ 4 exports configured

Configuration is valid and ready to use.
```

**Invalid config:**
```bash
$ fizgig-api-extractor validate-config custom-config.json
✗ Config validation failed: custom-config.json

Error at exports[1].format:
  Invalid format 'htm' - must be one of: markdown, csv, json, html
  Did you mean 'html'?

Error at exports[2].template:
  Template file not found: templates/missing.html
  Searched in:
    - /path/to/project/templates/missing.html
    - /current/directory/templates/missing.html

Fix these errors and try again.
```

### Implementation

Add to `cli.py`:

```python
@app.command("validate-config")
def validate_config(
    config_path: Optional[str] = typer.Argument(
        None,
        help="Path to config file (default: .fizgig-config.json in CWD)"
    )
) -> None:
    """
    Validate config file without running exports.

    Checks JSON syntax, schema validity, and referenced file existence.

    Examples:

        # Validate auto-discovered config
        fizgig-api-extractor validate-config

        # Validate specific config
        fizgig-api-extractor validate-config my-config.json
    """
    try:
        from api_extractor.config import load_config, validate_config_deep

        # Load and validate config
        if config_path is None:
            config_path = find_config_file()
            if config_path is None:
                console_err.print("[red]✗[/red] No config file found in current directory")
                console_err.print("Expected: .fizgig-config.json")
                raise typer.Exit(1)

        console.print(f"[bold]Validating[/bold] {config_path}...")
        config = load_config(config_path)

        # Deep validation with file checks
        validation_result = validate_config_deep(config, Path(config_path).parent)

        if validation_result["valid"]:
            console.print(f"[green]✓[/green] Config file is valid: {config_path}")
            console.print(f"[green]✓[/green] Input: {config['input']}")

            template_count = sum(1 for e in config['exports'] if 'template' in e)
            if template_count > 0:
                console.print(f"[green]✓[/green] All templates found ({template_count})")

            console.print(f"[green]✓[/green] {len(config['exports'])} exports configured")
            console.print("\n[bold green]Configuration is valid and ready to use.[/bold green]")
        else:
            console_err.print(f"[red]✗[/red] Config validation failed: {config_path}\n")

            for error in validation_result["errors"]:
                console_err.print(f"[red]Error at {error['path']}:[/red]")
                console_err.print(f"  {error['message']}")
                if "suggestion" in error:
                    console_err.print(f"  [dim]{error['suggestion']}[/dim]")
                console_err.print()

            console_err.print("[yellow]Fix these errors and try again.[/yellow]")
            raise typer.Exit(1)

    except FileNotFoundError as e:
        console_err.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console_err.print(f"[red]✗[/red] Invalid JSON in {config_path}:")
        console_err.print(f"  Line {e.lineno}: {e.msg}")
        raise typer.Exit(1)
    except Exception as e:
        console_err.print(f"[red]✗[/red] Validation error: {e}")
        raise typer.Exit(1)
```

### Additional config.py Functions

Add to `config.py`:

```python
def validate_config_deep(config: Dict[str, Any], config_dir: Path) -> Dict[str, Any]:
    """
    Deep validation including file existence checks.

    Args:
        config: Config dictionary
        config_dir: Directory containing config file

    Returns:
        {
            "valid": bool,
            "errors": [
                {
                    "path": "exports[0].format",
                    "message": "Invalid format 'htm'",
                    "suggestion": "Did you mean 'html'?"
                }
            ]
        }
    """
```

### Use Cases

**Development workflow:**
```bash
# Edit config
vim .fizgig-config.json

# Validate before running
fizgig-api-extractor validate-config

# If valid, run exports
fizgig-api-extractor extract api.json
```

**CI/CD pipeline:**
```bash
# Validate config as part of build
fizgig-api-extractor validate-config || exit 1

# Generate documentation
fizgig-api-extractor extract $API_SPEC
```

## Testing Strategy

### Unit Tests

**`test_fetcher.py`:**
- Mock HTTP requests with `responses` library
- Test successful fetch (JSON, YAML)
- Test error cases (404, timeout, invalid content)
- Test header injection
- Test save functionality

**`test_config.py`:**
- Test config loading and validation
- Test auto-discovery
- Test invalid config errors
- Test CLI override behaviour

**`test_field_mapper.py`:**
- Test field selection
- Test field renaming
- Test field ordering
- Test nested field access
- Test with missing fields

**`test_templating.py`:**
- Test default template loading
- Test custom template loading
- Test path resolution
- Test data preparation (grouped/flat)
- Test rendering

### Integration Tests

**`test_url_integration.py`:**
- End-to-end URL fetch and parse
- Test with real test server (or mock)

**`test_config_integration.py`:**
- Test full config-based workflow
- Test multiple exports
- Test CLI overrides

**`test_template_integration.py`:**
- Test HTML export with custom template
- Verify output matches expected structure

### Manual Testing

- Test with real OpenAPI specs from public URLs
- Test with real Postman collections
- Verify HTML templates render correctly in browsers
- Test config files with various combinations

## Migration Path

### Version 1.0.x → 1.1.0

All existing functionality continues to work:
- Existing CLI commands unchanged
- Python API unchanged
- No breaking changes

New features are opt-in:
- Use URLs by providing URL instead of file path
- Use config by creating `.fizgig-config.json`
- Use custom templates by providing `--template` flag

### Deprecations

None. All existing features remain supported.

## Documentation Updates

### README.md

Add sections:
- URL Support (with authentication examples)
- Config Files (with full example)
- Field Mapping (with examples)
- HTML Templating (with customisation guide)
- Init Command
- Validate Config Command

### CLAUDE.md

Update "Common Commands" section with new flags, init command, and validate-config command.

### New Documentation Files

Create `docs/` directory with:
- `CONFIG.md` - Complete config file reference
- `TEMPLATING.md` - Template customisation guide with examples
- `EXAMPLES.md` - Real-world usage examples

## Dependencies

Add to `requirements.txt`:
```
requests>=2.31.0
pystache>=0.6.5
```

Add to `setup.py`:
```python
install_requires=[
    'typer>=0.9.0',
    'rich>=13.0.0',
    'pyyaml>=6.0',
    'mistune>=3.0.0',
    'requests>=2.31.0',
    'pystache>=0.6.5',
],
```

## Implementation Checklist

### Phase 1: URL Support
- [ ] Create `fetcher.py` module
- [ ] Add URL detection to `loader.py`
- [ ] Add CLI flags (`--header`, `--save-url`)
- [ ] Write tests
- [ ] Update documentation

### Phase 2: HTML Templating
- [ ] Create `templating.py` module
- [ ] Create default template resource
- [ ] Modify `exporter.py` to use templating
- [ ] Add `--template` CLI flag
- [ ] Write tests
- [ ] Update documentation

### Phase 3: Field Mapping
- [ ] Create `field_mapper.py` module
- [ ] Integrate with CSV/JSON exporters
- [ ] Write tests
- [ ] Update documentation

### Phase 4: Config System
- [ ] Create `config.py` module
- [ ] Implement auto-discovery and validation
- [ ] Integrate with CLI
- [ ] Write tests
- [ ] Update documentation

### Phase 5: Init Command
- [ ] Implement init command in `cli.py`
- [ ] Create example config content
- [ ] Write tests
- [ ] Update documentation

### Phase 6: Validate Config Command
- [ ] Implement validate-config command in `cli.py`
- [ ] Add deep validation function to `config.py`
- [ ] Write tests for validation scenarios
- [ ] Update documentation

### Phase 7: Integration & Polish
- [ ] Integration tests for all features
- [ ] Manual testing with real specs
- [ ] Documentation review
- [ ] Update CHANGELOG.md
- [ ] Version bump to 1.1.0

## Security Considerations

### URL Fetching
- Validate URL schemes (only http/https)
- Set reasonable timeout (30s default)
- Limit response size (e.g., 10MB max)
- No automatic redirects to file:// or other schemes
- Headers should not be logged in normal output

### Template Rendering
- Use logic-less templates (Mustache) - no code execution
- Sanitize user input if ever added to templates
- Templates are static files, not executable code

### Config Files
- Validate config schema strictly
- Don't execute arbitrary code from config
- Warn if config contains sensitive data (API keys in examples)

## Future Enhancements

### Not in This Design (YAGNI)

These could be added later if needed:
- Profile support in config (multiple named configs)
- Template inheritance/includes
- More complex field transformations
- Authentication methods beyond headers (OAuth, etc.)
- Caching of URL fetches
- Config file merging
- YAML config support
- Plugin system

## Summary

This design adds powerful features whilst maintaining simplicity:
- URL support makes it easy to work with online specs
- Config files enable batch processing and team sharing
- Field mapping gives control over CSV/JSON output
- HTML templating allows full customisation
- Validate config command ensures correctness before running
- Init command helps users get started quickly

All features are optional and backwards compatible. The implementation follows YAGNI principles and extends the existing architecture without over-engineering.
