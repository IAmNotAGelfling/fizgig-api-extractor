"""
Tests for CLI functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from api_extractor.cli import app


runner = CliRunner()


@pytest.fixture
def sample_postman_file():
    """Create temporary Postman collection file."""
    data = {
        "info": {
            "name": "Test API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Get Users",
                "request": {
                    "method": "GET",
                    "url": "https://api.example.com/users"
                }
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink()


@pytest.fixture
def sample_openapi_file():
    """Create temporary OpenAPI spec file."""
    data = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink()


class TestCliVersion:
    """Tests for version command."""

    def test_version_flag(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "api-extractor version" in result.stdout


class TestCliExtract:
    """Tests for extract command."""

    def test_extract_postman(self, sample_postman_file):
        """Test extracting from Postman collection."""
        result = runner.invoke(app, ["extract", sample_postman_file])
        assert result.exit_code == 0
        assert "Detected format: postman" in result.stdout

    def test_extract_openapi(self, sample_openapi_file):
        """Test extracting from OpenAPI spec."""
        result = runner.invoke(app, ["extract", sample_openapi_file])
        assert result.exit_code == 0
        assert "Detected format: openapi" in result.stdout

    def test_extract_to_markdown(self, sample_postman_file):
        """Test extracting to Markdown file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, [
                "extract",
                sample_postman_file,
                "-o", output_path,
                "-f", "markdown"
            ])
            assert result.exit_code == 0
            assert Path(output_path).exists()

            # Check content
            content = Path(output_path).read_text()
            assert "# API Endpoints" in content

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_extract_to_csv(self, sample_postman_file):
        """Test extracting to CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, [
                "extract",
                sample_postman_file,
                "-o", output_path,
                "-f", "csv"
            ])
            assert result.exit_code == 0
            assert Path(output_path).exists()

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_extract_to_json(self, sample_postman_file):
        """Test extracting to JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, [
                "extract",
                sample_postman_file,
                "-o", output_path,
                "-f", "json"
            ])
            assert result.exit_code == 0
            assert Path(output_path).exists()

            # Verify JSON is valid
            with open(output_path) as f:
                data = json.load(f)
            assert isinstance(data, list)

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_extract_to_html(self, sample_postman_file):
        """Test extracting to HTML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, [
                "extract",
                sample_postman_file,
                "-o", output_path,
                "-f", "html"
            ])
            assert result.exit_code == 0
            assert Path(output_path).exists()

            # Check HTML content
            content = Path(output_path).read_text()
            assert "<!DOCTYPE html>" in content

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_extract_missing_file(self):
        """Test extracting from non-existent file."""
        result = runner.invoke(app, ["extract", "/nonexistent/file.json"])
        assert result.exit_code == 1

    def test_extract_invalid_format(self, sample_postman_file):
        """Test extracting with invalid output format."""
        result = runner.invoke(app, [
            "extract",
            sample_postman_file,
            "-o", "output.txt",
            "-f", "invalid"
        ])
        assert result.exit_code == 1
        # Error messages go to stderr
        assert "Unknown format" in result.output or "Unknown format" in str(result.exception)


class TestCliTree:
    """Tests for tree command."""

    def test_tree_basic(self, sample_postman_file):
        """Test tree view."""
        result = runner.invoke(app, ["tree", sample_postman_file])
        assert result.exit_code == 0
        assert "API Endpoints" in result.stdout

    def test_tree_with_params(self, sample_openapi_file):
        """Test tree view with parameters."""
        result = runner.invoke(app, ["tree", sample_openapi_file, "--params"])
        assert result.exit_code == 0


class TestCliConvert:
    """Tests for convert command."""

    def test_convert_openapi_to_postman(self, sample_openapi_file):
        """Test converting OpenAPI to Postman."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, [
                "convert",
                sample_openapi_file,
                output_path
            ])
            assert result.exit_code == 0
            assert Path(output_path).exists()

            # Verify Postman collection structure
            with open(output_path) as f:
                data = json.load(f)
            assert "info" in data
            assert "item" in data

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_convert_wrong_format(self, sample_postman_file):
        """Test converting non-OpenAPI file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, [
                "convert",
                sample_postman_file,
                output_path
            ])
            assert result.exit_code == 1
            # Error messages go to stderr
            assert "not an OpenAPI spec" in result.output or "not an OpenAPI spec" in str(result.exception)

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()
