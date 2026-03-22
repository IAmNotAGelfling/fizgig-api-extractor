# fizgig-api-extractor

Parse Postman collections and OpenAPI specifications, extract API endpoints, and export them in multiple formats.

## Features

- **Parse multiple formats**
  - Postman v2.1 collections (JSON)
  - OpenAPI 3.x specifications (JSON and YAML)
  - Automatic format detection

- **Extract comprehensive endpoint information**
  - HTTP methods (GET, POST, PUT, DELETE, etc.)
  - URL paths with parameter placeholders
  - Request parameters (path, query, header, body)
  - Descriptions and metadata
  - Folder/tag grouping

- **Export to multiple formats**
  - **Markdown** - Human-readable documentation
  - **CSV** - Spreadsheet-compatible format
  - **JSON** - Machine-readable structured data
  - **HTML** - Styled web page with interactive display

- **Convert between formats**
  - OpenAPI → Postman collection converter

- **Interactive TUI**
  - Tree view display using Rich
  - Color-coded HTTP methods
  - Hierarchical folder structure

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/IAmNotAGelfling/fizgig-api-extractor.git
cd fizgig-api-extractor

# Install with pip
pip install -e .
```

### Using pip (once published)

```bash
pip install fizgig-api-extractor
```

## Usage

### Command-line Interface

The tool provides a CLI with several commands:

#### Extract and Export

Extract endpoints and export to a file:

```bash
# Display endpoints as a tree (default behavior)
fizgig-api-extractor extract api.json

# Export to Markdown
fizgig-api-extractor extract api.json -o endpoints.md -f markdown

# Export to CSV
fizgig-api-extractor extract openapi.yaml -o endpoints.csv -f csv

# Export to JSON
fizgig-api-extractor extract collection.json -o endpoints.json -f json

# Export to HTML
fizgig-api-extractor extract api.yaml -o endpoints.html -f html
```

#### Tree View

Display endpoints in an interactive tree:

```bash
# Basic tree view
fizgig-api-extractor tree api.json

# Show parameter details
fizgig-api-extractor tree api.json --params
```

#### Convert Formats

Convert OpenAPI specifications to Postman collections:

```bash
fizgig-api-extractor convert openapi.yaml collection.json
```

### Python API

You can also use fizgig-api-extractor as a Python library:

```python
from api_extractor import (
    load_api_file,
    parse_postman_collection,
    parse_openapi_spec,
    export_markdown,
    export_csv,
    export_json,
    export_html,
    openapi_to_postman,
    display_tree
)

# Load and parse
data, format_type = load_api_file("api.json")

if format_type == "postman":
    endpoints = parse_postman_collection(data)
elif format_type == "openapi":
    endpoints = parse_openapi_spec(data)

# Export to different formats
export_markdown(endpoints, "endpoints.md")
export_csv(endpoints, "endpoints.csv")
export_json(endpoints, "endpoints.json")
export_html(endpoints, "endpoints.html")

# Display tree in terminal
display_tree(endpoints, show_params=True)

# Convert OpenAPI to Postman
postman_collection = openapi_to_postman(data)
```

## Output Examples

### Markdown Output

```markdown
# API Endpoints

Total endpoints: 12

---

## Users

*4 endpoint(s)*

### List all users

**`GET /api/users`**

Retrieve a paginated list of all users.

**Parameters:**

| Name | In | Type | Required | Description |
|------|-------|------|----------|-------------|
| `page` | query | integer | No | Page number |
| `limit` | query | integer | No | Items per page |

---

### Create user

**`POST /api/users`**
...
```

### Tree View Output

```
API Endpoints
├── Users
│   ├── GET    /api/users — List all users
│   ├── POST   /api/users — Create user
│   ├── GET    /api/users/{id} — Get user by ID
│   └── DELETE /api/users/{id} — Delete user
├── Posts
│   ├── GET    /api/posts — List posts
│   ├── POST   /api/posts — Create post
│   └── GET    /api/posts/{id} — Get post
└── Auth
    ├── POST   /api/auth/login — User login
    └── POST   /api/auth/logout — User logout

Total: 12 endpoint(s) in 3 group(s)
```

### HTML Output

The HTML export creates a styled, single-page documentation with:
- Color-coded HTTP methods
- Collapsible sections
- Parameter tables
- Responsive design
- Search-friendly structure

## Endpoint Data Structure

Each parsed endpoint contains:

```python
{
    "group": str,          # Category/folder name
    "name": str,           # Endpoint name
    "method": str,         # HTTP method (GET, POST, etc.)
    "path": str,           # Full URL path
    "description": str,    # Endpoint description
    "params": [            # List of parameters
        {
            "name": str,
            "in": str,     # "path", "query", "header", "body"
            "required": bool,
            "type": str,
            "description": str
        }
    ],
    "metadata": {          # Additional metadata
        # Format-specific fields
    }
}
```

## Supported Input Formats

### Postman Collection v2.1

- Folders and nested folders
- Request details (URL, method, headers, body)
- Path and query parameters
- Environment variables

### OpenAPI 3.x

- Servers and base URLs
- Paths and operations
- Parameters (path, query, header)
- Request bodies (JSON, form data, multipart)
- Response schemas
- Tags and grouping

## Requirements

- Python 3.8+
- typer >= 0.9.0
- rich >= 13.0.0
- pyyaml >= 6.0
- mistune >= 3.0.0

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

IAmNotAGelfling
