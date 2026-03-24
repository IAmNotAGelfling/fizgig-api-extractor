"""
Tests for test helper utilities.
"""

import pytest

from tests.test_helpers import normalize_rich_output, assert_in_output, assert_all_in_output


class TestNormalizeRichOutput:
    """Test Rich output normalization."""

    def test_normalize_simple_wrap(self):
        """Test normalizing a simple line wrap."""
        output = "Saved to \n/var/folders/long/path.json"
        normalized = normalize_rich_output(output)
        assert "Saved to /var/folders/long/path.json" in normalized

    def test_normalize_preserves_paragraphs(self):
        """Test that paragraph breaks are preserved."""
        output = "Line 1.\n\nLine 2."
        normalized = normalize_rich_output(output)
        assert normalized == output

    def test_normalize_preserves_intentional_breaks(self):
        """Test that intentional line breaks are preserved."""
        output = "Header:\n  Item 1\n  Item 2"
        normalized = normalize_rich_output(output)
        # Indented lines should be preserved
        assert "  Item 1" in normalized

    def test_normalize_handles_emoji(self):
        """Test handling output with emoji."""
        output = "✓ Success\n/some/path"
        normalized = normalize_rich_output(output)
        # Checkmark at end of word gets joined with next line
        assert "✓ Success /some/path" in normalized


class TestAssertInOutput:
    """Test assert_in_output helper."""

    def test_assert_in_output_success(self):
        """Test successful assertion."""
        output = "Saved to \n/var/path.json"
        # Should not raise
        assert_in_output("Saved to /var/path.json", output)

    def test_assert_in_output_failure(self):
        """Test failed assertion."""
        output = "Some output"
        with pytest.raises(AssertionError, match="Expected 'missing' in output"):
            assert_in_output("missing", output)

    def test_assert_in_output_without_normalization(self):
        """Test without normalization."""
        output = "Line 1\nLine 2"
        with pytest.raises(AssertionError):
            # Without normalization, wrapped line won't match
            assert_in_output("Line 1 Line 2", output, normalize=False)


class TestAssertAllInOutput:
    """Test assert_all_in_output helper."""

    def test_assert_all_in_output_success(self):
        """Test successful assertion with multiple parts."""
        output = "Saved to \n/var/folders/path.json"
        # Should not raise
        assert_all_in_output(["Saved to", "/var/folders/path.json"], output)

    def test_assert_all_in_output_partial_failure(self):
        """Test failure when one part is missing."""
        output = "Part 1 here"
        with pytest.raises(AssertionError, match="Expected 'Part 2' in output"):
            assert_all_in_output(["Part 1", "Part 2"], output)

    def test_assert_all_in_output_order_independent(self):
        """Test that order doesn't matter."""
        output = "Second thing\nFirst thing"
        # Should not raise - both present regardless of order
        assert_all_in_output(["First thing", "Second thing"], output)
