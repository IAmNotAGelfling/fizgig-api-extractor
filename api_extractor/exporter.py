"""
Export functionality for fizgig-api-extractor.

Exports parsed endpoints to multiple formats: Markdown, CSV, JSON, HTML.
"""

import json
import csv
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

import mistune
from mistune.renderers.html import HTMLRenderer

from api_extractor.utils import group_by_tag, truncate_text


class CustomHTMLRenderer(HTMLRenderer):
    """Custom HTML renderer that adds target='_blank' to links."""

    def link(self, text: str, url: str, title: str = None) -> str:
        """Render link with target='_blank' attribute."""
        s = f'<a href="{self.safe_url(url)}" target="_blank"'
        if title:
            s += f' title="{mistune.escape_html(title)}"'
        return s + f'>{text}</a>'


# Create mistune markdown renderer with custom link handling
markdown_renderer = mistune.create_markdown(
    renderer=CustomHTMLRenderer(escape=True),
    plugins=['strikethrough', 'table']
)


def markdown_to_html(text: str) -> str:
    """
    Convert markdown formatting to HTML using mistune.

    Args:
        text: Markdown text

    Returns:
        HTML formatted text
    """
    if not text:
        return ""

    # Render markdown to HTML with custom renderer
    html = markdown_renderer(text)

    return html.strip()


def clean_path_for_display(path: str) -> str:
    """
    Clean up path for display by removing Postman template variables.

    Args:
        path: Raw path with Postman variables

    Returns:
        Cleaned path
    """
    # Remove {{variable}} Postman templates
    cleaned = re.sub(r'\{\{[^}]+\}\}', '', path)

    # Clean up any double slashes
    cleaned = re.sub(r'/+', '/', cleaned)

    return cleaned


def markdown_to_plain_text(text: str) -> str:
    """
    Convert markdown to plain text using mistune, then strip HTML tags.

    Args:
        text: Markdown text

    Returns:
        Plain text without markdown or HTML formatting
    """
    if not text:
        return ""

    # Use mistune to convert markdown to HTML
    html = markdown_renderer(text)

    # Strip all HTML tags
    plain = re.sub(r'<[^>]+>', '', html)

    # Convert common HTML entities
    plain = plain.replace('&lt;', '<')
    plain = plain.replace('&gt;', '>')
    plain = plain.replace('&amp;', '&')
    plain = plain.replace('&quot;', '"')
    plain = plain.replace('&apos;', "'")

    # Clean up extra whitespace and newlines
    plain = re.sub(r'\n\n+', '\n', plain)
    plain = re.sub(r'  +', ' ', plain)
    plain = plain.strip()

    return plain


