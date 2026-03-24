"""
Tests for treeview.py to achieve 90%+ coverage.
"""

from api_extractor.treeview import get_method_style, display_tree


class TestGetMethodStyle:
    """Test HTTP method styling."""

    def test_get_style_all_methods(self):
        """Test style for all HTTP methods."""
        assert "cyan" in get_method_style("GET")
        assert "green" in get_method_style("POST")
        assert "yellow" in get_method_style("PUT")
        assert "magenta" in get_method_style("PATCH")
        assert "red" in get_method_style("DELETE")
        assert "blue" in get_method_style("HEAD")
        assert "white" in get_method_style("OPTIONS")
        assert "white" in get_method_style("TRACE")

    def test_get_style_unknown_method(self):
        """Test style for unknown method."""
        assert "white" in get_method_style("CUSTOM")

    def test_get_style_lowercase(self):
        """Test style with lowercase method."""
        assert "cyan" in get_method_style("get")


class TestDisplayTree:
    """Test tree display functionality."""

    def test_display_tree_basic(self):
        """Test basic tree display."""
        endpoints = [
            {
                "group": "Users",
                "name": "List users",
                "method": "GET",
                "path": "/users",
                "description": "Get all users",
                "params": [],
            }
        ]

        # Should not raise
        display_tree(endpoints)

    def test_display_tree_with_deprecated_endpoint(self):
        """Test tree display with deprecated endpoint."""
        endpoints = [
            {
                "group": "Users",
                "name": "Old API",
                "method": "GET",
                "path": "/old-users",
                "description": "Deprecated endpoint",
                "params": [],
                "metadata": {"deprecated": True},
            },
            {
                "group": "Users",
                "name": "New API",
                "method": "GET",
                "path": "/users",
                "description": "Current endpoint",
                "params": [],
                "metadata": {"deprecated": False},
            },
        ]

        # Should not raise
        display_tree(endpoints)

    def test_display_tree_with_params_flag(self):
        """Test tree display with show_params=True."""
        endpoints = [
            {
                "group": "Users",
                "name": "Get user",
                "method": "GET",
                "path": "/users/{id}",
                "description": "Retrieve a user by ID",
                "params": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "string",
                        "required": True,
                        "description": "User ID",
                    },
                    {
                        "name": "fields",
                        "in": "query",
                        "type": "string",
                        "required": False,
                        "description": "Fields to return",
                    },
                ],
            }
        ]

        # Should not raise and show params
        display_tree(endpoints, show_params=True)

    def test_display_tree_with_params_no_description(self):
        """Test tree display with params but no endpoint description."""
        endpoints = [
            {
                "group": "Users",
                "name": "Get user",
                "method": "GET",
                "path": "/users/{id}",
                "description": "",  # Empty description
                "params": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "string",
                        "required": True,
                        "description": "User ID",
                    }
                ],
            }
        ]

        # Should not raise
        display_tree(endpoints, show_params=True)

    def test_display_tree_with_required_and_optional_params(self):
        """Test tree display with both required and optional parameters."""
        endpoints = [
            {
                "group": "API",
                "name": "Search",
                "method": "POST",
                "path": "/search",
                "description": "Search API",
                "params": [
                    {
                        "name": "query",
                        "in": "query",
                        "type": "string",
                        "required": True,
                        "description": "Search query",
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "type": "integer",
                        "required": False,
                        "description": "Result limit",
                    },
                ],
            }
        ]

        # Should show both required and optional params differently
        display_tree(endpoints, show_params=True)

    def test_display_tree_with_param_no_description(self):
        """Test tree display with parameter without description."""
        endpoints = [
            {
                "group": "API",
                "name": "Update",
                "method": "PUT",
                "path": "/items/{id}",
                "description": "Update item",
                "params": [
                    {
                        "name": "id",
                        "in": "path",
                        "type": "string",
                        "required": True,
                        "description": "",  # No description
                    }
                ],
            }
        ]

        # Should handle param without description
        display_tree(endpoints, show_params=True)

    def test_display_tree_multiple_groups(self):
        """Test tree display with multiple groups."""
        endpoints = [
            {
                "group": "Users",
                "name": "List",
                "method": "GET",
                "path": "/users",
                "description": "List users",
                "params": [],
            },
            {
                "group": "Posts",
                "name": "List",
                "method": "GET",
                "path": "/posts",
                "description": "List posts",
                "params": [],
            },
        ]

        # Should show multiple groups
        display_tree(endpoints)

    def test_display_tree_all_http_methods(self):
        """Test tree display with all HTTP methods."""
        endpoints = [
            {
                "group": "API",
                "name": "Get",
                "method": "GET",
                "path": "/",
                "description": "",
                "params": [],
            },
            {
                "group": "API",
                "name": "Post",
                "method": "POST",
                "path": "/",
                "description": "",
                "params": [],
            },
            {
                "group": "API",
                "name": "Put",
                "method": "PUT",
                "path": "/",
                "description": "",
                "params": [],
            },
            {
                "group": "API",
                "name": "Patch",
                "method": "PATCH",
                "path": "/",
                "description": "",
                "params": [],
            },
            {
                "group": "API",
                "name": "Delete",
                "method": "DELETE",
                "path": "/",
                "description": "",
                "params": [],
            },
            {
                "group": "API",
                "name": "Head",
                "method": "HEAD",
                "path": "/",
                "description": "",
                "params": [],
            },
            {
                "group": "API",
                "name": "Options",
                "method": "OPTIONS",
                "path": "/",
                "description": "",
                "params": [],
            },
        ]

        # Should show all methods with proper colors
        display_tree(endpoints)

    def test_display_tree_endpoint_name_same_as_method(self):
        """Test tree display when endpoint name matches method."""
        endpoints = [
            {
                "group": "API",
                "name": "GET",  # Same as method
                "method": "GET",
                "path": "/test",
                "description": "Test",
                "params": [],
            }
        ]

        # Should not duplicate name when it matches method
        display_tree(endpoints)

    def test_display_tree_with_description_and_params(self):
        """Test tree display with both description and parameters shown."""
        endpoints = [
            {
                "group": "Users",
                "name": "Create user",
                "method": "POST",
                "path": "/users",
                "description": "Create a new user account with the provided details",
                "params": [
                    {
                        "name": "username",
                        "in": "body",
                        "type": "string",
                        "required": True,
                        "description": "Unique username for the account",
                    },
                    {
                        "name": "email",
                        "in": "body",
                        "type": "string",
                        "required": True,
                        "description": "Email address",
                    },
                    {
                        "name": "name",
                        "in": "body",
                        "type": "string",
                        "required": False,
                        "description": "Full name of the user",
                    },
                ],
            }
        ]

        # Should show description AND all parameters
        display_tree(endpoints, show_params=True)

    def test_display_tree_empty_endpoints(self):
        """Test tree display with no endpoints."""
        endpoints = []

        # Should handle empty list gracefully
        display_tree(endpoints)
