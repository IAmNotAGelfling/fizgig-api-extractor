"""
Tests for export functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from api_extractor.exporter import (
    export_markdown,
    export_csv,
    export_json,
    export_html,
)


@pytest.fixture
def sample_endpoints():
    """Sample endpoints for testing."""
    return [
        {
            "group": "Users",
            "name": "List users",
            "method": "GET",
            "path": "/api/users",
            "description": "Get all users",
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
        },
        {
            "group": "Users",
            "name": "Create user",
            "method": "POST",
            "path": "/api/users",
            "description": "Create a new user",
            "params": [
                {
                    "name": "body",
                    "in": "body",
                    "type": "object",
                    "required": True,
                    "description": "User data",
                }
            ],
            "metadata": {},
        },
        {
            "group": "Posts",
            "name": "List posts",
            "method": "GET",
            "path": "/api/posts",
            "description": "Get all posts",
            "params": [],
            "metadata": {"deprecated": False},
        },
    ]


class TestExportMarkdown:
    """Tests for Markdown export."""

    def test_export_markdown_basic(self, sample_endpoints):
        """Test basic Markdown export."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            temp_path = f.name

        try:
            export_markdown(sample_endpoints, temp_path)

            # Read and verify content
            content = Path(temp_path).read_text()
            assert "# API Endpoints" in content
            assert "## Users" in content
            assert "## Posts" in content
            assert "GET /api/users" in content
            assert "POST /api/users" in content
            assert "List users" in content

            # Check parameter table
            assert "| Name | In | Type | Required | Description |" in content
            assert "page" in content

        finally:
            Path(temp_path).unlink()

    def test_export_markdown_empty(self):
        """Test Markdown export with no endpoints."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            temp_path = f.name

        try:
            export_markdown([], temp_path)
            content = Path(temp_path).read_text()
            assert "Total endpoints: 0" in content
        finally:
            Path(temp_path).unlink()


class TestExportCsv:
    """Tests for CSV export."""

    def test_export_csv_basic(self, sample_endpoints):
        """Test basic CSV export."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            export_csv(sample_endpoints, temp_path)

            # Read and verify content
            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")

            # Check header
            assert (
                "Group,Name,Method,Path,Description,Parameters,Deprecated" in lines[0]
            )

            # Check data rows (3 endpoints)
            assert len(lines) == 4  # Header + 3 data rows

            # Check first endpoint
            assert "Users" in lines[1]
            assert "GET" in lines[1]
            assert "/api/users" in lines[1]

        finally:
            Path(temp_path).unlink()

    def test_export_csv_with_params(self, sample_endpoints):
        """Test CSV export includes parameters."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            export_csv(sample_endpoints, temp_path)
            content = Path(temp_path).read_text()

            # Check parameters are included
            assert "page" in content
            assert "query" in content
            assert "optional" in content

        finally:
            Path(temp_path).unlink()


class TestExportJson:
    """Tests for JSON export."""

    def test_export_json_basic(self, sample_endpoints):
        """Test basic JSON export."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            export_json(sample_endpoints, temp_path)

            # Read and verify content
            with open(temp_path) as f:
                data = json.load(f)

            assert len(data) == 3
            assert data[0]["name"] == "List users"
            assert data[0]["method"] == "GET"
            assert data[1]["method"] == "POST"

        finally:
            Path(temp_path).unlink()

    def test_export_json_pretty(self, sample_endpoints):
        """Test JSON export with pretty formatting."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            export_json(sample_endpoints, temp_path, pretty=True)

            # Check that file has indentation (pretty format)
            content = Path(temp_path).read_text()
            assert "  " in content  # Contains indentation

        finally:
            Path(temp_path).unlink()

    def test_export_json_compact(self, sample_endpoints):
        """Test JSON export without pretty formatting."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            export_json(sample_endpoints, temp_path, pretty=False)

            # Compact format should have no indentation
            with open(temp_path) as f:
                data = json.load(f)

            assert len(data) == 3  # Data should still be valid

        finally:
            Path(temp_path).unlink()


