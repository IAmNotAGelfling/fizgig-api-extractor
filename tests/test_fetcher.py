"""
Tests for URL fetching functionality.
"""

import pytest
import responses
from pathlib import Path
import tempfile
import json

from api_extractor.fetcher import fetch_from_url, save_url_content, load_from_url


class TestFetchFromUrl:
    """Test HTTP fetching."""

    @responses.activate
    def test_fetch_json_success(self):
        """Test successful JSON fetch."""
        # Arrange
        url = "https://api.example.com/spec.json"
        content = {"openapi": "3.0.0", "paths": {}}
        responses.add(
            responses.GET,
            url,
            json=content,
            status=200,
            headers={"Content-Type": "application/json"},
        )

        # Act
        result_content, detected_format = fetch_from_url(url)

        # Assert
        assert detected_format == "json"
        assert "openapi" in result_content

    @responses.activate
    def test_fetch_yaml_success(self):
        """Test successful YAML fetch."""
        # Arrange
        url = "https://api.example.com/spec.yaml"
        yaml_content = "openapi: '3.0.0'\npaths: {}"
        responses.add(
            responses.GET,
            url,
            body=yaml_content,
            status=200,
            headers={"Content-Type": "application/yaml"},
        )

        # Act
        result_content, detected_format = fetch_from_url(url)

        # Assert
        assert detected_format == "yaml"
        assert "openapi" in result_content

    @responses.activate
    def test_fetch_with_custom_headers(self):
        """Test fetch with custom headers."""
        # Arrange
        url = "https://api.example.com/spec.json"
        headers = {"Authorization": "Bearer token123", "X-API-Version": "v2"}
        responses.add(responses.GET, url, json={"test": "data"}, status=200)

        # Act
        fetch_from_url(url, headers=headers)

        # Assert
        assert len(responses.calls) == 1
        request_headers = responses.calls[0].request.headers
        assert request_headers["Authorization"] == "Bearer token123"
        assert request_headers["X-API-Version"] == "v2"

    @responses.activate
    def test_fetch_timeout(self):
        """Test fetch with timeout."""
        # Arrange
        url = "https://api.example.com/spec.json"
        responses.add(responses.GET, url, body=Exception("Timeout"))

        # Act & Assert
        with pytest.raises(Exception):
            fetch_from_url(url, timeout=1)

    @responses.activate
    def test_fetch_404_error(self):
        """Test fetch with 404 error."""
        # Arrange
        url = "https://api.example.com/notfound.json"
        responses.add(responses.GET, url, status=404)

        # Act & Assert
        with pytest.raises(ValueError, match="HTTP 404"):
            fetch_from_url(url)

    @responses.activate
    def test_fetch_invalid_json(self):
        """Test fetch with invalid JSON content."""
        # Arrange
        url = "https://api.example.com/spec.json"
        responses.add(
            responses.GET,
            url,
            body="not valid json{",
            status=200,
            headers={"Content-Type": "application/json"},
        )

        # Act & Assert
        with pytest.raises(ValueError, match="invalid JSON"):
            fetch_from_url(url)


class TestSaveUrlContent:
    """Test saving URL content to file."""

    def test_save_to_specified_path(self):
        """Test saving content to specified path."""
        # Arrange
        content = '{"test": "data"}'
        url = "https://api.example.com/spec.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = str(Path(tmpdir) / "custom.json")

            # Act
            result_path = save_url_content(content, save_path, url)

            # Assert
            assert result_path == save_path
            assert Path(save_path).exists()
            with open(save_path, "r") as f:
                assert f.read() == content

    def test_save_derives_filename_from_url(self):
        """Test saving content with filename derived from URL."""
        # Arrange
        content = '{"test": "data"}'
        url = "https://api.example.com/openapi.yaml"

        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result_path = save_url_content(content, None, url)

                # Assert
                assert result_path == "./openapi.yaml"
                assert Path("openapi.yaml").exists()
            finally:
                os.chdir(old_cwd)


