"""
Utility functions for fizgig-api-extractor.

Provides general-purpose helper functions used throughout the package.
"""

import re
from typing import Any, Dict, List, Union


def safe_get(data: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely retrieve nested dictionary values.

    Args:
        data: The dictionary or object to traverse
        *keys: Keys to traverse in order
        default: Default value if key path doesn't exist

    Returns:
        The value at the key path, or default if not found

    Example:
        >>> safe_get({"a": {"b": {"c": 42}}}, "a", "b", "c")
        42
        >>> safe_get({"a": {"b": {}}}, "a", "b", "c", default="missing")
        'missing'
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default

        if current is None:
            return default

    return current


def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.

    Args:
        text: Input text to slugify

    Returns:
        Slugified text (lowercase, alphanumeric and hyphens only)

    Example:
        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("API/Endpoints_2024")
        'api-endpoints-2024'
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)

    # Remove leading/trailing hyphens
    text = text.strip('-')

    # Replace multiple consecutive hyphens with single hyphen
    text = re.sub(r'-+', '-', text)

    return text


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries, with later dictionaries taking precedence.

    Args:
        *dicts: Variable number of dictionaries to merge

    Returns:
        Merged dictionary

    Example:
        >>> merge_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'a': 1, 'b': 3, 'c': 4}
    """
    result: Dict[str, Any] = {}

    for d in dicts:
        if isinstance(d, dict):
            result.update(d)

    return result


def normalise_url(url: str, base_url: str = "") -> str:
    """
    Normalise a URL by combining with base URL if needed.

    Args:
        url: The URL or path to normalise
        base_url: Optional base URL to prepend

    Returns:
        Normalised URL

    Example:
        >>> normalise_url("/api/users", "https://example.com")
        'https://example.com/api/users'
        >>> normalise_url("https://example.com/api/users", "")
        'https://example.com/api/users'
    """
    if not url:
        return base_url or ""

    # If URL is already absolute, return as-is
    if url.startswith(('http://', 'https://', '//')):
        return url

    # If no base URL provided, return the path
    if not base_url:
        return url if url.startswith('/') else f"/{url}"

    # Remove trailing slash from base_url
    base_url = base_url.rstrip('/')

    # Add leading slash to url if needed
    if not url.startswith('/'):
        url = f"/{url}"

    return f"{base_url}{url}"


def strip_empty(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively remove empty values (None, empty strings, empty lists/dicts) from data structures.

    Args:
        data: Data structure to clean

    Returns:
        Cleaned data structure

    Example:
        >>> strip_empty({"a": 1, "b": None, "c": "", "d": []})
        {'a': 1}
    """
    if isinstance(data, dict):
        return {
            k: strip_empty(v)
            for k, v in data.items()
            if v is not None and v != "" and v != [] and v != {}
        }
    elif isinstance(data, list):
        return [
            strip_empty(item)
            for item in data
            if item is not None and item != "" and item != [] and item != {}
        ]
    else:
        return data


def extract_path_params(path: str) -> List[str]:
    """
    Extract path parameter names from a URL path.

    Args:
        path: URL path with parameters (e.g., "/users/{id}/posts/{postId}")

    Returns:
        List of parameter names

    Example:
        >>> extract_path_params("/users/{id}/posts/{postId}")
        ['id', 'postId']
        >>> extract_path_params("/api/:userId/comments/:commentId")
        ['userId', 'commentId']
        >>> extract_path_params("/{{basePath}}users/:id")
        ['id']
    """
    params = []

    # Remove Postman double-brace variables {{variable}} first
    # These are template variables, not path parameters
    cleaned_path = re.sub(r'\{\{[^}]+\}\}', '', path)

    # Extract {param} style parameters (OpenAPI) - single braces only
    params.extend(re.findall(r'\{([^}]+)\}', cleaned_path))

    # Extract :param style parameters (Postman/Express)
    params.extend(re.findall(r':([a-zA-Z_][a-zA-Z0-9_]*)', cleaned_path))

    return params


def format_method(method: str) -> str:
    """
    Format HTTP method consistently (uppercase).

    Args:
        method: HTTP method name

    Returns:
        Uppercase method name

    Example:
        >>> format_method("get")
        'GET'
        >>> format_method("Post")
        'POST'
    """
    return method.upper() if method else "GET"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to append if truncated

    Returns:
        Truncated text

    Example:
        >>> truncate_text("This is a very long text that needs truncation", 20)
        'This is a very lo...'
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def group_by_tag(endpoints: List[Dict[str, Any]], tag_key: str = "group") -> Dict[str, List[Dict[str, Any]]]:
    """
    Group endpoints by a tag/category.

    Args:
        endpoints: List of endpoint dictionaries
        tag_key: Key to group by (default: "group")

    Returns:
        Dictionary mapping tag names to lists of endpoints

    Example:
        >>> endpoints = [
        ...     {"group": "Users", "path": "/users"},
        ...     {"group": "Users", "path": "/users/{id}"},
        ...     {"group": "Posts", "path": "/posts"}
        ... ]
        >>> grouped = group_by_tag(endpoints)
        >>> len(grouped["Users"])
        2
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for endpoint in endpoints:
        tag = endpoint.get(tag_key, "Uncategorized")
        if tag not in grouped:
            grouped[tag] = []
        grouped[tag].append(endpoint)

    return grouped


def ensure_list(value: Any) -> List[Any]:
    """
    Ensure a value is a list.

    Args:
        value: Value to convert

    Returns:
        List containing the value, or the value itself if already a list

    Example:
        >>> ensure_list("single")
        ['single']
        >>> ensure_list([1, 2, 3])
        [1, 2, 3]
        >>> ensure_list(None)
        []
    """
    if value is None:
        return []
    elif isinstance(value, list):
        return value
    else:
        return [value]
