"""
Tests for CLI functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest
import responses
from typer.testing import CliRunner

from api_extractor.cli import app
from tests.test_helpers import assert_all_in_output


runner = CliRunner()


@pytest.fixture
def sample_postman_file():
    """Create temporary Postman collection file."""
    data = {
        "info": {
            "name": "Test API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [
            {
                "name": "Get Users",
                "request": {"method": "GET", "url": "https://api.example.com/users"},
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(
                app,
                ["extract", sample_postman_file, "-o", output_path, "-f", "markdown"],
            )
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(
                app, ["extract", sample_postman_file, "-o", output_path, "-f", "csv"]
            )
            assert result.exit_code == 0
            assert Path(output_path).exists()

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_extract_to_json(self, sample_postman_file):
        """Test extracting to JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(
                app, ["extract", sample_postman_file, "-o", output_path, "-f", "json"]
            )
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(
                app, ["extract", sample_postman_file, "-o", output_path, "-f", "html"]
            )
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
        result = runner.invoke(
            app, ["extract", sample_postman_file, "-o", "output.txt", "-f", "invalid"]
        )
        assert result.exit_code == 1
        # Error messages go to stderr
        assert "Unknown format" in result.output or "Unknown format" in str(
            result.exception
        )


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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, ["convert", sample_openapi_file, output_path])
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = runner.invoke(app, ["convert", sample_postman_file, output_path])
            assert result.exit_code == 1
            # Error messages go to stderr
            assert (
                "not an OpenAPI spec" in result.output
                or "not an OpenAPI spec" in str(result.exception)
            )

        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()


