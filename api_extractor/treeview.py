"""
TUI tree viewer for fizgig-api-extractor.

Displays API endpoints in a tree structure using Rich.
"""

from typing import List, Dict, Any

from rich.console import Console
from rich.tree import Tree
from rich.text import Text

from api_extractor.utils import group_by_tag


def get_method_style(method: str) -> str:
    """
    Get Rich style for HTTP method.

    Args:
        method: HTTP method

    Returns:
        Rich style string
    """
    method = method.upper()

    styles = {
        "GET": "bold cyan",
        "POST": "bold green",
        "PUT": "bold yellow",
        "PATCH": "bold magenta",
        "DELETE": "bold red",
        "HEAD": "bold blue",
        "OPTIONS": "bold white",
        "TRACE": "bold white",
    }

    return styles.get(method, "bold white")


def display_tree(endpoints: List[Dict[str, Any]], show_params: bool = False) -> None:
    """
    Display API endpoints in a tree structure.

    Args:
        endpoints: List of endpoint dictionaries
        show_params: Whether to show parameter details (default: False)

    Example:
        >>> endpoints = parse_postman_collection(data)
        >>> display_tree(endpoints)
        API Endpoints
        ├── Users
        │   ├── GET /users — List users
        │   ├── POST /users — Create user
        │   └── GET /users/{id} — Get user by ID
        └── Posts
            ├── GET /posts — List posts
            └── POST /posts — Create post
    """
    console = Console()

    # Create root tree
    tree = Tree(Text("API Endpoints", style="bold blue"), guide_style="bright_black")

    # Group endpoints by category
    grouped = group_by_tag(endpoints, "group")

    # Add groups and endpoints
    for group_name in sorted(grouped.keys()):
        group_endpoints = grouped[group_name]

        # Create group node
        group_node = tree.add(
            Text(group_name, style="bold magenta"), guide_style="bright_black"
        )

        # Add endpoints to group
        for endpoint in group_endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "")
            name = endpoint.get("name", "")
            description = endpoint.get("description", "")
            params = endpoint.get("params", [])
            deprecated = endpoint.get("metadata", {}).get("deprecated", False)

            # Build endpoint label
            method_text = Text(f"{method:6s}", style=get_method_style(method))
            path_text = Text(f" {path}", style="cyan")

            if name and name != method:
                name_text = Text(f" — {name}", style="dim")
            else:
                name_text = Text()

            if deprecated:
                deprecated_text = Text(" [DEPRECATED]", style="bold red")
            else:
                deprecated_text = Text()

            endpoint_label = method_text + path_text + name_text + deprecated_text
            endpoint_node = group_node.add(endpoint_label)

            # Add description if available
            if show_params and description:
                endpoint_node.add(
                    Text(f"Description: {description}", style="dim italic")
                )

            # Add parameters if requested
            if show_params and params:
                params_node = endpoint_node.add(Text("Parameters:", style="bold"))

                for param in params:
                    param_name = param.get("name", "")
                    param_in = param.get("in", "")
                    param_type = param.get("type", "")
                    param_required = param.get("required", False)
                    param_desc = param.get("description", "")

                    # Build parameter label
                    param_label = Text()
                    param_label.append(param_name, style="bold cyan")
                    param_label.append(f" ({param_in}, {param_type}", style="dim")

                    if param_required:
                        param_label.append(", required", style="bold red")
                    else:
                        param_label.append(", optional", style="dim")

                    param_label.append(")", style="dim")

                    if param_desc:
                        param_label.append(f" — {param_desc}", style="dim italic")

                    params_node.add(param_label)

    # Print tree
    console.print()
    console.print(tree)
    console.print()

    # Print summary
    total_endpoints = len(endpoints)
    total_groups = len(grouped)

    console.print(
        f"[bold]Total:[/bold] {total_endpoints} endpoint(s) in {total_groups} group(s)"
    )
    console.print()
