"""
Tests for HTML templating functionality.
"""

import tempfile
from pathlib import Path

import pytest

from api_extractor.templating import (
    load_default_template,
    load_custom_template,
    clean_path_for_display,
    prepare_template_data,
    render_html_template,
)


class TestLoadDefaultTemplate:
    """Tests for loading default template."""

    def test_load_default_template(self):
        """Test loading default template from resources."""
        # Act
        template = load_default_template()

        # Assert
        assert template is not None
        assert len(template) > 0
        assert "<!DOCTYPE html>" in template
        assert "{{total_endpoints}}" in template
        assert "{{#groups}}" in template


class TestLoadCustomTemplate:
    """Tests for loading custom templates."""

    def test_load_custom_template_from_cwd(self):
        """Test loading custom template from current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            template_content = "<html>{{#endpoints}}{{name}}{{/endpoints}}</html>"
            template_path = Path(tmpdir) / "custom.html"
            template_path.write_text(template_content)

            import os

            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                result = load_custom_template("custom.html")

                # Assert
                assert result == template_content
            finally:
                os.chdir(old_cwd)

    def test_load_custom_template_from_config_dir(self):
        """Test loading custom template relative to config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            config_dir = Path(tmpdir)
            template_content = "<html>{{#endpoints}}{{name}}{{/endpoints}}</html>"
            template_path = config_dir / "custom.html"
            template_path.write_text(template_content)

            # Act
            result = load_custom_template("custom.html", config_dir=config_dir)

            # Assert
            assert result == template_content

    def test_load_custom_template_absolute_path(self):
        """Test loading custom template with absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            template_content = "<html>{{#endpoints}}{{name}}{{/endpoints}}</html>"
            template_path = Path(tmpdir) / "custom.html"
            template_path.write_text(template_content)

            # Act
            result = load_custom_template(str(template_path))

            # Assert
            assert result == template_content

    def test_load_custom_template_not_found(self):
        """Test error when custom template not found."""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            load_custom_template("nonexistent.html")


class TestCleanPathForDisplay:
    """Tests for path cleaning."""

    def test_remove_postman_variables(self):
        """Test removing Postman template variables."""
        # Arrange
        path = "{{baseUrl}}/api/users/{{id}}"

        # Act
        result = clean_path_for_display(path)

        # Assert
        assert result == "/api/users/"

    def test_clean_double_slashes(self):
        """Test cleaning up double slashes."""
        # Arrange
        path = "/api//users///items"

        # Act
        result = clean_path_for_display(path)

        # Assert
        assert result == "/api/users/items"

    def test_clean_path_no_variables(self):
        """Test cleaning path with no variables."""
        # Arrange
        path = "/api/users/{id}"

        # Act
        result = clean_path_for_display(path)

        # Assert
        assert result == "/api/users/{id}"


class TestPrepareTemplateData:
    """Tests for template data preparation."""

    def test_prepare_template_data_basic(self):
        """Test preparing basic template data."""
        # Arrange
        endpoints = [
            {
                "group": "Users",
                "name": "List users",
                "method": "GET",
                "path": "/api/users",
                "description": "Get all users",
                "params": [],
                "metadata": {},
            }
        ]

        # Act
        data = prepare_template_data(endpoints, "api.json", "openapi")

        # Assert
        assert data["total_endpoints"] == 1
        assert data["source_file"] == "api.json"
        assert data["source_format"] == "openapi"
        assert "generated_at" in data
        assert len(data["groups"]) == 1
        assert data["groups"][0]["name"] == "Users"
        assert data["groups"][0]["count"] == 1

    def test_prepare_template_data_with_markdown_description(self):
        """Test that markdown descriptions are converted to HTML."""
        # Arrange
        endpoints = [
            {
                "group": "Users",
                "name": "List users",
                "method": "GET",
                "path": "/api/users",
                "description": "Get **all** users",
                "params": [],
                "metadata": {},
            }
        ]

        # Act
        data = prepare_template_data(endpoints)

        # Assert
        description = data["groups"][0]["endpoints"][0]["description"]
        assert "<strong>" in description or "<b>" in description

    def test_prepare_template_data_deprecated_endpoint(self):
        """Test deprecated endpoint flag."""
        # Arrange
        endpoints = [
            {
                "group": "Users",
                "name": "Old endpoint",
                "method": "GET",
                "path": "/api/old",
                "description": "",
                "params": [],
                "metadata": {"deprecated": True},
            }
        ]

        # Act
        data = prepare_template_data(endpoints)

        # Assert
        assert data["groups"][0]["endpoints"][0]["deprecated"] is True

    def test_prepare_template_data_with_params(self):
        """Test endpoint with parameters."""
        # Arrange
        endpoints = [
            {
                "group": "Users",
                "name": "List users",
                "method": "GET",
                "path": "/api/users",
                "description": "",
                "params": [
                    {
                        "name": "page",
                        "in": "query",
                        "type": "integer",
                        "required": False,
                        "description": "Page number",
                    }
                ],
                "metadata": {},
            }
        ]

        # Act
        data = prepare_template_data(endpoints)

        # Assert
        endpoint = data["groups"][0]["endpoints"][0]
        assert endpoint["params"] is not None
        assert len(endpoint["params"]) == 1

    def test_prepare_template_data_cleans_paths(self):
        """Test that Postman variables are cleaned from paths."""
        # Arrange
        endpoints = [
            {
                "group": "Users",
                "name": "Get user",
                "method": "GET",
                "path": "{{baseUrl}}/api/users/{{id}}",
                "description": "",
                "params": [],
                "metadata": {},
            }
        ]

        # Act
        data = prepare_template_data(endpoints)

        # Assert
        path = data["groups"][0]["endpoints"][0]["path"]
        assert "{{" not in path


class TestRenderHtmlTemplate:
    """Tests for HTML rendering."""

    def test_render_html_with_default_template(self):
        """Test rendering HTML with default template."""
        # Arrange
        endpoints = [
            {
                "group": "Users",
                "name": "List users",
                "method": "GET",
                "path": "/api/users",
                "description": "Get all users",
                "params": [],
                "metadata": {},
            }
        ]

        # Act
        html = render_html_template(endpoints)

        # Assert
        assert "<!DOCTYPE html>" in html
        assert "Users" in html
        assert "List users" in html
        assert "GET" in html
        assert "/api/users" in html

    def test_render_html_with_custom_template(self):
        """Test rendering HTML with custom template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Arrange
            template_content = "<html><body>{{total_endpoints}} endpoints</body></html>"
            template_path = Path(tmpdir) / "custom.html"
            template_path.write_text(template_content)

            endpoints = [
                {
                    "group": "Users",
                    "name": "Test",
                    "method": "GET",
                    "path": "/test",
                    "description": "",
                    "params": [],
                    "metadata": {},
                }
            ]

            # Act
            html = render_html_template(endpoints, template_path=str(template_path))

            # Assert
            assert "1 endpoints" in html
