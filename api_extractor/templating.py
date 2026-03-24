"""
HTML templating functionality for fizgig-api-extractor.

Uses Chevron (Mustache) for template rendering.
"""

import chevron
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import importlib.resources
import re


def load_default_template() -> str:
    """
    Load default template from package resources.

    Returns:
        Template content as string
    """
    # Use importlib.resources to load from package
    try:
        # Python 3.9+
        files = importlib.resources.files('api_extractor')
        template_path = files / 'resources' / 'templates' / 'default.html'
        return template_path.read_text(encoding='utf-8')
    except AttributeError:
        # Python 3.8 fallback
        import pkg_resources
        return pkg_resources.resource_string(
            'api_extractor',
            'resources/templates/default.html'
        ).decode('utf-8')


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
    # Try paths in order
    paths_to_try = []

    # 1. Relative to config directory
    if config_dir:
        paths_to_try.append(config_dir / template_path)

    # 2. Relative to current working directory
    paths_to_try.append(Path.cwd() / template_path)

    # 3. Absolute path
    paths_to_try.append(Path(template_path))

    for path in paths_to_try:
        if path.exists():
            return path.read_text(encoding='utf-8')

    # Not found - provide helpful error
    tried_paths = '\n  - '.join(str(p) for p in paths_to_try)
    raise FileNotFoundError(
        f"Template file not found: {template_path}\n"
        f"Searched in:\n  - {tried_paths}"
    )


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


def prepare_template_data(endpoints: List[Dict[str, Any]],
                         source_file: str = "",
                         source_format: str = "") -> Dict[str, Any]:
    """
    Prepare data structure for template rendering.

    Creates both grouped and flat endpoint structures.

    Args:
        endpoints: List of endpoints
        source_file: Input file name
        source_format: Format type (postman/openapi)

    Returns:
        Data dictionary for template
    """
    from api_extractor.utils import group_by_tag
    from api_extractor.exporter import markdown_to_html

    # Group endpoints by category
    grouped = group_by_tag(endpoints, "group")

    # Prepare groups structure for template
    groups = []
    for group_name in sorted(grouped.keys()):
        group_endpoints = grouped[group_name]

        # Process each endpoint in group
        processed_endpoints = []
        for endpoint in group_endpoints:
            # Convert markdown description to HTML
            description = endpoint.get("description", "")
            if description:
                description = markdown_to_html(description)

            # Clean path for display
            path = clean_path_for_display(endpoint.get("path", ""))

            # Check if deprecated
            deprecated = endpoint.get("metadata", {}).get("deprecated", False)

            # Prepare params - check if any exist
            params = endpoint.get("params", [])
            has_params = len(params) > 0

            processed_endpoint = {
                "name": endpoint.get("name", ""),
                "method": endpoint.get("method", "GET"),
                "path": path,
                "description": description,
                "deprecated": deprecated,
                "params": params if has_params else None,  # None if empty for Mustache conditionals
            }

            processed_endpoints.append(processed_endpoint)

        groups.append({
            "name": group_name,
            "count": len(group_endpoints),
            "endpoints": processed_endpoints
        })

    # Prepare data for template
    data = {
        "total_endpoints": len(endpoints),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_file": source_file if source_file else None,
        "source_format": source_format if source_format else None,
        "groups": groups,
        "endpoints": endpoints  # Also provide flat structure
    }

    return data


def render_html_template(endpoints: List[Dict[str, Any]],
                        source_file: str = "",
                        source_format: str = "",
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
    # Load template
    if template_path:
        template = load_custom_template(template_path, config_dir)
    else:
        template = load_default_template()

    # Prepare data
    data = prepare_template_data(endpoints, source_file, source_format)

    # Render with Chevron
    html = chevron.render(template, data)

    return html
