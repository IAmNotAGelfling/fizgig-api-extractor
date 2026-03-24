"""
Tests for Postman collection parser.
"""

import json
from pathlib import Path


from api_extractor.parser_postman import (
    parse_postman_url,
    parse_postman_request,
    parse_postman_item,
    parse_postman_collection,
)


class TestParsePostmanUrl:
    """Tests for Postman URL parsing."""

    def test_parse_string_url(self):
        """Test parsing simple string URL."""
        url = "https://api.example.com/users"
        result = parse_postman_url(url)
        assert result["raw"] == url
        assert result["path"] == url

    def test_parse_url_object(self):
        """Test parsing Postman URL object."""
        url_obj = {
            "raw": "https://api.example.com/users",
            "protocol": "https",
            "host": ["api", "example", "com"],
            "path": ["users"]
        }
        result = parse_postman_url(url_obj)
        assert result["raw"] == "https://api.example.com/users"
        assert result["protocol"] == "https"
        assert result["host"] == "api.example.com"
        assert result["path"] == "/users"

    def test_parse_url_with_variables(self):
        """Test parsing URL with variables."""
        url_obj = {
            "raw": "https://api.example.com/users/{{userId}}",
            "host": ["api", "example", "com"],
            "path": ["users", "{{userId}}"],
            "variable": [
                {"key": "userId", "value": "123"}
            ]
        }
        result = parse_postman_url(url_obj)
        assert result["variables"]["userId"] == "123"


class TestParsePostmanRequest:
    """Tests for Postman request parsing."""

    def test_parse_get_request(self):
        """Test parsing GET request."""
        request = {
            "method": "GET",
            "url": "https://api.example.com/users"
        }
        result = parse_postman_request(request)
        assert result["method"] == "GET"
        assert result["url"]["raw"] == "https://api.example.com/users"

    def test_parse_request_with_headers(self):
        """Test parsing request with headers."""
        request = {
            "method": "GET",
            "url": "https://api.example.com/users",
            "header": [
                {"key": "Authorization", "value": "Bearer token"}
            ]
        }
        result = parse_postman_request(request)
        assert len(result["headers"]) == 1
        assert result["headers"][0]["key"] == "Authorization"

    def test_parse_request_with_query_params(self):
        """Test parsing request with query parameters."""
        request = {
            "method": "GET",
            "url": {
                "raw": "https://api.example.com/users?page=1",
                "host": ["api", "example", "com"],
                "path": ["users"],
                "query": [
                    {"key": "page", "value": "1", "description": "Page number"}
                ]
            }
        }
        result = parse_postman_request(request)
        assert len(result["query_params"]) == 1
        assert result["query_params"][0]["key"] == "page"

    def test_parse_request_with_body(self):
        """Test parsing request with body."""
        request = {
            "method": "POST",
            "url": "https://api.example.com/users",
            "body": {
                "mode": "raw",
                "raw": '{"name": "John"}'
            }
        }
        result = parse_postman_request(request)
        assert result["body"]["mode"] == "raw"


class TestParsePostmanItem:
    """Tests for Postman item parsing."""

    def test_parse_simple_request(self):
        """Test parsing simple request item."""
        item = {
            "name": "Get User",
            "request": {
                "method": "GET",
                "url": "https://api.example.com/users/123"
            }
        }
        endpoints = parse_postman_item(item)
        assert len(endpoints) == 1
        assert endpoints[0]["name"] == "Get User"
        assert endpoints[0]["method"] == "GET"

    def test_parse_folder(self):
        """Test parsing folder with multiple items."""
        item = {
            "name": "Users",
            "item": [
                {
                    "name": "List Users",
                    "request": {"method": "GET", "url": "/users"}
                },
                {
                    "name": "Create User",
                    "request": {"method": "POST", "url": "/users"}
                }
            ]
        }
        endpoints = parse_postman_item(item)
        assert len(endpoints) == 2
        assert endpoints[0]["group"] == "Users"
        assert endpoints[1]["group"] == "Users"

    def test_parse_nested_folders(self):
        """Test parsing nested folders."""
        item = {
            "name": "API",
            "item": [
                {
                    "name": "v1",
                    "item": [
                        {
                            "name": "Get User",
                            "request": {"method": "GET", "url": "/users/1"}
                        }
                    ]
                }
            ]
        }
        endpoints = parse_postman_item(item)
        assert len(endpoints) == 1
        assert endpoints[0]["group"] == "API / v1"


class TestParsePostmanCollection:
    """Tests for complete Postman collection parsing."""

    def test_parse_sample_collection(self):
        """Test parsing sample collection from fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_postman.json"
        with open(fixture_path) as f:
            data = json.load(f)

        endpoints = parse_postman_collection(data)

        # Should have 5 endpoints total
        assert len(endpoints) == 5

        # Check first endpoint
        assert endpoints[0]["group"] == "Users"
        assert endpoints[0]["name"] == "List Users"
        assert endpoints[0]["method"] == "GET"

        # Check metadata
        assert endpoints[0]["metadata"]["collection"] == "Sample API"

    def test_parse_empty_collection(self):
        """Test parsing empty collection."""
        data = {
            "info": {"name": "Empty API"},
            "item": []
        }
        endpoints = parse_postman_collection(data)
        assert len(endpoints) == 0

    def test_parse_collection_with_path_params(self):
        """Test parsing collection with path parameters."""
        data = {
            "info": {"name": "Test API"},
            "item": [
                {
                    "name": "Get User",
                    "request": {
                        "method": "GET",
                        "url": {
                            "raw": "https://api.example.com/users/:id",
                            "path": ["users", ":id"]
                        }
                    }
                }
            ]
        }
        endpoints = parse_postman_collection(data)
        assert len(endpoints) == 1

        # Check that path parameter was extracted
        params = [p for p in endpoints[0]["params"] if p["in"] == "path"]
        assert len(params) == 1
        assert params[0]["name"] == "id"
        assert params[0]["required"] is True
