"""
Tests for config file functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from api_extractor.config import (
    find_config_file,
    load_config,
    validate_config,
    validate_config_deep,
    ConfigError
)


class TestFindConfigFile:
    """Tests for config file auto-discovery."""

    def test_find_config_in_cwd(self):
        """Test finding config file in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_path = Path(tmpdir) / ".fizgig-config.json"
            config_path.write_text('{"input": "api.json", "exports": []}')

            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result = find_config_file()

                # Assert
                assert result is not None
                assert result.name == ".fizgig-config.json"
            finally:
                os.chdir(old_cwd)

    def test_find_config_not_found(self):
        """Test when config file not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result = find_config_file()

                # Assert
                assert result is None
            finally:
                os.chdir(old_cwd)


class TestLoadConfig:
    """Tests for config loading."""

    def test_load_valid_config(self):
        """Test loading valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "input": "api.json",
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }
            json.dump(config, f)
            temp_path = f.name

        try:
            # Act
            result = load_config(temp_path)

            # Assert
            assert result["input"] == "api.json"
            assert len(result["exports"]) == 1
        finally:
            Path(temp_path).unlink()

    def test_load_config_with_headers(self):
        """Test loading config with HTTP headers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "input": "https://api.example.com/spec.json",
                "headers": {
                    "Authorization": "Bearer token"
                },
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }
            json.dump(config, f)
            temp_path = f.name

        try:
            # Act
            result = load_config(temp_path)

            # Assert
            assert result["headers"]["Authorization"] == "Bearer token"
        finally:
            Path(temp_path).unlink()

    def test_load_config_missing_file(self):
        """Test error on missing config file."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.json")

    def test_load_invalid_json(self):
        """Test error on invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json{")
            temp_path = f.name

        try:
            # Act & Assert
            with pytest.raises(json.JSONDecodeError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()


class TestValidateConfig:
    """Tests for config validation."""

    def test_validate_valid_config(self):
        """Test validating valid config."""
        # Arrange
        config = {
            "input": "api.json",
            "exports": [
                {"format": "json", "output": "api.json"}
            ]
        }

        # Act & Assert - should not raise
        validate_config(config)

    def test_validate_missing_input(self):
        """Test error on missing input field."""
        # Arrange
        config = {
            "exports": [
                {"format": "json", "output": "api.json"}
            ]
        }

        # Act & Assert
        with pytest.raises(ConfigError, match="'input' field is required"):
            validate_config(config)

    def test_validate_missing_exports(self):
        """Test error on missing exports field."""
        # Arrange
        config = {
            "input": "api.json"
        }

        # Act & Assert
        with pytest.raises(ConfigError, match="'exports' field is required"):
            validate_config(config)

    def test_validate_empty_exports(self):
        """Test error on empty exports array."""
        # Arrange
        config = {
            "input": "api.json",
            "exports": []
        }

        # Act & Assert
        with pytest.raises(ConfigError, match="'exports' must contain at least one export"):
            validate_config(config)

    def test_validate_export_missing_format(self):
        """Test error on export missing format."""
        # Arrange
        config = {
            "input": "api.json",
            "exports": [
                {"output": "api.json"}
            ]
        }

        # Act & Assert
        with pytest.raises(ConfigError, match="exports\\[0\\]: 'format' field is required"):
            validate_config(config)

    def test_validate_export_missing_output(self):
        """Test error on export missing output."""
        # Arrange
        config = {
            "input": "api.json",
            "exports": [
                {"format": "json"}
            ]
        }

        # Act & Assert
        with pytest.raises(ConfigError, match="exports\\[0\\]: 'output' field is required"):
            validate_config(config)

    def test_validate_invalid_format(self):
        """Test error on invalid format."""
        # Arrange
        config = {
            "input": "api.json",
            "exports": [
                {"format": "invalid", "output": "api.invalid"}
            ]
        }

        # Act & Assert
        with pytest.raises(ConfigError, match="exports\\[0\\]: Invalid format"):
            validate_config(config)

    def test_validate_field_map_not_dict(self):
        """Test error when field map is not a dictionary."""
        # Arrange
        config = {
            "input": "api.json",
            "exports": [
                {"format": "json", "output": "api.json", "fields": "invalid"}
            ]
        }

        # Act & Assert
        with pytest.raises(ConfigError, match="exports\\[0\\]: 'fields' must be a dictionary"):
            validate_config(config)


class TestValidateConfigDeep:
    """Tests for deep config validation."""

    def test_validate_deep_all_valid(self):
        """Test deep validation with all valid references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create input file
            input_file = config_dir / "api.json"
            input_file.write_text('{"openapi": "3.0.0", "info": {}, "paths": {}}')

            # Create template
            template_dir = config_dir / "templates"
            template_dir.mkdir()
            template_file = template_dir / "custom.html"
            template_file.write_text("<html>{{total_endpoints}}</html>")

            # Arrange
            config = {
                "input": "api.json",
                "exports": [
                    {"format": "html", "output": "api.html", "template": "templates/custom.html"}
                ]
            }

            # Act
            result = validate_config_deep(config, config_dir)

            # Assert
            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_deep_missing_input_file(self):
        """Test deep validation with missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Arrange
            config = {
                "input": "nonexistent.json",
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }

            # Act
            result = validate_config_deep(config, config_dir)

            # Assert
            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert any("input file" in e["message"].lower() for e in result["errors"])

    def test_validate_deep_missing_template(self):
        """Test deep validation with missing template file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create input file
            input_file = config_dir / "api.json"
            input_file.write_text('{"openapi": "3.0.0", "info": {}, "paths": {}}')

            # Arrange
            config = {
                "input": "api.json",
                "exports": [
                    {"format": "html", "output": "api.html", "template": "nonexistent.html"}
                ]
            }

            # Act
            result = validate_config_deep(config, config_dir)

            # Assert
            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert any("template" in e["message"].lower() for e in result["errors"])

    def test_validate_deep_url_input_skips_file_check(self):
        """Test deep validation skips file check for URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Arrange
            config = {
                "input": "https://api.example.com/spec.json",
                "exports": [
                    {"format": "json", "output": "api.json"}
                ]
            }

            # Act
            result = validate_config_deep(config, config_dir)

            # Assert
            assert result["valid"] is True
            assert len(result["errors"]) == 0
