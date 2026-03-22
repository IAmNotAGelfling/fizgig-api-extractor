"""
Export functionality for fizgig-api-extractor.

Exports parsed endpoints to multiple formats: Markdown, CSV, JSON, HTML.
"""

import json
import csv
import re
from typing import List, Dict, Any
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


def export_csv(endpoints: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export endpoints to CSV format.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path

    Example:
        >>> export_csv(endpoints, "api_endpoints.csv")
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)

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


def export_json(endpoints: List[Dict[str, Any]], output_path: str, pretty: bool = True) -> None:
    """
    Export endpoints to JSON format.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path
        pretty: Whether to pretty-print JSON (default: True)

    Example:
        >>> export_json(endpoints, "api_endpoints.json")
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(endpoints, f, indent=2, ensure_ascii=False)
        else:
            json.dump(endpoints, f, ensure_ascii=False)


def export_html(endpoints: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export endpoints to HTML format.

    Args:
        endpoints: List of endpoint dictionaries
        output_path: Output file path

    Example:
        >>> export_html(endpoints, "api_endpoints.html")
    """
    # Group endpoints by category
    grouped = group_by_tag(endpoints, "group")

    html_parts = []

    # HTML header
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Endpoints</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }
        .endpoint {
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .endpoint-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        .method {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
            color: white;
        }
        .method.GET { background-color: #61affe; }
        .method.POST { background-color: #49cc90; }
        .method.PUT { background-color: #fca130; }
        .method.PATCH { background-color: #50e3c2; }
        .method.DELETE { background-color: #f93e3e; }
        .method.HEAD { background-color: #9012fe; }
        .method.OPTIONS { background-color: #0d5aa7; }
        .path {
            font-family: 'Courier New', monospace;
            font-size: 16px;
            color: #333;
        }
        .endpoint-name {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .description {
            color: #666;
            margin: 10px 0;
            line-height: 1.6;
        }
        .description a {
            color: #007acc;
            text-decoration: none;
        }
        .description a:hover {
            text-decoration: underline;
        }
        .description code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        .description strong {
            font-weight: 600;
            color: #333;
        }
        .deprecated {
            display: inline-block;
            padding: 2px 8px;
            background-color: #ff6b6b;
            color: white;
            border-radius: 3px;
            font-size: 12px;
            margin-left: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th {
            background-color: #f0f0f0;
            padding: 10px;
            text-align: left;
            border: 1px solid #ddd;
            font-weight: 600;
        }
        td {
            padding: 8px;
            border: 1px solid #ddd;
        }
        .param-name {
            font-family: 'Courier New', monospace;
            color: #007acc;
        }
        .required {
            color: #f93e3e;
            font-weight: bold;
        }
        .optional {
            color: #999;
        }
        .badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        }
        .badge.path { background-color: #e3f2fd; color: #1976d2; }
        .badge.query { background-color: #f3e5f5; color: #7b1fa2; }
        .badge.header { background-color: #e8f5e9; color: #388e3c; }
        .badge.body { background-color: #fff3e0; color: #f57c00; }
        .summary {
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>API Endpoints</h1>
    <div class="summary">
        <strong>Total endpoints:</strong> """ + str(len(endpoints)) + """
    </div>
""")

    # Generate HTML for each group
    for group_name in sorted(grouped.keys()):
        group_endpoints = grouped[group_name]

        html_parts.append(f'    <h2>{group_name}</h2>\n')
        html_parts.append(f'    <p><em>{len(group_endpoints)} endpoint(s)</em></p>\n')

        for endpoint in group_endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "")
            name = endpoint.get("name", "")
            description = endpoint.get("description", "")
            params = endpoint.get("params", [])
            deprecated = endpoint.get("metadata", {}).get("deprecated", False)

            html_parts.append('    <div class="endpoint">\n')
            html_parts.append('        <div class="endpoint-header">\n')
            html_parts.append(f'            <span class="method {method}">{method}</span>\n')
            # Clean path for display (remove Postman {{variables}})
            display_path = clean_path_for_display(path)
            html_parts.append(f'            <span class="path">{display_path}</span>\n')
            if deprecated:
                html_parts.append('            <span class="deprecated">DEPRECATED</span>\n')
            html_parts.append('        </div>\n')
            html_parts.append(f'        <div class="endpoint-name">{name}</div>\n')

            if description:
                # Convert markdown to HTML
                html_description = markdown_to_html(description)
                html_parts.append(f'        <div class="description">{html_description}</div>\n')

            if params:
                html_parts.append('        <table>\n')
                html_parts.append('            <thead>\n')
                html_parts.append('                <tr>\n')
                html_parts.append('                    <th>Parameter</th>\n')
                html_parts.append('                    <th>In</th>\n')
                html_parts.append('                    <th>Type</th>\n')
                html_parts.append('                    <th>Required</th>\n')
                html_parts.append('                    <th>Description</th>\n')
                html_parts.append('                </tr>\n')
                html_parts.append('            </thead>\n')
                html_parts.append('            <tbody>\n')

                for param in params:
                    param_name = param.get("name", "")
                    param_in = param.get("in", "")
                    param_type = param.get("type", "")
                    param_required = param.get("required", False)
                    param_desc = param.get("description", "")

                    required_class = "required" if param_required else "optional"
                    required_text = "Yes" if param_required else "No"

                    html_parts.append('                <tr>\n')
                    html_parts.append(f'                    <td class="param-name">{param_name}</td>\n')
                    html_parts.append(f'                    <td><span class="badge {param_in}">{param_in}</span></td>\n')
                    html_parts.append(f'                    <td>{param_type}</td>\n')
                    html_parts.append(f'                    <td class="{required_class}">{required_text}</td>\n')
                    html_parts.append(f'                    <td>{param_desc}</td>\n')
                    html_parts.append('                </tr>\n')

                html_parts.append('            </tbody>\n')
                html_parts.append('        </table>\n')

            html_parts.append('    </div>\n')

    # HTML footer
    html_parts.append("""</body>
</html>
""")

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(html_parts))