class TestLoadFromUrl:
    """Test complete URL loading with parsing."""

    @responses.activate
    def test_load_openapi_from_url(self):
        """Test loading and parsing OpenAPI from URL."""
        # Arrange
        url = "https://api.example.com/openapi.json"
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        responses.add(responses.GET, url, json=spec, status=200)

        # Act
        data, format_type = load_from_url(url)

        # Assert
        assert format_type == "openapi"
        assert data["openapi"] == "3.0.0"

    @responses.activate
    def test_load_postman_from_url(self):
        """Test loading and parsing Postman collection from URL."""
        # Arrange
        url = "https://api.example.com/collection.json"
        collection = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }
        responses.add(responses.GET, url, json=collection, status=200)

        # Act
        data, format_type = load_from_url(url)

        # Assert
        assert format_type == "postman"
        assert data["info"]["name"] == "Test Collection"

    @responses.activate
    def test_load_with_save(self):
        """Test loading from URL with save functionality."""
        # Arrange
        url = "https://api.example.com/spec.json"
        spec = {"openapi": "3.0.0", "paths": {}}
        responses.add(responses.GET, url, json=spec, status=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = str(Path(tmpdir) / "saved.json")

            # Act
            data, format_type = load_from_url(url, save_path=save_path)

            # Assert
            assert format_type == "openapi"
            assert Path(save_path).exists()
            with open(save_path, "r") as f:
                saved_data = json.load(f)
                assert saved_data["openapi"] == "3.0.0"


class TestFetcherErrorPaths:
    """Test error handling paths in fetcher."""

    @responses.activate
    def test_fetch_yaml_format_detection_from_url(self):
        """Test YAML format detection from .yaml URL extension."""
        # Arrange - URL ends with .yaml but no content-type header
        url = "https://api.example.com/spec.yaml"
        yaml_content = "openapi: '3.0.0'\npaths: {}"
        responses.add(responses.GET, url, body=yaml_content, status=200)

        # Act
        content, detected_format = fetch_from_url(url)

        # Assert
        assert detected_format == "yaml"

    @responses.activate
    def test_fetch_yml_format_detection_from_url(self):
        """Test YAML format detection from .yml URL extension."""
        # Arrange
        url = "https://api.example.com/spec.yml"
        yaml_content = "openapi: '3.0.0'\npaths: {}"
        responses.add(responses.GET, url, body=yaml_content, status=200)

        # Act
        content, detected_format = fetch_from_url(url)

        # Assert
        assert detected_format == "yaml"

    @responses.activate
    def test_fetch_default_to_json_format(self):
        """Test default to JSON format when no clear indicators."""
        # Arrange - No .yaml/.yml extension, no content-type
        url = "https://api.example.com/spec"
        json_content = '{"openapi": "3.0.0"}'
        responses.add(responses.GET, url, body=json_content, status=200)

        # Act
        content, detected_format = fetch_from_url(url)

        # Assert
        assert detected_format == "json"

    @responses.activate
    def test_fetch_invalid_yaml_content(self):
        """Test fetch with invalid YAML content."""
        # Arrange
        url = "https://api.example.com/spec.yaml"
        invalid_yaml = "invalid: yaml:\n  - bad indentation\n bad: syntax"
        responses.add(
            responses.GET,
            url,
            body=invalid_yaml,
            status=200,
            headers={"Content-Type": "application/yaml"},
        )

        # Act & Assert
        with pytest.raises(ValueError, match="invalid YAML"):
            fetch_from_url(url)

    @responses.activate
    def test_fetch_timeout_error(self):
        """Test fetch with timeout error."""
        # Arrange
        url = "https://api.example.com/spec.json"

        def timeout_callback(request):
            import requests

            raise requests.Timeout("Request timed out")

        responses.add_callback(responses.GET, url, callback=timeout_callback)

        # Act & Assert
        with pytest.raises(ValueError, match="Request timed out"):
            fetch_from_url(url, timeout=1)

    @responses.activate
    def test_fetch_request_exception(self):
        """Test fetch with generic request exception."""
        # Arrange
        url = "https://api.example.com/spec.json"

        def exception_callback(request):
            import requests

            raise requests.RequestException("Network error")

        responses.add_callback(responses.GET, url, callback=exception_callback)

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to fetch URL"):
            fetch_from_url(url)

    def test_save_url_content_to_cwd(self):
        """Test saving content to current working directory."""
        # Arrange
        content = '{"test": "data"}'
        url = "https://api.example.com/data.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act - save_path=None triggers filename derivation from URL
                result_path = save_url_content(content, None, url)

                # Assert
                assert Path(result_path).exists()
                assert "data.json" in result_path
            finally:
                os.chdir(old_cwd)

    @responses.activate
    def test_load_from_url_with_headers(self):
        """Test load_from_url with custom headers."""
        # Arrange
        url = "https://api.example.com/spec.json"
        spec = {"openapi": "3.0.0", "paths": {}}
        headers = {"Authorization": "Bearer token"}
        responses.add(responses.GET, url, json=spec, status=200)

        # Act
        data, format_type = load_from_url(url, headers=headers)

        # Assert
        assert format_type == "openapi"
        assert responses.calls[0].request.headers["Authorization"] == "Bearer token"

    @responses.activate
    def test_load_from_url_unknown_format(self):
        """Test load_from_url with unknown format."""
        # Arrange
        url = "https://api.example.com/spec.json"
        spec = {"unknown": "format", "no": "openapi or postman markers"}
        responses.add(responses.GET, url, json=spec, status=200)

        # Act & Assert
        with pytest.raises(ValueError, match="Could not detect format"):
            load_from_url(url)
