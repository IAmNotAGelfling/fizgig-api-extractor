# Configuration File Guide

fizgig-api-extractor supports JSON configuration files for batch processing and repeated exports. This allows you to define multiple export formats and settings in one place.

## Quick Start

Create a config file with the `init` command:

```bash
fizgig-api-extractor init
```

This creates `.fizgig-config.json` in the current directory with example configuration and `templates/default.html`.

## Configuration Structure

```json
{
  "input": "path/to/api-spec.json",
  "headers": {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
  },
  "exports": [
    {
      "format": "markdown",
      "output": "docs/api-endpoints.md"
    },
    {
      "format": "csv",
      "output": "reports/endpoints.csv",
      "delimiter": ",",
      "quoting": "minimal",
      "fields": {
        "method": "HTTP Method",
        "path": "Endpoint Path",
        "description": "Description"
      }
    },
    {
      "format": "json",
      "output": "data/endpoints.json",
      "plain_text": false,
      "fields": {
        "name": "endpoint_name",
        "method": "http_method",
        "path": "url_path"
      }
    },
    {
      "format": "html",
      "output": "web/api-docs.html",
      "template": "templates/custom.html"
    }
  ]
}
```

## Top-Level Fields

### `input` (required)

Path to the API specification file or URL:

```json
{
  "input": "api.json"              // Local file (relative to config file)
}
```

```json
{
  "input": "/absolute/path/api.yaml"  // Absolute path
}
```

```json
{
  "input": "https://api.example.com/openapi.json"  // Remote URL
}
```

### `headers` (optional)

Custom HTTP headers for URL requests:

```json
{
  "headers": {
    "Authorization": "Bearer token123",
    "X-API-Version": "v2",
    "Accept": "application/json"
  }
}
```

### `exports` (required)

Array of export configurations. Each export runs sequentially, processing the input once and exporting to different formats.

## Export Configuration

Each export object requires:
- `format` - Output format: `"markdown"`, `"csv"`, `"json"`, or `"html"`
- `output` - Output file path

### Markdown Export

```json
{
  "format": "markdown",
  "output": "docs/api-endpoints.md"
}
```

Exports human-readable documentation with:
- Grouped endpoints
- Parameter tables
- HTTP method badges
- Descriptions with markdown formatting

### CSV Export

```json
{
  "format": "csv",
  "output": "reports/endpoints.csv",
  "delimiter": ",",
  "quoting": "minimal",
  "fields": {
    "method": "HTTP Method",
    "path": "Endpoint",
    "description": "Description",
    "group": "Category"
  }
}
```

**Options:**
- `delimiter` (optional) - Column delimiter: `","` (default), `";"`, `"\t"`, or any string
- `quoting` (optional) - Quoting mode: `"minimal"` (default), `"all"`, `"nonnumeric"`, `"none"`
- `fields` (optional) - Field mapping (see Field Mapping section)

**Quoting modes:**
- `"minimal"` - Only quote fields containing special characters
- `"all"` - Quote all fields
- `"nonnumeric"` - Quote all non-numeric fields
- `"none"` - Never quote fields (may break CSV if data contains delimiters)

### JSON Export

```json
{
  "format": "json",
  "output": "data/endpoints.json",
  "plain_text": false,
  "fields": {
    "name": "endpoint_name",
    "method": "http_method",
    "path": "url_path",
    "metadata.deprecated": "is_deprecated"
  }
}
```

**Options:**
- `plain_text` (optional) - Convert markdown descriptions to plain text (default: `false`)
- `fields` (optional) - Field mapping (see Field Mapping section)

### HTML Export

```json
{
  "format": "html",
  "output": "web/api-docs.html",
  "template": "templates/custom.html"
}
```

**Options:**
- `template` (optional) - Path to custom Mustache template (see Templating section)

Without a template, uses the built-in default template.

## Field Mapping

Field mapping allows you to:
1. Select which fields to export
2. Rename fields in the output
3. Access nested fields with dot notation

### Syntax

```json
{
  "fields": {
    "original_field": "new_field_name"
  }
}
```

### Available Fields

- `group` - Endpoint category/folder/tag
- `name` - Endpoint name/summary
- `method` - HTTP method (GET, POST, etc.)
- `path` - URL path
- `description` - Endpoint description
- `params` - Parameters array (exported as JSON string in CSV)
- `metadata.*` - Nested metadata fields (e.g., `metadata.deprecated`)

### Examples

**Select and rename fields:**
```json
{
  "fields": {
    "method": "HTTP Method",
    "path": "URL",
    "description": "Summary"
  }
}
```

