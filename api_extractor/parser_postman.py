"""
Postman collection parser for fizgig-api-extractor.

Parses Postman v2.1 collection files and extracts endpoint information.
"""

from typing import Dict, Any, List, Optional

from api_extractor.utils import safe_get, format_method, extract_path_params, ensure_list


def parse_postman_url(url_data: Any) -> Dict[str, Any]:
    """
    Parse a Postman URL object.

    Args:
        url_data: URL data from Postman collection (can be string or object)

    Returns:
        Dictionary with parsed URL information
    """
    result = {
        "raw": "",
        "path": "",
        "host": "",
        "protocol": "",
        "variables": {}
    }

    # Handle string URL
    if isinstance(url_data, str):
        result["raw"] = url_data
        result["path"] = url_data
        return result

    # Handle URL object
    if not isinstance(url_data, dict):
        return result

    # Extract raw URL
    result["raw"] = url_data.get("raw", "")

    # Extract protocol
    protocol = url_data.get("protocol", "")
    if protocol:
        result["protocol"] = protocol

    # Extract host
    host = url_data.get("host", [])
    if isinstance(host, list):
        result["host"] = ".".join(str(h) for h in host)
    elif isinstance(host, str):
        result["host"] = host

    # Extract path segments
    path_segments = url_data.get("path", [])
    if isinstance(path_segments, list):
        # Join path segments
        path = "/" + "/".join(str(p) for p in path_segments)
        result["path"] = path
    elif isinstance(path_segments, str):
        result["path"] = path_segments if path_segments.startswith("/") else f"/{path_segments}"

    # Extract variables
    variables = url_data.get("variable", [])
    if isinstance(variables, list):
        for var in variables:
            if isinstance(var, dict):
                key = var.get("key", "")
                value = var.get("value", "")
                if key:
                    result["variables"][key] = value

    return result


def parse_postman_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a Postman request object.

    Args:
        request_data: Request data from Postman collection

    Returns:
        Dictionary with parsed request information
    """
    # Extract method
    method = format_method(request_data.get("method", "GET"))

    # Extract URL
    url_data = request_data.get("url", {})
    url_info = parse_postman_url(url_data)

    # Extract description
    description = request_data.get("description", "")

    # Extract headers
    headers = []
    for header in ensure_list(request_data.get("header", [])):
        if isinstance(header, dict) and not header.get("disabled", False):
            headers.append({
                "key": header.get("key", ""),
                "value": header.get("value", ""),
                "description": header.get("description", "")
            })

    # Extract query parameters
    query_params = []
    if isinstance(url_data, dict):
        for param in ensure_list(url_data.get("query", [])):
            if isinstance(param, dict) and not param.get("disabled", False):
                query_params.append({
                    "key": param.get("key", ""),
                    "value": param.get("value", ""),
                    "description": param.get("description", "")
                })

    # Extract body
    body = None
    body_data = request_data.get("body", {})
    if isinstance(body_data, dict):
        mode = body_data.get("mode", "")
        if mode:
            body = {
                "mode": mode,
                "content": body_data.get(mode, "")
            }

    # Extract path parameters
    path_params = extract_path_params(url_info["path"])

    return {
        "method": method,
        "url": url_info,
        "description": description,
        "headers": headers,
        "query_params": query_params,
        "path_params": path_params,
        "body": body
    }


def parse_postman_item(item: Dict[str, Any], parent_path: List[str] = None) -> List[Dict[str, Any]]:
    """
    Parse a Postman collection item (folder or request).

    Recursively processes folders and extracts request information.

    Args:
        item: Item from Postman collection
        parent_path: List of parent folder names

    Returns:
        List of endpoint dictionaries
    """
    if parent_path is None:
        parent_path = []

    endpoints = []

    # Get item name
    item_name = item.get("name", "Unnamed")

    # Check if this is a folder (has sub-items)
    sub_items = item.get("item", [])
    if sub_items:
        # This is a folder - recurse into sub-items
        new_path = parent_path + [item_name]
        for sub_item in sub_items:
            endpoints.extend(parse_postman_item(sub_item, new_path))
    else:
        # This is a request
        request_data = item.get("request")
        if not request_data:
            return endpoints

        # Parse request
        request_info = parse_postman_request(request_data)

        # Build endpoint group from folder hierarchy
        group = " / ".join(parent_path) if parent_path else "Endpoints"

        # Build parameters list
        params = []

        # Add path parameters
        for param_name in request_info["path_params"]:
            params.append({
                "name": param_name,
                "in": "path",
                "required": True,
                "type": "string"
            })

        # Add query parameters
        for qp in request_info["query_params"]:
            params.append({
                "name": qp["key"],
                "in": "query",
                "required": False,
                "type": "string",
                "description": qp["description"]
            })

        # Add header parameters
        for header in request_info["headers"]:
            params.append({
                "name": header["key"],
                "in": "header",
                "required": False,
                "type": "string",
                "description": header["description"]
            })

        # Build endpoint dictionary
        endpoint = {
            "group": group,
            "name": item_name,
            "method": request_info["method"],
            "path": request_info["url"]["path"],
            "description": request_info["description"] or item.get("description", ""),
            "params": params,
            "metadata": {
                "raw_url": request_info["url"]["raw"],
                "host": request_info["url"]["host"],
                "protocol": request_info["url"]["protocol"],
                "variables": request_info["url"]["variables"],
                "body": request_info["body"]
            }
        }

        endpoints.append(endpoint)

    return endpoints


def parse_postman_collection(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse a Postman v2.1 collection and extract all endpoints.

    Args:
        data: Parsed Postman collection data

    Returns:
        List of endpoint dictionaries with structure:
        {
            "group": str,          # Folder/category name
            "name": str,           # Request name
            "method": str,         # HTTP method (GET, POST, etc.)
            "path": str,           # URL path
            "description": str,    # Request description
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
                "raw_url": str,
                "host": str,
                "protocol": str,
                "variables": dict,
                "body": dict
            }
        }

    Example:
        >>> with open("collection.json") as f:
        ...     data = json.load(f)
        >>> endpoints = parse_postman_collection(data)
        >>> print(f"Found {len(endpoints)} endpoints")
    """
    endpoints = []

    # Get collection info
    info = data.get("info", {})
    collection_name = info.get("name", "API")

    # Parse all items
    items = data.get("item", [])
    for item in items:
        endpoints.extend(parse_postman_item(item))

    # Add collection name to metadata
    for endpoint in endpoints:
        endpoint["metadata"]["collection"] = collection_name

    return endpoints