class TestCliUrlSupport:
    """Tests for URL fetching in CLI."""

    @responses.activate
    def test_extract_from_url(self):
        """Test extracting from URL."""
        # Arrange
        url = "https://api.example.com/openapi.json"
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        }
        responses.add(responses.GET, url, json=spec, status=200)

        # Act
        result = runner.invoke(app, ["extract", url])

        # Assert
        assert result.exit_code == 0
        assert "openapi" in result.output.lower()
        assert "1 endpoint(s)" in result.output

    @responses.activate
    def test_extract_from_url_with_header(self):
        """Test extracting from URL with custom header."""
        # Arrange
        url = "https://api.example.com/spec.json"
        spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
        responses.add(responses.GET, url, json=spec, status=200)

        # Act
        result = runner.invoke(
            app, ["extract", url, "--header", "Authorization: Bearer token123"]
        )

        # Assert
        assert result.exit_code == 0
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["Authorization"] == "Bearer token123"

    @responses.activate
    def test_extract_from_url_with_multiple_headers(self):
        """Test extracting from URL with multiple headers."""
        # Arrange
        url = "https://api.example.com/spec.json"
        spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
        responses.add(responses.GET, url, json=spec, status=200)

        # Act
        result = runner.invoke(
            app,
            [
                "extract",
                url,
                "--header",
                "Authorization: Bearer token123",
                "--header",
                "X-API-Version: v2",
            ],
        )

        # Assert
        assert result.exit_code == 0
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["Authorization"] == "Bearer token123"
        assert responses.calls[0].request.headers["X-API-Version"] == "v2"

    @responses.activate
    def test_extract_from_url_with_save(self):
        """Test extracting from URL with save functionality."""
        # Arrange
        url = "https://api.example.com/openapi.yaml"
        spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
        responses.add(responses.GET, url, json=spec, status=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = str(Path(tmpdir) / "saved.json")

            # Act
            result = runner.invoke(app, ["extract", url, "--save-url", save_path])

            # Assert
            assert result.exit_code == 0
            # Use helper to handle Rich console wrapping across platforms
            assert_all_in_output(["Saved to", save_path], result.output)
            assert Path(save_path).exists()

    def test_extract_invalid_header_format(self):
        """Test error on invalid header format."""
        # Act
        result = runner.invoke(
            app,
            [
                "extract",
                "https://api.example.com/spec.json",
                "--header",
                "InvalidHeader",
            ],
        )

        # Assert
        assert result.exit_code == 1
        assert "Invalid header format" in result.output


class TestCliInit:
    """Tests for init command."""

    def test_init_both_files(self):
        """Test init command creates both config and template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result = runner.invoke(app, ["init"])

                # Assert
                assert result.exit_code == 0
                assert Path(".fizgig-config.json").exists()
                assert Path("templates/default.html").exists()

                # Verify config content
                with open(".fizgig-config.json") as f:
                    config = json.load(f)
                assert "input" in config
                assert "exports" in config

                # Verify template content
                template_content = Path("templates/default.html").read_text()
                assert "<!DOCTYPE html>" in template_content
                assert "{{total_endpoints}}" in template_content

            finally:
                os.chdir(old_cwd)

    def test_init_config_only(self):
        """Test init command with --config-only flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result = runner.invoke(app, ["init", "--config-only"])

                # Assert
                assert result.exit_code == 0
                assert Path(".fizgig-config.json").exists()
                assert not Path("templates/default.html").exists()

            finally:
                os.chdir(old_cwd)

    def test_init_template_only(self):
        """Test init command with --template-only flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result = runner.invoke(app, ["init", "--template-only"])

                # Assert
                assert result.exit_code == 0
                assert not Path(".fizgig-config.json").exists()
                assert Path("templates/default.html").exists()

            finally:
                os.chdir(old_cwd)

    def test_init_custom_output_dir(self):
        """Test init command with --output-dir flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "custom"

            # Act
            result = runner.invoke(app, ["init", "--output-dir", str(output_dir)])

            # Assert
            assert result.exit_code == 0
            assert (output_dir / ".fizgig-config.json").exists()
            assert (output_dir / "templates" / "default.html").exists()

    def test_init_existing_config_file(self):
        """Test init command when config file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Arrange - create existing config
                Path(".fizgig-config.json").write_text('{"input": "existing"}')

                # Act
                result = runner.invoke(app, ["init"])

                # Assert
                assert result.exit_code == 1
                assert "already exists" in result.output

            finally:
                os.chdir(old_cwd)

    def test_init_existing_template_file(self):
        """Test init command when template file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Arrange - create existing template
                templates_dir = Path("templates")
                templates_dir.mkdir()
                (templates_dir / "default.html").write_text("<html>existing</html>")

                # Act
                result = runner.invoke(app, ["init"])

                # Assert
                assert result.exit_code == 1
                assert "already exists" in result.output

            finally:
                os.chdir(old_cwd)


class TestCliConfigWorkflow:
    """Test CLI config file workflows."""

    def test_extract_with_config_file(self):
        """Test extract command with --config flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create input file
            input_file = tmpdir_path / "input.json"
            input_file.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "info": {"title": "Test", "version": "1.0.0"},
                        "paths": {
                            "/test": {
                                "get": {
                                    "summary": "Test",
                                    "responses": {"200": {"description": "OK"}},
                                }
                            }
                        },
                    }
                )
            )

            # Create config file
            config_file = tmpdir_path / "config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "input": str(input_file),
                        "exports": [
                            {
                                "format": "markdown",
                                "output": str(tmpdir_path / "output.md"),
                            }
                        ],
                    }
                )
            )

            # Act - When using --config, input_file can be anything (will be overridden)
            # But use the actual input file path to avoid issues
            result = runner.invoke(
                app, ["extract", str(input_file), "--config", str(config_file)]
            )

            # Assert
            if result.exit_code != 0:
                print(f"Output: {result.output}")
                print(f"Exception: {result.exception}")
            assert result.exit_code == 0
            assert (tmpdir_path / "output.md").exists()

    def test_extract_with_config_and_cli_overrides(self):
        """Test extract command with config file and CLI overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            input_file = tmpdir_path / "input.json"
            input_file.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "info": {"title": "Test", "version": "1.0.0"},
                        "paths": {
                            "/test": {
                                "get": {
                                    "summary": "Test",
                                    "responses": {"200": {"description": "OK"}},
                                }
                            }
                        },
                    }
                )
            )

            config_file = tmpdir_path / "config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "input": str(input_file),
                        "exports": [
                            {
                                "format": "markdown",
                                "output": str(tmpdir_path / "original.md"),
                            }
                        ],
                    }
                )
            )

            override_output = tmpdir_path / "override.md"

            # Act - CLI output flag should override config
            result = runner.invoke(
                app,
                [
                    "extract",
                    str(input_file),
                    "--config",
                    str(config_file),
                    "-o",
                    str(override_output),
                ],
            )

            # Assert
            assert result.exit_code == 0
            assert override_output.exists()

    def test_extract_with_invalid_config_file(self):
        """Test extract command with invalid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create invalid config (missing required fields)
            config_file = tmpdir_path / "config.json"
            config_file.write_text(json.dumps({"invalid": "config"}))

            # Act
            result = runner.invoke(
                app, ["extract", "dummy.json", "--config", str(config_file)]
            )

            # Assert - Should fail
            assert result.exit_code == 1


class TestCliTemplating:
    """Test CLI HTML template flag."""

    def test_extract_html_with_custom_template(self):
        """Test extract command with custom HTML template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create input file
            input_file = tmpdir_path / "input.json"
            input_file.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "info": {"title": "Test", "version": "1.0.0"},
                        "paths": {
                            "/test": {
                                "get": {
                                    "summary": "Test",
                                    "responses": {"200": {"description": "OK"}},
                                }
                            }
                        },
                    }
                )
            )

            # Create custom template
            template_file = tmpdir_path / "custom.html"
            template_file.write_text("""
<!DOCTYPE html>
<html>
<head><title>{{source_file}}</title></head>
<body>
<h1>Custom Template</h1>
<p>Total endpoints: {{total_endpoints}}</p>
{{#groups}}
  <h2>{{name}}</h2>
  {{#endpoints}}
    <p>{{method}} {{path}}</p>
  {{/endpoints}}
{{/groups}}
</body>
</html>
""")

            output_file = tmpdir_path / "output.html"

            # Act
            result = runner.invoke(
                app,
                [
                    "extract",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "-f",
                    "html",
                    "--template",
                    str(template_file),
                ],
            )

            # Assert
            assert result.exit_code == 0
            assert output_file.exists()
            content = output_file.read_text()
            assert "Custom Template" in content


