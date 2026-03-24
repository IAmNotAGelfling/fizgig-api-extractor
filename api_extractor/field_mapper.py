"""
Field mapping functionality for fizgig-api-extractor.

Allows custom field selection, renaming, and ordering for CSV/JSON exports.
"""

from typing import Dict, Any, List, Optional


def get_nested_field(obj: Dict[str, Any], field_path: str) -> Any:
    """
    Get value from nested dict using dot notation.

    Args:
        obj: Dictionary to extract from
        field_path: Dot-separated path (e.g., "metadata.deprecated")

    Returns:
        Field value or None if not found

    Example:
        >>> data = {"metadata": {"deprecated": True}}
        >>> get_nested_field(data, "metadata.deprecated")
        True
    """
    parts = field_path.split(".")
    current = obj

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]

    return current


def apply_field_mapping(
    endpoints: List[Dict[str, Any]], field_map: Optional[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Transform endpoints based on field mapping.

    Args:
        endpoints: List of endpoint dictionaries
        field_map: Mapping of original_field -> new_field_name
                   If None or empty, returns endpoints unchanged
                   Keys can use dot notation for nested fields

    Returns:
        Transformed endpoint list with only mapped fields

    Example:
        >>> endpoints = [{"method": "GET", "path": "/users", "name": "List"}]
        >>> field_map = {"method": "HTTP Method", "path": "Endpoint"}
        >>> result = apply_field_mapping(endpoints, field_map)
        >>> result[0]
        {'HTTP Method': 'GET', 'Endpoint': '/users'}
    """
    # If no mapping, return unchanged
    if not field_map:
        return endpoints

    # Transform each endpoint
    transformed = []
    for endpoint in endpoints:
        new_endpoint = {}

        # Process fields in the order specified in mapping
        for original_field, new_field_name in field_map.items():
            # Get value (supports nested fields with dot notation)
            value = get_nested_field(endpoint, original_field)

            # Use new field name in output
            new_endpoint[new_field_name] = value

        transformed.append(new_endpoint)

    return transformed
