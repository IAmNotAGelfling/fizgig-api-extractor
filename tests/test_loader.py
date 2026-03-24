"""
Tests for file loader and format detection.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
import responses

from api_extractor.loader import (
    detect_format,
    load_json,
    load_yaml,
    load_api_file,
    validate_postman_collection,
    validate_openapi_spec,
)


class TestDetectFormat:
    """Tests for format detection."""

    def test_detect_postman_by_schema(self):
        """Test detecting Postman collection by schema."""
        data = {
            "info": {
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            }
        }
        assert detect_format(data) == "postman"

    def test_detect_postman_by_items(self):
        """Test detecting Postman collection by items."""
        data = {"item": []}
        assert detect_format(data) == "postman"

    def test_detect_openapi_by_version(self):
        """Test detecting OpenAPI by version field."""
        data = {"openapi": "3.0.3", "info": {}, "paths": {}}
        assert detect_format(data) == "openapi"

    def test_detect_openapi_by_paths(self):
        """Test detecting OpenAPI by paths field."""
        data = {"paths": {}, "info": {}}
        assert detect_format(data) == "openapi"

    def test_detect_unknown_format(self):
        """Test unknown format detection."""
        data = {"random": "data"}
        assert detect_format(data) == "unknown"


class TestLoadJson:
    """Tests for JSON loading."""

    def test_load_valid_json(self):
        """Test loading valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            data = load_json(Path(temp_path))
            assert data == {"test": "data"}
        finally:
            Path(temp_path).unlink()

    def test_load_invalid_json(self):
        """Test loading invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_json(Path(temp_path))
        finally:
            Path(temp_path).unlink()

    def test_load_missing_file(self):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_json(Path("/nonexistent/file.json"))


class TestLoadYaml:
    """Tests for YAML loading."""

    def test_load_valid_yaml(self):
        """Test loading valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            data = load_yaml(Path(temp_path))
            assert data == {"test": "data"}
        finally:
            Path(temp_path).unlink()

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                load_yaml(Path(temp_path))
        finally:
            Path(temp_path).unlink()


class TestLoadApiFile:
    """Tests for API file loading."""

    def test_load_postman_json(self):
        """Test loading Postman collection JSON."""
        data = {
            "info": {"schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
            "item": []
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            loaded_data, format_type = load_api_file(temp_path)
            assert format_type == "postman"
            assert loaded_data["info"]["schema"] == data["info"]["schema"]
        finally:
            Path(temp_path).unlink()

    def test_load_openapi_yaml(self):
        """Test loading OpenAPI YAML."""
        data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(data, f)
            temp_path = f.name

        try:
            loaded_data, format_type = load_api_file(temp_path)
            assert format_type == "openapi"
            assert loaded_data["openapi"] == "3.0.3"
        finally:
            Path(temp_path).unlink()

    def test_load_unknown_format(self):
        """Test loading file with unknown format."""
        data = {"random": "data"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Could not detect format"):
                load_api_file(temp_path)
        finally:
            Path(temp_path).unlink()


class TestValidatePostmanCollection:
    """Tests for Postman collection validation."""

    def test_validate_valid_collection(self):
        """Test validating valid Postman collection."""
        data = {"info": {"name": "Test"}, "item": []}
        assert validate_postman_collection(data) is True

    def test_validate_missing_info(self):
        """Test validation fails without info."""
        data = {"item": []}
        assert validate_postman_collection(data) is False

    def test_validate_missing_item(self):
        """Test validation fails without item."""
        data = {"info": {"name": "Test"}}
        assert validate_postman_collection(data) is False


class TestValidateOpenapiSpec:
    """Tests for OpenAPI specification validation."""

    def test_validate_valid_spec(self):
        """Test validating valid OpenAPI spec."""
        data = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        assert validate_openapi_spec(data) is True

    def test_validate_missing_openapi(self):
        """Test validation fails without openapi field."""
        data = {"info": {"title": "Test"}, "paths": {}}
        assert validate_openapi_spec(data) is False

    def test_validate_wrong_version(self):
        """Test validation fails with wrong OpenAPI version."""
        data = {
            "openapi": "2.0",
            "info": {"title": "Test"},
            "paths": {}
        }
        assert validate_openapi_spec(data) is False

    def test_validate_missing_paths(self):
        """Test validation fails without paths."""
        data = {"openapi": "3.0.3", "info": {"title": "Test"}}
        assert validate_openapi_spec(data) is False


class TestLoadFromUrl:
    """Tests for loading API specs from URLs."""

    @responses.activate
    def test_load_openapi_from_url(self):
        """Test loading OpenAPI spec from URL."""
        # Arrange
        url = "https://api.example.com/openapi.json"
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        responses.add(responses.GET, url, json=spec, status=200)

        # Act
        data, format_type = load_api_file(url)

        # Assert
        assert format_type == "openapi"
        assert data["openapi"] == "3.0.0"

    @responses.activate
    def test_load_postman_from_url(self):
        """Test loading Postman collection from URL."""
        # Arrange
        url = "https://api.example.com/collection.json"
        collection = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        responses.add(responses.GET, url, json=collection, status=200)

        # Act
        data, format_type = load_api_file(url)

        # Assert
        assert format_type == "postman"
        assert data["info"]["name"] == "Test Collection"

    @responses.activate
    def test_load_url_with_headers(self):
        """Test loading from URL with custom headers."""
        # Arrange
        url = "https://api.example.com/spec.json"
        headers = {"Authorization": "Bearer token123"}
        spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
        responses.add(responses.GET, url, json=spec, status=200)

        # Act
        data, format_type = load_api_file(url, headers=headers)

        # Assert
        assert format_type == "openapi"
        assert len(responses.calls) == 1
        request_headers = responses.calls[0].request.headers
        assert request_headers["Authorization"] == "Bearer token123"

    @responses.activate
    def test_load_url_with_save(self):
        """Test loading from URL with save functionality."""
        # Arrange
        url = "https://api.example.com/spec.json"
        spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
        responses.add(responses.GET, url, json=spec, status=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = str(Path(tmpdir) / "saved.json")

            # Act
            data, format_type = load_api_file(url, save_path=save_path)

            # Assert
            assert format_type == "openapi"
            assert Path(save_path).exists()
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
                assert saved_data["openapi"] == "3.0.0"
