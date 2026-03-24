"""
Tests for OpenAPI specification parser.
"""

from pathlib import Path

import yaml

from api_extractor.parser_openapi import (
    resolve_server_url,
    parse_openapi_parameter,
    parse_openapi_request_body,
    parse_openapi_responses,
    parse_openapi_operation,
    parse_openapi_spec,
)


class TestResolveServerUrl:
    """Tests for server URL resolution."""

    def test_resolve_simple_url(self):
        """Test resolving simple server URL."""
        servers = [{"url": "https://api.example.com"}]
        assert resolve_server_url(servers) == "https://api.example.com"

    def test_resolve_url_with_variables(self):
        """Test resolving URL with variables."""
        servers = [
            {
                "url": "https://{environment}.example.com",
                "variables": {
                    "environment": {"default": "api"}
                }
            }
        ]
        assert resolve_server_url(servers) == "https://api.example.com"

    def test_resolve_empty_servers(self):
        """Test with empty servers list."""
        assert resolve_server_url([]) == ""

    def test_resolve_first_server(self):
        """Test that first server is used."""
        servers = [
            {"url": "https://api1.example.com"},
            {"url": "https://api2.example.com"}
        ]
        assert resolve_server_url(servers) == "https://api1.example.com"


class TestParseOpenapiParameter:
    """Tests for OpenAPI parameter parsing."""

    def test_parse_query_parameter(self):
        """Test parsing query parameter."""
        param = {
            "name": "page",
            "in": "query",
            "required": False,
            "schema": {"type": "integer"},
            "description": "Page number"
        }
        result = parse_openapi_parameter(param)
        assert result["name"] == "page"
        assert result["in"] == "query"
        assert result["type"] == "integer"
        assert result["required"] is False

    def test_parse_path_parameter(self):
        """Test parsing path parameter."""
        param = {
            "name": "id",
            "in": "path",
            "required": True,
            "schema": {"type": "string"}
        }
        result = parse_openapi_parameter(param)
        assert result["name"] == "id"
        assert result["in"] == "path"
        assert result["required"] is True


class TestParseOpenapiRequestBody:
    """Tests for OpenAPI request body parsing."""

    def test_parse_json_body(self):
        """Test parsing JSON request body."""
        request_body = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"}
                        }
                    }
                }
            }
        }
        params = parse_openapi_request_body(request_body)
        assert len(params) == 2
        assert params[0]["in"] == "body"

        # Check required field
        name_param = next(p for p in params if p["name"] == "name")
        assert name_param["required"] is True

        # Check optional field
        age_param = next(p for p in params if p["name"] == "age")
        assert age_param["required"] is False

    def test_parse_empty_body(self):
        """Test parsing empty request body."""
        assert parse_openapi_request_body({}) == []


class TestParseOpenapiResponses:
    """Tests for OpenAPI responses parsing."""

    def test_parse_responses(self):
        """Test parsing response codes."""
        responses = {
            "200": {"description": "Success"},
            "400": {"description": "Bad Request"},
            "404": {"description": "Not Found"},
            "default": {"description": "Error"}
        }
        codes = parse_openapi_responses(responses)
        assert "200" in codes
        assert "400" in codes
        assert "404" in codes
        assert "default" not in codes  # Default should be excluded


class TestParseOpenapiOperation:
    """Tests for OpenAPI operation parsing."""

    def test_parse_basic_operation(self):
        """Test parsing basic operation."""
        operation = {
            "summary": "List users",
            "operationId": "listUsers",
            "tags": ["Users"],
            "parameters": [],
            "responses": {"200": {"description": "Success"}}
        }
        result = parse_openapi_operation("/users", "get", operation, "https://api.example.com")
        assert result["name"] == "List users"
        assert result["method"] == "GET"
        assert result["group"] == "Users"
        assert result["path"] == "https://api.example.com/users"

    def test_parse_operation_with_parameters(self):
        """Test parsing operation with parameters."""
        operation = {
            "summary": "Get user",
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {"200": {"description": "Success"}}
        }
        result = parse_openapi_operation("/users/{id}", "get", operation, "")
        assert len(result["params"]) == 1
        assert result["params"][0]["name"] == "id"

    def test_parse_deprecated_operation(self):
        """Test parsing deprecated operation."""
        operation = {
            "summary": "Old endpoint",
            "deprecated": True,
            "responses": {"200": {"description": "Success"}}
        }
        result = parse_openapi_operation("/old", "get", operation, "")
        assert result["metadata"]["deprecated"] is True


class TestParseOpenapiSpec:
    """Tests for complete OpenAPI spec parsing."""

    def test_parse_sample_spec(self):
        """Test parsing sample OpenAPI spec from fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_openapi.yaml"
        with open(fixture_path) as f:
            data = yaml.safe_load(f)

        endpoints = parse_openapi_spec(data)

        # Should have 6 endpoints (GET/POST users, GET/DELETE users/{id}, GET posts, GET health)
        assert len(endpoints) == 6

        # Check first endpoint
        users_get = next(e for e in endpoints if e["path"].endswith("/users") and e["method"] == "GET")
        assert users_get["group"] == "Users"
        assert users_get["name"] == "List all users"

        # Check parameters
        assert len(users_get["params"]) == 2
        param_names = [p["name"] for p in users_get["params"]]
        assert "page" in param_names
        assert "limit" in param_names

    def test_parse_spec_with_base_url(self):
        """Test that base URL is correctly prepended to paths."""
        data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com/v1"}],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        endpoints = parse_openapi_spec(data)
        assert len(endpoints) == 1
        assert endpoints[0]["path"] == "https://api.example.com/v1/users"

    def test_parse_spec_without_tags(self):
        """Test parsing spec without tags."""
        data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        endpoints = parse_openapi_spec(data)
        assert len(endpoints) == 1
        assert endpoints[0]["group"] == "Endpoints"  # Default group

    def test_parse_empty_spec(self):
        """Test parsing empty spec."""
        data = {
            "openapi": "3.0.3",
            "info": {"title": "Empty API", "version": "1.0.0"},
            "paths": {}
        }
        endpoints = parse_openapi_spec(data)
        assert len(endpoints) == 0