class TestExportHtml:
    """Tests for HTML export."""

    def test_export_html_basic(self, sample_endpoints):
        """Test basic HTML export."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            export_html(sample_endpoints, temp_path)

            # Read and verify content
            content = Path(temp_path).read_text()

            # Check HTML structure
            assert "<!DOCTYPE html>" in content
            assert "<html" in content
            assert "</html>" in content

            # Check content
            assert "API Endpoints" in content
            assert "Users" in content
            assert "Posts" in content
            assert "GET" in content
            assert "POST" in content

            # Check styling exists
            assert "<style>" in content
            assert ".method" in content

        finally:
            Path(temp_path).unlink()

    def test_export_html_method_styles(self, sample_endpoints):
        """Test HTML export includes method-specific styles."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            export_html(sample_endpoints, temp_path)
            content = Path(temp_path).read_text()

            # Check method-specific CSS classes
            assert ".method.GET" in content
            assert ".method.POST" in content
            assert 'class="method GET"' in content
            assert 'class="method POST"' in content

        finally:
            Path(temp_path).unlink()

    def test_export_html_parameters(self, sample_endpoints):
        """Test HTML export includes parameter tables."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            export_html(sample_endpoints, temp_path)
            content = Path(temp_path).read_text()

            # Check parameter table exists
            assert "<table>" in content
            assert "<th>Parameter</th>" in content
            assert "page" in content
            assert "query" in content

        finally:
            Path(temp_path).unlink()


class TestFieldMappingIntegration:
    """Tests for field mapping in CSV and JSON exports."""

    def test_csv_export_with_field_mapping(self, sample_endpoints):
        """Test CSV export with custom field mapping."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            field_map = {"method": "HTTP Method", "path": "Endpoint", "name": "Name"}
            export_csv(sample_endpoints, temp_path, field_map=field_map)

            # Read CSV
            import csv

            with open(temp_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Check headers
            assert len(rows) > 0
            assert "HTTP Method" in rows[0]
            assert "Endpoint" in rows[0]
            assert "Name" in rows[0]
            # Old fields should not be present
            assert "method" not in rows[0]
            assert "group" not in rows[0]

            # Check data
            assert rows[0]["HTTP Method"] == "GET"
            assert rows[0]["Endpoint"] == "/api/users"
            assert rows[0]["Name"] == "List users"

        finally:
            Path(temp_path).unlink()

    def test_json_export_with_field_mapping(self, sample_endpoints):
        """Test JSON export with custom field mapping."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            field_map = {"method": "HTTP Method", "path": "Endpoint"}
            export_json(sample_endpoints, temp_path, field_map=field_map)

            # Read JSON
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check data
            assert len(data) > 0
            assert "HTTP Method" in data[0]
            assert "Endpoint" in data[0]
            # Old fields should not be present
            assert "method" not in data[0]
            assert "group" not in data[0]

            # Check values
            assert data[0]["HTTP Method"] == "GET"
            assert data[0]["Endpoint"] == "/api/users"

        finally:
            Path(temp_path).unlink()

    def test_csv_export_without_field_mapping(self, sample_endpoints):
        """Test CSV export still works without field mapping."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            export_csv(sample_endpoints, temp_path)

            # Read CSV
            import csv

            with open(temp_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Check default headers are present
            assert "Group" in rows[0]
            assert "Method" in rows[0]
            assert "Path" in rows[0]

        finally:
            Path(temp_path).unlink()

    def test_csv_export_with_custom_delimiter(self, sample_endpoints):
        """Test CSV export with custom delimiter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            temp_path = f.name

        try:
            export_csv(sample_endpoints, temp_path, delimiter="\t")

            # Read content
            content = Path(temp_path).read_text()

            # Check tabs are used
            assert "\t" in content
            # Check commas are in data (not delimiters)
            lines = content.split("\n")
            assert "\t" in lines[0]  # Header should have tabs

        finally:
            Path(temp_path).unlink()

    def test_csv_export_with_quote_all(self, sample_endpoints):
        """Test CSV export with quote all fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            export_csv(sample_endpoints, temp_path, quoting="all")

            # Read content
            content = Path(temp_path).read_text()

            # Check that fields are quoted
            lines = content.split("\n")
            header = lines[0]
            # All fields should be quoted
            assert header.startswith('"')
            assert '"Group"' in header or '"Method"' in header

        finally:
            Path(temp_path).unlink()

    def test_csv_export_with_field_mapping_and_options(self, sample_endpoints):
        """Test CSV export with field mapping and custom options."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            temp_path = f.name

        try:
            field_map = {"method": "Method", "path": "Path"}
            export_csv(
                sample_endpoints,
                temp_path,
                field_map=field_map,
                delimiter="\t",
                quoting="all",
            )

            # Read content
            content = Path(temp_path).read_text()

            # Check tabs are used
            assert "\t" in content
            # Check fields are quoted
            assert '"Method"' in content
            assert '"Path"' in content

        finally:
            Path(temp_path).unlink()
