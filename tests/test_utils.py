"""
Tests for utility functions.
"""

import pytest

from api_extractor.utils import (
    safe_get,
    slugify,
    merge_dicts,
    normalise_url,
    strip_empty,
    extract_path_params,
    format_method,
    truncate_text,
    group_by_tag,
    ensure_list,
)


class TestSafeGet:
    """Tests for safe_get function."""

    def test_safe_get_nested_dict(self):
        """Test retrieving nested dictionary values."""
        data = {"a": {"b": {"c": 42}}}
        assert safe_get(data, "a", "b", "c") == 42

    def test_safe_get_missing_key(self):
        """Test default value when key doesn't exist."""
        data = {"a": {"b": {}}}
        assert safe_get(data, "a", "b", "c", default="missing") == "missing"

    def test_safe_get_none_value(self):
        """Test handling of None values."""
        data = {"a": None}
        assert safe_get(data, "a", "b", default="default") == "default"

    def test_safe_get_empty_dict(self):
        """Test with empty dictionary."""
        assert safe_get({}, "a", default="empty") == "empty"


class TestSlugify:
    """Tests for slugify function."""

    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify("Hello World") == "hello-world"

    def test_slugify_special_chars(self):
        """Test slugification with special characters."""
        assert slugify("API/Endpoints_2024") == "api-endpoints-2024"

    def test_slugify_multiple_spaces(self):
        """Test handling of multiple spaces."""
        assert slugify("Hello   World") == "hello-world"

    def test_slugify_empty_string(self):
        """Test with empty string."""
        assert slugify("") == ""

    def test_slugify_leading_trailing(self):
        """Test removal of leading/trailing hyphens."""
        assert slugify("--test--") == "test"


class TestMergeDicts:
    """Tests for merge_dicts function."""

    def test_merge_two_dicts(self):
        """Test merging two dictionaries."""
        result = merge_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4})
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_multiple_dicts(self):
        """Test merging multiple dictionaries."""
        result = merge_dicts({"a": 1}, {"b": 2}, {"c": 3})
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_merge_empty_dicts(self):
        """Test merging with empty dictionaries."""
        result = merge_dicts({}, {"a": 1}, {})
        assert result == {"a": 1}


class TestNormaliseUrl:
    """Tests for normalise_url function."""

    def test_normalise_with_base(self):
        """Test URL normalisation with base URL."""
        assert normalise_url("/api/users", "https://example.com") == "https://example.com/api/users"

    def test_normalise_absolute_url(self):
        """Test that absolute URLs are unchanged."""
        url = "https://example.com/api/users"
        assert normalise_url(url, "https://base.com") == url

    def test_normalise_no_base(self):
        """Test URL normalisation without base URL."""
        assert normalise_url("/api/users", "") == "/api/users"

    def test_normalise_no_leading_slash(self):
        """Test URL without leading slash."""
        assert normalise_url("api/users", "https://example.com") == "https://example.com/api/users"


class TestStripEmpty:
    """Tests for strip_empty function."""

    def test_strip_empty_dict(self):
        """Test stripping empty values from dictionary."""
        data = {"a": 1, "b": None, "c": "", "d": []}
        assert strip_empty(data) == {"a": 1}

    def test_strip_empty_nested(self):
        """Test stripping empty values from nested structures."""
        data = {"a": {"b": 1, "c": None}, "d": [1, None, 2]}
        result = strip_empty(data)
        assert result == {"a": {"b": 1}, "d": [1, 2]}

    def test_strip_empty_list(self):
        """Test stripping empty values from list."""
        assert strip_empty([1, None, "", 2, []]) == [1, 2]


class TestExtractPathParams:
    """Tests for extract_path_params function."""

    def test_extract_openapi_style(self):
        """Test extracting OpenAPI-style parameters."""
        params = extract_path_params("/users/{id}/posts/{postId}")
        assert params == ["id", "postId"]

    def test_extract_express_style(self):
        """Test extracting Express-style parameters."""
        params = extract_path_params("/users/:userId/comments/:commentId")
        assert params == ["userId", "commentId"]

    def test_extract_no_params(self):
        """Test path with no parameters."""
        assert extract_path_params("/users/list") == []

    def test_extract_mixed_style(self):
        """Test mixed parameter styles."""
        params = extract_path_params("/users/{id}/posts/:postId")
        assert "id" in params
        assert "postId" in params


class TestFormatMethod:
    """Tests for format_method function."""

    def test_format_lowercase(self):
        """Test formatting lowercase method."""
        assert format_method("get") == "GET"

    def test_format_mixed_case(self):
        """Test formatting mixed case method."""
        assert format_method("Post") == "POST"

    def test_format_already_upper(self):
        """Test method already uppercase."""
        assert format_method("DELETE") == "DELETE"

    def test_format_empty(self):
        """Test empty method defaults to GET."""
        assert format_method("") == "GET"


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_truncate_long_text(self):
        """Test truncating long text."""
        text = "This is a very long text that needs truncation"
        result = truncate_text(text, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_short_text(self):
        """Test text shorter than max length."""
        text = "Short"
        assert truncate_text(text, 20) == "Short"

    def test_truncate_custom_suffix(self):
        """Test custom suffix."""
        text = "This is a very long text"
        result = truncate_text(text, 15, suffix="…")
        assert result.endswith("…")


class TestGroupByTag:
    """Tests for group_by_tag function."""

    def test_group_by_tag(self):
        """Test grouping endpoints by tag."""
        endpoints = [
            {"group": "Users", "path": "/users"},
            {"group": "Users", "path": "/users/{id}"},
            {"group": "Posts", "path": "/posts"},
        ]
        grouped = group_by_tag(endpoints)
        assert len(grouped["Users"]) == 2
        assert len(grouped["Posts"]) == 1

    def test_group_uncategorized(self):
        """Test endpoints without group."""
        endpoints = [{"path": "/test"}]
        grouped = group_by_tag(endpoints)
        assert "Uncategorized" in grouped


class TestEnsureList:
    """Tests for ensure_list function."""

    def test_ensure_list_single_value(self):
        """Test converting single value to list."""
        assert ensure_list("single") == ["single"]

    def test_ensure_list_already_list(self):
        """Test value already a list."""
        assert ensure_list([1, 2, 3]) == [1, 2, 3]

    def test_ensure_list_none(self):
        """Test None value."""
        assert ensure_list(None) == []
