"""
Tests for format conversion.
"""

from api_extractor.converter import (
    openapi_path_to_postman,
    openapi_parameter_to_postman,
    openapi_request_body_to_postman,
    generate_example_from_schema,
    openapi_to_postman,
)


class TestOpenapiPathToPostman:
    """Tests for OpenAPI path conversion."""

    def test_convert_simple_path(self):
        """Test converting simple path."""
        result = openapi_path_to_postman("/users", "https://api.example.com")
        assert "/users" in result["raw"]
        assert "users" in result["path"]

    def test_convert_path_with_params(self):
        """Test converting path with parameters."""
        result = openapi_path_to_postman("/users/{id}", "https://api.example.com")
        assert ":id" in result["path"]

    def test_convert_multiple_params(self):
        """Test converting path with multiple parameters."""
        result = openapi_path_to_postman("/users/{userId}/posts/{postId}", "")
        assert ":userId" in result["path"]
        assert ":postId" in result["path"]


class TestOpenapiParameterToPostman:
    """Tests for OpenAPI parameter conversion."""

    def test_convert_query_param(self):
        """Test converting query parameter."""
        param = {
            "name": "page",
            "in": "query",
            "schema": {"type": "integer", "example": 1},
            "description": "Page number",
        }
        result = openapi_parameter_to_postman(param)
        assert result["key"] == "page"
        assert result["value"] == "1"
        assert result["description"] == "Page number"

    def test_convert_param_without_example(self):
        """Test converting parameter without example."""
        param = {"name": "filter", "in": "query", "schema": {"type": "string"}}
        result = openapi_parameter_to_postman(param)
        assert result["key"] == "filter"
        assert result["value"] == ""


class TestOpenapiRequestBodyToPostman:
    """Tests for OpenAPI request body conversion."""

    def test_convert_json_body(self):
        """Test converting JSON request body."""
        request_body = {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                        },
                    }
                }
            }
        }
        result = openapi_request_body_to_postman(request_body)
        assert result["mode"] == "raw"
        assert "raw" in result

    def test_convert_form_urlencoded(self):
        """Test converting form-urlencoded body."""
        request_body = {
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string"},
                            "password": {"type": "string"},
                        },
                    }
                }
            }
        }
        result = openapi_request_body_to_postman(request_body)
        assert result["mode"] == "urlencoded"
        assert "urlencoded" in result

    def test_convert_multipart_form(self):
        """Test converting multipart form data."""
        request_body = {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string", "format": "binary"},
                            "description": {"type": "string"},
                        },
                    }
                }
            }
        }
        result = openapi_request_body_to_postman(request_body)
        assert result["mode"] == "formdata"
        assert "formdata" in result


class TestGenerateExampleFromSchema:
    """Tests for example generation from schema."""

    def test_generate_string_example(self):
        """Test generating string example."""
        schema = {"type": "string"}
        result = generate_example_from_schema(schema)
        assert isinstance(result, str)

    def test_generate_number_example(self):
        """Test generating number example."""
        schema = {"type": "number"}
        result = generate_example_from_schema(schema)
        assert isinstance(result, (int, float))

    def test_generate_object_example(self):
        """Test generating object example."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        }
        result = generate_example_from_schema(schema)
        assert isinstance(result, dict)
        assert "name" in result
        assert "age" in result

    def test_generate_array_example(self):
        """Test generating array example."""
        schema = {"type": "array", "items": {"type": "string"}}
        result = generate_example_from_schema(schema)
        assert isinstance(result, list)

    def test_use_explicit_example(self):
        """Test using explicit example from schema."""
        schema = {"type": "string", "example": "custom-value"}
        result = generate_example_from_schema(schema)
        assert result == "custom-value"


class TestOpenapiToPostman:
    """Tests for complete OpenAPI to Postman conversion."""

    def test_convert_basic_spec(self):
        """Test converting basic OpenAPI spec."""
        openapi_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        result = openapi_to_postman(openapi_data)

        # Check collection structure
        assert "info" in result
        assert result["info"]["name"] == "Test API"
        assert "item" in result
        assert len(result["item"]) > 0

    def test_convert_with_tags(self):
        """Test conversion groups endpoints by tags."""
        openapi_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "tags": ["Users"],
                        "summary": "List users",
                        "responses": {"200": {"description": "Success"}},
                    }
                },
                "/posts": {
                    "get": {
                        "tags": ["Posts"],
                        "summary": "List posts",
                        "responses": {"200": {"description": "Success"}},
                    }
                },
            },
        }

        result = openapi_to_postman(openapi_data)

        # Should have folders for Users and Posts
        folder_names = [item.get("name") for item in result["item"] if "item" in item]
        assert "Users" in folder_names
        assert "Posts" in folder_names

    def test_convert_with_parameters(self):
        """Test conversion includes parameters."""
        openapi_data = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "parameters": [
                            {
                                "name": "page",
                                "in": "query",
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        result = openapi_to_postman(openapi_data)

        # Find the endpoint
        endpoint = result["item"][0]
        if "item" in endpoint:
            endpoint = endpoint["item"][0]

        # Check query parameters
        assert "url" in endpoint["request"]
        if "query" in endpoint["request"]["url"]:
            query_params = endpoint["request"]["url"]["query"]
            param_names = [p["key"] for p in query_params]
            assert "page" in param_names

    def test_convert_empty_spec(self):
        """Test converting empty spec."""
        openapi_data = {
            "openapi": "3.0.3",
            "info": {"title": "Empty API", "version": "1.0.0"},
            "paths": {},
        }

        result = openapi_to_postman(openapi_data)

        assert result["info"]["name"] == "Empty API"
        assert result["item"] == []