class TestCliPlainText:
    """Test CLI plain text flag."""

    def test_extract_json_with_plain_text_flag(self):
        """Test extract command with --plain-text flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            input_file = tmpdir_path / "input.json"
            input_file.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "info": {"title": "Test", "version": "1.0.0"},
                        "paths": {
                            "/test": {
                                "get": {
                                    "summary": "Test with **markdown**",
                                    "description": "Description with [link](http://example.com)",
                                    "responses": {"200": {"description": "OK"}},
                                }
                            }
                        },
                    }
                )
            )

            output_file = tmpdir_path / "output.json"

            # Act
            result = runner.invoke(
                app,
                [
                    "extract",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "-f",
                    "json",
                    "--plain-text",
                ],
            )

            # Assert
            assert result.exit_code == 0
            assert output_file.exists()
            with open(output_file) as f:
                data = json.load(f)
            # Plain text should strip markdown - description should not contain **
            assert "**" not in str(data[0].get("description", ""))


class TestCliSaveUrl:
    """Test CLI URL save functionality."""

    def test_extract_with_save_url_flag_default(self):
        """Test extract command with --save-url flag (default filename)."""
        # This would require mocking HTTP requests
        # Skipping for now as it's covered in test_cli.py URL tests
        pass

    def test_extract_with_save_url_flag_custom_path(self):
        """Test extract command with --save-url custom path."""
        # This would require mocking HTTP requests
        # Skipping for now as it's covered in test_cli.py URL tests
        pass


class TestCliConfigWithHeaders:
    """Test config workflow with headers."""

    def test_extract_with_config_and_headers(self):
        """Test extract with --config and --header flags together."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            input_file = tmpdir_path / "input.json"
            input_file.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "info": {"title": "Test", "version": "1.0.0"},
                        "paths": {
                            "/test": {
                                "get": {
                                    "summary": "Test",
                                    "responses": {"200": {"description": "OK"}},
                                }
                            }
                        },
                    }
                )
            )

            config_file = tmpdir_path / "config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "input": str(input_file),
                        "exports": [
                            {
                                "format": "markdown",
                                "output": str(tmpdir_path / "output.md"),
                            }
                        ],
                    }
                )
            )

            # Act - Include --header with --config
            result = runner.invoke(
                app,
                [
                    "extract",
                    str(input_file),
                    "--config",
                    str(config_file),
                    "--header",
                    "Authorization: Bearer token123",
                ],
            )

            # Assert
            assert result.exit_code == 0

    def test_extract_with_config_and_invalid_header(self):
        """Test extract with --config and invalid --header format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            input_file = tmpdir_path / "input.json"
            input_file.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "info": {"title": "Test", "version": "1.0.0"},
                        "paths": {},
                    }
                )
            )

            config_file = tmpdir_path / "config.json"
            config_file.write_text(
                json.dumps({"input": str(input_file), "exports": []})
            )

            # Act - Invalid header format (no colon)
            result = runner.invoke(
                app,
                [
                    "extract",
                    str(input_file),
                    "--config",
                    str(config_file),
                    "--header",
                    "InvalidHeader",
                ],
            )

            # Assert
            assert result.exit_code == 1
            assert "Invalid header format" in result.output


class TestCliSaveUrlEmpty:
    """Test --save-url with value."""

    @responses.activate
    def test_extract_with_save_url_custom_path(self):
        """Test --save-url with custom path."""
        # Arrange
        url = "https://api.example.com/spec.json"
        spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
        responses.add(responses.GET, url, json=spec, status=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            save_file = tmpdir_path / "custom.json"

            # Act
            result = runner.invoke(app, ["extract", url, "--save-url", str(save_file)])

            # Assert
            assert result.exit_code == 0
            assert save_file.exists()


class TestCliErrorPaths:
    """Test CLI error handling paths."""

    def test_extract_unknown_format_detected(self):
        """Test extract with data that can't be classified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"random": "data"}, f)
            temp_path = f.name

        try:
            result = runner.invoke(app, ["extract", temp_path])
            # Should fail with unknown format
            assert result.exit_code == 1
        finally:
            Path(temp_path).unlink()

    def test_extract_invalid_export_format(self):
        """Test extract with invalid output format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            input_file = tmpdir_path / "input.json"
            input_file.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.0",
                        "info": {"title": "Test", "version": "1.0.0"},
                        "paths": {
                            "/test": {
                                "get": {
                                    "summary": "Test",
                                    "responses": {"200": {"description": "OK"}},
                                }
                            }
                        },
                    }
                )
            )

            output_file = tmpdir_path / "output.xyz"

            # Act
            result = runner.invoke(
                app,
                [
                    "extract",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "-f",
                    "invalid_format",
                ],
            )

            # Assert
            assert result.exit_code == 1
            assert "Unknown format" in result.output


class TestTreeCommand:
    """Test tree command error paths."""

    def test_tree_with_missing_file(self):
        """Test tree command with non-existent file."""
        result = runner.invoke(app, ["tree", "/nonexistent/file.json"])
        assert result.exit_code == 1


class TestConvertCommand:
    """Test convert command error paths."""

    def test_convert_with_postman_input(self):
        """Test convert command with Postman input (should fail)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create Postman collection
            input_file = tmpdir_path / "collection.json"
            input_file.write_text(
                json.dumps(
                    {
                        "info": {
                            "name": "Test",
                            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                        },
                        "item": [],
                    }
                )
            )

            output_file = tmpdir_path / "output.json"

            # Act - convert only works with OpenAPI input
            result = runner.invoke(app, ["convert", str(input_file), str(output_file)])

            # Assert
            assert result.exit_code == 1
            assert "not an OpenAPI spec" in result.output

    def test_convert_with_missing_input(self):
        """Test convert command with non-existent input."""
        result = runner.invoke(
            app, ["convert", "/nonexistent/input.json", "/tmp/output.json"]
        )
        assert result.exit_code == 1