Output only includes these three fields with new names.

**Access nested metadata:**
```json
{
  "fields": {
    "name": "endpoint_name",
    "metadata.deprecated": "is_deprecated",
    "metadata.tags": "tags"
  }
}
```

**CSV with custom fields:**
```json
{
  "format": "csv",
  "output": "endpoints.csv",
  "fields": {
    "group": "Category",
    "method": "Method",
    "path": "Path"
  }
}
```

Results in CSV with three columns: "Category", "Method", "Path".

## Path Resolution

Paths in config files are resolved in this order:

1. **Relative to config directory** - `templates/custom.html` looks in `<config-dir>/templates/custom.html`
2. **Relative to current working directory** - If not found above, checks `<cwd>/templates/custom.html`
3. **Absolute paths** - `/absolute/path/template.html` or `C:\path\template.html`

## Auto-Discovery

If you don't specify a config file, the tool looks for `.fizgig-config.json` in the current directory:

```bash
# Uses .fizgig-config.json if present
fizgig-api-extractor extract --config

# Or explicitly
fizgig-api-extractor extract --config .fizgig-config.json
```

## CLI Overrides

CLI flags override config file values:

```bash
# Override input and output
fizgig-api-extractor extract --config myconfig.json \
  -o different-output.html

# Override headers
fizgig-api-extractor extract --config myconfig.json \
  --header "Authorization: Bearer new-token"

# Override format options
fizgig-api-extractor extract --config myconfig.json \
  --plain-text
```

## Validation

Validate your config file before running exports:

```bash
# Validate specific config
fizgig-api-extractor validate-config myconfig.json

# Auto-discover and validate
fizgig-api-extractor validate-config
```

The validation checks:
- JSON syntax
- Required fields (`input`, `exports`)
- Export format validity
- Input file existence (for local files)
- Template file existence (if specified)

**Example validation output:**

```
Loading config...
✓ Config structure valid
Validating file references...
✗ Validation failed

● input
  Input file not found: api.json
  Checked: /path/to/project/api.json

● exports[2].template
  Template file not found: custom.html
  Searched in:
    /path/to/project/custom.html
    /current/directory/custom.html
    custom.html
```

## Example Configurations

### Simple Single Export

```json
{
  "input": "openapi.yaml",
  "exports": [
    {
      "format": "markdown",
      "output": "API.md"
    }
  ]
}
```

### Multiple Exports with Field Mapping

```json
{
  "input": "collection.json",
  "exports": [
    {
      "format": "csv",
      "output": "summary.csv",
      "delimiter": ";",
      "fields": {
        "method": "Method",
        "path": "Path"
      }
    },
    {
      "format": "json",
      "output": "full-data.json"
    },
    {
      "format": "html",
      "output": "docs.html"
    }
  ]
}
```

### Remote API with Authentication

```json
{
  "input": "https://api.example.com/openapi.json",
  "headers": {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "Accept": "application/json"
  },
  "exports": [
    {
      "format": "markdown",
      "output": "api-docs.md"
    }
  ]
}
```

### Custom Template and Field Selection

```json
{
  "input": "api.yaml",
  "exports": [
    {
      "format": "html",
      "output": "public-api.html",
      "template": "templates/public-api-template.html"
    },
    {
      "format": "json",
      "output": "endpoints-summary.json",
      "plain_text": true,
      "fields": {
        "name": "title",
        "method": "verb",
        "path": "route",
        "description": "summary"
      }
    }
  ]
}
```

## Best Practices

1. **Version control your configs** - Commit `.fizgig-config.json` to track documentation builds
2. **Use relative paths** - Makes configs portable across machines
3. **Validate before CI/CD** - Run `validate-config` in build pipelines
4. **Separate configs for different outputs** - Public vs internal documentation
5. **Use field mapping** - Reduce output size by selecting only needed fields
6. **Test with URLs** - Fetch specs directly from your API during builds

## Troubleshooting

**"Config file not found"**
- Check you're in the right directory
- Specify path explicitly: `--config path/to/config.json`

**"Input file not found"**
- Paths are relative to config file location
- Use absolute paths if needed
- Check file exists: `ls -la path/to/input.json`

**"Template file not found"**
- Template paths resolved relative to config directory first
- Export template: `fizgig-api-extractor init --template-only`
- Use absolute path if template is elsewhere

**"Invalid format"**
- Must be one of: `markdown`, `csv`, `json`, `html`
- Case-sensitive
- Check for typos in config file
