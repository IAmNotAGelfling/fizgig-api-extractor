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
        help="Path to Postman collection, OpenAPI spec (JSON/YAML), or HTTP(S) URL"
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
    ),
    plain_text: bool = typer.Option(
        False,
        "--plain-text",
        help="Convert markdown descriptions to plain text (JSON format only)"
    ),
    header: Optional[list[str]] = typer.Option(
        None,
        "--header",
        help="Custom HTTP header for URL requests (repeatable, format: 'Name: Value')"
    ),
    save_url: Optional[str] = typer.Option(
        None,
        "--save-url",
        help="Save URL content to file (optional path, defaults to filename from URL)"
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (auto-discovers .fizgig-config.json if not specified)"
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Path to custom HTML template (HTML format only)"
    )
) -> None:
    """
    Extract API endpoints from a Postman collection, OpenAPI spec, or URL.

    Examples:

        # Display as tree
        fizgig-api-extractor extract api.json

        # Export to Markdown
        fizgig-api-extractor extract api.json -o endpoints.md -f markdown

        # Export to CSV
        fizgig-api-extractor extract openapi.yaml -o endpoints.csv -f csv

        # Export to JSON
        fizgig-api-extractor extract collection.json -o endpoints.json -f json

        # Export to JSON with plain text descriptions (no markdown)
        fizgig-api-extractor extract collection.json -o endpoints.json -f json --plain-text

        # Export to HTML
        fizgig-api-extractor extract api.yaml -o endpoints.html -f html

        # Fetch from URL
        fizgig-api-extractor extract https://api.example.com/openapi.yaml

        # Fetch from URL with authentication
        fizgig-api-extractor extract https://api.example.com/spec.json \\
            --header "Authorization: Bearer token123"

        # Fetch from URL and save locally
        fizgig-api-extractor extract https://api.example.com/openapi.yaml --save-url
        fizgig-api-extractor extract https://api.example.com/spec --save-url custom.json
    """
    try:
        # Check if using config file
        if config:
            from api_extractor.config import run_exports_from_config

            # Parse headers for CLI override
            headers_dict = None
            if header:
                headers_dict = {}
                for h in header:
                    if ':' not in h:
                        console_err.print(f"[red]✗[/red] Invalid header format: '{h}'")
                        console_err.print("Expected format: 'Name: Value'")
                        raise typer.Exit(1)
                    name, value = h.split(':', 1)
                    headers_dict[name.strip()] = value.strip()

            # Build CLI overrides
            cli_overrides = {
                "input": input_file if input_file != "api.json" else None,  # Only override if not default
                "headers": headers_dict,
                "format": format if output_file else None,
                "output": output_file,
                "plain_text": plain_text,
                "template": template
            }

            # Remove None values
            cli_overrides = {k: v for k, v in cli_overrides.items() if v is not None}

            # Run exports from config
            console.print(f"[bold]Loading config[/bold] from {config}...")
            run_exports_from_config(config, cli_overrides)
            console.print("[green]✓[/green] All exports completed")
            return

        # Standard CLI-only mode (no config)
        # Parse headers if provided
        headers_dict = None
        if header:
            headers_dict = {}
            for h in header:
                if ':' not in h:
                    console_err.print(f"[red]✗[/red] Invalid header format: '{h}'")
                    console_err.print("Expected format: 'Name: Value'")
                    raise typer.Exit(1)
                name, value = h.split(':', 1)
                headers_dict[name.strip()] = value.strip()

        # Determine save path for URL
        save_path = None
        if save_url is not None:
            # If save_url is empty string (flag without value), set to None to auto-derive
            save_path = save_url if save_url else None

        # Load and detect format
        is_url = input_file.startswith('http://') or input_file.startswith('https://')
        console.print(f"[bold]Loading[/bold] {input_file}...")
        data, detected_format = load_api_file(input_file, headers=headers_dict, save_path=save_path)

        if is_url and save_path is not None:
            console.print(f"[green]✓[/green] Saved to [bold]{save_path}[/bold]")

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
            export_json(endpoints, output_file, plain_text=plain_text)
        elif format_lower == "html":
            export_html(endpoints, output_file, template_path=template)
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

        console.print("[green]✓[/green] Loaded OpenAPI spec")

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