class TestInitCommand:
    """Test init command error paths."""

    def test_init_with_existing_template(self):
        """Test init when template already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create existing template
            templates_dir = tmpdir_path / "templates"
            templates_dir.mkdir()
            (templates_dir / "default.html").write_text("<html>existing</html>")

            # Act
            result = runner.invoke(app, ["init", "--output-dir", str(tmpdir_path)])

            # Assert
            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_init_with_existing_config(self):
        """Test init when config already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create existing config
            (tmpdir_path / ".fizgig-config.json").write_text('{"test": "data"}')

            # Act
            result = runner.invoke(app, ["init", "--output-dir", str(tmpdir_path)])

            # Assert
            assert result.exit_code == 1
            assert "already exists" in result.output


class TestValidateConfigCommand:
    """Test validate-config command error paths."""

    def test_validate_config_missing_file(self):
        """Test validate-config with non-existent file."""
        result = runner.invoke(app, ["validate-config", "/nonexistent/config.json"])
        assert result.exit_code == 1

    def test_validate_config_invalid_json(self):
        """Test validate-config with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_file = tmpdir_path / "bad.json"
            config_file.write_text("{ invalid json")

            result = runner.invoke(app, ["validate-config", str(config_file)])

            assert result.exit_code == 1
            assert "Invalid JSON" in result.output

    def test_validate_config_with_errors(self):
        """Test validate-config with validation errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create config with missing input file
            config_file = tmpdir_path / "config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "input": "/nonexistent/file.json",
                        "exports": [{"format": "markdown", "output": "output.md"}],
                    }
                )
            )

            result = runner.invoke(app, ["validate-config", str(config_file)])

            assert result.exit_code == 1
            assert (
                "Validation failed" in result.output
                or "not found" in result.output.lower()
            )
