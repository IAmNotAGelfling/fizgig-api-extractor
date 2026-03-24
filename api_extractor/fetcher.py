"""
URL fetching functionality for fizgig-api-extractor.

Handles fetching API specifications from HTTP/HTTPS URLs with custom headers.
"""

import requests
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse


def fetch_from_url(
    url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30
) -> Tuple[str, str]:
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
        ValueError: On invalid content or HTTP error status codes
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)

        # Check for HTTP errors
        if response.status_code != 200:
            raise ValueError(f"HTTP {response.status_code}: {response.reason}")

        # Detect format from content-type or URL
        content_type = response.headers.get("Content-Type", "").lower()
        detected_format = None

        if "yaml" in content_type or "yml" in content_type:
            detected_format = "yaml"
        elif "json" in content_type:
            detected_format = "json"
        else:
            # Fall back to URL extension
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            if path.endswith((".yaml", ".yml")):
                detected_format = "yaml"
            else:
                detected_format = "json"  # Default to JSON

        content = response.text

        # Validate content can be parsed
        if detected_format == "json":
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"URL returned invalid JSON: {e}")
        elif detected_format == "yaml":
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"URL returned invalid YAML: {e}")

        return content, detected_format

    except requests.Timeout:
        raise ValueError(f"Request timed out after {timeout}s")
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch URL: {e}")


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
    if save_path is None:
        # Derive filename from URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = "spec.json"  # Default filename
        save_path = f"./{filename}"

    # Ensure parent directory exists
    save_file = Path(save_path)
    save_file.parent.mkdir(parents=True, exist_ok=True)

    # Write content
    with open(save_file, "w", encoding="utf-8") as f:
        f.write(content)

    return save_path


def load_from_url(
    url: str, headers: Optional[Dict[str, str]] = None, save_path: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Fetch, parse, and optionally save content from URL.

    Args:
        url: HTTP(S) URL to fetch
        headers: Optional HTTP headers
        save_path: Optional path to save content

    Returns:
        Tuple of (parsed_data, format_type) where format_type is "postman" or "openapi"

    Raises:
        ValueError: On fetch or parse errors
    """
    from api_extractor.loader import detect_format

    # Fetch content
    content, detected_format = fetch_from_url(url, headers)

    # Save if requested
    if save_path:
        save_url_content(content, save_path, url)

    # Parse content
    if detected_format == "json":
        data = json.loads(content)
    else:  # yaml
        data = yaml.safe_load(content)

    # Detect API format (Postman vs OpenAPI)
    format_type = detect_format(data)

    if format_type == "unknown":
        raise ValueError(
            "Could not detect format of URL content. "
            "Expected a Postman v2.1 collection or OpenAPI 3.x specification."
        )

    return data, format_type
