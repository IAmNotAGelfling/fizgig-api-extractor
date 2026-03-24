"""
Format conversion functionality for fizgig-api-extractor.

Converts between API specification formats, primarily OpenAPI → Postman.
"""

import uuid
from typing import Dict, Any, List

from api_extractor.utils import ensure_list


def generate_postman_id() -> str:
    """
    Generate a Postman-compatible UUID.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def openapi_path_to_postman(path: str, base_url: str = "") -> Dict[str, Any]:
    """
    Convert OpenAPI path template to Postman URL object.

    Args:
        path: OpenAPI path template (e.g., "/users/{id}")
        base_url: Base URL from servers

    Returns:
        Postman URL object
    """
    # Split base URL into protocol, host, and base path
    protocol = ""
    host_parts = []
    base_path = ""

    if base_url:
        if "://" in base_url:
            protocol, rest = base_url.split("://", 1)
        else:
            rest = base_url

        if "/" in rest:
            host, base_path = rest.split("/", 1)
            base_path = "/" + base_path
        else:
            host = rest

        host_parts = host.split(".")

    # Combine base path with endpoint path
    full_path = base_path.rstrip("/") + "/" + path.lstrip("/")

    # Split path into segments
    path_segments = [seg for seg in full_path.split("/") if seg]

    # Convert {param} to :param for Postman
    postman_path_segments = []
    for segment in path_segments:
        if segment.startswith("{") and segment.endswith("}"):
            # Convert {id} to :id
            param_name = segment[1:-1]
            postman_path_segments.append(f":{param_name}")
        else:
            postman_path_segments.append(segment)

    return {
        "raw": f"{protocol}://{'.'.join(host_parts)}/{'/'.join(postman_path_segments)}"
        if protocol
        else f"/{'/'.join(postman_path_segments)}",
        "protocol": protocol if protocol else "https",
        "host": host_parts if host_parts else ["localhost"],
        "path": postman_path_segments,
    }


def openapi_parameter_to_postman(param: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert OpenAPI parameter to Postman parameter format.

    Args:
        param: OpenAPI parameter object

    Returns:
        Postman parameter object
    """

    postman_param = {
        "key": param.get("name", ""),
        "value": "",
        "description": param.get("description", ""),
        "disabled": False,
    }

    # Add example value if available
    schema = param.get("schema", {})
    if isinstance(schema, dict):
        example = schema.get("example")
        if example is not None:
            postman_param["value"] = str(example)

    return postman_param


