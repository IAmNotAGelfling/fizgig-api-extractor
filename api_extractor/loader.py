"""
File loader and format detection for fizgig-api-extractor.

Handles loading API specification files and automatically detecting their format.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, Literal

from api_extractor.utils import safe_get


FormatType = Literal["postman", "openapi", "unknown"]


def detect_format(data: Dict[str, Any]) -> FormatType:
    """
    Detect whether data is a Postman collection or OpenAPI spec.

    Args:
        data: Parsed JSON/YAML data

    Returns:
        Format type: "postman", "openapi", or "unknown"

    Detection logic:
    - Postman: has "info.schema" containing "collection" or has "item" list
    - OpenAPI: has "openapi" field with version 3.x or has "paths" object
    """
    # Check for Postman v2.1 collection
    schema = safe_get(data, "info", "schema", default="")
    if "collection" in str(schema).lower():
        return "postman"

    # Check for Postman by presence of items
    if "item" in data and isinstance(data.get("item"), list):
        return "postman"

    # Check for OpenAPI 3.x
    openapi_version = data.get("openapi", "")
    if openapi_version and str(openapi_version).startswith("3"):
        return "openapi"

    # Check for OpenAPI by presence of paths
    if "paths" in data and isinstance(data.get("paths"), dict):
        return "openapi"

    return "unknown"


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If JSON is invalid
        FileNotFoundError: If file doesn't exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading {file_path}: {e}")


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """
    Load a YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML data

    Raises:
        ValueError: If YAML is invalid
        FileNotFoundError: If file doesn't exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading {file_path}: {e}")


def load_api_file(file_path: str, headers: Dict[str, str] = None,
                  save_path: str = None) -> Tuple[Dict[str, Any], FormatType]:
    """
    Load an API specification file or URL and detect its format.

    Automatically detects whether the input is a URL or local file.
    For files, detects JSON or YAML based on extension.
    Then detects whether it's a Postman collection or OpenAPI spec.

    Args:
        file_path: Path to API specification file or HTTP(S) URL
        headers: Optional HTTP headers for URL requests
        save_path: Optional path to save URL content to local file

    Returns:
        Tuple of (parsed_data, format_type)

    Raises:
        ValueError: If file format is invalid or cannot be detected
        FileNotFoundError: If file doesn't exist

    Example:
        >>> data, fmt = load_api_file("api.json")
        >>> print(f"Detected format: {fmt}")
        Detected format: openapi
        >>> data, fmt = load_api_file("https://api.example.com/openapi.yaml")
        >>> print(f"Detected format: {fmt}")
        Detected format: openapi
    """
    # Check if input is a URL
    if file_path.startswith('http://') or file_path.startswith('https://'):
        from api_extractor.fetcher import load_from_url
        return load_from_url(file_path, headers, save_path)

    # Otherwise, load from local file
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine file type by extension
    suffix = path.suffix.lower()

    if suffix == '.json':
        data = load_json(path)
    elif suffix in ['.yaml', '.yml']:
        data = load_yaml(path)
    else:
        # Try JSON first, then YAML for files without standard extensions
        json_error = None
        yaml_error = None

        try:
            data = load_json(path)
        except ValueError as e:
            json_error = str(e)
            try:
                data = load_yaml(path)
            except ValueError as e:
                yaml_error = str(e)
                raise ValueError(
                    f"Could not parse {file_path} as JSON or YAML. "
                    f"Supported extensions: .json, .yaml, .yml\n"
                    f"JSON parse error: {json_error}\n"
                    f"YAML parse error: {yaml_error}"
                )

    # Detect format
    format_type = detect_format(data)

    if format_type == "unknown":
        raise ValueError(
            f"Could not detect format of {file_path}. "
            f"Expected a Postman v2.1 collection or OpenAPI 3.x specification."
        )

    return data, format_type


def validate_postman_collection(data: Dict[str, Any]) -> bool:
    """
    Validate that data is a valid Postman collection.

    Args:
        data: Parsed data to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    # Must have info section
    if "info" not in data:
        return False

    # Must have item list (can be empty)
    if "item" not in data:
        return False

    return True


def validate_openapi_spec(data: Dict[str, Any]) -> bool:
    """
    Validate that data is a valid OpenAPI 3.x specification.

    Args:
        data: Parsed data to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    # Must have openapi version
    openapi_version = data.get("openapi", "")
    if not openapi_version or not str(openapi_version).startswith("3"):
        return False

    # Must have info section
    if "info" not in data:
        return False

    # Must have paths (can be empty)
    if "paths" not in data:
        return False

    return True
