"""
fizgig-api-extractor: Parse Postman collections and OpenAPI specs, extract endpoints, and export in multiple formats.

This package provides tools for:
- Parsing Postman v2.1 collections
- Parsing OpenAPI 3.x specifications (JSON and YAML)
- Automatically detecting input format
- Extracting API endpoints with full metadata
- Exporting to multiple formats (Markdown, CSV, JSON, HTML)
- Converting OpenAPI specs to Postman collections
- Displaying API structure in a TUI tree view
"""

__version__ = "1.1.0"
__author__ = "IAmNotAGelfling"
__license__ = "MIT"

from api_extractor.loader import load_api_file, detect_format
from api_extractor.parser_postman import parse_postman_collection
from api_extractor.parser_openapi import parse_openapi_spec
from api_extractor.exporter import (
    export_markdown,
    export_csv,
    export_json,
    export_html,
)
from api_extractor.converter import openapi_to_postman
from api_extractor.treeview import display_tree

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "load_api_file",
    "detect_format",
    "parse_postman_collection",
    "parse_openapi_spec",
    "export_markdown",
    "export_csv",
    "export_json",
    "export_html",
    "openapi_to_postman",
    "display_tree",
]
