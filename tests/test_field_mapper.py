"""
Tests for field mapping functionality.
"""

from api_extractor.field_mapper import apply_field_mapping, get_nested_field


class TestGetNestedField:
    """Tests for nested field access."""

    def test_get_top_level_field(self):
        """Test getting top-level field."""
        # Arrange
        obj = {"name": "test", "value": 123}

        # Act
        result = get_nested_field(obj, "name")

        # Assert
        assert result == "test"

    def test_get_nested_field(self):
        """Test getting nested field."""
        # Arrange
        obj = {"metadata": {"deprecated": True, "version": "1.0"}}

        # Act
        result = get_nested_field(obj, "metadata.deprecated")

        # Assert
        assert result is True

    def test_get_deeply_nested_field(self):
        """Test getting deeply nested field."""
        # Arrange
        obj = {"data": {"user": {"profile": {"name": "John"}}}}

        # Act
        result = get_nested_field(obj, "data.user.profile.name")

        # Assert
        assert result == "John"

    def test_get_missing_field(self):
        """Test getting missing field returns None."""
        # Arrange
        obj = {"name": "test"}

        # Act
        result = get_nested_field(obj, "missing")

        # Assert
        assert result is None

    def test_get_missing_nested_field(self):
        """Test getting missing nested field returns None."""
        # Arrange
        obj = {"metadata": {"version": "1.0"}}

        # Act
        result = get_nested_field(obj, "metadata.missing")

        # Assert
        assert result is None


class TestApplyFieldMapping:
    """Tests for field mapping."""

    def test_no_mapping_returns_unchanged(self):
        """Test that no mapping returns data unchanged."""
        # Arrange
        endpoints = [
            {"method": "GET", "path": "/users", "name": "List users"},
            {"method": "POST", "path": "/users", "name": "Create user"},
        ]

        # Act
        result = apply_field_mapping(endpoints, None)

        # Assert
        assert result == endpoints

    def test_empty_mapping_returns_unchanged(self):
        """Test that empty mapping returns data unchanged."""
        # Arrange
        endpoints = [{"method": "GET", "path": "/users", "name": "List users"}]

        # Act
        result = apply_field_mapping(endpoints, {})

        # Assert
        assert result == endpoints

    def test_select_and_rename_fields(self):
        """Test selecting and renaming fields."""
        # Arrange
        endpoints = [
            {
                "method": "GET",
                "path": "/users",
                "name": "List users",
                "description": "Get all users",
            }
        ]
        field_map = {"method": "HTTP Method", "path": "Endpoint"}

        # Act
        result = apply_field_mapping(endpoints, field_map)

        # Assert
        assert len(result) == 1
        assert result[0] == {"HTTP Method": "GET", "Endpoint": "/users"}

    def test_preserve_field_order(self):
        """Test that field order matches mapping order."""
        # Arrange
        endpoints = [{"method": "GET", "path": "/users", "name": "List users"}]
        field_map = {"name": "Name", "method": "Method", "path": "Path"}

        # Act
        result = apply_field_mapping(endpoints, field_map)

        # Assert
        keys = list(result[0].keys())
        assert keys == ["Name", "Method", "Path"]

    def test_map_nested_field(self):
        """Test mapping nested field."""
        # Arrange
        endpoints = [
            {
                "method": "GET",
                "path": "/users",
                "metadata": {"deprecated": True, "version": "1.0"},
            }
        ]
        field_map = {"method": "Method", "metadata.deprecated": "Deprecated"}

        # Act
        result = apply_field_mapping(endpoints, field_map)

        # Assert
        assert result[0] == {"Method": "GET", "Deprecated": True}

    def test_missing_field_returns_none(self):
        """Test that missing fields are included as None."""
        # Arrange
        endpoints = [{"method": "GET", "path": "/users"}]
        field_map = {"method": "Method", "missing": "Missing Field"}

        # Act
        result = apply_field_mapping(endpoints, field_map)

        # Assert
        assert result[0] == {"Method": "GET", "Missing Field": None}

    def test_map_multiple_endpoints(self):
        """Test mapping multiple endpoints."""
        # Arrange
        endpoints = [
            {"method": "GET", "path": "/users", "name": "List"},
            {"method": "POST", "path": "/users", "name": "Create"},
            {"method": "DELETE", "path": "/users/{id}", "name": "Delete"},
        ]
        field_map = {"method": "HTTP Method", "name": "Name"}

        # Act
        result = apply_field_mapping(endpoints, field_map)

        # Assert
        assert len(result) == 3
        assert result[0] == {"HTTP Method": "GET", "Name": "List"}
        assert result[1] == {"HTTP Method": "POST", "Name": "Create"}
        assert result[2] == {"HTTP Method": "DELETE", "Name": "Delete"}

    def test_keep_original_name_if_mapping_value_empty(self):
        """Test that empty string in mapping keeps original field name."""
        # Arrange
        endpoints = [{"method": "GET", "path": "/users"}]
        field_map = {"method": "method", "path": "path"}

        # Act
        result = apply_field_mapping(endpoints, field_map)

        # Assert
        assert result[0] == {"method": "GET", "path": "/users"}
