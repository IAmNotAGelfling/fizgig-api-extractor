"""
Configuration file handling for fizgig-api-extractor.

Handles loading, validating, and executing config-based exports.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class ConfigError(Exception):
    """Raised when config is invalid."""
    pass


def find_config_file() -> Optional[Path]:
    """
    Look for .fizgig-config.json in current directory.

    Returns:
        Path to config file or None if not found
    """
    config_path = Path.cwd() / ".fizgig-config.json"
    if config_path.exists():
        return config_path
    return None


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load and validate config file.

    Args:
        config_path: Path to config file, or None for auto-discovery

    Returns:
        Validated config dict

    Raises:
        ConfigError: If config is invalid
        FileNotFoundError: If specified config not found
        json.JSONDecodeError: If JSON is invalid
    """
    # Auto-discover if not specified
    if config_path is None:
        found_config = find_config_file()
        if found_config is None:
            raise FileNotFoundError("No config file found in current directory")
        config_path = str(found_config)

    # Load JSON
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Validate
    validate_config(config)

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate config schema.

    Raises:
        ConfigError: With helpful message about what's wrong
    """
    # Check required fields
    if "input" not in config:
        raise ConfigError("'input' field is required in config")

    if "exports" not in config:
        raise ConfigError("'exports' field is required in config")

    if not isinstance(config["exports"], list):
        raise ConfigError("'exports' must be an array")

    if len(config["exports"]) == 0:
        raise ConfigError("'exports' must contain at least one export")

    # Validate each export
    valid_formats = ["markdown", "csv", "json", "html"]

    for idx, export in enumerate(config["exports"]):
        if not isinstance(export, dict):
            raise ConfigError(f"exports[{idx}]: must be a dictionary")

        if "format" not in export:
            raise ConfigError(f"exports[{idx}]: 'format' field is required")

        if "output" not in export:
            raise ConfigError(f"exports[{idx}]: 'output' field is required")

        format_value = export["format"]
        if format_value not in valid_formats:
            # Provide suggestion
            suggestions = [f for f in valid_formats if f.startswith(format_value[:2])]
            suggestion_text = f" Did you mean '{suggestions[0]}'?" if suggestions else ""
            raise ConfigError(
                f"exports[{idx}]: Invalid format '{format_value}' - "
                f"must be one of: {', '.join(valid_formats)}.{suggestion_text}"
            )

        # Validate field mapping if present
        if "fields" in export and export["fields"] is not None:
            if not isinstance(export["fields"], dict):
                raise ConfigError(f"exports[{idx}]: 'fields' must be a dictionary")


def validate_config_deep(config: Dict[str, Any], config_dir: Path) -> Dict[str, Any]:
    """
    Deep validation including file existence checks.

    Args:
        config: Config dictionary
        config_dir: Directory containing config file

    Returns:
        {
            "valid": bool,
            "errors": [
                {
                    "path": "exports[0].format",
                    "message": "Invalid format 'htm'",
                    "suggestion": "Did you mean 'html'?"
                }
            ]
        }
    """
    errors = []

    # First do basic validation
    try:
        validate_config(config)
    except ConfigError as e:
        return {
            "valid": False,
            "errors": [{"path": "config", "message": str(e)}]
        }

    # Check input file exists (if not a URL)
    input_path = config["input"]
    if not (input_path.startswith('http://') or input_path.startswith('https://')):
        # Try relative to config dir first, then absolute
        resolved_path = None
        if not Path(input_path).is_absolute():
            config_input = config_dir / input_path
            if config_input.exists():
                resolved_path = config_input
        else:
            if Path(input_path).exists():
                resolved_path = Path(input_path)

        if resolved_path is None:
            errors.append({
                "path": "input",
                "message": f"Input file not found: {input_path}",
                "suggestion": f"Checked: {config_dir / input_path}"
            })

    # Check templates exist
    for idx, export in enumerate(config["exports"]):
        if "template" in export and export["template"]:
            template_path = export["template"]

            # Try resolution order
            found = False
            tried_paths = []

            # 1. Relative to config dir
            path1 = config_dir / template_path
            tried_paths.append(str(path1))
            if path1.exists():
                found = True

            # 2. Relative to CWD
            if not found:
                path2 = Path.cwd() / template_path
                tried_paths.append(str(path2))
                if path2.exists():
                    found = True

            # 3. Absolute
            if not found:
                path3 = Path(template_path)
                tried_paths.append(str(path3))
                if path3.exists():
                    found = True

            if not found:
                errors.append({
                    "path": f"exports[{idx}].template",
                    "message": f"Template file not found: {template_path}",
                    "suggestion": f"Searched in:\n    " + "\n    ".join(tried_paths)
                })

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def run_exports_from_config(config_path: Optional[str] = None,
                           cli_overrides: Optional[Dict[str, Any]] = None) -> None:
    """
    Execute all exports defined in config file.

    Loads input once, then runs each export sequentially.
    CLI overrides can override config values.

    Args:
        config_path: Path to config file, or None for auto-discovery
        cli_overrides: Optional dict of CLI flag overrides

    Raises:
        ConfigError: If config is invalid
        FileNotFoundError: If config or input files not found
    """
    from api_extractor.loader import load_api_file
    from api_extractor.parser_postman import parse_postman_collection
    from api_extractor.parser_openapi import parse_openapi_spec
    from api_extractor.exporter import export_markdown, export_csv, export_json, export_html

    # Load config
    config = load_config(config_path)
    config_dir = Path(config_path).parent if config_path else Path.cwd()

    # Apply CLI overrides
    if cli_overrides:
        if "input" in cli_overrides and cli_overrides["input"]:
            config["input"] = cli_overrides["input"]
        if "headers" in cli_overrides and cli_overrides["headers"]:
            config["headers"] = cli_overrides["headers"]

    # Load input file/URL once
    input_path = config["input"]
    headers = config.get("headers")
    data, detected_format = load_api_file(input_path, headers=headers)

    # Parse endpoints once
    if detected_format == "postman":
        endpoints = parse_postman_collection(data)
    elif detected_format == "openapi":
        endpoints = parse_openapi_spec(data)
    else:
        raise ValueError(f"Unknown format: {detected_format}")

    # Run each export
    for export_cfg in config["exports"]:
        export_format = export_cfg["format"]
        output_path = export_cfg["output"]

        # Apply CLI overrides for this export
        if cli_overrides:
            if "format" in cli_overrides and cli_overrides["format"]:
                export_format = cli_overrides["format"]
            if "output" in cli_overrides and cli_overrides["output"]:
                output_path = cli_overrides["output"]

        # Get format-specific options
        field_map = export_cfg.get("fields")
        plain_text = export_cfg.get("plain_text", False)
        template_path = export_cfg.get("template")
        delimiter = export_cfg.get("delimiter", ',')
        quoting = export_cfg.get("quoting", 'minimal')

        # Apply CLI overrides for format-specific options
        if cli_overrides:
            if "plain_text" in cli_overrides:
                plain_text = cli_overrides["plain_text"]
            if "template" in cli_overrides and cli_overrides["template"]:
                template_path = cli_overrides["template"]

        # Execute export based on format
        if export_format == "markdown" or export_format == "md":
            export_markdown(endpoints, output_path)
        elif export_format == "csv":
            export_csv(endpoints, output_path, field_map=field_map,
                      delimiter=delimiter, quoting=quoting)
        elif export_format == "json":
            export_json(endpoints, output_path, plain_text=plain_text,
                       field_map=field_map)
        elif export_format == "html":
            export_html(endpoints, output_path, template_path=template_path,
                       config_dir=config_dir)
        else:
            raise ValueError(f"Unknown format: {export_format}")