@app.command()
def init(
    config_only: bool = typer.Option(
        False,
        "--config-only",
        help="Only create config file, skip template"
    ),
    template_only: bool = typer.Option(
        False,
        "--template-only",
        help="Only create template, skip config file"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="Output directory (defaults to current directory)"
    )
) -> None:
    """
    Initialize fizgig-api-extractor with example config and template.

    Creates:
    - .fizgig-config.json with example configuration
    - templates/default.html with the default HTML template

    Examples:

        # Create both config and template
        fizgig-api-extractor init

        # Only create config file
        fizgig-api-extractor init --config-only

        # Only create template
        fizgig-api-extractor init --template-only

        # Create in custom directory
        fizgig-api-extractor init --output-dir ./my-project
    """
    try:
        import importlib.resources as pkg_resources
        from api_extractor import resources

        # Determine output directory
        if output_dir:
            base_dir = Path(output_dir)
            base_dir.mkdir(parents=True, exist_ok=True)
        else:
            base_dir = Path.cwd()

        # Create config file unless --template-only
        if not template_only:
            config_path = base_dir / ".fizgig-config.json"

            if config_path.exists():
                console_err.print(f"[red]✗[/red] Config file already exists: {config_path}")
                raise typer.Exit(1)

            # Example config structure
            example_config = {
                "input": "api.json",
                "headers": {
                    "Authorization": "Bearer YOUR_TOKEN_HERE"
                },
                "exports": [
                    {
                        "format": "markdown",
                        "output": "docs/api-endpoints.md"
                    },
                    {
                        "format": "csv",
                        "output": "reports/endpoints.csv",
                        "delimiter": ",",
                        "quoting": "minimal",
                        "fields": {
                            "method": "HTTP Method",
                            "path": "Endpoint Path",
                            "description": "Description"
                        }
                    },
                    {
                        "format": "json",
                        "output": "data/endpoints.json",
                        "plain_text": False,
                        "fields": {
                            "name": "endpoint_name",
                            "method": "http_method",
                            "path": "url_path"
                        }
                    },
                    {
                        "format": "html",
                        "output": "web/api-docs.html",
                        "template": "templates/custom.html"
                    }
                ]
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(example_config, f, indent=2, ensure_ascii=False)

            console.print(f"[green]✓[/green] Created config file: [bold]{config_path}[/bold]")

        # Create template file unless --config-only
        if not config_only:
            template_dir = base_dir / "templates"
            template_path = template_dir / "default.html"

            if template_path.exists():
                console_err.print(f"[red]✗[/red] Template file already exists: {template_path}")
                raise typer.Exit(1)

            template_dir.mkdir(parents=True, exist_ok=True)

            # Load default template from package resources
            try:
                template_content = pkg_resources.files(resources).joinpath('templates/default.html').read_text(encoding='utf-8')
            except Exception:
                # Fallback for older Python versions
                with pkg_resources.path(resources, 'templates') as templates_path:
                    default_template = templates_path / 'default.html'
                    template_content = default_template.read_text(encoding='utf-8')

            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)

            console.print(f"[green]✓[/green] Created template file: [bold]{template_path}[/bold]")

        console.print("\n[bold]Next steps:[/bold]")
        if not template_only:
            console.print("1. Edit .fizgig-config.json with your API spec path and export settings")
        if not config_only:
            console.print("2. Customize templates/default.html if needed")
        console.print("3. Run: fizgig-api-extractor extract --config .fizgig-config.json")

    except Exception as e:
        console_err.print(f"[red]✗[/red] Unexpected error: {e}")
        raise typer.Exit(1)


@app.command()
def validate_config(
    config_path: Optional[str] = typer.Argument(
        None,
        help="Path to config file (auto-discovers .fizgig-config.json if not specified)"
    )
) -> None:
    """
    Validate a config file without running exports.

    Performs comprehensive validation:
    - JSON syntax and structure
    - Required fields (input, exports)
    - Export format validity
    - Input file existence (if local path)
    - Template file existence (if specified)

    Examples:

        # Validate specific config file
        fizgig-api-extractor validate-config my-config.json

        # Auto-discover and validate .fizgig-config.json
        fizgig-api-extractor validate-config
    """
    try:
        from api_extractor.config import load_config, validate_config_deep

        # Load config (auto-discovers if path not specified)
        console.print("[bold]Loading config[/bold]...")
        try:
            config = load_config(config_path)
        except FileNotFoundError as e:
            console_err.print(f"[red]✗[/red] {e}")
            raise typer.Exit(1)
        except json.JSONDecodeError as e:
            console_err.print(f"[red]✗[/red] Invalid JSON: {e}")
            raise typer.Exit(1)

        # Determine config directory for deep validation
        if config_path:
            config_dir = Path(config_path).parent
        else:
            config_dir = Path.cwd()

        console.print("[green]✓[/green] Config structure valid")

        # Deep validation (file existence checks)
        console.print("[bold]Validating file references[/bold]...")
        validation_result = validate_config_deep(config, config_dir)

        if validation_result["valid"]:
            console.print("[green]✓[/green] All file references valid")
            console.print("\n[bold green]Config is valid![/bold green]")
            console.print("\nConfig summary:")
            console.print(f"  Input: [bold]{config['input']}[/bold]")
            console.print(f"  Exports: [bold]{len(config['exports'])}[/bold] configured")
            return

        # Display validation errors
        console.print("[red]✗[/red] Validation failed\n")
        for error in validation_result["errors"]:
            console_err.print(f"[red]●[/red] {error['path']}")
            console_err.print(f"  {error['message']}")
            if "suggestion" in error:
                console_err.print(f"  [dim]{error['suggestion']}[/dim]")
            console_err.print()

        raise typer.Exit(1)

    except Exception as e:
        if isinstance(e, typer.Exit):
            raise
        console_err.print(f"[red]✗[/red] Unexpected error: {e}")
        raise typer.Exit(1)


# Default behavior: if no command is provided, display help
if __name__ == "__main__":
    app()