def export_markdown(endpoints: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export endpoints to Markdown format.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path

    Example:
        >>> export_markdown(endpoints, "api_endpoints.md")
    """
    # Group endpoints by category
    grouped = group_by_tag(endpoints, "group")

    lines = []
    lines.append("# API Endpoints\n")
    lines.append(f"Total endpoints: {len(endpoints)}\n")
    lines.append("---\n")

    for group_name in sorted(grouped.keys()):
        group_endpoints = grouped[group_name]

        lines.append(f"\n## {group_name}\n")
        lines.append(f"*{len(group_endpoints)} endpoint(s)*\n")

        for endpoint in group_endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "")
            name = endpoint.get("name", "")
            description = endpoint.get("description", "")
            params = endpoint.get("params", [])

            lines.append(f"\n### {name}\n")
            lines.append(f"**`{method} {path}`**\n")

            if description:
                lines.append(f"\n{description}\n")

            if params:
                lines.append("\n**Parameters:**\n")
                lines.append("| Name | In | Type | Required | Description |\n")
                lines.append("|------|-------|------|----------|-------------|\n")

                for param in params:
                    param_name = param.get("name", "")
                    param_in = param.get("in", "")
                    param_type = param.get("type", "")
                    param_required = "Yes" if param.get("required", False) else "No"
                    param_desc = param.get("description", "")

                    lines.append(f"| `{param_name}` | {param_in} | {param_type} | {param_required} | {param_desc} |\n")

            lines.append("\n---\n")

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def export_csv(endpoints: List[Dict[str, Any]], output_path: str,
               field_map: Dict[str, str] = None, delimiter: str = ',',
               quoting: str = 'minimal') -> None:
    """
    Export endpoints to CSV format.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path
        field_map: Optional field mapping for custom field selection/renaming
        delimiter: CSV delimiter character (default: ',')
        quoting: Quoting style - 'minimal', 'all', 'nonnumeric', 'none' (default: 'minimal')

    Example:
        >>> export_csv(endpoints, "api_endpoints.csv")
        >>> export_csv(endpoints, "api.csv", {"method": "HTTP Method", "path": "Endpoint"})
        >>> export_csv(endpoints, "api.tsv", delimiter='\\t')
        >>> export_csv(endpoints, "api.csv", quoting='all')
    """
    from api_extractor.field_mapper import apply_field_mapping

    # Map quoting parameter to csv module constants
    quoting_map = {
        'minimal': csv.QUOTE_MINIMAL,
        'all': csv.QUOTE_ALL,
        'nonnumeric': csv.QUOTE_NONNUMERIC,
        'none': csv.QUOTE_NONE
    }
    csv_quoting = quoting_map.get(quoting.lower(), csv.QUOTE_MINIMAL)

    # Apply field mapping if provided
    if field_map:
        endpoints = apply_field_mapping(endpoints, field_map)

        # Export mapped fields
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter, quoting=csv_quoting)

            # Write header from mapped field names
            writer.writerow(list(field_map.values()))

            # Write data
            for endpoint in endpoints:
                writer.writerow(list(endpoint.values()))

        return

    # Default behavior (no field mapping)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=delimiter, quoting=csv_quoting)

        # Write header
        writer.writerow([
            "Group",
            "Name",
            "Method",
            "Path",
            "Description",
            "Parameters",
            "Deprecated"
        ])

        # Write endpoints
        for endpoint in endpoints:
            group = endpoint.get("group", "")
            name = endpoint.get("name", "")
            method = endpoint.get("method", "")
            path = endpoint.get("path", "")
            # Strip markdown from description for plain text CSV
            description = markdown_to_plain_text(endpoint.get("description", ""))
            params = endpoint.get("params", [])
            deprecated = endpoint.get("metadata", {}).get("deprecated", False)

            # Format parameters as a readable string
            param_strings = []
            for param in params:
                param_name = param.get("name", "")
                param_in = param.get("in", "")
                param_type = param.get("type", "")
                param_required = "required" if param.get("required", False) else "optional"
                # Strip markdown from parameter description
                param_desc = markdown_to_plain_text(param.get("description", ""))
                if param_desc:
                    param_strings.append(f"{param_name} ({param_in}, {param_type}, {param_required}) - {param_desc}")
                else:
                    param_strings.append(f"{param_name} ({param_in}, {param_type}, {param_required})")

            params_str = "; ".join(param_strings)

            writer.writerow([
                group,
                name,
                method,
                path,
                description,
                params_str,
                "Yes" if deprecated else "No"
            ])


def export_json(endpoints: List[Dict[str, Any]], output_path: str, pretty: bool = True,
                plain_text: bool = False, field_map: Dict[str, str] = None) -> None:
    """
    Export endpoints to JSON format.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path
        pretty: Whether to pretty-print JSON (default: True)
        plain_text: Whether to convert markdown descriptions to plain text (default: False)
        field_map: Optional field mapping for custom field selection/renaming

    Example:
        >>> export_json(endpoints, "api_endpoints.json")
        >>> export_json(endpoints, "api_endpoints.json", plain_text=True)
        >>> export_json(endpoints, "api.json", field_map={"method": "HTTP Method"})
    """
    from api_extractor.field_mapper import apply_field_mapping

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Apply field mapping if provided
    if field_map:
        endpoints = apply_field_mapping(endpoints, field_map)

    # If plain_text is requested, strip markdown from descriptions
    if plain_text and not field_map:  # Only strip if not using custom fields
        endpoints = [
            {
                **endpoint,
                "description": markdown_to_plain_text(endpoint.get("description", "")),
                "params": [
                    {
                        **param,
                        "description": markdown_to_plain_text(param.get("description", ""))
                    }
                    for param in endpoint.get("params", [])
                ]
            }
            for endpoint in endpoints
        ]

    with open(output_file, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(endpoints, f, indent=2, ensure_ascii=False)
        else:
            json.dump(endpoints, f, ensure_ascii=False)


def export_html(endpoints: List[Dict[str, Any]], output_path: str,
                template_path: Optional[str] = None,
                config_dir: Optional[Path] = None) -> None:
    """
    Export endpoints to HTML format using template.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path
        template_path: Optional custom template path
        config_dir: Config directory for template resolution

    Example:
        >>> export_html(endpoints, "api_endpoints.html")
        >>> export_html(endpoints, "api.html", template_path="custom.html")
    """
    from api_extractor.templating import render_html_template

    # Extract source info from output path
    source_file = Path(output_path).stem

    # Render HTML using template
    html = render_html_template(
        endpoints=endpoints,
        source_file=source_file,
        source_format="unknown",
        template_path=template_path,
        config_dir=config_dir
    )

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