def openapi_request_body_to_postman(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert OpenAPI requestBody to Postman body format.

    Args:
        request_body: OpenAPI requestBody object

    Returns:
        Postman body object
    """
    if not isinstance(request_body, dict):
        return {}

    content = request_body.get("content", {})
    if not isinstance(content, dict):
        return {}

    # Get first content type
    content_types = list(content.keys())
    if not content_types:
        return {}

    content_type = content_types[0]
    media_type = content[content_type]

    body = {"mode": "raw"}

    # Determine mode based on content type
    if "application/json" in content_type:
        body["mode"] = "raw"
        body["options"] = {"raw": {"language": "json"}}

        # Generate example JSON from schema
        schema = media_type.get("schema", {})
        if isinstance(schema, dict):
            example = generate_example_from_schema(schema)
            if example:
                import json

                body["raw"] = json.dumps(example, indent=2)

    elif "application/x-www-form-urlencoded" in content_type:
        body["mode"] = "urlencoded"
        body["urlencoded"] = []

        schema = media_type.get("schema", {})
        if isinstance(schema, dict):
            properties = schema.get("properties", {})
            for prop_name in properties.keys():
                body["urlencoded"].append(
                    {"key": prop_name, "value": "", "type": "text"}
                )

    elif "multipart/form-data" in content_type:
        body["mode"] = "formdata"
        body["formdata"] = []

        schema = media_type.get("schema", {})
        if isinstance(schema, dict):
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if isinstance(prop_schema, dict):
                    param_type = (
                        "file"
                        if prop_schema.get("type") == "string"
                        and prop_schema.get("format") == "binary"
                        else "text"
                    )
                    body["formdata"].append(
                        {"key": prop_name, "value": "", "type": param_type}
                    )

    return body


def _generate_object_example(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate example data for object schema type."""
    properties = schema.get("properties", {})
    example = {}
    for prop_name, prop_schema in properties.items():
        if isinstance(prop_schema, dict):
            example[prop_name] = generate_example_from_schema(prop_schema)
    return example


def _generate_array_example(schema: Dict[str, Any]) -> List[Any]:
    """Generate example data for array schema type."""
    items = schema.get("items", {})
    if isinstance(items, dict):
        return [generate_example_from_schema(items)]
    return []


def generate_example_from_schema(schema: Dict[str, Any]) -> Any:
    """
    Generate example data from OpenAPI schema.

    Args:
        schema: OpenAPI schema object

    Returns:
        Example data matching the schema
    """
    if not isinstance(schema, dict):
        return None

    # Check for explicit example
    if "example" in schema:
        return schema["example"]

    schema_type = schema.get("type", "object")

    # Dispatch to type-specific generators
    type_generators = {
        "object": _generate_object_example,
        "array": _generate_array_example,
        "string": lambda s: s.get("default", "string"),
        "number": lambda s: s.get("default", 0),
        "integer": lambda s: s.get("default", 0),
        "boolean": lambda s: s.get("default", False),
    }

    generator = type_generators.get(schema_type)
    if generator:
        return generator(schema)

    return None


def openapi_operation_to_postman_item(
    path: str, method: str, operation: Dict[str, Any], base_url: str
) -> Dict[str, Any]:
    """
    Convert OpenAPI operation to Postman request item.

    Args:
        path: URL path template
        method: HTTP method
        operation: OpenAPI operation object
        base_url: Base URL from servers

    Returns:
        Postman item object
    """
    name = (
        operation.get("summary")
        or operation.get("operationId")
        or f"{method.upper()} {path}"
    )
    description = operation.get("description", "")

    # Build Postman URL
    url = openapi_path_to_postman(path, base_url)

    # Convert parameters
    header_params = []
    query_params = []

    for param in ensure_list(operation.get("parameters", [])):
        if not isinstance(param, dict):
            continue

        param_in = param.get("in", "query")
        postman_param = openapi_parameter_to_postman(param)

        if param_in == "header":
            header_params.append(postman_param)
        elif param_in == "query":
            query_params.append(postman_param)

    # Add query parameters to URL
    if query_params:
        url["query"] = query_params

    # Build request object
    request = {"method": method.upper(), "header": header_params, "url": url}

    if description:
        request["description"] = description

    # Convert request body
    request_body = operation.get("requestBody")
    if request_body:
        body = openapi_request_body_to_postman(request_body)
        if body:
            request["body"] = body

    return {"name": name, "request": request, "response": []}


def openapi_to_postman(openapi_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert OpenAPI 3.x specification to Postman v2.1 collection.

    Args:
        openapi_data: Parsed OpenAPI specification

    Returns:
        Postman collection object

    Example:
        >>> with open("openapi.yaml") as f:
        ...     openapi_data = yaml.safe_load(f)
        >>> postman_collection = openapi_to_postman(openapi_data)
        >>> with open("collection.json", "w") as f:
        ...     json.dump(postman_collection, f, indent=2)
    """
    # Extract API info
    info = openapi_data.get("info", {})
    api_title = info.get("title", "API")
    api_description = info.get("description", "")

    # Resolve base URL
    servers = ensure_list(openapi_data.get("servers", []))
    base_url = ""
    if servers and isinstance(servers[0], dict):
        base_url = servers[0].get("url", "")

    # Create Postman collection structure
    collection = {
        "info": {
            "_postman_id": generate_postman_id(),
            "name": api_title,
            "description": api_description,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [],
    }

    # Group endpoints by tags
    paths = openapi_data.get("paths", {})
    if not isinstance(paths, dict):
        return collection

    # Collect all operations grouped by tag
    tag_items: Dict[str, List[Dict[str, Any]]] = {}
    untagged_items = []

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        # Path-level parameters
        path_params = ensure_list(path_item.get("parameters", []))

        # Process each HTTP method
        http_methods = ["get", "post", "put", "patch", "delete", "head", "options"]

        for method in http_methods:
            operation = path_item.get(method)
            if not operation or not isinstance(operation, dict):
                continue

            # Merge path-level parameters
            operation_params = ensure_list(operation.get("parameters", []))
            merged_params = path_params + operation_params
            operation_copy = operation.copy()
            operation_copy["parameters"] = merged_params

            # Convert to Postman item
            item = openapi_operation_to_postman_item(
                path, method, operation_copy, base_url
            )

            # Group by tag
            tags = ensure_list(operation.get("tags", []))
            if tags:
                tag = tags[0]
                if tag not in tag_items:
                    tag_items[tag] = []
                tag_items[tag].append(item)
            else:
                untagged_items.append(item)

    # Build collection items with folders for tags
    for tag_name in sorted(tag_items.keys()):
        folder = {"name": tag_name, "item": tag_items[tag_name]}
        collection["item"].append(folder)

    # Add untagged items at the root level
    if untagged_items:
        collection["item"].extend(untagged_items)

    return collection
