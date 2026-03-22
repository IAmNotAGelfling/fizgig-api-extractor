"""
CLI interface for fizgig-api-extractor.

Provides command-line interface using Typer.
"""

import sys
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from api_extractor import __version__
from api_extractor.loader import load_api_file
from api_extractor.parser_postman import parse_postman_collection
from api_extractor.parser_openapi import parse_openapi_spec
from api_extractor.exporter import export_markdown, export_csv, export_json, export_html
from api_extractor.converter import openapi_to_postman
from api_extractor.treeview import display_tree


app = typer.Typer(
    name="fizgig-api-extractor",
    help="Parse Postman collections and OpenAPI specs, extract endpoints, and export in multiple formats.",
    add_completion=False,
    no_args_is_help=True
)

import os

# Fix Windows console encoding for Unicode support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

console = Console()
console_err = Console(stderr=True)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"fizgig-api-extractor version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
) -> None:
    """
    fizgig-api-extractor: Parse Postman collections and OpenAPI specs.
    """
    pass


@app.command()
def extract(
    input_file: str = typer.Argument(
        ...,
        help="Path to Postman collection or OpenAPI spec (JSON/YAML)"
    ),
    output_file: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path"
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown, csv, json, html"
    ),
    pretty: bool = typer.Option(
        False,
        "--pretty",
        "-p",
        help="Pretty print tree to console (default action if no output file)"
    )
) -> None:
    """
    Extract API endpoints from a Postman collection or OpenAPI spec.

    Examples:

        # Display as tree
        fizgig-api-extractor extract api.json

        # Export to Markdown
        fizgig-api-extractor extract api.json -o endpoints.md -f markdown

        # Export to CSV
        fizgig-api-extractor extract openapi.yaml -o endpoints.csv -f csv

        # Export to JSON
        fizgig-api-extractor extract collection.json -o endpoints.json -f json

        # Export to HTML
        fizgig-api-extractor extract api.yaml -o endpoints.html -f html
    """
    try:
        # Load and detect format
        console.print(f"[bold]Loading[/bold] {input_file}...")
        data, detected_format = load_api_file(input_file)
        console.print(f"[green]✓[/green] Detected format: [bold]{detected_format}[/bold]")

        # Parse endpoints
        console.print("[bold]Parsing[/bold] endpoints...")
        if detected_format == "postman":
            endpoints = parse_postman_collection(data)
        elif detected_format == "openapi":
            endpoints = parse_openapi_spec(data)
        else:
            console_err.print(f"[red]✗[/red] Unknown format: {detected_format}")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Extracted [bold]{len(endpoints)}[/bold] endpoint(s)")

        # If no output file, display tree
        if not output_file:
            display_tree(endpoints, show_params=pretty)
            return

        # Export to specified format
        format_lower = format.lower()
        console.print(f"[bold]Exporting[/bold] to {format_lower}...")

        if format_lower == "markdown" or format_lower == "md":
            export_markdown(endpoints, output_file)
        elif format_lower == "csv":
            export_csv(endpoints, output_file)
        elif format_lower == "json":
            export_json(endpoints, output_file)
        elif format_lower == "html":
            export_html(endpoints, output_file)
        else:
            console_err.print(f"[red]✗[/red] Unknown format: {format}")
            console_err.print("Supported formats: markdown, csv, json, html")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Exported to [bold]{output_file}[/bold]")

    except FileNotFoundError as e:
        console_err.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console_err.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console_err.print(f"[red]✗[/red] Unexpected error: {e}")
        raise typer.Exit(1)


@app.command()
def convert(
    input_file: str = typer.Argument(
        ...,
        help="Path to OpenAPI spec (JSON/YAML)"
    ),
    output_file: str = typer.Argument(
        ...,
        help="Output Postman collection file path (JSON)"
    )
) -> None:
    """
    Convert OpenAPI spec to Postman collection.

    Example:

        fizgig-api-extractor convert openapi.yaml collection.json
    """
    try:
        # Load and detect format
        console.print(f"[bold]Loading[/bold] {input_file}...")
        data, detected_format = load_api_file(input_file)

        if detected_format != "openapi":
            console_err.print(f"[red]✗[/red] Input file is not an OpenAPI spec (detected: {detected_format})")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] Loaded OpenAPI spec")

        # Convert to Postman
        console.print("[bold]Converting[/bold] to Postman collection...")
        postman_collection = openapi_to_postman(data)

        # Count endpoints
        total_items = 0
        for item in postman_collection.get("item", []):
            if "item" in item:
                # Folder
                total_items += len(item["item"])
            else:
                # Single item
                total_items += 1

        console.print(f"[green]✓[/green] Converted [bold]{total_items}[/bold] endpoint(s)")

        # Write output
        console.print(f"[bold]Writing[/bold] to {output_file}...")
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(postman_collection, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓[/green] Written to [bold]{output_file}[/bold]")

    except FileNotFoundError as e:
        console_err.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console_err.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console_err.print(f"[red]✗[/red] Unexpected error: {e}")
        raise typer.Exit(1)


@app.command()
def tree(
    input_file: str = typer.Argument(
        ...,
        help="Path to Postman collection or OpenAPI spec (JSON/YAML)"
    ),
    show_params: bool = typer.Option(
        False,
        "--params",
        "-p",
        help="Show parameter details"
    )
) -> None:
    """
    Display API endpoints in a tree view.

    Example:

        fizgig-api-extractor tree api.json
        fizgig-api-extractor tree api.json --params
    """
    try:
        # Load and detect format
        data, detected_format = load_api_file(input_file)

        # Parse endpoints
        if detected_format == "postman":
            endpoints = parse_postman_collection(data)
        elif detected_format == "openapi":
            endpoints = parse_openapi_spec(data)
        else:
            console_err.print(f"[red]✗[/red] Unknown format: {detected_format}")
            raise typer.Exit(1)

        # Display tree
        display_tree(endpoints, show_params=show_params)

    except FileNotFoundError as e:
        console_err.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console_err.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console_err.print(f"[red]✗[/red] Unexpected error: {e}")
        raise typer.Exit(1)


# Default behavior: if no command is provided, display help
if __name__ == "__main__":
    app()
