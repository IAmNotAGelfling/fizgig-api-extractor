"""
Tests for validate-config CLI command.
"""

import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from api_extractor.cli import app


runner = CliRunner()


class TestCliValidateConfig:
    """Tests for validate-config command."""

    def test_validate_valid_config_file(self):
        """Test validating a valid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_dir = Path(tmpdir)
            config_path = config_dir / ".fizgig-config.json"

            # Create valid input file
            input_file = config_dir / "api.json"
            input_file.write_text('{"openapi": "3.0.0", "info": {}, "paths": {}}')

            # Create valid config
            config = {
                "input": "api.json",
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }
            config_path.write_text(json.dumps(config))

            # Act
            result = runner.invoke(app, ["validate-config", str(config_path)])

            # Assert
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_validate_config_missing_required_field(self):
        """Test validating config with missing required field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_path = Path(tmpdir) / "config.json"
            config = {
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }
            config_path.write_text(json.dumps(config))

            # Act
            result = runner.invoke(app, ["validate-config", str(config_path)])

            # Assert
            assert result.exit_code == 1
            assert "'input' field is required" in result.output

    def test_validate_config_invalid_format(self):
        """Test validating config with invalid export format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_path = Path(tmpdir) / "config.json"
            config = {
                "input": "api.json",
                "exports": [
                    {"format": "invalid", "output": "api.txt"}
                ]
            }
            config_path.write_text(json.dumps(config))

            # Act
            result = runner.invoke(app, ["validate-config", str(config_path)])

            # Assert
            assert result.exit_code == 1
            assert "Invalid format" in result.output

    def test_validate_config_missing_input_file(self):
        """Test validating config with missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_path = Path(tmpdir) / "config.json"
            config = {
                "input": "nonexistent.json",
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }
            config_path.write_text(json.dumps(config))

            # Act
            result = runner.invoke(app, ["validate-config", str(config_path)])

            # Assert
            assert result.exit_code == 1
            assert "Input file not found" in result.output

    def test_validate_config_missing_template(self):
        """Test validating config with missing template file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_dir = Path(tmpdir)
            config_path = config_dir / "config.json"

            # Create valid input file
            input_file = config_dir / "api.json"
            input_file.write_text('{"openapi": "3.0.0", "info": {}, "paths": {}}')

            # Create config with missing template
            config = {
                "input": "api.json",
                "exports": [
                    {"format": "html", "output": "api.html", "template": "nonexistent.html"}
                ]
            }
            config_path.write_text(json.dumps(config))

            # Act
            result = runner.invoke(app, ["validate-config", str(config_path)])

            # Assert
            assert result.exit_code == 1
            assert "Template file not found" in result.output

    def test_validate_config_with_url_input(self):
        """Test validating config with URL input (skips file check)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_path = Path(tmpdir) / "config.json"
            config = {
                "input": "https://api.example.com/spec.json",
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }
            config_path.write_text(json.dumps(config))

            # Act
            result = runner.invoke(app, ["validate-config", str(config_path)])

            # Assert
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_validate_config_invalid_json(self):
        """Test validating config with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{not valid json")

            # Act
            result = runner.invoke(app, ["validate-config", str(config_path)])

            # Assert
            assert result.exit_code == 1
            assert "JSON" in result.output or "json" in result.output

    def test_validate_config_missing_file(self):
        """Test validating non-existent config file."""
        # Act
        result = runner.invoke(app, ["validate-config", "nonexistent.json"])

        # Assert
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_validate_config_auto_discover(self):
        """Test validate-config with auto-discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Arrange
                config_path = Path(".fizgig-config.json")

                # Create valid input file
                input_file = Path("api.json")
                input_file.write_text('{"openapi": "3.0.0", "info": {}, "paths": {}}')

                # Create valid config
                config = {
                    "input": "api.json",
                    "exports": [
                        {"format": "json", "output": "api.json"}
                    ]
                }
                config_path.write_text(json.dumps(config))

                # Act
                result = runner.invoke(app, ["validate-config"])

                # Assert
                assert result.exit_code == 0
                assert "valid" in result.output.lower()

            finally:
                os.chdir(old_cwd)

    def test_validate_config_auto_discover_not_found(self):
        """Test validate-config auto-discovery when no config found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result = runner.invoke(app, ["validate-config"])

                # Assert
                assert result.exit_code == 1
                assert "No config file found" in result.output

            finally:
                os.chdir(old_cwd)
