"""
OpenAPI specification parser for fizgig-api-extractor.

Parses OpenAPI 3.x specifications (JSON and YAML) and extracts endpoint information.
"""

from typing import Dict, Any, List, Optional

from api_extractor.utils import safe_get, format_method, normalise_url, ensure_list


def resolve_server_url(servers: List[Dict[str, Any]]) -> str:
    """
    Resolve the base URL from OpenAPI servers array.

    Args:
        servers: List of server objects from OpenAPI spec

    Returns:
        Base URL string (empty if no servers defined)
    """
    if not servers or not isinstance(servers, list) or len(servers) == 0:
        return ""

    # Use first server
    server = servers[0]
    if not isinstance(server, dict):
        return ""

    url = server.get("url", "")

    # Replace variables with defaults
    variables = server.get("variables", {})
    if isinstance(variables, dict):
        for var_name, var_data in variables.items():
            if isinstance(var_data, dict):
                default_value = var_data.get("default", "")
                placeholder = f"{{{var_name}}}"
                url = url.replace(placeholder, str(default_value))

    return url


def parse_openapi_parameter(param: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse an OpenAPI parameter object.

    Args:
        param: Parameter object from OpenAPI spec

    Returns:
        Normalized parameter dictionary
    """
    schema = param.get("schema", {})
    param_type = "string"

    if isinstance(schema, dict):
        param_type = schema.get("type", "string")

    return {
        "name": param.get("name", ""),
        "in": param.get("in", "query"),
        "required": param.get("required", False),
        "type": param_type,
        "description": param.get("description", "")
    }


def parse_openapi_request_body(request_body: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse an OpenAPI requestBody object into parameter format.

    Args:
        request_body: RequestBody object from OpenAPI spec

    Returns:
        List of parameter dictionaries representing the request body
    """
    params = []

    if not isinstance(request_body, dict):
        return params

    content = request_body.get("content", {})
    if not isinstance(content, dict):
        return params

    required = request_body.get("required", False)
    description = request_body.get("description", "")

    # Get first content type (usually application/json)
    content_types = list(content.keys())
    if not content_types:
        return params

    first_content_type = content_types[0]
    media_type = content[first_content_type]

    if not isinstance(media_type, dict):
        return params

    schema = media_type.get("schema", {})
    if not isinstance(schema, dict):
        return params

    # Extract properties from schema
    properties = schema.get("properties", {})
    required_fields = ensure_list(schema.get("required", []))

    if isinstance(properties, dict):
        for prop_name, prop_schema in properties.items():
            if isinstance(prop_schema, dict):
                params.append({
                    "name": prop_name,
                    "in": "body",
                    "required": prop_name in required_fields,
                    "type": prop_schema.get("type", "string"),
                    "description": prop_schema.get("description", "")
                })
    else:
        # If no properties, add a generic body parameter
        params.append({
            "name": "body",
            "in": "body",
            "required": required,
            "type": schema.get("type", "object"),
            "description": description
        })

    return params


def parse_openapi_responses(responses: Dict[str, Any]) -> List[str]:
    """
    Extract response status codes from OpenAPI responses object.

    Args:
        responses: Responses object from OpenAPI spec

    Returns:
        List of status codes
    """
    if not isinstance(responses, dict):
        return []

    return [str(code) for code in responses.keys() if code != "default"]


def parse_openapi_operation(
    path: str,
    method: str,
    operation: Dict[str, Any],
    base_url: str,
    global_tags: List[str] = None
) -> Dict[str, Any]:
    """
    Parse an OpenAPI operation (endpoint).

    Args:
        path: URL path template
        method: HTTP method
        operation: Operation object from OpenAPI spec
        base_url: Base URL from servers
        global_tags: Global tags from spec

    Returns:
        Endpoint dictionary
    """
    # Extract operation details
    operation_id = operation.get("operationId", "")
    summary = operation.get("summary", "")
    description = operation.get("description", "")
    tags = ensure_list(operation.get("tags", []))
    deprecated = operation.get("deprecated", False)

    # Use first tag as group, or "Endpoints" if no tags
    group = tags[0] if tags else "Endpoints"

    # Use summary as name, fallback to operationId or method
    name = summary or operation_id or method.upper()

    # Parse parameters
    params = []

    # Global and operation-level parameters
    for param in ensure_list(operation.get("parameters", [])):
        if isinstance(param, dict):
            params.append(parse_openapi_parameter(param))

    # Request body
    request_body = operation.get("requestBody")
    if request_body:
        params.extend(parse_openapi_request_body(request_body))

    # Parse responses
    responses = parse_openapi_responses(operation.get("responses", {}))

    # Build full URL
    full_path = normalise_url(path, base_url)

    return {
        "group": group,
        "name": name,
        "method": format_method(method),
        "path": full_path,
        "description": description or summary,
        "params": params,
        "metadata": {
            "operation_id": operation_id,
            "tags": tags,
            "deprecated": deprecated,
            "responses": responses,
            "path_template": path
        }
    }


def parse_openapi_spec(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse an OpenAPI 3.x specification and extract all endpoints.

    Args:
        data: Parsed OpenAPI specification data

    Returns:
        List of endpoint dictionaries with structure:
        {
            "group": str,          # Tag/category name
            "name": str,           # Operation summary or operationId
            "method": str,         # HTTP method (GET, POST, etc.)
            "path": str,           # Full URL path with base URL
            "description": str,    # Operation description
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
                "operation_id": str,
                "tags": list,
                "deprecated": bool,
                "responses": list,
                "path_template": str
            }
        }

    Example:
        >>> with open("openapi.yaml") as f:
        ...     data = yaml.safe_load(f)
        >>> endpoints = parse_openapi_spec(data)
        >>> print(f"Found {len(endpoints)} endpoints")
    """
    endpoints = []

    # Extract API info
    info = data.get("info", {})
    api_title = info.get("title", "API")
    api_version = info.get("version", "1.0.0")

    # Resolve base URL from servers
    servers = ensure_list(data.get("servers", []))
    base_url = resolve_server_url(servers)

    # Extract global tags
    global_tags = [tag.get("name") for tag in ensure_list(data.get("tags", [])) if isinstance(tag, dict)]

    # Parse paths
    paths = data.get("paths", {})
    if not isinstance(paths, dict):
        return endpoints

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        # Path-level parameters (apply to all operations)
        path_params = ensure_list(path_item.get("parameters", []))

        # Iterate through HTTP methods
        http_methods = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]

        for method in http_methods:
            operation = path_item.get(method)
            if not operation or not isinstance(operation, dict):
                continue

            # Merge path-level parameters with operation parameters
            operation_params = ensure_list(operation.get("parameters", []))
            merged_params = path_params + operation_params

            # Create a copy of operation with merged parameters
            operation_copy = operation.copy()
            operation_copy["parameters"] = merged_params

            # Parse operation
            endpoint = parse_openapi_operation(
                path=path,
                method=method,
                operation=operation_copy,
                base_url=base_url,
                global_tags=global_tags
            )

            # Add API info to metadata
            endpoint["metadata"]["api_title"] = api_title
            endpoint["metadata"]["api_version"] = api_version

            endpoints.append(endpoint)

    return endpoints
