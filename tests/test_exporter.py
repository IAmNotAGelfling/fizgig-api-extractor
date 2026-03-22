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
                    "description": "Page number"
                }
            ],
            "metadata": {}
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
                    "description": "User data"
                }
            ],
            "metadata": {}
        },
        {
            "group": "Posts",
            "name": "List posts",
            "method": "GET",
            "path": "/api/posts",
            "description": "Get all posts",
            "params": [],
            "metadata": {"deprecated": False}
        }
    ]


class TestExportMarkdown:
    """Tests for Markdown export."""

    def test_export_markdown_basic(self, sample_endpoints):
        """Test basic Markdown export."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            export_csv(sample_endpoints, temp_path)

            # Read and verify content
            content = Path(temp_path).read_text()
            lines = content.strip().split('\n')

            # Check header
            assert "Group,Name,Method,Path,Description,Parameters,Deprecated" in lines[0]

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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
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
